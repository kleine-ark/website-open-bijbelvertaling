#!/usr/bin/env python3
"""Zet de citaatopmaak van een boek klaar om na te lezen.

Nalezen gebeurt per hoofdstuk en op de opmaak zoals die er nu staat, niet op de
kale tekst: de vraag is immers of de bestaande spans op de goede plaats staan en
de goede spreker noemen, en dat is aan de kale tekst niet te zien.

Elk vers komt op één regel, met de notenmarkeringen ingekort tot [n] zodat ze de
regel niet onleesbaar maken -- ze worden bij het toepassen letterlijk terug-
geëist, dus wie een voorstel doet moet ze wél overnemen. Vandaar --volledig voor
wie de echte tekst nodig heeft.

    python scripts/citaat_werkblad.py jeremia 1 3        hoofdstuk 1 tot en met 3
    python scripts/citaat_werkblad.py henoch 1           één hoofdstuk
    python scripts/citaat_werkblad.py tobit              het hele boek
"""
import argparse
import json
import os
import re
import sys

WORTEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def hoofdstukken(boek):
    p = os.path.join(WORTEL, "data", boek)
    return sorted(int(f[:-5]) for f in os.listdir(p)
                  if f.endswith(".json") and f[:-5].isdigit())


def main():
    p = argparse.ArgumentParser(description="Citaatopmaak klaarzetten om na te lezen.")
    p.add_argument("boek")
    p.add_argument("van", nargs="?", type=int)
    p.add_argument("tot", nargs="?", type=int)
    p.add_argument("--volledig", action="store_true",
                   help="notenmarkeringen voluit in plaats van [n]")
    p.add_argument("--wortel", help="andere map met data/ dan de repository zelf; "
                                    "voor werken op een uitgepakte kopie van origin/main")
    args = p.parse_args()

    global WORTEL
    if args.wortel:
        WORTEL = args.wortel

    alle = hoofdstukken(args.boek)
    van = args.van or alle[0]
    tot = args.tot or args.van or alle[-1]

    for c in [x for x in alle if van <= x <= tot]:
        pad = os.path.join(WORTEL, "data", args.boek, "%d.json" % c)
        data = json.load(open(pad, encoding="utf-8"))
        print("=== %s %d ===" % (args.boek, c))
        for v in data.get("verses", []):
            html = v.get("text2026_html") or v.get("text2026") or ""
            if not args.volledig:
                html = re.sub(r'<sup class="note-marker" data-note="(\d+)">\d+</sup>',
                              r'[\1]', html)
            print("%d:%s | %s" % (c, v["number"], html))
        print()


if __name__ == "__main__":
    sys.exit(main())
