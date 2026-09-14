#!/usr/bin/env python3
"""Verwerk de Google-opmerkingen bij Judith.

Van de zes meldingen stonden er drie al goed. Nieuw: "uitgelezen mannen"
(2:7) en een uitleg bij de naam Nabuchodonosor (2:1) in de begrippenlijst.

Draaien vanuit de repo-root:  python scripts/apply_google_review_judith.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from review_hulp import registreer_principes, schrijf_reviewlijst, verwerk_correcties  # noqa: E402
from sweep_principe import lees, schrijf  # noqa: E402

BOEK = "judith"
NAAM = "Judith"

CORRECTIES = {
    (2, 7): [("telde uitgelezen mannen", "telde uitgekozen mannen", "MR-JDT-001")],
}

NIEUW = [
    {
        "id": "MR-JDT-001",
        "categorie": "Menselijke review",
        "oud": "uitgelezen mannen",
        "nieuw": "uitgekozen mannen",
        "toelichting": "Zoals MR-1KR-004 in 1 Kronieken 9:22. Beoordeeld in de review "
                       "van Judith; niet zonder herbeoordeling buiten dit bereik toepassen.",
        "regex": "",
        "voorbeeld": "judith 2:7",
        "bereik": {BOEK: ["2:7"]},
        "bron": "menselijke-review",
    },
]

NABUCHODONOSOR = (
    "Koning van het Nieuw-Babylonische rijk (regeerde 605-562 v.Chr.), in de boeken uit "
    "het Hebreeuws Nebukadnezar genoemd. Nabuchodonosor is de Griekse en Latijnse vorm "
    "van die naam, zoals de Septuagint en de Vulgaat hem schrijven. De Statenvertaling "
    "vertaalde de apocriefe boeken uit het Grieks en nam die spelling over. Het boek "
    "Judith noemt hem koning van de Assyriërs, al was hij Babyloniër."
)


def werk_begrippenlijst_bij():
    pad = ROOT / "data" / "begrippenlijst-judith.json"
    data, vorm = lees(str(pad))
    # lees() leidt de inspringing af uit de eerste regel met een sleutel; bij een
    # lijst als buitenste laag staat die een niveau dieper dan de inspringing.
    ruw = pad.read_text(encoding="utf-8")
    vorm["indent"] = len(re.search(r"\n( +)\S", ruw).group(1))
    lemma = next(item for item in data if item["woord"] == "Nabuchodonosor")
    if lemma["uitleg"] == NABUCHODONOSOR:
        return False
    lemma["uitleg"] = NABUCHODONOSOR
    lemma.setdefault("ook", [])
    if "Nebukadnezar" not in lemma["ook"]:
        lemma["ook"].append("Nebukadnezar")
    schrijf(str(pad), data, vorm)
    return True


REEDS = "Stond al zo in de leestekst."

BESLUITEN = [
    ("1:3", "Eenheden missen op meerdere plekkenngier in ditbhoofdstuk", "eenheden",
     "afgedekt",
     "De leesoptie voor maten rekent de ellen in dit hoofdstuk om, bijvoorbeeld "
     "'honderd ellen (ongeveer 45 meter)'."),
    ("2:1", "Onderzoek waarom deze verbastering van nebudanzear er js", "onderzoek",
     "verwerkt",
     "Nabuchodonosor is de Griekse en Latijnse spelling van Nebukadnezar; de "
     "Statenvertaling vertaalde de apocriefen uit het Grieks. Die uitleg staat nu bij "
     "het lemma in de begrippenlijst van Judith."),
    ("2:7", "[Oude woorden vervangen] Yutgelezen", "tekst_eenduidig", "verwerkt",
     "'uitgelezen mannen' is nu 'uitgekozen mannen'."),
    ("5:3", "[Principe] Kanaans - van kanaan", "principe", "afgedekt",
     "Staat als 'u kinderen van Kanaän' (principe O26)."),
    ("7:10", "[Oude woorden vervangen] Beoorloog", "tekst_eenduidig", "afgedekt",
     "'beoorloog' staat als 'bevecht' (principe V1636)."),
    ("8:15", "[Oude woorden vervangen] Ten pand", "tekst_eenduidig", "afgedekt",
     "'ten pand' staat als 'in pand' (principe V1639)."),
]


def main():
    registreer_principes("MR-JDT-", NIEUW, gebruikt=["MR-JDT-001"])
    verzen = verwerk_correcties(BOEK, NAAM, CORRECTIES)
    lemma = werk_begrippenlijst_bij()
    lijst = schrijf_reviewlijst(BOEK, NAAM, BESLUITEN)
    print("%d verzen in %s bijgewerkt; begrippenlijst %s; %d meldingen in de reviewlijst."
          % (verzen, NAAM, "bijgewerkt" if lemma else "ongewijzigd", lijst))


if __name__ == "__main__":
    main()
