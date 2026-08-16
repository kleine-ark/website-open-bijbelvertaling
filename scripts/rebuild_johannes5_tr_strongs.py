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
    11: [("Hij antwoordde hun", r(0, 1)), ("Die mij gezond gemaakt heeft", r(2, 5)),
         ("Die heeft mij gezegd", r(6, 8)), ("Neem uw bed op", r(9, 12)),
         ("en wandel", r(13, 14))],
    12: [("Zij vraagden hem dan", r(0, 2)), ("Wie is de Mens", r(3, 6)),
         ("Die u gezegd heeft", r(7, 9)), ("Neem uw bed op", r(10, 13)),
         ("en wandel", r(14, 15))],
    13: [("En die gezond gemaakt was", r(0, 2)), ("wist niet, Wie Hij was", r(3, 6)),
         ("want Jezus was ontweken", r(7, 10)),
         ("zo er een grote menigte in die plaats was", r(11, 15))],
    14: [("Daarna", r(0, 1)), ("vond hem Jezus", r(2, 5)), ("in de tempel", r(6, 8)),
         ("en zei tot hem", r(9, 11)), ("Zie", r(12)),
         ("u bent gezond geworden", r(13, 14)), ("zondig niet meer", r(15, 16)),
         ("opdat u niet wat ergers gebeurt", r(17, 22))],
    15: [("De mens ging heen", r(0, 2)), ("en boodschapte de Joden", r(3, 6)),
         ("dat het Jezus was", r(7, 9)), ("Die hem gezond gemaakt had", r(10, 13))],
    16: [("En daarom", r(0, 2)), ("vervolgden de Joden Jezus", r(3, 7)),
         ("en zochten Hem te doden", r(8, 11)),
         ("omdat Hij deze dingen op de sabbat deed", r(12, 16))],
    17: [("En Jezus antwoordde hun", r(0, 4)), ("Mijn Vader", r(5, 7)),
         ("werkt tot nu toe", r(8, 10)), ("en Ik werk ook", r(11, 12))],
    18: [("Daarom zochten dan de Joden te meer", [0, 1, 2, 3, 4, 6, 7]), ("Hem te doden", [5, 8]),
         ("omdat Hij niet alleen de sabbat brak", r(9, 14)), ("maar ook zei", r(15, 16)),
         ("dat God Zijn eigen Vader was", r(17, 21)),
         ("Zichzelf voor God gelijkenis makende", r(22, 26))],
    19: [("Jezus dan antwoordde en zei tot hen", r(0, 6)),
         ("Voorwaar, voorwaar zeg Ik u", r(7, 10)), ("De Zoon kan", r(11, 14)),
         ("niets van Zichzelf doen", r(15, 18)), ("tenzij", r(19, 21)),
         ("Hij de Vader dat ziet doen", r(22, 25)), ("want zo wat Die doet", r(26, 31)),
         ("het doet ook de Zoon evenzo", r(32, 36))],
    20: [("Want de Vader", r(0, 2)), ("heeft de Zoon lief", r(3, 5)),
         ("en toont Hem alles", r(6, 9)), ("wat Hij doet", r(10, 12)),
         ("en Hij zal Hem groter werken tonen dan deze", r(13, 18)),
         ("opdat u zich verwondert", r(19, 21))],
    21: [("Want zoals de Vader", r(0, 3)), ("de doden opwekt", r(4, 6)),
         ("en levend maakt", r(7, 8)), ("zo maakt ook de Zoon levend", [9, 10, 11, 12, 15]),
         ("Die Hij wil", r(13, 14))],
    22: [("Want ook de Vader", r(0, 3)), ("oordeelt niemand", r(4, 5)),
         ("maar heeft al het oordeel", r(6, 10)), ("de Zoon gegeven", r(11, 12))],
    23: [("Opdat zij allen de Zoon eren", r(0, 4)), ("zoals zij de Vader eren", r(5, 8)),
         ("Die de Zoon niet eer", r(9, 13)), ("eer de Vader niet", r(14, 17)),
         ("Die Hem gezonden heeft", r(18, 20))],
    24: [("Voorwaar, voorwaar zeg Ik u", r(0, 4)), ("Die Mijn woord hoort", r(5, 9)),
         ("en gelooft Hem, Die Mij gezonden heeft", r(10, 14)),
         ("die heeft het eeuwige leven", r(15, 17)), ("en komt niet in de verdoemenis", r(18, 22)),
         ("maar is uit de dood overgegaan in het leven", r(23, 30))],
    25: [("Voorwaar, voorwaar zeg Ik u", r(0, 4)), ("Het uur komt", r(5, 6)),
         ("en is nu", r(7, 9)), ("wanneer de doden", r(10, 12)),
         ("zullen horen de stem van de Zoon van God", r(13, 19)),
         ("en die ze gehoord hebben, zullen leven", r(20, 23))],
    26: [("Want zoals de Vader", r(0, 3)), ("het leven heeft in Zichzelf", r(4, 7)),
         ("zo heeft Hij ook de Zoon gegeven", r(8, 12)),
         ("het leven te hebben in Zichzelf", r(13, 16))],
    27: [("En heeft Hem macht gegeven", r(0, 3)), ("ook gericht te houden", r(4, 6)),
         ("omdat Hij van de Mensen Zoon is", r(7, 10))],
    28: [("Verwonder u daar niet over", r(0, 2)), ("want het uur komt", r(3, 5)),
         ("in die allen, die in de graven zijn", r(6, 12)),
         ("Zijn stem zullen horen", r(13, 16))],
    29: [("En zullen uitgaan", r(0, 1)), ("die het goede gedaan hebben", r(2, 5)),
         ("tot de opstanding van het leven", r(6, 8)),
         ("en die het kwade gedaan hebben", r(9, 13)),
         ("tot de opstanding van de verdoemenis", r(14, 16))],
    30: [("Ik kan", r(0, 2)), ("van Mijzelf niets doen", r(3, 6)),
         ("Zoals Ik hoor, oordeel Ik", r(7, 9)), ("en Mijn oordeel is rechtvaardig", r(10, 16)),
         ("want Ik zoek niet Mijn wil", r(17, 23)), ("maar de wil van de Vader", [24, 25, 26, 27, 30]),
         ("Die Mij gezonden heeft", r(28, 29))],
    31: [("Als Ik van Mijzelf getuig", r(0, 4)), ("Mijn getuigenis", r(5, 7)),
         ("is niet waarachtig", r(8, 10))],
    32: [("Er is een ander", r(0, 1)), ("die van Mij getuigt", r(2, 5)),
         ("en Ik weet", r(6, 7)), ("dat de getuigenis", [8, 11, 12]),
         ("die hij van Mij getuigt", r(13, 16)), ("waarachtig is", r(9, 10))],
    33: [("U hebt tot Johannes gezonden", r(0, 3)),
         ("en hij heeft van de waarheid getuigenis gegeven", r(4, 7))],
    34: [("Maar Ik neem geen getuigenis van een mens", r(0, 7)),
         ("maar dit zeg Ik", r(8, 10)), ("opdat u zou behouden worden", r(11, 13))],
    35: [("Hij was een brandende en lichtende kaars", r(0, 7)),
         ("en u hebt u voor een korte tijd", r(8, 10)),
         ("in zijn licht willen verheugen", r(11, 17))],
    36: [("Maar Ik heb een getuigenis meerder", r(0, 5)), ("dan die van Johannes", r(6, 7)),
         ("want de werken", r(8, 10)), ("die Mij de Vader gegeven heeft", r(11, 15)),
         ("om die te volbrengen", r(16, 18)), ("dezelfde werken", r(19, 21)),
         ("die Ik doe", r(22, 24)), ("getuigen van Mij", r(25, 27)),
         ("dat Mij de Vader gezonden heeft", r(28, 32))],
    37: [("En de Vader, Die Mij gezonden heeft", r(0, 4)),
         ("Die heeft Zelf van Mij getuigd", r(5, 8)),
         ("U hebt noch Zijn stem ooit gehoord", r(9, 13)),
         ("noch Zijn gedaante gezien", r(14, 17))],
    38: [("En Zijn woord hebt u niet in u blijvende", r(0, 8)),
         ("want u gelooft Die niet", [9, 13, 14, 15, 16]),
         ("Die Hij gezonden heeft", r(10, 12))],
    39: [("Onderzoek de Schriften", r(0, 2)), ("want u denkt", r(3, 5)),
         ("in deze het eeuwige leven te hebben", r(6, 10)),
         ("en die zijn het", r(11, 14)), ("die van Mij getuigen", r(15, 17))],
    40: [("En u wilt", r(0, 2)), ("tot Mij niet komen", r(3, 5)),
         ("opdat u het leven mag hebben", r(6, 8))],
    41: [("Ik neem geen eer van mensen", r(0, 4))],
    42: [("Maar Ik ken u", r(0, 2)), ("dat u de liefde van God", r(3, 7)),
         ("in uzelf niet hebt", r(8, 11))],
    43: [("Ik ben gekomen", r(0, 1)), ("in de Naam van Mijn Vader", r(2, 7)),
         ("en u neemt Mij niet aan", r(8, 11)), ("zo een ander komt", r(12, 14)),
         ("in zijn eigen naam", r(15, 19)), ("die zult u aannemen", r(20, 21))],
    44: [("Hoe kunt u geloven", r(0, 3)), ("u, die eer van elkaar neemt", r(4, 7)),
         ("en de eer", r(8, 10)), ("die van God alleen is", r(11, 15)),
         ("niet zoekt", r(16, 17))],
    45: [("Denk niet", r(0, 1)), ("dat Ik u aanklagen zal", r(2, 5)),
         ("bij de Vader", r(6, 8)), ("die u aanklaagt, is Mozes", r(9, 13)),
         ("op wie u gehoopt hebt", r(14, 17))],
    46: [("Want als u Mozes geloofde", r(0, 3)), ("zo zou u Mij geloven", r(4, 6)),
         ("want hij heeft van Mij geschreven", r(7, 11))],
    47: [("Maar zo u zijn Schriften niet gelooft", r(0, 6)),
         ("hoe zult u Mijn woorden geloven", r(7, 11))],
}


def build(utr_path: Path, osis_path: Path, write=False):
    source = load_tr_chapter(utr_path, osis_path, chapter=5, osis_book="John")
    chapter_path = ROOT / "data" / "johannes" / "5.json"
    chapter = json.loads(chapter_path.read_text(encoding="utf-8"))
    review = {"book": "johannes", "chapter": 5, "reviewed_through": 47, "verses": {}}
    for verse in chapter["verses"]:
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
            str(v["number"]): v["woordnummers"] for v in chapter["verses"]
        }
        inline_path.write_text(json.dumps(inline, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"verses": 47, "tokens": sum(len(source[n]) for n in range(1, 48))}


def main():
    parser = argparse.ArgumentParser(); parser.add_argument("--utr", type=Path, required=True)
    parser.add_argument("--osis", type=Path, required=True); parser.add_argument("--write", action="store_true")
    args = parser.parse_args(); print(json.dumps(build(args.utr, args.osis, args.write), indent=2))


if __name__ == "__main__":
    main()
