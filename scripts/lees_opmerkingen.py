#!/usr/bin/env python3
"""Haalt de opmerkingen van lezers op uit de gepubliceerde Google Sheet.

De sheet wordt gevuld door een Google Formulier; zie
docs/opmerkingen-in-google-sheet.md. Publiceren als CSV maakt hem leesbaar
zonder inloggen of sleutel, dus dit script heeft geen geheimen nodig en kan
gewoon in de repo staan.

Gebruik:
    python scripts/lees_opmerkingen.py                 alle nieuwe opmerkingen
    python scripts/lees_opmerkingen.py --alles         ook de afgehandelde
    python scripts/lees_opmerkingen.py --boek genesis  alleen dat boek
    python scripts/lees_opmerkingen.py --json          machineleesbaar

Het adres komt uit de omgevingsvariabele OV_OPMERKINGEN_CSV, of anders uit
data/opmerkingen-bron.json. Dat laatste bestand staat in .gitignore, zodat
het adres van de sheet niet in de geschiedenis belandt.
"""
import argparse
import csv
import io
import json
import os
import sys
import unicodedata
import urllib.request

WORTEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BRON_BESTAND = os.path.join(WORTEL, "data", "opmerkingen-bron.json")


def csv_adres():
    adres = os.environ.get("OV_OPMERKINGEN_CSV")
    if adres:
        return adres
    try:
        with open(BRON_BESTAND, encoding="utf-8") as fh:
            return json.load(fh).get("csv")
    except FileNotFoundError:
        return None


def haal_op(adres):
    with urllib.request.urlopen(adres, timeout=30) as r:
        ruw = r.read().decode("utf-8-sig")
    return list(csv.DictReader(io.StringIO(ruw)))


def kolom(rij, *namen):
    """De sheet-kolommen heten Nederlands; wees mild in het herkennen."""
    for n in namen:
        for k, v in rij.items():
            if k and k.strip().lower() == n.lower():
                return (v or "").strip()
    return ""


def _sleutel(tekst):
    """Vergelijk boeknamen onafhankelijk van spaties en diakritische tekens."""
    zonder_acc = "".join(
        teken for teken in unicodedata.normalize("NFD", tekst.lower())
        if unicodedata.category(teken) != "Mn"
    )
    return "".join(teken for teken in zonder_acc if teken.isalnum())


def zelfde_boek(vers, boek):
    """Geeft terug of een sheet-verwijzing met het gevraagde boek begint."""
    return _sleutel(vers).startswith(_sleutel(boek))


def main():
    p = argparse.ArgumentParser(description="Opmerkingen van lezers ophalen.")
    p.add_argument("--alles", action="store_true", help="ook al afgehandelde meldingen")
    p.add_argument("--boek", help="alleen meldingen over dit boek, bijv. genesis")
    p.add_argument("--json", action="store_true", help="uitvoer als JSON")
    a = p.parse_args()

    adres = csv_adres()
    if not adres:
        print("Geen adres van de sheet bekend.\n", file=sys.stderr)
        print("Zet OV_OPMERKINGEN_CSV in je omgeving, of maak "
              f"{os.path.relpath(BRON_BESTAND, WORTEL)} met:\n"
              '  {"csv": "https://docs.google.com/…/pub?output=csv"}\n',
              file=sys.stderr)
        print("Instellen staat beschreven in docs/opmerkingen-in-google-sheet.md",
              file=sys.stderr)
        return 1

    try:
        rijen = haal_op(adres)
    except Exception as e:
        print(f"Ophalen mislukt: {e}", file=sys.stderr)
        print("Staat de sheet gepubliceerd als CSV?", file=sys.stderr)
        return 1

    uit = []
    for r in rijen:
        status = kolom(r, "Status") or "nieuw"
        if not a.alles and status.lower() not in ("", "nieuw"):
            continue
        vers = kolom(r, "Vers")
        if a.boek and not zelfde_boek(vers, a.boek):
            continue
        uit.append({
            "ontvangen": kolom(r, "Ontvangen"),
            "vers": vers,
            "selectie": kolom(r, "Geselecteerde tekst"),
            "suggestie": kolom(r, "Suggestie"),
            "van": kolom(r, "Van"),
            "status": status,
        })

    if a.json:
        print(json.dumps(uit, ensure_ascii=False, indent=1))
        return 0

    if not uit:
        print("Geen openstaande opmerkingen." if not a.alles else "Geen opmerkingen.")
        return 0

    print(f"{len(uit)} opmerking(en)\n")
    for o in uit:
        print(f"  {o['vers'] or '(geen vers)'}   [{o['status']}]   {o['ontvangen']}")
        if o["selectie"]:
            print(f"     tekst     : {o['selectie'][:110]}")
        print(f"     suggestie : {o['suggestie'][:110]}")
        if o["van"] and o["van"] != "anoniem":
            print(f"     van       : {o['van']}")
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
