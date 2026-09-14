#!/usr/bin/env python3
"""Verwerk de Google-opmerkingen bij 4 Ezra.

Acht van de elf meldingen stonden al goed of zijn elders opgelost (de
getaloptie las "de duizenden van de hemel" in 13:3 als getal). Nieuw hier:

1. De oude verleden tijd op -t na "u" ("u verwektet", 3:23). Principe V1168
   had die vormen elders al vervangen; in de boeken die nog niet definitief
   zijn stonden er nog vijftien, in 4 Ezra, 2 Samuël, de Wijsheid van
   Salomo, 3 Makkabeeën, 3 Meqabyan en 4 Baruch.
2. De datering: die noemt nu dat hoofdstuk 1-2 en 15-16 later zijn toegevoegd.

De melding bij 3:4 (hoofdletters voor God in alle apocriefen) raakt veel meer
verzen en loopt als eigen doorvoering.

Draaien vanuit de repo-root:  python scripts/apply_google_review_4ezra.py
"""

from __future__ import annotations

import io
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from review_hulp import schrijf_reviewlijst, verwerk_correcties  # noqa: E402

BOEK = "4ezra"
NAAM = "4 Ezra"

# De oude verleden tijd op -t, per boek. Alle aan principe V1168.
OUDE_VERLEDEN_TIJD = {
    ("4ezra", "4 Ezra"): {
        (3, 9): [("deedt u na verloop van tijd", "deed u na verloop van tijd"),
                 ("en u verdierft ze", "en u verdierf ze")],
        (3, 18): [("Daar boogt u de hemel", "Daar boog u de hemel"),
                  ("u bewoogt de aardbodem", "u bewoog de aardbodem"),
                  ("de afgrond deedt u beven", "de afgrond deed u beven"),
                  ("u verschriktet de wereld", "u verschrikte de wereld")],
        (3, 23): [("u verwektet u een knecht", "u verwekte voor uzelf een knecht")],
        (5, 43): [("Kondt u niet maken", "Kon u niet maken")],
        (6, 41): [("schiept U de lucht", "schiep U de lucht")],
        (6, 46): [("U geboodt hun", "U gebood hun")],
        (6, 53): [("geboodt U de aarde", "gebood U de aarde")],
    },
    ("2samuel", "2 Samuël"): {
        (22, 40): [("U deedt onder mij", "U deed onder mij")],
    },
    ("boekderwijsheid", "Wijsheid"): {
        (18, 5): [("naamt u tot overtuiging", "nam u tot overtuiging"),
                  ("en verdierft hen", "en verdierf hen")],
    },
    ("3makkabeeen", "3 Makkabeeën"): {
        (6, 5): [("maar U zondt de vlam", "maar U zond de vlam")],
    },
    ("3meqabyan", "3 Meqabyan"): {
        (2, 18): [("toen u Eva verleiddet", "toen u Eva verleidde"),
                  ("verleiddet u haar", "verleidde u haar")],
    },
    ("4baruch", "4 Baruch"): {
        (5, 20): [("Waart u geen oude man", "Was u geen oude man")],
    },
}

SCHRIJFTIJD = ("±100–120 n.Chr. (na verwoesting Jeruzalem); hoofdstuk 1–2 en 15–16 "
               "zijn latere christelijke toevoegingen uit de 2e–3e eeuw")


def werk_datering_bij():
    """Vervang alleen de waarde, zodat de opmaak van het bestand blijft zoals hij is."""
    pad = ROOT / "data" / "book-dating.json"
    with io.open(pad, encoding="utf-8", newline="") as bestand:
        ruw = bestand.read()
    huidig = json.loads(ruw)[BOEK]["schrijftijd"]
    if huidig == SCHRIJFTIJD:
        return False
    oud, nieuw = json.dumps(huidig, ensure_ascii=False), json.dumps(SCHRIJFTIJD, ensure_ascii=False)
    if ruw.count(oud) != 1:
        raise ValueError("schrijftijd van %s niet eenduidig te vinden" % BOEK)
    with io.open(pad, "w", encoding="utf-8", newline="") as bestand:
        bestand.write(ruw.replace(oud, nieuw))
    return True


