#!/usr/bin/env python3
"""Verwerk uitsluitend eenduidige Google-opmerkingen voor 1 Koningen."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from sweep_principe import kaal, lees, nieuwe_diff, schrijf  # noqa: E402
from synchroniseer_opmaak import bijtrekken  # noqa: E402


CORRECTIES = {
    (1, 9): [("noodde", "nodigde")],
    (1, 10): [("noodde hij niet", "nodigde hij niet uit")],
    (1, 49): [("ieder zijns weegs", "ieder zijn eigen weg")],
    (3, 9): [("Uw zwaar volk", "Uw machtig volk")],
    (3, 20): [("haar doden zoon", "haar dode zoon")],
    (3, 26): [("haar binnenste ontstak over haar zoon", "haar moederhart brandde van medelijden om haar zoon")],
    (4, 23): [("uitgenomen", "uitgezonderd")],
    (5, 4): [("bejegening van kwaad", "bedreiging")],
    (5, 10): [("cederenhout", "cederhout")],
    (5, 13): [
        (
            "deed een uitschot opkomen uit geheel Isra\u00ebl; en het uitschot was dertig duizend man",
            "legde heel Isra\u00ebl een herendienst op; de herendienst bestond uit dertig duizend man",
        )
    ],
    (5, 14): [("Adoniram was over dit uitschot", "Adoniram had de leiding over deze herendienst")],
    (6, 4): [("vensteren", "vensters")],
    (6, 5): [("zijkameren", "zijkamers")],
    (6, 11): [("gebeurde het woord", "kwam het woord")],
    (6, 21): [("overtoog", "overtrok")],
    (7, 17): [("nettenwerk", "vlechtwerk")],
    (7, 28): [("werk der stelling", "werk van het onderstel")],
    (7, 30): [("stelling", "onderstel"), ("schouders", "steunen")],
    (7, 32): [("aan de stelling", "aan het onderstel")],
    (7, 34): [
        ("ener stelling", "van een onderstel"),
        ("uit de stelling", "uit het onderstel"),
        ("schouders", "steunen"),
    ],
    (7, 35): [
        ("ener stelling", "van een onderstel"),
        ("der stelling", "van het onderstel"),
    ],
    (7, 37): [("stellingen", "onderstellen")],
    (7, 38): [("op elke stelling", "op elk onderstel"), ("stellingen", "onderstellen")],
    (7, 39): [("stellingen", "onderstellen")],
    (7, 43): [("stellingen", "onderstellen")],
    (7, 47): [("zeer grote menigte", "zeer grote hoeveelheid")],
    (7, 50): [("gaffelen", "messen"), ("herren", "scharnieren")],
    (8, 5): [("hele vergadering", "hele gemeenschap")],
    (8, 19): [("uit uw lendenen", "uit uw lichaam")],
    (9, 15): [
        (
            "Dit is nu de oorzaak van het uitschot, dat de koning Salomo deed opkomen, om",
            "Dit is de reden waarom koning Salomo herendienst oplegde: om",
        )
    ],
    (9, 21): [
        ("heeft Salomo gebracht op slaafsen uitschot", "heeft Salomo tot slavenarbeid verplicht")
    ],
}


def pas_tekst_aan(vers, vervangingen, referentie):
    """Pas exacte vervangingen toe en behoud de zichtbare HTML-opmaak."""
    nieuw = vers["text2026"]
    for oud, vervang in vervangingen:
        if oud not in nieuw:
            if vervang in nieuw:
                continue
            raise ValueError(f"{referentie}: niet gevonden: {oud!r}")
        nieuw = nieuw.replace(oud, vervang)

    if nieuw == vers["text2026"]:
        return False
    html = bijtrekken(vers["text2026_html"], nieuw)
    if html is None or kaal(html) != kaal(nieuw):
        raise ValueError(f"{referentie}: HTML kon niet veilig worden bijgewerkt")
    vers["text2026"] = nieuw
    vers["text2026_html"] = html
    vers["phraseDiff"] = nieuwe_diff(
        kaal(vers["textSV1888"]),
        kaal(nieuw),
        vers.get("phraseDiff", []),
        None,
        referentie.lower(),
    )
    return True


def voeg_dubbelhartigheid_toe(data):
    """Voeg de eerste expliciete verwijzing voor het onderwerp toe."""
    tags = data.setdefault("tags", [])
    tag = next((item for item in tags if item.get("id") == "dubbelhartigheid"), None)
    if tag is None:
        tag = {
            "id": "dubbelhartigheid",
            "naam": "Dubbelhartigheid",
            "beschrijving": "Een verdeelde toewijding aan JAHWEH en andere wegen.",
            "kleur": "#8b5e3c",
            "verzen": [],
        }
        tags.append(tag)
    refs = {item.get("ref") for item in tag["verzen"]}
    if "1koningen 3:3" not in refs:
        tag["verzen"].append({"ref": "1koningen 3:3", "rang": 1})
    return tag


def voeg_zaaien_en_oogsten_toe(data):
    """Koppel Salomo's gebed over rechtvaardig vergelding aan het onderwerp."""
    tag = next(
        (item for item in data.get("tags", []) if item.get("id") == "zaaien-en-oogsten"),
        None,
    )
    if tag is None:
        raise ValueError("Onderwerp 'zaaien-en-oogsten' ontbreekt in data/tags.json")
    if "1koningen 8:32" not in {item.get("ref") for item in tag["verzen"]}:
        tag["verzen"].append({"ref": "1koningen 8:32", "rang": 1})
    return tag


def pas_2kronieken_8_8_aan():
    """Houd de parallel bij Salomo's herendienst in 2 Kronieken gelijk."""
    pad = ROOT / "data" / "2kronieken" / "8.json"
    data, vorm = lees(str(pad))
    vers = next(item for item in data["verses"] if item["number"] == 8)
    gewijzigd = pas_tekst_aan(
        vers,
        [("bracht Salomo op uitschot", "verplichtte Salomo tot slavenarbeid")],
        "2 Kronieken 8:8",
    )
    if gewijzigd:
        schrijf(str(pad), data, vorm)
    return gewijzigd


def main():
    per_hoofdstuk = {}
    for (hoofdstuk, nummer), vervangingen in CORRECTIES.items():
        per_hoofdstuk.setdefault(hoofdstuk, []).append((nummer, vervangingen))

    geraakt = 0
    for hoofdstuk, verscorrecties in per_hoofdstuk.items():
        pad = ROOT / "data" / "1koningen" / f"{hoofdstuk}.json"
        data, vorm = lees(str(pad))
        verzen = {item["number"]: item for item in data["verses"]}
        gewijzigd = False
        for nummer, vervangingen in verscorrecties:
            if pas_tekst_aan(verzen[nummer], vervangingen, f"1 Koningen {hoofdstuk}:{nummer}"):
                geraakt += 1
                gewijzigd = True
        if gewijzigd:
            schrijf(str(pad), data, vorm)
    if pas_2kronieken_8_8_aan():
        geraakt += 1

    tag_pad = ROOT / "data" / "tags.json"
    tags, vorm = lees(str(tag_pad))
    voeg_dubbelhartigheid_toe(tags)
    voeg_zaaien_en_oogsten_toe(tags)
    schrijf(str(tag_pad), tags, vorm)
    print(f"{geraakt} verzen in 1 Koningen bijgewerkt.")


if __name__ == "__main__":
    main()
