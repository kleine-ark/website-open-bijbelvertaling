#!/usr/bin/env python3
"""Publiceer gecontroleerde TR-koppelingen voor Johannes 12 in versbatches."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from rebuild_nt_tr_strongs import load_tr_chapter
from rebuild_johannes2_tr_strongs import mapping, r

ROOT = Path(__file__).resolve().parents[1]

SPECS = {
    1: [("Jezus dan kwam", [0, 1, 2, 8]),
        ("zes dagen voor het pascha", r(3, 7)), ("te Bethanië", r(9, 10)),
        ("daar Lazarus was", r(11, 13)), ("die gestorven was geweest", r(14, 15)),
        ("wie Hij opgewekt had uit de doden", r(16, 19))],
    2: [("Zij bereidden Hem dan daar een avondmaal", r(0, 4)),
        ("en Martha diende", r(5, 8)), ("en Lazarus", r(9, 11)),
        ("was één van degenen, die met Hem aanzaten", r(12, 16))],
    3: [("Maria dan", r(0, 2)), ("genomen hebbende", r(3)),
        ("een pond zalf van onvervalste, zeer kostelijke nardus", r(4, 8)),
        ("heeft de voeten van Jezus gezalfd", r(9, 13)),
        ("en met haar haar Zijn voeten afgedroogd", r(14, 21)),
        ("en het huis werd vervuld", r(22, 25)),
        ("van de reuk van de zalf", r(26, 30))],
    4: [("Zo zei dan", r(0, 1)), ("één van Zijn discipelen", r(2, 6)),
        ("namelijk Judas, Simons zoon, Iskariot", r(7, 9)),
        ("die Hem verraden zou", r(10, 13))],
    5: [("Waarom", r(0, 1)), ("is deze zalf niet verkocht", r(2, 6)),
        ("voor driehonderd penningen", r(7, 8)), ("en de armen gegeven", r(9, 11))],
    6: [("En dit zei hij", r(0, 2)),
        ("niet omdat hij bezorgd was voor de armen", r(3, 9)),
        ("maar omdat hij een dief was", r(10, 13)), ("en de beurs had", r(14, 17)),
        ("en droeg wat gegeven werd", r(18, 21))],
    7: [("Jezus dan zei", r(0, 3)), ("Laat af van haar", r(4, 5)),
        ("zij heeft dit bewaard", r(12, 13)),
        ("tegen de dag van Mijn begrafenis", r(6, 11))],
    8: [("Want de armen hebt u altijd met u", r(0, 6)),
        ("maar Mij hebt u niet altijd", r(7, 11))],
    9: [("Een grote menigte dan van de Joden verstond", r(0, 6)),
        ("dat Hij daar was", r(7, 9)), ("en zij kwamen", r(10, 11)),
        ("niet alleen om Jezus' wil", r(12, 16)),
        ("maar opdat zij ook Lazarus zouden zien", r(17, 22)),
        ("die Hij uit de doden opgewekt had", r(23, 26))],
    10: [("En de overpriesters beraadslaagden", r(0, 3)),
         ("dat zij ook Lazarus doden zouden", r(4, 8))],
    11: [("Want velen van de Joden", [0, 1, 5, 6]),
         ("gingen heen om zijnentwil", r(2, 4)),
         ("en geloofden in Jezus", r(7, 11))],
    12: [("Op de andere dag", r(0, 1)), ("een grote menigte", r(2, 3)),
         ("die tot het feest gekomen was", r(4, 8)), ("horende", r(9)),
         ("dat Jezus naar Jeruzalem kwam", r(10, 15))],
    13: [("Namen de takken van palmbomen", r(0, 4)),
         ("en gingen uit Hem tegemoet", r(5, 9)), ("en riepen", r(10, 11)),
         ("Hosanna", r(12)), ("Gezegend is Hij, Die komt", r(13, 15)),
         ("in de Naam van de Heere", r(16, 18)),
         ("Hij, Die is de Koning van Israël", r(19, 22))],
    14: [("En Jezus vond", [1, 2, 3, 0]), ("een jonge ezel", r(4)),
         ("en zat daarop", r(5, 7)), ("zoals geschreven is", r(8, 10))],
    15: [("Vrees niet", r(0, 1)), ("u dochter van Sion", r(2, 3)),
         ("zie", r(4)), ("uw Koning komt", r(5, 8)),
         ("zittende op het veulen van een ezelin", r(9, 12))],
    16: [("Maar dit verstonden Zijn discipelen", [0, 1, 3, 4, 5, 6]),
         ("in het eerst niet", [7, 8, 2]),
         ("maar als Jezus verheerlijkt was", r(9, 13)),
         ("toen werden zij indachtig", r(14, 15)),
         ("dat dit van Hem geschreven was", r(16, 21)),
         ("en dat zij Hem dit gedaan hadden", r(22, 25))],
    17: [("De menigte dan", r(1, 3)), ("die met Hem was", r(4, 7)),
         ("getuigde dat", [0, 8]), ("Hij Lazarus uit het graf geroepen", r(9, 14)),
         ("en hem uit de doden opgewekt had", r(15, 19))],
    18: [("Daarom", r(0, 1)), ("ging ook de menigte Hem tegemoet", r(2, 6)),
         ("omdat zij gehoord had", r(7, 8)),
         ("dat Hij dat teken gedaan had", r(9, 13))],
    19: [("De Farizeeën dan zeiden onder elkaar", r(0, 5)),
         ("Ziet u wel", r(6)), ("dat u geheel niet vordert", r(7, 10)),
         ("Ziet", r(11)), ("de hele wereld gaat Hem na", r(12, 16))],
    20: [("En er waren sommige Grieken", r(0, 3)),
         ("uit degenen, die opgekomen waren", r(4, 6)),
         ("opdat zij op het feest zouden aanbidden", r(7, 11))],
    21: [("Deze dan gingen tot Filippus", r(0, 3)),
         ("die van Bethsaïda in Galilea was", r(4, 8)),
         ("en baden hem", r(9, 11)), ("zeggende", r(12)), ("Heere", r(13)),
         ("wij wilden Jezus wel zien", r(14, 17))],
    22: [("Filippus kwam", r(0, 1)), ("en zei het Andreas", r(2, 5)),
         ("en Andreas en Filippus opnieuw", r(6, 10)),
         ("zeiden het Jezus", r(11, 13))],
    23: [("Maar Jezus", r(0, 2)), ("antwoordde hun", r(3, 4)),
         ("zeggende", r(5)), ("Het uur is gekomen", r(6, 8)),
         ("dat de Zoon des mensen zal verheerlijkt worden", r(9, 14))],
    24: [("Voorwaar, voorwaar zeg Ik u", r(0, 3)),
         ("Als het tarwegraan", [4, 6, 7, 8, 9]), ("in de aarde niet valt", [11, 12, 13, 5, 10]),
         ("en sterft", r(14)), ("zo blijft het alleen", r(15, 17)),
         ("maar als het sterft", r(18, 20)), ("zo brengt het veel vrucht voort", r(21, 23))],
    25: [("Die zijn leven liefheeft", r(0, 4)), ("zal het verliezen", r(5, 6)),
         ("en die zijn leven haat", r(7, 12)), ("in deze wereld", r(13, 16)),
         ("zal het bewaren", [20, 21]), ("tot het eeuwige leven", r(17, 19))],
    26: [("Zo iemand Mij dient", r(0, 3)), ("die volge Mij", r(4, 5)),
         ("en waar Ik ben", r(6, 9)), ("daar zal ook Mijn dienaar zijn", r(10, 16)),
         ("En zo iemand Mij dient", r(17, 21)), ("de Vader zal hem eren", r(22, 25))],
    27: [("Nu is Mijn ziel ontroerd", r(0, 4)), ("en wat zal Ik zeggen", r(5, 7)),
         ("Vader", r(8)), ("verlos Mij uit dit uur", r(9, 14)),
         ("Maar hierom", r(15, 17)), ("ben Ik in dit uur gekomen", r(18, 22))],
    28: [("Vader", r(0)), ("verheerlijk Uw Naam", r(1, 4)),
         ("Er kwam dan een stem uit de hemel", r(5, 10)),
         ("En Ik heb Hem verheerlijkt", r(11, 12)),
         ("en Ik zal Hem opnieuw verheerlijken", r(13, 15))],
    29: [("De menigte dan", r(0, 2)), ("die daar stond", r(3, 4)),
         ("en dit hoorde", r(5, 6)), ("zei", r(7)),
         ("dat er een donderslag gebeurd was", r(8, 9)),
         ("Anderen zeiden", r(10, 11)), ("Een engel heeft tot Hem gesproken", r(12, 14))],
    30: [("Jezus antwoordde en zei", r(0, 4)),
         ("Niet om Mijnentwil", r(5, 7)), ("is deze stem gebeurd", r(8, 11)),
         ("maar om uwentwil", r(12, 14))],
    31: [("Nu is het oordeel van deze wereld", r(0, 5)),
         ("nu zal de overste van deze wereld buiten geworpen worden", r(6, 13))],
    32: [("En Ik", r(0)), ("zo wanneer", r(1)),
         ("Ik van de aarde zal verhoogd zijn", r(2, 5)),
         ("zal hen allen tot Mij trekken", r(6, 9))],
    33: [("En dit zei Hij", r(0, 2)), ("betekenende", r(3)),
         ("wat voor dood Hij sterven zou", r(4, 7))],
    34: [("De menigte antwoordde Hem", r(0, 3)),
         ("Wij hebben uit de wet gehoord", r(4, 8)),
         ("dat de Christus blijft in de eeuwigheid", r(9, 15)),
         ("en hoe zegt U", r(16, 19)),
         ("dat de Zoon des mensen moet verhoogd worden", r(20, 26)),
         ("Wie is deze Zoon des mensen", r(27, 33))],
    35: [("Jezus dan zei tot hen", r(0, 4)),
         ("Nog een kleine tijd is het Licht bij u", r(5, 12)),
         ("wandel, terwijl u het Licht hebt", r(13, 17)),
         ("opdat de duisternis u niet bevange", r(18, 22)),
         ("En die in de duisternis wandelt", r(23, 28)),
         ("weet niet, waar hij heengaat", r(29, 32))],
    36: [("Terwijl u het Licht hebt", r(0, 3)),
         ("gelooft in het Licht", r(4, 7)),
         ("opdat u kinderen van het Licht mag zijn", r(8, 11)),
         ("Deze dingen sprak Jezus", r(12, 15)),
         ("en weggaande verborg Hij Zich van hen", r(16, 20))],
    37: [("En hoewel Hij zovele tekenen voor hen gedaan had", r(0, 6)),
         ("toch geloofden zij in Hem niet", r(7, 10))],
    38: [("Opdat het woord van Jesaja, de profeet, vervuld werd", r(0, 6)),
         ("dat hij gesproken heeft", r(7, 8)), ("Heere", r(9)),
         ("wie heeft onze prediking geloofd", r(10, 14)),
         ("en wie is de arm van de Heere geopenbaard", r(15, 20))],
    39: [("Daarom konden zij niet geloven", r(0, 4)),
         ("omdat Jesaja opnieuw gezegd heeft", r(5, 8))],
    40: [("Hij heeft hun ogen verblind", r(0, 3)),
         ("en hun hart verhard", r(4, 8)),
         ("opdat zij met de ogen niet zien", r(9, 13)),
         ("en met het hart niet verstaan", r(14, 17)),
         ("en zij bekeerd worden", r(18, 19)),
         ("en Ik hen geneze", r(20, 22))],
    41: [("Dit zei Jesaja", r(0, 2)),
         ("toen hij Zijn heerlijkheid zag", r(3, 7)),
         ("en van Hem sprak", r(8, 11))],
    42: [("Toch geloofden ook zelfs velen uit de oversten in Hem", r(0, 9)),
         ("maar vanwege de Farizeeën", r(10, 13)),
         ("beleden zij het niet", r(14, 15)),
         ("opdat zij uit de synagoge niet zouden geworpen worden", r(16, 19))],
    43: [("Want zij hadden de eer van de mensen lief", r(0, 5)),
         ("meer dan de eer van God", r(6, 11))],
    44: [("En Jezus riep, en zei", r(0, 4)),
         ("Die in Mij gelooft", r(5, 8)), ("gelooft in Mij niet", r(9, 12)),
         ("maar in Degene, Die Mij gezonden heeft", r(13, 17))],
    45: [("En die Mij ziet", r(0, 3)),
         ("die ziet Degene, Die Mij gezonden heeft", r(4, 7))],
    46: [("Ik ben een Licht", r(0, 1)), ("in de wereld gekomen", r(2, 5)),
         ("opdat een ieder, die in Mij gelooft", r(6, 11)),
         ("in de duisternis niet blijve", r(12, 16))],
    47: [("En als iemand Mijn woorden gehoord", r(0, 6)),
         ("en niet geloofd zal hebben", r(7, 9)),
         ("Ik oordeel hem niet", r(10, 13)),
         ("want Ik ben niet gekomen", r(14, 16)),
         ("opdat Ik de wereld oordele", r(17, 20)),
         ("maar opdat Ik de wereld zalig make", r(21, 25))],
    48: [("Die Mij verwerpt", r(0, 2)),
         ("en Mijn woorden niet ontvangt", r(3, 8)),
         ("heeft, die hem oordeelt", r(9, 12)),
         ("het woord, dat Ik gesproken heb", r(13, 16)),
         ("dat zal hem oordelen", r(17, 19)),
         ("ten laatsten dage", r(20, 23))],
    49: [("Want Ik heb uit Mijzelf niet gesproken", r(0, 5)),
         ("maar de Vader, Die Mij gezonden heeft", r(6, 10)),
         ("Die heeft Mij een gebod gegeven", r(11, 14)),
         ("wat Ik zeggen zal", r(15, 16)),
         ("en wat Ik spreken zal", r(17, 19))],
    50: [("En Ik weet", r(0, 1)), ("dat Zijn gebod het eeuwige leven is", r(2, 8)),
         ("Wat Ik dan spreek", r(9, 12)),
         ("dat spreek Ik zo, zoals Mij de Vader gezegd heeft", r(13, 19))],
}


def build(utr_path: Path, osis_path: Path, write: bool = False):
    source = load_tr_chapter(utr_path, osis_path, chapter=12, osis_book="John")
    chapter_path = ROOT / "data" / "johannes" / "12.json"
    chapter = json.loads(chapter_path.read_text(encoding="utf-8"))
    review_path = ROOT / "data" / "woordnummers-review" / "johannes-12.json"
    review = (json.loads(review_path.read_text(encoding="utf-8"))
              if review_path.exists() else {"book": "johannes", "chapter": 12, "verses": {}})
    review["reviewed_through"] = 50

    for verse in chapter["verses"][:50]:
        number = int(verse["number"])
        tokens = source[number]
        groups = SPECS[number]
        covered = [index for _, indices in groups for index in indices]
        if sorted(covered) != list(range(len(tokens))) or len(set(covered)) != len(tokens):
            raise ValueError(f"Johannes 12:{number}: onvolledige of dubbele handmatige review")
        verse["grondtekst"] = [{
            "woord": token["woord"],
            "strongs": token["display_strong"],
            "lemma_strongs": token["lemma_strong"],
            "morfologie": token["morphology"],
            **({"tvm": token["tvm"]} if token.get("tvm") else {}),
            **({"bronstatus": token["bronstatus"]} if token.get("bronstatus") else {}),
        } for token in tokens]
        verse["woordnummers"] = [mapping(anchor, indices, tokens, number)
                                  for anchor, indices in groups]
        occurrences = {}
        for item in verse["woordnummers"]:
            occurrences[item["tekst"]] = occurrences.get(item["tekst"], 0) + 1
            item["voorkomen"] = occurrences[item["tekst"]]
            item["herkomst"]["referentie"] = f"JHN 12:{number}"
        review["verses"][str(number)] = [{
            "tekst": anchor,
            "bronindices": indices,
            "reviewstatus": "handmatig_gecontroleerd",
        } for anchor, indices in groups]

    if write:
        chapter_path.write_text(json.dumps(chapter, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        review_path.write_text(json.dumps(review, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        inline_path = ROOT / "data" / "woordnummers-inline" / "johannes.json"
        inline = json.loads(inline_path.read_text(encoding="utf-8"))
        inline["chapters"]["12"] = {
            str(verse["number"]): verse["woordnummers"] for verse in chapter["verses"][:50]
        }
        inline_path.write_text(json.dumps(inline, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    return {"verses": 50, "tokens": sum(len(source[number]) for number in range(1, 51))}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--utr", type=Path, required=True)
    parser.add_argument("--osis", type=Path, required=True)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    print(json.dumps(build(args.utr, args.osis, args.write), indent=2))


if __name__ == "__main__":
    main()
