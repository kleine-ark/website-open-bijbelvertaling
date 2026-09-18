"""Regressies voor gecontroleerde bron-naar-OV-versnummering."""

import importlib.util
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / "scripts" / "geografie_versificatie.py"


class GeografieVersificatieTests(unittest.TestCase):
    def convert(self, verse):
        self.assertTrue(HELPER.is_file(), "De versificatiehelper ontbreekt.")
        spec = importlib.util.spec_from_file_location("geografie_versificatie", HELPER)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module.source_osis(verse)

    def check_pairs(self, pairs):
        for source, expected in pairs:
            with self.subTest(source=source):
                self.assertEqual(self.convert({"osis": source}), expected)

    def test_psalm_body_uses_numbered_superscription_offset(self):
        self.check_pairs([
            ("Ps.22.12", "Ps.22.13"),
            ("Ps.48.2", "Ps.48.3"),
            ("Ps.51.18", "Ps.51.20"),
            ("Ps.52.9", "Ps.52.11"),
            ("Ps.54.7", "Ps.54.9"),
            ("Ps.60.8", "Ps.60.10"),
            ("Ps.68.22", "Ps.68.23"),
            ("Ps.83.7", "Ps.83.8"),
            ("Ps.108.9", "Ps.108.10"),
            ("Ps.137.1", "Ps.137.1"),
        ])

    def test_geographic_mentions_in_psalm_titles_are_not_body_verses(self):
        self.check_pairs([
            ("Ps.56.1", "Ps.56.1"),
            ("Ps.56.2", "Ps.56.3"),
            ("Ps.60.1", "Ps.60.2"),
            ("Ps.60.2", "Ps.60.4"),
            ("Ps.65.1", "Ps.65.2"),
        ])

    def test_hosea_chapter_boundaries_and_last_verses(self):
        self.check_pairs([
            ("Hos.1.11", "Hos.1.11"),
            ("Hos.2.1", "Hos.1.12"),
            ("Hos.2.2", "Hos.2.1"),
            ("Hos.2.15", "Hos.2.14"),
            ("Hos.2.23", "Hos.2.22"),
            ("Hos.11.11", "Hos.11.11"),
            ("Hos.11.12", "Hos.12.1"),
            ("Hos.12.1", "Hos.12.2"),
            ("Hos.12.4", "Hos.12.5"),
            ("Hos.12.14", "Hos.12.15"),
            ("Hos.13.15", "Hos.13.15"),
            ("Hos.13.16", "Hos.14.1"),
            ("Hos.14.1", "Hos.14.2"),
            ("Hos.14.9", "Hos.14.10"),
        ])

    def test_verified_old_testament_chapter_boundaries(self):
        self.check_pairs([
            ("Exod.5.23", "Exod.5.23"),
            ("Exod.6.1", "Exod.5.24"),
            ("Exod.6.2", "Exod.6.1"),
            ("Exod.6.4", "Exod.6.3"),
            ("Exod.6.30", "Exod.6.29"),
            ("Exod.7.1", "Exod.7.1"),
            ("1Sam.23.28", "1Sam.23.28"),
            ("1Sam.23.29", "1Sam.24.1"),
            ("1Sam.24.1", "1Sam.24.2"),
            ("1Sam.24.22", "1Sam.24.23"),
            ("Dan.5.30", "Dan.5.30"),
            ("Dan.5.31", "Dan.6.1"),
            ("Dan.6.1", "Dan.6.2"),
            ("Dan.6.28", "Dan.6.29"),
            ("Isa.8.22", "Isa.8.22"),
            ("Isa.9.1", "Isa.8.23"),
            ("Isa.9.2", "Isa.9.1"),
            ("Isa.9.21", "Isa.9.20"),
            ("Mic.4.13", "Mic.4.13"),
            ("Mic.5.1", "Mic.4.14"),
            ("Mic.5.2", "Mic.5.1"),
            ("Mic.5.15", "Mic.5.14"),
            ("Hag.1.14", "Hag.1.14"),
            ("Hag.1.15", "Hag.2.1"),
            ("Hag.2.1", "Hag.2.2"),
            ("Hag.2.23", "Hag.2.24"),
        ])

    def test_verified_offsets_after_split_verses(self):
        self.check_pairs([
            ("1Kgs.22.43", "1Kgs.22.43"),
            ("1Kgs.22.44", "1Kgs.22.45"),
            ("1Kgs.22.48", "1Kgs.22.49"),
            ("1Kgs.22.53", "1Kgs.22.54"),
            ("Neh.7.73", "Neh.7.73"),
            ("Neh.8.1", "Neh.8.2"),
            ("Neh.8.16", "Neh.8.17"),
            ("Neh.8.18", "Neh.8.19"),
            ("John.1.38", "John.1.38"),
            ("John.1.39", "John.1.40"),
            ("John.1.43", "John.1.44"),
            ("John.1.44", "John.1.45"),
            ("John.1.51", "John.1.52"),
            ("John.2.1", "John.2.1"),
        ])

    def test_arimathea_uses_the_documented_kjv_alternate(self):
        verse = {"osis": "Luke.23.50", "alternate_verses": {"kjv": "Luke.23.51"}}
        self.assertEqual(self.convert(verse), "Luke.23.51")
        self.assertEqual(verse["osis"], "Luke.23.50")

    def test_jerusalem_alternate_returns_to_the_local_verse(self):
        self.assertEqual(self.convert({
            "osis": "Acts.4.5", "alternate_verses": {"kjv": "Acts.4.6"},
        }), "Acts.4.5")
        self.assertEqual(self.convert({"osis": "Acts.4.6"}), "Acts.4.6")

    def test_unverified_or_unsupported_references_are_not_guessed(self):
        self.check_pairs([
            ("Joel.2.32", "Joel.2.32"),
            ("Joel.3.1", "Joel.3.1"),
            ("Mal.4.4", "Mal.4.4"),
            ("Job.40.1", "Job.40.1"),
            ("1Sam.20.42", "1Sam.20.42"),
            ("Ps.22.12-Ps.22.13", "Ps.22.12-Ps.22.13"),
            ("Ps.title.1", "Ps.title.1"),
            ("Hos.2.99", "Hos.2.99"),
            ("", ""),
        ])
        self.assertEqual(self.convert({}), "")
        self.assertEqual(self.convert({
            "osis": "Luke.23.50", "alternate_verses": {"niv": "Luke.23.51"},
        }), "Luke.23.50")

    def test_corrected_geographic_references_contain_the_local_place(self):
        examples = [
            ({"osis": "Ps.22.12"}, "psalmen", "Basan"),
            ({"osis": "Ps.60.1"}, "psalmen", "Edom"),
            ({"osis": "Ps.83.7"}, "psalmen", "Amalek"),
            ({"osis": "Hos.12.4"}, "hosea", "Beth-el"),
            ({"osis": "Hos.13.16"}, "hosea", "Samaria"),
            ({"osis": "Exod.6.4"}, "exodus", "Kanaän"),
            ({"osis": "1Sam.23.29"}, "1samuel", "En-gedi"),
            ({"osis": "1Kgs.22.48"}, "1koningen", "Ezeon-geber"),
            ({"osis": "Dan.6.10"}, "daniel", "Jeruzalem"),
            ({"osis": "Isa.9.1"}, "jesaja", "Galilea"),
            ({"osis": "Mic.5.2"}, "micha", "Bethlehem"),
            ({"osis": "Neh.8.16"}, "nehemia", "Efraïmspoort"),
            ({"osis": "Hag.2.5"}, "haggai", "Egypte"),
            ({"osis": "John.1.44"}, "johannes", "Bethsaïda"),
            ({"osis": "Luke.23.50", "alternate_verses": {"kjv": "Luke.23.51"}}, "lukas", "Arimathea"),
            ({"osis": "Acts.4.5", "alternate_verses": {"kjv": "Acts.4.6"}}, "handelingen", "Jeruzalem"),
        ]
        for source, book, label in examples:
            with self.subTest(source=source["osis"], label=label):
                _, chapter, number = self.convert(source).split(".")
                payload = json.loads((ROOT / "data" / book / f"{chapter}.json").read_text(encoding="utf-8"))
                verse = next(v for v in payload["verses"] if v["number"] == int(number))
                self.assertIn(label, verse["text2026"])


if __name__ == "__main__":
    unittest.main()
