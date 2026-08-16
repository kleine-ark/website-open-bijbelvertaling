#!/usr/bin/env python3
"""Publiceer gecontroleerde TR-koppelingen voor Mattheüs 22:1-10."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from rebuild_johannes2_tr_strongs import mapping, r
from rebuild_nt_tr_strongs import load_tr_chapter

ROOT = Path(__file__).resolve().parents[1]

SPECS = {
    1: [("En Jezus, antwoordende, sprak tot hen opnieuw door gelijkenissen, zeggende:", r(0, 9))],
    2: [("Het Koninkrijk van de hemelen is gelijk aan een zeker koning, die zijn zoon een bruiloft bereid had;", r(0, 12))],
    3: [("En zond zijn dienaren uit, om de genodigden ter bruiloft te roepen; en zij wilden niet komen.", r(0, 14))],
    4: [("Opnieuw zond hij andere dienaren uit, zeggende: Zeg de genodigden: Zie, ik heb mijn middagmaal bereid; mijn ossen, en de gemeste beesten zijn geslacht, en alle dingen zijn gereed; kom tot de bruiloft.", r(0, 26))],
    5: [("Maar zij, dat niet achtende, zijn heengegaan, deze tot zijn akker, de ander tot zijn koopmanschap.", r(0, 15))],
    6: [("En de anderen grepen zijn dienaren, deden hun smaad aan, en doodden hen.", r(0, 9))],
    7: [("Als nu de koning dat hoorde, werd hij boos, en zijn legers zendende, heeft die moordenaars vernield, en hun stad in brand gestoken.", r(0, 18))],
    8: [("Toen zei hij tot zijn dienaren: De bruiloft is wel bereid, maar de genodigden waren het niet waard.", r(0, 15))],
    9: [("Daarom gaat op de uitgangen van de wegen, en zovelen als u er zult vinden, roept ze tot de bruiloft.", r(0, 14))],
    10: [("En dezelfde dienaren, uitgaande op de wegen, verzamelden allen, die zij vonden, zowel kwaden als goeden; en de bruiloft werd vervuld met aanzittende gasten.", r(0, 20))],
    11: [("En als de koning ingegaan was, om de aanzittende gasten te overzien, zag hij daar een mens, niet gekleed zijnde met een bruiloftskleed;", r(0, 13))],
    12: [("En zei tot hem: Vriend! hoe bent u hier ingekomen, geen bruiloftskleed aan hebbende? En hij verstomde.", r(0, 13))],
    13: [("Toen zei de koning tot de dienaren: Bind zijn handen en voeten, neemt hem weg, en werpt hem uit in de buitenste duisternis; daar zal zijn gehuil en knersing van de tanden.", r(0, 28))],
    14: [("Want velen zijn geroepen, maar weinigen uitverkoren.", r(0, 6))],
    15: [("Toen gingen de Farizeën heen, en hielden samen raad, hoe zij Hem verstrikken zouden in Zijn rede.", r(0, 10))],
    16: [("En zij zonden uit tot Hem hun discipelen, met de Herodianen, zeggende: Meester! wij weten, dat U waarachtig bent, en de weg van God in van de waarheid leert, en naar niemand vraagt; want U ziet de persoon van de mensen niet aan;", r(0, 34))],
    17: [("Zeg ons dan: wat denkt U? Is het geoorloofd, de keizer belasting te geven of niet?", r(0, 11))],
    18: [("Maar Jezus, bekennende hun boosheid, zei:", r(0, 11))],
    19: [("U huichelaars, wat verzoekt u Mij? Toon Mij de schattingpenning. En zij brachten Hem een penning.", r(0, 10))],
    20: [("En Hij zei tot hen: Van wie is dit beeld en het opschrift?", r(0, 9))],
    21: [("Zij zeiden tot Hem: van de keizer. Toen zei Hij tot hen: Geef dan de keizer, dat van de keizer is, en voor God, dat van God is.", r(0, 16))],
    22: [("En zij, dit horende, verwonderden zich, en Hem verlatende, zijn zij weggegaan.", r(0, 6))],
    23: [("Op dezelfde dag kwamen tot Hem de Sadduceën, die zeggen, dat er geen opstanding is, en vraagden Hem.", r(0, 14))],
    24: [("Zeggende: Meester! Mozes heeft gezegd: Als iemand sterft, geen kinderen hebbende, zo zal zijn broer zijn vrouw trouwen, en zijn broer zaad verwekken.", r(0, 22))],
    25: [("Nu waren er bij ons zeven broers; en de eerste, een vrouw getrouwd hebbende, stierf; en omdat hij geen zaad had, zo liet hij zijn vrouw voor zijn broer.", r(0, 21))],
    26: [("Evenzo ook de tweede, en de derde, tot de zevende toe.", r(0, 9))],
    27: [("Ten laatste na allen, is ook de vrouw gestorven.", r(0, 6))],
    28: [("In de opstanding dan, wiens vrouw zal zij wezen van die zeven, want zij hebben ze allen gehad?", r(0, 12))],
    29: [("Maar Jezus antwoordde en zei tot hen: U dwaalt, niet wetende de Schriften, noch de kracht van God.", r(0, 15))],
    30: [("Want in de opstanding nemen zij niet ten huwelijk, noch worden ten huwelijk uitgegeven; maar zij zijn als engelen van God in de hemel.", r(0, 15))],
    31: [("En wat betreft de opstanding van de doden, hebt u niet gelezen, wat van God tot u gesproken is, Die daar zegt:", r(0, 14))],
    32: [("Ik ben de God van Abraham, en de God van Izak, en de God van Jakob! God is niet een God van de doden, maar van de levenden.", r(0, 20))],
    33: [("En de menigten, dit horende, werden verslagen over Zijn leer.", r(0, 8))],
    34: [("En de Farizeën, gehoord hebbende, dat Hij de Sadduceën de mond gestopt had, zijn samen bijeenvergaderd.", r(0, 11))],
    35: [("En één uit hen, zijnde een wetgeleerde, heeft gevraagd, Hem verzoekende, en zeggende:", r(0, 9))],
    36: [("Meester! welk is het grote gebod in de wet?", r(0, 6))],
    37: [("En Jezus zei tot hem: U zult liefhebben de Heere, uw God, met geheel uw hart, en met geheel uw ziel, en met geheel uw verstand.", r(0, 26))],
    38: [("Dit is het eerste en het grote gebod.", r(0, 5))],
    39: [("En het tweede aan dit gelijk, is: U zult uw naaste liefhebben als uzelf.", r(0, 9))],
    40: [("Aan deze twee geboden hangt de hele wet en de profeten.", r(0, 11))],
    41: [("Als nu de Farizeën samenvergaderd waren, vraagde hun Jezus,", r(0, 7))],
    42: [("En zei: Wat denkt u van de Christus? Van wie is Hij de Zoon? Zij zeiden tot Hem: Davids Zoon.", r(0, 13))],
    43: [("Hij zei tot hen: Hoe noemt Hem dan David, in de Geest, zijn Heere? zeggende:", r(0, 10))],
    44: [("De Heere heeft gezegd tot Mijn Heere: Zit aan Mijn rechterhand, totdat Ik Uw vijanden zal gezet hebben tot een voetbank van Uw voeten.", r(0, 19))],
    45: [("Als Hem dan David noemt zijn Heere, hoe is Hij zijn Zoon?", r(0, 9))],
    46: [("En niemand kon Hem een woord antwoorden; noch iemand durfde Hem van die dag aan iets meer vragen.", r(0, 15))],
}


def build(utr_path: Path, osis_path: Path, write=False):
    source = load_tr_chapter(utr_path, osis_path, chapter=22, osis_book="Matt")
    chapter_path = ROOT / "data" / "mattheus" / "22.json"
    chapter = json.loads(chapter_path.read_text(encoding="utf-8"))
    reviewed_through = max(SPECS)
    review = {"book": "mattheus", "chapter": 22, "reviewed_through": reviewed_through, "verses": {}}
    for verse in chapter["verses"][:reviewed_through]:
        number = int(verse["number"])
        tokens = source[number]
        groups = SPECS[number]
        covered = [index for _, indices in groups for index in indices]
        if sorted(covered) != list(range(len(tokens))) or len(set(covered)) != len(tokens):
            raise ValueError(f"Mattheüs 22:{number}: onvolledige of dubbele handmatige review")
        verse["grondtekst"] = [
            {"woord": token["woord"], "strongs": token["display_strong"], "lemma_strongs": token["lemma_strong"], "morfologie": token["morphology"], **({"tvm": token["tvm"]} if token.get("tvm") else {})}
            for token in tokens
        ]
        verse["woordnummers"] = [mapping(anchor, indices, tokens, number) for anchor, indices in groups]
        for item in verse["woordnummers"]:
            item["herkomst"]["referentie"] = f"MAT 22:{number}"
        review["verses"][str(number)] = [
            {"tekst": anchor, "bronindices": indices, "reviewstatus": "handmatig_gecontroleerd"}
            for anchor, indices in groups
        ]
    if write:
        chapter_path.write_text(json.dumps(chapter, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        (ROOT / "data" / "woordnummers-review" / "mattheus-22.json").write_text(
            json.dumps(review, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        inline_path = ROOT / "data" / "woordnummers-inline" / "mattheus.json"
        inline = json.loads(inline_path.read_text(encoding="utf-8"))
        inline["chapters"]["22"] = {
            str(verse["number"]): verse["woordnummers"] for verse in chapter["verses"][:reviewed_through]
        }
        inline_path.write_text(json.dumps(inline, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"verses": reviewed_through, "tokens": sum(len(source[number]) for number in range(1, reviewed_through + 1))}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--utr", type=Path, required=True)
    parser.add_argument("--osis", type=Path, required=True)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    print(json.dumps(build(args.utr, args.osis, args.write), indent=2))
