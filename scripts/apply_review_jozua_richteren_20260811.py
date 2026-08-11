#!/usr/bin/env python3
"""Verwerk de menselijke reviewcorrecties voor Jozua en Richteren 1-7."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from sweep_principe import kaal, lees, nieuwe_diff, schrijf  # noqa: E402
from synchroniseer_opmaak import bijtrekken  # noqa: E402


CORRECTIES = {
    ("jozua", 3, 13): [("afvlieten", "afvloeien")],
    ("jozua", 3, 16): [("ter zijde van Sarthan", "aan de kant van Sarthan")],
    ("jozua", 3, 17): [("stonden steevast", "stonden onbeweeglijk")],
    ("jozua", 4, 3): [("het nachtleger", "het kamp")],
    ("jozua", 4, 4): [
        (
            "die hij had doen bestellen van de Israëlieten",
            "die hij uit de Israëlieten had aangesteld",
        )
    ],
    ("jozua", 4, 10): [
        (
            "totdat alle ding volbracht was, dat JAHWEH",
            "totdat alle dingen voltooid waren, die JAHWEH",
        )
    ],
    ("jozua", 9, 2): [
        (
            "om tegen Jozua en tegen Israël eenmoedig te krijgen",
            "om eenmoedig tegen Jozua en tegen Israël te strijden",
        )
    ],
    ("jozua", 9, 14): [
        (
            "Toen namen de mannen van hun reiskost; en zij vraagden het de mond van JAHWEH niet.",
            "Toen namen de mannen van hun reiskost, maar zij baden JAHWEH niet om raad.",
        )
    ],
    ("jozua", 10, 26): [("houten", "palen")],
    ("jozua", 10, 27): [("houten", "palen"), ("alwaar", "waar")],
    ("jozua", 11, 6): [("hen altegader", "hen allen")],
    ("jozua", 15, 19): [("waterwellingen", "bronnen")],
    ("jozua", 17, 14): [("een lot en een snoer", "een lot en een deel")],
    ("jozua", 20, 9): [("een ziel slaat door dwaling", "een ziel slaat zonder opzet")],
    ("jozua", 24, 2): [("[namelijk] Terah", "Terah")],
    ("richteren", 1, 15): [
        ("waterwellingen", "bronnen"),
        ("hoge wellingen en lage wellingen", "hoge bronnen en lage bronnen"),
    ],
    ("richteren", 5, 5): [("De bergen vervloten", "De bergen vloeiden weg")],
    ("richteren", 5, 29): [
        (
            "De wijsten van haar staatsvrouwen antwoordden; ook beantwoordde zij haar redenen aan zichzelf:",
            "Haar meest wijze vorstinnen antwoordden haar; ook beantwoordde zij zichzelf:",
        )
    ],
    ("richteren", 6, 19): [("een efa meels", "een efa meel")],
    ("richteren", 6, 21): [
        ("de Engel van JAHWEH bekwam uit zijn ogen", "de Engel van JAHWEH verdween uit zijn ogen")
    ],
    ("richteren", 7, 3): [("Wie blode en versaagd is", "Wie bevreesd is en beeft")],
}


def pas_verzen_aan() -> None:
    per_bestand: dict[tuple[str, int], list[tuple[int, list[tuple[str, str]]]]] = {}
    for (boek, hoofdstuk, nummer), vervangingen in CORRECTIES.items():
        per_bestand.setdefault((boek, hoofdstuk), []).append((nummer, vervangingen))

    for (boek, hoofdstuk), verscorrecties in per_bestand.items():
        pad = ROOT / "data" / boek / f"{hoofdstuk}.json"
        data, vorm = lees(str(pad))
        for nummer, vervangingen in verscorrecties:
            vers = next(item for item in data["verses"] if item["number"] == nummer)
            tekst = vers["text2026"]
            gewijzigd = False
            for oud, nieuw in vervangingen:
                if oud in tekst:
                    tekst = tekst.replace(oud, nieuw)
                    gewijzigd = True
                elif nieuw in tekst:
                    continue
                else:
                    raise ValueError(f"{boek} {hoofdstuk}:{nummer}: niet gevonden: {oud!r}")
            if not gewijzigd:
                continue
            vers["text2026"] = tekst

            nieuw_html = bijtrekken(vers["text2026_html"], tekst)
            if nieuw_html is not None:
                if kaal(nieuw_html) != kaal(tekst):
                    raise ValueError(f"{boek} {hoofdstuk}:{nummer}: HTML kon niet veilig synchroniseren")
                vers["text2026_html"] = nieuw_html

            vers["phraseDiff"] = nieuwe_diff(
                kaal(vers["textSV1888"]),
                kaal(tekst),
                vers.get("phraseDiff", []),
                None,
                f"{boek} {hoofdstuk}:{nummer}",
            )
        schrijf(str(pad), data, vorm)


def werk_reuzentag_bij() -> None:
    pad = ROOT / "data" / "tags.json"
    data, vorm = lees(str(pad))
    tag = next(item for item in data["tags"] if item["id"] == "reuzen")
    refs = {item["ref"] for item in tag["verzen"]}
    if "jozua 12:5" not in refs:
        tag["verzen"].append({"ref": "jozua 12:5", "rang": 3})
    schrijf(str(pad), data, vorm)


def werk_reviewstatus_bij() -> None:
    pad = ROOT / "data" / "verified-chapters.json"
    data = json.loads(pad.read_text(encoding="utf-8"))
    data["jozua"] = "all"
    data["richteren"] = list(range(1, 8))
    pad.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    pas_verzen_aan()
    werk_reuzentag_bij()
    werk_reviewstatus_bij()
    print(f"{len(CORRECTIES)} verzen bijgewerkt; Jozua en Richteren 1-7 geregistreerd.")


if __name__ == "__main__":
    main()
