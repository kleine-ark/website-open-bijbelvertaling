"""Regressies voor tekstpunten die in de overdracht bewust openbleven."""

import html
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def verse(book: str, chapter: int, number: int) -> dict:
    data = json.loads(
        (ROOT / "data" / book / f"{chapter}.json").read_text(encoding="utf-8")
    )
    return next(item for item in data["verses"] if item["number"] == number)


def visible_text(markup: str) -> str:
    markup = re.sub(r"<sup\b[^>]*>.*?</sup>", "", markup, flags=re.IGNORECASE)
    return html.unescape(re.sub(r"<[^>]+>", "", markup)).strip()


def assert_both_layers(book: str, chapter: int, number: int, expected: str) -> None:
    item = verse(book, chapter, number)
    assert expected in item["text2026"]
    assert expected in visible_text(item["text2026_html"])


def test_genesis_1_28_heeft_een_consequente_moderne_gebiedende_wijs():
    assert_both_layers(
        "genesis",
        1,
        28,
        "Wees vruchtbaar, en vermenigvuldig, en vervul de aarde, en onderwerp haar, en heb heerschappij",
    )


def test_opengebleven_naamvalsconstructies_zijn_modern_nederlands():
    assert_both_layers("spreuken", 16, 4, "JAHWEH heeft alles gewerkt voor Zichzelf")
    assert_both_layers("johannes", 4, 42, "Wij geloven niet meer vanwege wat u zei")
    assert_both_layers("job", 12, 16, "van Hem zijn de dwalende, en die doet dwalen")


def test_leviticus_21_10_verklaart_de_oude_ambtsuitdrukking():
    assert_both_layers("leviticus", 21, 10, "die men in zijn ambt heeft bevestigd")


def test_de_vijf_genoteerde_ter_constructies_zijn_opgelost():
    verouderd = {
        "ter oren",
        "ter vrouwe",
        "ter middernacht",
        "ter dodenrijk",
        "ter gevangenis",
    }
    gevonden = []
    for chapter_path in (ROOT / "data").glob("*/*.json"):
        try:
            chapter = json.loads(chapter_path.read_text(encoding="utf-8-sig"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            continue
        if not isinstance(chapter, dict) or not isinstance(chapter.get("verses"), list):
            continue
        for item in chapter["verses"]:
            if not isinstance(item, dict):
                continue
            text = (item.get("text2026") or "").lower()
            for phrase in verouderd:
                if phrase in text:
                    gevonden.append(
                        f"{chapter_path.parent.name} {chapter_path.stem}:"
                        f"{item.get('number')} — {phrase}"
                    )

    assert not gevonden, gevonden
