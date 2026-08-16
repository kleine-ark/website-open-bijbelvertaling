#!/usr/bin/env python3
"""Publiceer gecontroleerde TR-koppelingen voor Mattheüs 14 in versbatches."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from rebuild_nt_tr_strongs import load_tr_chapter
from rebuild_johannes2_tr_strongs import mapping, r

ROOT = Path(__file__).resolve().parents[1]

# Deze eerste batch bewaart elk vers als één volledig, Nederlands leesanker;
# de TR-indexreeks blijft ononderbroken en toetsbaar.
SPECS = {
    1: [("In die tijd hoorde Herodes, de viervorst, het gerucht van Jezus", r(0, 10))],
    2: [("En zei tot zijn knechten: Deze is Johannes de Doper; hij is opgewekt van de doden, en daarom werken die krachten in Hem", r(0, 22))],
    3: [("Want Herodes had Johannes gevangen genomen, en hem gebonden, en in de kerker gezet, om Herodias' wil, de huisvrouw van Filippus, zijn broer", r(0, 19))],
    4: [("Want Johannes zei tot hem: Het is u niet geoorloofd haar te hebben", r(0, 9))],
    5: [("En willende hem doden, vreesde hij het volk, omdat zij hem hielden voor een profeet", r(0, 11))],
    6: [("Maar als de dag van de geboorte van Herodes gehouden werd, danste de dochter van Herodias in het midden van hen, en zij behaagde aan Herodes", r(0, 16))],
    7: [("Waarom hij haar met ede beloofde te geven, wat zij ook zou eisen", r(0, 8))],
    8: [("En zij, te voren onderricht zijnde van haar moeder, zei: Geef mij hier in een schotel het hoofd van Johannes de Doper", r(0, 17))],
    9: [("En de koning werd bedroefd; maar om de eden, en degenen, die met hem aanzaten, gebood hij, dat het haar zou gegeven worden", r(0, 12))],
    10: [("En zond heen, en onthoofdde Johannes in de kerker", r(0, 7))],
    11: [("En zijn hoofd werd gebracht in een schotel, en het dochtertje gegeven; en zij droeg het tot haar moeder", r(0, 15))],
    12: [("En zijn discipelen kwamen, en namen het lichaam weg, en begroeven hetzelfde; en gingen en boodschapten het Jezus", r(0, 15))],
    13: [("En als Jezus dit hoorde, vertrok Hij van daar te scheep, naar een woeste plaats alleen; en de menigten, dat horende, zijn Hem te voet gevolgd uit de steden", r(0, 22))],
    14: [("En Jezus uitgaande, zag een grote menigte, en werd innerlijk met ontferming over hen bewogen, en genas hun zieken", r(0, 15))],
    15: [("En als het nu avond werd, kwamen Zijn discipelen tot Hem, zeggende: Deze plaats is woest, en de tijd is nu voorbijgegaan; laat de menigten van U, opdat zij heengaan in de plaatsen en zichzelf voedsel kopen", r(0, 28))],
    16: [("Maar Jezus zei tot hen: Het is hun niet nodig heen te gaan, geeft u hun te eten", r(0, 12))],
    17: [("Maar zij zeiden tot Hem: Wij hebben hier niet, dan vijf broden en twee vissen", r(0, 13))],
    18: [("En Hij zei: Breng Mij dezelfde hier", r(0, 6))],
    19: [("En Hij beval de menigten neer te zitten op het gras, en nam de vijf broden en de twee vissen, en omhoog ziende naar de hemel, zegende dezelfde; en als Hij ze gebroken had, gaf Hij de broden de discipelen, en de discipelen aan de menigten", r(0, 33))],
    20: [("En zij aten allen en werden verzadigd, en zij namen op, het overschot van de stukken brood, twaalf volle manden", r(0, 13))],
    21: [("Die nu gegeten hadden, waren ongeveer vijf duizend mannen, zonder de vrouwen en kinderen", r(0, 10))],
    22: [("En meteen dwong Jezus Zijn discipelen in het schip te gaan, en voor Hem af te varen naar de andere zijde, terwijl Hij de menigten van Zich zou laten", r(0, 22))],
    23: [("En als Hij nu de menigten van Zich gelaten had, klom Hij op de berg alleen, om te bidden. En als het nu avond was geworden, zo was Hij daar alleen", r(0, 16))],
    24: [("En het schip was nu midden in de zee, zijnde in nood van de baren; want de wind was hun tegen", r(0, 16))],
    25: [("Maar ter vierde wake in de nacht kwam Jezus af tot hen, wandelende op de zee", r(0, 13))],
    26: [("En de discipelen, ziende Hem op de zee wandelen, werden ontroerd, zeggende: Het is een spook! En zij schreeuwden van vrees", r(0, 18))],
    27: [("Maar meteen sprak hen Jezus aan, zeggende: Heb goede moed, Ik ben het, vreest niet", r(0, 11))],
    28: [("En Petrus antwoordde Hem, en zei: Heere! als U het bent, zo gebied mij tot U te komen op het water", r(0, 17))],
    29: [("En Hij zei: Kom. En Petrus klom neer van het schip, en wandelde op het water, om tot Jezus te komen", r(0, 18))],
    30: [("Maar ziende de sterke wind, werd hij bevreesd, en als hij begon neer te zinken, riep hij, zeggende: Heere, behoud mij!", r(0, 13))],
    31: [("En Jezus, meteen de hand uitstekende, greep hem aan, en zei tot hem: U kleingelovige! waarom hebt u gewankeld?", r(0, 15))],
    32: [("En als zij in het schip geklommen waren, stilde de wind", r(0, 8))],
    33: [("Die nu in het schip waren, kwamen en aanbaden Hem, zeggende: Werkelijk, U bent Gods Zoon!", r(0, 12))],
    34: [("En overgevaren zijnde, kwamen zij in het land Gennesaret", r(0, 6))],
    35: [("En als de mannen van die plaats Hem werden kennende, zonden zij in dat hele omliggende land, en brachten tot Hem allen, die kwalijk gesteld waren", r(0, 20))],
    36: [("En baden Hem, dat zij alleen de zoom van Zijn kleed zouden mogen aanraken; en zovelen als Hem aanraakten, werden gezond", r(0, 14))],
}


def build(utr_path: Path, osis_path: Path, write=False):
    source = load_tr_chapter(utr_path, osis_path, chapter=14, osis_book="Matt")
    chapter_path = ROOT / "data" / "mattheus" / "14.json"
    chapter = json.loads(chapter_path.read_text(encoding="utf-8"))
    reviewed_through = max(SPECS)
    review = {"book": "mattheus", "chapter": 14, "reviewed_through": reviewed_through, "verses": {}}
    for verse in chapter["verses"][:reviewed_through]:
        number = int(verse["number"]); tokens = source[number]; groups = SPECS[number]
        covered = [index for _, ids in groups for index in ids]
        if sorted(covered) != list(range(len(tokens))) or len(set(covered)) != len(tokens):
            raise ValueError(f"Mattheüs 14:{number}: onvolledige of dubbele handmatige review")
        verse["grondtekst"] = [{"woord": t["woord"], "strongs": t["display_strong"], "lemma_strongs": t["lemma_strong"], "morfologie": t["morphology"], **({"tvm": t["tvm"]} if t.get("tvm") else {})} for t in tokens]
        verse["woordnummers"] = [mapping(anchor, ids, tokens, number) for anchor, ids in groups]
        for item in verse["woordnummers"]: item["herkomst"]["referentie"] = f"MAT 14:{number}"
        review["verses"][str(number)] = [{"tekst": a, "bronindices": ids, "reviewstatus": "handmatig_gecontroleerd"} for a, ids in groups]
    if write:
        chapter_path.write_text(json.dumps(chapter, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        (ROOT / "data" / "woordnummers-review" / "mattheus-14.json").write_text(json.dumps(review, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        inline_path = ROOT / "data" / "woordnummers-inline" / "mattheus.json"; inline = json.loads(inline_path.read_text(encoding="utf-8"))
        inline["chapters"]["14"] = {str(v["number"]): v["woordnummers"] for v in chapter["verses"][:reviewed_through]}
        inline_path.write_text(json.dumps(inline, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"verses": reviewed_through, "tokens": sum(len(source[n]) for n in range(1, reviewed_through + 1))}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(); parser.add_argument("--utr", type=Path, required=True); parser.add_argument("--osis", type=Path, required=True); parser.add_argument("--write", action="store_true")
    args = parser.parse_args(); print(json.dumps(build(args.utr, args.osis, args.write), indent=2))
