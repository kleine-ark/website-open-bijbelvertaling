#!/usr/bin/env python3
"""Build the revision-bound catalog consumed by the collaboration API.

The catalog describes reviewable data; it never contains reviewer identities.
Those identities and immutable decisions live in the server-side audit store.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "data" / "review-catalog.json"


def canonical_hash(value: object) -> str:
    encoded = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def text_review_payload(chapter: dict) -> dict:
    intro = chapter.get("chapterIntro") or {}
    if not isinstance(intro, dict):
        raise ValueError("chapterIntro moet een object zijn")
    chapter_verses = chapter.get("verses")
    if not isinstance(chapter_verses, list):
        raise ValueError("verses moet een lijst zijn")
    verses = []
    for verse in chapter_verses:
        if not isinstance(verse, dict):
            raise ValueError("ieder vers moet een object zijn")
        margin_notes = verse.get("marginNotes") or []
        if not isinstance(margin_notes, list):
            raise ValueError("marginNotes moet een lijst zijn")
        notes = []
        for note in margin_notes:
            if not isinstance(note, dict):
                raise ValueError("iedere kanttekening moet een object zijn")
            notes.append({
                "marker": note.get("marker"),
                "type": note.get("type"),
                "text2026": note.get("text2026"),
            })
        verses.append({
            "number": verse.get("number"),
            "text2026": verse.get("text2026"),
            "text2026_html": verse.get("text2026_html"),
            "marginNotes": notes,
        })
    return {
        "number": chapter.get("number"),
        "chapterIntro": {"text2026": intro.get("text2026")},
        "verses": verses,
    }


def text_revision(chapter: dict) -> str:
    return canonical_hash(text_review_payload(chapter))


def location_review_payload(feature: dict) -> dict:
    if not isinstance(feature, dict) or not isinstance(feature.get("properties"), dict):
        raise ValueError("ieder geografisch punt moet properties hebben")
    properties = dict(feature["properties"])
    properties.pop("humanReviewed", None)
    properties.pop("koppelingStatus", None)
    refs = []
    source_refs = properties.get("refs", [])
    if not isinstance(source_refs, list):
        raise ValueError("geografische refs moet een lijst zijn")
    for ref in source_refs:
        if not isinstance(ref, dict):
            raise ValueError("iedere geografische ref moet een object zijn")
        item = dict(ref)
        item.pop("status", None)
        refs.append(item)
    if "refs" in properties:
        properties["refs"] = refs
    return {"geometry": feature.get("geometry"), "properties": properties}


def is_verified(verified: dict, book_id: str, chapter: int) -> bool:
    value = verified.get(book_id)
    return value == "all" or isinstance(value, list) and chapter in value


def build_catalog(root: Path = ROOT) -> dict:
    data = root / "data"
    books = json.loads((data / "books.json").read_text(encoding="utf-8"))["books"]
    verified = json.loads(
        (data / "verified-chapters.json").read_text(encoding="utf-8")
    )
    geography = json.loads(
        (data / "geografie-runtime.geojson").read_text(encoding="utf-8")
    )

    book_ids = [book["id"] for book in books]
    if len(book_ids) != len(set(book_ids)):
        raise ValueError("books.json bevat dubbele boek-id's")
    unknown_verified = set(verified) - set(book_ids)
    if unknown_verified:
        raise ValueError(f"reviewstatus voor onbekende boeken: {sorted(unknown_verified)}")

    subjects = []
    for book in books:
        book_id = book["id"]
        included = book.get("chaptersIncluded")
        if not isinstance(included, list) or len(included) != len(set(included)):
            raise ValueError(f"ongeldige hoofdstuklijst voor {book_id}")
        verified_value = verified.get(book_id)
        if verified_value is not None and verified_value != "all":
            if (
                not isinstance(verified_value, list)
                or len(verified_value) != len(set(verified_value))
                or any(chapter not in included for chapter in verified_value)
            ):
                raise ValueError(f"ongeldige reviewstatus voor {book_id}")
        for chapter_number in included:
            path = data / book_id / f"{chapter_number}.json"
            chapter = json.loads(path.read_text(encoding="utf-8"))
            approved = is_verified(verified, book_id, chapter_number)
            subject = {
                "type": "text-chapter",
                "id": f"{book_id}/{chapter_number}",
                "revision": text_revision(chapter),
                "label": f"{book['nameDutch']} {chapter_number}",
                "href": f"index.html#{book_id}/{chapter_number}",
                "source": f"data/{book_id}/{chapter_number}.json",
                "publishedStatus": "approved" if approved else "pending",
                "metadata": {
                    "book": book_id,
                    "chapter": chapter_number,
                    "verses": len(chapter.get("verses", [])),
                },
            }
            if approved:
                subject["migrationSource"] = "data/verified-chapters.json"
            subjects.append(subject)

    features = geography.get("features")
    if not isinstance(features, list):
        raise ValueError("geografie-runtime.geojson moet features bevatten")
    for feature in features:
        if not isinstance(feature, dict) or not isinstance(feature.get("properties"), dict):
            raise ValueError("ieder geografisch punt moet properties hebben")
        properties = feature["properties"]
        subject_id = properties.get("id")
        if not subject_id:
            raise ValueError("Geografisch punt zonder stabiele id")
        if not isinstance(properties.get("humanReviewed"), bool):
            raise ValueError(f"humanReviewed moet boolean zijn voor {subject_id}")
        approved = properties.get("humanReviewed") is True
        subject = {
            "type": "location",
            "id": subject_id,
            "revision": canonical_hash(location_review_payload(feature)),
            "label": properties.get("naam") or subject_id,
            "href": f"plaats.html?id={subject_id}",
            "source": "data/geografie-runtime.geojson",
            "publishedStatus": "approved" if approved else "pending",
            "metadata": {
                "certainty": properties.get("zekerheid", "onzeker"),
                "sourceDataset": (properties.get("bron") or {}).get("dataset"),
            },
        }
        if approved:
            subject["migrationSource"] = "data/geografie-runtime.geojson"
        subjects.append(subject)

    subject_keys = [(item["type"], item["id"]) for item in subjects]
    if len(subject_keys) != len(set(subject_keys)):
        raise ValueError("reviewcatalogus bevat dubbele onderwerp-id's")
    subjects.sort(key=lambda item: (item["type"], item["label"].casefold(), item["id"]))
    catalog = {
        "schemaVersion": 1,
        "subjectTypes": {
            "text-chapter": "Bijbelhoofdstuk",
            "location": "Geografische locatie",
        },
        "subjects": subjects,
    }
    catalog["catalogRevision"] = canonical_hash(catalog)
    return catalog


def main() -> None:
    catalog = build_catalog()
    OUTPUT.write_text(
        json.dumps(catalog, ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    print(
        f"{OUTPUT.relative_to(ROOT)}: {len(catalog['subjects'])} reviewonderwerpen"
    )


if __name__ == "__main__":
    main()
