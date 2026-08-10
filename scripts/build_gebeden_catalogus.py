#!/usr/bin/env python3
"""Vul de gebedencatalogus aan en zet hem in canonieke leesvolgorde."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "data" / "naslag-gebeden.json"

GEBEDSPSALMEN = [
    3, 4, 5, 6, 7, 9, 10, 12, 13, 16, 17, 19, 20, 22, 25, 26, 27, 28,
    30, 31, 33, 35, 36, 38, 39, 40, 41, 42, 43, 44, 51, 54, 55, 56, 57,
    58, 59, 60, 61, 63, 64, 67, 69, 70, 71, 72, 74, 77, 79, 80, 82, 83,
    84, 85, 86, 88, 89, 90, 94, 102, 106, 108, 109, 115, 116, 118, 119,
    120, 122, 123, 125, 126, 129, 130, 132, 137, 138, 139, 140, 141, 142,
    143, 144,
]

BOOK_ORDER = """
genesis exodus leviticus numeri deuteronomium jozua richteren ruth 1samuel
2samuel 1koningen 2koningen 1kronieken 2kronieken ezra nehemia esther job
psalmen spreuken prediker hooglied jesaja jeremia klaagliederen ezechiel daniel
hosea joel amos obadja jona micha nahum habakuk zefanja haggai zacharia maleachi
3ezra 4ezra tobit judith boekderwijsheid jezussirach baruch estherapocrief
gebedvanazaria gezangindevuuroven susanna belenddedraak gebedvanmanasse
1makkabeeen 2makkabeeen 3makkabeeen mattheus markus lukas johannes handelingen
romeinen 1korinthiers 2korinthiers galaten efeziers filippenzen kolossenzen
1tessalonicensen 2tessalonicensen 1timotheus 2timotheus titus filemon hebreeen
jakobus 1petrus 2petrus 1johannes 2johannes 3johannes judas openbaring
""".split()

BEKENDE_PSALMEN = {
    17: "davids-gebed-om-bewaring-psalm-17",
    51: "davids-boetgebed-psalm-51",
    72: "davids-gebed-voor-salomo-psalm-72",
    86: "davids-gebed-in-benauwdheid-psalm-86",
    90: "het-gebed-van-mozes-psalm-90",
    102: "gebed-van-de-verdrukte-psalm-102",
    119: "gebed-om-leven-naar-gods-woord-psalm-119",
    130: "gebed-uit-de-diepten-psalm-130",
    142: "davids-gebed-in-de-grot-psalm-142",
}


def tekstpassage(boek: str, hoofdstuk: int, van: int, tot: int, label: str) -> dict:
    return {
        "boek": boek,
        "hoofdstuk": hoofdstuk,
        "van": van,
        "tot": tot,
        "label": label,
    }


def gebed(item_id: str, naam: str, beschrijving: str, passages: list[dict]) -> dict:
    eerste = passages[0]
    return {
        "id": item_id,
        "naam": naam,
        "beschrijving": beschrijving,
        "verzen": [
            f"{passage['boek']} {passage['hoofdstuk']}:{passage['van']}"
            for passage in passages
        ],
        "tekstpassages": passages,
    }


def mozes_gebeden() -> list[dict]:
    gegevens = [
        ("mozes-klacht-over-farao", "Mozes' klacht na Farao's verzwaring", "Mozes keert tot JAHWEH terug wanneer Farao de last van Israël verzwaart.", "exodus", 5, 22, 23, "Exodus 5:22–23"),
        ("mozes-gebed-bij-refidim", "Mozes' gebed om hulp bij Refidim", "Wanneer het volk hem bijna stenigt, roept Mozes tot JAHWEH om hulp.", "exodus", 17, 4, 4, "Exodus 17:4"),
        ("mozes-voorbede-na-het-gouden-kalf", "Mozes' voorbede na het gouden kalf", "Mozes pleit voor Israël met een beroep op Gods Naam, uittocht en beloften.", "exodus", 32, 11, 14, "Exodus 32:11–14"),
        ("mozes-tweede-voorbede-na-het-gouden-kalf", "Mozes' tweede voorbede na het gouden kalf", "Mozes belijdt de grote zonde van het volk en biedt zichzelf aan in hun plaats.", "exodus", 32, 31, 32, "Exodus 32:31–32"),
        ("mozes-gebed-om-gods-tegenwoordigheid", "Mozes' gebed om Gods tegenwoordigheid", "Mozes vraagt dat Gods aangezicht met Israël meegaat en het volk van alle volken onderscheidt.", "exodus", 33, 12, 17, "Exodus 33:12–17"),
        ("mozes-gebed-om-gods-heerlijkheid", "Mozes' gebed om Gods heerlijkheid te zien", "Mozes vraagt God Zijn heerlijkheid te tonen.", "exodus", 33, 18, 23, "Exodus 33:18–23"),
        ("mozes-voorbede-na-de-verbondsvernieuwing", "Mozes' voorbede na de verbondsvernieuwing", "Mozes vraagt dat JAHWEH in het midden van het hardnekkige volk meegaat en het tot erfdeel aanneemt.", "exodus", 34, 8, 9, "Exodus 34:8–9"),
        ("mozes-gebeden-bij-het-optrekken-en-rusten-van-de-ark", "Mozes' gebeden bij het optrekken en rusten van de ark", "Bij vertrek en rust van de ark bidt Mozes om Gods overwinning en blijvende tegenwoordigheid.", "numeri", 10, 35, 36, "Numeri 10:35–36"),
        ("mozes-klacht-over-de-last-van-het-volk", "Mozes' klacht over de last van het volk", "Mozes legt de ondraaglijke last van het morrende volk voor JAHWEH neer.", "numeri", 11, 10, 15, "Numeri 11:10–15"),
        ("mozes-gebed-voor-mirjam", "Mozes' gebed voor Mirjam", "Mozes roept tot God om de genezing van zijn zuster Mirjam.", "numeri", 12, 13, 13, "Numeri 12:13"),
        ("mozes-voorbede-na-de-verspieders", "Mozes' voorbede na het verslag van de verspieders", "Mozes pleit voor vergeving van Israël op grond van Gods geduld en goedertierenheid.", "numeri", 14, 13, 19, "Numeri 14:13–19"),
        ("mozes-en-aaron-voor-de-gemeente", "Mozes en Aäron bidden voor de gemeente", "Mozes en Aäron vallen op hun aangezicht en vragen of heel de gemeente om de zonde van één man zal worden getroffen.", "numeri", 16, 22, 22, "Numeri 16:22"),
        ("mozes-gebed-om-een-opvolger", "Mozes' gebed om een opvolger", "Mozes vraagt JAHWEH een man over de gemeente te stellen die het volk leidt.", "numeri", 27, 15, 17, "Numeri 27:15–17"),
        ("mozes-gebed-om-kanaan-binnen-te-gaan", "Mozes' gebed om Kanaän binnen te gaan", "Mozes smeekt de goede aarde aan de overzijde van de Jordaan te mogen zien.", "deuteronomium", 3, 23, 25, "Deuteronomium 3:23–25"),
    ]
    result = [
        gebed(item_id, naam, beschrijving, [tekstpassage(boek, hoofdstuk, van, tot, label)])
        for item_id, naam, beschrijving, boek, hoofdstuk, van, tot, label in gegevens
    ]
    result[2]["verzen"].append("deuteronomium 9:26")
    result[2]["tekstpassages"].append(
        tekstpassage("deuteronomium", 9, 26, 29, "Deuteronomium 9:26–29")
    )
    return result


def psalm_item(number: int, bestaand: dict[str, dict]) -> dict:
    bestaand_id = BEKENDE_PSALMEN.get(number)
    if bestaand_id and bestaand_id in bestaand:
        return bestaand[bestaand_id]

    chapter = json.loads((ROOT / "data" / "psalmen" / f"{number}.json").read_text(encoding="utf-8"))
    verse_numbers = [int(verse["number"]) for verse in chapter["verses"]]
    first, last = min(verse_numbers), max(verse_numbers)
    label = f"Psalm {number}:{first}" if first == last else f"Psalm {number}:{first}–{last}"
    return gebed(
        f"gebed-uit-psalm-{number}",
        f"Gebed uit Psalm {number}",
        f"Psalm {number} bevat een rechtstreeks gebed tot God. Hier staat de volledige psalmtekst.",
        [tekstpassage("psalmen", number, first, last, label)],
    )


def sort_key(item: dict, original_index: int) -> tuple[int, int, int, int]:
    passage = item["tekstpassages"][0]
    try:
        book_index = BOOK_ORDER.index(passage["boek"])
    except ValueError:
        book_index = len(BOOK_ORDER)
    return (
        book_index,
        int(passage.get("hoofdstuk", passage.get("vanHoofdstuk", 0))),
        int(passage.get("van", 0)),
        original_index,
    )


def build() -> dict:
    source = json.loads(TARGET.read_text(encoding="utf-8"))
    existing = {item["id"]: item for item in source["items"]}
    mozes = mozes_gebeden()
    mozes_ids = {item["id"] for item in mozes}
    items = [
        item
        for item in source["items"]
        if item["tekstpassages"][0]["boek"] != "psalmen"
        and item["id"] != "mozes-voorbeden-voor-israel"
        and item["id"] not in mozes_ids
    ]
    items.extend(mozes)
    items.extend(psalm_item(number, existing) for number in GEBEDSPSALMEN)
    items = [item for _, item in sorted(enumerate(items), key=lambda pair: sort_key(pair[1], pair[0]))]
    source["items"] = items
    return source


def main() -> None:
    catalogus = build()
    TARGET.write_text(json.dumps(catalogus, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"gebedencatalogus gebouwd: {len(catalogus['items'])} gebeden")


if __name__ == "__main__":
    main()
