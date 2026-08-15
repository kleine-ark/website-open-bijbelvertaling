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
    11: [("De vrouw zei tot Hem", r(0, 3)), ("Heere", r(4)),
         ("U hebt niet om mee te putten", r(5, 7)), ("en de put is diep", r(8, 12)),
         ("vanwaar hebt U dan", r(13, 15)), ("het levend water", r(16, 19))],
    12: [("Bent U meerder", r(0, 3)), ("dan onze vader Jakob", r(4, 7)),
         ("die ons de put gegeven heeft", r(8, 12)), ("en hijzelf heeft daaruit gedronken", r(13, 17)),
         ("en zijn kinderen", r(18, 21)), ("en zijn vee", r(22, 25))],
    13: [("Jezus antwoordde, en zei tot haar", r(0, 5)), ("Een ieder, die", r(6, 7)),
         ("drinkt", r(8)), ("van dit water", r(9, 12)), ("zal opnieuw dorsten", r(13, 14))],
    14: [("Maar zo wie gedronken zal hebben", r(0, 3)), ("van het water", r(4, 6)),
         ("dat Ik hem geven zal", r(7, 10)), ("niet dorsten", r(11, 13)),
         ("in eeuwigheid", r(14, 16)), ("maar het water", r(17, 19)),
         ("dat Ik hem zal geven", r(20, 22)), ("zal in hem worden", r(23, 25)),
         ("een fontein van water", r(26, 27)), ("springende", r(28)),
         ("tot in het eeuwige leven", r(29, 31))],
    15: [("De vrouw zei tot Hem", r(0, 4)), ("Heere", r(5)),
         ("geef mij dat water", r(6, 10)), ("opdat mij niet dorste", r(11, 13)),
         ("en ik hier niet moet komen", r(14, 16)), ("om te putten", r(17))],
    16: [("Jezus zei tot haar", r(0, 3)), ("Ga heen", r(4)),
         ("roep uw man", r(5, 8)), ("en kom hier", r(9, 11))],
    17: [("De vrouw antwoordde en zei", r(0, 4)), ("Ik heb geen man", r(5, 7)),
         ("Jezus zei tot haar", r(8, 11)), ("U hebt wel gezegd", r(12, 13)),
         ("gezegd: Ik heb geen man", r(14, 17))],
    18: [("Want u hebt vijf mannen gehad", r(0, 3)), ("en die u nu hebt", r(4, 7)),
         ("is uw man niet", r(8, 11)), ("dat hebt u met waarheid gezegd", r(12, 14))],
    19: [("De vrouw zei tot Hem", r(0, 3)), ("Heere", r(4)),
         ("ik zie", r(5)), ("dat U een profeet bent", r(6, 9))],
    20: [("Onze vaders", r(0, 2)), ("hebben op deze berg aangebeden", r(3, 7)),
         ("en u zegt", r(8, 10)), ("dat te Jeruzalem", r(11, 13)),
         ("de plaats is", r(14, 16)), ("waar men moet aanbidden", r(17, 19))],
    21: [("Jezus zei tot haar", r(0, 3)), ("Vrouw", r(4)), ("geloof Mij", r(5, 7)),
         ("het uur komt", r(8, 9)), ("wanneer", r(10)), ("noch op deze berg", r(11, 15)),
         ("noch te Jeruzalem", r(16, 18)), ("de Vader zult aanbidden", r(19, 21))],
    22: [("U aanbidt", r(0, 1)), ("wat u niet weet", r(2, 4)),
         ("wij aanbidden", r(5, 6)), ("wat wij weten", r(7, 8)),
         ("want de zaligheid", r(9, 11)), ("is uit de Joden", r(12, 15))],
    23: [("Maar het uur komt", r(0, 2)), ("en is nu", r(3, 5)), ("wanneer", r(6)),
         ("de ware aanbidders", r(7, 9)), ("de Vader aanbidden zullen", r(10, 12)),
         ("in geest en waarheid", r(13, 16)), ("want de Vader", r(17, 20)),
         ("zoekt ook zulke", r(21, 22)), ("die Hem zo aanbidden", r(23, 25))],
    24: [("God is één Geest", r(0, 2)), ("en die Hem aanbidden", r(3, 6)),
         ("in geest en waarheid", r(7, 10)), ("moeten Hem aanbidden", r(11, 12))],
    25: [("De vrouw zei tot Hem", r(0, 3)), ("Ik weet", r(4)),
         ("dat de Messias komt", r(5, 7)), ("Die genoemd wordt Christus", r(8, 10)),
         ("wanneer Die zal gekomen zijn", r(11, 13)),
         ("zo zal Hij ons alle dingen verkondigen", r(14, 16))],
    26: [("Jezus zei tot haar", r(0, 3)), ("Ik ben het", r(4, 6)),
         ("Die met u spreek", r(7, 8))],
    27: [("En daarop kwamen Zijn discipelen", r(0, 6)), ("en verwonderden zich", r(7, 8)),
         ("dat Hij met een vrouw sprak", r(9, 12)), ("Toch zei niemand", r(13, 15)),
         ("Wat vraagt U", r(16, 17)), ("of", r(18)), ("Wat spreekt U met haar", r(19, 22))],
    28: [("Zo verliet de vrouw dan haar watervat", r(0, 6)),
         ("en ging heen in de stad", r(7, 11)), ("en zei tot de mensen", r(12, 15))],
    29: [("Kom, ziet een Mens", r(0, 2)), ("Die mij gezegd heeft", r(3, 5)),
         ("alles, wat ik gedaan heb", r(6, 8)), ("is Deze niet de Christus", r(9, 13))],
    30: [("Zij dan gingen uit de stad", r(0, 4)), ("en kwamen tot Hem", r(5, 8))],
    31: [("En ondertussen", r(0, 3)), ("baden Hem de discipelen", r(4, 7)),
         ("zeggende", r(8)), ("Rabbi, eet", r(9, 10))],
    32: [("Maar Hij zei tot hen", r(0, 3)), ("Ik heb een voedsel", r(4, 6)),
         ("om te eten", r(7)), ("die u niet weet", r(8, 11))],
    33: [("Zo zeiden dan de discipelen", r(0, 3)), ("tegen elkaar", r(4, 5)),
         ("Heeft Hem iemand", r(6, 9)), ("te eten gebracht", r(10))],
    34: [("Jezus zei tot hen", r(0, 3)), ("Mijn voedsel is", r(4, 6)),
         ("dat Ik doe de wil", r(7, 10)), ("Van Degene, Die Mij gezonden heeft", r(11, 13)),
         ("en Zijn werk volbrenge", r(14, 18))],
    35: [("Zegt u niet", r(0, 3)), ("Het zijn nog vier maanden", r(4, 6)),
         ("en dan komt de oogst", r(7, 10)), ("Zie, Ik zeg u", r(11, 13)),
         ("Hef uw ogen op", r(14, 17)), ("en aanschouwt de landen", r(18, 21)),
         ("want zij zijn al wit om te oogsten", r(22, 27))],
    36: [("En die maait", r(0, 2)), ("ontvangt loon", r(3, 4)),
         ("en verzamelt vrucht", r(5, 7)), ("ten eeuwigen leven", r(8, 10)),
         ("opdat", r(11)), ("zowel, die zaait", r(12, 14)),
         ("zich samen verblijde", r(15, 16)), ("als die maait", r(17, 19))],
    37: [("Want hierin", r(0, 2)), ("is die spreuk waarachtig", r(3, 7)),
         ("Een ander is het, die zaait", r(8, 12)), ("en een ander, die maait", r(13, 16))],
    38: [("Ik heb u uitgezonden", r(0, 2)), ("om te maaien", r(3)),
         ("wat u niet bearbeid hebt", r(4, 7)), ("anderen hebben het bearbeid", r(8, 9)),
         ("en u bent tot hun arbeid ingegaan", r(10, 16))],
    39: [("En velen van de Samaritanen uit die stad", r(0, 5)),
         ("geloofden in Hem", r(6, 10)), ("om het woord van de vrouw", r(11, 15)),
         ("die getuigde", r(16, 17)), ("Hij heeft mij gezegd", r(18, 19)),
         ("alles, wat ik gedaan heb", r(20, 22))],
    40: [("Als dan de Samaritanen tot Hem gekomen waren", r(0, 6)),
         ("baden zij Hem", r(7, 8)), ("dat Hij bij hen bleef", r(9, 11)),
         ("en Hij bleef daar twee dagen", r(12, 16))],
    41: [("En er geloofden er veel meer", r(0, 3)), ("omwille van Zijn woord", r(4, 7))],
    42: [("En zeiden tot de vrouw", r(0, 3)), ("Wij geloven niet meer", [4, 5, 10]),
         ("vanwege wat u zei", r(6, 9)), ("want wij zelf hebben Hem gehoord", r(11, 13)),
         ("en weten", r(14, 15)), ("dat Deze werkelijk is", r(16, 19)),
         ("de Zaligmaker van de wereld", r(20, 23)), ("de Christus", r(24, 25))],
    43: [("En na de twee dagen", r(0, 4)), ("ging Hij van daar", r(5, 6)),
         ("en ging heen naar Galilea", r(7, 11))],
    44: [("Want Jezus heeft Zelf getuigd", r(0, 4)), ("dat een profeet", r(5, 6)),
         ("in zijn eigen vaderland", r(7, 10)), ("geen eer heeft", r(11, 13))],
    45: [("Als Hij dan in Galilea kwam", r(0, 5)), ("ontvingen Hem de Galileërs", r(6, 9)),
         ("gezien hebbende al de dingen", r(10, 12)),
         ("die Hij te Jeruzalem op het feest gedaan had", r(13, 18)),
         ("want ook zij waren tot het feest gegaan", r(19, 25))],
    46: [("Zo kwam dan Jezus opnieuw", r(0, 4)), ("te Kana in Galilea", r(5, 9)),
         ("waar Hij het water wijn gemaakt had", r(10, 14)),
         ("En er was een zeker koninklijk hoveling", r(15, 18)),
         ("wiens zoon ziek was", r(19, 22)), ("te Kapernaüm", r(23, 24))],
    47: [("Deze, gehoord hebbende", r(0, 2)), ("dat Jezus uit Judea in Galilea kwam", r(3, 10)),
         ("ging tot Hem", r(11, 13)), ("en bad Hem", r(14, 16)),
         ("dat Hij afkwame", r(17, 18)), ("en zijn zoon gezond maakte", r(19, 23)),
         ("want hij lag op zijn sterven", r(24, 26))],
    48: [("Jezus dan zei tot hem", r(0, 5)),
         ("Tenzij dat u tekenen en wonderen ziet", r(6, 11)),
         ("zo zult u niet geloven", r(12, 14))],
    49: [("De koninklijke hoveling zei tot Hem", r(0, 4)), ("Heere", r(5)),
         ("kom af", r(6)), ("eer mijn kind sterft", r(7, 11))],
    50: [("Jezus zei tot hem", r(0, 3)), ("Ga heen", r(4)),
         ("uw zoon leeft", r(5, 8)), ("En de mens geloofde het woord", r(9, 14)),
         ("dat Jezus tot hem zei", r(15, 18)), ("en ging heen", r(19, 20))],
    51: [("En als hij nu afging", r(0, 3)), ("kwamen hem zijn dienaren tegemoet", r(4, 8)),
         ("en boodschapten, zeggende", r(9, 12)), ("Uw kind leeft", r(13, 16))],
    52: [("Zo vraagde hij dan van hen", r(0, 3)), ("het uur", r(4, 5)),
         ("in welke het beter met hem geworden was", r(6, 9)),
         ("En zij zeiden tot hem", r(10, 13)), ("Gisteren om zeven uur", r(14, 16)),
         ("verliet hem de koorts", r(17, 20))],
    53: [("De vader bekende dan", r(0, 3)), ("dat het in dit uur was", r(4, 8)),
         ("in die Jezus tot hem gezegd had", r(9, 15)), ("Uw zoon leeft", r(16, 19)),
         ("En hij geloofde zelf", r(20, 22)), ("en zijn hele huis", r(23, 27))],
    54: [("Dit tweede teken", r(0, 3)), ("heeft Jezus opnieuw gedaan", r(4, 6)),
         ("als Hij uit Judea in Galilea gekomen was", r(7, 13))],
}


