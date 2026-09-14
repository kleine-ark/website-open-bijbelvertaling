"""Historical attribution and first Google sign-in must share one stable account."""
import importlib.util
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "collaboration_tests", Path(__file__).with_name("test_collaboration_system.py")
)
fixtures = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixtures)
api = fixtures.api_module

MAARTEN = "maartenvroegindeweij@gmail.com"


class GhostVerificationTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "reviews.sqlite3"
        self.admins = {MAARTEN, "admin@example.test"}
        self.store = api.ReviewStore(self.path, self.admins)
        self.admin = self.store.upsert_user(self.claims("admin", "admin@example.test", "Admin"))
        subjects = [{
            "type": kind, "id": identifier, "revision": "a" * 64,
            "label": identifier, "href": "index.html", "source": "data/test.json",
            "metadata": {"sourceHash": "b" * 64},
        } for kind, identifier in [
            ("text-chapter", "genesis/1"), ("text-verse", "genesis/1/1"), ("location", "geo-test"),
        ]]
        self.catalog = {
            "schemaVersion": 2,
            "subjectTypes": {item["type"]: item["type"] for item in subjects},
            "subjects": subjects,
            "historicalSubjects": [dict(item, migrationSource="confirmed historical reviews") for item in subjects],
        }
        self.catalog["catalogRevision"] = api.review_catalog_revision(self.catalog)
        self.store.sync_catalog(self.catalog)

    @staticmethod
    def claims(uid="google-maarten", email=MAARTEN, name="Maarten Vroegindeweij"):
        return {"sub": uid, "email": email, "name": name, "email_verified": True}

    def ghost(self):
        result = self.store.list_users(self.admin, MAARTEN)
        self.assertEqual(result["total"], 1)
        return result["items"][0]

    def test_all_historical_types_are_verified_by_the_unregistered_account(self):
        ghost = self.ghost()
        self.assertFalse(ghost["registered"])
        self.assertEqual(ghost["displayName"], "Maarten Vroegindeweij")
        for item in self.catalog["subjects"]:
            subject = self.store.get_subject(self.admin, item["type"], item["id"])
            self.assertEqual(subject["status"], "approved")
            self.assertEqual(subject["latestReview"]["actor"], {
                "kind": "historical-import", "uid": ghost["uid"], "email": MAARTEN,
                "displayName": "Maarten Vroegindeweij", "registered": False,
            })
        self.assertEqual(self.store.verified_chapters(), {"genesis": [1]})
        with self.assertRaises(api.Forbidden):
            self.store.list_users(ghost)

    def test_first_signin_claims_the_same_account_without_rewriting_audit(self):
        before = self.ghost()
        self.store.set_roles(self.admin, before["uid"], ["reviewer"])
        with self.store._connect() as db:
            events = [tuple(row) for row in db.execute("SELECT * FROM review_events ORDER BY rowid")]
            roles = [tuple(row) for row in db.execute("SELECT * FROM role_events ORDER BY rowid")]
        signed_in = self.store.upsert_user(self.claims())
        self.assertEqual(signed_in["uid"], before["uid"])
        self.assertEqual(signed_in["createdAt"], before["createdAt"])
        self.assertEqual(signed_in["roles"], before["roles"])
        self.assertTrue(signed_in["registered"])
        self.assertEqual(self.ghost()["uid"], signed_in["uid"])
        self.assertEqual(self.store.upsert_user(self.claims())["uid"], before["uid"])
        history = self.store.list_review_events(signed_in)
        self.assertTrue(all(event["actor"]["registered"] for event in history["items"]))
        self.assertTrue(all(event["actor"]["uid"] == signed_in["uid"] for event in history["items"]))
        with self.store._connect() as db:
            self.assertEqual(events, [tuple(row) for row in db.execute("SELECT * FROM review_events ORDER BY rowid")])
            self.assertEqual(roles, [tuple(row) for row in db.execute("SELECT * FROM role_events ORDER BY rowid")])
            with self.assertRaises(sqlite3.IntegrityError):
                db.execute("UPDATE review_events SET actor_name='changed'")

    def test_name_or_unverified_email_cannot_claim_the_ghost(self):
        before = self.ghost()
        stranger = self.store.upsert_user(self.claims("stranger", "stranger@example.test"))
        self.assertNotEqual(stranger["uid"], before["uid"])
        self.assertFalse(self.ghost()["registered"])
        with self.assertRaises(api.Unauthorized):
            self.store.upsert_user(dict(self.claims(), email_verified=False))
        self.assertFalse(self.ghost()["registered"])

    def test_different_google_uid_cannot_replace_an_already_linked_identity(self):
        signed_in = self.store.upsert_user(self.claims())
        with self.assertRaises(api.Unauthorized):
            self.store.upsert_user(self.claims("different-google-uid"))
        self.assertEqual(self.ghost()["uid"], signed_in["uid"])

    def test_historical_identity_is_private_before_and_after_signin(self):
        reviewer = self.store.upsert_user(self.claims("reader", "reader@example.test", "Reader"))
        reviewer = self.store.set_roles(self.admin, reviewer["uid"], ["reviewer"])
        for signed_in in (False, True):
            if signed_in:
                self.store.upsert_user(self.claims())
            for actor in (None, reviewer):
                subject = self.store.get_subject(actor, "text-chapter", "genesis/1")
                self.assertEqual(subject["status"], "approved")
                self.assertNotIn("latestReview", subject)
                self.assertNotIn(MAARTEN, json.dumps(subject))
            self.assertNotIn(MAARTEN, json.dumps(self.store.list_subjects(reviewer)))

    def test_repeat_approval_does_not_replace_maarten_but_revocation_does(self):
        payload = {"subjectType": "text-chapter", "subjectId": "genesis/1",
                   "revision": "a" * 64, "sourceHash": "b" * 64, "decision": "approved"}
        original = self.store.get_subject(self.admin, "text-chapter", "genesis/1")["latestReview"]
        repeated = self.store.record_review(self.admin, payload)
        self.assertEqual(repeated["latestReview"]["id"], original["id"])
        self.store.record_review(self.admin, dict(payload, decision="revoked"))
        self.assertEqual(self.store.verified_chapters(), {})
        approval = self.store.record_review(self.admin, payload)
        self.assertEqual(approval["latestReview"]["actor"]["uid"], self.admin["uid"])

    def test_changed_historical_content_needs_reverification(self):
        self.catalog["subjects"][0]["revision"] = "c" * 64
        self.catalog["catalogRevision"] = api.review_catalog_revision(self.catalog)
        self.store.sync_catalog(self.catalog)
        subject = self.store.get_subject(self.admin, "text-chapter", "genesis/1")
        self.assertEqual(subject["status"], "pending")
        self.assertTrue(subject["needsReverification"])
        self.assertEqual(self.store.verified_chapters(), {})

    def make_v2_database(self):
        """Recreate the previous schema, unknown imports and replaced placeholder IDs."""
        with self.store._connect() as db:
            for table in ("role_events", "review_events"):
                db.execute(f"DROP TRIGGER immutable_{table}_update")
            db.execute("""UPDATE review_events SET actor_uid=NULL, actor_email=NULL,
                          actor_name='Onbekend (bestaande reviewstatus)'
                          WHERE actor_kind='historical-import'""")
            # The former login implementation replaced users.uid, leaving any
            # audit references to a pre-sign-in placeholder behind.
            db.execute("UPDATE users SET uid=firebase_uid WHERE registered=1")
            db.execute("UPDATE users SET display_name=email WHERE registered=0")
            db.execute("DROP INDEX users_firebase_uid")
            db.execute("ALTER TABLE users DROP COLUMN firebase_uid")
            db.execute("""DELETE FROM metadata WHERE key IN
                          ('account-identity-v1', 'historical-review-attribution-v3')""")
            db.execute("INSERT INTO metadata VALUES ('historical-review-import-v1', 'old')")
            for table in ("role_events", "review_events"):
                db.execute(f"""CREATE TRIGGER immutable_{table}_update BEFORE UPDATE ON {table}
                               BEGIN SELECT RAISE(ABORT, '{table} are immutable'); END""")

    def restart(self):
        self.store = api.ReviewStore(self.path, self.admins)
        self.admin = self.store.upsert_user(self.claims("admin", "admin@example.test", "Admin"))
        self.store.sync_catalog(self.catalog)

    def test_existing_v2_database_migrates_all_imports_once_with_unchanged_catalog(self):
        self.store.set_roles(self.admin, self.ghost()["uid"], ["reviewer"])
        with self.store._connect() as db:
            original = [tuple(row) for row in db.execute(
                "SELECT rowid,id,subject_type,subject_id,revision,decision,note,created_at FROM review_events"
            )]
        self.make_v2_database()
        for _ in range(2):
            self.restart()
            self.assertEqual(self.store.verified_chapters(), {"genesis": [1]})
            history = self.store.list_review_events(self.admin)
            self.assertEqual(history["total"], 3)
            self.assertTrue(all(event["actor"]["uid"] == self.ghost()["uid"] for event in history["items"]))
            with self.store._connect() as db:
                self.assertEqual(original, [tuple(row) for row in db.execute(
                    "SELECT rowid,id,subject_type,subject_id,revision,decision,note,created_at FROM review_events"
                )])
                self.assertEqual(db.execute("PRAGMA integrity_check").fetchone()[0], "ok")
                for table in ("review_events", "role_events"):
                    with self.assertRaises(sqlite3.IntegrityError):
                        db.execute(f"UPDATE {table} SET id='changed'")

    def test_migration_reuses_already_signed_in_maarten_and_repairs_role_targets(self):
        ghost_uid = self.ghost()["uid"]
        self.store.set_roles(self.admin, ghost_uid, ["reviewer"])
        self.store.upsert_user(self.claims())
        self.make_v2_database()
        self.restart()
        maarten = self.store.upsert_user(self.claims())
        self.assertEqual(maarten["uid"], "google-maarten")
        self.assertEqual(self.ghost()["uid"], maarten["uid"])
        role = self.store.list_role_events(self.admin)[0]
        self.assertEqual(role["targetUid"], maarten["uid"])
        self.assertEqual(role["actor"]["uid"], self.admin["uid"])
        history = self.store.list_review_events(self.admin)
        self.assertTrue(all(event["actor"]["uid"] == maarten["uid"] for event in history["items"]))
        self.assertTrue(all(event["actor"]["registered"] for event in history["items"]))

    def test_migration_preserves_later_named_decisions_and_their_order(self):
        payload = {"subjectType": "text-chapter", "subjectId": "genesis/1",
                   "revision": "a" * 64, "sourceHash": "b" * 64, "decision": "revoked"}
        revoked = self.store.record_review(self.admin, payload)["latestReview"]
        location = dict(payload, subjectType="location", subjectId="geo-test")
        self.store.record_review(self.admin, location)
        approved = self.store.record_review(self.admin, dict(location, decision="approved"))["latestReview"]
        self.make_v2_database()
        self.restart()
        chapter = self.store.get_subject(self.admin, "text-chapter", "genesis/1")
        place = self.store.get_subject(self.admin, "location", "geo-test")
        self.assertEqual(chapter["status"], "pending")
        self.assertEqual(chapter["latestReview"]["id"], revoked["id"])
        self.assertEqual(place["status"], "approved")
        self.assertEqual(place["latestReview"]["id"], approved["id"])
        self.assertEqual(place["latestReview"]["actor"]["uid"], self.admin["uid"])
        self.assertEqual(self.store.verified_chapters(), {})


if __name__ == "__main__":
    unittest.main()
