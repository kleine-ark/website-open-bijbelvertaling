"""A verse correction must not revoke unrelated verses through their chapter."""
import json
import unittest
from unittest.mock import patch

import test_corrections as fixtures


class VerseScopeTests(unittest.TestCase):
    setUp = fixtures.CorrectionsTests.setUp
    user = fixtures.CorrectionsTests.user
    sync = fixtures.CorrectionsTests.sync
    payload = fixtures.CorrectionsTests.payload
    review_payload = fixtures.CorrectionsTests.review_payload
    decision = fixtures.CorrectionsTests.decision
    propose = fixtures.CorrectionsTests.propose

    def state(self, number=None):
        kind = 'text-chapter' if number is None else 'text-verse'
        return self.store.get_subject(self.admin, kind, 'genesis/1' + (f'/{number}' if number else ''))

    def approve(self, number=None):
        kind = 'text-chapter' if number is None else 'text-verse'
        return self.store.record_review(self.admin, self.review_payload(kind, 'genesis/1' + (f'/{number}' if number else '')))

    def request(self, number=1, component='text'):
        kind = 'text-chapter' if number is None else 'text-verse'
        return self.service.create(self.reviewer, dict(self.payload(kind,
            'genesis/1' + (f'/{number}' if number else '')), component=component))

    def test_request_keeps_other_verse_identity_and_chapter_approval_record(self):
        chapter = self.approve()
        other = self.state(2)
        task = self.request()
        self.assertEqual(self.state(1)['status'], 'correction-needed')
        self.assertEqual(self.state()['status'], 'correction-needed')
        self.assertEqual(self.state(2)['components'], other['components'])
        self.decision(task, 'close', 'Test afgerond.')
        self.assertEqual(self.state()['status'], 'pending')
        self.approve(1)
        self.assertEqual(self.state()['status'], 'approved')
        self.assertEqual(self.state()['latestReview'], chapter['latestReview'])
        self.assertEqual(self.store.verified_chapters(), {'genesis': [1]})

    def test_two_requests_remain_independent_until_both_are_reviewed(self):
        self.approve()
        first, second = self.request(1), self.request(2)
        self.decision(first, 'close', 'Eerste afgerond.')
        self.approve(1)
        self.assertEqual(self.state(1)['status'], 'approved')
        self.assertEqual(self.state(2)['status'], 'correction-needed')
        self.assertEqual(self.state()['status'], 'correction-needed')
        self.decision(second, 'close', 'Tweede afgerond.')
        self.approve(2)
        self.assertEqual(self.state()['status'], 'approved')

    def test_an_actual_chapter_request_still_covers_all_verses(self):
        self.approve()
        self.request(None)
        self.migrate()
        for number in (None, 1, 2):
            self.assertEqual(self.state(number)['status'], 'correction-needed')

    def test_rebase_and_publication_leave_the_other_verse_verified(self):
        self.approve()
        other = self.state(2)
        task = self.request()
        task = self.decision(task, 'rebase', 'Nogmaals controleren.')
        self.assertEqual(self.state(2)['components'], other['components'])
        task = self.propose(task)
        self.decision(task, 'accept')
        fixtures.apply_bundle(self.root, self.service.export('accepted'))
        self.sync()
        self.service.reconcile()
        self.assertEqual(self.state(2)['components'], other['components'])
        self.assertEqual(self.state(1)['status'], 'pending')

    def old_request(self, number=1):
        def old_revoke(db, subject, actor, note, component):
            rows = db.execute("""SELECT * FROM review_subjects WHERE active=1 AND source=?
                AND (subject_type='text-chapter' OR (subject_type=? AND subject_id=?))
                ORDER BY subject_type""", (subject['source'], subject['subject_type'], subject['subject_id'])).fetchall()
            return self.service._revoke_rows(db, [(row, {component}) for row in rows], actor,
                                             'Aanpassing aangevraagd: ' + note)
        with patch.object(self.service, '_revoke_affected', side_effect=old_revoke):
            return self.request(number)

    def migrate(self):
        with self.store._connect() as db:
            db.execute("DELETE FROM metadata WHERE key='correction-verse-scopes-v1'")
        self.sync()

    def test_migration_restores_other_verses_without_replacing_any_review(self):
        chapter = self.approve()
        before = self.state(2)
        task = self.old_request()
        self.assertEqual(self.state(2)['status'], 'pending')
        with self.store._connect() as db:
            events = [dict(row) for row in db.execute('SELECT * FROM review_events ORDER BY rowid')]
        self.migrate()
        self.assertEqual(self.state(2)['components'], before['components'])
        self.assertEqual(self.state(1)['status'], 'correction-needed')
        self.decision(task, 'close', 'Afgerond.')
        self.assertEqual(self.state(1)['status'], 'pending')
        self.approve(1)
        self.assertEqual(self.state()['status'], 'approved')
        self.assertEqual(self.state()['latestReview'], chapter['latestReview'])
        with self.store._connect() as db:
            self.assertEqual(events, [dict(row) for row in db.execute(
                'SELECT * FROM review_events ORDER BY rowid LIMIT ?', (len(events),))])
            self.assertEqual(db.execute("SELECT count(*) FROM correction_events WHERE kind='verse-scope-migrated'").fetchone()[0], 1)
            with self.assertRaises(fixtures.sqlite3.IntegrityError):
                db.execute('UPDATE review_components SET members_json=members_json')
        self.sync()
        with self.store._connect() as db:
            self.assertEqual(db.execute("SELECT count(*) FROM correction_events WHERE kind='verse-scope-migrated'").fetchone()[0], 1)

    def test_migration_does_not_overwrite_later_individual_approval_or_revocation(self):
        for decision in ('approved', 'revoked'):
            with self.subTest(decision=decision):
                self.setUp()
                self.approve()
                self.old_request()
                self.approve(2)
                if decision == 'revoked':
                    self.store.record_review(self.admin, dict(self.review_payload('text-verse', 'genesis/1/2'), decision='revoked'))
                before = self.state(2)
                self.migrate()
                self.assertEqual(self.state(2)['components'], before['components'])

    def test_migration_keeps_a_later_request_that_was_masked_by_the_first(self):
        self.approve()
        first, second = self.old_request(1), self.old_request(2)
        self.decision(second, 'close', 'Moet nog geverifieerd worden.')
        self.migrate()
        self.assertEqual(self.state(2)['status'], 'pending')
        self.decision(first, 'close', 'Afgerond.')
        self.approve(1)
        self.assertEqual(self.state()['status'], 'pending')
        self.approve(2)
        self.assertEqual(self.state()['status'], 'approved')

    def test_migration_handles_requests_from_before_review_id_provenance(self):
        self.approve()
        self.old_request()
        with self.store._connect() as db:
            db.execute('DROP TRIGGER immutable_correction_events_update')
            for event in db.execute("SELECT id,data_json FROM correction_events WHERE kind='requested'").fetchall():
                data = json.loads(event['data_json'])
                del data['reviewEventIds']
                db.execute('UPDATE correction_events SET data_json=? WHERE id=?', (json.dumps(data), event['id']))
            db.execute("""CREATE TRIGGER immutable_correction_events_update BEFORE UPDATE ON correction_events
                BEGIN SELECT RAISE(ABORT, 'Immutable correction audit'); END""")
        self.migrate()
        self.assertEqual(self.state(1)['status'], 'correction-needed')
        self.assertEqual(self.state(2)['status'], 'approved')
        repaired = [e for e in self.store.list_review_events(self.admin)['items'] if e['verseScopes']]
        self.assertEqual(len(repaired), 1)
        self.assertEqual(repaired[0]['verseScopes'], {'text': [1]})

    def test_old_publication_of_an_approved_revision_is_scoped_to_changed_verses(self):
        original = self.path.read_text()
        future = json.loads(original)
        future['verses'][0].update(text2026='Nieuwe tekst.', text2026_html='Nieuwe tekst.')
        self.path.write_text(json.dumps(future))
        self.sync()
        self.approve()
        self.path.write_text(original)
        self.sync()
        self.approve()
        task = self.propose(self.old_request())
        self.decision(task, 'accept')
        fixtures.apply_bundle(self.root, self.service.export('accepted'))
        self.sync()
        with self.store._connect() as db:
            rows = db.execute("SELECT * FROM review_subjects WHERE active=1 AND source='data/genesis/1.json' ORDER BY subject_type").fetchall()
            self.service._revoke_rows(db, [(r, {'text'}) for r in rows if r['subject_id'] != 'genesis/1/2'],
                self.reviewer, 'Correctie gepubliceerd; de gewijzigde versie moet opnieuw worden geverifieerd.')
        self.service.reconcile()
        self.assertEqual(self.state(2)['status'], 'pending')
        self.migrate()
        self.assertEqual(self.state(2)['status'], 'approved')
        self.assertEqual(self.state(1)['status'], 'pending')
        self.assertEqual(self.state()['status'], 'pending')
        self.approve(1)
        self.assertEqual(self.state()['status'], 'approved')

    def test_component_scope_column_upgrade_preserves_records(self):
        self.approve()
        with self.store._connect() as db:
            before = [dict(r) for r in db.execute('SELECT * FROM review_events')]
            db.execute('ALTER TABLE review_components DROP COLUMN scope')
            db.execute("DELETE FROM metadata WHERE key='review-component-scope-v1'")
        self.store = fixtures.ReviewStore(self.store.database_path, {'admin@example.test'})
        with self.store._connect() as db:
            self.assertEqual(before, [dict(r) for r in db.execute('SELECT * FROM review_events')])
            self.assertEqual({r[0] for r in db.execute('SELECT scope FROM review_components')}, {'subject'})


if __name__ == '__main__':
    unittest.main()
