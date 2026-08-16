#!/usr/bin/env python3
"""Verwerk de eenduidige tekstcorrecties uit de Google-review voor 2 Koningen."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from sweep_principe import kaal, lees, nieuwe_diff, schrijf  # noqa: E402
from synchroniseer_opmaak import bijtrekken  # noqa: E402


CORRECTIES = {
    (5, 5): [("talenten zilvers", "talenten zilver")],
    (5, 22): [("talent zilvers", "talent zilver")],
    (5, 23): [("talenten zilvers", "talenten zilver")],
    (9, 3): [("vlied", "vlucht")],
    (9, 14): [("een verbintenis", "een samenzwering"), ("uit oorzake van", "wegens")],
    (9, 35): [("bekkeneel", "schedel"), ("het schedel", "de schedel")],
    (10, 1): [("voedsterheren", "verzorgers")],
    (10, 18): [("een weinig", "een beetje")],
    (10, 19): [("door listigheid", "door list")],
    (10, 20): [("Heilig Ba\u00e4l een verbodsdag", "Roep een dag van samenkomst voor Ba\u00e4l af")],
    (10, 25): [("trawanten", "lijfwachten"), ("hoofdmannen", "officieren")],
    (11, 1): [("al het koninklijke zaad", "het hele koninklijke nageslacht")],
    (12, 4): [("de geheiligde dingen", "de gewijde gaven")],
    (12, 5): [
        ("de breuken van het huis verbeteren, naar alles wat er voor breuk bevonden zal worden", "de bouwvalligheden van het huis herstellen, naar alles wat er aan bouwvalligheden gevonden zal worden"),
    ],
    (12, 10): [("veel gelds", "veel geld")],
    (12, 13): [("Evenwel", "Echter")],
    (12, 17): [("voerde krijg", "voerde strijd")],
    (12, 18): [("geheiligde dingen", "gewijde gaven")],
    (13, 17): [("tot verdoens toe", "tot hun vernietiging")],
    (15, 15): [("zijn verbintenis", "zijn samenzwering")],
    (15, 19): [("talenten zilvers", "talenten zilver")],
    (16, 3): [("de gruwelen", "de gruweldaden")],
    (16, 5): [("vermochten niet met strijden", "konden hem niet verslaan")],
    (16, 10): [("naar zijn hele maaksel", "met zijn volledige vormgeving")],
    (17, 4): [
        ("bevond een verbintenis in Hosea, dat hij", "ontdekte dat Hosea samenzwoer: hij had"),
        ("zo besloot hem de koning van Assyri\u00eb, en bond hem in het gevangenhuis", "daarom nam de koning van Assyri\u00eb hem gevangen en zette hem vast in de gevangenis"),
    ],
    (17, 5): [("drie jaren", "drie jaar")],
    (18, 10): [("drie jaren", "drie jaar")],
    (18, 14): [("talenten zilvers", "talenten zilver")],
    (21, 3): [("verdorven had", "vernietigd had")],
    (21, 23): [("maakten een verbintenis", "smeedden een samenzwering")],
    (23, 33): [("talenten zilvers", "talenten zilver")],
    (24, 1): [("drie jaren", "drie jaar")],
    (24, 14): [("tien duizend gevangen", "tien duizend gevangenen")],
    (25, 1): [("vestingen", "schansen")],
    (25, 30): [("En voor wat betreft zijn tering, een voortdurende tering werd hem van de koning gegeven, elk dagelijks bestemde deel op zijn dag, al de dagen van zijn leven.", "En wat zijn levensonderhoud betreft, kreeg hij voortdurend een door de koning vastgesteld dagelijks deel, alle dagen van zijn leven.")],
}


def main() -> None:
    per_hoofdstuk: dict[int, list[tuple[int, list[tuple[str, str]]]]] = {}
    for (hoofdstuk, nummer), wijzigingen in CORRECTIES.items():
        per_hoofdstuk.setdefault(hoofdstuk, []).append((nummer, wijzigingen))

    geraakt = 0
    for hoofdstuk, verswijzigingen in per_hoofdstuk.items():
        pad = ROOT / "data" / "2koningen" / f"{hoofdstuk}.json"
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
                    raise ValueError(f"2 Koningen {hoofdstuk}:{nummer}: niet gevonden: {zoek!r}")
            if not tekstueel_gewijzigd:
                continue
            item["text2026"] = nieuw
            html = bijtrekken(item["text2026_html"], nieuw)
            if html is None or kaal(html) != kaal(nieuw):
                raise ValueError(f"2 Koningen {hoofdstuk}:{nummer}: opmaak kon niet veilig worden bijgewerkt")
            item["text2026_html"] = html
            item["phraseDiff"] = nieuwe_diff(
                kaal(item["textSV1888"]),
                kaal(nieuw),
                item.get("phraseDiff", []),
                None,
                f"2koningen {hoofdstuk}:{nummer}",
            )
            geraakt += 1
            gewijzigd = True
        if gewijzigd:
            schrijf(str(pad), data, vorm)
    print(f"{geraakt} 2-Koningsverzen bijgewerkt.")


if __name__ == "__main__":
    main()
