#!/usr/bin/env python3
"""Publiceer gecontroleerde TR-koppelingen voor Mattheüs 19 in versbatches."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from rebuild_nt_tr_strongs import load_tr_chapter
from rebuild_johannes2_tr_strongs import mapping, r

ROOT = Path(__file__).resolve().parents[1]

SPECS = {
    1: [("En het gebeurde, toen Jezus deze woorden geëindigd had, dat Hij vertrok van Galilea, en kwam over de Jordaan, in het gebied van Judea", r(0, 22))],
    2: [("En vele menigten volgden Hem, en Hij genas ze daar", r(0, 8))],
    3: [("En de Farizeën kwamen tot Hem, verzoekende Hem, en zeggende tot Hem: Is het een mens geoorloofd zijn vrouw te verlaten, om allerlei oorzaak?", r(0, 19))],
    4: [("Maar Hij, antwoordende, zei tot hen: Hebt u niet gelezen, Die van de beginne de mens gemaakt heeft, dat Hij ze gemaakt heeft man en vrouw?", r(0, 16))],
    5: [("En gezegd heeft: Daarom zal een mens vader en moeder verlaten, en zal zijn vrouw aanhangen, en die twee zullen tot één vlees zijn", r(0, 22))],
    6: [("Zo dat zij niet meer twee zijn, maar één vlees. Wat dan God samengevoegd heeft, scheide de mens niet", r(0, 14))],
    7: [("Zij zeiden tot hem: Waarom heeft dan Mozes geboden een scheidbrief te geven en haar te verlaten?", r(0, 11))],
    8: [("Hij zei tot hen: Mozes heeft vanwege de hardheid van uw harten u toegelaten uw vrouwen te verlaten; maar van de beginne is het zo niet geweest", r(0, 19))],
    9: [("Maar Ik zeg u, dat zo wie zijn vrouw verlaat, anders dan om hoererij, en een andere trouwt, die doet overspel, en die de verlatene trouwt, doet ook overspel", r(0, 22))],
    10: [("Zijn discipelen zeiden tot Hem: Als de zaak van de mensen met de vrouw zo staat, zo is het niet raadzaam te trouwen", r(0, 17))],
    11: [("Maar Hij zei tot hen: Allen vatten dit woord niet, maar die het gegeven is", r(0, 12))],
    12: [("Want er zijn gesnedenen, die uit moeders lijf zo geboren zijn; en er zijn gesnedenen, die van de mensen gesneden zijn; en er zijn gesnedenen, die zichzelf gesneden hebben, om het Koninkrijk van de hemelen. Die dit vatten kan, vatte het", r(0, 31))],
    13: [("Toen werden kinderen tot Hem gebracht, opdat Hij de handen hun zou opleggen en bidden; en de discipelen bestraften dezelfde", r(0, 15))],
    14: [("Maar Jezus zei: Laat af van de kinderen, en verhindert hen niet tot Mij te komen; want voor zulke mensen is het Koninkrijk van de hemelen", r(0, 21))],
    15: [("En als Hij hun de handen opgelegd had, vertrok Hij van daar", r(0, 6))],
    16: [("En ziet, er kwam een tot Hem, en zei tot Hem: Goede Meester! wat zal ik goeds doen, opdat ik het eeuwige leven hebbe?", r(0, 14))],
    17: [("En Hij zei tot hem: Wat noemt u Mij goed? Niemand is goed dan Één, namelijk God. Maar wilt u in het leven ingaan, onderhoud de geboden", r(0, 24))],
    18: [("Hij zei tot Hem: Welke? En Jezus zei: Deze: U zult niet doden; u zult geen overspel doen; u zult niet stelen; u zult geen valse getuigenis geven", r(0, 15))],
    19: [("Eer uw vader en moeder; en: U zult uw naaste liefhebben als uzelf", r(0, 13))],
    20: [("De jongeling zei tot Hem: Al deze dingen heb ik onderhouden van mijn jeugd af; wat ontbreekt mij nog?", r(0, 12))],
    21: [("Jezus zei tot hem: Zo u wilt volmaakt zijn, ga heen, verkoop wat u hebt, en geef het de armen, en u zult een schat hebben in de hemel; en kom herwaarts, volg Mij", r(0, 24))],
    22: [("Als nu de jongeling dit woord hoorde, ging hij bedroefd weg; want hij had vele goederen", r(0, 12))],
    23: [("En Jezus zei tot Zijn discipelen: Voorwaar, Ik zeg u, dat een rijke moeilijk in het Koninkrijk van de hemelen zal ingaan", r(0, 18))],
    24: [("En opnieuw zeg Ik u: Het is gemakkelijker, dat een kameel gaat door het oog van een naald, dan dat een rijke ingaat in het Koninkrijk van God", r(0, 18))],
    25: [("Zijn discipelen nu, dit horende, werden zeer verslagen, zeggende: Wie kan dan zalig worden?", r(0, 11))],
    26: [("En Jezus, hen aanziende, zei tot hen: Bij de mensen is dat onmogelijk, maar bij God zijn alle dingen mogelijk", r(0, 16))],
    27: [("Toen antwoordde Petrus, en zei tot Hem: Zie, wij hebben alles verlaten, en zijn U gevolgd, wat zal ons dan geworden?", r(0, 16))],
    28: [("En Jezus zei tot hen: Voorwaar, Ik zeg u, dat u, die Mij gevolgd bent, in de wedergeboorte, wanneer de Zoon des mensen zal gezeten zijn op de troon van Zijn heerlijkheid, dat u ook zult zitten op twaalf tronen, oordelende de twaalf geslachten van Israël", r(0, 37))],
    29: [("En zo wie zal verlaten hebben, huizen, of broers, of zussen, of vader, of moeder, of vrouw, of kinderen, of akkers, omwille van Mijn Naam, die zal honderdvoud ontvangen, en het eeuwige leven beërven", r(0, 28))],
    30: [("Maar vele eersten zullen de laatsten zijn, en vele laatsten de eersten", r(0, 7))],
}


def build(utr_path: Path, osis_path: Path, write=False):
    source = load_tr_chapter(utr_path, osis_path, chapter=19, osis_book="Matt")
    chapter_path = ROOT / "data" / "mattheus" / "19.json"
    chapter = json.loads(chapter_path.read_text(encoding="utf-8"))
    reviewed_through = max(SPECS)
    review = {"book": "mattheus", "chapter": 19, "reviewed_through": reviewed_through, "verses": {}}
    for verse in chapter["verses"][:reviewed_through]:
        number = int(verse["number"]); tokens = source[number]; groups = SPECS[number]
        covered = [index for _, ids in groups for index in ids]
        if sorted(covered) != list(range(len(tokens))) or len(set(covered)) != len(tokens):
            raise ValueError(f"Mattheüs 19:{number}: onvolledige of dubbele handmatige review")
        verse["grondtekst"] = [{"woord": t["woord"], "strongs": t["display_strong"], "lemma_strongs": t["lemma_strong"], "morfologie": t["morphology"], **({"tvm": t["tvm"]} if t.get("tvm") else {})} for t in tokens]
        verse["woordnummers"] = [mapping(anchor, ids, tokens, number) for anchor, ids in groups]
        for item in verse["woordnummers"]: item["herkomst"]["referentie"] = f"MAT 19:{number}"
        review["verses"][str(number)] = [{"tekst": a, "bronindices": ids, "reviewstatus": "handmatig_gecontroleerd"} for a, ids in groups]
    if write:
        chapter_path.write_text(json.dumps(chapter, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        (ROOT / "data" / "woordnummers-review" / "mattheus-19.json").write_text(json.dumps(review, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        inline_path = ROOT / "data" / "woordnummers-inline" / "mattheus.json"; inline = json.loads(inline_path.read_text(encoding="utf-8"))
        inline["chapters"]["19"] = {str(v["number"]): v["woordnummers"] for v in chapter["verses"][:reviewed_through]}
        inline_path.write_text(json.dumps(inline, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"verses": reviewed_through, "tokens": sum(len(source[n]) for n in range(1, reviewed_through + 1))}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(); parser.add_argument("--utr", type=Path, required=True); parser.add_argument("--osis", type=Path, required=True); parser.add_argument("--write", action="store_true")
    args = parser.parse_args(); print(json.dumps(build(args.utr, args.osis, args.write), indent=2))
