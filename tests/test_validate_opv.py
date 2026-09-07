from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts.validate_opv import validate_corpus


READING_TEXT = "God maakte in het begin de hemel en de aarde."
SOURCE_TEXT = "In den beginne schiep God den hemel en de aarde."


VALID_CHAPTER = {
    "schema": 1,
    "editie": "nl-opv",
    "boek": "genesis",
    "hoofdstuk": 1,
    "kop": "God maakt de hemel en de aarde",
    "blokken": [{"id": "gen-1-b1", "kop": "Het begin", "vanaf": 1, "tot": 1}],
    "verzen": [
        {
            "nummer": 1,
            "tekst": READING_TEXT,
            "bron": {
                "bestand": "data/genesis/1.json",
                "vers": 1,
                "tekstveld": "textSV1888",
            },
            "segmenten": [{"id": "GEN.1.1.s1", "tekst": READING_TEXT}],
            "begrippen": [],
            "citaten": [],
            "review": {
                "status": "concept",
                "inhoudSha256": "3de1d2d8d4735d49b002aca96ba7fc4b0227acabe72cf4d03f9330f10c99f45c",
                "bronSha256": "ad7db6a21814ca5d62e90b9d9f04b435d51c91f41fbea1dcd872f573e4d4d5ee",
                "controles": [],
            },
        }
    ],
}


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


class ValidateOpvTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.chapter = copy.deepcopy(VALID_CHAPTER)
        self.registry = {
            "schema": 1,
            "edities": [
                {
                    "code": "nl-opv",
                    "naam": "Open Parafrase Vertaling",
                    "taal": "nl",
                    "richting": "ltr",
                    "dataRoot": "data/edities/opv/chapters",
                    "boeken": ["genesis"],
                    "hoofdstukken": {"genesis": [1]},
                    "status": "pilot",
                }
            ],
        }
        self.edition_manifest = {
            "schema": 1,
            "editie": "nl-opv",
            "boeken": [{"code": "genesis", "hoofdstukken": [1]}],
        }
        self.concepts = {
            "schema": 1,
            "concepten": [
                {
                    "id": "schepping",
                    "label": "Schepping",
                    "uitleg": "God brengt de werkelijkheid tot bestaan.",
                }
            ],
        }
        self._write_all()

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def _write_all(self) -> None:
        write_json(self.root / "data/edities/manifest.json", self.registry)
        write_json(self.root / "data/edities/opv/manifest.json", self.edition_manifest)
        write_json(self.root / "data/edities/opv/concepten.json", self.concepts)
        self._write_source("genesis", 1, SOURCE_TEXT)
        self._write_chapter(self.chapter)

    def _write_source(self, book: str, chapter: int, text: str) -> None:
        write_json(
            self.root / f"data/{book}/{chapter}.json",
            {"number": chapter, "verses": [{"number": 1, "textSV1888": text}]},
        )

    def _write_chapter(self, chapter: dict) -> None:
        write_json(
            self.root
            / "data/edities/opv/chapters"
            / chapter["boek"]
            / f'{chapter["hoofdstuk"]}.json',
            chapter,
        )

    def _errors_after_rewrite(self) -> list[str]:
        self._write_all()
        return validate_corpus(self.root)

    def assertHasCode(self, errors: list[str], code: str) -> None:
        self.assertTrue(
            any(error.split(" ", 1)[0] == code for error in errors),
            f"{code!r} niet gevonden in {errors!r}",
        )

    def test_valid_mini_corpus_has_no_errors(self) -> None:
        self.assertEqual([], validate_corpus(self.root))

    def test_duplicate_verse_number_is_reported(self) -> None:
        self.chapter["verzen"].append(copy.deepcopy(self.chapter["verzen"][0]))
        errors = self._errors_after_rewrite()
        self.assertHasCode(errors, "VERSE_DUPLICATE")

    def test_empty_reading_text_is_reported(self) -> None:
        self.chapter["verzen"][0]["tekst"] = ""
        self.chapter["verzen"][0]["segmenten"][0]["tekst"] = ""
        errors = self._errors_after_rewrite()
        self.assertHasCode(errors, "TEXT_EMPTY")

    def test_html_in_reading_text_is_reported(self) -> None:
        self.chapter["verzen"][0]["tekst"] = "God <em>maakte</em> alles."
        self.chapter["verzen"][0]["segmenten"][0]["tekst"] = (
            "God <em>maakte</em> alles."
        )
        errors = self._errors_after_rewrite()
        self.assertHasCode(errors, "TEXT_HTML")

    def test_missing_source_is_reported(self) -> None:
        del self.chapter["verzen"][0]["bron"]
        errors = self._errors_after_rewrite()
        self.assertHasCode(errors, "SOURCE_MISSING")

    def test_unsafe_source_path_is_reported(self) -> None:
        self.chapter["verzen"][0]["bron"]["bestand"] = "../geheim.json"
        errors = self._errors_after_rewrite()
        self.assertHasCode(errors, "SOURCE_PATH_UNSAFE")

    def test_overlapping_blocks_are_reported(self) -> None:
        self.chapter["blokken"].append(
            {"id": "gen-1-b2", "kop": "Nogmaals", "vanaf": 1, "tot": 1}
        )
        errors = self._errors_after_rewrite()
        self.assertHasCode(errors, "BLOCKS_OVERLAP")

    def test_incomplete_blocks_are_reported(self) -> None:
        self.chapter["blokken"] = []
        errors = self._errors_after_rewrite()
        self.assertHasCode(errors, "BLOCKS_INCOMPLETE")

    def test_duplicate_segment_id_across_chapters_is_reported(self) -> None:
        second = copy.deepcopy(self.chapter)
        second["hoofdstuk"] = 2
        second["blokken"][0]["id"] = "gen-2-b1"
        second["verzen"][0]["bron"]["bestand"] = "data/genesis/2.json"
        self.registry["edities"][0]["hoofdstukken"]["genesis"] = [1, 2]
        self.edition_manifest["boeken"][0]["hoofdstukken"] = [1, 2]
        self._write_all()
        self._write_source("genesis", 2, SOURCE_TEXT)
        self._write_chapter(second)
        errors = validate_corpus(self.root)
        self.assertHasCode(errors, "SEGMENT_DUPLICATE")

    def test_unknown_concept_is_reported(self) -> None:
        self.chapter["verzen"][0]["begrippen"] = [
            {"conceptId": "onbekend", "segmenten": ["GEN.1.1.s1"]}
        ]
        errors = self._errors_after_rewrite()
        self.assertHasCode(errors, "CONCEPT_UNKNOWN")

    def test_unknown_segment_reference_is_reported(self) -> None:
        self.chapter["verzen"][0]["begrippen"] = [
            {"conceptId": "schepping", "segmenten": ["GEN.1.1.s9"]}
        ]
        errors = self._errors_after_rewrite()
        self.assertHasCode(errors, "SEGMENT_REFERENCE_UNKNOWN")

    def test_citation_without_speaker_id_is_reported(self) -> None:
        self.chapter["verzen"][0]["citaten"] = [self._valid_citation()]
        del self.chapter["verzen"][0]["citaten"][0]["spreker"]["id"]
        errors = self._errors_after_rewrite()
        self.assertHasCode(errors, "SPEAKER_ID_MISSING")

    def test_citation_without_speaker_type_is_reported(self) -> None:
        self.chapter["verzen"][0]["citaten"] = [self._valid_citation()]
        del self.chapter["verzen"][0]["citaten"][0]["spreker"]["type"]
        errors = self._errors_after_rewrite()
        self.assertHasCode(errors, "SPEAKER_TYPE_MISSING")

    def test_segments_must_reconstruct_reading_text_exactly(self) -> None:
        self.chapter["verzen"][0]["segmenten"][0]["tekst"] += " "
        errors = self._errors_after_rewrite()
        self.assertHasCode(errors, "SEGMENTS_TEXT_MISMATCH")

    def test_source_and_content_hashes_are_checked(self) -> None:
        review = self.chapter["verzen"][0]["review"]
        review["inhoudSha256"] = "0" * 64
        review["bronSha256"] = "f" * 64
        errors = self._errors_after_rewrite()
        self.assertHasCode(errors, "REVIEW_CONTENT_HASH")
        self.assertHasCode(errors, "REVIEW_SOURCE_HASH")

    def test_non_nfc_text_and_replacement_character_are_reported(self) -> None:
        self.chapter["kop"] = "Schépping \ufffd"
        errors = self._errors_after_rewrite()
        self.assertHasCode(errors, "UNICODE_NOT_NFC")
        self.assertHasCode(errors, "UNICODE_REPLACEMENT")

    def test_any_strong_field_is_rejected(self) -> None:
        self.chapter["verzen"][0]["segmenten"][0]["strongs"] = "H430"
        errors = self._errors_after_rewrite()
        self.assertHasCode(errors, "STRONG_FIELD_FORBIDDEN")

    def test_citation_requires_unique_id_and_canonical_semantic_id(self) -> None:
        citation = self._valid_citation()
        duplicate = copy.deepcopy(citation)
        duplicate["semanticId"] = "Niet canoniek"
        self.chapter["verzen"][0]["citaten"] = [citation, duplicate]
        errors = self._errors_after_rewrite()
        self.assertHasCode(errors, "CITATION_ID_DUPLICATE")
        self.assertHasCode(errors, "SEMANTIC_ID_INVALID")

    def test_crossed_citation_ranges_are_rejected(self) -> None:
        verse = self.chapter["verzen"][0]
        verse["tekst"] = "Een twee drie vier."
        verse["segmenten"] = [
            {"id": "GEN.1.1.s1", "tekst": "Een "},
            {"id": "GEN.1.1.s2", "tekst": "twee "},
            {"id": "GEN.1.1.s3", "tekst": "drie "},
            {"id": "GEN.1.1.s4", "tekst": "vier."},
        ]
        verse["review"]["inhoudSha256"] = (
            "de028ba98b32ff4e609ddbc792e427579b42046c8a66870de16fae4d524379b3"
        )
        first = self._valid_citation()
        first.update({"startSegment": "GEN.1.1.s1", "endSegment": "GEN.1.1.s3"})
        second = self._valid_citation()
        second.update(
            {
                "id": "GEN.1.1.q2",
                "semanticId": "spraak.god.tweede",
                "startSegment": "GEN.1.1.s2",
                "endSegment": "GEN.1.1.s4",
            }
        )
        verse["citaten"] = [first, second]
        errors = self._errors_after_rewrite()
        self.assertHasCode(errors, "CITATION_RANGES_CROSSED")

    def test_final_status_requires_three_current_approvals(self) -> None:
        review = self.chapter["verzen"][0]["review"]
        review["status"] = "definitief"
        review["controles"] = [
            {
                "type": "bron",
                "status": "goedgekeurd",
                "inhoudSha256": review["inhoudSha256"],
            },
            {
                "type": "taal",
                "status": "goedgekeurd",
                "inhoudSha256": review["inhoudSha256"],
            },
        ]
        errors = self._errors_after_rewrite()
        self.assertHasCode(errors, "FINAL_REVIEW_MISSING")

    def test_errors_are_deterministically_sorted(self) -> None:
        self.chapter["verzen"][0]["tekst"] = ""
        self.chapter["verzen"][0]["segmenten"] = []
        errors = self._errors_after_rewrite()
        self.assertEqual(sorted(errors), errors)

    def test_cli_returns_zero_for_valid_data_and_one_error_per_line(self) -> None:
        script = Path(__file__).parents[1] / "scripts/validate_opv.py"
        valid = subprocess.run(
            [sys.executable, str(script), "--root", str(self.root)],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(0, valid.returncode, valid.stdout + valid.stderr)

        self.chapter["verzen"][0]["tekst"] = ""
        self.chapter["verzen"][0]["segmenten"] = []
        self._write_all()
        invalid = subprocess.run(
            [sys.executable, str(script), "--root", str(self.root)],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(1, invalid.returncode)
        lines = invalid.stdout.splitlines()
        self.assertGreater(len(lines), 0)
        self.assertTrue(all(line.count(" ") >= 2 for line in lines))

    @staticmethod
    def _valid_citation() -> dict:
        return {
            "id": "GEN.1.1.q1",
            "semanticId": "spraak.god.schepping",
            "startSegment": "GEN.1.1.s1",
            "endSegment": "GEN.1.1.s1",
            "spreker": {"id": "god", "type": "god", "naam": "God"},
            "aangesprokene": [],
        }


if __name__ == "__main__":
    unittest.main()
