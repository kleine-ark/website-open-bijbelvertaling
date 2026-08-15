#!/usr/bin/env python3
"""Publiceer de handmatig beoordeelde TR-koppelingen voor Johannes 2."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from rebuild_nt_tr_strongs import load_tr_chapter

ROOT = Path(__file__).resolve().parents[1]
SOURCE_ID = "robinson-scrivener-tr"
SOURCE_VERSION = "7fd4d02c3e5adebd379ebfbc824040820dde10fc"
SOURCE_SHA256 = "77FBB830AE3E11B79F7F47A8E68A119DC77F0722EBCC99BB00111702797BFFE5"


def r(start, end=None):
    return list(range(start, start + 1 if end is None else end + 1))


# (Nederlands anker, nulgebaseerde TR-indices). De groepen zijn inhoudelijk
# beoordeeld; woordvolgordeverschillen blijven binnen de passende woordgroep.
SPECS = {
    1: [("En", r(0)), ("op de derde dag", r(1, 4)), ("was er een bruiloft", r(5, 6)),
        ("te Kana in Galilea", r(7, 10)), ("en de moeder van Jezus", r(11, 16)), ("daar", r(17))],
    2: [("En Jezus was ook uitgenodigd", r(0, 4)), ("en Zijn discipelen", r(5, 8)),
        ("tot de bruiloft", r(9, 11))],
    3: [("En als er wijn ontbrak", r(0, 2)), ("zei de moeder van Jezus tot Hem", r(3, 9)),
        ("Zij hebben geen wijn", r(10, 12))],
    4: [("Jezus zei tot haar", r(0, 3)), ("wat heb Ik met u te doen", r(4, 8)),
        ("Mijn uur is nog niet gekomen", r(9, 13))],
    5: [("Zijn moeder zei", r(0, 3)), ("tot de dienaren", r(4, 5)),
        ("Zo wat", r(6, 8)), ("Hij u zal zeggen", r(9, 10)), ("doet dat", r(11))],
    6: [("En daar waren", r(0, 2)), ("zes stenen watervaten gesteld", r(3, 6)),
        ("naar de reiniging van de Joden", r(7, 11)), ("elk houdende", r(12, 13)),
        ("twee of drie metreten", r(14, 17))],
    7: [("Jezus zei tot hen", r(0, 3)), ("Vul de watervaten met water", r(4, 7)),
        ("En zij vulden ze", r(8, 10)), ("tot boven toe", r(11, 12))],
    8: [("En Hij zei tot hen", r(0, 2)), ("Schept nu", r(3, 4)),
        ("en draagt het tot de hofmeester", r(5, 8)), ("en zij droegen het", r(9, 10))],
    9: [("Als nu de hofmeester", r(0, 4)), ("het water, dat wijn geworden was", r(5, 8)),
        ("en hij wist niet, vanwaar de wijn was", r(9, 13)),
        ("maar de dienaren", r(14, 16)), ("wisten het", r(17)),
        ("die het water geschept hadden", r(18, 21)), ("zo riep", r(22)),
        ("de hofmeester", r(25, 26)), ("de bruidegom", r(23, 24))],
    10: [("En zei tot hem", r(0, 2)), ("Alle man", r(3, 4)),
         ("zet eerst de goede wijn op", r(5, 9)), ("en wanneer men wel gedronken heeft", r(10, 12)),
         ("dan de minderen", r(13, 15)), ("maar u hebt de goede wijn", r(16, 20)),
         ("tot nu toe", r(21, 22))],
    11: [("Dit", r(0)), ("gedaan", r(1)), ("begin", r(2, 3)),
         ("van de tekenen", r(4, 5)), ("Jezus", r(6, 7)),
         ("te Kana in Galilea", r(8, 11)), ("en heeft Zijn heerlijkheid geopenbaard", r(12, 16)),
         ("en Zijn discipelen geloofden in Hem", r(17, 23))],
    12: [("Daarna", r(0, 1)), ("ging Hij af naar Kapernaüm", r(2, 5)),
         ("en Zijn moeder", r(6, 9)), ("en Zijn broers", r(10, 13)),
         ("en Zijn discipelen", r(14, 17)), ("en zij bleven daar", r(18, 20)),
         ("niet vele dagen", r(21, 23))],
    13: [("En het pascha van de Joden was nabij", r(0, 6)),
         ("en Jezus ging op naar Jeruzalem", r(7, 12))],
    14: [("En Hij vond in de tempel", r(0, 4)), ("die ossen", r(5, 7)),
         ("en schapen", r(8, 9)), ("en duiven", r(10, 11)),
         ("en de bankiers daar zittende", r(12, 15))],
    15: [("En een gesel van touwtjes gemaakt hebbende", r(0, 4)),
         ("dreef Hij ze allen uit de tempel", r(5, 9)), ("ook de schapen en de ossen", r(10, 15)),
         ("en het geld van de bankiers stortte Hij uit", r(16, 21)),
         ("en keerde de tafelen om", r(22, 25))],
    16: [("En Hij zei tot degenen, die de duiven verkochten", r(0, 5)),
         ("Neem deze dingen van hier weg", r(6, 8)), ("maak niet", r(9, 10)),
         ("het huis van Mijn Vader", r(11, 15)), ("tot een huis van koophandel", r(16, 17))],
    17: [("En Zijn discipelen werden indachtig", r(0, 4)), ("dat er geschreven is", r(5, 7)),
         ("De ijver van Uw huis", r(8, 12)), ("heeft mij verslonden", r(13, 14))],
    18: [("De Joden antwoordden dan", r(0, 3)), ("en zeiden tot Hem", r(4, 6)),
         ("Wat teken toont U ons", r(7, 10)), ("dat U deze dingen doet", r(11, 13))],
    19: [("Jezus antwoordde en zei tot hen", r(0, 5)), ("Breek deze tempel", r(6, 9)),
         ("en in drie dagen", r(10, 13)), ("zal Ik deze oprichten", r(14, 15))],
    20: [("De Joden zeiden dan", r(0, 3)), ("Zes en veertig jaren", r(4, 7)),
         ("is over deze tempel gebouwd", r(8, 11)), ("en U", r(12, 13)),
         ("in drie dagen", r(14, 16)), ("oprichten", r(17, 18))],
    21: [("Maar Hij zei", r(0, 2)), ("dit van", r(3)), ("de tempel van Zijn lichaam", r(4, 8))],
    22: [("Daarom, als Hij opgestaan was van de doden", r(0, 4)),
         ("werden Zijn discipelen gedachtig", r(5, 8)), ("dat Hij dit tot hen gezegd had", r(9, 12)),
         ("en zij geloofden de Schrift", r(13, 16)), ("en het woord", r(17, 19)),
         ("dat Jezus gesproken had", r(20, 23))],
    23: [("En als Hij te Jeruzalem was", r(0, 4)), ("op het pascha", r(5, 7)),
         ("in het feest", r(8, 10)), ("geloofden velen", r(11, 12)),
         ("in Zijn Naam", r(13, 16)), ("ziende Zijn tekenen", r(17, 20)),
         ("die Hij deed", r(21, 22))],
    24: [("Maar Jezus Zelf", r(0, 3)), ("betrouwde hun Zichzelf niet", r(4, 7)),
         ("omdat Hij", r(8, 10)), ("hen allen kende", r(11, 12))],
    25: [("En omdat Hij niet nodig had", r(0, 4)), ("dat iemand getuigen zou", r(5, 7)),
         ("van de mens", r(8, 10)), ("want Hij Zelf wist", r(11, 13)),
         ("wat in de mens was", r(14, 18))],
}


def mapping(anchor, token_ids, tokens, verse):
    chosen = [tokens[index] for index in token_ids]
    record = {
        "tekst": anchor,
        "voorkomen": 1,
        "strongs": [token["display_strong"] for token in chosen],
        "lemma_strongs": [token["lemma_strong"] for token in chosen],
        "morfologie": [token["morphology"] for token in chosen],
        "bronwoorden": [token["woord"] for token in chosen],
        "transliteraties": [str(token.get("transliteratie") or "") for token in chosen],
        "glossen": [str(token.get("gloss") or token.get("betekenis") or "") for token in chosen],
        "status": "vertaald",
        "confidence": 1.0,
        "reviewstatus": "handmatig_gecontroleerd",
        "herkomst": {
            "dataset": SOURCE_ID,
            "versie": SOURCE_VERSION,
            "sha256": SOURCE_SHA256,
            "referentie": f"JHN 2:{verse}",
            "bronindices": token_ids,
        },
    }
    tvm = [token.get("tvm") for token in chosen]
    if any(tvm):
        record["tvm"] = tvm
    return record


def build(utr_path: Path, osis_path: Path, write=False):
    source = load_tr_chapter(utr_path, osis_path, chapter=2, osis_book="John")
    chapter_path = ROOT / "data" / "johannes" / "2.json"
    chapter = json.loads(chapter_path.read_text(encoding="utf-8"))
    review = {"book": "johannes", "chapter": 2, "verses": {}}
    for verse in chapter["verses"]:
        number = int(verse["number"])
        tokens = source[number]
        groups = SPECS[number]
        covered = [index for _, token_ids in groups for index in token_ids]
        if sorted(covered) != list(range(len(tokens))) or len(set(covered)) != len(tokens):
            raise ValueError(f"Johannes 2:{number}: onvolledige of dubbele handmatige review")
        verse["grondtekst"] = [
            {
                "woord": token["woord"],
                "strongs": token["display_strong"],
                "lemma_strongs": token["lemma_strong"],
                "morfologie": token["morphology"],
            }
            for token in tokens
        ]
        verse["woordnummers"] = [mapping(anchor, ids, tokens, number) for anchor, ids in groups]
        review["verses"][str(number)] = [
            {"tekst": anchor, "bronindices": ids, "reviewstatus": "handmatig_gecontroleerd"}
            for anchor, ids in groups
        ]
    if write:
        chapter_path.write_text(json.dumps(chapter, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        review_dir = ROOT / "data" / "woordnummers-review"
        review_dir.mkdir(exist_ok=True)
        (review_dir / "johannes-2.json").write_text(
            json.dumps(review, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        inline_path = ROOT / "data" / "woordnummers-inline" / "johannes.json"
        inline = json.loads(inline_path.read_text(encoding="utf-8"))
        inline["chapters"]["2"] = {
            str(verse["number"]): verse["woordnummers"] for verse in chapter["verses"]
        }
        inline_path.write_text(json.dumps(inline, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"verses": len(chapter["verses"]), "tokens": sum(len(value) for value in source.values())}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--utr", type=Path, required=True)
    parser.add_argument("--osis", type=Path, required=True)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    print(json.dumps(build(args.utr, args.osis, args.write), indent=2))


if __name__ == "__main__":
    main()
