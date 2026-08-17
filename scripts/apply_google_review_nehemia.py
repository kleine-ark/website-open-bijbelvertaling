#!/usr/bin/env python3
"""Verwerk de eenduidige menselijke review van Nehemia en registreer principes."""

from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from sweep_principe import kaal, lees, nieuwe_diff, schrijf  # noqa: E402
from synchroniseer_opmaak import bijtrekken  # noqa: E402


CORRECTIES = {
    (2, 9): [("ruiteren", "ruiters")],
    (3, 13): [("grendelen", "grendels")],
    (3, 18): [("verbeterden", "herstelden")],
    (4, 2): [("amechtige Joden", "zwakke Joden")],
    (4, 8): [("een verbintenis", "een samenzwering")],
    (4, 10): [("De kracht van de dragers is vervallen", "De kracht van de dragers is afgenomen"),
              ("veel stof", "veel puin")],
    (4, 22): [("vernachte", "overnachte")],
    (4, 23): [("geweer", "werpspies")],
    (5, 18): [("allen wijn", "alle wijn")],
    (6, 19): [("vreesachtig te maken", "bang te maken")],
    (9, 3): [("een vierendeel", "een vierde deel"), ("een ander vierendeel", "een ander vierde deel")],
    (9, 11): [("gekliefd", "gespleten")],
    (10, 33): [("spijsoffer", "voedseloffer")],
}


def norm(tekst: str) -> str:
    return re.sub(r"\s+", " ", tekst.strip().lower())


def registreer_principes() -> dict[tuple[str, str], str]:
    pad = ROOT / "data" / "wijzigingsprincipes.json"
    data = json.loads(pad.read_text(encoding="utf-8"))
    data["principes"] = [p for p in data["principes"] if not p.get("id", "").startswith("MR-NEH-")]
    koppeling = {}
    nummer = 1
    for (hoofdstuk, vers), paren in sorted(CORRECTIES.items()):
        for oud, nieuw in paren:
            pid = f"MR-NEH-{nummer:03d}"
            nummer += 1
            koppeling[(norm(oud), norm(nieuw))] = pid
            data["principes"].append({
                "id": pid,
                "categorie": "Menselijke review",
                "oud": oud,
                "nieuw": nieuw,
                "toelichting": "Contextueel beoordeeld tijdens de menselijke review van Nehemia.",
                "regex": "",
                "voorbeeld": f"Nehemia {hoofdstuk}:{vers}",
                "bereik": {"nehemia": [f"{hoofdstuk}:{vers}"]},
                "bron": "menselijke-review",
            })
    pad.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return koppeling


def main() -> None:
    principes = registreer_principes()
    per_hoofdstuk = defaultdict(list)
    for (hoofdstuk, nummer), paren in CORRECTIES.items():
        per_hoofdstuk[hoofdstuk].append((nummer, paren))

    geraakt = 0
    for hoofdstuk, regels in per_hoofdstuk.items():
        pad = ROOT / "data" / "nehemia" / f"{hoofdstuk}.json"
        data, vorm = lees(str(pad))
        verzen = {item["number"]: item for item in data["verses"]}
        gewijzigd = False
        for nummer, paren in regels:
            item = verzen[nummer]
            tekst = item["text2026"]
            opgeslagen_tekst = tekst
            # Herstel uitvoer van een oudere, niet woordbegrensde proefrun.
            tekst = tekst.replace("oovernachte", "overnachte")
            oud_tekst = tekst
            for oud, nieuw in paren:
                patroon = re.compile(rf"(?<!\w){re.escape(oud)}(?!\w)")
                if patroon.search(tekst):
                    tekst = patroon.sub(nieuw, tekst)
                elif not re.search(rf"(?<!\w){re.escape(nieuw)}(?!\w)", tekst):
                    raise ValueError(f"Nehemia {hoofdstuk}:{nummer}: niet gevonden: {oud!r}")
            if tekst != opgeslagen_tekst:
                item["text2026"] = tekst
                html = bijtrekken(item["text2026_html"], tekst)
                if html is None or kaal(html) != kaal(tekst):
                    raise ValueError(f"Nehemia {hoofdstuk}:{nummer}: opmaak kon niet veilig worden bijgewerkt")
                item["text2026_html"] = html
                item["phraseDiff"] = nieuwe_diff(kaal(item["textSV1888"]), kaal(tekst), item.get("phraseDiff", []), None, f"nehemia {hoofdstuk}:{nummer}")
                geraakt += 1
                gewijzigd = True
            # Iedere handmatig beoordeelde correctie krijgt een expliciete koppeling.
            for oud, nieuw in paren:
                pid = principes[(norm(oud), norm(nieuw))]
                verschillen = item.setdefault("phraseDiff", [])
                if not any(v.get("principe") == pid for v in verschillen):
                    doel = next((v for v in verschillen if norm(nieuw) in norm(v.get("new", "")) and not v.get("principe")), None)
                    if doel is None:
                        doel = {"old": oud, "new": nieuw}
                        verschillen.append(doel)
                    doel["principe"] = pid
                    gewijzigd = True
        if gewijzigd:
            schrijf(str(pad), data, vorm)
    print(f"{geraakt} Nehemia-verzen tekstueel bijgewerkt; {len(principes)} principes gekoppeld.")


if __name__ == "__main__":
    main()
