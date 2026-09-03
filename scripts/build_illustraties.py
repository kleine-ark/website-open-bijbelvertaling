#!/usr/bin/env python3
"""Bouwt data/illustraties.json uit wat er in images/illustraties/ staat.

De drukversie kan bij het begin van een hoofdstuk een plaat op de onderste helft
van het blad zetten. Welke hoofdstukken er een hebben moet de browser weten
zonder honderden verzoeken te doen die op een 404 uitlopen, en een handgeschreven
lijst loopt achter zodra er een bestand bij komt. Daarom leest dit script de map
en schrijft het de lijst weg.

Bestandsnamen volgen images/chapters: {boek-id}_{hoofdstuk}.jpg, waarbij het
boek-id het id-veld uit data/books.json is.

Gebruik:  python scripts/build_illustraties.py
"""
import collections
import json
import os
import re

WORTEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAP = os.path.join(WORTEL, "images", "illustraties")
UIT = os.path.join(WORTEL, "data", "illustraties.json")
NAAM = re.compile(r"^([a-z0-9]+)_(\d+)\.(jpg|jpeg|png|webp)$", re.I)


def main():
    platen = collections.defaultdict(list)
    extensies = collections.Counter()
    if os.path.isdir(MAP):
        for naam in sorted(os.listdir(MAP)):
            m = NAAM.match(naam)
            if not m:
                continue
            platen[m.group(1)].append(int(m.group(2)))
            extensies["." + m.group(3).lower()] += 1

    uit = {
        "bron": "Jan van 't Hoff",
        "map": "images/illustraties/",
        "extensie": extensies.most_common(1)[0][0] if extensies else ".jpg",
        "platen": {boek: sorted(set(h)) for boek, h in sorted(platen.items())},
    }
    tekst = json.dumps(uit, ensure_ascii=False, indent=1)
    with open(UIT, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(tekst + "\n")
    print("illustraties.json: %d boeken, %d platen"
          % (len(uit["platen"]), sum(len(h) for h in uit["platen"].values())))


if __name__ == "__main__":
    main()
