import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_handeling_four_jerusalem_tokens_belong_to_verse_five():
    chapter = json.loads(
        (ROOT / "data" / "handelingen" / "4.json").read_text(encoding="utf-8")
    )
    verses = chapter["verses"]

    assert len(verses) == 37
    assert sum(len(verse.get("grondtekst", [])) for verse in verses) == 685
    assert [token["strongs"] for token in verses[4]["grondtekst"][-2:]] == [
        "G1519",
        "G2419",
    ]
    assert verses[5]["grondtekst"][0]["strongs"] == "G2532"


def test_handeling_four_apostles_feet_tokens_belong_to_verse_thirty_four():
    chapter = json.loads(
        (ROOT / "data" / "handelingen" / "4.json").read_text(encoding="utf-8")
    )
    verses = chapter["verses"]

    assert [token["strongs"] for token in verses[33]["grondtekst"][-7:]] == [
        "G2532",
        "G5087",
        "G3844",
        "G3588",
        "G4228",
        "G3588",
        "G652",
    ]
    assert verses[34]["grondtekst"][0]["strongs"] == "G1239"
