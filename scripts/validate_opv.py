#!/usr/bin/env python3
"""Valideer het corpuscontract van de Open Parafrase Vertaling."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import unicodedata
from collections.abc import Iterable
from pathlib import Path, PurePosixPath
from typing import Any


ALLOWED_REVIEW_STATUSES = {
    "concept",
    "bron_gecontroleerd",
    "taal_gecontroleerd",
    "definitief",
}
ALLOWED_SPEAKER_TYPES = {
    "god",
    "human",
    "angel",
    "spirit",
    "animal",
    "group",
    "narrator",
    "unknown",
}
REQUIRED_REGISTRY_FIELDS = {
    "code",
    "naam",
    "taal",
    "richting",
    "dataRoot",
    "boeken",
    "hoofdstukken",
    "status",
}
HTML_RE = re.compile(r"<\s*/?\s*[A-Za-z!][^>]*>")
SEMANTIC_ID_RE = re.compile(r"^[a-z0-9]+(?:\.[a-z0-9]+)+$")


def _error(code: str, filename: str, json_path: str) -> str:
    return f"{code} {filename} {json_path}"


def _load_json(repo_root: Path, filename: str, errors: list[str]) -> Any | None:
    path = repo_root / Path(*PurePosixPath(filename).parts)
    if not path.is_file():
        errors.append(_error("FILE_MISSING", filename, "$"))
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        errors.append(_error("JSON_INVALID", filename, "$"))
        return None


def _walk(value: Any, json_path: str = "$") -> Iterable[tuple[str, Any]]:
    yield json_path, value
    if isinstance(value, dict):
        for key, child in value.items():
            yield from _walk(child, f"{json_path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _walk(child, f"{json_path}[{index}]")


def _validate_text_integrity(value: Any, filename: str) -> list[str]:
    errors: list[str] = []
    for json_path, child in _walk(value):
        if not isinstance(child, str):
            continue
        if unicodedata.normalize("NFC", child) != child:
            errors.append(_error("UNICODE_NOT_NFC", filename, json_path))
        if "\ufffd" in child:
            errors.append(_error("UNICODE_REPLACEMENT", filename, json_path))
        if HTML_RE.search(child):
            errors.append(_error("TEXT_HTML", filename, json_path))
    return errors


def _validate_no_strong_fields(value: Any, filename: str) -> list[str]:
    errors: list[str] = []

    def visit(child: Any, json_path: str) -> None:
        if isinstance(child, dict):
            for key, nested in child.items():
                key_path = f"{json_path}.{key}"
                if "strong" in str(key).casefold():
                    errors.append(_error("STRONG_FIELD_FORBIDDEN", filename, key_path))
                visit(nested, key_path)
        elif isinstance(child, list):
            for index, nested in enumerate(child):
                visit(nested, f"{json_path}[{index}]")

    visit(value, "$")
    return errors


def _safe_repo_file(repo_root: Path, raw_path: Any) -> Path | None:
    if not isinstance(raw_path, str) or not raw_path or "\\" in raw_path:
        return None
    pure = PurePosixPath(raw_path)
    if pure.is_absolute() or ".." in pure.parts or "." in pure.parts:
        return None
    if not pure.parts or pure.parts[0] != "data" or pure.suffix != ".json":
        return None
    candidate = (repo_root / Path(*pure.parts)).resolve()
    try:
        candidate.relative_to(repo_root.resolve())
    except ValueError:
        return None
    return candidate


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _book_chapters_from_edition_manifest(manifest: Any) -> dict[str, list[int]]:
    result: dict[str, list[int]] = {}
    if not isinstance(manifest, dict) or not isinstance(manifest.get("boeken"), list):
        return result
    for book in manifest["boeken"]:
        if not isinstance(book, dict):
            continue
        code = book.get("code")
        chapters = book.get("hoofdstukken")
        if isinstance(code, str) and isinstance(chapters, list):
            result[code] = chapters
    return result


def validate_manifest(
    repo_root: Path,
    registry: Any | None = None,
    edition_manifest: Any | None = None,
) -> list[str]:
    """Valideer het centrale register en het OPV-manifest."""

    errors: list[str] = []
    registry_file = "data/edities/manifest.json"
    edition_file = "data/edities/opv/manifest.json"
    if registry is None:
        registry = _load_json(repo_root, registry_file, errors)
    if edition_manifest is None:
        edition_manifest = _load_json(repo_root, edition_file, errors)
    if registry is None or edition_manifest is None:
        return errors

    errors.extend(_validate_text_integrity(registry, registry_file))
    errors.extend(_validate_text_integrity(edition_manifest, edition_file))
    errors.extend(_validate_no_strong_fields(registry, registry_file))
    errors.extend(_validate_no_strong_fields(edition_manifest, edition_file))

    if not isinstance(registry, dict) or registry.get("schema") != 1:
        errors.append(_error("MANIFEST_SCHEMA", registry_file, "$.schema"))
        editions: list[Any] = []
    else:
        editions = registry.get("edities", [])
        if not isinstance(editions, list):
            errors.append(_error("MANIFEST_EDITIONS", registry_file, "$.edities"))
            editions = []

    opv_entries = [
        (index, entry)
        for index, entry in enumerate(editions)
        if isinstance(entry, dict) and entry.get("code") == "nl-opv"
    ]
    if len(opv_entries) != 1:
        errors.append(_error("MANIFEST_OPV_ENTRY", registry_file, "$.edities"))
        registry_chapters: dict[str, list[int]] = {}
    else:
        index, entry = opv_entries[0]
        for field in sorted(REQUIRED_REGISTRY_FIELDS):
            if field not in entry or entry[field] in (None, "", [], {}):
                errors.append(
                    _error("MANIFEST_FIELD_MISSING", registry_file, f"$.edities[{index}].{field}")
                )
        if entry.get("richting") not in {"ltr", "rtl"}:
            errors.append(
                _error("MANIFEST_DIRECTION", registry_file, f"$.edities[{index}].richting")
            )
        if entry.get("dataRoot") != "data/edities/opv/chapters":
            errors.append(
                _error("MANIFEST_DATA_ROOT", registry_file, f"$.edities[{index}].dataRoot")
            )
        registry_chapters = (
            entry.get("hoofdstukken")
            if isinstance(entry.get("hoofdstukken"), dict)
            else {}
        )
        books = entry.get("boeken") if isinstance(entry.get("boeken"), list) else []
        if sorted(books) != sorted(registry_chapters):
            errors.append(
                _error("MANIFEST_BOOKS_MISMATCH", registry_file, f"$.edities[{index}].boeken")
            )

    if not isinstance(edition_manifest, dict) or edition_manifest.get("schema") != 1:
        errors.append(_error("EDITION_SCHEMA", edition_file, "$.schema"))
    if not isinstance(edition_manifest, dict) or edition_manifest.get("editie") != "nl-opv":
        errors.append(_error("EDITION_CODE", edition_file, "$.editie"))

    edition_chapters = _book_chapters_from_edition_manifest(edition_manifest)
    if not edition_chapters:
        errors.append(_error("EDITION_BOOKS", edition_file, "$.boeken"))
    if registry_chapters != edition_chapters:
        errors.append(_error("MANIFEST_CHAPTERS_MISMATCH", edition_file, "$.boeken"))

    for book, chapters in edition_chapters.items():
        if not isinstance(chapters, list) or any(
            not isinstance(chapter, int) or isinstance(chapter, bool) or chapter < 1
            for chapter in chapters
        ):
            errors.append(_error("EDITION_CHAPTER_INVALID", edition_file, f"$.boeken.{book}"))
        elif len(chapters) != len(set(chapters)) or chapters != sorted(chapters):
            errors.append(_error("EDITION_CHAPTER_ORDER", edition_file, f"$.boeken.{book}"))
    return errors


def validate_review(
    review: Any,
    reading_text: str,
    source_text: str | None,
    filename: str,
    json_path: str,
) -> list[str]:
    """Valideer hashes, status en vereiste definitieve controles."""

    errors: list[str] = []
    if not isinstance(review, dict):
        return [_error("REVIEW_MISSING", filename, json_path)]
    status = review.get("status")
    if status not in ALLOWED_REVIEW_STATUSES:
        errors.append(_error("REVIEW_STATUS", filename, f"{json_path}.status"))
    content_hash = _sha256(reading_text)
    if review.get("inhoudSha256") != content_hash:
        errors.append(_error("REVIEW_CONTENT_HASH", filename, f"{json_path}.inhoudSha256"))
    if source_text is not None and review.get("bronSha256") != _sha256(source_text):
        errors.append(_error("REVIEW_SOURCE_HASH", filename, f"{json_path}.bronSha256"))

    controls = review.get("controles")
    if not isinstance(controls, list):
        errors.append(_error("REVIEW_CONTROLS", filename, f"{json_path}.controles"))
        controls = []
    if status == "definitief":
        approved = {
            control.get("type")
            for control in controls
            if isinstance(control, dict)
            and control.get("status") == "goedgekeurd"
            and control.get("inhoudSha256") == content_hash
        }
        if not {"bron", "taal", "leesbaarheid"}.issubset(approved):
            errors.append(_error("FINAL_REVIEW_MISSING", filename, f"{json_path}.controles"))
    return errors


def _source_text_for_verse(
    repo_root: Path,
    verse: dict[str, Any],
    filename: str,
    json_path: str,
    source_cache: dict[str, Any],
) -> tuple[str | None, str | None, list[str]]:
    errors: list[str] = []
    source_ref = verse.get("bron")
    if not isinstance(source_ref, dict):
        return None, None, [_error("SOURCE_MISSING", filename, f"{json_path}.bron")]
    raw_path = source_ref.get("bestand")
    source_path = _safe_repo_file(repo_root, raw_path)
    if source_path is None:
        return None, None, [
            _error("SOURCE_PATH_UNSAFE", filename, f"{json_path}.bron.bestand")
        ]
    source_name = PurePosixPath(str(raw_path)).as_posix()
    if not source_path.is_file():
        return source_name, None, [
            _error("SOURCE_FILE_MISSING", filename, f"{json_path}.bron.bestand")
        ]
    if source_name not in source_cache:
        try:
            source_cache[source_name] = json.loads(source_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            source_cache[source_name] = None
    source_doc = source_cache[source_name]
    if not isinstance(source_doc, dict) or not isinstance(source_doc.get("verses"), list):
        return source_name, None, [
            _error("SOURCE_JSON_INVALID", filename, f"{json_path}.bron.bestand")
        ]

    source_number = source_ref.get("vers")
    candidates = [
        candidate
        for candidate in source_doc["verses"]
        if isinstance(candidate, dict) and candidate.get("number") == source_number
    ]
    if len(candidates) != 1:
        return source_name, None, [
            _error("SOURCE_VERSE_MISSING", filename, f"{json_path}.bron.vers")
        ]
    text_field = source_ref.get("tekstveld")
    source_text = candidates[0].get(text_field) if isinstance(text_field, str) else None
    if not isinstance(source_text, str):
        errors.append(_error("SOURCE_TEXT_MISSING", filename, f"{json_path}.bron.tekstveld"))
        return source_name, None, errors
    return source_name, source_text, errors


def validate_verse(
    repo_root: Path,
    verse: Any,
    filename: str,
    json_path: str,
    source_cache: dict[str, Any],
    seen_segment_ids: dict[str, str],
) -> tuple[list[str], list[str], str | None]:
    """Valideer één vers en retourneer fouten, segment-id's en bronbestand."""

    errors: list[str] = []
    if not isinstance(verse, dict):
        return [_error("VERSE_INVALID", filename, json_path)], [], None
    reading_text = verse.get("tekst")
    if not isinstance(reading_text, str) or not reading_text.strip():
        errors.append(_error("TEXT_EMPTY", filename, f"{json_path}.tekst"))
        reading_text = reading_text if isinstance(reading_text, str) else ""

    segments = verse.get("segmenten")
    segment_ids: list[str] = []
    segment_texts: list[str] = []
    if not isinstance(segments, list) or not segments:
        errors.append(_error("SEGMENTS_MISSING", filename, f"{json_path}.segmenten"))
        segments = []
    for index, segment in enumerate(segments):
        segment_path = f"{json_path}.segmenten[{index}]"
        if not isinstance(segment, dict):
            errors.append(_error("SEGMENT_INVALID", filename, segment_path))
            continue
        segment_id = segment.get("id")
        segment_text = segment.get("tekst")
        if not isinstance(segment_id, str) or not segment_id:
            errors.append(_error("SEGMENT_ID_MISSING", filename, f"{segment_path}.id"))
        else:
            segment_ids.append(segment_id)
            if segment_id in seen_segment_ids:
                errors.append(_error("SEGMENT_DUPLICATE", filename, f"{segment_path}.id"))
            else:
                seen_segment_ids[segment_id] = f"{filename} {segment_path}.id"
        if not isinstance(segment_text, str):
            errors.append(_error("SEGMENT_TEXT_INVALID", filename, f"{segment_path}.tekst"))
        else:
            segment_texts.append(segment_text)
    if "".join(segment_texts) != reading_text:
        errors.append(_error("SEGMENTS_TEXT_MISMATCH", filename, f"{json_path}.segmenten"))

    source_name, source_text, source_errors = _source_text_for_verse(
        repo_root, verse, filename, json_path, source_cache
    )
    errors.extend(source_errors)
    errors.extend(
        validate_review(
            verse.get("review"), reading_text, source_text, filename, f"{json_path}.review"
        )
    )
    return errors, segment_ids, source_name