def build(utr_path: Path, osis_path: Path, write=False):
    source = load_tr_chapter(utr_path, osis_path, chapter=4, osis_book="John")
    chapter_path = ROOT / "data" / "johannes" / "4.json"
    chapter = json.loads(chapter_path.read_text(encoding="utf-8"))
    review = {"book": "johannes", "chapter": 4, "reviewed_through": 54, "verses": {}}
    for verse in chapter["verses"]:
        number = int(verse["number"]); tokens = source[number]; groups = SPECS[number]
        covered = [index for _, token_ids in groups for index in token_ids]
        if sorted(covered) != list(range(len(tokens))) or len(set(covered)) != len(tokens):
            raise ValueError(f"Johannes 4:{number}: onvolledige of dubbele handmatige review")
        verse["grondtekst"] = [{
            "woord": token["woord"], "strongs": token["display_strong"],
            "lemma_strongs": token["lemma_strong"], "morfologie": token["morphology"],
            **({"tvm": token["tvm"]} if token.get("tvm") else {}),
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
            str(v["number"]): v["woordnummers"] for v in chapter["verses"]
        }
        inline_path.write_text(json.dumps(inline, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"verses": 54, "tokens": sum(len(source[n]) for n in range(1, 55))}


def main():
    parser = argparse.ArgumentParser(); parser.add_argument("--utr", type=Path, required=True)
    parser.add_argument("--osis", type=Path, required=True); parser.add_argument("--write", action="store_true")
    args = parser.parse_args(); print(json.dumps(build(args.utr, args.osis, args.write), indent=2))


if __name__ == "__main__":
    main()
