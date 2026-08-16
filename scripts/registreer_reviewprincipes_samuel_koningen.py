#!/usr/bin/env python3
"""Registreer de menselijke reviewcorrecties als begrensde principes.

Deze correcties zijn inhoudelijk door een lezer beoordeeld. Ze worden bewust
niet automatisch corpusbreed gemaakt: een gelijk woord kan elders een andere
betekenis of zinsfunctie hebben. Herhaalde paren delen wel één principe en alle
beoordeelde vindplaatsen worden in het bereik opgenomen.
"""

from __future__ import annotations

import json
import re
from collections import defaultdict
from difflib import SequenceMatcher
from pathlib import Path

from scripts.apply_google_review_1koningen import CORRECTIES as KONINGEN_CORRECTIES
from scripts.apply_google_review_2koningen import CORRECTIES as TWEE_KONINGEN_CORRECTIES
from scripts.apply_review_2samuel_20260813 import CORRECTIES as TWEE_SAMUEL_CORRECTIES


ROOT = Path(__file__).resolve().parents[1]
PRINCIPES_PAD = ROOT / "data" / "wijzigingsprincipes.json"


def _regels(boek: str, correcties: dict) -> list[tuple[str, int, int, str, str]]:
    return [
        (boek, hoofdstuk, vers, oud, nieuw)
        for (hoofdstuk, vers), paren in correcties.items()
        for oud, nieuw in paren
    ]


REVIEW_CORRECTIES = [
    ("1samuel", 17, 18, "bescheid", "een teken van leven"),
    *_regels("2samuel", TWEE_SAMUEL_CORRECTIES),
    *_regels("1koningen", KONINGEN_CORRECTIES),
    *_regels("2koningen", TWEE_KONINGEN_CORRECTIES),
]


def normaliseer(tekst: str) -> str:
    return re.sub(r"\s+", " ", tekst.strip().lower())


def _overeenkomst(oud: str, nieuw: str, verschil: dict) -> float:
    """Waardeer welk bestaand woordverschil bij een reviewcorrectie hoort."""
    oud_score = SequenceMatcher(None, normaliseer(oud), normaliseer(verschil.get("old", ""))).ratio()
    nieuw_score = SequenceMatcher(None, normaliseer(nieuw), normaliseer(verschil.get("new", ""))).ratio()
    return oud_score + nieuw_score


