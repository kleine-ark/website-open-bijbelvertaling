"""Regressies voor de menselijke review van Jozua en Richteren 1-7."""

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def vers(boek: str, hoofdstuk: int, nummer: int) -> dict:
    data = json.loads(
        (ROOT / "data" / boek / f"{hoofdstuk}.json").read_text(encoding="utf-8")
    )
    return next(item for item in data["verses"] if item["number"] == nummer)


def assert_tekst(boek: str, hoofdstuk: int, nummer: int, verwacht: str) -> None:
    item = vers(boek, hoofdstuk, nummer)
    assert verwacht in item["text2026"]
    zichtbare_html = re.sub(r"<sup[^>]*>.*?</sup>|<[^>]+>", "", item["text2026_html"])
    assert verwacht in zichtbare_html


def test_opgegeven_correcties_in_jozua():
    controles = {
        (3, 13): "van boven afvloeien",
        (3, 16): "aan de kant van Sarthan",
        (3, 17): "stonden onbeweeglijk op het droge",
        (4, 3): "stelt ze in het kamp",
        (4, 4): "uit de Israëlieten had aangesteld",
        (4, 10): "totdat alle dingen voltooid waren, die JAHWEH",
        (9, 2): "om eenmoedig tegen Jozua en tegen Israël te strijden",
        (9, 14): "maar zij baden JAHWEH niet om raad",
        (10, 26): "hing ze aan vijf palen",
        (10, 27): "van de palen afname",
        (11, 6): "zal Ik hen allen verslagen geven",
        (15, 19): "geef mij ook bronnen",
        (17, 14): "maar een lot en een deel gegeven",
        (20, 9): "een ziel slaat zonder opzet",
    }
    for (hoofdstuk, nummer), verwacht in controles.items():
        assert_tekst("jozua", hoofdstuk, nummer, verwacht)

    item_10_27 = vers("jozua", 10, 27)
    assert "waar zij verborgen geweest waren" in item_10_27["text2026"]
    assert "alwaar" not in item_10_27["text2026"]

    item_24_2 = vers("jozua", 24, 2)
    assert "[namelijk]" not in item_24_2["text2026"]
    assert "[namelijk]" not in item_24_2["text2026_html"]
    assert '<span class="direct-speech"><i>Zo zegt JAHWEH' in item_24_2["text2026_html"]


def test_opgegeven_correcties_in_richteren():
    controles = {
        (1, 15): "geef mij ook bronnen",
        (5, 5): "De bergen vloeiden weg van het aangezicht",
        (5, 29): "Haar meest wijze vorstinnen antwoordden haar",
        (6, 19): "koeken van een efa meel",
        (6, 21): "de Engel van JAHWEH verdween uit zijn ogen",
        (7, 3): "Wie bevreesd is en beeft",
    }
    for (hoofdstuk, nummer), verwacht in controles.items():
        assert_tekst("richteren", hoofdstuk, nummer, verwacht)


def test_reuzentag_bevat_de_drie_opgegeven_jozuaverzen():
    tags = json.loads((ROOT / "data" / "tags.json").read_text(encoding="utf-8"))
    reuzen = next(tag for tag in tags["tags"] if tag["id"] == "reuzen")
    refs = {item["ref"] for item in reuzen["verzen"]}
    assert {"jozua 12:5", "jozua 13:12", "jozua 14:12"} <= refs


def test_waarheidstag_bevat_de_bijbelse_verkenners_en_spionnen():
    tags = json.loads((ROOT / "data" / "tags.json").read_text(encoding="utf-8"))
    waarheid = next(tag for tag in tags["tags"] if tag["id"] == "waarheid-en-levensgevaar")
    refs = {item["ref"] for item in waarheid["verzen"]}
    verwacht = {
        "genesis 42:9", "genesis 42:11", "genesis 42:14", "genesis 42:16",
        "genesis 42:30", "genesis 42:31", "genesis 42:34",
        "numeri 13:2", "numeri 13:16", "numeri 13:17", "numeri 13:21",
        "numeri 13:25", "numeri 13:32", "numeri 14:6", "numeri 14:7",
        "numeri 14:34", "numeri 14:36", "numeri 14:38", "numeri 21:32",
        "deuteronomium 1:22", "deuteronomium 1:23", "deuteronomium 1:24",
        "deuteronomium 1:25", "jozua 2:1", "jozua 2:14", "jozua 2:16",
        "jozua 2:22", "jozua 2:23", "jozua 2:24", "jozua 6:22",
        "jozua 6:23", "jozua 6:25", "jozua 14:7", "richteren 1:23",
        "richteren 1:24", "richteren 1:25", "richteren 18:2",
        "richteren 18:14", "richteren 18:17", "1samuel 26:4",
        "2samuel 10:3", "2samuel 15:10", "1kronieken 19:3",
        "lukas 20:20", "galaten 2:4", "hebreeen 11:31",
    }
    assert verwacht <= refs
    assert len(refs) == len(waarheid["verzen"])
