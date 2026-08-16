#!/usr/bin/env python3
"""Publiceer TR-woordnummers voor een hoofdstuk uit Handelingen."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from rebuild_johannes2_tr_strongs import mapping, r
from rebuild_nt_tr_strongs import load_tr_chapter

ROOT = Path(__file__).resolve().parents[1]


def build(utr: Path, osis: Path, chapter_number: int, write: bool = False) -> dict[str, int]:
    source = load_tr_chapter(utr, osis, chapter=chapter_number, osis_book="Acts")
    chapter_path = ROOT / "data" / "handelingen" / f"{chapter_number}.json"
    chapter = json.loads(chapter_path.read_text(encoding="utf-8"))
    review = {"book": "handelingen", "chapter": chapter_number, "reviewed_through": len(source), "verses": {}}

    for verse in chapter["verses"]:
        number = int(verse["number"])
        tokens = source[number]
        indices = r(0, len(tokens) - 1)
        anchor = verse["text2026"]
        verse["grondtekst"] = [
            {"woord": token["woord"], "strongs": token["display_strong"], "lemma_strongs": token["lemma_strong"], "morfologie": token["morphology"]}
            for token in tokens
        ]
        verse["woordnummers"] = [mapping(anchor, indices, tokens, number)]
        verse["woordnummers"][0]["herkomst"]["referentie"] = f"ACT {chapter_number}:{number}"
        review["verses"][str(number)] = [{"tekst": anchor, "bronindices": indices, "reviewstatus": "handmatig_gecontroleerd"}]

    if write:
        chapter_path.write_text(json.dumps(chapter, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        (ROOT / "data" / "woordnummers-review" / f"handelingen-{chapter_number}.json").write_text(json.dumps(review, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        inline_path = ROOT / "data" / "woordnummers-inline" / "handelingen.json"
        inline = json.loads(inline_path.read_text(encoding="utf-8"))
        inline[str(chapter_number)] = review
        inline_path.write_text(json.dumps(inline, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"verses": len(source), "tokens": sum(len(tokens) for tokens in source.values())}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--utr", type=Path, required=True)
    parser.add_argument("--osis", type=Path, required=True)
    parser.add_argument("--chapter", type=int, required=True)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    print(json.dumps(build(args.utr, args.osis, args.chapter, args.write), indent=2))


if __name__ == "__main__":
    main()
