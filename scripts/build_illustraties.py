#!/usr/bin/env python3
"""Bouwt data/illustraties.json uit wat er in images/illustraties/ staat.

De drukversie kan bij het begin van een hoofdstuk een plaat op de onderste helft
van het blad zetten. Welke hoofdstukken er een hebben moet de browser weten
zonder honderden verzoeken te doen die op een 404 uitlopen, en een handgeschreven
lijst loopt achter zodra er een bestand bij komt. Daarom leest dit script de map
en schrijft het de lijst weg.

Bestandsnamen volgen images/chapters: {boek-id}_{hoofdstuk}.jpg, waarbij het
boek-id het id-veld uit data/books.json is.

Twee dingen worden er onderweg uitgefilterd. Een plaat die niet bij een tekst
hoort -- een boek dat niet bestaat, of een hoofdstuk voorbij het laatste --
wordt overgeslagen; de drukversie zou er anders een blad voor vrijmaken dat
nergens op slaat. En een plaat die al ergens anders staat wordt maar een keer
gebruikt: dezelfde afbeelding twee keer in een uitgave valt op als een fout,
ook al is het er geen. Wie wint is het eerste hoofdstuk in canonieke volgorde.

Gebruik:  python scripts/build_illustraties.py
"""
import collections
import hashlib
import json
import os
import re

WORTEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAP = os.path.join(WORTEL, "images", "illustraties")
UIT = os.path.join(WORTEL, "data", "illustraties.json")
NAAM = re.compile(r"^([a-z0-9]+)_(\d+)\.(jpg|jpeg|png|webp)$", re.I)


def hoofdstukken_per_boek():
    """boek-id -> aantal hoofdstukken, uit data/books.json."""
    with open(os.path.join(WORTEL, "data", "books.json"), encoding="utf-8") as fh:
        boeken = json.load(fh)
    if isinstance(boeken, dict):
        boeken = boeken.get("books") or []
    uit = {}
    for b in boeken:
        aantal = b.get("totalChapters") or len(b.get("chaptersIncluded") or [])
        uit[b.get("id")] = aantal or 0
    return uit


def volgorde_van(boeken, boek):
    """Positie in de canonieke volgorde; onbekende boeken achteraan."""
    try:
        return list(boeken).index(boek)
    except ValueError:
        return len(boeken)


def main():
    boeken = hoofdstukken_per_boek()
    platen = collections.defaultdict(dict)
    gevonden = []
    if os.path.isdir(MAP):
        for naam in sorted(os.listdir(MAP)):
            m = NAAM.match(naam)
            if not m:
                continue
            boek, hoofdstuk = m.group(1), int(m.group(2))
            if boek not in boeken:
                print("overgeslagen, onbekend boek: " + naam)
                continue
            if boeken[boek] and hoofdstuk > boeken[boek]:
                print("overgeslagen, %s heeft geen hoofdstuk %d: %s"
                      % (boek, hoofdstuk, naam))
                continue
            with open(os.path.join(MAP, naam), "rb") as fh:
                vinger = hashlib.sha1(fh.read()).hexdigest()
            gevonden.append((volgorde_van(boeken, boek), hoofdstuk, boek, naam,
                             vinger))

    gezien = {}
    for _, hoofdstuk, boek, naam, vinger in sorted(gevonden):
        eerder = gezien.get(vinger)
        if eerder:
            print("overgeslagen, zelfde plaat als %s: %s" % (eerder, naam))
            continue
        gezien[vinger] = naam
        # Per hoofdstuk de hele bestandsnaam, niet alleen het nummer: de map mag
        # jpg en webp door elkaar bevatten.
        platen[boek][str(hoofdstuk)] = naam

    uit = {
        "bron": "Jan van 't Hoff",
        "map": "images/illustraties/",
        "platen": {boek: dict(sorted(h.items(), key=lambda p: int(p[0])))
                   for boek, h in sorted(platen.items())},
    }
    tekst = json.dumps(uit, ensure_ascii=False, indent=1)
    with open(UIT, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(tekst + "\n")
    print("illustraties.json: %d boeken, %d platen"
          % (len(uit["platen"]), sum(len(h) for h in uit["platen"].values())))


if __name__ == "__main__":
    main()
