import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CHAPTER = ROOT / "data" / "lukas" / "23.json"


def _verses():
    data = json.loads(CHAPTER.read_text(encoding="utf-8"))
    return {int(verse["number"]): verse for verse in data["verses"]}


def test_lukas_23_keeps_all_ground_tokens():
    verses = _verses()
    assert sum(len(verse["grondtekst"]) for verse in verses.values()) == 879


def test_lukas_23_moves_said_to_them_to_visible_verse_13():
    verses = _verses()
    assert [token["woord"] for token in verses[13]["grondtekst"][-3:]] == [
        "ειπεν",
        "προς",
        "αυτους",
    ]
    assert [token["strongs"] for token in verses[13]["grondtekst"][-3:]] == [
        "G3004",
        "G4314",
        "G846",
    ]


def test_lukas_23_visible_verse_14_starts_with_brought():
    verses = _verses()
    assert verses[14]["grondtekst"][0]["woord"] == "προσηνεγκατε"
    assert verses[14]["grondtekst"][0]["strongs"] == "G4374"
    assert len(verses[13]["grondtekst"]) == 14
    assert len(verses[14]["grondtekst"]) == 26
