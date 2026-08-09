#!/usr/bin/env python3
"""Haalt de citaatmarkering van Mozes' eigen rede uit Deuteronomium weg.

Deuteronomium is één lange toespraak van Mozes. Die als citaat markeren zet
vrijwel het hele boek tussen aanhalingstekens, en dat zegt de lezer niets: het
boek ís Mozes. De uitzondering op de gewone regel — sprekende mensen krijgen
direct-speech — geldt dus voor Mozes zelf in dit boek.

Wat blijft staan:

* elke god-speaks — JAHWEH aangehaald binnen de rede van Mozes is wél een
  citaat, en dat is juist het hart van het boek;
* elke direct-speech waar iemand anders dan Mozes spreekt: het volk dat
  antwoordt ("Toen antwoordde u mij, en zei:"), de verspieders, de broers, en
  de hypothetische sprekers in de wetten ("dat hij zichzelf zegene in zijn
  hart, zeggende:").

Wat weggaat:

* de spans die aan het begin van een vers staan — dat is de rede van Mozes die
  doorloopt van vers op vers;
* de spans waar Mozes zelf de aangekondigde spreker is; die verzen staan
  hieronder met naam en toenaam, zodat de keuze na te lopen is;
* tien lege spans, <span class="direct-speech"><i></i></span>, die achter "Zo
  zei JAHWEH tot mij:" waren blijven staan terwijl de woorden zelf in een
  aparte god-speaks zitten. Die leverden een zwevend leesteken op.

Gebruik:
    python scripts/deuteronomium_mozes.py --droog
    python scripts/deuteronomium_mozes.py
"""
import argparse
import glob
import json
import os
import re
import sys

WORTEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(WORTEL, "scripts"))
from sweep_principe import lees, schrijf, kaal  # noqa: E402

# Verzen waar een aankondiging vóór de span staat én Mozes de spreker is.
# Met de hand nagelopen; de rest van de aangekondigde spans is iemand anders.
MOZES_SPREEKT = {
    (1, 9), (1, 16), (1, 20), (1, 29),
    (3, 18), (3, 21),
    (15, 11), (19, 7),
    (27, 1), (29, 2),
    (31, 2), (31, 7), (31, 10),
    (32, 46),
}

OPEN = '<span class="direct-speech"><i>'
LEEG = '<span class="direct-speech"><i></i></span>'


def verwijder_span(html, pos):
    """Haalt de span die op pos begint weg, met zijn eigen sluittag.

    Er kan een god-speaks in genest zitten; die moet blijven staan. Daarom
    wordt geteld hoeveel spans er open staan, zodat de juiste sluittag wordt
    gevonden en niet de eerste de beste.
    """
    i = pos + len(OPEN)
    diepte = 1
    while i < len(html):
        if html.startswith("<span", i):
            diepte += 1
            i = html.index(">", i) + 1
            continue
        if html.startswith("</i></span>", i):
            diepte -= 1
            if diepte == 0:
                return html[:pos] + html[pos + len(OPEN):i] + html[i + len("</i></span>"):]
            i += len("</i></span>")
            continue
        i += 1
    return None


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--droog", action="store_true")
    a = p.parse_args()

    weg_begin = weg_mozes = weg_leeg = behouden = 0
    bestanden = 0

    for pad in sorted(glob.glob(os.path.join(WORTEL, "data", "deuteronomium", "*.json")),
                      key=lambda x: int(re.search(r"(\d+)\.json", x).group(1))):
        d, vorm = lees(pad)
        hs = d.get("number")
        gewijzigd = False
        for v in d["verses"]:
            html = v.get("text2026_html") or ""
            if OPEN not in html:
                continue
            voor = html

            # 1) lege spans zijn altijd restafval
            n = html.count(LEEG)
            if n:
                html = html.replace(LEEG, "")
                weg_leeg += n

            # 2) van achter naar voren, zodat de posities blijven kloppen
            posities = [m.start() for m in re.finditer(re.escape(OPEN), html)]
            for pos in reversed(posities):
                aankondiging = re.sub(r"<[^>]+>", "", html[:pos]).strip()
                begin_van_vers = not aankondiging or re.fullmatch(r"[\w']{1,3}", aankondiging)
                if begin_van_vers:
                    nieuw = verwijder_span(html, pos)
                    if nieuw is not None:
                        html = nieuw
                        weg_begin += 1
                elif (hs, v["number"]) in MOZES_SPREEKT:
                    nieuw = verwijder_span(html, pos)
                    if nieuw is not None:
                        html = nieuw
                        weg_mozes += 1
                else:
                    behouden += 1

            if html == voor:
                continue
            if kaal(html) != kaal(voor):
                print(f"!! {hs}:{v['number']} tekst gewijzigd, overgeslagen")
                continue
            if html.count("<span") != html.count("</span>") or html.count("<i>") != html.count("</i>"):
                print(f"!! {hs}:{v['number']} ongebalanceerd, overgeslagen")
                continue
            if not a.droog:
                v["text2026_html"] = re.sub(r"  +", " ", html)
                gewijzigd = True
        if gewijzigd:
            schrijf(pad, d, vorm)
            bestanden += 1

    print(f"{'ZOU WEGHALEN' if a.droog else 'WEGGEHAALD'}:")
    print(f"  doorlopende rede van Mozes : {weg_begin}")
    print(f"  Mozes als spreker aangekondigd: {weg_mozes}")
    print(f"  lege spans                 : {weg_leeg}")
    print(f"  behouden (iemand anders spreekt): {behouden}")
    if not a.droog:
        print(f"  bestanden geschreven: {bestanden}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
