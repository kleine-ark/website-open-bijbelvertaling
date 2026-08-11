#!/usr/bin/env python3
"""Importeer gereviewde inline woordnummerkoppelingen uit een gepinde USJ-bron."""

import argparse
import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STRONG_RE = re.compile(r"[HG]\d+[A-Za-z]?")
REVIEWED = "handmatig_gecontroleerd"


def _strongs(value):
    if isinstance(value, list):
        values = value
    else:
        values = STRONG_RE.findall(str(value or ""))
    return list(dict.fromkeys(str(item) for item in values if STRONG_RE.fullmatch(str(item))))


def parse_usj(path):
    """Lees woordniveau-Strongdata uit een USJ 3.x-bestand."""
    document = json.loads(Path(path).read_text(encoding="utf-8"))
    if document.get("type") != "USJ":
        raise ValueError(f"Geen USJ-document: {path}")

    verses = {}
    chapter = None
    verse = None

    def visit(items):
        nonlocal chapter, verse
        for item in items or []:
            if not isinstance(item, dict):
                continue
            kind = item.get("type")
            if kind == "chapter":
                chapter = int(item["number"])
                verse = None
            elif kind == "verse":
                if chapter is None:
                    raise ValueError("Vers vóór hoofdstuk in USJ")
                verse = int(str(item["number"]).split("-")[0])
                verses.setdefault((chapter, verse), [])
            elif kind == "char" and item.get("marker") == "w" and verse is not None:
                numbers = _strongs(item.get("strong"))
                if numbers:
                    text = "".join(part for part in item.get("content", []) if isinstance(part, str))
                    verses[(chapter, verse)].append({"text": text, "strongs": numbers})
            if kind not in {"char", "verse", "chapter"} and isinstance(item.get("content"), list):
                visit(item["content"])

    visit(document.get("content", []))
    return verses


def build_inline_mapping(review, external_tokens, local_tokens, source, reference):
    if review.get("reviewstatus") != REVIEWED:
        raise ValueError(f"Ongeldige reviewstatus voor {reference}: {review.get('reviewstatus')!r}")
    confidence = review.get("confidence")
    if not isinstance(confidence, (int, float)) or not 0 <= confidence <= 1:
        raise ValueError(f"Ongeldige confidence voor {reference}")

    source_indices = review.get("bronindices") or []
    ground_indices = review.get("grondindices", source_indices)
    try:
        external = [external_tokens[index] for index in source_indices]
        local = [local_tokens[index] for index in ground_indices]
    except (IndexError, TypeError):
        raise ValueError(f"Ongeldige bronvolgorde voor {reference}") from None

    external_numbers = [number for token in external for number in _strongs(token.get("strongs"))]
    local_numbers = [number for token in local for number in _strongs(token.get("strongs"))]
    if not external_numbers or external_numbers != local_numbers:
        raise ValueError(
            f"Afwijkende bronvolgorde voor {reference}: extern {external_numbers}, lokaal {local_numbers}"
        )

    return {
        "tekst": str(review["tekst"]),
        "voorkomen": int(review.get("voorkomen", 1)),
        "strongs": external_numbers,
        "bronwoorden": [str(token.get("woord") or "") for token in local],
        "transliteraties": [
            str(token.get("transliteratie") or token.get("translit") or "") for token in local
        ],
        "glossen": [str(token.get("gloss") or token.get("betekenis") or "") for token in local],
        "confidence": float(confidence),
        "reviewstatus": REVIEWED,
        "herkomst": {
            "dataset": source["id"],
            "versie": source["version"],
            "sha256": source["sha256"],
            "referentie": reference,
            "bronindices": list(source_indices),
        },
    }


def _anchor_key(mapping):
    return (str(mapping.get("tekst") or "").casefold(), int(mapping.get("voorkomen", 1)))


def merge_reviewed_mappings(verse, proposed):
    """Voeg alleen nieuwe ankers toe; bestaande mappings zijn autoritatief."""
    existing = verse.setdefault("woordnummers", [])
    existing_keys = {_anchor_key(mapping) for mapping in existing if isinstance(mapping, dict)}
    added = 0
    preserved = 0
    text = str(verse.get("text2026") or verse.get("textHerzien") or "")
    for mapping in proposed:
        key = _anchor_key(mapping)
        if key in existing_keys:
            preserved += 1
            continue
        if mapping.get("reviewstatus") != REVIEWED:
            continue
        if text.casefold().count(key[0]) < key[1]:
            raise ValueError(f"Anker {mapping.get('tekst')!r}#{key[1]} ontbreekt in Nederlandse tekst")
        existing.append(mapping)
        existing_keys.add(key)
        added += 1
    return added, preserved


def _sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def apply_review_file(review_path, source_dir, data_dir=None, write=False):
    """Bouw en merge alle gereviewde mappings uit één reproduceerbaar reviewbestand."""
    review = json.loads(Path(review_path).read_text(encoding="utf-8"))
    source = review["source"]
    source_dir = Path(source_dir)
    data_dir = Path(data_dir or ROOT / "data")
    report = {"mode": "write" if write else "dry-run", "added": 0, "preserved": 0, "verses": 0}

    for book in review.get("books", []):
        source_path = source_dir / book["source_file"]
        expected_hash = str(book.get("source_file_sha256") or "").upper()
        if expected_hash and _sha256(source_path) != expected_hash:
            raise ValueError(f"SHA-256 wijkt af voor {source_path.name}")
        external_verses = parse_usj(source_path)
        chapter_path = data_dir / book["repo_book"] / f"{book['chapter']}.json"
        original = chapter_path.read_text(encoding="utf-8")
        chapter = json.loads(original)
        by_number = {int(verse["number"]): verse for verse in chapter.get("verses", [])}

        for verse_review in book.get("verses", []):
            number = int(verse_review["verse"])
            verse = by_number[number]
            reference = f"{book['code']} {book['chapter']}:{number}"
            external = external_verses.get((int(book["chapter"]), number), [])
            local = verse.get("grondtekst") or []
            proposed = [
                build_inline_mapping(item, external, local, source, reference)
                for item in verse_review.get("mappings", [])
            ]
            added, preserved = merge_reviewed_mappings(verse, proposed)
            report["added"] += added
            report["preserved"] += preserved
            report["verses"] += 1

        if write and report["added"]:
            rendered = json.dumps(chapter, ensure_ascii=False, indent=2) + "\n"
            chapter_path.write_text(rendered, encoding="utf-8")
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--review", type=Path, required=True)
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    report = apply_review_file(args.review, args.source_dir, args.data_dir, args.write)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
