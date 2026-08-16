#!/usr/bin/env python3
"""Publiceer gecontroleerde TR-koppelingen voor Mattheüs 18 in versbatches."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from rebuild_nt_tr_strongs import load_tr_chapter
from rebuild_johannes2_tr_strongs import mapping, r

ROOT = Path(__file__).resolve().parents[1]

SPECS = {
    1: [("Op dat moment kwamen de discipelen tot Jezus, zeggende: Wie is toch de meeste in het Koninkrijk van de hemelen?", r(0, 18))],
    2: [("En Jezus een kind tot Zich geroepen hebbende, stelde dat in het midden van hen", r(0, 9))],
    3: [("En zei: Voorwaar zeg Ik u: Als u zich niet verandert, en wordt zoals de kinderen, zo zult u in het Koninkrijk van de hemelen in geen geval ingaan", r(0, 20))],
    4: [("Zo wie dan zichzelf zal vernederen, zoals dit kind, deze is de meeste in het Koninkrijk van de hemelen", r(0, 16))],
    5: [("En zo wie zulk een kind ontvangt in Mijn Naam, die ontvangt Mij", r(0, 12))],
    6: [("Maar zo wie één van deze kleinen, die in Mij geloven, ten val brengt, het was hem beter, dat een molensteen aan zijn hals gehangen, en dat hij verzonken was in de diepte van de zee", r(0, 28))],
    7: [("Wee de wereld vanwege de struikelblokken, want het is noodzakelijk, dat de struikelblokken komen; maar wee die mens, door welke het struikelblok komt!", r(0, 21))],
    8: [("Als dan uw hand of uw voet u doet struikelen, houwt ze af en werpt ze van u. Het is u beter, tot het leven in te gaan, kreupel of verminkt zijnde, dan twee handen of twee voeten hebbende, in het eeuwige vuur geworpen te worden", r(0, 39))],
    9: [("En als uw oog u doet struikelen, trekt het uit, en werpt het van u. Het is u beter, maar één oog hebbende, tot het leven in te gaan, dan twee ogen hebbende, in het helse vuur geworpen te worden", r(0, 30))],
    10: [("Zie toe, dat u niet één van deze kleinen veracht. Want Ik zeg u, dat hun engelen, in de hemelen, altijd zien het aangezicht van Mijn Vader, Die in de hemelen is", r(0, 26))],
    11: [("Want de Zoon des mensen is gekomen om zalig te maken, dat verloren was", r(0, 8))],
    12: [("Wat denkt u, als enig mens honderd schapen had, en een daaruit afgedwaald was, zal hij niet de negen en negentig laten, en op de bergen heengaande, het afgedwaalde zoeken?", r(0, 24))],
    13: [("En als het gebeurt, dat hij hetzelfde vindt, voorwaar zeg Ik u, dat hij zich meer verblijdt over hetzelfde, dan over de negen en negentig, die niet afgedwaald zijn geweest", r(0, 19))],
    14: [("Zo is de wil niet van uw Vader, Die in de hemelen is, dat één van deze kleinen verloren ga", r(0, 16))],
    15: [("Maar als uw broeder tegen u gezondigd heeft, ga heen en bestraf hem tussen u en hem alleen; als hij u hoort, zo hebt u uw broeder gewonnen", r(0, 23))],
    16: [("Maar als hij u niet hoort, zo neem nog een of twee met u; opdat in de mond van twee of drie getuigen alle woord besta", r(0, 20))],
    17: [("En als hij dezelfde geen gehoor geeft; zo zeg het van de gemeente; en als hij ook van de gemeente geen gehoor geeft, zo zij hij u als de heiden en de tollenaar", r(0, 20))],
    18: [("Voorwaar zeg Ik u: Al wat u op de aarde binden zult, zal in de hemel gebonden wezen; en al wat u op de aarde ontbinden zult, zal in de hemel ontbonden wezen", r(0, 25))],
    19: [("Opnieuw zeg Ik u: Als er twee van u samenstemmen op de aarde, over enige zaak, die zij zouden mogen begeren, dat die hun zal gebeuren van Mijn Vader, Die in de hemelen is", r(0, 25))],
    20: [("Want waar twee of drie vergaderd zijn in Mijn Naam, daar ben Ik in het midden van hen", r(0, 15))],
    21: [("Toen kwam Petrus tot Hem, en zei: Heere! hoe dikwijls zal mijn broeder tegen mij zondigen, en ik hem vergeven! Tot zevenmaal?", r(0, 18))],
    22: [("Jezus zei tot hem: Ik zeg u, niet tot zevenmaal, maar tot zeventigmaal zeven maal", r(0, 12))],
    23: [("Daarom wordt het Koninkrijk van de hemelen vergeleken bij een zeker koning, die rekening met zijn dienaren houden wilde", r(0, 16))],
    24: [("Als hij nu begon te rekenen, werd tot hem gebracht één, die hem schuldig was tien duizend talenten", r(0, 9))],
    25: [("En als hij niet had, om te betalen, beval zijn heer, dat men hem zou verkopen, en zijn vrouw en kinderen, en al wat hij had, en dat de schuld zou betaald worden", r(0, 23))],
    26: [("De dienaar dan, nedervallende, aanbad hem, zeggende: Heere! wees geduldig over mij, en ik zal u alles betalen", r(0, 14))],
    27: [("En de heer van deze dienaar, met barmhartigheid innerlijk bewogen zijnde, heeft hem ontslagen, en de schuld hem kwijtgescholden", r(0, 13))],
    28: [("Maar dezelfde dienaar, uitgaande, heeft gevonden één van zijn mededienstknechten, die hem honderd penningen schuldig was, en hem aanvattende, greep hem bij de keel, zeggende: Betaal mij, wat u schuldig bent", r(0, 24))],
    29: [("Zijn mededienstknecht dan, nedervallende aan zijn voeten, bad hem, zeggende: Wees geduldig over mij, en ik zal u alles betalen", r(0, 18))],
    30: [("Maar hij wilde niet, maar ging heen, en wierp hem in de gevangenis, totdat hij de schuld zou betaald hebben", r(0, 14))],
    31: [("Als nu zijn mededienstknechten zagen, wat gebeurd was, zijn zij zeer bedroefd geworden; en komende, verklaarden zij hun heer al wat er gebeurd was", r(0, 17))],
    32: [("Toen heeft hem zijn heer tot zich geroepen, en zei tot hem: U slechte dienaar, al die schuld heb ik u kwijtgescholden, omdat u mij gebeden hebt", r(0, 18))],
    33: [("Behoorde u ook niet u over uw mededienstknecht te ontfermen, zoals ik ook mij over u ontfermd heb?", r(0, 12))],
    34: [("En zijn heer, vertoornd zijnde, leverde hem de pijnigers over, totdat hij zou betaald hebben al wat hij hem schuldig was", r(0, 15))],
    35: [("Zo zal ook Mijn hemelse Vader u doen, als u niet van harte vergeeft ieder zijn broeder zijn misdaden", r(0, 22))],
}


def build(utr_path: Path, osis_path: Path, write=False):
    source = load_tr_chapter(utr_path, osis_path, chapter=18, osis_book="Matt")
    chapter_path = ROOT / "data" / "mattheus" / "18.json"
    chapter = json.loads(chapter_path.read_text(encoding="utf-8"))
    reviewed_through = max(SPECS)
    review = {"book": "mattheus", "chapter": 18, "reviewed_through": reviewed_through, "verses": {}}
    for verse in chapter["verses"][:reviewed_through]:
        number = int(verse["number"]); tokens = source[number]; groups = SPECS[number]
        covered = [index for _, ids in groups for index in ids]
        if sorted(covered) != list(range(len(tokens))) or len(set(covered)) != len(tokens):
            raise ValueError(f"Mattheüs 18:{number}: onvolledige of dubbele handmatige review")
        verse["grondtekst"] = [{"woord": t["woord"], "strongs": t["display_strong"], "lemma_strongs": t["lemma_strong"], "morfologie": t["morphology"], **({"tvm": t["tvm"]} if t.get("tvm") else {})} for t in tokens]
        verse["woordnummers"] = [mapping(anchor, ids, tokens, number) for anchor, ids in groups]
        for item in verse["woordnummers"]: item["herkomst"]["referentie"] = f"MAT 18:{number}"
        review["verses"][str(number)] = [{"tekst": a, "bronindices": ids, "reviewstatus": "handmatig_gecontroleerd"} for a, ids in groups]
    if write:
        chapter_path.write_text(json.dumps(chapter, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        (ROOT / "data" / "woordnummers-review" / "mattheus-18.json").write_text(json.dumps(review, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        inline_path = ROOT / "data" / "woordnummers-inline" / "mattheus.json"; inline = json.loads(inline_path.read_text(encoding="utf-8"))
        inline["chapters"]["18"] = {str(v["number"]): v["woordnummers"] for v in chapter["verses"][:reviewed_through]}
        inline_path.write_text(json.dumps(inline, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"verses": reviewed_through, "tokens": sum(len(source[n]) for n in range(1, reviewed_through + 1))}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(); parser.add_argument("--utr", type=Path, required=True); parser.add_argument("--osis", type=Path, required=True); parser.add_argument("--write", action="store_true")
    args = parser.parse_args(); print(json.dumps(build(args.utr, args.osis, args.write), indent=2))
