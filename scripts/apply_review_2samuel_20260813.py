#!/usr/bin/env python3
"""Verwerk de eenduidige taalcorrecties uit de redactionele lijst voor 2 Samuel."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from sweep_principe import kaal, lees, nieuwe_diff, schrijf  # noqa: E402
from synchroniseer_opmaak import bijtrekken  # noqa: E402


# Alleen expliciete, tekstuele vervangingen. Citatie-, tag- en onderzoeksverzoeken
# blijven in de bronlijst staan totdat zij inhoudelijk zijn uitgewerkt.
CORRECTIES = {
    (1, 1): [("wedergekomen", "teruggekomen")],
    (1, 2): [("wiens kleren", "van wie de kleren")],
    (1, 4): [("Verhaal het mij", "Vertel het mij")],
    (1, 6): [("bij geval", "toevallig")],
    (1, 10): [("armgesmijde", "armband")],
    (1, 13): [("vreemden man", "vreemdeling")],
    (2, 14): [("voor ons aangezicht spelen", "voor ons aangezicht vechten")],
    (2, 25): [("tot één hoop", "tot één groep")],
    (3, 7): [("wier naam", "van wie de naam")],
    (4, 4): [("geslagen was aan beide voeten", "verlamd was aan beide voeten")],
    (4, 6): [("als zullende", "alsof zij")],
    (4, 7): [("hieuwen zijn hoofd af", "hakten zijn hoofd af")],
    (5, 6): [("dat is te zeggen", "dat wil zeggen")],
    (6, 1): [("uitgelezenen", "beste mannen")],
    (6, 8): [("een scheur gescheurd had", "een zware slag toegebracht had")],
    (6, 21): [("mij instellende tot", "mij aangesteld heeft als")],
    (7, 29): [("Zo believe het U nu", "Zo moge het U nu behagen")],
    (8, 8): [("kopers", "koper")],
    (9, 1): [("omwille van", "vanwege")],
    (10, 5): [("gewassen zal zijn", "gegroeid zal zijn")],
    (10, 8): [("waren bijzonder in het veld", "stonden afzonderlijk in het veld")],
    (11, 1): [("met de wederkomst van het jaar", "bij het aanbreken van het nieuwe jaar"), ("henenzond", "heenzond"), ("verderven", "zouden vernietigen")],
    (11, 2): [("zeer schoon van aanzien", "heel knap om te zien")],
    (11, 8): [("volgde hem een gerecht van de koning achterna", "werd hem een gerecht van de koning achternagebracht")],
    (12, 4): [("een wandelaar overkwam", "een wandelaar ontving"), ("verschoonde hij te nemen", "zag hij ervan af te nemen")],
    (12, 31): [("ticheloven", "kleioven")],
    (13, 1): [("een schone zus", "een knappe zus"), ("wier naam", "van wie de naam")],
    (13, 16): [("geen oorzaken", "geen redenen")],
    (14, 2): [("rouw droegt", "rouw draagt")],
    (14, 30): [("het stuk akkers", "de akker")],
    (15, 2): [("allen man", "iedereen")],
    (15, 4): [("Dat alle man tot mij kwame", "Dat iedereen tot mij zou komen")],
    (15, 28): [("vertoeven", "verblijven")],
    (17, 1): [("mannen uitlezen", "mannen uitzoeken")],
    (17, 10): [("wiens hart", "van wie het hart")],
    (18, 5): [("zachtkens", "voorzichtig")],
    (18, 22): [("bekwame boodschap", "passende boodschap")],
    (18, 27): [("de loop van de eerste", "de manier van lopen van de eerste")],
    (19, 3): [("steelsgewijze", "sluipend")],
    (20, 3): [("haarlieder dood", "hun dood")],
    (20, 6): [("meer kwaads doen", "meer kwaad doen")],
    (21, 12): [("burgeren", "burgers")],
    (23, 7): [("ter zelver plaats", "op die plaats")],
}


def main() -> None:
    per_hoofdstuk: dict[int, list[tuple[int, list[tuple[str, str]]]]] = {}
    for (hoofdstuk, nummer), wijzigingen in CORRECTIES.items():
        per_hoofdstuk.setdefault(hoofdstuk, []).append((nummer, wijzigingen))
    geraakt = 0
    for hoofdstuk, verswijzigingen in per_hoofdstuk.items():
        pad = ROOT / "data" / "2samuel" / f"{hoofdstuk}.json"
        data, vorm = lees(str(pad))
        by_number = {item["number"]: item for item in data["verses"]}
        gewijzigd = False
        for nummer, wijzigingen in verswijzigingen:
            item = by_number[nummer]
            oud = item["text2026"]
            nieuw = oud
            tekstueel_gewijzigd = False
            for zoek, vervang in wijzigingen:
                if zoek in nieuw:
                    nieuw = nieuw.replace(zoek, vervang)
                    tekstueel_gewijzigd = True
                elif vervang not in nieuw:
                    raise ValueError(f"2 Samuel {hoofdstuk}:{nummer}: niet gevonden: {zoek!r}")
            if not tekstueel_gewijzigd:
                continue
            item["text2026"] = nieuw
            html = bijtrekken(item["text2026_html"], nieuw)
            if html is None or kaal(html) != kaal(nieuw):
                raise ValueError(f"2 Samuel {hoofdstuk}:{nummer}: opmaak kon niet veilig worden bijgewerkt")
            item["text2026_html"] = html
            item["phraseDiff"] = nieuwe_diff(kaal(item["textSV1888"]), kaal(nieuw), item.get("phraseDiff", []), None, f"2samuel {hoofdstuk}:{nummer}")
            geraakt += 1
            gewijzigd = True
        if gewijzigd:
            schrijf(str(pad), data, vorm)
    print(f"{geraakt} 2-Samuel-verzen bijgewerkt.")


if __name__ == "__main__":
    main()
