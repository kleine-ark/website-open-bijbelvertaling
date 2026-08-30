import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CHAPTER = ROOT / "data" / "1korinthiers" / "6.json"


def _chapter():
    return json.loads(CHAPTER.read_text(encoding="utf-8"))


def test_dwaal_niet_begins_the_local_tenth_verse():
    verses = {verse["number"]: verse for verse in _chapter()["verses"]}

    verse_nine = verses[9]["grondtekst"]
    verse_ten = verses[10]["grondtekst"]

    assert len(verse_nine) == 9
    assert verse_nine[-1]["woord"] == "κληρονομησουσιν"
    assert [token["woord"] for token in verse_ten[:2]] == ["μη", "πλανασθε"]
    assert len(verse_ten) == 26


def test_chapter_keeps_all_346_ground_tokens_after_boundary_repair():
    ground = [
        token
        for verse in _chapter()["verses"]
        for token in verse.get("grondtekst", [])
    ]

    assert len(ground) == 346
    assert ground[0]["woord"] == "τολμα"
    assert ground[-1]["woord"] == "θεου"
