#!/usr/bin/env python3
"""Publiceer gecontroleerde TR-koppelingen voor Johannes 5 in versbatches."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from rebuild_nt_tr_strongs import load_tr_chapter
from rebuild_johannes2_tr_strongs import mapping, r

ROOT = Path(__file__).resolve().parents[1]

SPECS = {
    1: [("Na deze", r(0, 1)), ("was een feest", r(2, 3)),
        ("van de Joden", r(4, 5)), ("en Jezus ging op", r(6, 9)),
        ("naar Jeruzalem", r(10, 11))],
    2: [("En er is te Jeruzalem", r(0, 4)), ("aan de Schaapspoort", r(5, 7)),
        ("een badwater", r(8)), ("dat in het Hebreeuws toegenaamd wordt Bethesda", r(9, 12)),
        ("hebbende vijf zalen", r(13, 15))],
    3: [("In deze lag", r(0, 2)), ("een grote menigte", r(3, 4)),
        ("van zieken, blinden, kreupelen, verdorden", r(5, 9)),
        ("wachtende", r(10)), ("op de roering van het water", r(11, 14))],
    4: [("Want een engel", r(0, 1)), ("op zekeren tijd", r(2, 3)),
        ("daalde neer", r(4)), ("in dat badwater", r(5, 7)), ("en beroerde het water", r(8, 11)),
        ("die dan eerst daarin kwam", r(12, 15)), ("na de beroering van het water", r(16, 20)),
        ("die werd gezond", r(21, 22)), ("van wat ziekte hij ook bevangen was", r(23, 26))],
    5: [("En daar was een zeker mens", r(0, 4)), ("die acht en dertig jaren", r(5, 8)),
        ("ziek gelegen had", r(9, 12))],
    6: [("Jezus, ziende deze liggen", r(0, 4)), ("en wetende", r(5, 6)),
        ("dat hij nu langen tijd gelegen had", r(7, 11)), ("zei tot hem", r(12, 13)),
        ("Wilt u gezond worden", r(14, 16))],
    7: [("De zieke antwoordde Hem", r(0, 3)), ("Heere", r(4)),
        ("ik heb geen mens", r(5, 7)), ("om mij te werpen in het badwater", [8, 13, 14, 15, 16, 17]),
        ("wanneer het water beroerd wordt", r(9, 12)),
        ("en terwijl ik kom", r(18, 22)), ("zo daalt een ander voor mij neer", r(23, 26))],
    8: [("Jezus zei tot hem", r(0, 3)), ("Sta op", r(4)),
        ("neem uw bed op", r(5, 8)), ("en wandel", r(9, 10))],
    9: [("En meteen werd de mens gezond", r(0, 5)), ("en nam zijn bed op", r(6, 10)),
        ("en wandelde", r(11, 12)), ("En het was sabbat", r(13, 15)),
        ("op deze dag", r(16, 19))],
    10: [("De Joden zeiden dan", r(0, 3)), ("tot degene, die genezen was", r(4, 5)),
         ("Het is sabbat", r(6, 7)), ("het is u niet geoorloofd", r(8, 10)),
         ("het bed te dragen", r(11, 13))],
}


def build(utr_path: Path, osis_path: Path, write=False):
    source = load_tr_chapter(utr_path, osis_path, chapter=5, osis_book="John")
    chapter_path = ROOT / "data" / "johannes" / "5.json"
    chapter = json.loads(chapter_path.read_text(encoding="utf-8"))
    review = {"book": "johannes", "chapter": 5, "reviewed_through": 10, "verses": {}}
    for verse in chapter["verses"][:10]:
        number = int(verse["number"]); tokens = source[number]; groups = SPECS[number]
        covered = [index for _, token_ids in groups for index in token_ids]
        if sorted(covered) != list(range(len(tokens))) or len(set(covered)) != len(tokens):
            raise ValueError(f"Johannes 5:{number}: onvolledige of dubbele handmatige review")
        verse["grondtekst"] = [{
            "woord": token["woord"], "strongs": token["display_strong"],
            "lemma_strongs": token["lemma_strong"], "morfologie": token["morphology"],
            **({"tvm": token["tvm"]} if token.get("tvm") else {}),
        } for token in tokens]
        verse["woordnummers"] = [mapping(anchor, ids, tokens, number) for anchor, ids in groups]
        for item in verse["woordnummers"]:
            item["herkomst"]["referentie"] = f"JHN 5:{number}"
        review["verses"][str(number)] = [
            {"tekst": anchor, "bronindices": ids, "reviewstatus": "handmatig_gecontroleerd"}
            for anchor, ids in groups
        ]
    if write:
        chapter_path.write_text(json.dumps(chapter, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        review_dir = ROOT / "data" / "woordnummers-review"; review_dir.mkdir(exist_ok=True)
        (review_dir / "johannes-5.json").write_text(json.dumps(review, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        inline_path = ROOT / "data" / "woordnummers-inline" / "johannes.json"
        inline = json.loads(inline_path.read_text(encoding="utf-8"))
        inline["chapters"]["5"] = {
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