def validate_annotations(
    verse: Any,
    filename: str,
    json_path: str,
    concept_ids: set[str],
    segment_positions: dict[str, int],
    seen_citation_ids: dict[str, str],
) -> tuple[list[str], list[tuple[int, int, str]]]:
    """Valideer begrippen, citaten en hun segmentverwijzingen."""

    errors: list[str] = []
    ranges: list[tuple[int, int, str]] = []
    if not isinstance(verse, dict):
        return errors, ranges

    concepts = verse.get("begrippen")
    if not isinstance(concepts, list):
        errors.append(_error("CONCEPTS_INVALID", filename, f"{json_path}.begrippen"))
        concepts = []
    for index, concept in enumerate(concepts):
        concept_path = f"{json_path}.begrippen[{index}]"
        if not isinstance(concept, dict):
            errors.append(_error("CONCEPT_INVALID", filename, concept_path))
            continue
        if concept.get("conceptId") not in concept_ids:
            errors.append(_error("CONCEPT_UNKNOWN", filename, f"{concept_path}.conceptId"))
        references = concept.get("segmenten")
        if not isinstance(references, list):
            errors.append(_error("SEGMENT_REFERENCES_INVALID", filename, f"{concept_path}.segmenten"))
            continue
        for ref_index, reference in enumerate(references):
            if reference not in segment_positions:
                errors.append(
                    _error(
                        "SEGMENT_REFERENCE_UNKNOWN",
                        filename,
                        f"{concept_path}.segmenten[{ref_index}]",
                    )
                )

    citations = verse.get("citaten")
    if not isinstance(citations, list):
        errors.append(_error("CITATIONS_INVALID", filename, f"{json_path}.citaten"))
        citations = []
    for index, citation in enumerate(citations):
        citation_path = f"{json_path}.citaten[{index}]"
        if not isinstance(citation, dict):
            errors.append(_error("CITATION_INVALID", filename, citation_path))
            continue
        citation_id = citation.get("id")
        if not isinstance(citation_id, str) or not citation_id:
            errors.append(_error("CITATION_ID_MISSING", filename, f"{citation_path}.id"))
        elif citation_id in seen_citation_ids:
            errors.append(_error("CITATION_ID_DUPLICATE", filename, f"{citation_path}.id"))
        else:
            seen_citation_ids[citation_id] = f"{filename} {citation_path}.id"

        semantic_id = citation.get("semanticId")
        if not isinstance(semantic_id, str) or not SEMANTIC_ID_RE.fullmatch(semantic_id):
            errors.append(_error("SEMANTIC_ID_INVALID", filename, f"{citation_path}.semanticId"))

        start_id = citation.get("startSegment")
        end_id = citation.get("endSegment")
        start = segment_positions.get(start_id) if isinstance(start_id, str) else None
        end = segment_positions.get(end_id) if isinstance(end_id, str) else None
        if start is None:
            errors.append(_error("SEGMENT_REFERENCE_UNKNOWN", filename, f"{citation_path}.startSegment"))
        if end is None:
            errors.append(_error("SEGMENT_REFERENCE_UNKNOWN", filename, f"{citation_path}.endSegment"))
        if start is not None and end is not None:
            if start > end:
                errors.append(_error("CITATION_RANGE_INVALID", filename, citation_path))
            else:
                ranges.append((start, end, citation_path))

        speaker = citation.get("spreker")
        if not isinstance(speaker, dict):
            errors.append(_error("SPEAKER_ID_MISSING", filename, f"{citation_path}.spreker.id"))
            errors.append(_error("SPEAKER_TYPE_MISSING", filename, f"{citation_path}.spreker.type"))
        else:
            if not isinstance(speaker.get("id"), str) or not speaker.get("id"):
                errors.append(_error("SPEAKER_ID_MISSING", filename, f"{citation_path}.spreker.id"))
            if "type" not in speaker or speaker.get("type") in (None, ""):
                errors.append(_error("SPEAKER_TYPE_MISSING", filename, f"{citation_path}.spreker.type"))
            elif speaker.get("type") not in ALLOWED_SPEAKER_TYPES:
                errors.append(_error("SPEAKER_TYPE_INVALID", filename, f"{citation_path}.spreker.type"))
    return errors, ranges


