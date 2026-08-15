#!/usr/bin/env python3
"""Publiceer de handmatig beoordeelde TR-koppelingen voor Johannes 3."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from rebuild_nt_tr_strongs import load_tr_chapter
from rebuild_johannes2_tr_strongs import mapping, r

ROOT = Path(__file__).resolve().parents[1]


SPECS = {
    1: [("En er was", r(0, 1)), ("een mens", r(2)), ("uit de Farizeeën", r(3, 5)),
        ("wiens naam Nicodemus was", r(6, 8)), ("een overste van de Joden", r(9, 11))],
    2: [("Deze kwam", r(0, 1)), ("in de nacht tot Jezus", r(2, 5)), ("en zei tot Hem", r(6, 8)),
        ("Rabbi", r(9)), ("wij weten, dat", r(10, 11)), ("U bent een Leraar van God gekomen", r(12, 15)),
        ("want niemand kan", r(16, 17)), ("deze tekenen doen", r(18, 22)),
        ("die U doet", r(23, 25)), ("zo God met hem niet is", r(26, 32))],
    3: [("Jezus antwoordde en zei tot hem", r(0, 5)), ("Voorwaar, voorwaar zeg Ik u", r(6, 9)),
        ("Tenzij dat iemand", r(10, 12)), ("opnieuw geboren wordt", r(13, 14)),
        ("hij kan", r(15, 16)), ("het Koninkrijk van God niet zien", r(17, 21))],
    4: [("Nicodemus zei tot Hem", r(0, 4)), ("Hoe kan een mens geboren worden", r(5, 8)),
        ("nu oud zijnde", r(9, 10)), ("Kan hij ook", r(11, 12)),
        ("andermaal in van zijn moeders buik ingaan", r(13, 20)), ("en geboren worden", r(21, 22))],
    5: [("Jezus antwoordde", r(0, 2)), ("Voorwaar, voorwaar zeg Ik u", r(3, 6)),
        ("Zo iemand niet", r(7, 9)), ("geboren wordt uit water en Geest", r(10, 14)),
        ("hij kan", r(15, 16)), ("in het Koninkrijk van God niet ingaan", r(17, 22))],
    6: [("Wat uit het vlees geboren is", r(0, 4)), ("dat is vlees", r(5, 6)),
        ("en wat uit de Geest geboren is", r(7, 12)), ("dat is geest", r(13, 14))],
    7: [("Verwonder u niet", r(0, 1)), ("dat Ik u gezegd heb", r(2, 4)),
        ("U moet", r(5, 6)), ("opnieuw geboren worden", r(7, 8))],
    8: [("De wind", r(0, 1)), ("waarheen hij wil", r(2, 3)), ("blaast", r(4)),
        ("en u hoort zijn geluid", r(5, 9)), ("maar u weet niet", r(10, 12)),
        ("vanwaar hij komt", r(13, 14)), ("en waar hij heen gaat", r(15, 17)),
        ("zo is ieder", r(18, 20)), ("die uit de Geest geboren is", r(21, 25))],
    9: [("Nicodemus antwoordde en zei tot Hem", r(0, 4)), ("Hoe kunnen deze dingen gebeuren", r(5, 8))],
    10: [("Jezus antwoordde en zei tot hem", r(0, 5)), ("Bent u", r(6, 7)),
         ("een leraar van Israël", r(8, 11)), ("en weet u deze dingen niet", r(12, 15))],
    11: [("Voorwaar, voorwaar zeg Ik u", r(0, 3)), ("Wij spreken, wat Wij weten", r(4, 7)),
         ("en getuigen, wat Wij gezien hebben", r(8, 11)),
         ("en u neemt Onze getuigenis niet aan", r(12, 17))],
    12: [("Als Ik u de aardse dingen gezegd heb", r(0, 4)), ("en u niet gelooft", r(5, 7)),
         ("hoe zult u geloven", r(8, 9)), ("als Ik u de hemelse zou zeggen", r(10, 14))],
    13: [("En niemand is opgevaren in de hemel", r(0, 5)),
         ("dan Die uit de hemel nedergekomen is", r(6, 12)),
         ("namelijk de Zoon des mensen", r(13, 16)), ("Die in de hemel is", r(17, 21))],
    14: [("En zoals Mozes", r(0, 2)), ("de slang in de woestijn verhoogd heeft", r(3, 8)),
         ("zo moet", r(9, 11)), ("de Zoon des mensen verhoogd worden", r(12, 15))],
    15: [("Opdat een ieder", r(0, 2)), ("die in Hem gelooft", r(3, 5)),
         ("niet verderve", r(6, 7)), ("maar het eeuwige leven hebbe", r(8, 11))],
    16: [("Want zo lief heeft God", r(0, 4)), ("de wereld gehad", r(5, 6)),
         ("dat Hij Zijn eniggeboren Zoon gegeven heeft", r(7, 13)),
         ("opdat een ieder", r(14, 16)), ("die in Hem gelooft", r(17, 19)),
         ("niet verderve", r(20, 21)), ("maar het eeuwige leven hebbe", r(22, 25))],
    17: [("Want God heeft Zijn Zoon niet gezonden", r(0, 7)), ("in de wereld", r(8, 10)),
         ("opdat Hij de wereld veroordelen zou", r(11, 14)),
         ("maar opdat de wereld", r(15, 19)), ("door Hem zou behouden worden", r(20, 21))],
    18: [("Die in Hem gelooft", r(0, 3)), ("wordt niet veroordeeld", r(4, 5)),
         ("maar die niet gelooft", r(6, 9)), ("is al veroordeeld", r(10, 11)),
         ("omdat hij niet heeft geloofd", r(12, 14)), ("in de Naam", r(15, 17)),
         ("van de eniggeboren Zoon van God", r(18, 22))],
    19: [("En dit is het oordeel", r(0, 4)), ("dat het licht", r(5, 7)),
         ("in de wereld gekomen is", r(8, 11)), ("en de mensen hebben", r(12, 15)),
         ("de duisternis liever gehad dan het licht", r(16, 21)),
         ("want hun werken waren boos", r(22, 27))],
    20: [("Want ieder, die kwaad doet", r(0, 4)), ("haat het licht", r(5, 7)),
         ("en komt tot het licht niet", r(8, 13)),
         ("opdat zijn werken niet bestraft worden", r(14, 19))],
    21: [("Maar die de waarheid doet", r(0, 4)), ("komt tot het licht", r(5, 8)),
         ("opdat zijn werken openbaar worden", r(9, 13)),
         ("dat zij in God gedaan zijn", r(14, 18))],
    22: [("Na deze kwam Jezus", r(0, 4)), ("en Zijn discipelen", r(5, 8)),
         ("in het land van Judea", r(9, 12)), ("en onthield Zich daar met hen", r(13, 17)),
         ("en doopte", r(18, 19))],
    23: [("En Johannes doopte ook", r(0, 4)), ("in Enon bij Salim", r(5, 9)),
         ("omdat daar vele wateren waren", r(10, 14)), ("en zij kwamen daar", r(15, 16)),
         ("en werden gedoopt", r(17, 18))],
    24: [("Want Johannes was nog niet", r(0, 2)), ("in de gevangenis geworpen", r(3, 8))],
    25: [("Er rees dan een vraag", r(0, 2)), ("van enige uit de discipelen van Johannes", r(3, 6)),
         ("met de Joden", r(7, 8)), ("over de reiniging", r(9, 10))],
    26: [("En zij kwamen tot Johannes", r(0, 4)), ("en zeiden tot hem", r(5, 7)),
         ("Rabbi", r(8)), ("Die met u was", r(9, 12)), ("over de Jordaan", r(13, 15)),
         ("Wie u getuigenis gaf", r(16, 18)), ("zie, Die doopt", r(19, 21)),
         ("en zij komen allen tot Hem", r(22, 26))],
    27: [("Johannes antwoordde en zei", r(0, 3)), ("Een mens kan geen ding aannemen", r(4, 8)),
         ("zo het hem", r(9, 13)), ("uit de hemel niet gegeven zij", r(14, 16))],
    28: [("U bent mijn getuigen", r(0, 3)), ("dat ik gezegd heb", r(4, 5)),
         ("Ik ben de Christus niet", r(6, 10)), ("maar dat ik", r(11, 12)),
         ("voor Hem heen uitgezonden ben", r(13, 16))],
    29: [("Die de bruid heeft", r(0, 3)), ("is de bruidegom", r(4, 5)),
         ("maar de vriend van de bruidegom", r(6, 10)), ("die staat en hem hoort", r(11, 15)),
         ("verblijdt zich met blijdschap", r(16, 17)), ("om de stem van de bruidegom", r(18, 22)),
         ("Zo is dan deze mijn blijdschap", r(23, 28)), ("vervuld geworden", r(29))],
    30: [("Hij moet groeien", r(0, 2)), ("maar ik minder worden", r(3, 5))],
    31: [("Die van boven komt", r(0, 2)), ("is boven allen", r(3, 5)),
         ("die uit de aarde is voortgekomen", r(6, 10)), ("die is uit de aarde", r(11, 14)),
         ("en spreekt uit de aarde", r(15, 19)), ("Die uit de hemel komt", r(20, 24)),
         ("is boven allen", r(25, 27))],
    32: [("En wat Hij gezien en gehoord heeft", r(0, 4)), ("dat getuigt Hij", r(5, 6)),
         ("en Zijn getuigenis", r(7, 10)), ("neemt niemand aan", r(11, 12))],
    33: [("Die Zijn getuigenis aangenomen heeft", r(0, 4)), ("die heeft verzegeld", r(5)),
         ("dat God waarachtig is", r(6, 10))],
    34: [("Want Die God gezonden heeft", r(0, 4)), ("Die spreekt", r(9)),
         ("de woorden van God", r(5, 8)), ("want God", r(10, 11)),
         ("geeft Hem de Geest niet met mate", r(12, 18))],
    35: [("De Vader", r(0, 1)), ("heeft de Zoon lief", r(2, 4)),
         ("en heeft alle dingen", r(5, 7)), ("in Zijn hand gegeven", r(8, 11))],
    36: [("Die in de Zoon gelooft", r(0, 4)), ("die heeft het eeuwige leven", r(5, 7)),
         ("maar die de Zoon ongehoorzaam is", r(8, 12)), ("die zal het leven niet zien", r(13, 15)),
         ("maar de toorn van God", r(16, 20)), ("blijft op hem", r(21, 23))],
}


def build(utr_path: Path, osis_path: Path, write=False):
    source = load_tr_chapter(utr_path, osis_path, chapter=3, osis_book="John")
    chapter_path = ROOT / "data" / "johannes" / "3.json"
    chapter = json.loads(chapter_path.read_text(encoding="utf-8"))
    review = {"book": "johannes", "chapter": 3, "verses": {}}
    for verse in chapter["verses"]:
        number = int(verse["number"])
        tokens = source[number]
        groups = SPECS[number]
        covered = [index for _, token_ids in groups for index in token_ids]
        if sorted(covered) != list(range(len(tokens))) or len(set(covered)) != len(tokens):
            raise ValueError(f"Johannes 3:{number}: onvolledige of dubbele handmatige review")
        verse["grondtekst"] = [{
            "woord": token["woord"], "strongs": token["display_strong"],
            "lemma_strongs": token["lemma_strong"], "morfologie": token["morphology"],
        } for token in tokens]
        verse["woordnummers"] = [mapping(anchor, ids, tokens, number) for anchor, ids in groups]
        if number == 31:
            verse["woordnummers"][-1]["voorkomen"] = 2
        for item in verse["woordnummers"]:
            item["herkomst"]["referentie"] = f"JHN 3:{number}"
        review["verses"][str(number)] = [
            {"tekst": anchor, "bronindices": ids, "reviewstatus": "handmatig_gecontroleerd"}
            for anchor, ids in groups
        ]
    if write:
        chapter_path.write_text(json.dumps(chapter, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        review_dir = ROOT / "data" / "woordnummers-review"; review_dir.mkdir(exist_ok=True)
        (review_dir / "johannes-3.json").write_text(json.dumps(review, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        inline_path = ROOT / "data" / "woordnummers-inline" / "johannes.json"
        inline = json.loads(inline_path.read_text(encoding="utf-8"))
        inline["chapters"]["3"] = {str(v["number"]): v["woordnummers"] for v in chapter["verses"]}
        inline_path.write_text(json.dumps(inline, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"verses": len(chapter["verses"]), "tokens": sum(len(value) for value in source.values())}


def main():
    parser = argparse.ArgumentParser(); parser.add_argument("--utr", type=Path, required=True)
    parser.add_argument("--osis", type=Path, required=True); parser.add_argument("--write", action="store_true")
    args = parser.parse_args(); print(json.dumps(build(args.utr, args.osis, args.write), indent=2))


if __name__ == "__main__":
    main()
