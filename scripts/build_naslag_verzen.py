#!/usr/bin/env python3
"""Bouwt data/naslag-verzen.json — de index van vers naar naslagingang.

De leesoptie "Tekstverbanden" beloofde onderwerpen, materialen, dieren, planten
en geografische locaties te markeren, maar js/tags.js las alleen data/tags.json:
de drieënvijftig thematische onderwerpen. De naslagverzamelingen werden nooit
geraadpleegd, zodat een lezer van Hooglied 3:5 geen enkel teken kreeg dat de ree
en de hinde daar een eigen wiki-ingang hebben — terwijl die ingangen dat vers
zelf wél noemen.

Rechtstreeks uit die verzamelingen lezen kan niet: samen zijn ze ruim twee
megabyte, want ze bevatten per vindplaats de tekstvorm, de zekerheid en de
reviewstatus. Voor het zetten van een stipje naast een versnummer is daarvan
alleen nodig wélke ingang het is. Deze index houdt dat over: ongeveer
driehonderd kilobyte voor vijfenvijftighonderd verzen.

De vorm is bewust kort. Elk vers wijst naar paren [categorie, id]; de namen
staan één keer apart, en per categorie staan het label, de kleur van het stipje
en de pagina waar de ingang te vinden is.

Gebruik:  python scripts/build_naslag_verzen.py
"""
import collections
import json
import os

WORTEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(WORTEL, "data")
UIT = os.path.join(DATA, "naslag-verzen.json")

# categorie, bronbestand, label, kleur van het stipje, pagina
BRONNEN = [
    ("dieren", "naslag-dieren.json", "Dieren", "#a0522d", "dieren.html"),
    ("bomen-planten", "naslag-bomen-planten.json", "Bomen en planten", "#4a7c3f",
     "bomen-planten.html"),
    ("materialen", "naslag-materialen.json", "Materialen", "#7d6b57", "materialen.html"),
    ("muziekinstrumenten", "naslag-muziekinstrumenten.json", "Muziekinstrumenten", "#8a6aa8",
     "muziekinstrumenten.html"),
    ("voedsel", "naslag-voedsel.json", "Voedsel", "#c07a2a", "voedsel.html"),
    ("afgoden", "naslag-afgoden.json", "Afgoden en machten", "#8a3a3a", "afgoden.html"),
]


def lees(naam):
    with open(os.path.join(DATA, naam), encoding="utf-8") as fh:
        return json.load(fh)


def main():
    verzen = collections.defaultdict(list)
    namen = {}
    per_categorie = {}
    for categorie, bestand, label, kleur, pagina in BRONNEN:
        pad = os.path.join(DATA, bestand)
        if not os.path.exists(pad):
            print("overgeslagen, ontbreekt: " + bestand)
            continue
        bron = lees(bestand)
        items = bron.get("items") or []
        per_categorie[categorie] = {"label": label, "kleur": kleur, "pagina": pagina}
        for item in items:
            item_id = item.get("id")
            naam = item.get("naam")
            if not item_id or not naam:
                continue
            namen["%s/%s" % (categorie, item_id)] = naam
            for ref in item.get("verzen") or []:
                if isinstance(ref, str) and ref.strip():
                    verzen[ref.strip()].append([categorie, item_id])
        print("%-22s %3d ingangen" % (categorie, len(items)))

    uit = {
        "categorieen": per_categorie,
        "namen": namen,
        "verzen": {ref: paren for ref, paren in sorted(verzen.items())},
    }
    # Kort wegschrijven: dit bestand wordt door de lezer opgehaald, niet gelezen
    # door mensen.
    tekst = json.dumps(uit, ensure_ascii=False, separators=(",", ":"))
    with open(UIT, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(tekst + "\n")
    print("\nnaslag-verzen.json: %d verzen, %d ingangen, %.0f KB"
          % (len(verzen), len(namen), len(tekst.encode("utf-8")) / 1024))


if __name__ == "__main__":
    main()
