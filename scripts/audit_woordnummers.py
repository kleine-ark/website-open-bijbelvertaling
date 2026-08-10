#!/usr/bin/env python3
"""Valideer en rapporteer bronvaste woordnummers in het volledige corpus."""

import json
import re
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
NUMBER_RE = re.compile(r"^(?:H\d+[A-Za-z]?|G\d+[A-Za-z]?|OVL\d+|OVG\d+)$")


def audit():
    books = json.loads((DATA / "books.json").read_text(encoding="utf-8"))["books"]
    report = {
        "books": len(books),
        "books_with_numbers": 0,
        "verses": 0,
        "verses_with_ground_text": 0,
        "verses_with_numbers": 0,
        "ground_tokens": 0,
        "numbered_tokens": 0,
        "families": Counter(),
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
                verse_has_numbers = False
                for word in words:
                    if not isinstance(word, dict):
                        continue
                    report["ground_tokens"] += 1
                    raw = str(word.get("strongs") or "").strip()
                    if not raw:
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
    return report


if __name__ == "__main__":
    result = audit()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(1 if result["invalid"] or result["books_with_numbers"] != result["books"] else 0)
