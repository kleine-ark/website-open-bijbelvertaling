"""On-request corrections: real storage, publication and permission boundaries."""
import copy
import hashlib
import json
import sys
import tempfile
import unittest
import sqlite3
import subprocess
from unittest.mock import patch
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'server'))
from collaboration_api import ReviewStore, Forbidden, Conflict, InvalidRequest
from corrections import Corrections
from correction_files import apply_bundle
from review_content import canonical_hash, text_review_payload, location_review_payload
from correction_cli import prepare
import correction_files


class CorrectionsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'data/genesis').mkdir(parents=True)
        self.chapter = {'number': 1, 'chapterIntro': {'text2026': 'Begin'}, 'verses': [
            {'number': 1, 'text2026': 'Oude tekst.', 'text2026_html': 'Oude tekst.', 'marginNotes': []},
            {'number': 2, 'text2026': 'Ander vers.', 'text2026_html': 'Ander vers.', 'marginNotes': []},
        ]}
        self.path = self.root / 'data/genesis/1.json'
        self.path.write_text(json.dumps(self.chapter))
        self.location = {'type': 'Feature', 'geometry': {'type': 'Point', 'coordinates': [35, 31]},
                         'properties': {'id': 'jerusalem', 'naam': 'Jerusalem'}}
        (self.root / 'data/geografie-runtime.geojson').write_text(json.dumps({
            'features': [self.location]}))
        self.store = ReviewStore(self.root / 'private/db.sqlite3', {'admin@example.test'})
        self.admin = self.user('admin')
        self.reviewer = self.user('reviewer')
        self.reader = self.user('reader')
        self.reviewer = self.store.set_roles(self.admin, self.reviewer['uid'], ['reviewer'])
        self.service = Corrections(self.store, self.root)
        self.sync()

    def user(self, name):
        return self.store.upsert_user({'sub': name, 'name': name, 'email': name + '@example.test',
                                       'email_verified': True})

    def sync(self):
        chapter = json.loads(self.path.read_text())
        items = [('text-chapter', 'genesis/1', text_review_payload(chapter), 'data/genesis/1.json')]
        items += [('text-verse', 'genesis/1/' + str(v['number']), v, 'data/genesis/1.json')
                  for v in text_review_payload(chapter)['verses']]
        location = json.loads((self.root / 'data/geografie-runtime.geojson').read_text())['features'][0]
        items += [('location', 'jerusalem', location_review_payload(location), 'data/geografie-runtime.geojson')]
        catalog = {'schemaVersion': 2, 'historicalSubjects': [], 'subjectTypes': {
            'text-chapter': 'Hoofdstuk', 'text-verse': 'Vers', 'location': 'Locatie'}, 'subjects': [
                {'type': kind, 'id': key, 'revision': canonical_hash(value), 'label': key,
                 'href': 'index.html#' + key, 'source': source,
                 'metadata': {'sourceHash': hashlib.sha256((self.root / source).read_bytes()).hexdigest()}}
                for kind, key, value, source in items]}
        catalog['catalogRevision'] = canonical_hash(catalog)
        self.store.sync_catalog(catalog)

    def payload(self, kind='text-verse', key='genesis/1/1'):
        subject = self.store.get_subject(self.reviewer, kind, key)
        return {'subjectType': kind, 'subjectId': key, 'revision': subject['revision'],
                'sourceHash': subject['metadata']['sourceHash'], 'reason': 'De vertaling klopt niet.'}

    def request(self, kind='text-verse', key='genesis/1/1'):
        return self.service.create(self.reviewer, self.payload(kind, key))

    def propose(self, task):
        changed = copy.deepcopy(self.chapter)
        changed['verses'][0].update(text2026='Nieuwe tekst.', text2026_html='Nieuwe tekst.')
        return self.service.propose({'id': task['id'], 'version': task['version'],
            'summary': 'Woordkeuze aangepast.', 'files': [{'path': 'data/genesis/1.json',
                'before': self.path.read_text(), 'after': json.dumps(changed)}]})

    def decision(self, task, action, note=''):
        return self.service.decide(self.reviewer, task['id'], {
            'version': task['version'], 'action': action, 'note': note})

    def test_permissions_are_identical_to_verification_and_rechecked(self):
        with self.assertRaises(Forbidden):
            self.service.create(self.reader, self.payload())
        with self.assertRaises(Forbidden):
            self.service.list(self.reader)
        task = self.request()
        self.store.set_roles(self.admin, self.reviewer['uid'], [])
        with self.assertRaises(Forbidden):
            self.decision(task, 'close', 'Niet meer nodig.')
        with self.assertRaises(Forbidden):
            self.service.get(self.reviewer, task['id'])

    def test_reason_revision_source_and_identity_are_validated(self):
        for patch in ({'reason': ' '}, {'actorUid': 'admin'}, {'reason': 12}):
            with self.assertRaises(InvalidRequest):
                self.service.create(self.reviewer, dict(self.payload(), **patch))
        for patch in ({'revision': 'a' * 64}, {'sourceHash': 'a' * 64}):
            with self.assertRaises(Conflict):
                self.service.create(self.reviewer, dict(self.payload(), **patch))

    def test_request_revokes_affected_approvals_and_blocks_reverification(self):
        for kind, key in [('text-verse', 'genesis/1/1'), ('text-chapter', 'genesis/1')]:
            payload = self.payload(kind, key)
            payload.pop('reason')
            self.store.record_review(self.admin, dict(payload, decision='approved', note=''))
        task = self.request()
        for kind, key in [('text-verse', 'genesis/1/1'), ('text-chapter', 'genesis/1')]:
            subject = self.store.get_subject(None, kind, key)
            self.assertEqual(subject['status'], 'correction-needed')
            self.assertNotIn('latestReview', subject)
            payload = self.payload(kind, key)
            payload.pop('reason')
            with self.assertRaises(Conflict):
                self.store.record_review(self.admin, dict(payload, decision='approved', note=''))
        self.assertEqual(self.store.verified_chapters(), {})
        self.decision(task, 'close', 'Melding ingetrokken.')
        self.assertEqual(self.store.get_subject(None, 'text-chapter', 'genesis/1')['status'], 'pending')

    def test_duplicate_requests_are_not_silently_overwritten(self):
        self.request()
        with self.assertRaises(Conflict):
            self.request()

    def test_complete_manual_flow_requires_publication_and_new_verification(self):
        task = self.request()
        task = self.propose(task)
        self.assertEqual(task['status'], 'proposed')
        self.assertEqual(json.loads(self.path.read_text()), self.chapter)
        task = self.decision(task, 'accept')
        self.assertEqual(task['status'], 'accepted')
        bundle = self.service.export('accepted')
        apply_bundle(self.root, bundle)
        self.sync()
        self.service.reconcile()
        task = self.service.get(self.reviewer, task['id'])
        self.assertEqual(task['status'], 'applied')
        self.assertEqual(self.store.get_subject(None, 'text-verse', 'genesis/1/1')['status'], 'pending')
        payload = self.payload()
        payload.pop('reason')
        self.store.record_review(self.reviewer, dict(payload, decision='approved', note=''))
        self.assertEqual(self.store.get_subject(None, 'text-verse', 'genesis/1/1')['status'], 'approved')

    def test_returned_proposal_preserves_history_and_requires_new_acceptance(self):
        task = self.propose(self.request())
        version = task['version']
        task = self.decision(task, 'return', 'Gebruik een ander woord.')
        self.assertEqual(task['status'], 'requested')
        with self.assertRaises(Conflict):
            self.service.decide(self.reviewer, task['id'], {'version': version, 'action': 'accept', 'note': ''})
        task = self.propose(task)
        self.assertEqual(len(task['proposals']), 2)
        self.assertIn('Gebruik een ander woord.', json.dumps(task, ensure_ascii=False))

    def test_only_admin_sees_actor_identity_and_audit_is_immutable(self):
        task = self.propose(self.request())
        task = self.decision(task, 'accept')
        public = json.dumps(self.service.get(self.reviewer, task['id']))
        self.assertNotIn('reviewer@example.test', public)
        self.assertNotIn('actor', public)
        private = self.service.get(self.admin, task['id'])
        self.assertEqual(private['events'][0]['actor']['uid'], self.reviewer['uid'])
        with self.store._connect() as db:
            for table in ('correction_events', 'correction_proposals'):
                with self.assertRaises(sqlite3.IntegrityError):
                    db.execute('DELETE FROM ' + table)
                with self.assertRaises(sqlite3.IntegrityError):
                    db.execute('UPDATE ' + table + ' SET id=id')

    def test_stale_proposals_require_explicit_rebase(self):
        task = self.propose(self.request())
        changed = copy.deepcopy(self.chapter)
        changed['verses'][0]['text2026'] = 'Intussen veranderd.'
        self.path.write_text(json.dumps(changed))
        self.sync()
        self.assertTrue(self.service.get(self.reviewer, task['id'])['stale'])
        with self.assertRaises(Conflict):
            self.decision(task, 'accept')
        task = self.decision(task, 'rebase', 'Geldt ook voor de nieuwe tekst.')
        self.assertEqual(task['status'], 'requested')
        self.assertFalse(task['stale'])

    def test_apply_rejects_unaccepted_conflicting_and_unsafe_files_without_partial_writes(self):
        task = self.propose(self.request())
        with self.assertRaises(ValueError):
            apply_bundle(self.root, self.service.export('proposed'))
        self.decision(task, 'accept')
        bundle = self.service.export('accepted')
        original = self.path.read_text()
        for path in ('../secret.json', 'js/app.js', 'data/../private/key.json'):
            invalid = copy.deepcopy(bundle)
            invalid['items'][0]['proposal']['files'][0]['path'] = path
            with self.assertRaises(ValueError):
                apply_bundle(self.root, invalid)
        self.path.write_text(original + '\n')
        with self.assertRaises(ValueError):
            apply_bundle(self.root, bundle)
        self.assertEqual(self.path.read_text(), original + '\n')

    def test_location_uses_same_queue_and_exact_snapshot(self):
        task = self.request('location', 'jerusalem')
        self.assertEqual(task['before'], location_review_payload(self.location))
        self.assertEqual(self.store.get_subject(None, 'location', 'jerusalem')['status'], 'correction-needed')

    def test_schema_upgrade_keeps_existing_accounts_and_reviews(self):
        self.request()
        another = ReviewStore(self.store.database_path, {'admin@example.test'})
        self.assertEqual(Corrections(another, self.root).list(self.reviewer)['total'], 1)

    def test_pre_correction_database_is_migrated_without_changing_accounts_or_reviews(self):
        payload = self.payload()
        payload.pop('reason')
        self.store.record_review(self.reviewer, dict(payload, decision='approved', note='Al nagekeken.'))
        with self.store._connect() as db:
            users = [tuple(row) for row in db.execute('SELECT * FROM users ORDER BY uid')]
            reviews = [tuple(row) for row in db.execute('SELECT * FROM review_events ORDER BY id')]
            for table in ('correction_proposals', 'correction_events', 'corrections'):
                db.execute('DROP TABLE ' + table)
            db.execute("DELETE FROM metadata WHERE key='corrections-v1'")
        upgraded = ReviewStore(self.store.database_path, {'admin@example.test'})
        with upgraded._connect() as db:
            self.assertEqual(users, [tuple(row) for row in db.execute('SELECT * FROM users ORDER BY uid')])
            self.assertEqual(reviews, [tuple(row) for row in db.execute('SELECT * FROM review_events ORDER BY id')])
        self.assertEqual(Corrections(upgraded, self.root).list(self.reviewer)['total'], 0)

    def test_revoked_role_cannot_accept_and_second_click_cannot_change_decision(self):
        task = self.propose(self.request())
        self.store.set_roles(self.admin, self.reviewer['uid'], [])
        with self.assertRaises(Forbidden):
            self.decision(task, 'accept')
        self.store.set_roles(self.admin, self.reviewer['uid'], ['reviewer'])
        self.decision(task, 'accept')
        with self.assertRaises(Conflict):
            self.decision(task, 'accept')

    def test_supporting_files_must_match_before_acceptance_and_after_publication(self):
        task = self.request()
        data = copy.deepcopy(self.chapter)
        data['verses'][0]['text2026'] = 'Nieuwe tekst.'
        source = self.root / 'data/support.json'
        source.write_text('{"value": "oud"}')
        task = self.service.propose({'id': task['id'], 'version': task['version'], 'summary': 'Met brondata.', 'files': [
            {'path': 'data/genesis/1.json', 'before': self.path.read_text(), 'after': json.dumps(data)},
            {'path': 'data/support.json', 'before': source.read_text(), 'after': '{"value": "nieuw"}'}]})
        source.write_text('{"value": "intussen gewijzigd"}')
        with self.assertRaises(Conflict):
            self.decision(task, 'accept')
        source.write_text('{"value": "oud"}')
        task = self.decision(task, 'accept')
        self.path.write_text(json.dumps(data))
        self.sync()
        self.service.reconcile()
        self.assertEqual(self.service.get(self.reviewer, task['id'])['status'], 'accepted')
        source.write_text('{"value": "nieuw"}')
        self.service.reconcile()
        self.assertEqual(self.service.get(self.reviewer, task['id'])['status'], 'applied')

    def test_prepare_bundles_real_worktree_changes_and_apply_rolls_back_on_io_error(self):
        def git(*args):
            return subprocess.check_output(['git', '-C', str(self.root), *args], stderr=subprocess.DEVNULL)
        git('init')
        (self.root / '.git/info/exclude').write_text('/private/\n')
        git('add', 'data')
        git('-c', 'user.name=Test', '-c', 'user.email=test@example.test', 'commit', '-qm', 'Fixture')
        task = self.request()
        exported = self.service.export('requested')
        original = self.path.read_text()
        changed = copy.deepcopy(self.chapter)
        changed['verses'][0]['text2026'] = 'Andere tekst.'
        self.path.write_bytes(json.dumps(changed, indent=2).replace('\n', '\r\n').encode('utf-8'))
        proposal = prepare(self.root, exported, task['id'], 'Op verzoek aangepast.', 'HEAD')
        self.assertEqual(proposal['files'][0]['before'], original)
        self.assertEqual(proposal['files'][0]['after'], self.path.read_bytes().decode('utf-8'))
        self.path.write_text(original)
        other = self.root / 'data/support.json'
        other.write_text('{}')
        proposal['files'].append({'path': 'data/support.json', 'before': '{}', 'after': '{"ok": true}'})
        task = self.service.propose(proposal)
        self.decision(task, 'accept')
        bundle = self.service.export('accepted')
        actual_replace = correction_files.replace_file
        def fail_second(path, content):
            if path == other:
                raise OSError('Test disk failure')
            actual_replace(path, content)
        with patch.object(correction_files, 'replace_file', side_effect=fail_second):
            with self.assertRaises(OSError):
                apply_bundle(self.root, bundle)
        self.assertEqual(self.path.read_text(), original)
        self.assertEqual(other.read_text(), '{}')

    def test_reverting_to_historically_approved_content_still_requires_new_verification(self):
        original = self.path.read_text()
        future = copy.deepcopy(self.chapter)
        future['verses'][0].update(text2026='Nieuwe tekst.', text2026_html='Nieuwe tekst.')
        self.path.write_text(json.dumps(future))
        self.sync()
        payload = self.payload()
        payload.pop('reason')
        self.store.record_review(self.reviewer, dict(payload, decision='approved', note='Eerdere versie.'))
        self.path.write_text(original)
        self.sync()
        task = self.propose(self.request())
        self.decision(task, 'accept')
        apply_bundle(self.root, self.service.export('accepted'))
        self.sync()
        self.service.reconcile()
        self.assertEqual(self.store.get_subject(None, 'text-verse', 'genesis/1/1')['status'], 'pending')

    def test_location_proposal_can_be_accepted_and_published_without_auto_verification(self):
        task = self.request('location', 'jerusalem')
        path = self.root / 'data/geografie-runtime.geojson'
        changed = json.loads(path.read_text())
        changed['features'][0]['geometry']['coordinates'] = [35.1, 31.2]
        task = self.service.propose({'id': task['id'], 'version': task['version'], 'summary': 'Coördinaten gecorrigeerd.',
            'files': [{'path': 'data/geografie-runtime.geojson', 'before': path.read_text(), 'after': json.dumps(changed)}]})
        self.decision(task, 'accept')
        apply_bundle(self.root, self.service.export('accepted'))
        self.sync()
        self.service.reconcile()
        self.assertEqual(self.service.get(self.reviewer, task['id'])['status'], 'applied')
        self.assertEqual(self.store.get_subject(None, 'location', 'jerusalem')['status'], 'pending')

    def test_proposal_cannot_remove_other_subjects_or_change_stable_ids(self):
        task = self.request()
        altered = copy.deepcopy(self.chapter)
        altered['verses'].pop()
        altered['verses'][0]['text2026'] = 'Nieuwe tekst.'
        with self.assertRaises(ValueError):
            self.service.propose({'id': task['id'], 'version': task['version'], 'summary': 'Ongeldig.',
                'files': [{'path': 'data/genesis/1.json', 'before': self.path.read_text(), 'after': json.dumps(altered)}]})


if __name__ == '__main__':
    unittest.main()
