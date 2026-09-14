import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KLEIN = re.compile(r"(?<![\wÀ-ÿ'])(u|uw|uwe|uzelf)(?![\wÀ-ÿ'])")


def zichtbaar(boek, hoofdstuk, nummer):
    data = json.loads((ROOT / "data" / boek / f"{hoofdstuk}.json").read_text(encoding="utf-8"))
    html = next(item for item in data["verses"] if item["number"] == nummer)["text2026_html"]
    return re.sub(r"<[^>]+>", "", re.sub(r"<sup[^>]*>.*?</sup>", "", html))


def test_in_de_gebeden_staat_god_met_hoofdletter():
    for boek, hoofdstuk, nummer, fragment in (
        ("4ezra", 3, 4, "O heersende Heere, U hebt van de beginne gesproken"),
        ("4ezra", 3, 23, "U verwekte voor Uzelf een knecht"),
        ("4ezra", 9, 29, "toen U Uzelf ons vertoonde"),
        ("3ezra", 8, 88, "Want U, Heere, die onze zonden hebt verlicht"),
        ("tobit", 3, 2, "Heere, U bent rechtvaardig, en al Uw wegen"),
        ("estherapocrief", 14, 4, "Heere, U bent alleen onze Koning"),
        ("jezussirach", 36, 14, "Ontferm U over Uw volk, Heere"),
        ("boekderwijsheid", 15, 2, "wij zijn Uw"),
        ("2makkabeeen", 1, 25, "U die alleen milddadig bent"),
        ("belenddedraak", 1, 37, "U gedenkt mij dan Heere"),
    ):
        tekst = zichtbaar(boek, hoofdstuk, nummer)
        assert fragment in tekst, f"{boek} {hoofdstuk}:{nummer}"
        assert not KLEIN.search(tekst), f"{boek} {hoofdstuk}:{nummer}: {KLEIN.findall(tekst)}"


def test_wie_niet_god_is_houdt_de_kleine_letter():
    assert "Wat slaat u ons" in zichtbaar("tobit", 3, 11)
    assert "zult u uw dochters niet geven" in zichtbaar("3ezra", 8, 85)
    assert "Ik zaai Mijn wet in u" in zichtbaar("4ezra", 9, 31)
    assert "Jeruzalem, u heilige stad" in zichtbaar("tobit", 13, 10)
    assert "Ik bid u Heere" in zichtbaar("4ezra", 4, 22)
