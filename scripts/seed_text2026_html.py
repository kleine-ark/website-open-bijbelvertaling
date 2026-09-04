#!/usr/bin/env python3
"""Geeft de Ethiopische boeken het veld text2026_html dat ze nooit gekregen hebben.

De zes Ethiopische boeken -- Henoch, Jubileeen, 1 tot en met 3 Meqabyan en
4 Baruch -- zijn nooit door de html-pijplijn gegaan. Van hun 3897 verzen hebben
er vijf een `text2026_html`, en die vijf zijn leeg. Voor de lezer valt dat niet
op: `js/lees.js` en `js/app.js` vallen terug op `text2026`. Maar alles wat opmaak
áán de tekst hangt -- citaatopmaak, notenmarkeringen, Strong-koppelingen --
schrijft in `text2026_html`, en dat veld is er niet om in te schrijven.

Het gevaar van half seeden. Zou het veld alleen worden aangemaakt op de verzen
die opmaak krijgen, dan staan er in hetzelfde boek verzen met en zonder. Een
latere woordsweep die alleen `text2026` bijwerkt -- en die zijn er geweest --
verandert dan wél de tekst maar niet wat de site toont, precies op die verzen.
Vandaar dat het veld voor alle verzen wordt aangemaakt, zodat deze boeken zich
gedragen als alle andere.

Het veld komt direct na `text2026` te staan, op dezelfde plaats als in de
overige boeken, en krijgt letterlijk dezelfde tekst. Er wordt niets aan de
inhoud veranderd; verzen die het veld al hebben blijven onaangeroerd.

    python scripts/seed_text2026_html.py --proef
    python scripts/seed_text2026_html.py
    python scripts/seed_text2026_html.py --boek henoch --wortel <map>
"""
import argparse
import glob
import io
import json
import os
import re
import sys

WORTEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ETHIOPISCH = ("henoch", "jubileeen", "1meqabyan", "2meqabyan", "3meqabyan", "4baruch")


def schrijf(pad, data, ruw):
    nl = "\r\n" if "\r\n" in ruw else "\n"
    m = re.search(r'\n( +)"', ruw.replace("\r\n", "\n"))
    tekst = json.dumps(data, ensure_ascii=False, indent=len(m.group(1)) if m else 1)
    if ruw.endswith("\n"):
        tekst += "\n"
    io.open(pad, "w", encoding="utf-8", newline="").write(tekst.replace("\n", nl))


def met_html_na_text2026(vers):
    """Nieuw versobject met text2026_html direct achter text2026."""
    uit = {}
    for sleutel, waarde in vers.items():
        uit[sleutel] = waarde
        if sleutel == "text2026" and "text2026_html" not in vers:
            uit["text2026_html"] = waarde
    if "text2026_html" not in uit:          # geen text2026 om achter te hangen
        uit["text2026_html"] = vers.get("text2026", "")
    return uit


def main():
    p = argparse.ArgumentParser(description="text2026_html aanmaken waar het ontbreekt.")
    p.add_argument("--boek", action="append", help="beperk tot deze boeken")
    p.add_argument("--proef", action="store_true", help="alleen tellen, niets opslaan")
    p.add_argument("--wortel", help="andere map met data/ dan de repository zelf")
    args = p.parse_args()

    wortel = args.wortel or WORTEL
    boeken = args.boek or list(ETHIOPISCH)

    tot_nieuw = tot_leeg = tot_al = 0
    for boek in boeken:
        map_ = os.path.join(wortel, "data", boek)
        if not os.path.isdir(map_):
            print("  ontbreekt: %s" % map_)
            continue
        nieuw = leeg = al = 0
        for pad in sorted(glob.glob(os.path.join(map_, "*.json")),
                          key=lambda q: int(os.path.basename(q)[:-5])
                          if os.path.basename(q)[:-5].isdigit() else 0):
            if not os.path.basename(pad)[:-5].isdigit():
                continue
            ruw = io.open(pad, encoding="utf-8", newline="").read()
            data = json.loads(ruw)
            raak = False
            verzen = []
            for v in data.get("verses", []):
                if "text2026_html" not in v:
                    verzen.append(met_html_na_text2026(v))
                    nieuw += 1
                    raak = True
                elif not v["text2026_html"]:
                    v["text2026_html"] = v.get("text2026", "")
                    verzen.append(v)
                    leeg += 1
                    raak = True
                else:
                    verzen.append(v)
                    al += 1
            if raak and not args.proef:
                data["verses"] = verzen
                schrijf(pad, data, ruw)
        print("%-12s %5d aangemaakt, %3d lege gevuld, %5d hadden het al"
              % (boek, nieuw, leeg, al))
        tot_nieuw += nieuw
        tot_leeg += leeg
        tot_al += al

    print("\nsamen %d verzen een text2026_html gegeven%s"
          % (tot_nieuw + tot_leeg, "  (proef, niets opgeslagen)" if args.proef else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
