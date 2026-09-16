"""Behavioral tests for account-linked, private, one-click verification."""
import importlib.util
import json
from component_fixtures import fingerprint_catalog
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "collaboration_tests", Path(__file__).with_name("test_collaboration_system.py")
)
fixtures = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixtures)
api = fixtures.api_module


class DirectVerificationTests(fixtures.CollaborationStoreTests):
    def approve(self, actor=None):
        return self.store.record_review(actor or self.admin, {
            "subjectType": "location", "subjectId": "geo-jerusalem",
            "revision": "b" * 64, "sourceHash": "b" * 64, "decision": "approved", "note": "",
        })

    def test_identity_is_only_returned_to_administrators(self):
        self.approve()
        reviewer = self.store.set_roles(self.admin, "reader", ["reviewer"])
        response = self.store.list_subjects(reviewer)
        serialized = json.dumps(response)
        self.assertNotIn(self.admin["email"], serialized)
        self.assertNotIn('"actor"', serialized)
        self.assertNotIn('"note"', serialized)
        result = self.store.get_subject(None, "location", "geo-jerusalem")
        self.assertEqual(result["status"], "approved")
        self.assertNotIn("latestReview", result)
        self.assertEqual(
            self.store.get_subject(self.admin, "location", "geo-jerusalem")
            ["latestReview"]["actor"]["uid"], self.admin["uid"]
        )
        with self.assertRaises(api.Forbidden):
            self.store.list_review_events(reviewer)

    def test_click_uses_session_identity_and_retries_do_not_create_events(self):
        first = self.approve()
        second = self.approve()
        self.assertEqual(first["latestReview"]["id"], second["latestReview"]["id"])
        reviewer = self.store.set_roles(self.admin, "reader", ["reviewer"])
        result = self.approve(reviewer)
        self.assertNotIn("latestReview", result)
        self.assertEqual(
            self.store.get_subject(self.admin, "location", "geo-jerusalem")
            ["latestReview"]["actor"]["uid"], self.admin["uid"]
        )

    def test_old_actor_cannot_keep_using_revoked_permission(self):
        reviewer = self.store.set_roles(self.admin, "reader", ["reviewer"])
        self.store.set_roles(self.admin, "reader", [])
        with self.assertRaises(api.Forbidden):
            self.approve(reviewer)

    def test_changed_content_requires_reverification_but_preserves_history(self):
        self.approve()
        self.catalog["subjects"][1]["revision"] = "c" * 64
        self.catalog["catalogRevision"] = fingerprint_catalog(self.catalog)
        self.store.sync_catalog(self.catalog)
        current = self.store.get_subject(self.admin, "location", "geo-jerusalem")
        self.assertEqual(current["status"], "pending")
        self.assertTrue(current["needsReverification"])
        self.assertIsNone(current["latestReview"])
        with self.assertRaises(api.Conflict):
            self.approve()
        self.assertTrue(any(
            event["actor"]["uid"] == self.admin["uid"]
            for event in self.store.list_review_events(self.admin)["items"]
        ))

    def test_public_chapter_status_comes_from_current_decisions(self):
        # Confirmed historical reviews count for their unchanged content revision.
        self.assertEqual(self.store.verified_chapters(), {"genesis": [1]})
        self.store.record_review(self.admin, {
            "subjectType": "text-chapter", "subjectId": "genesis/1",
            "revision": "a" * 64, "sourceHash": "a" * 64, "decision": "approved", "note": "",
        })
        self.assertEqual(self.store.verified_chapters(), {"genesis": [1]})
        self.store.record_review(self.admin, {
            "subjectType": "text-chapter", "subjectId": "genesis/1",
            "revision": "a" * 64, "sourceHash": "a" * 64, "decision": "revoked", "note": "",
        })
        self.assertEqual(self.store.verified_chapters(), {})

    def test_forged_identity_is_rejected(self):
        with self.assertRaises(api.InvalidRequest):
            self.store.record_review(self.admin, {
                "subjectType": "location", "subjectId": "geo-jerusalem",
                "revision": "b" * 64, "sourceHash": "b" * 64, "decision": "approved", "note": "",
                "verifierUid": "reader",
            })

    def test_source_hash_must_match_the_content_the_user_loaded(self):
        with self.assertRaises(api.Conflict):
            self.store.record_review(self.admin, {
                "subjectType": "location", "subjectId": "geo-jerusalem",
                "revision": "b" * 64, "sourceHash": "c" * 64,
                "decision": "approved",
            })

    def test_stale_administrator_profile_cannot_read_private_identity(self):
        self.store.set_roles(self.admin, "reader", ["administrator"])
        profile = self.store._require_role(self.user, "administrator")
        self.approve()
        self.store.set_roles(self.admin, "reader", ["reviewer"])
        self.assertNotIn("latestReview", self.store.get_subject(profile, "location", "geo-jerusalem"))

    def test_migration_is_idempotent_and_survives_restarts(self):
        original = self.store.list_review_events(self.admin)["total"]
        with self.store._connect() as db:
            db.execute("DELETE FROM metadata WHERE key='historical-review-import-v3'")
            db.execute("DELETE FROM metadata WHERE key='catalog-revision'")
            db.execute("INSERT INTO metadata VALUES ('historical-review-import-v1', 'old')")
        self.catalog["subjects"][0]["revision"] = "d" * 64
        self.catalog["catalogRevision"] = fingerprint_catalog(self.catalog)
        restarted = api.ReviewStore(Path(self.directory.name) / "reviews.sqlite3", self.store.bootstrap_admins)
        restarted.sync_catalog(self.catalog)
        self.assertEqual(restarted.list_review_events(self.admin)["total"], original)
        self.assertEqual(restarted.verified_chapters(), {})
        self.assertEqual(restarted.get_subject(self.admin, "text-chapter", "genesis/1")["status"], "pending")

    def test_export_rejects_a_catalog_from_another_release(self):
        with self.assertRaises(api.Conflict):
            self.store.verified_chapters("f" * 64)
        self.assertEqual(self.store.verified_chapters(self.catalog["catalogRevision"]), {"genesis": [1]})

    def test_v3_import_adds_later_completed_chapters_to_an_existing_v2_store_once(self):
        before = self.store.list_review_events(self.admin)["total"]
        with self.store._connect() as db:
            db.execute("DELETE FROM metadata WHERE key='historical-review-import-v3'")
            db.execute("INSERT INTO metadata VALUES ('historical-review-import-v2', 'old')")
        chapter = dict(self.catalog["subjects"][0], id="genesis/2", label="Genesis 2")
        self.catalog["subjects"].append(chapter)
        self.catalog["historicalSubjects"].append(dict(chapter))
        self.catalog["catalogRevision"] = fingerprint_catalog(self.catalog)
        self.store.sync_catalog(self.catalog)
        self.assertEqual(self.store.verified_chapters(), {"genesis": [1, 2]})
        self.assertEqual(self.store.list_review_events(self.admin)["total"], before + 1)
        restarted = api.ReviewStore(Path(self.directory.name) / "reviews.sqlite3", self.store.bootstrap_admins)
        restarted.sync_catalog(self.catalog)
        self.assertEqual(restarted.list_review_events(self.admin)["total"], before + 1)

    def test_imported_history_cannot_supersede_an_existing_named_verification(self):
        approval = self.approve()
        self.catalog["historicalSubjects"].append(dict(self.catalog["subjects"][1]))
        self.catalog["catalogRevision"] = fingerprint_catalog(self.catalog)
        with self.store._connect() as db:
            db.execute("DELETE FROM metadata WHERE key='historical-review-import-v3'")
        self.store.sync_catalog(self.catalog)
        subject = self.store.get_subject(self.admin, "location", "geo-jerusalem")
        self.assertEqual(subject["status"], "approved")
        self.assertEqual(subject["latestReview"]["id"], approval["latestReview"]["id"])


if __name__ == "__main__":
    unittest.main()
