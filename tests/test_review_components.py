import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'server'))
from review_components import component_metadata
import test_corrections as fixtures


class ComponentContentTests(unittest.TestCase):
    def setUp(self):
        self.chapter = {'number': 1, 'chapterIntro': {'text2026': 'Inleiding'}, 'verses': [{
            'number': 1, 'text2026': 'God sprak.',
            'text2026_html': ' <span class="god-speaks"><i>God <sup class="note-marker" data-note="a">a</sup>sprak.</i></span>',
            'marginNotes': [{'marker': 'a', 'type': 'explanation', 'text2026': 'Een noot.'}],
        }]}

    def changed(self, after):
        before = component_metadata('text-chapter', self.chapter)
        after = component_metadata('text-chapter', after)
        return {key for key in before if before[key]['revision'] != after[key]['revision']}

    def test_marker_change_is_not_a_text_or_citation_change(self):
        after = copy.deepcopy(self.chapter)
        after['verses'][0]['text2026_html'] = after['verses'][0]['text2026_html'].replace('data-note="a">a', 'data-note="b">b')
        self.assertEqual(self.changed(after), {'markers'})

    def test_notes_are_separate_from_text(self):
        after = copy.deepcopy(self.chapter)
        after['verses'][0]['marginNotes'][0]['text2026'] = 'Andere uitleg.'
        self.assertEqual(self.changed(after), {'notes'})

    def test_citations_are_separate_from_text_and_markers(self):
        after = copy.deepcopy(self.chapter)
        after['verses'][0]['text2026_html'] = after['verses'][0]['text2026_html'].replace('god-speaks', 'direct-speech')
        self.assertEqual(self.changed(after), {'citations'})

    def test_html_word_changes_cannot_keep_text_approval(self):
        after = copy.deepcopy(self.chapter)
        after['verses'][0]['text2026_html'] = after['verses'][0]['text2026_html'].replace('God ', 'Hij ')
        self.assertIn('text', self.changed(after))

    def test_whitespace_and_intro_are_independent(self):
        after = copy.deepcopy(self.chapter)
        after['verses'][0]['text2026_html'] = after['verses'][0]['text2026_html'].strip()
        self.assertEqual(self.changed(after), set())
        after['chapterIntro']['text2026'] = 'Andere inleiding'
        self.assertEqual(self.changed(after), {'intro'})