def _validate_blocks(chapter: dict[str, Any], filename: str) -> list[str]:
    errors: list[str] = []
    verses = chapter.get("verzen") if isinstance(chapter.get("verzen"), list) else []
    verse_numbers = {
        verse.get("nummer")
        for verse in verses
        if isinstance(verse, dict)
        and isinstance(verse.get("nummer"), int)
        and not isinstance(verse.get("nummer"), bool)
    }
    coverage = {number: 0 for number in verse_numbers}
    blocks = chapter.get("blokken")
    if not isinstance(blocks, list):
        blocks = []
    for index, block in enumerate(blocks):
        block_path = f"$.blokken[{index}]"
        if not isinstance(block, dict):
            errors.append(_error("BLOCK_INVALID", filename, block_path))
            continue
        start = block.get("vanaf")
        end = block.get("tot")
        if (
            not isinstance(start, int)
            or isinstance(start, bool)
            or not isinstance(end, int)
            or isinstance(end, bool)
            or start > end
        ):
            errors.append(_error("BLOCK_RANGE_INVALID", filename, block_path))
            continue
        for number in range(start, end + 1):
            if number in coverage:
                coverage[number] += 1
            else:
                errors.append(_error("BLOCK_RANGE_UNKNOWN_VERSE", filename, block_path))
    if any(count > 1 for count in coverage.values()):
        errors.append(_error("BLOCKS_OVERLAP", filename, "$.blokken"))
    if any(count == 0 for count in coverage.values()) or (verse_numbers and not blocks):
        errors.append(_error("BLOCKS_INCOMPLETE", filename, "$.blokken"))
    return errors


