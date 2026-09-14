#!/usr/bin/env python3
"""Verwerk de Google-opmerkingen bij 3 Ezra.

Van de veertien meldingen stonden er twaalf al goed: de oude woorden waren
eerder vervangen, de maten en het grote getal in 2:14 rekent de leesoptie om,
en de ongezuurde broden staan in de voedselwiki. Alleen "niet te verzuimen"
(2:20) stond er nog.

Draaien vanuit de repo-root:  python scripts/apply_google_review_3ezra.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from review_hulp import registreer_principes, schrijf_reviewlijst, verwerk_correcties  # noqa: E402

BOEK = "3ezra"
NAAM = "3 Ezra"

CORRECTIES = {
    (2, 20): [("niet te verzuimen", "dit niet te laten liggen", "MR-3EZ-001")],
}

NIEUW = [
    {
        "id": "MR-3EZ-001",
        "categorie": "Menselijke review",
        "oud": "niet te verzuimen",
        "nieuw": "dit niet te laten liggen",
        "toelichting": "De brief aan de koning zegt dat men de zaak niet wil laten "
                       "liggen. Beoordeeld in de review van 3 Ezra; niet zonder "
                       "herbeoordeling buiten dit bereik toepassen.",
        "regex": "",
        "voorbeeld": "3ezra 2:20",
        "bereik": {BOEK: ["2:20"]},
        "bron": "menselijke-review",
    },
]

REEDS = "Stond al zo in de leestekst."
MATEN = "De leesoptie voor maten rekent dit al om"

BESLUITEN = [
    ("1:2", "[Oude woorden vervangen] Dagordening", "tekst_eenduidig", "afgedekt",
     "'dagordening' staat als 'dagelijkse beurt' (principe V1628)."),
    ("1:5", "[Principe] Voorwchrift van David", "principe", "afgedekt",
     "Staat als 'naar het voorschrift van David'."),
    ("1:10", "Ongezuurde broden in de wiki opnemen", "wiki", "afgedekt",
     "Het lemma Ongezuurd brood in de voedselwiki noemt dit vers al."),
    ("1:36", "Talenten zilver ook eenheden erbij", "eenheden", "afgedekt",
     MATEN + ": 'honderd talenten (ongeveer 3,4 ton) zilver'."),
    ("1:43", "Meer tussenkopjes", "kopjes", "afgedekt",
     "3 Ezra heeft kopjes om de zes tot twaalf verzen; bij 1:43 staat 'Joakim en "
     "Zedekia'. De langste stukken zonder kopje zijn elk één toespraak, één gebed of "
     "één lijst (4:13-32, 8:74-91, 9:18-36)."),
    ("2:14", "Eenheden ook integreren dus 5469", "getalweergave", "afgedekt",
     "Met de optie 'getallen in cijfers' staat er 'vijfduizend, "
     "vierhonderdennegenenzestig (5.469)'."),
    ("2:20", "[Oude woorden vervangen] Verzuimen", "tekst_eenduidig", "verwerkt",
     "'niet te verzuimen' is nu 'dit niet te laten liggen'."),
    ("3:19", "[Oude woorden vervangen] Oversterk -", "tekst_eenduidig", "afgedekt",
     "'oversterk' staat als 'buitengewoon sterk' (principe V1629)."),
    ("4:4", "[Oude woorden vervangen] Slechten", "tekst_eenduidig", "afgedekt",
     "'slechten' staat als 'met de grond gelijkmaken' (principe V1630)."),
    ("4:27", "[Oude woorden vervangen] Verworgd", "tekst_eenduidig", "afgedekt",
     "'verworgd' staat als 'gewurgd'."),
    ("6:9", "Bouwende waren , andere volgorde", "tekst_eenduidig", "afgedekt",
     "Staat als 'een nieuw en groot huis bouwden'."),
    ("8:23,53", "[Oude woorden vervangen] Sterkte onzes heeren", "tekst_eenduidig",
     "afgedekt", "Staat als 'de sterkte van onze Heere'."),
    ("8:23,57", "Eenehden erij", "eenheden", "afgedekt",
     MATEN + ": 'zeshonderdvijftig talenten (ongeveer 22 ton) zilver'."),
    ("9:36", "[Principe] Uitlandse - buitenlandse", "principe", "afgedekt",
     REEDS + " Principe V1638."),
]


def main():
    registreer_principes("MR-3EZ-", NIEUW, gebruikt=["MR-3EZ-001"])
    verzen = verwerk_correcties(BOEK, NAAM, CORRECTIES)
    lijst = schrijf_reviewlijst(BOEK, NAAM, BESLUITEN)
    print("%d verzen in %s bijgewerkt; %d meldingen in de reviewlijst." % (verzen, NAAM, lijst))


if __name__ == "__main__":
    main()
