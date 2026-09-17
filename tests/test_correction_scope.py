"""A request names one component; it is not a rejection of every addition."""
import copy
import json
import unittest
import sqlite3
from unittest.mock import patch

import test_corrections as fixtures
from collaboration_errors import InvalidRequest, Conflict


class CorrectionScopeTests(unittest.TestCase):
    setUp = fixtures.CorrectionsTests.setUp
    user = fixtures.CorrectionsTests.user
    sync = fixtures.CorrectionsTests.sync
    payload = fixtures.CorrectionsTests.payload
    review_payload = fixtures.CorrectionsTests.review_payload
    decision = fixtures.CorrectionsTests.decision

    def approve(self):
        self.store.record_review(self.admin, self.review_payload('text-chapter', 'genesis/1'))

    def request(self, component='text', custom=''):
        return self.service.create(self.reviewer, dict(self.payload(), component=component, customTarget=custom))

    def test_text_request_does_not_revoke_other_components(self):
        self.approve()
        before = self.store.get_subject(self.admin, 'text-verse', 'genesis/1/1')
        task = self.request()
        self.assertEqual(task['component'], 'text')
        for kind, key in [('text-verse', 'genesis/1/1'), ('text-chapter', 'genesis/1')]:
            subject = self.store.get_subject(self.admin, kind, key)
            self.assertEqual(subject['components']['text']['status'], 'correction-needed')
            for component, part in subject['components'].items():
                if component != 'text':
                    self.assertEqual(part['status'], 'approved', component)
            self.store.record_review(self.reviewer, self.review_payload(kind, key, ['notes']))
        after = self.store.get_subject(self.admin, 'text-verse', 'genesis/1/1')
        self.assertEqual(after['components']['notes']['latestReview'], before['components']['notes']['latestReview'])

    def test_notes_request_keeps_bible_text_verified_and_can_coexist(self):
        self.approve()
        notes = self.request('notes')
        subject = self.store.get_subject(self.reviewer, 'text-verse', 'genesis/1/1')
        self.assertEqual(subject['status'], 'approved')
        self.assertEqual(subject['components']['notes']['status'], 'correction-needed')
        self.assertEqual(self.store.verified_chapters(), {'genesis': [1]})
        self.store.record_review(self.reviewer, self.review_payload(components=['text']))
        with self.assertRaises(Conflict):
            self.store.record_review(self.reviewer, self.review_payload(components=['notes']))
        text = self.request('text')
        self.assertNotEqual(text['id'], notes['id'])
        self.assertEqual(len(self.store.get_subject(self.reviewer, 'text-verse', 'genesis/1/1')['corrections']), 2)
        with self.assertRaises(Conflict):
            self.request('notes')

    def test_custom_target_is_exported_but_not_misrepresented_as_text(self):
        self.approve()
        task = self.request('custom', 'De woordkoppeling naar de grondtekst')
        self.assertEqual(task['customTarget'], 'De woordkoppeling naar de grondtekst')
        self.assertEqual(self.service.export()['items'][0]['customTarget'], task['customTarget'])
        subject = self.store.get_subject(None, 'text-verse', 'genesis/1/1')
        self.assertNotIn('corrections', subject)
        self.assertTrue(all(p['status'] == 'approved' for p in subject['components'].values()))

    def test_scope_is_required_and_validated_at_the_boundary(self):
        for patch in ({'component': 'unknown'}, {'component': ['text', 'notes']},
                      {'component': 'intro'}, {'component': 'custom', 'customTarget': ' '},
                      {'customTarget': 'Not a custom scope'}, {'customTarget': None}):
            with self.subTest(patch=patch), self.assertRaises(InvalidRequest):
                self.service.create(self.reviewer, dict(self.payload(), **patch))
        payload = self.payload()
        del payload['component']
        with self.assertRaises(InvalidRequest):
            self.service.create(self.reviewer, payload)

    def test_rebase_keeps_selected_component(self):
        self.approve()
        task = self.request('notes')
        self.chapter['verses'][0]['marginNotes'] = [{'marker': '1', 'text2026': 'Uitleg'}]
        self.path.write_text(json.dumps(self.chapter))
        self.sync()
        task = self.decision(task, 'rebase', 'De uitleg blijft onduidelijk.')
        self.assertEqual(task['component'], 'notes')
        self.assertEqual(self.store.get_subject(None, 'text-chapter', 'genesis/1')['status'], 'approved')

    def test_note_publication_does_not_revoke_unchanged_text(self):
        from correction_files import apply_bundle
        self.approve()
        task = self.request('notes')
        after = copy.deepcopy(self.chapter)
        after['verses'][0]['marginNotes'] = [{'marker': '1', 'text2026': 'Betere uitleg'}]
        task = self.service.propose({'id': task['id'], 'version': task['version'], 'summary': 'Uitleg aangepast.',
            'files': [{'path': 'data/genesis/1.json', 'before': self.path.read_text(), 'after': json.dumps(after)}]})
        self.decision(task, 'accept')
        apply_bundle(self.root, self.service.export('accepted'))
        self.sync()
        self.service.reconcile()
        self.assertEqual(self.store.get_subject(None, 'text-chapter', 'genesis/1')['status'], 'approved')

    def test_old_requests_and_overbroad_revocations_are_migrated_once(self):
        self.approve()
        before = self.store.get_subject(self.admin, 'text-chapter', 'genesis/1')
        with patch('corrections.timestamp', return_value='2026-09-17T12:00:00Z'):
            task = self.request()
            with self.store._connect() as db:
                rows = db.execute("SELECT * FROM review_subjects WHERE source='data/genesis/1.json'").fetchall()
                self.service._revoke_rows(db, [(row, {'notes', 'markers', 'citations', 'layout', 'intro'})
                    for row in rows], self.reviewer, 'Aanpassing aangevraagd: ' + task['reason'])
        with self.store._connect() as db:
            events = [dict(row) for row in db.execute('SELECT * FROM review_events ORDER BY rowid')]
            db.execute('DROP INDEX correction_open_component')
            db.execute('ALTER TABLE corrections DROP COLUMN component')
            db.execute('ALTER TABLE corrections DROP COLUMN custom_target')
            db.execute("CREATE UNIQUE INDEX correction_open_subject ON corrections(subject_type,subject_id) WHERE status NOT IN ('applied','closed')")
            db.execute("DELETE FROM metadata WHERE key IN ('correction-scope-columns-v1','correction-review-scopes-v1')")
        self.store = fixtures.ReviewStore(self.store.database_path, {'admin@example.test'})
        self.service = fixtures.Corrections(self.store, self.root)
        self.sync()
        task = self.service.get(self.reviewer, task['id'])
        self.assertEqual(task['component'], 'text')
        self.assertEqual(task['customTarget'], '')
        after = self.store.get_subject(self.admin, 'text-chapter', 'genesis/1')
        self.assertEqual(after['components']['text']['status'], 'correction-needed')
        for key in ('notes', 'markers', 'citations', 'layout', 'intro'):
            self.assertEqual(after['components'][key], before['components'][key])
        self.sync()
        with self.store._connect() as db:
            self.assertEqual(events, [dict(row) for row in db.execute('SELECT * FROM review_events ORDER BY rowid')])
            self.assertEqual(db.execute("SELECT count(*) FROM correction_events WHERE kind='scope-migrated'").fetchone()[0], 1)
            with self.assertRaises(sqlite3.IntegrityError):
                db.execute('DELETE FROM review_components')

    def test_old_publication_revocations_preserve_unchanged_components(self):
        from correction_files import apply_bundle
        self.approve()
        task = self.request('custom', 'De uitleg')
        after = copy.deepcopy(self.chapter)
        after['verses'][0]['marginNotes'] = [{'marker': '1', 'text2026': 'Betere uitleg'}]
        task = self.service.propose({'id': task['id'], 'version': task['version'], 'summary': 'Uitleg aangepast.',
            'files': [{'path': 'data/genesis/1.json', 'before': self.path.read_text(), 'after': json.dumps(after)}]})
        self.decision(task, 'accept')
        apply_bundle(self.root, self.service.export('accepted'))
        self.sync()
        revoke = self.service._revoke_rows
        def old_revoke(db, rows, actor, note):
            return revoke(db, [(row, set(json.loads(row['metadata_json'])['components'])) for row, _ in rows], actor, note)
        with patch.object(self.service, '_revoke_rows', side_effect=old_revoke):
            self.service.reconcile()
        self.assertEqual(self.store.get_subject(None, 'text-chapter', 'genesis/1')['status'], 'pending')
        with self.store._connect() as db:
            db.execute("DELETE FROM metadata WHERE key='correction-review-scopes-v1'")
        self.sync()
        self.assertEqual(self.store.get_subject(None, 'text-chapter', 'genesis/1')['status'], 'approved')
        self.assertEqual(self.service.get(self.reviewer, task['id'])['status'], 'applied')


if __name__ == '__main__':
    unittest.main()
