#!/usr/bin/env python3
"""Verwerk concrete taal- en opmaakcorrecties voor Richteren."""

from __future__ import annotations

import sys
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from sweep_principe import kaal, lees, nieuwe_diff, schrijf  # noqa: E402
from synchroniseer_opmaak import bijtrekken  # noqa: E402


CORRECTIES = {
    (8, 1): [("Wat stuk is dit", "Wat is dit")],
    (9, 34): [("vier hopen", "vier groepen")],
    (10, 17): [("de kinderen Ammons", "de kinderen van Ammon")],
    (11, 2): [("stieten Jeftha uit", "verstootten Jeftha uit")],
    (11, 38): [("met haar gezellinnen", "met haar vriendinnen")],
    (11, 39): [("een gewoonheid in Israël", "een gewoonte in Israël")],
    (12, 3): [("u niet verlostet", "u niet verloste")],
    (13, 25): [("hem bij wijlen te drijven", "hem bij tijden aan te vuren")],
    (14, 8): [("het aas van de leeuw", "het kadaver van de leeuw")],
    (14, 20): [("hem vergezelschapt had", "hem vergezeld had")],
    (15, 2): [("u haar geheel haattet", "u haar geheel haatte")],
    (16, 31): [("Israël gericht twintig jaren", "Israël gericht twintig jaar")],
    (20, 38): [("tijd met de achterlage", "tijd met de hinderlaag")],
}

TAGGEN = {
    "afgoden": {
        "id": "afgoden",
        "naam": "Afgoden in de Bijbel",
        "beschrijving": "Teksten over afgoderij en het dienen van andere goden.",
        "kleur": "#8b5e3c",
        "verzen": [{"ref": "richteren 8:33", "rang": 2}],
    },
    "almacht-van-god": {
        "id": "almacht-van-god",
        "naam": "De almacht van God",
        "beschrijving": "God bestuurt ook de loop van volken en koningen.",
        "kleur": "#315b7d",
        "verzen": [{"ref": "richteren 9:23", "rang": 2}],
    },
    "zaaien-en-oogsten": {
        "id": "zaaien-en-oogsten",
        "naam": "Zaaien en oogsten",
        "beschrijving": "Wat een mens doet, heeft gevolgen die hij terugontvangt.",
        "kleur": "#6d8f39",
        "verzen": [{"ref": "richteren 9:56", "rang": 2}],
    },
    "vruchtbaarheid-en-onvruchtbaarheid": {
        "id": "vruchtbaarheid-en-onvruchtbaarheid",
        "naam": "Vruchtbaarheid en onvruchtbaarheid",
        "beschrijving": "Teksten over kinderloosheid, ontvangenis en geboorte.",
        "kleur": "#b36f8c",
        "verzen": [{"ref": "richteren 13:2", "rang": 2}],
    },
}


def vers(data: dict, nummer: int) -> dict:
    return next(item for item in data["verses"] if item["number"] == nummer)


def main() -> None:
    per_hoofdstuk: dict[int, list[tuple[int, list[tuple[str, str]]]]] = {}
    for (hoofdstuk, nummer), wijzigingen in CORRECTIES.items():
        per_hoofdstuk.setdefault(hoofdstuk, []).append((nummer, wijzigingen))

    gewijzigd = 0
    for hoofdstuk, verswijzigingen in per_hoofdstuk.items():
        pad = ROOT / "data" / "richteren" / f"{hoofdstuk}.json"
        data, vorm = lees(str(pad))
        for nummer, wijzigingen in verswijzigingen:
            item = vers(data, nummer)
            oud = item["text2026"]
            nieuw = oud
            for zoek, vervang in wijzigingen:
                if zoek in nieuw:
                    nieuw = nieuw.replace(zoek, vervang)
                elif vervang not in nieuw:
                    raise ValueError(f"Richteren {hoofdstuk}:{nummer}: niet gevonden: {zoek!r}")
            if nieuw == oud:
                continue
            item["text2026"] = nieuw
            html = bijtrekken(item["text2026_html"], nieuw)
            if html is None or kaal(html) != kaal(nieuw):
                raise ValueError(f"Richteren {hoofdstuk}:{nummer}: opmaak kon niet veilig worden bijgewerkt")
            item["text2026_html"] = html
            item["phraseDiff"] = nieuwe_diff(
                kaal(item["textSV1888"]), kaal(nieuw), item.get("phraseDiff", []), None,
                f"richteren {hoofdstuk}:{nummer}",
            )
            gewijzigd += 1
        schrijf(str(pad), data, vorm)

    # Beide verzen zijn uitgesproken tekst. De volledige versinhoud krijgt één citaatblok.
    for hoofdstuk, nummer in ((17, 9), (18, 10)):
        pad = ROOT / "data" / "richteren" / f"{hoofdstuk}.json"
        data, vorm = lees(str(pad))
        item = vers(data, nummer)
        html = item["text2026_html"]
        if hoofdstuk == 17:
            html = html.replace(
                "</i></span> verkeren, waar ik gelegenheid zal vinden.",
                " verkeren, waar ik gelegenheid zal vinden.</i></span>",
            )
        elif not html.startswith('<span class="direct-speech"><i>'):
            html = f'<span class="direct-speech"><i>{html}</i></span>'
        if kaal(html) != kaal(item["text2026"]):
            raise ValueError(f"Richteren {hoofdstuk}:{nummer}: citaatopmaak wijkt af van tekst")
        item["text2026_html"] = html
        schrijf(str(pad), data, vorm)

    tag_pad = ROOT / "data" / "tags.json"
    tags_data = json.loads(tag_pad.read_text(encoding="utf-8"))
    tags = tags_data["tags"]
    per_id = {tag["id"]: tag for tag in tags if tag.get("id")}
    for tag_id, nieuw in TAGGEN.items():
        tag = per_id.get(tag_id) or next(
            (bestaand for bestaand in tags if bestaand.get("naam") == nieuw["naam"]), None
        )
        if tag is None:
            tag = dict(nieuw)
            tags.append(tag)
        else:
            tag.setdefault("id", tag_id)
        bestaande = {item["ref"] for item in tag["verzen"]}
        for item in nieuw["verzen"]:
            if item["ref"] not in bestaande:
                tag["verzen"].append(item)
    lhbtq = per_id["lhbtq"]
    if "richteren 19:22" not in {item["ref"] for item in lhbtq["verzen"]}:
        lhbtq["verzen"].append({"ref": "richteren 19:22", "rang": 2})
    tag_pad.write_text(json.dumps(tags_data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    print(f"{gewijzigd} Richteren-verzen tekstueel bijgewerkt; 2 citaten en 5 onderwerpen bijgewerkt.")


if __name__ == "__main__":
    main()
