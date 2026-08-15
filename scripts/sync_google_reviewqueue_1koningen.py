#!/usr/bin/env python3
"""Leg niet-automatische Google-opmerkingen bij 1 Koningen lokaal vast.

De gepubliceerde sheet blijft ongewijzigd. Alleen verwijzing, suggestie en
lokale afhandeling worden bewaard; inzenders worden bewust niet overgenomen.
"""

from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path

try:  # uitvoer als script
    from apply_google_review_1koningen import CORRECTIES
    from apply_citations_1koningen import RANGES as CITATIE_RANGES
    from lees_opmerkingen import csv_adres, haal_op, kolom, zelfde_boek
except ModuleNotFoundError:  # import vanuit tests
    from scripts.apply_google_review_1koningen import CORRECTIES
    from scripts.apply_citations_1koningen import RANGES as CITATIE_RANGES
    from scripts.lees_opmerkingen import csv_adres, haal_op, kolom, zelfde_boek


ROOT = Path(__file__).resolve().parents[1]
UITVOER = ROOT / "data" / "google-opmerkingen-1koningen-reviewqueue.json"


def sleutel(tekst: str) -> str:
    return re.sub(r"\s+", " ", (tekst or "").strip().lower())


def referenties(ref: str):
    """Lees alle verzen uit notaties als 3:11,20 en 14:12-16."""
    match = re.match(r"1\s*koningen\s+(\d+)\s*:\s*([\d,\s-]+)", ref or "", re.I)
    if not match:
        return []
    hoofdstuk = int(match.group(1))
    verzen = []
    for deel in match.group(2).split(","):
        deel = deel.strip()
        if not deel:
            continue
        if "-" in deel:
            begin, einde = (int(getal.strip()) for getal in deel.split("-", 1))
            verzen.extend((hoofdstuk, vers) for vers in range(begin, einde + 1))
        else:
            verzen.append((hoofdstuk, int(deel)))
    return verzen


AFGEDEKTE_TAGS = {
    (3, 3): "dubbelhartigheid",
    (7, 14): "vakmanschap",
    (8, 32): "zaaien-en-oogsten",
    (11, 14): "straf-in-dit-leven",
    (11, 41): "verloren-bijbelse-bronnen",
    (19, 8): "horeb",
    (22, 3): "valse-profetie",
    (22, 19): "boze-geesten",
    (22, 20): "boze-geesten",
    (22, 21): "boze-geesten",
    (22, 22): "boze-geesten",
    (22, 23): "boze-geesten",
    (22, 24): "boze-geesten",
}

AFGEDEKTE_CITATEN = {(5, 2), *CITATIE_RANGES.keys()}


def classificeer(ref: str, suggestie: str):
    """Classificeer zonder inhoudelijke suggesties als tekstwijziging te doen."""
    laag = sleutel(suggestie)
    keys = referenties(ref)
    correcties = [correctie for key in keys for correctie in CORRECTIES.get(key, [])]

    if any(term in laag for term in ("cit", "cot", "cita")):
        if any(key in AFGEDEKTE_CITATEN for key in keys):
            return "citatieopmaak", "afgedekt", "De sprekers en de begrenzing van het citaat zijn gecontroleerd."
        return "citatieopmaak", "open", "Vraagt nog controle in de universele citeerweergave."
    if "lage getallen" in laag:
        return "getalweergave", "afgedekt", "Dit valt onder de globale optie voor getalweergave."
    if any(term in laag for term in ("unit", "unut", "eenhed", "ellen", "talent", "sikkel", "kor", "bath")):
        return "eenheden", "afgedekt", "De eenheid is gekoppeld aan de globale maten- en gewichtenoptie."
    if any(key in AFGEDEKTE_TAGS for key in keys):
        return "tag_of_onderwerp", "afgedekt", "De onderwerp-tag is in de versgegevens opgenomen."
    if "tag" in laag or "pagina" in laag or "geograf" in laag:
        return "tag_of_onderwerp", "open", "Als inhoudelijke koppeling bewaard voor de betreffende onderwerp- of kaartgegevens."
    if correcties:
        return "tekst_eenduidig", "verwerkt", "In de leestekst verwerkt en met een regressietest afgedekt."
    if any(term in laag for term in ("gouds", "inwoneren", "meels", "overtoog")):
        return "tekst_eenduidig", "verwerkt", "Corpusbreed als wijzigingsprincipe verwerkt."
    return "inhoudelijk_review", "open", "Vraagt redactionele beoordeling; niet automatisch als tekstwijziging toegepast."


def bouw_queue(rijen):
    items = []
    gezien = set()
    for rij in rijen:
        ref = kolom(rij, "Vers")
        if not zelfde_boek(ref, "1koningen"):
            continue
        suggestie = kolom(rij, "Suggestie")
        uniek = (sleutel(ref), sleutel(suggestie))
        if uniek in gezien:
            continue
        gezien.add(uniek)
        categorie, status, resultaat = classificeer(ref, suggestie)
        items.append({
            "ref": re.sub(r"\s+", " ", ref).strip(),
            "suggestie": re.sub(r"\s+", " ", suggestie).strip(),
            "categorie": categorie,
            "status": status,
            "resultaat": resultaat,
        })
    return items


def main():
    adres = csv_adres()
    if not adres:
        raise SystemExit("Geen adres van de opmerkingen-sheet geconfigureerd.")
    items = bouw_queue(haal_op(adres))
    payload = {
        "source": f"Google-opmerkingen, opgehaald {date.today().isoformat()}",
        "book": "1 Koningen",
        "items": items,
    }
    UITVOER.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{len(items)} unieke opmerkingen in {UITVOER.name} vastgelegd.")


if __name__ == "__main__":
    main()