REEDS = "Stond al zo in de leestekst."

BESLUITEN = [
    ("1:5", "Bij Gods citatie hoofdletters gebruiken", "hoofdletters", "afgedekt",
     "Waar God spreekt staan Mijn en Mij met hoofdletter (principe V1640)."),
    ("2:9", "[Oude woorden vervangen] Pekachollen", "tekst_eenduidig", "afgedekt",
     "'pekschollen' staat als 'brokken pek'."),
    ("3:4", "Ina lle apocrieven hoofdletter gebruik van God nalopen", "hoofdletters",
     "gepland",
     "Loopt als eigen doorvoering door de apocriefe boeken die nog niet definitief "
     "zijn: U en Uw waar iemand God aanspreekt."),
    ("3:9", "[Oude woorden vervangen] Mettertijd", "tekst_eenduidig", "afgedekt",
     "'mettertijd' staat als 'na verloop van tijd' (principe V1635). Daarbij zijn "
     "'deedt' en 'verdierft' nu 'deed' en 'verdierf'."),
    ("3:23", "Verwektet", "tekst_eenduidig", "verwerkt",
     "'u verwektet u een knecht' is nu 'u verwekte voor uzelf een knecht'. Dezelfde "
     "oude vormen zijn ook elders vervangen: 3:9, 3:18, 5:43, 6:41, 6:46, 6:53, en in "
     "2 Samuël 22:40, Wijsheid 18:5, 3 Makkabeeën 6:5, 3 Meqabyan 2:18 en 4 Baruch "
     "5:20 (principe V1168)."),
    ("4:7", "[Oude woorden vervangen] Firmament", "tekst_eenduidig", "afgedekt",
     "'firmament' staat als 'uitspansel' (principe V1634)."),
    ("4:36", "[Citatie]", "citatieopmaak", "afgedekt",
     "De opmaak klopt: Uriël vertelt wat de aartsengel Jeremiël de zielen antwoordde, "
     "en die woorden staan als citaat binnen het zijne."),
    ("5:19", "Pas de schrijftijd aan, klopt niet ook bij 3 ezra", "datering", "open",
     "Bij 4 Ezra noemt de datering nu ook dat hoofdstuk 1-2 en 15-16 later zijn "
     "toegevoegd. Bij 3 Ezra staat '± 2e eeuw v.Chr.', wat de gangbare datering is; "
     "wat daar niet klopt is uit de melding niet op te maken."),
    ("11:22", "Vederkens - veertjes", "tekst_eenduidig", "afgedekt",
     REEDS + " Principe V1067."),
    ("11:24", "[Principe] Vederkens - veren", "principe", "afgedekt",
     "Principe V1067 kiest 'veertjes', zoals de melding bij 11:22 voorstelt; de twee "
     "meldingen spreken elkaar hier tegen."),
    ("13:3", "Geen getal in dit geval", "getalweergave", "verwerkt",
     "De getaloptie las 'de duizenden van de hemel' als 1.000. Een meervoud als "
     "'duizenden' telt nu niet meer als getal."),
]


def main():
    verzen = 0
    for (boek, naam), correcties in OUDE_VERLEDEN_TIJD.items():
        met_principe = {sleutel: [(o, n, "V1168") for o, n in paren]
                        for sleutel, paren in correcties.items()}
        verzen += verwerk_correcties(boek, naam, met_principe)
    datering = werk_datering_bij()
    lijst = schrijf_reviewlijst(BOEK, NAAM, BESLUITEN)
    print("%d verzen bijgewerkt; datering %s; %d meldingen in de reviewlijst."
          % (verzen, "bijgewerkt" if datering else "ongewijzigd", lijst))


if __name__ == "__main__":
    main()
