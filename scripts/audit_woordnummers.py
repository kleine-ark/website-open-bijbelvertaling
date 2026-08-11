#!/usr/bin/env python3
"""Valideer en rapporteer bronvaste woordnummers in het volledige corpus."""

import json
import re
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
NUMBER_RE = re.compile(r"^(?:H\d+[A-Za-z]?|G\d+[A-Za-z]?|OVL\d+|OVG\d+)$")


def source_script(word):
    codepoints = [ord(char) for char in str(word or "") if char.isalpha()]
    if not codepoints:
        return None
    if any(0x0590 <= cp <= 0x05FF for cp in codepoints):
        return "hebrew"
    if any(0x0370 <= cp <= 0x03FF or 0x1F00 <= cp <= 0x1FFF for cp in codepoints):
        return "greek"
    if any(0x1200 <= cp <= 0x139F or 0x2D80 <= cp <= 0x2DDF for cp in codepoints):
        return "geez"
    if all(
        0x0041 <= cp <= 0x005A
        or 0x0061 <= cp <= 0x007A
        or 0x00C0 <= cp <= 0x024F
        for cp in codepoints
    ):
        return "latin"
    return "other"


def classify_unnumbered(word):
    script = source_script(word.get("woord") if isinstance(word, dict) else "")
    if not script:
        return "non_lexical_source_marker"
    if script == "hebrew":
        morph = str(word.get("morph") or "")
        if re.search(r"(?:^|/)Sp\w*", morph):
            return "hebrew_grammatical_segment"
        return "hebrew_unmapped_lexeme"
    if script in {"greek", "geez", "latin"}:
        return f"{script}_unmapped_lexeme"
    return "other_unmapped_token"


def audit():
    books = json.loads((DATA / "books.json").read_text(encoding="utf-8"))["books"]
    report = {
        "books": len(books),
        "books_with_numbers": 0,
        "verses": 0,
        "verses_with_ground_text": 0,
        "verses_with_numbers": 0,
        "verses_without_ground_text": 0,
        "ground_tokens": 0,
        "numbered_tokens": 0,
        "unnumbered_tokens": 0,
        "families": Counter(),
        "unnumbered_categories": Counter(),
        "unnumbered_by_book": Counter(),
        "missing_ground_text_by_book": Counter(),
        "missing_ground_text_field_state": Counter(),
        "missing_ground_text_refs": {},
        "invalid": [],
    }
    for book in books:
        book_has_numbers = False
        for chapter in book.get("chaptersIncluded", []):
            path = DATA / book["id"] / f"{chapter}.json"
            if not path.exists():
                continue
            data = json.loads(path.read_text(encoding="utf-8"))
            for verse in data.get("verses", []):
                if not isinstance(verse, dict):
                    continue
                report["verses"] += 1
                words = verse.get("grondtekst") or []
                if words:
                    report["verses_with_ground_text"] += 1
                else:
                    report["verses_without_ground_text"] += 1
                    report["missing_ground_text_by_book"][book["id"]] += 1
                    state = "field_absent" if "grondtekst" not in verse else "empty_list"
                    report["missing_ground_text_field_state"][state] += 1
                    report["missing_ground_text_refs"].setdefault(book["id"], []).append(
                        f"{chapter}:{verse.get('number')}"
                    )
                verse_has_numbers = False
                for word in words:
                    if not isinstance(word, dict):
                        continue
                    report["ground_tokens"] += 1
                    raw = str(word.get("strongs") or "").strip()
                    if not raw:
                        report["unnumbered_tokens"] += 1
                        report["unnumbered_categories"][classify_unnumbered(word)] += 1
                        report["unnumbered_by_book"][book["id"]] += 1
                        continue
                    numbers = raw.split()
                    valid = True
                    for number in numbers:
                        if not NUMBER_RE.fullmatch(number):
                            report["invalid"].append({
                                "book": book["id"], "chapter": chapter,
                                "verse": verse.get("number"), "number": number,
                            })
                            valid = False
                            continue
                        family = "OVL" if number.startswith("OVL") else (
                            "OVG" if number.startswith("OVG") else number[0]
                        )
                        report["families"][family] += 1
                    if valid:
                        report["numbered_tokens"] += 1
                        verse_has_numbers = True
                        book_has_numbers = True
                if verse_has_numbers:
                    report["verses_with_numbers"] += 1
        if book_has_numbers:
            report["books_with_numbers"] += 1
    report["families"] = dict(sorted(report["families"].items()))
    for key in (
        "unnumbered_categories",
        "unnumbered_by_book",
        "missing_ground_text_by_book",
        "missing_ground_text_field_state",
    ):
        report[key] = dict(sorted(report[key].items()))
    return report


if __name__ == "__main__":
    result = audit()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(1 if result["invalid"] or result["books_with_numbers"] != result["books"] else 0)
