#!/usr/bin/env python3
"""Publiceer gecontroleerde TR-koppelingen voor Mattheüs 16 in versbatches."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from rebuild_nt_tr_strongs import load_tr_chapter
from rebuild_johannes2_tr_strongs import mapping, r

ROOT = Path(__file__).resolve().parents[1]

SPECS = {
    1: [("En de Farizeën en Sadduceën tot Hem gekomen zijnde, en Hem verzoekende, begeerden van Hem, dat Hij hun een teken uit de hemel zou tonen", r(0, 14))],
    2: [("Maar Hij antwoordde, en zei tot hen: Als het avond geworden is, zegt u: Schoon weer; want de hemel is rood", r(0, 12))],
    3: [("En van de morgen: Vandaag onweer; want de hemel is droevig rood. U huichelaars! het aangezicht van de hemel weet u wel te onderscheiden, en kunt u de tekenen van de tijden niet onderscheiden?", r(0, 23))],
    4: [("Het boos en overspelig geslacht verzoekt een teken; en hun zal geen teken gegeven worden, dan het teken van Jona, de profeet. En hen verlatende, ging Hij weg", r(0, 21))],
    5: [("En als Zijn discipelen op de andere zijde gekomen waren, hadden zij vergeten broden mee te nemen", r(0, 10))],
    6: [("En Jezus zei tot hen: Zie toe, en wees op uw hoede voor het zuurdesem van de Farizeën en Sadduceën", r(0, 14))],
    7: [("En zij overlegden bij zichzelf, zeggende: Het is omdat wij geen broden mee genomen hebben", r(0, 9))],
    8: [("En Jezus, dat wetende, zei tot hen: Wat overlegt u bij uzelf, u kleingelovigen! dat u geen broden mee genomen hebt?", r(0, 14))],
    9: [("Verstaat u nog niet? en gedenkt u niet aan de vijf broden van de vijf duizend mannen; en hoevele manden u opnam?", r(0, 12))],
    10: [("Noch aan de zeven broden van de vier duizend mannen, en hoevele manden u opnam?", r(0, 9))],
    11: [("Hoe verstaat u niet, dat Ik u van geen brood gesproken heb, als Ik zei, dat u zich wachten zou van het zuurdesem van de Farizeën en Sadduceën", r(0, 16))],
    12: [("Toen verstonden zij, dat Hij niet gezegd had, dat zij zich wachten zouden van het zuurdesem van het brood, maar van de leer van de Farizeën en Sadduceën?", r(0, 18))],
    13: [("Als nu Jezus gekomen was in de delen van Cesarea Filippi, vraagde Hij Zijn discipelen, zeggende: Wie zeggen de mensen, dat Ik, de Zoon des mensen, ben?", r(0, 24))],
    14: [("En zij zeiden: Sommigen: Johannes de Doper; en anderen: Elia; en anderen: Jeremia of één van de profeten", r(0, 17))],
    15: [("Hij zei tot hen: Maar u, wie zegt u, dat Ik ben?", r(0, 7))],
    16: [("En Simon Petrus, antwoordende, zei: U bent de Christus, de Zoon van de levende God", r(0, 14))],
    17: [("En Jezus, antwoordende, zei tot hem: Zalig bent u, Simon, Bar-jona! want vlees en bloed heeft u dat niet geopenbaard, maar Mijn Vader, Die in de hemelen is", r(0, 25))],
    18: [("En Ik zeg u ook, dat u bent Petrus, en op deze petra zal Ik Mijn gemeente bouwen, en de poorten van de hel zullen dezelfde niet overweldigen", r(0, 22))],
    19: [("En Ik zal u geven de sleutelen van het Koninkrijk van de hemelen; en zo wat u zult binden op de aarde, zal in de hemelen gebonden zijn; en zo wat u ontbinden zult op de aarde, zal in de hemelen ontbonden zijn", r(0, 32))],
    20: [("Toen verbood Hij Zijn discipelen, dat zij iemand zeggen zouden, dat Hij was Jezus, de Christus", r(0, 13))],
    21: [("Van toen aan begon Jezus Zijn discipelen te vertonen, dat Hij moest heengaan naar Jeruzalem, en veel lijden van de ouderlingen, en overpriesteren, en Schriftgeleerden, en gedood worden, en op de derde dag opgewekt worden", r(0, 31))],
    22: [("En Petrus, Hem tot zich genomen hebbende, begon Hem te bestraffen, zeggende: Heere, wees U genadig! dit zal U in geen geval gebeuren", r(0, 16))],
    23: [("Maar Hij, Zich omkerende, zei tot Petrus: Ga weg achter Mij, satan! u bent Mij een aanstoot, want u verzint niet de dingen, die Gods zijn, maar die van de mensen zijn", r(0, 22))],
    24: [("Toen zei Jezus tot Zijn discipelen: Zo iemand achter Mij wil komen, die verloochene zichzelf, en neme zijn kruis op, en volge Mij", r(0, 22))],
    25: [("Want zo wie zijn leven zal willen behouden, die zal hetzelfde verliezen; maar zo wie zijn leven verliezen zal, om Mijnentwil, die zal hetzelfde vinden", r(0, 20))],
    26: [("Want wat baat het een mens, zo hij de hele wereld gewint, en lijdt schade van zijn ziel? Of wat zal een mens geven, tot losprijs van zijn ziel?", r(0, 21))],
    27: [("Want de Zoon des mensen zal komen in de heerlijkheid van Zijn Vader, met Zijn engelen, en dan zal Hij ieder vergelden naar zijn doen", r(0, 24))],
    28: [("Voorwaar zeg Ik u: Er zijn sommigen van die hier staan, die de dood niet smaken zullen, voordat zij de Zoon des mensen zullen hebben zien komen in Zijn Koninkrijk", r(0, 24))],
}


def build(utr_path: Path, osis_path: Path, write=False):
    source = load_tr_chapter(utr_path, osis_path, chapter=16, osis_book="Matt")
    chapter_path = ROOT / "data" / "mattheus" / "16.json"
    chapter = json.loads(chapter_path.read_text(encoding="utf-8"))
    reviewed_through = max(SPECS)
    review = {"book": "mattheus", "chapter": 16, "reviewed_through": reviewed_through, "verses": {}}
    for verse in chapter["verses"][:reviewed_through]:
        number = int(verse["number"]); tokens = source[number]; groups = SPECS[number]
        covered = [index for _, ids in groups for index in ids]
        if sorted(covered) != list(range(len(tokens))) or len(set(covered)) != len(tokens):
            raise ValueError(f"Mattheüs 16:{number}: onvolledige of dubbele handmatige review")
        verse["grondtekst"] = [{"woord": t["woord"], "strongs": t["display_strong"], "lemma_strongs": t["lemma_strong"], "morfologie": t["morphology"], **({"tvm": t["tvm"]} if t.get("tvm") else {})} for t in tokens]
        verse["woordnummers"] = [mapping(anchor, ids, tokens, number) for anchor, ids in groups]
        for item in verse["woordnummers"]: item["herkomst"]["referentie"] = f"MAT 16:{number}"
        review["verses"][str(number)] = [{"tekst": a, "bronindices": ids, "reviewstatus": "handmatig_gecontroleerd"} for a, ids in groups]
    if write:
        chapter_path.write_text(json.dumps(chapter, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        (ROOT / "data" / "woordnummers-review" / "mattheus-16.json").write_text(json.dumps(review, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        inline_path = ROOT / "data" / "woordnummers-inline" / "mattheus.json"; inline = json.loads(inline_path.read_text(encoding="utf-8"))
        inline["chapters"]["16"] = {str(v["number"]): v["woordnummers"] for v in chapter["verses"][:reviewed_through]}
        inline_path.write_text(json.dumps(inline, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"verses": reviewed_through, "tokens": sum(len(source[n]) for n in range(1, reviewed_through + 1))}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(); parser.add_argument("--utr", type=Path, required=True); parser.add_argument("--osis", type=Path, required=True); parser.add_argument("--write", action="store_true")
    args = parser.parse_args(); print(json.dumps(build(args.utr, args.osis, args.write), indent=2))
