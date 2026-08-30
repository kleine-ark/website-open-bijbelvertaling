import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CHAPTER = ROOT / "data" / "galaten" / "5.json"
FLAT_SHA = "261E7FBCB652ED23A7A7E42707CACE1E5FD141128702FB01C6D9A2869B4AB8FB"


def _data():
    return json.loads(CHAPTER.read_text(encoding="utf-8"))


def test_galatians_five_keeps_every_ground_token_in_source_order():
    chapter = _data()
    flat = [token for verse in chapter["verses"] for token in verse.get("grondtekst", [])]
    serialized = json.dumps(
        flat, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    assert len(flat) == 318
    assert hashlib.sha256(serialized).hexdigest().upper() == FLAT_SHA


def test_galatians_five_places_the_last_two_fruits_in_verse_22():
    verses = {verse["number"]: verse for verse in _data()["verses"]}
    assert [token["strongs"] for token in verses[22]["grondtekst"][-3:]] == [
        "G4102", "G4240", "G1466"
    ]
    assert [token["strongs"] for token in verses[23]["grondtekst"][:3]] == [
        "G2596", "G3588", "G5108"
    ]
