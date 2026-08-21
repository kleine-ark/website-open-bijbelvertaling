#!/usr/bin/env python3
"""Verwerk de handmatige beoordeling van de 27 B-citaatgevallen.

De detector kan niet onderscheiden of een aankondiging vertelling is, of deel
uitmaakt van een doorgaande rede waarin iemand anders wordt aangehaald. Daarom
staat ieder geval hier expliciet als te corrigeren of bewust te behouden.
"""

from collections import defaultdict
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from apply_citations_2koningen import markeer
from sweep_principe import kaal, lees, schrijf


# (boek, hoofdstuk, vers) -> [(spreker, begin, einde)]
# Alleen de letterlijke woorden staan in de span; de aankondiging en eventuele
# vertelling na het citaat blijven erbuiten.
CLEAR_RANGES = {
    ("daniel", 6, 26): [("mens", "Uw vrede worde", "vermenigvuldigd!")],
    ("exodus", 33, 21): [("god", "Zie, er is", "steenrots stellen.")],
    ("jeremia", 4, 11): [("god", "Een dorre wind", "om te zuiveren.")],
    ("jeremia", 46, 17): [("mens", "Farao, de koning", "laten voorbijgaan.")],
    ("jesaja", 10, 13): [("mens", "Door de kracht", "doen neerdalen;")],
    ("jesaja", 28, 12): [("god", "Dit is de rust", "dit is de verkwikking;")],
    ("jesaja", 37, 22): [("god", "De jonkvrouw", "hoofd achter u.")],
    ("job", 42, 7): [("god", "Mijn toorn is", "Mijn knecht Job.")],
    ("mattheus", 18, 22): [("god", "Ik zeg u", "zeventigmaal zeven maal.")],
}

# Deze verzen zijn handmatig beoordeeld. De aankondiging staat hier binnen een
# doorgaande rede (of binnen een als geheel aangehaalde Schriftpassage) en is
# daarom geen grensfout. Sommige bevatten een aanhaling binnen die rede; die
# rechtvaardigt geen verwijdering van de buitenste span.
REVIEWED_KEEP = {
    ("4ezra", 4, 15): "Uriël spreekt door en vertelt de gelijkenis van zee en bos.",
    ("4ezra", 4, 35): "De vraag staat binnen Uriëls doorgaande antwoord.",
    ("baruch", 3, 35): "De poëtische rede wordt als geheel aangehaald.",
    ("exodus", 16, 16): "Mozes spreekt door en haalt het gebod van JAHWEH aan.",
    ("exodus", 32, 12): "Mozes bidt en citeert daarin de mogelijke woorden van Egypte.",
    ("ezechiel", 26, 2): "JAHWEH spreekt door en haalt Tyrus aan.",
    ("johannes", 7, 36): "De omstanders spreken en halen Jezus binnen hun vraag aan.",
    ("leviticus", 9, 3): "Mozes spreekt door en geeft een opdracht over wat gezegd moet worden.",
    ("lukas", 19, 20): "Jezus spreekt door in de gelijkenis en haalt de dienaar aan.",
    ("markus", 12, 36): "Jezus spreekt door en citeert binnen Zijn rede de Psalm.",
    ("markus", 7, 10): "Jezus spreekt door en citeert Mozes.",
    ("mattheus", 15, 4): "Jezus spreekt door en citeert het gebod.",
    ("mattheus", 19, 5): "Jezus spreekt door vanuit vers 4 en citeert de Schrift.",
    ("mattheus", 25, 23): "Jezus spreekt door in de gelijkenis en haalt de heer aan.",
    ("psalmen", 83, 5): "De Psalm is de buitenste rede en haalt de vijanden aan.",
    ("richteren", 9, 8): "Jotham spreekt door in de gelijkenis van de bomen.",
    ("romeinen", 9, 26): "De aangehaalde Schriftpassage wordt als geheel weergegeven.",
    ("ruth", 2, 7): "De knecht antwoordt door en haalt Ruth binnen zijn antwoord aan.",
}


def main() -> int:
    per_bestand = defaultdict(dict)
    for (boek, hoofdstuk, vers), ranges in CLEAR_RANGES.items():
        per_bestand[(boek, hoofdstuk)][vers] = ranges

    gewijzigd = 0
    for (boek, hoofdstuk), opdrachten in sorted(per_bestand.items()):
        pad = ROOT / "data" / boek / f"{hoofdstuk}.json"
        data, vorm = lees(str(pad))
        bestand_gewijzigd = False
        for item in data["verses"]:
            ranges = opdrachten.get(item["number"])
            if ranges is None:
                continue
            oud = item["text2026_html"]
            nieuw = markeer(oud, ranges)
            if kaal(oud) != kaal(nieuw):
                raise ValueError(f"Citaatcorrectie veranderde tekst: {boek} {hoofdstuk}:{item['number']}")
            if nieuw.count("<span") != nieuw.count("</span>"):
                raise ValueError(f"Ongebalanceerde span: {boek} {hoofdstuk}:{item['number']}")
            if nieuw.count("<i>") != nieuw.count("</i>"):
                raise ValueError(f"Ongebalanceerde cursivering: {boek} {hoofdstuk}:{item['number']}")
            if nieuw != oud:
                item["text2026_html"] = nieuw
                gewijzigd += 1
                bestand_gewijzigd = True
        if bestand_gewijzigd:
            schrijf(str(pad), data, vorm)

    print(f"Citaatgrenzen bijgewerkt: {gewijzigd} verzen; {len(REVIEWED_KEEP)} B-gevallen bewust behouden.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
