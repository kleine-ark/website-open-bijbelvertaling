#!/usr/bin/env python3
"""Haalt de aankondiging uit het citaat, Bijbelbreed.

De meest voorkomende fout in de citaatopmaak: een vers begint met een
spraak-span, en de aankondiging staat daarbinnen in plaats van erbuiten.

    <span class="god-speaks"><i>En Hij zei tot hen: Wie oren heeft…</i></span>

Daardoor wordt "En Hij zei tot hen:" weergegeven alsof het uitgesproken wordt.
Het hoort te zijn:

    En Hij zei tot hen: <span class="god-speaks"><i>Wie oren heeft…</i></span>

Dit is de enige vorm die zonder oordeel te verhelpen is. De spreker verandert
niet, dus de klasse blijft staan; er wordt alleen een grens verlegd. De andere
soorten fouten — twee sprekers in dezelfde span, een verkeerde klasse, of
opmaak die helemaal ontbreekt — vragen wél een beslissing en blijven hier
buiten.

Voorwaarden waaronder er wordt ingegrepen, alle drie tegelijk:

  1. De span staat aan het begin van het vers. Staat hij verderop, dan kan een
     "hij zei:" erbinnen een aangehaald citaat zijn (iemand die vertelt wat een
     ander zei), en dat hoort juist wél in de span.
  2. De aankondiging begint met een vertellend onderwerp (En, Toen, Maar…).
  3. Er staat een dubbele punt in, met daarachter nog echte tekst.

Na afloop wordt per vers getoetst dat de kale tekst onveranderd is en de opmaak
gebalanceerd — alleen de grens mocht verschuiven, geen letter.

Gebruik:
    python scripts/citaat_sweep.py --proef          laat zien wat er zou gebeuren
    python scripts/citaat_sweep.py                  voert het door
    python scripts/citaat_sweep.py --boek lukas     één boek
"""
import argparse
import json
import os
import re
import sys

WORTEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Een <sup> mag in de aankondiging staan (notenmarkering), verder geen opmaak:
# zodra er een span begint zijn we in een aangehaald citaat beland.
STUK = r'(?:[^<:]|<sup[^>]*>.*?</sup>)'
SPREEK = r'(?:zei|zeide|zeiden|sprak|spraken|riep|riepen|antwoordde|antwoordden|gebood|vroeg|vraagde)'
OPENER = r'(?:En|Toen|Doch|Maar|Evenwel|Zo|Daarna|Verder|Deze|Dezen|Dit|De|Hij|Zij|Alzo|Want|Anderen|Sommigen|Als|Ook)'

VERS = re.compile(
    r'^((?:<sup[^>]*>.*?</sup>|\s)*)'            # notenmarkering vóór de span
    r'<span class="([a-z-]+)"><i>'
    r'(' + OPENER + r'\b' + STUK + r'{0,130}?\b' + SPREEK + r'\b' + STUK + r'{0,70}:)'
    r'\s*(.+)</i></span>(.*)$', re.S)


def kaal(html):
    zonder = re.sub(r'<sup[^>]*>.*?</sup>', '', html)
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', zonder)).strip()


def herzie(html):
    """Verlegt de grens, of geeft None als dit vers niet in aanmerking komt."""
    m = VERS.match(html)
    if not m:
        return None
    kopnoten, klasse, aankondiging, rede, staart = m.groups()
    if len(kaal(rede)) < 10:
        return None
    if rede.lstrip().startswith('<span'):
        # De rede zit al in een eigen span. Wat de buitenste dan is, hangt van
        # de zin af en niet van de vorm:
        #
        #   1 Koningen 21:23  "Verder ook over Izebel sprak JAHWEH, zeggende:"
        #                     — vertelling, dus de buitenste moet weg
        #   2 Samuel 1:7      "…en hij riep mij, en ik zei:"
        #                     — iemand vertelt in de eerste persoon wat hij zei;
        #                       die hele rede hoort juist gemarkeerd te blijven
        #
        # Beide zien er hetzelfde uit. Hier niet aan beginnen dus.
        return None
    nieuw = f'{kopnoten}{aankondiging} <span class="{klasse}"><i>{rede}</i></span>{staart}'
    if kaal(nieuw) != kaal(html):
        return None                                  # er zou tekst verschuiven
    if nieuw.count('<span') != nieuw.count('</span>') or nieuw.count('<i>') != nieuw.count('</i>'):
        return None
    return nieuw


def main():
    p = argparse.ArgumentParser(description="Aankondiging uit het citaat halen.")
    p.add_argument("--proef", action="store_true", help="alleen tonen, niets opslaan")
    p.add_argument("--boek", help="beperk tot één boek")
    p.add_argument("--toon", type=int, default=8, help="hoeveel voorbeelden tonen")
    a = p.parse_args()

    data = os.path.join(WORTEL, "data")
    boeken = [a.boek] if a.boek else sorted(
        b for b in os.listdir(data)
        if os.path.isdir(os.path.join(data, b)) and os.path.exists(os.path.join(data, b, "1.json")))

    aantal = 0
    getoond = 0
    perboek = {}
    for b in boeken:
        map_ = os.path.join(data, b)
        for fn in sorted(os.listdir(map_)):
            if not fn.endswith(".json"):
                continue
            pad = os.path.join(map_, fn)
            ruw = open(pad, encoding="utf-8").read()
            mi = re.search(r'\n( +)"', ruw)
            inspring = len(mi.group(1)) if mi else 2
            d = json.loads(ruw)
            raak = False
            for v in d.get("verses", []):
                h = v.get("text2026_html")
                if not h:
                    continue
                nieuw = herzie(h)
                if nieuw is None:
                    continue
                aantal += 1
                perboek[b] = perboek.get(b, 0) + 1
                if getoond < a.toon:
                    getoond += 1
                    print(f'  {b} {d.get("number")}:{v["number"]}')
                    print(f'    was: {h[:118]}')
                    print(f'    nu : {nieuw[:118]}')
                v["text2026_html"] = nieuw
                raak = True
            if raak and not a.proef:
                open(pad, "w", encoding="utf-8", newline="").write(
                    json.dumps(d, ensure_ascii=False, indent=inspring) + "\n")

    print(f'\n{aantal} verzen{" (proef, niets opgeslagen)" if a.proef else " aangepast"}')
    for b, n in sorted(perboek.items(), key=lambda x: -x[1]):
        print(f'  {b:<18} {n}')
    return 0


if __name__ == "__main__":
    sys.exit(main())
