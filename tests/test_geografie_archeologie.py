"""Archeologische inventaris: lege dossiers tellen niet als brononderzoek."""
import copy
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / "scripts" / "build_geografie_archeologie.py"


def reviewed(**changes):
    value = {
        "plaatsId": "geo-stad", "onderzoeksstatus": "archeologische-bron",
        "siteNaam": "Tel Voorbeeld", "samenvatting": "Er zijn stadsresten onderzocht.",
        "koppelingAanPlaats": "De vindplaats hoort bij deze stad.",
        "perioden": ["Bronstijd"], "bevindingen": [
            {"tekst": "Er is een muur opgegraven.", "bronIds": ["rapport"]}],
        "beperkingen": ["De muur bewijst geen afzonderlijke beschreven gebeurtenis."],
        "bronnen": [{"id": "rapport", "titel": "Opgravingsrapport", "url": "https://example.org/rapport",
                     "organisatie": "Onderzoeksinstituut", "jaar": 2022, "type": "opgravingsrapport"}],
        "gecontroleerdOp": "2026-09-13", "humanReviewed": False,
    }
    value.update(changes)
    return value


class ArcheologieInventarisTests(unittest.TestCase):
    def setUp(self):
        self.runtime = {"features": [
            {"properties": {"id": "geo-stad", "naam": "Stad", "type": "stad-dorp"}},
            {"properties": {"id": "geo-streek", "naam": "Streek", "type": "land-streek"}},
        ]}

    def build(self, dossiers):
        self.assertTrue(HELPER.exists(), "Een volledige archeologie-inventaris ontbreekt.")
        spec = importlib.util.spec_from_file_location("archeologie_builder", HELPER)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod.build_index(self.runtime, [{"schemaVersion": 1, "dossiers": dossiers}])

    def test_every_runtime_place_gets_an_explicit_research_status(self):
        output = self.build([])
        self.assertEqual(set(output["dossiers"]), {"geo-stad", "geo-streek"})
        self.assertEqual(output["dossiers"]["geo-streek"]["onderzoeksstatus"], "nog-te-onderzoeken")
        self.assertEqual(output["metadata"]["onderzocht"], 0)
        self.assertEqual(output["metadata"]["totaal"], 2)

    def test_sourced_research_does_not_turn_all_placeholders_into_research(self):
        output = self.build([reviewed()])
        self.assertEqual(output["metadata"]["onderzocht"], 1)
        self.assertEqual(output["metadata"]["metArcheologischeBron"], 1)
        self.assertEqual(output["metadata"]["perStatus"]["nog-te-onderzoeken"], 1)
        self.assertEqual(output["dossiers"]["geo-stad"]["bevindingen"][0]["bronIds"], ["rapport"])

    def test_identification_paper_is_not_counted_as_direct_archaeology(self):
        output = self.build([reviewed(onderzoeksstatus="alleen-identificatie")])
        self.assertEqual(output["metadata"]["onderzocht"], 1)
        self.assertEqual(output["metadata"]["metArcheologischeBron"], 0)

    def test_unknown_or_legacy_identifier_cannot_attach_to_a_similarly_named_site(self):
        for place in ("geo-onbekend", "geo-legacy-stad"):
            with self.subTest(place=place):
                with self.assertRaisesRegex(ValueError, "Onbekende plaats"):
                    self.build([reviewed(plaatsId=place)])

    def test_duplicate_dossiers_cannot_silently_replace_each_other(self):
        with self.assertRaisesRegex(ValueError, "Dubbel dossier"):
            self.build([reviewed(), reviewed()])

    def test_findings_require_real_source_ids(self):
        with self.assertRaisesRegex(ValueError, "bron"):
            self.build([reviewed(bevindingen=[{"tekst": "Een claim.", "bronIds": ["onbekend"]}])])
        with self.assertRaisesRegex(ValueError, "bron"):
            self.build([reviewed(bevindingen=[{"tekst": "Een claim.", "bronIds": []}])])

    def test_unsafe_or_missing_source_links_are_not_published(self):
        for url in ("", "javascript:alert(1)", "http://example.org"):
            with self.subTest(url=url):
                item = reviewed()
                item["bronnen"][0]["url"] = url
                with self.assertRaisesRegex(ValueError, "bron"):
                    self.build([item])

    def test_sources_without_research_content_are_not_marked_done(self):
        for key in ("samenvatting", "koppelingAanPlaats", "siteNaam", "bevindingen"):
            with self.subTest(key=key):
                with self.assertRaises(ValueError):
                    self.build([reviewed(**{key: [] if key == "bevindingen" else ""})])

    def test_agent_records_do_not_silently_claim_human_review(self):
        with self.assertRaisesRegex(ValueError, "humanReviewed"):
            self.build([reviewed(humanReviewed=True)])

    def test_a_review_date_is_required(self):
        for date in ("", "2026-02-31", "ooit"):
            with self.subTest(date=date):
                with self.assertRaises(ValueError):
                    self.build([reviewed(gecontroleerdOp=date)])

    def test_unsupported_status_cannot_inflate_progress(self):
        with self.assertRaisesRegex(ValueError, "status"):
            self.build([reviewed(onderzoeksstatus="klaar")])

    def test_geography_and_authored_source_records_remain_unchanged(self):
        doc = reviewed()
        original = copy.deepcopy(self.runtime)
        original_doc = copy.deepcopy(doc)
        self.build([doc])
        self.assertEqual(self.runtime, original)
        self.assertEqual(doc, original_doc)


if __name__ == "__main__":
    unittest.main()

