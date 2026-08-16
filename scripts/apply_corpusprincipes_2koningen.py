#!/usr/bin/env python3
"""Voer de veilige, algemene principes uit de review van 2 Koningen uit."""

from __future__ import annotations

import json
import re
from pathlib import Path

from sweep_principe import kaal, lees, nieuwe_diff, schrijf


ROOT = Path(__file__).resolve().parents[1]
PRINCIPES = ROOT / "data" / "wijzigingsprincipes.json"


REGELS = (
    {
        "id": "MR-2K-GLOBAL-001",
        "categorie": "Spelling en grammatica",
        "oud": "zilvers",
        "nieuw": "zilver",
        "toelichting": "De stofnaam zilver krijgt in deze constructies geen verbuigings-s.",
        "regex": r"\bzilvers\b",
        "patroon": re.compile(r"\bzilvers\b", re.IGNORECASE),
        "vervang": lambda m: "Zilver" if m.group(0)[0].isupper() else "zilver",
    },
    {
        "id": "MR-2K-GLOBAL-002",
        "categorie": "Verouderde woorden",
        "oud": "uit oorzake van",
        "nieuw": "wegens",
        "toelichting": "Verouderde voorzetselgroep vervangen door het hedendaagse wegens.",
        "regex": r"\buit oorzake van\b",
        "patroon": re.compile(r"\buit oorzake van\b", re.IGNORECASE),
        "vervang": lambda m: "Wegens" if m.group(0)[0].isupper() else "wegens",
    },
    {
        "id": "MR-2K-GLOBAL-003",
        "categorie": "Verouderde woorden",
        "oud": "trawant / trawanten",
        "nieuw": "lijfwacht / lijfwachten",
        "toelichting": "Trawant duidt hier op een gewapende lijfwacht.",
        "regex": r"\btrawant(en)?\b",
        "patroon": re.compile(r"\btrawant(en)?\b", re.IGNORECASE),
        "vervang": lambda m: ("Lijfwachten" if m.group(0)[0].isupper() else "lijfwachten")
        if m.group(1) else ("Lijfwacht" if m.group(0)[0].isupper() else "lijfwacht"),
    },
    {
        "id": "MR-2K-GLOBAL-004",
        "categorie": "Spelling en grammatica",
        "oud": "drie jaren",
        "nieuw": "drie jaar",
        "toelichting": "Na een bepaald hoofdtelwoord blijft jaar in deze tijdsduurconstructie enkelvoud.",
        "regex": r"\bdrie jaren\b",
        "patroon": re.compile(r"\bdrie jaren\b", re.IGNORECASE),
        "vervang": lambda m: "Drie jaar" if m.group(0)[0].isupper() else "drie jaar",
    },
    {
        "id": "V340",
        "categorie": "Verouderde woorden",
        "oud": "vlied",
        "nieuw": "vlucht",
        "toelichting": "De verouderde gebiedende wijs vlied wordt vlucht.",
        "regex": r"\bvlied\b",
        "patroon": re.compile(r"\bvlied\b", re.IGNORECASE),
        "bronpatroon": re.compile(r"\bvliedt?\b", re.IGNORECASE),
        "vervang": lambda m: "Vlucht" if m.group(0)[0].isupper() else "vlucht",
    },
)


def registreer_principes() -> None:
    data = json.loads(PRINCIPES.read_text(encoding="utf-8"))
    bestaand = {item["id"]: item for item in data["principes"]}
    for regel in REGELS:
        velden = {k: regel[k] for k in ("id", "categorie", "oud", "nieuw", "toelichting", "regex")}
        velden.update({"bron": "menselijke-review", "bereik": "hele corpus"})
        if regel["id"] in bestaand:
            bestaand[regel["id"]].update(velden)
        else:
            data["principes"].append(velden)
    PRINCIPES.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def pas_toe() -> int:
    geraakt = 0
    for pad in sorted((ROOT / "data").glob("*/*.json")):
        if not pad.stem.isdigit():
            continue
        try:
            data, vorm = lees(str(pad))
        except (OSError, ValueError, json.JSONDecodeError):
            continue
        gewijzigd = False
        for vers in data.get("verses", []):
            ov = vers.get("text2026", "")
            html = vers.get("text2026_html", "")
            sv = vers.get("textSV1888", "")
            for regel in REGELS:
                patroon = regel["patroon"]
                bronpatroon = regel.get("bronpatroon", patroon)
                if not patroon.search(ov) or not bronpatroon.search(sv or ov):
                    continue
                nieuw = patroon.sub(regel["vervang"], ov)
                nieuw_html = patroon.sub(regel["vervang"], html)
                if nieuw == ov:
                    continue
                vers["text2026"] = nieuw
                vers["text2026_html"] = nieuw_html
                oude_diff = vers.get("phraseDiff", [])
                nieuwe_phrase_diff = nieuwe_diff(
                    kaal(sv), kaal(nieuw), vers.get("phraseDiff", []), regel["id"],
                    f"{pad.parent.name}:{pad.stem}:{vers.get('number')}",
                )
                aanwezige_ids = {item.get("principe") for item in nieuwe_phrase_diff}
                for bestaand in oude_diff:
                    if bestaand.get("principe") and bestaand["principe"] not in aanwezige_ids:
                        nieuwe_phrase_diff.append(dict(bestaand))
                        aanwezige_ids.add(bestaand["principe"])
                vers["phraseDiff"] = nieuwe_phrase_diff
                ov, html = nieuw, nieuw_html
                geraakt += 1
                gewijzigd = True
        if gewijzigd:
            schrijf(str(pad), data, vorm)
    return geraakt


if __name__ == "__main__":
    registreer_principes()
    print(f"{pas_toe()} corpusbrede wijzigingen toegepast.")