def validate_chapter(
    repo_root: Path,
    chapter: Any,
    filename: str,
    expected_book: str,
    expected_chapter: int,
    concept_ids: set[str],
    source_cache: dict[str, Any],
    seen_segment_ids: dict[str, str],
    seen_citation_ids: dict[str, str],
) -> list[str]:
    """Valideer één hoofdstuk inclusief corpusbrede identifiers."""

    errors: list[str] = []
    if not isinstance(chapter, dict):
        return [_error("CHAPTER_INVALID", filename, "$" )]
    errors.extend(_validate_text_integrity(chapter, filename))
    errors.extend(_validate_no_strong_fields(chapter, filename))
    if chapter.get("schema") != 1:
        errors.append(_error("CHAPTER_SCHEMA", filename, "$.schema"))
    if chapter.get("editie") != "nl-opv":
        errors.append(_error("CHAPTER_EDITION", filename, "$.editie"))
    if chapter.get("boek") != expected_book:
        errors.append(_error("CHAPTER_BOOK", filename, "$.boek"))
    if chapter.get("hoofdstuk") != expected_chapter:
        errors.append(_error("CHAPTER_NUMBER", filename, "$.hoofdstuk"))

    verses = chapter.get("verzen")
    if not isinstance(verses, list) or not verses:
        errors.append(_error("VERSES_MISSING", filename, "$.verzen"))
        verses = []
    verse_numbers: list[Any] = [
        verse.get("nummer") if isinstance(verse, dict) else None for verse in verses
    ]
    valid_numbers = [
        number
        for number in verse_numbers
        if isinstance(number, int) and not isinstance(number, bool) and number > 0
    ]
    if len(valid_numbers) != len(verse_numbers):
        errors.append(_error("VERSE_NUMBER_INVALID", filename, "$.verzen"))
    if len(valid_numbers) != len(set(valid_numbers)):
        errors.append(_error("VERSE_DUPLICATE", filename, "$.verzen"))
    if valid_numbers != sorted(valid_numbers):
        errors.append(_error("VERSE_ORDER", filename, "$.verzen"))

    errors.extend(_validate_blocks(chapter, filename))
    segment_order: list[str] = []
    source_names: list[str] = []
    for index, verse in enumerate(verses):
        verse_errors, segment_ids, source_name = validate_verse(
            repo_root,
            verse,
            filename,
            f"$.verzen[{index}]",
            source_cache,
            seen_segment_ids,
        )
        errors.extend(verse_errors)
        segment_order.extend(segment_ids)
        if source_name is not None:
            source_names.append(source_name)

    if source_names and len(set(source_names)) != 1:
        errors.append(_error("SOURCE_FILE_INCONSISTENT", filename, "$.verzen"))
    elif source_names:
        source_doc = source_cache.get(source_names[0])
        if isinstance(source_doc, dict) and isinstance(source_doc.get("verses"), list):
            source_numbers = [
                source_verse.get("number")
                for source_verse in source_doc["verses"]
                if isinstance(source_verse, dict)
            ]
            if verse_numbers != source_numbers:
                errors.append(_error("VERSE_LIST_MISMATCH", filename, "$.verzen"))

    positions = {segment_id: index for index, segment_id in enumerate(segment_order)}
    ranges: list[tuple[int, int, str]] = []
    for index, verse in enumerate(verses):
        annotation_errors, verse_ranges = validate_annotations(
            verse,
            filename,
            f"$.verzen[{index}]",
            concept_ids,
            positions,
            seen_citation_ids,
        )
        errors.extend(annotation_errors)
        ranges.extend(verse_ranges)
    for first_index, first in enumerate(ranges):
        for second in ranges[first_index + 1 :]:
            a_start, a_end, _ = first
            b_start, b_end, _ = second
            if (a_start < b_start <= a_end < b_end) or (
                b_start < a_start <= b_end < a_end
            ):
                errors.append(_error("CITATION_RANGES_CROSSED", filename, "$.verzen"))
                return errors
    return errors


