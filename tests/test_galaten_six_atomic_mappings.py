import json
import re
from collections import Counter
from pathlib import Path

from scripts.import_inline_woordnummers import _grondtekst_sha256


ROOT = Path(__file__).resolve().parents[1]
CHAPTER = ROOT / "data" / "galaten" / "6.json"
REVIEW = ROOT / "data" / "woordnummers-review" / "galaten-6.json"
GROUND_SHA = "B4167DF81ACE4F27E4D0F609BC17FA21F380C28763647BAC139F3AF6A5DFE910"
GUIDE_SHA = "B174BEE2C87B305DB86862D810BE20B77706C7A87E2298147E7FC90C5D17A7C3"
TR_SHA = "6D4A37FDC317AB54A38876425267F98A691FCA6FDD2E7CF10098281C7B1BEF75"


def _data():
    chapter = json.loads(CHAPTER.read_text(encoding="utf-8"))
    review = json.loads(REVIEW.read_text(encoding="utf-8"))
    verses = {verse["number"]: verse for verse in chapter["verses"]}
    reviewed = {verse["verse"]: verse for verse in review["books"][0]["verses"]}
    return chapter, review, verses, reviewed


def _matches(text, target):
    pattern = rf"(?<!\w){re.escape(target)}(?!\w)"
    return list(re.finditer(pattern, text, flags=re.IGNORECASE | re.UNICODE))


def test_galatians_six_pins_and_complete_ground_coverage():
    chapter, review, verses, reviewed = _data()
    assert _grondtekst_sha256(chapter) == GROUND_SHA
    assert review["source"]["sha256"] == GUIDE_SHA
    assert review["grondtekst_bron"]["sha256"] == TR_SHA
    assert review["grondtekst_bron"]["lokale_grondtekst_sha256"] == GROUND_SHA
    assert sorted(verses) == list(range(1, 19))
    assert sorted(reviewed) == list(range(1, 19))

    for number, verse in verses.items():
        record = reviewed[number]
        covered = [
            index
            for mapping in record["mappings"]
            for index in mapping["grondindices"]
        ]
        covered += [
            index
            for item in record.get("ongemapt", [])
            for index in item["grondindices"]
        ]
        assert Counter(covered) == Counter(range(len(verse["grondtekst"])))


def test_galatians_six_review_is_atomic_manual_and_reachable():
    _, _, verses, reviewed = _data()
    mappings = [mapping for verse in reviewed.values() for mapping in verse["mappings"]]
    assert len(mappings) == 270
    assert sum(len(mapping["grondindices"]) for mapping in mappings) == 272
    assert max(len(mapping["grondindices"]) for mapping in mappings) == 2
    assert sorted(
        (verse, mapping["tekst"], mapping["grondindices"])
        for verse, record in reviewed.items()
        for mapping in record["mappings"]
        if len(mapping["grondindices"]) == 2
    ) == [(16, "daarover", [7, 8]), (17, "Verder", [0, 1])]
    assert max(len((mapping.get("tekst") or mapping["anker"]).split()) for mapping in mappings) <= 3
    assert all(mapping["confidence"] == 1 for mapping in mappings)
    assert all(mapping["reviewstatus"] == "handmatig_gecontroleerd" for mapping in mappings)
    assert "voorstel_" not in REVIEW.read_text(encoding="utf-8")

    for number, record in reviewed.items():
        text = verses[number]["text2026"]
        for mapping in record["mappings"]:
            target = mapping.get("tekst") or mapping["anker"]
            matches = _matches(text, target)
            assert matches, (number, target)
            occurrence = mapping.get("voorkomen", 1)
            assert 1 <= occurrence <= len(matches), (number, target, occurrence)
            if len(matches) > 1:
                assert "voorkomen" in mapping, (number, target, len(matches))


def test_galatians_six_documents_all_guide_tr_differences():
    _, _, _, reviewed = _data()

    assert reviewed[14]["bronafwijkingen"][0]["grondtekst_strongs"] == ["G3588"]
    assert [
        item["grondtekst_strongs"] for item in reviewed[15]["bronafwijkingen"]
    ] == [["G1722"], ["G5547"], ["G2424"], ["G2480"]]
    assert reviewed[17]["bronafwijkingen"][0]["grondtekst_strongs"] == ["G2962"]

    strength = next(
        mapping
        for mapping in reviewed[15]["mappings"]
        if mapping["tekst"] == "kracht"
    )
    assert strength["bronindices"] == [5]
    assert strength["grondindices"] == [7]
