#!/usr/bin/env python3
"""Hoofdletter voor God in de gebeden van de apocriefe boeken.

In de canonieke boeken schreef de Statenvertaling "Gij" en "Uw" met een
hoofdletter waar God wordt aangesproken; in de apocriefen niet. Principe A1
(gij -> u / U) nam die kleine letter over, zodat Ezra in 4 Ezra 3:4 bidt: "O
heersende Heere, u hebt van de beginne gesproken". Een lezersmelding vroeg dit
in alle apocriefe boeken na te lopen.

Of "u" God is, volgt uit de zin en niet uit het woord. In het gebed van Ezra
(3 Ezra 8) staat midden in de aanspraak tot God een aanhaling van Gods gebod
aan Israël, waar "u" het volk is; in Tobit 13 spreekt Tobit Jeruzalem aan.
Daarom is hieronder per gebed uitgeschreven welke verzen tot God gericht zijn.
Wat niet in de lijst staat, blijft zoals het was. Dat geldt bewust ook voor de
gesprekken in 4 Ezra (4:22, 5:41, 5:56, 6:11, 7:17, 8:63, 10:37), waar Ezra
"Heere" zegt tegen de engel die hem antwoordt en de aangesprokene niet zeker is.

Alleen boeken die nog niet definitief zijn. Judith, 3 Makkabeeën, het Gebed
van Azaria en de gebeden in 4 Ezra 6 en 8:6-23 hadden de hoofdletters al.

Draaien vanuit de repo-root:  python scripts/apply_hoofdletters_god_apocriefen.py
"""

from __future__ import annotations

import io
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from review_hulp import verwerk_correcties  # noqa: E402
from sweep_principe import lees, schrijf  # noqa: E402


def reeks(*delen):
    uit = []
    for deel in delen:
        if isinstance(deel, tuple):
            uit.extend(range(deel[0], deel[1] + 1))
        else:
            uit.append(deel)
    return uit


GEBEDEN = {
    ("3ezra", "3 Ezra"): {
        # Ezra's schuldbelijdenis; 8:84-86 citeren Gods gebod aan Israël.
        8: reeks(75, 79, 83, (88, 91)),
    },
    ("4ezra", "4 Ezra"): {
        3: reeks((4, 36)),
        5: reeks((23, 30)),
        8: reeks((24, 36)),
        # 9:31 citeert Gods woorden aan Israël.
        9: reeks(29, 32),
        12: reeks(7, 8, 9),
    },
    ("tobit", "Tobit"): {
        # 3:11 zijn de woorden van de dienstmaagd tegen Sara.
        3: reeks((2, 6), 22),
    },
    ("estherapocrief", "Esther (apocrief)"): {
        13: reeks((8, 18)),
        14: reeks((3, 19)),
    },
    ("jezussirach", "Jezus Sirach"): {
        23: reeks((1, 6)),
        36: reeks((1, 19)),
        51: reeks((10, 16)),
    },
    ("boekderwijsheid", "Wijsheid"): {
        9: reeks((1, 18)),
        10: reeks(20),
        12: reeks((1, 27)),
        14: reeks(3),
        15: reeks((1, 3)),
        16: reeks((12, 29)),
        17: reeks(1),
        18: reeks((1, 8)),
        19: reeks((5, 9), 21, 22),
    },
    ("belenddedraak", "Bel en de draak"): {
        1: reeks(37),
    },
    ("2makkabeeen", "2 Makkabeeën"): {
        1: reeks((24, 29)),
    },
}

WOORDEN = [
    (re.compile(r"(?<![\wÀ-ÿ'])uzelf(?![\wÀ-ÿ])"), "Uzelf"),
    (re.compile(r"(?<![\wÀ-ÿ'])uwen(?![\wÀ-ÿ])"), "Uwen"),
    (re.compile(r"(?<![\wÀ-ÿ'])uwe(?![\wÀ-ÿ])"), "Uwe"),
    (re.compile(r"(?<![\wÀ-ÿ'])uw(?![\wÀ-ÿ])"), "Uw"),
    (re.compile(r"(?<![\wÀ-ÿ'])u(?![\wÀ-ÿ'])"), "U"),
    (re.compile(r"(?<![\wÀ-ÿ'])U zich(?![\wÀ-ÿ])"), "U Zich"),
]


def met_hoofdletters(tekst):
    for patroon, vervanging in WOORDEN:
        tekst = patroon.sub(vervanging, tekst)
    return tekst


def open_boeken():
    verified = json.loads((ROOT / "data" / "verified-chapters.json").read_text(encoding="utf-8"))
    return {boek for boek, _ in GEBEDEN if verified.get(boek) != "all"}


def correcties(boek, hoofdstukken):
    uit = {}
    for hoofdstuk, nummers in hoofdstukken.items():
        pad = ROOT / "data" / boek / ("%d.json" % hoofdstuk)
        verzen = {v["number"]: v for v in json.loads(io.open(pad, encoding="utf-8").read())["verses"]}
        for nummer in nummers:
            if nummer not in verzen:
                continue
            tekst = verzen[nummer]["text2026"]
            nieuw = met_hoofdletters(tekst)
            if nieuw != tekst:
                uit[(hoofdstuk, nummer)] = [(tekst, nieuw, "A1")]
    return uit


def werk_a1_bij():
    pad = ROOT / "data" / "wijzigingsprincipes.json"
    data, vorm = lees(str(pad))
    a1 = next(p for p in data["principes"] if p["id"] == "A1")
    toevoeging = (" In de apocriefen schreef de Statenvertaling ook tot God 'gij' en 'uw' met een "
                  "kleine letter; in de gebeden die tot God gericht zijn staat daar 'U' en 'Uw'.")
    if toevoeging not in (a1.get("toelichting") or ""):
        a1["toelichting"] = (a1.get("toelichting") or "") + toevoeging
        schrijf(str(pad), data, vorm)


def main():
    open_ = open_boeken()
    totaal = 0
    for (boek, naam), hoofdstukken in GEBEDEN.items():
        if boek not in open_:
            raise ValueError("%s staat op definitief" % boek)
        totaal += verwerk_correcties(boek, naam, correcties(boek, hoofdstukken))
    werk_a1_bij()
    print("%d verzen kregen een hoofdletter voor God." % totaal)


if __name__ == "__main__":
    main()
