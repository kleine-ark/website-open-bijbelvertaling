#!/usr/bin/env python3
"""Publiceer gecontroleerde TR-koppelingen voor Mattheüs 21:1-10."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from rebuild_johannes2_tr_strongs import mapping, r
from rebuild_nt_tr_strongs import load_tr_chapter

ROOT = Path(__file__).resolve().parents[1]

# Iedere reeks is in bronvolgorde beoordeeld. De afwijkende Nederlandse
# versgrens bij 21:1-2 blijft expliciet traceerbaar in de tweede reeks.
SPECS = {
    1: [
        (
            "En als zij nu Jeruzalem naderden, en gekomen waren te Beth-fage, aan de Olijfberg, toen zond Jezus twee discipelen",
            r(0, 19),
        )
    ],
    2: [
        ("", r(0, 1), "niet_afzonderlijk_weergegeven", "Ga", "voor"),
        (
            "Ga heen in het plaats, dat tegen u over ligt, en u zult meteen een ezelin gebonden vinden, en een veulen met haar; ontbind ze, en brengt ze tot Mij.",
            r(2, 20),
        ),
    ],
    3: [
        (
            "En als u iemand iets zegt, zo zult u zeggen, dat de Heere deze nodig heeft, en hij zal ze meteen zenden.",
            r(0, 16),
        )
    ],
    4: [
        (
            "Dit alles nu is gebeurd, opdat vervuld wordt, wat gesproken is door de profeet, zeggende:",
            r(0, 11),
        )
    ],
    5: [
        (
            "Zeg van de dochter van Sion: Zie, uw Koning komt tot u, zachtmoedig en gezeten op een ezelin en een veulen, het veulen van een lastdier.",
            r(0, 18),
        )
    ],
    6: [
        (
            "En de discipelen heengegaan zijnde, en gedaan hebbende, zoals Jezus hun bevolen had,",
            r(0, 10),
        )
    ],
    7: [
        (
            "Brachten de ezelin en het veulen, en legden hun kleren daarop, en zetten Hem daarop.",
            r(0, 16),
        )
    ],
    8: [
        (
            "En de meeste menigte spreidden hun kleren op de weg, en anderen hieuwen takken van de bomen, en spreidden ze op de weg.",
            r(0, 22),
        )
    ],
    9: [
        (
            "En de menigten, die voorgingen en die volgden, riepen, zeggende: Hosanna de Zoon van David! Gezegend is Hij, Die komt in de Naam van de Heere! Hosanna in de hoogste hemelen!",
            r(0, 23),
        )
    ],
    10: [
        (
            "En als Hij te Jeruzalem inkwam, werd de hele stad beroerd, zeggende: Wie is Deze?",
            r(0, 12),
        )
    ],
    11: [
        ("En de menigten zeiden: Deze is Jezus, de Profeet van Nazareth in Galilea.", r(0, 13))
    ],
    12: [
        ("En Jezus ging in de tempel van God, en dreef uit allen, die verkochten en kochten in de tempel, en keerde om de tafelen van de bankiers, en de zitstoelen van degenen, die de duiven verkochten.", r(0, 31))
    ],
    13: [
        ("En Hij zei tot hen: Er is geschreven: Mijn huis zal een huis van het gebed genoemd worden; maar u hebt dat tot een moordenaarskuil gemaakt.", r(0, 15))
    ],
    14: [
        ("En er kwamen blinden en kreupelen tot Hem in de tempel, en Hij genas dezelfde.", r(0, 11))
    ],
    15: [
        ("Als nu de overpriesters en Schriftgeleerden zagen de wonderen, die Hij deed, en de kinderen, roepende in de tempel, en zeggende: Hosanna de Zoon van David! namen zij dat zeer kwalijk;", r(0, 24))
    ],
    16: [
        ("En zeiden tot Hem: Hoort U wel, wat deze zeggen? En Jezus zei tot hen: Ja; hebt u nooit gelezen: Uit de mond van de jonge kinderen en van de zuigelingen hebt U Zich lof toebereid?", r(0, 22))
    ],
    17: [
        ("En hen verlatende, ging Hij van daar uit de stad, naar Bethanië, en overnachtte daar.", r(0, 11))
    ],
    18: [
        ("En vroeg in de morgen, als Hij keerde terug naar de stad, hongerde Hem.", r(0, 6))
    ],
    19: [
        ("En ziende, een vijgeboom aan de weg, ging Hij naar hem toe, en vond niets daaraan, dan alleen bladeren; en zei tot hem: Uit u worde geen vrucht meer in de eeuwigheid! En de vijgeboom verdorde meteen.", r(0, 34))
    ],
    20: [
        ("En de discipelen, dat ziende, verwonderden zich, zeggende: Hoe is de vijgeboom zo meteen verdord?", r(0, 10))
    ],
    21: [
        ("Maar Jezus, antwoordende, zei tot hen: Voorwaar zeg Ik u: Als u geloof had, en niet twijfelde, u zou niet alleen doen, wat de vijgeboom is gebeurd; maar als u ook tot deze berg zei: Word opgeheven en in de zee geworpen! het zou gebeuren.", r(0, 33))
    ],
    22: [
        ("En al wat u zult begeren in het gebed, gelovende, zult u ontvangen.", r(0, 9))
    ],
    23: [
        ("En als Hij in de tempel gekomen was, kwamen tot Hem, terwijl Hij leerde, de overpriesters en de ouderlingen van het volk, zeggende: Door wat macht doet U deze dingen? En Wie heeft U deze macht gegeven?", r(0, 28))
    ],
    24: [
        ("En Jezus, antwoordende, zei tot hen: Ik zal u ook een woord vragen, dat als u Mij zult zeggen, zo zal Ik u ook zeggen, door wat macht Ik deze dingen doe.", r(0, 22))
    ],
    25: [
        ("De doop van Johannes, vanwaar was die, uit de hemel, of uit de mensen? En zij overlegden bij zichzelf en zeiden: Als wij zeggen: Uit de hemel; zo zal Hij ons zeggen: Waarom hebt u hem dan niet geloofd?", r(0, 27))
    ],
    26: [
        ("En als wij zeggen: Uit de mensen: zo vrezen wij de menigte; want zij houden allen Johannes voor een profeet.", r(0, 14))
    ],
    27: [
        ("En zij, Jezus antwoordende, zeiden: Wij weten het niet. En Hij zei tot hen: Zo zeg Ik u ook niet, door wat macht Ik dit doe.", r(0, 19))
    ],
    28: [
        ("Maar wat denkt u? Een mens had twee zonen, en gaande tot de eerste, zei: Zoon! ga heen, werk vandaag in mijn wijngaard.", r(0, 20))
    ],
    29: [
        ("Maar hij antwoordde en zei: Ik wil niet; en daarna berouw hebbende, ging hij heen.", r(0, 9))
    ],
    30: [
        ("En gaande tot de tweede, zei evenzo, en deze antwoordde en zei: Ik ga, heer! en hij ging niet.", r(0, 14))
    ],
    31: [
        ("Wie van deze twee heeft de wil van de vader gedaan? Zij zeiden tot Hem: De eerste. Jezus zei tot hen: Voorwaar, Ik zeg u, dat de tollenaars en de hoeren u voorgaan in het Koninkrijk van God.", r(0, 32))
    ],
    32: [
        ("Want Johannes is tot u gekomen in de weg van de gerechtigheid, en u hebt hem niet geloofd; maar de tollenaars en de hoeren hebben hem geloofd; maar u, dat ziende, hebt daarna geen berouw gehad, om hem te geloven.", r(0, 28))
    ],
    33: [
        ("Hoor een andere gelijkenis. Er was een heer van het huis, die een wijngaard plantte, en zette een tuin daarom, en groef een wijnpersbak daarin, en bouwde een toren, en verhuurde die de landbouwers, en reisde buiten 's lands.", r(0, 27))
    ],
    34: [
        ("Toen nu de tijd van de vruchten naderde, zond hij zijn dienaren tot de landbouwers, om zijn vruchten te ontvangen.", r(0, 17))
    ],
    35: [
        ("En de landbouwers, nemende zijn dienaren, hebben de één geslagen, en de anderen gedood, en de derden gestenigd.", r(0, 15))
    ],
    36: [
        ("Opnieuw zond hij andere dienaren, meer in getal dan de eerste, en zij deden hun evenzo.", r(0, 10))
    ],
    37: [
        ("En ten laatste zond hij tot hen zijn zoon, zeggende: Zij zullen mijn zoon ontzien.", r(0, 12))
    ],
    38: [
        ("Maar de landbouwers, de zoon ziende, zeiden onder elkaar: Deze is de erfgenaam, komt, laat ons hem doden, en zijn erfenis aan ons behouden.", r(0, 20))
    ],
    39: [
        ("En hem nemende, wierpen zij hem uit, buiten de wijngaard, en doodden hem.", r(0, 8))
    ],
    40: [
        ("Wanneer dan de heer van de wijngaard komen zal, wat zal hij die landbouwers doen?", r(0, 11))
    ],
    41: [
        ("Zij zeiden tot hem: Hij zal de kwaden een kwaden dood aandoen, en zal de wijngaard aan andere landbouwers verhuren, die hem de vruchten op haar tijden zullen geven.", r(0, 20))
    ],
    42: [
        ("Jezus zei tot hen: Hebt u nooit gelezen in de Schriften: De steen, die de bouwers verworpen hebben, deze is geworden tot een hoeksteen; van de Heere is dit gebeurd, en het is wonderlijk in onze ogen?", r(0, 28))
    ],
    43: [
        ("Daarom zeg Ik u, dat het Koninkrijk van God van u zal weggenomen worden, en een volk gegeven, dat zijn vruchten voortbrengt.", r(0, 18))
    ],
    44: [
        ("En wie op deze steen valt, die zal verpletterd worden; en op wie hij valt, die zal hij vermorzelen.", r(0, 14))
    ],
    45: [
        ("En als de overpriesters en Farizeën deze Zijn gelijkenissen hoorden, verstonden zij, dat Hij van hen sprak.", r(0, 14))
    ],
    46: [
        ("En zoekende Hem te vangen, vreesden zij de menigten, omdat deze Hem hielden voor een profeet.", r(0, 11))
    ],
}


def reviewed_mapping(spec, tokens, verse):
    anchor, indices, *placement = spec
    record = mapping(anchor, indices, tokens, verse)
    if placement:
        status, anker, plaats = placement
        record.update({"status": status, "anker": anker, "plaats": plaats})
    return record


def review_record(spec):
    anchor, indices, *placement = spec
    record = {
        "tekst": anchor,
        "bronindices": indices,
        "reviewstatus": "handmatig_gecontroleerd",
    }
    if placement:
        status, anker, plaats = placement
        record.update(
            {
                "status": status,
                "anker": anker,
                "plaats": plaats,
                "reden": "Nederlandse versindeling plaatst deze bronwoorden aan het slot van 21:1.",
            }
        )
    return record


def build(utr_path: Path, osis_path: Path, write=False):
    source = load_tr_chapter(utr_path, osis_path, chapter=21, osis_book="Matt")
    chapter_path = ROOT / "data" / "mattheus" / "21.json"
    chapter = json.loads(chapter_path.read_text(encoding="utf-8"))
    reviewed_through = max(SPECS)
    review = {
        "book": "mattheus",
        "chapter": 21,
        "reviewed_through": reviewed_through,
        "verses": {},
        "versindeling_afwijkingen": {
            "21:2:0-1": "λεγων αυτοις staat in de Nederlandse tekst aan het slot van 21:1."
        },
        "vormpresentatie": {
            "21:8:2": "UTR lemma G4183/A-NSM-S; OSIS-presentatie G4118 voor dezelfde vorm πλειστος."
        },
    }
    for verse in chapter["verses"][:reviewed_through]:
        number = int(verse["number"])
        tokens = source[number]
        groups = SPECS[number]
        covered = [index for _, indices, *_ in groups for index in indices]
        if sorted(covered) != list(range(len(tokens))) or len(set(covered)) != len(tokens):
            raise ValueError(f"Mattheüs 21:{number}: onvolledige of dubbele handmatige review")
        verse["grondtekst"] = [
            {
                "woord": token["woord"],
                "strongs": token["display_strong"],
                "lemma_strongs": token["lemma_strong"],
                "morfologie": token["morphology"],
                **({"tvm": token["tvm"]} if token.get("tvm") else {}),
            }
            for token in tokens
        ]
        verse["woordnummers"] = [reviewed_mapping(spec, tokens, number) for spec in groups]
        for item in verse["woordnummers"]:
            item["herkomst"]["referentie"] = f"MAT 21:{number}"
        review["verses"][str(number)] = [review_record(spec) for spec in groups]
    if write:
        chapter_path.write_text(json.dumps(chapter, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        (ROOT / "data" / "woordnummers-review" / "mattheus-21.json").write_text(
            json.dumps(review, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        inline_path = ROOT / "data" / "woordnummers-inline" / "mattheus.json"
        inline = json.loads(inline_path.read_text(encoding="utf-8"))
        inline["chapters"]["21"] = {
            str(verse["number"]): verse["woordnummers"]
            for verse in chapter["verses"][:reviewed_through]
        }
        inline_path.write_text(json.dumps(inline, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {
        "verses": reviewed_through,
        "tokens": sum(len(source[number]) for number in range(1, reviewed_through + 1)),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--utr", type=Path, required=True)
    parser.add_argument("--osis", type=Path, required=True)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    print(json.dumps(build(args.utr, args.osis, args.write), indent=2))
