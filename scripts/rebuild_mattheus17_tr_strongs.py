#!/usr/bin/env python3
"""Publiceer gecontroleerde TR-koppelingen voor Mattheüs 17 in versbatches."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from rebuild_nt_tr_strongs import load_tr_chapter
from rebuild_johannes2_tr_strongs import mapping, r

ROOT = Path(__file__).resolve().parents[1]

SPECS = {
    1: [("En na zes dagen nam Jezus met Zich Petrus, en Jakobus, en Johannes, zijn broer, en bracht hen op een hoge berg alleen", r(0, 23))],
    2: [("En Hij werd voor hen veranderd van gedaante; en Zijn aangezicht blonk gelijk de zon, en Zijn kleren werden wit gelijk het licht", r(0, 20))],
    3: [("En ziet, van hen werden gezien Mozes en Elia, met Hem samensprekende", r(0, 9))],
    4: [("En Petrus, antwoordende, zei tot Jezus: Heere! het is goed, dat wij hier zijn; zo U wilt, laat ons hier drie tenten maken, voor U één, en voor Mozes één, en één voor Elia", r(0, 26))],
    5: [("Terwijl hij nog sprak, ziet, een luchtige wolk heeft hen overschaduwd; en ziet, een stem uit de wolk, zeggende: Deze is Mijn geliefde Zoon, in Die Ik Mijn welbehagen heb; hoor Hem!", r(0, 26))],
    6: [("En de discipelen, dit horende, vielen op hun aangezicht, en werden zeer bevreesd", r(0, 10))],
    7: [("En Jezus, bij hen komende, raakte hen aan, en zei: Sta op en vreest niet", r(0, 11))],
    8: [("En hun ogen opheffende, zagen zij niemand, dan Jezus alleen", r(0, 11))],
    9: [("En als zij van de berg afkwamen, gebood hun Jezus, zeggende: Zeg niemand dit visioen, totdat de Zoon des mensen zal opgestaan zijn uit de doden", r(0, 23))],
    10: [("En Zijn discipelen vraagden Hem, zeggende: Wat zeggen dan de Schriftgeleerden, dat Elia eerst moet komen?", r(0, 16))],
    11: [("Maar Jezus, antwoordende, zei tot hen: Elia zal wel eerst komen, en alles weer oprichten", r(0, 12))],
    12: [("Maar Ik zeg u, dat Elia nu gekomen is, en zij hebben hem niet gekend; maar zij hebben aan hem gedaan, al wat zij hebben gewild; zo zal ook de Zoon des mensen van hen lijden", r(0, 26))],
    13: [("Toen verstonden de discipelen dat Hij hun van Johannes de Doper gesproken had", r(0, 10))],
    14: [("En als zij bij de menigte gekomen waren, kwam tot Hem een mens, vallende voor Hem op de knieën, en zeggende", r(0, 12))],
    15: [("Heere! ontferm U over mijn zoon; want hij is maanziek, en is in zwaar lijden; want dikwijls valt hij in het vuur, en dikwijls in het water", r(0, 20))],
    16: [("En ik heb hem tot Uw discipelen gebracht, en zij hebben hem niet kunnen genezen", r(0, 10))],
    17: [("En Jezus, antwoordende, zei: O, ongelovig en verkeerd geslacht, hoe lang zal Ik nog met u zijn, hoe lang zal Ik u nog verdragen? Breng hem Mij hier", r(0, 22))],
    18: [("En Jezus bestrafte hem, en de duivel ging van hem uit, en het kind werd genezen van dat uur af", r(0, 18))],
    19: [("Toen kwamen de discipelen tot Jezus alleen, en zeiden: Waarom hebben wij hem niet kunnen uitwerpen?", r(0, 15))],
    20: [("En Jezus zei tot hen: Vanwege uw ongeloof; want voorwaar zeg Ik u: Zo u een geloof had als een mosterdzaad, u zou tot deze berg zeggen: Ga heen van hier daarheen, en hij zal heengaan; en niets zal u onmogelijk zijn", r(0, 31))],
    21: [("Maar dit geslacht vaart niet uit, dan door bidden en vasten", r(0, 11))],
    22: [("En als zij in Galilea verbleven, zei Jezus tot hen: De Zoon des mensen zal overgeleverd worden in de handen van de mensen", r(0, 18))],
    23: [("En zij zullen Hem doden, en op de derde dag zal Hij opgewekt worden. En zij werden zeer bedroefd", r(0, 10))],
    24: [("En als zij te Kapernaüm ingekomen waren, gingen tot Petrus die de didrachmen ontvingen, en zeiden: Uw Meester, betaalt Hij de didrachmen niet?", r(0, 20))],
    25: [("Hij zei: Ja. En toen hij in huis gekomen was, voorkwam hem Jezus, zeggende: Wat denkt u, Simon! de koningen van de aarde, van wie nemen zij tollen of belasting, van hun zonen, of van de vreemden?", r(0, 34))],
    26: [("Petrus zei tot Hem: Van de vreemden. Jezus zei tot hem: Zo zijn dan de zonen vrij", r(0, 15))],
    27: [("Maar opdat wij hun geen aanstoot geven, ga heen naar de zee, werp de vishaak uit, en de eerste vis, die opkomt, neem, en zijn mond geopend hebbende, zult u een stater vinden; neem die, en geef hem aan hen voor Mij en u", r(0, 31))],
}


def build(utr_path: Path, osis_path: Path, write=False):
    source = load_tr_chapter(utr_path, osis_path, chapter=17, osis_book="Matt")
    chapter_path = ROOT / "data" / "mattheus" / "17.json"
    chapter = json.loads(chapter_path.read_text(encoding="utf-8"))
    reviewed_through = max(SPECS)
    review = {"book": "mattheus", "chapter": 17, "reviewed_through": reviewed_through, "verses": {}}
    for verse in chapter["verses"][:reviewed_through]:
        number = int(verse["number"]); tokens = source[number]; groups = SPECS[number]
        covered = [index for _, ids in groups for index in ids]
        if sorted(covered) != list(range(len(tokens))) or len(set(covered)) != len(tokens):
            raise ValueError(f"Mattheüs 17:{number}: onvolledige of dubbele handmatige review")
        verse["grondtekst"] = [{"woord": t["woord"], "strongs": t["display_strong"], "lemma_strongs": t["lemma_strong"], "morfologie": t["morphology"], **({"tvm": t["tvm"]} if t.get("tvm") else {})} for t in tokens]
        verse["woordnummers"] = [mapping(anchor, ids, tokens, number) for anchor, ids in groups]
        for item in verse["woordnummers"]: item["herkomst"]["referentie"] = f"MAT 17:{number}"
        review["verses"][str(number)] = [{"tekst": a, "bronindices": ids, "reviewstatus": "handmatig_gecontroleerd"} for a, ids in groups]
    if write:
        chapter_path.write_text(json.dumps(chapter, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        (ROOT / "data" / "woordnummers-review" / "mattheus-17.json").write_text(json.dumps(review, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        inline_path = ROOT / "data" / "woordnummers-inline" / "mattheus.json"; inline = json.loads(inline_path.read_text(encoding="utf-8"))
        inline["chapters"]["17"] = {str(v["number"]): v["woordnummers"] for v in chapter["verses"][:reviewed_through]}
        inline_path.write_text(json.dumps(inline, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"verses": reviewed_through, "tokens": sum(len(source[n]) for n in range(1, reviewed_through + 1))}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(); parser.add_argument("--utr", type=Path, required=True); parser.add_argument("--osis", type=Path, required=True); parser.add_argument("--write", action="store_true")
    args = parser.parse_args(); print(json.dumps(build(args.utr, args.osis, args.write), indent=2))
