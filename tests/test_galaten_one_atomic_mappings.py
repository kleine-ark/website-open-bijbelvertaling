import json
import re
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CHAPTER = ROOT / "data" / "galaten" / "1.json"
REVIEW = ROOT / "data" / "woordnummers-review" / "galaten-1.json"


def _data():
    chapter = json.loads(CHAPTER.read_text(encoding="utf-8"))
    review = json.loads(REVIEW.read_text(encoding="utf-8"))["books"][0]
    verses = {verse["number"]: verse for verse in chapter["verses"]}
    reviewed = {verse["verse"]: verse for verse in review["verses"]}
    return verses, reviewed


def _matches(text, target):
    pattern = rf"(?<!\w){re.escape(target)}(?!\w)"
    return list(re.finditer(pattern, text, flags=re.IGNORECASE | re.UNICODE))


def test_every_galatians_one_ground_token_is_covered_once():
    verses, reviewed = _data()
    assert sorted(verses) == list(range(1, 25))
    assert sorted(reviewed) == list(range(1, 25))

    for number, verse in verses.items():
        review = reviewed[number]
        covered = [
            index
            for mapping in review["mappings"]
            for index in mapping["grondindices"]
        ]
        covered += [
            index
            for item in review.get("ongemapt", [])
            for index in item["grondindices"]
        ]
        assert Counter(covered) == Counter(range(len(verse["grondtekst"])))


def test_review_is_atomic_and_fully_manual():
    _, reviewed = _data()
    mappings = [mapping for verse in reviewed.values() for mapping in verse["mappings"]]
    assert len(mappings) == 361
    assert sum(len(mapping["grondindices"]) for mapping in mappings) == 364
    assert max(len(mapping["grondindices"]) for mapping in mappings) <= 2
    assert max(len(mapping["tekst"].split()) for mapping in mappings) <= 4
    assert all(mapping["confidence"] == 1 for mapping in mappings)
    assert all(mapping["reviewstatus"] == "handmatig_gecontroleerd" for mapping in mappings)
    assert "voorstel_" not in REVIEW.read_text(encoding="utf-8")


def test_every_visible_target_and_empty_anchor_is_reachable_and_explicit():
    verses, reviewed = _data()
    for number, review in reviewed.items():
        text = verses[number]["text2026"]
        for mapping in review["mappings"]:
            target = mapping["tekst"] or mapping["anker"]
            matches = _matches(text, target)
            assert matches, (number, target)
            occurrence = mapping.get("voorkomen", 1)
            assert 1 <= occurrence <= len(matches), (number, target, occurrence)
            if len(matches) > 1:
                assert "voorkomen" in mapping, (number, target, len(matches))
