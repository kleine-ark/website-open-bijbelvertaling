#!/usr/bin/env python3
"""Publiceer gecontroleerde TR-koppelingen voor Johannes 4 in versbatches."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from rebuild_nt_tr_strongs import load_tr_chapter
from rebuild_johannes2_tr_strongs import mapping, r

ROOT = Path(__file__).resolve().parents[1]

SPECS = {
    1: [("Als dan", r(0, 1)), ("de Heere verstond", r(2, 4)),
        ("dat de Farizeeën gehoord hadden", r(5, 8)), ("dat Jezus", r(9, 10)),
        ("meer discipelen maakte", r(11, 13)), ("en doopte", r(14, 15)),
        ("dan Johannes", r(16, 17))],
    2: [("Hoewel", r(0)), ("Jezus zelf niet doopte", r(1, 4)),
        ("maar Zijn discipelen", r(5, 8))],
    3: [("Zo verliet Hij Judea", r(0, 2)), ("en ging opnieuw heen", r(3, 5)),
        ("naar Galilea", r(6, 8))],
    4: [("En Hij moest", r(0, 2)), ("door Samaria gaan", r(3, 6))],
    5: [("Hij kwam dan", r(0, 1)), ("in een stad van Samaria", r(2, 5)),
        ("genoemd Sichar", r(6, 7)), ("nabij het stuk land", r(8, 10)),
        ("dat Jakob zijn zoon Jozef gaf", r(11, 17))],
    6: [("En daar was", r(0, 2)), ("de fontein Jakobs", r(3, 5)),
        ("Jezus dan", r(6, 8)), ("vermoeid zijnde van de reize", r(9, 12)),
        ("zat zo neer naast de fontein", r(13, 17)),
        ("Het was ongeveer het zesde uur", r(18, 21))],
    7: [("Er kwam een vrouw uit Samaria", r(0, 4)), ("om water te putten", r(5, 6)),
        ("Jezus zei tot haar", r(7, 10)), ("Geef Mij te drinken", r(11, 13))],
    8: [("Want Zijn discipelen", r(0, 3)), ("waren heengegaan in de stad", r(4, 7)),
        ("opdat zij zouden eten kopen", r(8, 10))],
    9: [("Zo zei dan", r(0, 2)), ("de Samaritaanse vrouw", r(3, 6)),
        ("Hoe begeert U, Die een Jood bent", r(7, 10)), ("van mij te drinken", r(11, 14)),
        ("die een Samaritaanse vrouw ben", r(15, 17)),
        ("Want de Joden houden geen gemeenschap", r(18, 21)), ("met de Samaritanen", r(22))],
    10: [("Jezus antwoordde en zei tot haar", r(0, 4)), ("Als", r(5)), ("kende", r(6)),
         ("de gave van God", r(7, 10)), ("en Wie Hij is", r(11, 13)),
         ("Die tot u zegt", r(14, 16)), ("Geef Mij te drinken", r(17, 19)),
         ("zo zou u van Hem hebben begeerd", r(20, 23)),
         ("en", r(24)), ("gegeven hebben", r(25)), ("zou", r(26)), ("u", r(27)),
         ("water", r(28)), ("levend", r(29))],
}


def build(utr_path: Path, osis_path: Path, write=False):
    source = load_tr_chapter(utr_path, osis_path, chapter=4, osis_book="John")
    chapter_path = ROOT / "data" / "johannes" / "4.json"
    chapter = json.loads(chapter_path.read_text(encoding="utf-8"))
    review = {"book": "johannes", "chapter": 4, "reviewed_through": 10, "verses": {}}
    for verse in chapter["verses"][:10]:
        number = int(verse["number"]); tokens = source[number]; groups = SPECS[number]
        covered = [index for _, token_ids in groups for index in token_ids]
        if sorted(covered) != list(range(len(tokens))) or len(set(covered)) != len(tokens):
            raise ValueError(f"Johannes 4:{number}: onvolledige of dubbele handmatige review")
        verse["grondtekst"] = [{
            "woord": token["woord"], "strongs": token["display_strong"],
            "lemma_strongs": token["lemma_strong"], "morfologie": token["morphology"],
        } for token in tokens]
        verse["woordnummers"] = [mapping(anchor, ids, tokens, number) for anchor, ids in groups]
        for item in verse["woordnummers"]:
            item["herkomst"]["referentie"] = f"JHN 4:{number}"
        review["verses"][str(number)] = [
            {"tekst": anchor, "bronindices": ids, "reviewstatus": "handmatig_gecontroleerd"}
            for anchor, ids in groups
        ]
    if write:
        chapter_path.write_text(json.dumps(chapter, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        review_dir = ROOT / "data" / "woordnummers-review"; review_dir.mkdir(exist_ok=True)
        (review_dir / "johannes-4.json").write_text(json.dumps(review, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        inline_path = ROOT / "data" / "woordnummers-inline" / "johannes.json"
        inline = json.loads(inline_path.read_text(encoding="utf-8"))
        inline["chapters"]["4"] = {
            str(v["number"]): v["woordnummers"] for v in chapter["verses"][:10]
        }
        inline_path.write_text(json.dumps(inline, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"verses": 10, "tokens": sum(len(source[n]) for n in range(1, 11))}


def main():
    parser = argparse.ArgumentParser(); parser.add_argument("--utr", type=Path, required=True)
    parser.add_argument("--osis", type=Path, required=True); parser.add_argument("--write", action="store_true")
    args = parser.parse_args(); print(json.dumps(build(args.utr, args.osis, args.write), indent=2))


if __name__ == "__main__":
    main()
