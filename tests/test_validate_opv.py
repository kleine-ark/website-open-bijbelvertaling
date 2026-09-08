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
                    "gepubliceerdeHoofdstukken": {"genesis": [1]},
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
            "gepubliceerdeHoofdstukken": {"genesis": [1]},
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

    def test_gepubliceerde_hoofdstukken_is_verplicht_in_beide_manifesten(self) -> None:
        del self.registry["edities"][0]["gepubliceerdeHoofdstukken"]
        del self.edition_manifest["gepubliceerdeHoofdstukken"]
        errors = self._errors_after_rewrite()
        self.assertHasCode(errors, "MANIFEST_FIELD_MISSING")
        self.assertHasCode(errors, "EDITION_FIELD_MISSING")

    def test_gepubliceerde_hoofdstukken_weigert_malformed_waarden(self) -> None:
        cases = (
            ({"genesis": "1"}, "PUBLISHED_CHAPTERS_INVALID"),
            ({"genesis": [True]}, "PUBLISHED_CHAPTERS_INVALID"),
            ({"genesis": [1, 1]}, "PUBLISHED_CHAPTERS_INVALID"),
            ({"genesis": [2, 1]}, "PUBLISHED_CHAPTERS_INVALID"),
            ({"exodus": [1]}, "PUBLISHED_BOOK_UNKNOWN"),
            ({"../escape": [True, 999, "1"]}, "MANIFEST_PATH_UNSAFE"),
        )
        for value, expected_code in cases:
            with self.subTest(value=value):
                self.registry["edities"][0]["hoofdstukken"]["genesis"] = [1, 2]
                self.edition_manifest["boeken"][0]["hoofdstukken"] = [1, 2]
                self.registry["edities"][0]["gepubliceerdeHoofdstukken"] = copy.deepcopy(value)
                self.edition_manifest["gepubliceerdeHoofdstukken"] = copy.deepcopy(value)
                errors = self._errors_after_rewrite()
                self.assertHasCode(errors, expected_code)
                self.assertEqual(sorted(errors), errors)

    def test_gepubliceerde_hoofdstukken_moet_binnen_de_planning_vallen(self) -> None:
        published = {"genesis": [2]}
        self.registry["edities"][0]["gepubliceerdeHoofdstukken"] = published
        self.edition_manifest["gepubliceerdeHoofdstukken"] = copy.deepcopy(published)
        errors = self._errors_after_rewrite()
        self.assertHasCode(errors, "PUBLISHED_CHAPTER_OUTSIDE_PLAN")

    def test_publicatielijsten_in_beide_manifesten_moeten_gelijk_zijn(self) -> None:
        self.edition_manifest["gepubliceerdeHoofdstukken"] = {"genesis": []}
        errors = self._errors_after_rewrite()
        self.assertHasCode(errors, "PUBLISHED_CHAPTERS_MISMATCH")

    def test_geregistreerd_gepubliceerd_hoofdstuk_moet_bestaan(self) -> None:
        planned = [1, 2]
        published = {"genesis": [1, 2]}
        self.registry["edities"][0]["hoofdstukken"]["genesis"] = planned
        self.edition_manifest["boeken"][0]["hoofdstukken"] = planned
        self.registry["edities"][0]["gepubliceerdeHoofdstukken"] = published
        self.edition_manifest["gepubliceerdeHoofdstukken"] = copy.deepcopy(published)
        errors = self._errors_after_rewrite()
        self.assertIn(
            "FILE_MISSING data/edities/opv/chapters/genesis/2.json $",
            errors,
        )

    def test_aanwezig_hoofdstukbestand_moet_geregistreerd_zijn(self) -> None:
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
        self.assertHasCode(errors, "PUBLISHED_FILE_UNREGISTERED")

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
        self.registry["edities"][0]["gepubliceerdeHoofdstukken"]["genesis"] = [1, 2]
        self.edition_manifest["gepubliceerdeHoofdstukken"]["genesis"] = [1, 2]
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
        self.assertEqual("OPV geldig: 1 hoofdstukken, 1 verzen.\n", valid.stdout)

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
            edition = json.loads((self.root / "data/edities/opv/manifest.json").read_text(encoding="utf-8"))
            registry["edities"][0]["gepubliceerdeHoofdstukken"] = {"genesis": [1], "johannes": [1]}
            edition["gepubliceerdeHoofdstukken"] = {"genesis": [1], "johannes": [1]}
            write_json(root / "data/edities/manifest.json", registry)
            write_json(root / "data/edities/opv/manifest.json", edition)
            concepts = json.loads((self.root / "data/edities/opv/concepten.json").read_text(encoding="utf-8"))
            write_json(root / "data/edities/opv/concepten.json", concepts)
            for book, chapter in chapters.items():
                write_json(root / f"data/edities/opv/chapters/{book}/1.json", chapter)
                source = json.loads((self.root / f"data/{book}/1.json").read_text(encoding="utf-8"))
                write_json(root / f"data/{book}/1.json", source)
            self.assertEqual([], validate_corpus(root))

    def test_productie_cli_meldt_de_volledige_gepubliceerde_pilot(self) -> None:
        script = self.root / "scripts/validate_opv.py"
        result = subprocess.run(
            [sys.executable, str(script), "--root", str(self.root)],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertEqual("OPV geldig: 10 hoofdstukken, 352 verzen.\n", result.stdout)


class OpvGenesisPilotTests(unittest.TestCase):
    root = Path(__file__).resolve().parents[1]

    def chapter(self, number: int) -> dict:
        path = self.root / f"data/edities/opv/chapters/genesis/{number}.json"
        self.assertTrue(path.is_file(), f"Genesis-hoofdstuk {number} ontbreekt")
        return json.loads(path.read_text(encoding="utf-8"))

    def test_genesis_has_exact_source_verse_lists_and_138_verses(self) -> None:
        total = 0
        for number in range(1, 6):
            with self.subTest(chapter=number):
                chapter = self.chapter(number)
                source = json.loads((self.root / f"data/genesis/{number}.json").read_text(encoding="utf-8"))
                self.assertEqual([v["number"] for v in source["verses"]],
                                 [v["nummer"] for v in chapter["verzen"]])
                total += len(chapter["verzen"])
                self.assertEqual(("genesis", number), (chapter["boek"], chapter["hoofdstuk"]))
                self.assertTrue(chapter["blokken"])
                for verse in chapter["verzen"]:
                    self.assertEqual({"bestand": f"data/genesis/{number}.json",
                                      "vers": verse["nummer"], "tekstveld": "textSV1888"}, verse["bron"])
        self.assertEqual(138, total)

    def test_new_genesis_blocks_cover_the_approved_passages(self) -> None:
        expected = {
            2: [(1, 3), (4, 7), (8, 14), (15, 17), (18, 20), (21, 25)],
            3: [(1, 5), (6, 7), (8, 13), (14, 19), (20, 21), (22, 24)],
            4: [(1, 5), (6, 7), (8, 16), (17, 24), (25, 26)],
            5: [(1, 5), (6, 20), (21, 24), (25, 27), (28, 32)],
        }
        for number, ranges in expected.items():
            with self.subTest(chapter=number):
                self.assertEqual(ranges, [(b["vanaf"], b["tot"]) for b in self.chapter(number)["blokken"]])

    def test_publication_registers_both_complete_pilot_books(self) -> None:
        registry = json.loads((self.root / "data/edities/manifest.json").read_text(encoding="utf-8"))
        edition = json.loads((self.root / "data/edities/opv/manifest.json").read_text(encoding="utf-8"))
        entry = next(e for e in registry["edities"] if e["code"] == "nl-opv")
        expected = {"genesis": [1, 2, 3, 4, 5], "johannes": [1, 2, 3, 4, 5]}
        self.assertEqual(expected, entry["gepubliceerdeHoofdstukken"])
        self.assertEqual(expected, edition["gepubliceerdeHoofdstukken"])
        pending = [(book, n) for book, ns in entry["hoofdstukken"].items()
                   for n in ns if n not in entry["gepubliceerdeHoofdstukken"][book]]
        self.assertEqual([], pending)
        self.assertEqual([], validate_corpus(self.root))

    def test_genesis_five_preserves_names_numbers_children_and_death_refrain(self) -> None:
        verses = self.chapter(5)["verzen"]
        expected_numbers = {3: [130], 4: [800], 5: [930], 6: [105], 7: [807], 8: [912],
                            9: [90], 10: [815], 11: [905], 12: [70], 13: [840], 14: [910],
                            15: [65], 16: [830], 17: [895], 18: [162], 19: [800], 20: [962],
                            21: [65], 22: [300], 23: [365], 25: [187], 26: [782], 27: [969],
                            28: [182], 30: [595], 31: [777], 32: [500]}
        for number, values in expected_numbers.items():
            self.assertEqual(values, [int(n) for n in re.findall(r"\b\d+\b", verses[number - 1]["tekst"])])
        source = json.loads((self.root / "data/genesis/5.json").read_text(encoding="utf-8"))
        names = ("Adam", "Seth", "Enos", "Kenan", "Mahalal-el", "Jered", "Henoch", "Methusalach", "Lamech", "Noach", "Sem", "Cham", "Jafeth")
        for original, verse in zip(source["verses"], verses):
            for name in names:
                if name in original["textSV1888"]:
                    self.assertIn(name, verse["tekst"])
        for number in (4, 7, 10, 13, 16, 19, 22, 26, 30):
            self.assertIn("zonen en dochters", verses[number - 1]["tekst"])
        self.assertEqual([5, 8, 11, 14, 17, 20, 27, 31],
                         [v["nummer"] for v in verses if "en hij stierf" in v["tekst"]])
        for number in (22, 24):
            self.assertIn("met God", verses[number - 1]["tekst"])

    def test_new_metadata_has_local_exact_anchors_and_concept_reviews(self) -> None:
        for number in range(2, 6):
            chapter = self.chapter(number)
            source = json.loads((self.root / f"data/genesis/{number}.json").read_text(encoding="utf-8"))
            for block in chapter["blokken"]:
                self.assertEqual("concept", block["review"]["status"])
            for verse, original in zip(chapter["verzen"], source["verses"]):
                ids = [s["id"] for s in verse["segmenten"]]
                self.assertEqual([f"GEN.{number}.{verse['nummer']}.s{i}" for i in range(1, len(ids) + 1)], ids)
                self.assertEqual(verse["tekst"], "".join(s["tekst"] for s in verse["segmenten"]))
                for segment in verse["segmenten"]:
                    self.assertTrue(segment["bronfrase"])
                    self.assertIn(segment["bronfrase"], original["textSV1888"])
                for concept in verse["begrippen"]:
                    self.assertTrue(concept["segmenten"])
                    self.assertLessEqual(set(concept["segmenten"]), set(ids))
                for quote in verse["citaten"]:
                    self.assertIn(quote["startSegment"], ids)
                    self.assertIn(quote["endSegment"], ids)
                    self.assertIsInstance(quote["aangesprokene"], list)
                self.assertEqual("concept", verse["review"]["status"])
                self.assertEqual([], verse["review"]["controles"])

    def test_dialogue_speakers_and_embedded_divine_quotes_are_preserved(self) -> None:
        expected = {2: {16: ["god"], 17: ["god"], 18: ["god"], 23: ["adam"]},
                    3: {1: ["slang", "god"], 2: ["eva"], 3: ["eva", "god"], 4: ["slang"],
                        5: ["slang"], 9: ["god"], 10: ["adam"], 11: ["god"], 12: ["adam"],
                        13: ["god", "eva"], 14: ["god"], 15: ["god"], 16: ["god"],
                        17: ["god", "god"], 18: ["god"], 19: ["god"], 22: ["god"]},
                    4: {1: ["eva"], 6: ["god"], 7: ["god"], 9: ["god", "kain"],
                        10: ["god"], 11: ["god"], 12: ["god"], 13: ["kain"], 14: ["kain"],
                        15: ["god"], 23: ["lamech-kain"], 24: ["lamech-kain"], 25: ["eva"]},
                    5: {29: ["lamech-noach"]}}
        for number, speakers in expected.items():
            actual = {v["nummer"]: [q["spreker"]["id"] for q in v["citaten"]]
                      for v in self.chapter(number)["verzen"] if v["citaten"]}
            self.assertEqual(speakers, actual)

    def test_risk_passages_preserve_primary_readings_without_added_explanations(self) -> None:
        third = self.chapter(3)["verzen"]
        fourth = self.chapter(4)["verzen"]
        self.assertNotRegex(third[14]["tekst"], r"Christus|Jezus|Messias|Satan")
        self.assertIn("vergeven", fourth[12]["tekst"])
        self.assertNotIn("straf", fourth[12]["tekst"])
        self.assertIn("zeventig keer zeven", fourth[23]["tekst"])
        for verse in fourth[2:5]:
            self.assertNotRegex(verse["tekst"], r"omdat|slechte|beste|ongeloof|geloof")

    def test_genesis_three_22_prevents_a_possibility_without_new_permission_bans(self) -> None:
        verse = self.chapter(3)["verzen"][21]
        text = verse["tekst"]
        self.assertNotRegex(text, r"(?i)\bmag\b[^.!?]*\bniet\b")
        self.assertIn("zou", text)
        self.assertIn("voorkomen", text)
        for element in ("een van ons", "goed en kwaad", "hand", "uitsteken", "boom van het leven", "nemen", "eten", "voor altijd leven"):
            self.assertIn(element, text)
        self.assertEqual(1, len(verse["citaten"]))
        self.assertEqual("god", verse["citaten"][0]["spreker"]["id"])
        self.assertEqual([], verse["citaten"][0]["aangesprokene"])
        self.assertIn("voorkomen", OpvCalibrationCorpusTests._citation_text(verse, verse["citaten"][0]))

    def test_genesis_two_5_does_not_make_plants_before_they_exist(self) -> None:
        text = self.chapter(2)["verzen"][4]["tekst"]
        self.assertNotRegex(text, r"(?i)maakte[^.!?]*voordat ze er waren")
        self.assertNotRegex(text, r"(?i)maakte Hij|daarvoor|daarvóór")
        self.assertRegex(text, r"(?i)nog geen struiken[^.!?]*land")
        self.assertRegex(text, r"(?i)veldplanten[^.!?]*nog niet opgekomen")
        for element in ("De HEERE God", "nog niet laten regenen", "nog geen mens", "grond te bewerken"):
            self.assertIn(element, text)
        self.assertLess(text.index("struiken"), text.index("regenen"))
        self.assertLess(text.index("regenen"), text.index("grond te bewerken"))

    def test_genesis_three_24_keeps_combined_placement_as_the_guarding_means(self) -> None:
        text = self.chapter(3)["verzen"][23]["tekst"]
        self.assertNotIn("Ze moesten", text)
        self.assertRegex(text, r"plaatste Hij cherubs en een vlammend zwaard")
        self.assertRegex(text, r"(?:Zo|Daarmee) liet Hij[^.!?]*bewaken")
        for element in ("oosten", "Eden", "draaide", "weg naar de boom van het leven"):
            self.assertIn(element, text)
        self.assertNotRegex(text, r"vasthield|vasthielden|hanteerde|hanteerden")

    def test_henoch_retains_the_repeated_walking_image_and_its_exact_anchors(self) -> None:
        for number in (22, 24):
            with self.subTest(verse=number):
                verse = self.chapter(5)["verzen"][number - 1]
                self.assertIn("Henoch wandelde met God", verse["tekst"])
                self.assertEqual(["wandelde met God"],
                                 OpvCalibrationCorpusTests._concept_texts(verse, "wandelen-met-god"))
        self.assertEqual([300], [int(n) for n in re.findall(r"\b\d+\b", self.chapter(5)["verzen"][21]["tekst"])])

    def test_lamechs_from_distinct_families_never_share_a_speaker_identity(self) -> None:
        fourth = self.chapter(4)["verzen"]
        fifth = self.chapter(5)["verzen"]
        first, repeated, other = fourth[22]["citaten"][0], fourth[23]["citaten"][0], fifth[28]["citaten"][0]
        self.assertNotEqual(first["spreker"]["id"], other["spreker"]["id"])
        self.assertEqual(first["spreker"]["id"], repeated["spreker"]["id"])
        self.assertEqual("lamech-kain", first["spreker"]["id"])
        self.assertEqual("lamech-noach", other["spreker"]["id"])
        for citation in (first, repeated, other):
            self.assertEqual(("Lamech", "human"), (citation["spreker"]["naam"], citation["spreker"]["type"]))
        self.assertTrue(fifth[28]["tekst"].startswith("Lamech noemde hem Noach"))

    def test_genesis_four_7_explains_the_door_image_without_changing_the_brother_reading(self) -> None:
        verse = self.chapter(4)["verzen"][6]
        self.assertRegex(verse["tekst"], r"Je broer verlangt\b[^.!?]*\bmet jou\b")
        self.assertNotIn("op jou gericht", verse["tekst"])
        self.assertIn("jij zult over hem heersen", verse["tekst"])
        self.assertNotRegex(verse["tekst"], r"\bstraf\b|eerstgeboren|oudste|moet.*heersen")
        self.assertIn("ligt de zonde aan de deur", verse["tekst"])
        concepts = json.loads((self.root / "data/edities/opv/concepten.json").read_text(encoding="utf-8"))["concepten"]
        explanation = next(c["uitleg"] for c in concepts if c["id"] == "zonde")
        self.assertIn("Genesis 4:7", explanation)
        self.assertIn("straf", explanation)
        self.assertIn("Statenvertaling", explanation)

    def test_genesis_four_7_explains_its_relational_desire_at_a_precise_anchor(self) -> None:
        verse = self.chapter(4)["verzen"][6]
        self.assertEqual(["verlangt toch naar een goede band met jou"],
                         OpvCalibrationCorpusTests._concept_texts(verse, "verlangen-van-de-broer"))
        concepts = json.loads((self.root / "data/edities/opv/concepten.json").read_text(encoding="utf-8"))["concepten"]
        explanation = next(c["uitleg"] for c in concepts if c["id"] == "verlangen-van-de-broer")
        for element in ("Genesis 4:7", "Abel", "oudere broer", "Statenvertaling"):
            self.assertIn(element, explanation)
        self.assertEqual("god", verse["citaten"][0]["spreker"]["id"])
        self.assertEqual(["kain"], verse["citaten"][0]["aangesprokene"])


class OpvJohannesPilotTests(unittest.TestCase):
    root = Path(__file__).resolve().parents[1]

    def chapter(self, number: int) -> dict:
        path = self.root / f"data/edities/opv/chapters/johannes/{number}.json"
        self.assertTrue(path.is_file(), f"Johannes-hoofdstuk {number} ontbreekt")
        return json.loads(path.read_text(encoding="utf-8"))

    def test_johannes_has_source_verse_lists_214_verses_and_pilot_352(self) -> None:
        total = 0
        for number in range(1, 6):
            with self.subTest(chapter=number):
                chapter = self.chapter(number)
                source = json.loads((self.root / f"data/johannes/{number}.json").read_text(encoding="utf-8"))
                self.assertEqual([v["number"] for v in source["verses"]],
                                 [v["nummer"] for v in chapter["verzen"]])
                self.assertEqual(("johannes", number), (chapter["boek"], chapter["hoofdstuk"]))
                total += len(chapter["verzen"])
                for verse in chapter["verzen"]:
                    self.assertEqual({"bestand": f"data/johannes/{number}.json",
                                      "vers": verse["nummer"], "tekstveld": "textSV1888"}, verse["bron"])
        self.assertEqual(214, total)
        genesis_total = sum(len(json.loads(p.read_text(encoding="utf-8"))["verzen"])
                            for p in (self.root / "data/edities/opv/chapters/genesis").glob("*.json"))
        self.assertEqual(352, total + genesis_total)

    def test_johannes_blocks_match_all_approved_boundaries(self) -> None:
        expected = {
            2: [(1, 12), (13, 17), (18, 22), (23, 25)],
            3: [(1, 8), (9, 15), (16, 21), (22, 30), (31, 36)],
            4: [(1, 6), (7, 15), (16, 26), (27, 30), (31, 38), (39, 42), (43, 45), (46, 54)],
            5: [(1, 9), (10, 18), (19, 30), (31, 40), (41, 47)],
        }
        for number, ranges in expected.items():
            with self.subTest(chapter=number):
                self.assertEqual(ranges, [(b["vanaf"], b["tot"]) for b in self.chapter(number)["blokken"]])

    def test_new_johannes_annotations_are_precise_owned_and_unique(self) -> None:
        all_ids = set()
        citation_ids = set()
        for number in range(2, 6):
            for verse in self.chapter(number)["verzen"]:
                ids = [s["id"] for s in verse["segmenten"]]
                self.assertEqual([f"JHN.{number}.{verse['nummer']}.s{i}" for i in range(1, len(ids) + 1)], ids)
                self.assertFalse(all_ids.intersection(ids))
                all_ids.update(ids)
                self.assertEqual(verse["tekst"], "".join(s["tekst"] for s in verse["segmenten"]))
                source = json.loads((self.root / verse["bron"]["bestand"]).read_text(encoding="utf-8"))
                original = source["verses"][verse["nummer"] - 1]["textSV1888"]
                for segment in verse["segmenten"]:
                    self.assertTrue(segment["bronfrase"])
                    self.assertIn(segment["bronfrase"], original)
                for concept in verse["begrippen"]:
                    self.assertTrue(concept["segmenten"])
                    self.assertLessEqual(set(concept["segmenten"]), set(ids))
                for citation in verse["citaten"]:
                    self.assertNotIn(citation["id"], citation_ids)
                    citation_ids.add(citation["id"])
                    self.assertIn(citation["startSegment"], ids)
                    self.assertIn(citation["endSegment"], ids)
                    self.assertLessEqual(ids.index(citation["startSegment"]), ids.index(citation["endSegment"]))
                    self.assertIsInstance(citation["aangesprokene"], list)
                self.assertEqual("concept", verse["review"]["status"])
                self.assertEqual([], verse["review"]["controles"])
        self.assertEqual([], validate_corpus(self.root))

    def test_johannes_three_speaker_choices_are_explicit_in_metadata(self) -> None:
        verses = self.chapter(3)["verzen"]
        for start, end, speaker in ((16, 21, "jezus"), (31, 36, "johannes")):
            for number in range(start, end + 1):
                verse = verses[number - 1]
                self.assertEqual(speaker, verse["citaten"][0]["spreker"]["id"])
                self.assertEqual(verse["tekst"], OpvCalibrationCorpusTests._citation_text(verse, verse["citaten"][0]))
        self.assertTrue(OpvCalibrationCorpusTests._concept_texts(verses[15], "sprekergrens-johannes-3"))
        self.assertTrue(OpvCalibrationCorpusTests._concept_texts(verses[30], "sprekergrens-johannes-3"))

    def test_johannes_five_tr_passage_has_exact_variant_anchors(self) -> None:
        verses = self.chapter(5)["verzen"]
        waiting, angel = verses[2], verses[3]
        self.assertEqual(["Ze wachtten tot het water bewoog."],
                         OpvCalibrationCorpusTests._concept_texts(waiting, "bethesda-handschriften"))
        self.assertEqual([angel["tekst"]],
                         OpvCalibrationCorpusTests._concept_texts(angel, "bethesda-handschriften"))
        for word in ("engel", "water", "eerste", "gezond", "ziekte"):
            self.assertIn(word, angel["tekst"])
        self.assertIn("blinden", waiting["tekst"])
        self.assertIn("verschrompelde ledematen", waiting["tekst"])
        registry = json.loads((self.root / "data/edities/opv/concepten.json").read_text(encoding="utf-8"))
        note = next(c["uitleg"] for c in registry["concepten"] if c["id"] == "bethesda-handschriften")
        self.assertIn("handschriften", note)
        self.assertIn("Statenvertaling", note)

    def test_johannes_images_units_and_wordplay_keep_the_second_layer(self) -> None:
        cases = ((2, 6, "metreet"), (3, 3, "opnieuw-van-boven"), (3, 8, "wind-geest"),
                 (4, 10, "levend-water"), (4, 24, "aanbidden-geest-waarheid"),
                 (5, 39, "schriften-onderzoeken"))
        for chapter, number, concept in cases:
            with self.subTest(chapter=chapter, verse=number):
                verse = self.chapter(chapter)["verzen"][number - 1]
                self.assertTrue(OpvCalibrationCorpusTests._concept_texts(verse, concept))
        measure = self.chapter(2)["verzen"][5]["tekst"]
        self.assertIn("zes", measure)
        self.assertIn("twee of drie metreten", measure)
        self.assertNotIn("liter", measure)

    def test_johannes_nested_speech_excludes_narrative_introductions(self) -> None:
        for chapter, number, expected in ((3, 7, "Jullie moeten opnieuw geboren worden."),
                                           (4, 17, "Ik heb geen man."),
                                           (4, 35, "Nog vier maanden en dan komt de oogst."),
                                           (5, 11, "Pak je slaapmat op en loop.")):
            verse = self.chapter(chapter)["verzen"][number - 1]
            self.assertEqual(expected, OpvCalibrationCorpusTests._citation_text(verse, verse["citaten"][-1]))

    def test_unspoken_questions_are_not_quotes_and_proverb_has_jesus_as_speaker(self) -> None:
        verses = self.chapter(4)["verzen"]
        self.assertEqual([], verses[26]["citaten"])
        self.assertIn("Toch vroeg niemand", verses[26]["tekst"])
        self.assertEqual("jezus", verses[43]["citaten"][0]["spreker"]["id"])
        self.assertEqual("Een profeet krijgt in zijn eigen land geen eer.",
                         OpvCalibrationCorpusTests._citation_text(verses[43], verses[43]["citaten"][0]))

    def test_all_registry_concepts_are_linked_in_the_published_pilot(self) -> None:
        registry = json.loads((self.root / "data/edities/opv/concepten.json").read_text(encoding="utf-8"))
        linked = {c["conceptId"] for p in (self.root / "data/edities/opv/chapters").glob("*/*.json")
                  for v in json.loads(p.read_text(encoding="utf-8"))["verzen"] for c in v["begrippen"]}
        self.assertEqual({c["id"] for c in registry["concepten"]}, linked)

    def test_johannes_human_address_and_future_temple_question_are_preserved(self) -> None:
        human_address = self.chapter(3)["verzen"][25]["tekst"]
        self.assertNotIn("Rabbi, U", human_address)
        self.assertNotIn("U weet toch", human_address)
        temple_question = self.chapter(2)["verzen"][19]["tekst"]
        self.assertIn("zult U", temple_question)
        self.assertNotIn("wilt", temple_question)

    def test_johannes_five_keeps_all_distinct_life_judgment_and_number_statements(self) -> None:
        verses = self.chapter(5)["verzen"]
        for number, phrase in ((2, "vijf"), (5, "38"), (19, "niets uit zichzelf"),
                               (21, "wie Hij wil"), (22, "het hele oordeel"),
                               (24, "al overgegaan"), (25, "nu al"),
                               (26, "de Vader Hem gegeven"), (27, "omdat de Zoon de Mensenzoon is"),
                               (28, "iedereen in de graven"), (29, "veroordeeld"),
                               (30, "de wil van de Vader"), (45, "Mozes"),
                               (46, "over mij geschreven")):
            with self.subTest(verse=number):
                self.assertIn(phrase, verses[number - 1]["tekst"])

    def test_johannes_four_10_keeps_jesus_as_the_one_requesting_water(self) -> None:
        verse = self.chapter(4)["verzen"][9]
        self.assertIn("wie het is die jou om drinken vraagt", verse["tekst"])
        self.assertIn("zou jij Hem erom vragen", verse["tekst"])
        self.assertNotIn("wie je om drinken vraagt", verse["tekst"])
        self.assertEqual("jezus", verse["citaten"][0]["spreker"]["id"])
        self.assertIn("die jou om drinken vraagt", OpvCalibrationCorpusTests._citation_text(verse, verse["citaten"][0]))
        self.assertEqual(["levend water"], OpvCalibrationCorpusTests._concept_texts(verse, "levend-water"))

    def test_johannes_five_23_preserves_the_purpose_of_giving_judgment(self) -> None:
        verse = self.chapter(5)["verzen"][22]
        self.assertTrue(verse["tekst"].startswith("Dat heeft Hij gedaan zodat iedereen de Zoon eert zoals de Vader."))
        self.assertNotIn("Zo zal iedereen", verse["tekst"])
        self.assertIn("Wie de Zoon niet eert, eert ook de Vader niet die Hem gestuurd heeft.", verse["tekst"])
        self.assertEqual(["de Zoon eert zoals de Vader"], OpvCalibrationCorpusTests._concept_texts(verse, "vader-zoon"))
        self.assertEqual(verse["tekst"], OpvCalibrationCorpusTests._citation_text(verse, verse["citaten"][0]))

    def test_johannes_five_18_keeps_intensified_effort_to_kill(self) -> None:
        text = self.chapter(5)["verzen"][17]["tekst"]
        self.assertIn("waren de Joden er nog sterker op uit Hem te doden", text)
        self.assertNotIn("liever", text)
        for phrase in ("Hij brak niet alleen de sabbat", "Zijn eigen Vader", "zichzelf gelijk aan God"):
            self.assertIn(phrase, text)

    def test_johannes_two_22_refers_to_the_specific_temple_statement(self) -> None:
        verse = self.chapter(2)["verzen"][21]
        self.assertIn("de Schrift en deze uitspraak van Jezus", verse["tekst"])
        self.assertNotIn("de woorden van Jezus", verse["tekst"])
        self.assertIn("dat Hij dit tegen hen had gezegd", verse["tekst"])
        self.assertEqual(["de Schrift"], OpvCalibrationCorpusTests._concept_texts(verse, "schriften"))

    def test_johannes_four_27_keeps_the_object_of_the_unasked_question(self) -> None:
        verse = self.chapter(4)["verzen"][26]
        self.assertIn("Toch vroeg niemand: Wat wilt U van haar?", verse["tekst"])
        self.assertNotIn("Wat vraagt U?", verse["tekst"])
        self.assertIn("Waarom praat U met haar?", verse["tekst"])
        self.assertEqual([], verse["citaten"])

    def test_johannes_five_22_keeps_the_explanatory_link_to_judgment(self) -> None:
        verse = self.chapter(5)["verzen"][21]
        self.assertTrue(verse["tekst"].startswith("De Vader oordeelt namelijk niemand."))
        self.assertIn("Hij heeft het hele oordeel aan de Zoon gegeven.", verse["tekst"])
        self.assertNotIn("ook over niemand", verse["tekst"])
        self.assertEqual(["het hele oordeel"], OpvCalibrationCorpusTests._concept_texts(verse, "oordeel"))
        self.assertEqual(verse["tekst"], OpvCalibrationCorpusTests._citation_text(verse, verse["citaten"][0]))


    def test_johannes_three_17_identifies_the_son_as_the_means_of_rescue(self) -> None:
        verse = self.chapter(3)["verzen"][16]
        expected = "God stuurde Zijn Zoon immers niet naar de wereld om die te veroordelen, maar om de wereld door Zijn Zoon te redden."
        self.assertEqual(expected, OpvCalibrationCorpusTests._citation_text(verse, verse["citaten"][0]))
        self.assertEqual(["de wereld door Zijn Zoon te redden"], OpvCalibrationCorpusTests._concept_texts(verse, "redding"))

    def test_johannes_three_35_gives_everything_to_the_son(self) -> None:
        verse = self.chapter(3)["verzen"][34]
        expected = "De Vader houdt van de Zoon en heeft Hem alles in handen gegeven."
        self.assertEqual(expected, OpvCalibrationCorpusTests._citation_text(verse, verse["citaten"][0]))
        self.assertEqual(["Hem alles in handen gegeven"], OpvCalibrationCorpusTests._concept_texts(verse, "alles-in-zijn-hand"))

    def test_johannes_five_20_names_the_father_as_the_one_showing_his_works(self) -> None:
        verse = self.chapter(5)["verzen"][19]
        expected = "Want de Vader houdt van de Zoon en laat Hem alles zien wat de Vader doet. De Vader zal Hem nog grotere werken laten zien, zodat jullie je zullen verwonderen."
        self.assertEqual(expected, OpvCalibrationCorpusTests._citation_text(verse, verse["citaten"][0]))

    def test_johannes_five_27_names_the_giver_and_recipient_of_judgment(self) -> None:
        verse = self.chapter(5)["verzen"][26]
        expected = "De Vader heeft de Zoon ook de macht gegeven om het oordeel uit te voeren, omdat de Zoon de Mensenzoon is."
        self.assertEqual(expected, OpvCalibrationCorpusTests._citation_text(verse, verse["citaten"][0]))
        self.assertEqual(["Mensenzoon"], OpvCalibrationCorpusTests._concept_texts(verse, "mensenzoon"))

    def test_johannes_four_42_keeps_the_womans_witness_and_adds_direct_hearing(self) -> None:
        verse = self.chapter(4)["verzen"][41]
        expected = "We geloven nu niet meer alleen vanwege jouw verhaal, want we hebben Hem zelf gehoord. We weten dat Hij werkelijk de Christus is, de Redder van de wereld."
        self.assertEqual(expected, OpvCalibrationCorpusTests._citation_text(verse, verse["citaten"][0]))
        self.assertEqual(["Christus"], OpvCalibrationCorpusTests._concept_texts(verse, "messias"))
        self.assertEqual(["Redder van de wereld"], OpvCalibrationCorpusTests._concept_texts(verse, "redder-wereld"))

    def test_johannes_four_1_gives_the_report_content_directly(self) -> None:
        verse = self.chapter(4)["verzen"][0]
        expected = "De Heere wist dat de Farizeeën hadden gehoord dat Hij meer leerlingen maakte en doopte dan Johannes."
        self.assertEqual(expected, verse["tekst"])

    def test_johannes_four_25_keeps_the_promise_to_make_everything_known(self) -> None:
        verse = self.chapter(4)["verzen"][24]
        expected = "Ik weet dat de Messias komt. Wanneer Hij komt, zal Hij ons alles bekendmaken."
        self.assertEqual(expected, OpvCalibrationCorpusTests._citation_text(verse, verse["citaten"][0]))

    def test_johannes_two_6_expresses_capacity_without_converting_the_unit(self) -> None:
        verse = self.chapter(2)["verzen"][5]
        expected = "Er stonden zes stenen watervaten voor de reiniging van de Joden. Elk vat kon twee of drie metreten bevatten."
        self.assertEqual(expected, verse["tekst"])
        self.assertEqual(["twee of drie metreten"], OpvCalibrationCorpusTests._concept_texts(verse, "metreet"))

    def test_johannes_two_13_connects_the_passover_and_the_journey(self) -> None:
        verse = self.chapter(2)["verzen"][12]
        expected = "Het Joodse paasfeest naderde. Daarom ging Jezus naar Jeruzalem."
        self.assertEqual(expected, verse["tekst"])
        self.assertEqual(["Joodse paasfeest"], OpvCalibrationCorpusTests._concept_texts(verse, "pascha"))

    def test_johannes_two_25_describes_human_testimony_in_plain_words(self) -> None:
        verse = self.chapter(2)["verzen"][24]
        expected = "Hij had niemand nodig om Hem iets over mensen te vertellen. Hij wist zelf wat er in een mens omging."
        self.assertEqual(expected, verse["tekst"])

    def test_johannes_three_23_connects_johns_baptizing_and_its_location(self) -> None:
        verse = self.chapter(3)["verzen"][22]
        expected = "Ook Johannes doopte in Enon bij Salim, omdat daar veel water was. Mensen kwamen naar hem toe en werden gedoopt."
        self.assertEqual(expected, verse["tekst"])
        self.assertEqual(["doopte"], OpvCalibrationCorpusTests._concept_texts(verse, "doop"))

    def test_johannes_four_26_makes_jesus_identity_statement_direct(self) -> None:
        verse = self.chapter(4)["verzen"][25]
        expected = "Dat ben ik, degene die met je spreekt."
        self.assertEqual(expected, OpvCalibrationCorpusTests._citation_text(verse, verse["citaten"][0]))

    def test_johannes_four_46_identifies_the_royal_official_in_plain_words(self) -> None:
        verse = self.chapter(4)["verzen"][45]
        expected = "Jezus kwam weer in Kana in Galilea, waar Hij water in wijn had veranderd. Een ambtenaar van de koning had een zoon die ziek lag in Kapernaüm."
        self.assertEqual(expected, verse["tekst"])
        self.assertEqual(["ambtenaar van de koning"], OpvCalibrationCorpusTests._concept_texts(verse, "hoveling"))

    def test_johannes_four_52_asks_when_the_son_recovered(self) -> None:
        verse = self.chapter(4)["verzen"][51]
        expected = "Hij vroeg op welk uur zijn zoon was opgeknapt. Ze zeiden: Gisteren, op het zevende uur, verdween zijn koorts."
        self.assertEqual(expected, verse["tekst"])
        self.assertEqual(["zevende uur"], OpvCalibrationCorpusTests._concept_texts(verse, "zevende-uur"))


if __name__ == "__main__":
    unittest.main()
