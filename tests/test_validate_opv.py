from __future__ import annotations

import copy
import json
import re
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

from scripts.validate_opv import _validate_blocks, validate_corpus


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
        self.root = Path(self.temp_dir.name) / "repo"
        self.chapter = copy.deepcopy(VALID_CHAPTER)
        self.registry = {
            "schema": 1,
            "edities": [
                {
                    "code": "nl-opv",
                    "naam": "Open Parafrase Vertaling (proef)",
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
            "naam": "Open Parafrase Vertaling (proef)",
            "taal": "nl",
            "richting": "ltr",
            "status": "pilot",
            "versie": "0.1.0",
            "doelgroep": "16-jarige HAVO-lezer",
            "bronnenbeleid": {
                "basistekst": "Statenvertaling 1888",
                "controlebronnen": [
                    "Statenvertaling 1637",
                    "Open Vertaling",
                    "Hebreeuwse en Griekse grondtekst",
                ],
            },
            "redactioneleStatussen": [
                "concept",
                "bron_gecontroleerd",
                "taal_gecontroleerd",
                "definitief",
            ],
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
        self._write_source_verses(
            book, chapter, [{"number": 1, "textSV1888": text}]
        )

    def _write_source_verses(
        self, book: str, chapter: int, verses: list[dict]
    ) -> None:
        write_json(
            self.root / f"data/{book}/{chapter}.json",
            {"number": chapter, "verses": verses},
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

    def _configure_two_verse_chapter(self) -> None:
        second = {
            "nummer": 2,
            "tekst": "De aarde was leeg en donker.",
            "bron": {
                "bestand": "data/genesis/1.json",
                "vers": 2,
                "tekstveld": "textSV1888",
            },
            "segmenten": [
                {"id": "GEN.1.2.s1", "tekst": "De aarde was leeg en donker."}
            ],
            "begrippen": [],
            "citaten": [],
            "review": {
                "status": "concept",
                "inhoudSha256": "9c6fcc12a7bbf286f47042b100fb8cb9c8462c1585ab444443074f5bcbb5951c",
                "bronSha256": "25f782d86a4d2b779fce6a903d2d5770cdc7c363d0ee92842bc6b76c6a683583",
                "controles": [],
            },
        }
        self.chapter["verzen"].append(second)
        self.chapter["blokken"][0]["tot"] = 2

    def test_valid_mini_corpus_has_no_errors(self) -> None:
        self.assertEqual([], validate_corpus(self.root))

    def test_json_booleans_are_rejected_for_every_schema_field(self) -> None:
        self.registry["schema"] = True
        self.edition_manifest["schema"] = True
        self.concepts["schema"] = True
        self.chapter["schema"] = True
        errors = self._errors_after_rewrite()
        self.assertHasCode(errors, "MANIFEST_SCHEMA")
        self.assertHasCode(errors, "EDITION_SCHEMA")
        self.assertHasCode(errors, "CONCEPT_SCHEMA")
        self.assertHasCode(errors, "CHAPTER_SCHEMA")

    def test_json_boolean_is_not_an_opv_chapter_number(self) -> None:
        self.chapter["hoofdstuk"] = True
        write_json(
            self.root / "data/edities/opv/chapters/genesis/1.json",
            self.chapter,
        )
        errors = validate_corpus(self.root)
        self.assertHasCode(errors, "CHAPTER_NUMBER")

    def test_json_booleans_are_rejected_for_source_chapter_and_verse_numbers(self) -> None:
        self.chapter["verzen"][0]["bron"]["vers"] = True
        self._write_all()
        write_json(
            self.root / "data/genesis/1.json",
            {
                "number": True,
                "verses": [{"number": True, "textSV1888": SOURCE_TEXT}],
            },
        )
        errors = validate_corpus(self.root)
        self.assertHasCode(errors, "SOURCE_CHAPTER_MISMATCH")
        self.assertHasCode(errors, "SOURCE_VERSE_MISMATCH")
        self.assertHasCode(errors, "SOURCE_VERSE_NUMBER_INVALID")

    def test_boolean_verse_and_block_numbers_remain_invalid(self) -> None:
        self.chapter["verzen"][0]["nummer"] = True
        self.chapter["blokken"][0]["vanaf"] = True
        self.chapter["blokken"][0]["tot"] = True
        errors = self._errors_after_rewrite()
        self.assertHasCode(errors, "VERSE_NUMBER_INVALID")
        self.assertHasCode(errors, "BLOCK_RANGE_INVALID")

    def test_boolean_manifest_chapter_number_remains_invalid(self) -> None:
        self.registry["edities"][0]["hoofdstukken"]["genesis"] = [True]
        self.edition_manifest["boeken"][0]["hoofdstukken"] = [True]
        errors = self._errors_after_rewrite()
        self.assertHasCode(errors, "MANIFEST_CHAPTERS_INVALID")
        self.assertHasCode(errors, "EDITION_CHAPTER_INVALID")

    def test_nul_in_source_path_returns_a_deterministic_error(self) -> None:
        self.chapter["verzen"][0]["bron"]["bestand"] = "data/genesis/\x00.json"
        errors = self._errors_after_rewrite()
        self.assertHasCode(errors, "SOURCE_PATH_UNSAFE")
        self.assertEqual(sorted(errors), errors)

    def test_nul_in_data_root_returns_a_deterministic_error(self) -> None:
        self.registry["edities"][0]["dataRoot"] = "data/edities/\x00/chapters"
        errors = self._errors_after_rewrite()
        self.assertHasCode(errors, "MANIFEST_PATH_UNSAFE")
        self.assertEqual(sorted(errors), errors)

    def test_other_unsafe_path_characters_return_contract_errors(self) -> None:
        for character in ("\n", "\r", "\t", ":", "?", "*", "<", ">", '"', "|"):
            with self.subTest(character=repr(character)):
                self.chapter["verzen"][0]["bron"]["bestand"] = (
                    f"data/genesis/unsafe{character}.json"
                )
                self.registry["edities"][0]["dataRoot"] = (
                    "data/edities/opv/chapters"
                )
                source_errors = self._errors_after_rewrite()
                self.assertHasCode(source_errors, "SOURCE_PATH_UNSAFE")

                self.chapter["verzen"][0]["bron"]["bestand"] = "data/genesis/1.json"
                self.registry["edities"][0]["dataRoot"] = (
                    f"data/edities/opv/{character}/chapters"
                )
                manifest_errors = self._errors_after_rewrite()
                self.assertHasCode(manifest_errors, "MANIFEST_PATH_UNSAFE")

    def test_dynamic_json_path_control_characters_stay_on_one_cli_line(self) -> None:
        self.chapter["strong\nbad"] = "H1"
        self._write_all()
        script = Path(__file__).parents[1] / "scripts/validate_opv.py"
        result = subprocess.run(
            [sys.executable, str(script), "--root", str(self.root)],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(1, result.returncode)
        self.assertEqual(1, len(result.stdout.splitlines()), result.stdout)
        self.assertIn(r"\n", result.stdout)

    def test_source_verse_must_match_current_opv_verse(self) -> None:
        self._configure_two_verse_chapter()
        self.chapter["verzen"][1]["bron"]["vers"] = 1
        self.chapter["verzen"][1]["review"]["bronSha256"] = (
            "ad7db6a21814ca5d62e90b9d9f04b435d51c91f41fbea1dcd872f573e4d4d5ee"
        )
        self._write_all()
        self._write_source_verses(
            "genesis",
            1,
            [
                {"number": 1, "textSV1888": SOURCE_TEXT},
                {
                    "number": 2,
                    "textSV1888": "De aarde nu was woest en ledig.",
                },
            ],
        )
        errors = validate_corpus(self.root)
        self.assertHasCode(errors, "SOURCE_VERSE_MISMATCH")

    def test_source_file_must_match_current_opv_book_and_chapter(self) -> None:
        self.chapter["verzen"][0]["bron"]["bestand"] = "data/johannes/2.json"
        self._write_all()
        self._write_source("johannes", 2, SOURCE_TEXT)
        errors = validate_corpus(self.root)
        self.assertHasCode(errors, "SOURCE_PATH_MISMATCH")

    def test_source_document_chapter_must_match_current_opv_chapter(self) -> None:
        self._write_all()
        write_json(
            self.root / "data/genesis/1.json",
            {"number": 2, "verses": [{"number": 1, "textSV1888": SOURCE_TEXT}]},
        )
        errors = validate_corpus(self.root)
        self.assertHasCode(errors, "SOURCE_CHAPTER_MISMATCH")

    def test_edition_manifest_requires_all_contract_metadata(self) -> None:
        complete = copy.deepcopy(self.edition_manifest)
        fields = [
            "naam",
            "taal",
            "richting",
            "status",
            "versie",
            "doelgroep",
            "bronnenbeleid",
            "redactioneleStatussen",
        ]
        for field in fields:
            with self.subTest(field=field):
                self.edition_manifest = copy.deepcopy(complete)
                del self.edition_manifest[field]
                self._write_all()
                errors = validate_corpus(self.root)
                self.assertTrue(
                    any(
                        error.startswith("EDITION_FIELD_MISSING ")
                        and error.endswith(f"$.{field}")
                        for error in errors
                    ),
                    errors,
                )

    def test_edition_manifest_rejects_incorrect_editorial_statuses(self) -> None:
        self.edition_manifest["redactioneleStatussen"] = ["concept", "klaar"]
        errors = self._errors_after_rewrite()
        self.assertHasCode(errors, "EDITION_REVIEW_STATUSES")

    def test_chapter_and_block_require_non_empty_headings_and_block_id(self) -> None:
        self.chapter["kop"] = " "
        self.chapter["blokken"][0]["kop"] = ""
        self.chapter["blokken"][0]["id"] = None
        errors = self._errors_after_rewrite()
        self.assertHasCode(errors, "CHAPTER_HEADING_MISSING")
        self.assertHasCode(errors, "BLOCK_HEADING_MISSING")
        self.assertHasCode(errors, "BLOCK_ID_MISSING")

    def test_block_ids_are_unique(self) -> None:
        self._configure_two_verse_chapter()
        self.chapter["blokken"] = [
            {"id": "gen-1-b1", "kop": "Eerste", "vanaf": 1, "tot": 1},
            {"id": "gen-1-b1", "kop": "Tweede", "vanaf": 2, "tot": 2},
        ]
        self._write_all()
        self._write_source_verses(
            "genesis",
            1,
            [
                {"number": 1, "textSV1888": SOURCE_TEXT},
                {
                    "number": 2,
                    "textSV1888": "De aarde nu was woest en ledig.",
                },
            ],
        )
        errors = validate_corpus(self.root)
        self.assertHasCode(errors, "BLOCK_ID_DUPLICATE")

    def test_blocks_must_be_sorted_by_verse_range(self) -> None:
        self._configure_two_verse_chapter()
        self.chapter["blokken"] = [
            {"id": "gen-1-b2", "kop": "Tweede", "vanaf": 2, "tot": 2},
            {"id": "gen-1-b1", "kop": "Eerste", "vanaf": 1, "tot": 1},
        ]
        self._write_all()
        self._write_source_verses(
            "genesis",
            1,
            [
                {"number": 1, "textSV1888": SOURCE_TEXT},
                {
                    "number": 2,
                    "textSV1888": "De aarde nu was woest en ledig.",
                },
            ],
        )
        errors = validate_corpus(self.root)
        self.assertHasCode(errors, "BLOCK_ORDER")

    def test_manifest_book_code_cannot_escape_data_root(self) -> None:
        malicious_book = "../../../../../escaped"
        self.registry["edities"][0]["boeken"] = [malicious_book]
        self.registry["edities"][0]["hoofdstukken"] = {malicious_book: [1]}
        self.edition_manifest["boeken"] = [
            {"code": malicious_book, "hoofdstukken": [1]}
        ]
        escaped_chapter = copy.deepcopy(self.chapter)
        escaped_chapter["boek"] = malicious_book
        self._write_all()
        write_json(self.root.parent / "escaped/1.json", escaped_chapter)
        errors = validate_corpus(self.root)
        self.assertHasCode(errors, "MANIFEST_PATH_UNSAFE")

    def test_wrong_registry_container_types_return_errors_without_traceback(self) -> None:
        self.registry["edities"][0]["boeken"] = ["genesis", 1]
        errors = self._errors_after_rewrite()
        self.assertHasCode(errors, "MANIFEST_BOOKS_INVALID")
        self.assertEqual(sorted(errors), errors)

    def test_wrong_registry_scalar_container_returns_error_without_traceback(self) -> None:
        self.registry["edities"][0]["richting"] = {}
        errors = self._errors_after_rewrite()
        self.assertHasCode(errors, "MANIFEST_DIRECTION")
        self.assertEqual(sorted(errors), errors)

    def test_registry_text_fields_reject_non_empty_containers(self) -> None:
        self.registry["edities"][0]["naam"] = {"waarde": "OPV"}
        self.registry["edities"][0]["taal"] = ["nl"]
        self.registry["edities"][0]["status"] = {"fase": "pilot"}
        errors = self._errors_after_rewrite()
        self.assertHasCode(errors, "MANIFEST_FIELD_INVALID")
        self.assertEqual(sorted(errors), errors)

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

    def test_extreme_block_range_is_bounded_and_reports_one_compact_error(self) -> None:
        self.chapter["blokken"][0]["tot"] = 100_000

        started_at = time.perf_counter()
        errors = _validate_blocks(self.chapter, "chapter.json")
        elapsed = time.perf_counter() - started_at

        unknown_verse_errors = [
            error
            for error in errors
            if error.startswith("BLOCK_RANGE_UNKNOWN_VERSE ")
        ]
        self.assertEqual(1, len(unknown_verse_errors), errors[:3])
        self.assertLess(elapsed, 0.25)

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


class OpvCalibrationCorpusTests(unittest.TestCase):
    """Detecteer ontbrekende verzen en ongeldige bron- of metadatakoppelingen."""

    root = Path(__file__).resolve().parents[1]

    def _chapter(self, book: str) -> dict:
        path = self.root / f"data/edities/opv/chapters/{book}/1.json"
        self.assertTrue(path.is_file(), f"Kalibratiehoofdstuk ontbreekt: {path}")
        return json.loads(path.read_text(encoding="utf-8"))

    def test_genesis_one_has_all_31_verses(self) -> None:
        chapter = self._chapter("genesis")
        self.assertEqual(list(range(1, 32)), [v["nummer"] for v in chapter["verzen"]])

    def test_john_one_has_all_52_repository_verses(self) -> None:
        chapter = self._chapter("johannes")
        self.assertEqual(list(range(1, 53)), [v["nummer"] for v in chapter["verzen"]])

    def test_calibration_sources_point_to_corresponding_sv_verse(self) -> None:
        for book in ("genesis", "johannes"):
            chapter = self._chapter(book)
            self.assertEqual((book, 1), (chapter["boek"], chapter["hoofdstuk"]))
            for verse in chapter["verzen"]:
                with self.subTest(book=book, verse=verse["nummer"]):
                    self.assertEqual(
                        {"bestand": f"data/{book}/1.json", "vers": verse["nummer"],
                         "tekstveld": "textSV1888"}, verse["bron"],
                    )

    @staticmethod
    def _concept_texts(verse: dict, concept_id: str) -> list[str]:
        segments = {segment["id"]: segment["tekst"] for segment in verse["segmenten"]}
        return [
            "".join(segments[reference] for reference in concept["segmenten"])
            for concept in verse["begrippen"] if concept["conceptId"] == concept_id
        ]

    @staticmethod
    def _citation_text(verse: dict, citation: dict) -> str:
        ids = [segment["id"] for segment in verse["segmenten"]]
        start = ids.index(citation["startSegment"])
        end = ids.index(citation["endSegment"])
        return "".join(segment["tekst"] for segment in verse["segmenten"][start:end + 1])

    def test_john_links_both_life_occurrences_and_required_concepts(self) -> None:
        chapter = self._chapter("johannes")
        self.assertEqual(["leven", "Dat leven"], self._concept_texts(chapter["verzen"][3], "leven"))
        required = {"woord", "leven", "licht", "genade", "waarheid", "messias",
                    "lam-van-god", "heilige-geest", "zoon-van-god", "mensenzoon"}
        linked = {c["conceptId"] for v in chapter["verzen"] for c in v["begrippen"]}
        registry = json.loads((self.root / "data/edities/opv/concepten.json").read_text(encoding="utf-8"))
        self.assertLessEqual(required, linked)
        self.assertLessEqual(required, {c["id"] for c in registry["concepten"]})

    def test_john_isaiah_quote_is_exact_and_nested(self) -> None:
        verse = self._chapter("johannes")["verzen"][22]
        self.assertEqual(2, len(verse["citaten"]))
        outer, inner = verse["citaten"]
        self.assertEqual("johannes", outer["spreker"]["id"])
        self.assertEqual(("jesaja", "human"), (inner["spreker"]["id"], inner["spreker"]["type"]))
        self.assertEqual("Maak voor de Heere een rechte weg.", self._citation_text(verse, inner))
        self.assertEqual("Ik ben de stem van iemand die in de woestijn roept: Maak voor de Heere een rechte weg. Dat heeft de profeet Jesaja gezegd.", self._citation_text(verse, outer))
        ids = [s["id"] for s in verse["segmenten"]]
        self.assertLess(ids.index(outer["startSegment"]), ids.index(inner["startSegment"]))
        self.assertLess(ids.index(inner["endSegment"]), ids.index(outer["endSegment"]))

    def test_concept_anchors_include_essential_modifiers_and_action(self) -> None:
        for book, number, concept, expected in (
            ("genesis", 21, "zeedieren", "grote zeedieren"),
            ("johannes", 14, "menswording", "werd mens"),
            ("johannes", 21, "de-profeet", "de profeet"),
        ):
            with self.subTest(book=book, verse=number):
                verse = self._chapter(book)["verzen"][number - 1]
                self.assertEqual([expected], self._concept_texts(verse, concept))

    def test_calibration_blocks_follow_the_repository_verse_boundaries(self) -> None:
        expected = {
            "genesis": [(1, 2), (3, 5), (6, 8), (9, 13), (14, 19), (20, 23), (24, 31)],
            "johannes": [(1, 5), (6, 13), (14, 18), (19, 28), (29, 34), (35, 43), (44, 52)],
        }
        for book, ranges in expected.items():
            self.assertEqual(ranges, [(b["vanaf"], b["tot"]) for b in self._chapter(book)["blokken"]])

    def test_john_creation_statement_retains_the_created_scope(self) -> None:
        text = self._chapter("johannes")["verzen"][2]["tekst"]
        self.assertIn("Niets wat gemaakt is, is zonder Hem ontstaan.", text)
        self.assertNotIn("wat bestaat", text)

    def test_genesis_water_both_produces_and_teems_with_life(self) -> None:
        for number in (20, 21):
            with self.subTest(verse=number):
                text = self._chapter("genesis")["verzen"][number - 1]["tekst"]
                self.assertIn("voortbr", text)
                self.assertIn("overvloed", text)
                self.assertIn("wemel", text)

    def test_genesis_food_refers_explicitly_to_plants_and_fruit(self) -> None:
        text = self._chapter("genesis")["verzen"][28]["tekst"]
        self.assertIn("De planten en de vruchten zijn jullie voedsel.", text)

    def test_john_second_identity_question_has_a_narrative_speaker_intro(self) -> None:
        verse = self._chapter("johannes")["verzen"][20]
        self.assertIn("Ze vroegen verder: Bent u de profeet?", verse["tekst"])
        self.assertEqual(["gezanten", "johannes", "gezanten", "johannes"],
                         [q["spreker"]["id"] for q in verse["citaten"]])
        self.assertEqual("Bent u de profeet?", self._citation_text(verse, verse["citaten"][2]))

    def test_annotations_are_owned_by_their_verse_and_segments_are_sequential(self) -> None:
        for book, prefix in (("genesis", "GEN"), ("johannes", "JHN")):
            for verse in self._chapter(book)["verzen"]:
                ids = [s["id"] for s in verse["segmenten"]]
                self.assertEqual([f"{prefix}.1.{verse['nummer']}.s{i}" for i in range(1, len(ids) + 1)], ids)
                for concept in verse["begrippen"]:
                    self.assertLessEqual(set(concept["segmenten"]), set(ids))
                for citation in verse["citaten"]:
                    self.assertIn(citation["startSegment"], ids)
                    self.assertIn(citation["endSegment"], ids)

    def test_capitalization_preserves_sentence_starts_without_extra_reverence(self) -> None:
        cases = [
            ("genesis", 30, "geef ik de groene planten"),
            ("johannes", 12, ". Dat zijn de mensen die in Zijn naam geloven."),
            ("johannes", 13, ". Dat komt niet door hun afkomst"),
            ("johannes", 14, ". Wij zagen Zijn majesteit"),
            ("johannes", 15, "Dit is degene over wie ik sprak."),
            ("johannes", 30, "een man die boven mij staat"),
            ("johannes", 38, "Jezus draaide zich om"),
            ("johannes", 44, "Volg mij."),
            ("johannes", 48, "naar zich toe"),
            ("johannes", 49, "zag ik je al"),
            ("johannes", 51, "omdat ik je zei dat ik je"),
        ]
        for book, number, expected in cases:
            with self.subTest(book=book, verse=number):
                self.assertIn(expected, self._chapter(book)["verzen"][number - 1]["tekst"])

    def test_concept_explanations_do_not_add_reverence_capitals(self) -> None:
        registry = json.loads((self.root / "data/edities/opv/concepten.json").read_text(encoding="utf-8"))
        for concept in registry["concepten"]:
            with self.subTest(concept=concept["id"]):
                self.assertNotRegex(concept["uitleg"], r"\b(?:Naam|Persoon|Zichzelf)\b")
        explanations = {c["id"]: c["uitleg"] for c in registry["concepten"]}
        self.assertIn("Zijn naam", explanations["kinderen-van-god"])

    def test_editorial_decisions_do_not_add_reverence_capitals(self) -> None:
        register = (self.root / "docs/opv/besluitregister.md").read_text(encoding="utf-8")
        own_prose = re.sub(r"“[^”]*”|`[^`]*`", "", register)
        self.assertEqual([], re.findall(r"\b(?:Naam|Persoon|Zichzelf|Degene door Wie)\b", own_prose))
        self.assertIn("Jezus Christus als degene door wie", own_prose)

    def test_calibration_slice_passes_real_corpus_validation(self) -> None:
        chapters = {book: self._chapter(book) for book in ("genesis", "johannes")}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            registry = json.loads((self.root / "data/edities/manifest.json").read_text(encoding="utf-8"))
            registry["edities"] = [entry for entry in registry["edities"] if entry["code"] == "nl-opv"]
            registry["edities"][0]["hoofdstukken"] = {"genesis": [1], "johannes": [1]}
            edition = json.loads((self.root / "data/edities/opv/manifest.json").read_text(encoding="utf-8"))
            for book in edition["boeken"]:
                book["hoofdstukken"] = [1]
            write_json(root / "data/edities/manifest.json", registry)
            write_json(root / "data/edities/opv/manifest.json", edition)
            concepts = json.loads((self.root / "data/edities/opv/concepten.json").read_text(encoding="utf-8"))
            write_json(root / "data/edities/opv/concepten.json", concepts)
            for book, chapter in chapters.items():
                write_json(root / f"data/edities/opv/chapters/{book}/1.json", chapter)
                source = json.loads((self.root / f"data/{book}/1.json").read_text(encoding="utf-8"))
                write_json(root / f"data/{book}/1.json", source)
            self.assertEqual([], validate_corpus(root))


if __name__ == "__main__":
    unittest.main()
