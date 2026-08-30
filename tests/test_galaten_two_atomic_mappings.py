import json
import re
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CHAPTER = ROOT / "data" / "galaten" / "2.json"
REVIEW = ROOT / "data" / "woordnummers-review" / "galaten-2.json"
GROUND_SHA = "C5CA7EBAFCCC9B97A198F58C4F17102538CF97004A6F8DAE779270A25FFC3E2D"


def _data():
    chapter = json.loads(CHAPTER.read_text(encoding="utf-8"))
    review = json.loads(REVIEW.read_text(encoding="utf-8"))
    verses = {verse["number"]: verse for verse in chapter["verses"]}
    reviewed = {verse["verse"]: verse for verse in review["books"][0]["verses"]}
    return review, verses, reviewed


def _matches(text, target):
    pattern = rf"(?<!\w){re.escape(target)}(?!\w)"
    return list(re.finditer(pattern, text, flags=re.IGNORECASE | re.UNICODE))


def test_galatians_two_pins_and_full_ground_coverage():
    review, verses, reviewed = _data()
    assert review["source"]["sha256"] == "B174BEE2C87B305DB86862D810BE20B77706C7A87E2298147E7FC90C5D17A7C3"
    assert review["grondtekst_bron"]["sha256"] == "6D4A37FDC317AB54A38876425267F98A691FCA6FDD2E7CF10098281C7B1BEF75"
    assert review["grondtekst_bron"]["lokale_grondtekst_sha256"] == GROUND_SHA
    assert sorted(verses) == list(range(1, 22))
    assert sorted(reviewed) == list(range(1, 22))

    for number, verse in verses.items():
        reviewed_verse = reviewed[number]
        covered = [
            index
            for mapping in reviewed_verse["mappings"]
            for index in mapping["grondindices"]
        ]
        covered += [
            index
            for item in reviewed_verse.get("ongemapt", [])
            for index in item["grondindices"]
        ]
        assert Counter(covered) == Counter(range(len(verse["grondtekst"])))


def test_galatians_two_review_is_atomic_and_fully_manual():
    _, _, reviewed = _data()
    mappings = [mapping for verse in reviewed.values() for mapping in verse["mappings"]]
    assert len(mappings) == 379
    assert sum(len(mapping["grondindices"]) for mapping in mappings) == 383
    assert max(len(mapping["grondindices"]) for mapping in mappings) <= 2
    assert max(len(mapping["tekst"].split()) for mapping in mappings) <= 4
    assert all(mapping["confidence"] == 1 for mapping in mappings)
    assert all(mapping["reviewstatus"] == "handmatig_gecontroleerd" for mapping in mappings)
    assert "voorstel_" not in REVIEW.read_text(encoding="utf-8")


def test_galatians_two_targets_and_empty_anchors_are_explicitly_reachable():
    _, verses, reviewed = _data()
    for number, reviewed_verse in reviewed.items():
        text = verses[number]["text2026"]
        for mapping in reviewed_verse["mappings"]:
            target = mapping["tekst"] or mapping["anker"]
            matches = _matches(text, target)
            assert matches, (number, target)
            occurrence = mapping.get("voorkomen", 1)
            assert 1 <= occurrence <= len(matches), (number, target, occurrence)
            if len(matches) > 1:
                assert "voorkomen" in mapping, (number, target, len(matches))
