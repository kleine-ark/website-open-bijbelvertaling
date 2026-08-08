"""Regressietests voor de resterende lezersmeldingen bij Numeri 1–20."""

import html
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def verse(chapter, number):
    data = json.loads(
        (ROOT / "data" / "numeri" / f"{chapter}.json").read_text(encoding="utf-8")
    )
    return next(item for item in data["verses"] if item["number"] == number)


def visible_text(markup):
    markup = re.sub(r"<sup\b[^>]*>.*?</sup>", "", markup, flags=re.IGNORECASE)
    return html.unescape(re.sub(r"<[^>]+>", "", markup)).strip()


def test_numeri_2_3_gebruikt_kamp_opslaan_in_plaats_van_legeren():
    item = verse(2, 3)

    assert "zullen hun kamp opslaan" in item["text2026"]
    assert "legeren" not in item["text2026"]


def test_numeri_3_1_html_loopt_gelijk_met_de_nagekeken_tekst():
    item = verse(3, 1)

    assert "afstammelingen" in item["text2026_html"]
    assert "geboorten" not in item["text2026_html"]
    assert visible_text(item["text2026_html"]) == item["text2026"]


def test_numeri_5_4_is_geen_rechtstreeks_citaat_van_god():
    assert "god-speaks" not in verse(5, 4)["text2026_html"]


def test_numeri_8_3_en_8_4_zijn_geen_rechtstreeks_citaat_van_god():
    assert "god-speaks" not in verse(8, 3)["text2026_html"]
    assert "god-speaks" not in verse(8, 4)["text2026_html"]
