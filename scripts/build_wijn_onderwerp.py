#!/usr/bin/env python3
"""Bouw het onderwerp Wijn uit alle letterlijke vermeldingen in de Bijbeltekst."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
from typing import Any

try:
    from scripts.build_corpus_naslag import load_books, load_corpus
except ModuleNotFoundError:  # rechtstreeks uitgevoerd vanuit scripts/
    from build_corpus_naslag import load_books, load_corpus


ROOT = Path(__file__).resolve().parents[1]
WIJN = re.compile(r"(?<![0-9A-Za-zÀ-ÖØ-öø-ÿ-])wijn(?![0-9A-Za-zÀ-ÖØ-öø-ÿ-])", re.I)
TOP_TIEN = [
    "genesis 14:18",
    "numeri 6:3",
    "deuteronomium 14:26",
    "psalmen 104:15",
    "spreuken 20:1",
    "jesaja 5:11",
    "johannes 2:9",
    "romeinen 14:21",
    "efeziers 5:18",
    "openbaring 19:15",
]


def _json_dump(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def build_wijn(root: Path = ROOT, *, write: bool = True) -> dict[str, Any]:
    """Vind alle zichtbare verzen met het zelfstandige woord `wijn`."""
    books = load_books(root)
    corpus = load_corpus(root, include_ethiopic=True)
    refs = [vers.ref for vers in corpus if WIJN.search(vers.text)]
    ref_set = set(refs)
    ontbrekend = [ref for ref in TOP_TIEN if ref not in ref_set]
    if ontbrekend:
        raise ValueError(f"Top 10 bevat geen wijnverzen: {', '.join(ontbrekend)}")

    tag = {
        "id": "wijn",
        "naam": "Wijn in de Bijbel",
        "beschrijving": "Teksten waarin wijn wordt genoemd: als gave, offer, drank, waarschuwing en beeldspraak.",
        "kleur": "#7a3f4f",
        "selectiemethode": "alle-letterlijke-vermeldingen-van-wijn",
        "topTien": TOP_TIEN,
        "reviewStatus": "automatisch-geïdentificeerd",
        "humanReviewed": False,
        "verzen": [
            {
                "ref": ref,
                "rang": 1 if ref in TOP_TIEN else 2,
                "reviewStatus": "automatisch-geïdentificeerd",
                "humanReviewed": False,
            }
            for ref in refs
        ],
    }
    per_book = [
        {
            "boek": book["id"],
            "naam": book["nameDutch"],
            "gescand": True,
            "verzenGetagd": sum(ref.startswith(book["id"] + " ") for ref in refs),
        }
        for book in books
    ]
    report = {
        "onderwerp": "wijn",
        "selectiemethode": tag["selectiemethode"],
        "boekenGescand": len(books),
        "verzenGescand": len(corpus),
        "verzenGetagd": len(refs),
        "boekenMetTreffers": sum(book["verzenGetagd"] > 0 for book in per_book),
        "topTien": TOP_TIEN,
        "reviewStatus": tag["reviewStatus"],
        "humanReviewed": False,
        "perBoek": per_book,
    }
    result = {"tag": tag, "report": report}

    if write:
        data = root / "data"
        _json_dump(data / "onderwerp-wijn-dekking.json", report)
        tags_path = data / "tags.json"
        tags_doc = json.loads(tags_path.read_text(encoding="utf-8"))
        tags = tags_doc.get("tags", [])
        tags_doc["tags"] = [item for item in tags if item.get("id") != "wijn"] + [tag]
        _json_dump(tags_path, tags_doc)

    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="scan zonder bestanden te wijzigen")
    args = parser.parse_args()
    built = build_wijn(write=not args.check)
    print(json.dumps(built["report"], ensure_ascii=False, indent=2))