def koppel_reviewcorrecties(principe_ids: dict[tuple[str, str], str]) -> int:
    per_vers: dict[tuple[str, int, int], list[tuple[str, str]]] = defaultdict(list)
    for boek, hoofdstuk, vers, oud, nieuw in REVIEW_CORRECTIES:
        per_vers[(boek, hoofdstuk, vers)].append((oud, nieuw))

    per_hoofdstuk: dict[tuple[str, int], list[tuple[int, list[tuple[str, str]]]]] = defaultdict(list)
    for (boek, hoofdstuk, vers), paren in per_vers.items():
        per_hoofdstuk[(boek, hoofdstuk)].append((vers, paren))

    gekoppeld = 0
    for (boek, hoofdstuk), versregels in per_hoofdstuk.items():
        pad = ROOT / "data" / boek / f"{hoofdstuk}.json"
        hoofdstukdata = json.loads(pad.read_text(encoding="utf-8"))
        verzen = {item["number"]: item for item in hoofdstukdata["verses"]}
        gewijzigd = False
        for versnummer, paren in versregels:
            verschillen = verzen[versnummer].setdefault("phraseDiff", [])
            gebruikt: set[int] = set()
            for oud, nieuw in paren:
                principe = principe_ids[(normaliseer(oud), normaliseer(nieuw))]
                if principe in {item.get("principe") for item in verschillen}:
                    continue
                kandidaten = [
                    (index, _overeenkomst(oud, nieuw, verschil))
                    for index, verschil in enumerate(verschillen)
                    if index not in gebruikt and not verschil.get("principe")
                ]
                if not kandidaten:
                    verschillen.append({"old": oud, "new": nieuw, "principe": principe})
                    gebruikt.add(len(verschillen) - 1)
                else:
                    index, _ = max(kandidaten, key=lambda item: item[1])
                    verschillen[index]["principe"] = principe
                    gebruikt.add(index)
                gekoppeld += 1
                gewijzigd = True
        if gewijzigd:
            pad.write_text(
                json.dumps(hoofdstukdata, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
    return gekoppeld


def registreer() -> int:
    data = json.loads(PRINCIPES_PAD.read_text(encoding="utf-8"))
    bestaande_reviewprincipes = [
        item for item in data["principes"] if item.get("id", "").startswith("MR-SK-")
    ]
    principes = [
        item for item in data["principes"] if not item.get("id", "").startswith("MR-SK-")
    ]

    vindplaatsen: dict[tuple[str, str], dict[str, set[str]]] = defaultdict(
        lambda: defaultdict(set)
    )
    schrijfwijze: dict[tuple[str, str], tuple[str, str]] = {}
    for boek, hoofdstuk, vers, oud, nieuw in REVIEW_CORRECTIES:
        sleutel = (normaliseer(oud), normaliseer(nieuw))
        schrijfwijze.setdefault(sleutel, (oud, nieuw))
        vindplaatsen[sleutel][boek].add(f"{hoofdstuk}:{vers}")

    nieuwe_reviewprincipes = []
    for volgnummer, sleutel in enumerate(sorted(vindplaatsen), start=1):
        oud, nieuw = schrijfwijze[sleutel]
        bereik = {
            boek: sorted(plaatsen, key=lambda ref: tuple(map(int, ref.split(":"))))
            for boek, plaatsen in sorted(vindplaatsen[sleutel].items())
        }
        nieuwe_reviewprincipes.append(
            {
                "id": f"MR-SK-{volgnummer:03d}",
                "categorie": "Menselijke review",
                "oud": oud,
                "nieuw": nieuw,
                "toelichting": (
                    "Contextueel beoordeeld tijdens de menselijke review van "
                    "1–2 Samuel en 1 Koningen; niet zonder herbeoordeling buiten "
                    "het vermelde bereik toepassen."
                ),
                "regex": "",
                "voorbeeld": next(iter(bereik)) + " " + next(iter(next(iter(bereik.values())))),
                "bereik": bereik,
                "bron": "menselijke-review",
            }
        )
    principes.extend(nieuwe_reviewprincipes)
    data["principes"] = principes

    PRINCIPES_PAD.write_text(
        json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )
    principe_ids = {
        (normaliseer(item.get("oud", "")), normaliseer(item.get("nieuw", ""))): item["id"]
        for item in principes
    }
    # Wis oude, soms dubbele review-ID's. Daarna wordt iedere koppeling
    # deterministisch opnieuw opgebouwd vanuit de complete reviewmatrix.
    for pad in (ROOT / "data").glob("*/*.json"):
        try:
            hoofdstukdata = json.loads(pad.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue
        if not isinstance(hoofdstukdata, dict) or "verses" not in hoofdstukdata:
            continue
        gewijzigd = False
        for vers in hoofdstukdata["verses"]:
            if not isinstance(vers, dict):
                continue
            for verschil in vers.get("phraseDiff", []):
                principe = verschil.get("principe") if isinstance(verschil, dict) else None
                if isinstance(principe, str) and principe.startswith("MR-SK-"):
                    verschil.pop("principe", None)
                    gewijzigd = True
        if gewijzigd:
            pad.write_text(
                json.dumps(hoofdstukdata, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

    koppel_reviewcorrecties(principe_ids)
    oude_sleutels = {
        (normaliseer(item.get("oud", "")), normaliseer(item.get("nieuw", "")))
        for item in bestaande_reviewprincipes
    }
    return len(set(vindplaatsen) - oude_sleutels)


if __name__ == "__main__":
    print(f"{registreer()} ontbrekende reviewprincipes toegevoegd.")