class ComponentStoreTests(unittest.TestCase):
    setUp = fixtures.CorrectionsTests.setUp
    user = fixtures.CorrectionsTests.user
    sync = fixtures.CorrectionsTests.sync

    def approve(self, actor=None, keys=None):
        current = self.store.get_subject(self.admin, 'text-chapter', 'genesis/1')
        return self.store.record_review(actor or self.admin, {
            'subjectType': current['type'], 'subjectId': current['id'], 'revision': current['revision'],
            'sourceHash': current['metadata']['sourceHash'], 'decision': 'approved',
            'components': {key: part['revision'] for key, part in current['components'].items()
                           if keys is None or key in keys}})

    def publish(self):
        self.path.write_text(fixtures.json.dumps(self.chapter))
        self.sync()
        return self.store.get_subject(self.admin, 'text-chapter', 'genesis/1')

    def test_marker_changes_preserve_text_notes_and_their_responsible_person(self):
        before = self.approve()
        self.chapter['verses'][0]['text2026_html'] += '<sup class="note-marker" data-note="1">1</sup>'
        after = self.publish()
        self.assertEqual(after['status'], 'approved')
        self.assertEqual(after['components']['text']['latestReview'], before['components']['text']['latestReview'])
        self.assertEqual(after['components']['markers']['status'], 'pending')
        self.assertTrue(after['components']['markers']['needsReverification'])
        self.assertEqual(self.store.verified_chapters(), {'genesis': [1]})

    def test_review_only_covers_selected_components(self):
        self.approve(keys=['text'])
        after = self.store.get_subject(None, 'text-chapter', 'genesis/1')
        self.assertEqual(after['components']['text']['status'], 'approved')
        self.assertEqual(after['components']['notes']['status'], 'pending')
        self.assertNotIn('actor', fixtures.json.dumps(after))
        self.assertEqual(self.store.list_review_events(self.admin)['items'][0]['components'], ['text'])
        # A second reviewer does not take over the first reviewer's text approval.
        after = self.approve(actor=self.reviewer, keys=['text', 'notes'])
        current = self.store.get_subject(self.admin, 'text-chapter', 'genesis/1')
        self.assertEqual(current['components']['text']['latestReview']['actor']['uid'], self.admin['uid'])
        self.assertEqual(current['components']['notes']['latestReview']['actor']['uid'], self.reviewer['uid'])

    def test_chapter_review_also_covers_unchanged_verse_additions(self):
        self.approve()
        self.chapter['verses'][0]['marginNotes'] = [{'marker': 'a', 'text2026': 'Nieuwe noot'}]
        self.publish()
        first = self.store.get_subject(None, 'text-verse', 'genesis/1/1')
        second = self.store.get_subject(None, 'text-verse', 'genesis/1/2')
        self.assertEqual(first['components']['notes']['status'], 'pending')
        self.assertTrue(first['components']['notes']['needsReverification'])
        self.assertEqual(second['components']['notes']['status'], 'approved')
        self.assertEqual(first['components']['text']['status'], 'approved')

    def test_citations_and_html_words_are_independent(self):
        self.approve()
        self.chapter['verses'][0]['text2026_html'] = '<span class="god-speaks"><i>Oude tekst.</i></span>'
        current = self.publish()
        self.assertEqual(current['status'], 'approved')
        self.assertEqual(current['components']['citations']['status'], 'pending')
        self.chapter['verses'][0]['text2026_html'] = '<span class="god-speaks"><i>Nieuwe tekst.</i></span>'
        self.assertEqual(self.publish()['status'], 'pending')

    def test_stale_component_selection_is_rejected(self):
        current = self.store.get_subject(self.admin, 'text-chapter', 'genesis/1')
        with self.assertRaises(fixtures.Conflict):
            self.store.record_review(self.admin, {
                'subjectType': current['type'], 'subjectId': current['id'], 'revision': current['revision'],
                'sourceHash': current['metadata']['sourceHash'], 'decision': 'approved', 'components': {'text': '0' * 64}})

    def test_verse_revocation_invalidates_parent_until_a_newer_review(self):
        self.approve()
        verse = self.store.get_subject(self.admin, 'text-verse', 'genesis/1/1')
        self.store.record_review(self.admin, {
            'subjectType': verse['type'], 'subjectId': verse['id'], 'revision': verse['revision'],
            'sourceHash': verse['metadata']['sourceHash'], 'decision': 'revoked',
            'components': {'text': verse['components']['text']['revision']}})
        self.assertEqual(self.store.verified_chapters(), {})
        self.approve(keys=['text'])
        self.assertEqual(self.store.verified_chapters(), {'genesis': [1]})
        self.assertEqual(self.store.get_subject(None, 'text-verse', 'genesis/1/1')['status'], 'approved')

    def test_versioned_migration_preserves_audit_identity_without_new_approval(self):
        import component_reviews
        before = self.approve()
        with self.store._connect() as db:
            history = [dict(row) for row in db.execute('SELECT * FROM review_events')]
            db.executescript('DROP TABLE review_components;')
            db.execute("DELETE FROM metadata WHERE key='component-reviews-v1'")
            db.executescript(component_reviews.SCHEMA)
            old = {**before, 'metadata': before['metadata']}
            self.chapter['verses'][0]['text2026_html'] += '<sup class="note-marker">a</sup>'
            new = {'type': 'text-chapter', 'id': 'genesis/1', 'revision': 'new',
                   'metadata': {'components': component_metadata('text-chapter', self.chapter)}}
            catalog = {'subjects': [new], 'historicalSubjects': [], 'componentHistory': [old]}
            component_reviews.migrate(db, catalog)
            component_reviews.migrate(db, catalog)
            self.assertEqual([dict(row) for row in db.execute('SELECT * FROM review_events')], history)
            self.assertEqual(db.execute('SELECT count(*) FROM review_components').fetchone()[0], 6)
        self.assertEqual(self.publish()['components']['markers']['status'], 'pending')
