"""Bouw de vindplaatsen voor de wiki-pagina over tijdsaanduidingen."""

from __future__ import annotations

import argparse
import json
import pathlib
import re


LETTER = r"[A-Za-zÀ-ÖØ-öø-ÿĀ-ž]"


def _patterns(tijden):
    rangtelwoorden = tijden["rangtelwoorden"]
    rangen = "|".join(re.escape(woord) for woord in rangtelwoorden)
    dagdeel = (
        r"(?:\s+van\s+(?:de|den|het)\s+(?:nacht|dag)"
        r"|\s+in\s+de\s+nacht|\s+overdag)?"
    )
    lidwoord = r"(?:(?:het|den|de|dit|dat|die)\s+)?"
    uur = re.compile(
        r"\b(?:(ongeveer|omtrent|omstreeks|circa)\s+)?"
        r"(?:(op|om|te|ten|ter)\s+)?"
        + lidwoord
        + r"("
        + rangen
        + r")"
        + r"(?:\s+en\s+"
        + lidwoord
        + r"("
        + rangen
        + r"))?\s+(?:uur|ure)("
        + dagdeel
        + r")(?!"
        + LETTER
        + r")",
        re.IGNORECASE,
    )
    wake = re.compile(
        r"\b("
        + rangen
        + r")\s+(?:nachtwake|nachtwaak|wake|waak)(?!\s+op\b)"
        + r"(?:\s+in\s+de\s+nacht)?(?!"
        + LETTER
        + r")",
        re.IGNORECASE,
    )
    return uur, wake


def build_index(root: pathlib.Path):
    root = pathlib.Path(root)
    tijden = json.loads((root / "data" / "tijden.json").read_text(encoding="utf-8"))
    boeken = json.loads((root / "data" / "books.json").read_text(encoding="utf-8"))["books"]
    rangtelwoorden = tijden["rangtelwoorden"]
    uur_re, wake_re = _patterns(tijden)

    groepen = {}
    for soort in ("dag", "nacht"):
        for nummer in range(1, 13):
            groepen[f"{soort}-{nummer}"] = []
    for nummer in range(1, 5):
        groepen[f"wake-{nummer}"] = []
    for regel in tijden["genoemdeWaken"] + tijden["frases"] + tijden["toelichtingen"]:
        if regel["id"] != "joh452":
            groepen.setdefault(regel["id"], [])

    def voeg_toe(groep, vindplaats):
        waarden = groepen.setdefault(groep, [])
        if vindplaats not in waarden:
            waarden.append(vindplaats)

    for boek in boeken:
        boek_id = boek["id"]
        for hoofdstuk in boek.get("chaptersIncluded", []):
            pad = root / "data" / boek_id / f"{hoofdstuk}.json"
            if not pad.exists():
                continue
            data = json.loads(pad.read_text(encoding="utf-8"))
            for vers in data.get("verses", []):
                tekst = vers.get("text2026", "")
                vindplaats = f"{boek_id} {hoofdstuk}:{vers['number']}"

                for match in uur_re.finditer(tekst):
                    nacht = "nacht" in (match.group(5) or "").lower()
                    soort = "nacht" if nacht else "dag"
                    voeg_toe(
                        f"{soort}-{rangtelwoorden[match.group(3).lower()]}",
                        vindplaats,
                    )
                    if match.group(4):
                        voeg_toe(
                            f"{soort}-{rangtelwoorden[match.group(4).lower()]}",
                            vindplaats,
                        )

                for match in wake_re.finditer(tekst):
                    nummer = rangtelwoorden[match.group(1).lower()]
                    voeg_toe(f"wake-{nummer}", vindplaats)

                regels = tijden["genoemdeWaken"] + tijden["frases"] + tijden["toelichtingen"]
                for regel in regels:
                    if regel.get("alleenIn") and vindplaats not in regel["alleenIn"]:
                        continue
                    if not re.search(regel["patroon"], tekst, re.IGNORECASE):
                        continue
                    groep = "dag-7" if regel["id"] == "joh452" else regel["id"]
                    voeg_toe(groep, vindplaats)

    unieke_vindplaatsen = {
        vindplaats for vindplaatsen in groepen.values() for vindplaats in vindplaatsen
    }
    return {
        "gegenereerdUit": [
            "data/books.json",
            "data/tijden.json",
            "data/<boek>/<hoofdstuk>.json",
        ],
        "aantalUniekeVindplaatsen": len(unieke_vindplaatsen),
        "groepen": groepen,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=pathlib.Path, default=pathlib.Path(__file__).resolve().parents[1])
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    output = args.root / "data" / "naslag-tijdsaanduidingen.json"
    inhoud = json.dumps(build_index(args.root), ensure_ascii=False, indent=2) + "\n"

    if args.check:
        if not output.exists() or output.read_text(encoding="utf-8") != inhoud:
            raise SystemExit("data/naslag-tijdsaanduidingen.json is niet actueel")
        return
    output.write_text(inhoud, encoding="utf-8")


if __name__ == "__main__":
    main()
