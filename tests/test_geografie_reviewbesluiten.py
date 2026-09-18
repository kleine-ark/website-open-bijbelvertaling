"""Bewaar inhoudelijke beslissingen zonder oude of tegenstrijdige bevestigingen."""

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / "scripts" / "geografie_reviewbesluiten.py"
TEXT = "Hij kwam uit Kana in Galilea."


class GeografieReviewTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.directory = Path(self.tmp.name)
        self.features = {"geo-kana": {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [35.3, 32.7]},
            "properties": {"id": "geo-kana", "naam": "Cana", "zekerheid": "onzeker",
                           "humanReviewed": False, "aliases": [],
                           "refs": [{"boek": "johannes", "hoofdstuk": 2, "vers": 1,
                                     "ref": "johannes 2:1", "status": "needs-human-review",
                                     "bronOsis": "John.2.1"}]},
        }}

    def decision(self, **changes):
        result = {
            "entityId": "geo-kana", "ref": "johannes 2:1", "decision": "confirmed",
            "label": "Kana", "reason": "De plaatsnaam staat expliciet in dit vers.",
            "textSha256": hashlib.sha256(TEXT.encode("utf-8")).hexdigest(),
            "sources": [{"title": "Bronentiteit", "url": "https://example.org/kana"}],
        }
        result.update(changes)
        return result

    def save(self, decisions, name="controle.json", **extra):
        doc = {"schemaVersion": 1, "scope": "johannes", "humanReviewed": False,
               "decisions": decisions, **extra}
        (self.directory / name).write_text(json.dumps(doc), encoding="utf-8")

    def apply(self, text=TEXT):
        self.assertTrue(HELPER.exists(), "De generator bewaart nog geen reviewbesluiten.")
        spec = importlib.util.spec_from_file_location("geografie_reviewbesluiten", HELPER)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module.apply_reviews(self.features, self.directory, lambda ref: text)

    def test_confirmation_updates_link_not_coordinate_certainty(self):
        self.save([self.decision()])
        result = self.apply()
        props = self.features["geo-kana"]["properties"]
        ref = props["refs"][0]
        self.assertEqual(ref["status"], "agent-reviewed")
        self.assertEqual(ref["label"], "Kana")
        self.assertEqual(ref["bronOsis"], "John.2.1")
        self.assertEqual(ref["review"]["reason"], "De plaatsnaam staat expliciet in dit vers.")
        self.assertEqual(props["zekerheid"], "onzeker")
        self.assertFalse(props["humanReviewed"])
        self.assertEqual(result["metadata"]["confirmed"], 1)

    def test_confirmed_missing_reference_is_added_with_working_reader_link(self):
        self.save([self.decision(ref="johannes 4:46")])
        self.apply()
        added = self.features["geo-kana"]["properties"]["refs"][1]
        self.assertEqual(added["href"], "index.html#johannes/4/46")
        self.assertEqual(added["vers"], 46)

    def test_rejected_reference_is_removed_but_decision_remains(self):
        self.save([self.decision(decision="rejected", label=None)])
        result = self.apply()
        self.assertEqual(self.features["geo-kana"]["properties"]["refs"], [])
        self.assertEqual(result["metadata"]["rejected"], 1)
        self.assertTrue((self.directory / "controle.json").exists())
        self.assertIn(("geo-kana", "johannes 2:1"), result["settled"])

    def test_pending_can_downgrade_an_automatic_confirmation(self):
        self.features["geo-kana"]["properties"]["refs"][0]["status"] = "agent-reviewed"
        self.save([self.decision(decision="needs-human-review", label=None)])
        self.apply()
        self.assertEqual(self.features["geo-kana"]["properties"]["refs"][0]["status"],
                         "needs-human-review")

    def test_changed_text_invalidates_confirmation(self):
        self.features["geo-kana"]["properties"]["refs"][0]["status"] = "agent-reviewed"
        self.save([self.decision()])
        result = self.apply("Hij kwam uit een andere plaats.")
        ref = self.features["geo-kana"]["properties"]["refs"][0]
        self.assertEqual(ref["status"], "needs-human-review")
        self.assertEqual(result["metadata"]["stale"], 1)
        self.assertNotIn(("geo-kana", "johannes 2:1"), result["settled"])
        self.assertNotIn("label", ref)

    def test_stale_rejection_does_not_remove_the_new_text_link(self):
        self.save([self.decision(decision="rejected", label=None)])
        self.apply("Nu noemt het vers Kana wel.")
        self.assertEqual(len(self.features["geo-kana"]["properties"]["refs"]), 1)

    def test_conflicting_decisions_fail_before_mutating_features(self):
        self.save([self.decision()])
        self.save([self.decision(decision="rejected")], name="tweede.json")
        before = copy.deepcopy(self.features)
        with self.assertRaisesRegex(ValueError, "Tegenstrijdige"):
            self.apply()
        self.assertEqual(self.features, before)

    def test_identical_parallel_decisions_share_one_runtime_link(self):
        self.save([self.decision()])
        self.save([self.decision()], name="tweede.json")
        result = self.apply()
        self.assertEqual(len(self.features["geo-kana"]["properties"]["refs"]), 1)
        self.assertEqual(result["metadata"]["confirmed"], 1)
        self.assertEqual(result["metadata"]["duplicates"], 1)

    def test_wrong_label_or_substring_is_not_confirmed(self):
        for label in ("Nazareth", "Kan"):
            with self.subTest(label=label):
                self.save([self.decision(label=label)])
                with self.assertRaisesRegex(ValueError, "Label"):
                    self.apply()

    def test_origin_is_not_added_as_a_place_alias(self):
        self.save([self.decision(label="Hij", mentionType="origin")])
        self.apply()
        self.assertNotIn("Hij", self.features["geo-kana"]["properties"]["aliases"])
        self.assertEqual(self.features["geo-kana"]["properties"]["refs"][0]["mentionType"], "origin")

    def test_context_can_have_no_literal_place_label(self):
        self.save([self.decision(label=None, mentionType="contextual")])
        self.apply()
        ref = self.features["geo-kana"]["properties"]["refs"][0]
        self.assertEqual(ref["status"], "agent-reviewed")
        self.assertNotIn("label", ref)
        self.assertEqual(self.features["geo-kana"]["properties"]["aliases"], [])

    def test_missing_hash_is_not_a_reproducible_review(self):
        decision = self.decision()
        del decision["textSha256"]
        self.save([decision])
        with self.assertRaisesRegex(ValueError, "textSha256"):
            self.apply()

    def test_unknown_entity_must_not_get_an_invented_point(self):
        self.save([self.decision(entityId="geo-onbekend")])
        with self.assertRaisesRegex(ValueError, "Onbekende entiteit"):
            self.apply()

    def test_rejection_still_requires_a_real_entity_identifier(self):
        for entity_id in (None, "", " "):
            with self.subTest(entity_id=entity_id):
                self.save([self.decision(entityId=entity_id, decision="rejected")])
                with self.assertRaisesRegex(ValueError, "entiteit-ID"):
                    self.apply()

    def test_one_name_occurrence_cannot_confirm_two_homonyms(self):
        other = copy.deepcopy(self.features["geo-kana"])
        other["properties"]["id"] = "geo-ander-kana"
        self.features["geo-ander-kana"] = other
        self.save([self.decision(), self.decision(entityId="geo-ander-kana")])
        with self.assertRaisesRegex(ValueError, "Meerdere entiteiten"):
            self.apply()

    def test_rejected_legacy_entity_does_not_require_a_published_point(self):
        self.save([self.decision(entityId="geo-legacy-pella", decision="rejected", label=None)])
        result = self.apply()
        self.assertNotIn("geo-legacy-pella", self.features)
        self.assertEqual(result["metadata"]["rejected"], 1)

    def test_new_sourced_entity_is_added_only_with_valid_coordinates(self):
        entity = {
            "id": "geo-extra", "naam": "Kana", "punt": {"lat": 32.7, "lon": 35.3},
            "humanReviewed": False,
            "coordinatenBron": {"dataset": "Plaatsregister", "url": "https://example.org/kana",
                               "onderbouwing": "Bronpunt voor de stad."},
        }
        self.save([self.decision(entityId="geo-extra")], entities=[entity])
        self.apply()
        self.assertEqual(self.features["geo-extra"]["geometry"]["coordinates"], [35.3, 32.7])
        self.assertEqual(self.features["geo-extra"]["properties"]["refs"][0]["status"], "agent-reviewed")

    def test_new_point_without_source_or_with_nan_is_rejected(self):
        for point, source in [
            ({"lat": 32.7, "lon": 35.3}, {}),
            ({"lat": float("nan"), "lon": 35.3}, {"url": "https://example.org/kana"}),
            ({"lat": 100, "lon": 35.3}, {"url": "https://example.org/kana"}),
        ]:
            with self.subTest(point=point, source=source):
                self.save([], entities=[{"id": "geo-extra", "naam": "Kana", "punt": point,
                                        "coordinatenBron": source, "humanReviewed": False}])
                with self.assertRaises(ValueError):
                    self.apply()


if __name__ == "__main__":
    unittest.main()