def _concept_ids(concepts: Any, filename: str) -> tuple[set[str], list[str]]:
    errors: list[str] = []
    identifiers: set[str] = set()
    if not isinstance(concepts, dict) or concepts.get("schema") != 1:
        errors.append(_error("CONCEPT_SCHEMA", filename, "$.schema"))
        return identifiers, errors
    entries = concepts.get("concepten")
    if not isinstance(entries, list):
        errors.append(_error("CONCEPT_LIST", filename, "$.concepten"))
        return identifiers, errors
    for index, concept in enumerate(entries):
        concept_id = concept.get("id") if isinstance(concept, dict) else None
        if not isinstance(concept_id, str) or not concept_id:
            errors.append(_error("CONCEPT_ID_MISSING", filename, f"$.concepten[{index}].id"))
        elif concept_id in identifiers:
            errors.append(_error("CONCEPT_ID_DUPLICATE", filename, f"$.concepten[{index}].id"))
        else:
            identifiers.add(concept_id)
    return identifiers, errors


def validate_corpus(repo_root: Path) -> list[str]:
    """Valideer alle in het OPV-manifest geregistreerde hoofdstukken."""

    root = Path(repo_root).resolve()
    errors: list[str] = []
    registry_file = "data/edities/manifest.json"
    edition_file = "data/edities/opv/manifest.json"
    concepts_file = "data/edities/opv/concepten.json"
    registry = _load_json(root, registry_file, errors)
    edition_manifest = _load_json(root, edition_file, errors)
    concepts = _load_json(root, concepts_file, errors)
    if registry is not None and edition_manifest is not None:
        errors.extend(validate_manifest(root, registry, edition_manifest))
    if concepts is None:
        return sorted(set(errors))
    errors.extend(_validate_text_integrity(concepts, concepts_file))
    errors.extend(_validate_no_strong_fields(concepts, concepts_file))
    concept_ids, concept_errors = _concept_ids(concepts, concepts_file)
    errors.extend(concept_errors)
    if edition_manifest is None:
        return sorted(set(errors))

    chapter_map = _book_chapters_from_edition_manifest(edition_manifest)
    source_cache: dict[str, Any] = {}
    seen_segment_ids: dict[str, str] = {}
    seen_citation_ids: dict[str, str] = {}
    for book in sorted(chapter_map):
        for chapter_number in chapter_map[book]:
            filename = f"data/edities/opv/chapters/{book}/{chapter_number}.json"
            chapter = _load_json(root, filename, errors)
            if chapter is None:
                continue
            errors.extend(
                validate_chapter(
                    root,
                    chapter,
                    filename,
                    book,
                    chapter_number,
                    concept_ids,
                    source_cache,
                    seen_segment_ids,
                    seen_citation_ids,
                )
            )
    return sorted(set(errors))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="hoofdmap van de repository",
    )
    args = parser.parse_args(argv)
    errors = validate_corpus(args.root)
    for error in errors:
        print(error)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
