import json
import re
from collections import Counter
from pathlib import Path

from scripts.import_inline_woordnummers import _grondtekst_sha256


ROOT = Path(__file__).resolve().parents[1]
CHAPTER = ROOT / "data" / "filippenzen" / "2.json"
REVIEW = ROOT / "data" / "woordnummers-review" / "filippenzen-2.json"
INLINE = ROOT / "data" / "woordnummers-inline" / "filippenzen.json"
GROUND_SHA = "D740FF23E3D2AC6DE8B2A20048EF3E201021DDE707C1B79147D0179773C36400"
GUIDE_SHA = "AA4B83FA5DEAAE7CD012AD92E02ED80DBB44CA78A783E828BC2B444414A172F9"
TR_SHA = "DF5C55B552DBF44460AE33E39CC0238F112049F67BA05B46F15303B5A496BD58"


def _data():
    chapter = json.loads(CHAPTER.read_text(encoding="utf-8"))
    review = json.loads(REVIEW.read_text(encoding="utf-8"))
    verses = {verse["number"]: verse for verse in chapter["verses"]}
    reviewed = {verse["verse"]: verse for verse in review["books"][0]["verses"]}
    return chapter, review, verses, reviewed


def _matches(text, target):
    pattern = rf"(?<!\w){re.escape(target)}(?!\w)"
    return list(re.finditer(pattern, text, flags=re.IGNORECASE | re.UNICODE))


def test_philippians_two_pins_and_complete_ground_coverage():
    chapter, review, verses, reviewed = _data()
    assert _grondtekst_sha256(chapter) == GROUND_SHA
    assert review["source"]["sha256"] == GUIDE_SHA
    assert review["grondtekst_bron"]["sha256"] == TR_SHA
    assert review["grondtekst_bron"]["lokale_grondtekst_sha256"] == GROUND_SHA
    assert sorted(verses) == list(range(1, 31))
    assert sorted(reviewed) == list(range(1, 31))

    for number, verse in verses.items():
        covered = [
            index
            for mapping in reviewed[number]["mappings"]
            for index in mapping["grondindices"]
        ]
        covered += [
            index
            for item in reviewed[number].get("ongemapt", [])
            for index in item["grondindices"]
        ]
        assert Counter(covered) == Counter(range(len(verse["grondtekst"])))


def test_philippians_two_review_is_atomic_manual_and_reachable():
    _, _, verses, reviewed = _data()
    mappings = [mapping for verse in reviewed.values() for mapping in verse["mappings"]]
    assert len(mappings) == 390
    assert sum(len(mapping["grondindices"]) for mapping in mappings) == 434
    assert max(len(mapping["grondindices"]) for mapping in mappings) == 2
    assert max(len((mapping.get("tekst") or mapping["anker"]).split()) for mapping in mappings) <= 2
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


def test_philippians_two_documents_guide_tr_differences():
    _, _, _, reviewed = _data()
    deviations = {
        number: [
            (item["bron_strongs"], item["grondtekst_strongs"])
            for item in record.get("bronafwijkingen", [])
        ]
        for number, record in reviewed.items()
        if record.get("bronafwijkingen")
    }
    assert deviations == {
        3: [(["G3366", "G2596"], ["G2228"])],
        5: [([], ["G1063"])],
        9: [(["G3588", "G3588", "G5228"], ["G3588", "G5228"])],
        13: [(["G2316"], ["G3588", "G2316"])],
        15: [(["G299"], ["G298"]), ([], ["G1722"])],
        21: [(["G5547"], ["G3588", "G5547"])],
        26: [(["G1510"], ["G2258"])],
        27: [(["G3441"], ["G3440"])],
        30: [(["G5547"], ["G3588", "G5547"])],
    }


def test_philippians_two_keeps_composita_and_occurrences_semantically_aligned():
    _, _, _, reviewed = _data()

    def mapping(verse, ground_indices):
        return next(
            item
            for item in reviewed[verse]["mappings"]
            if item["grondindices"] == ground_indices
        )

    assert mapping(3, [3]) | {"tekst": "of", "bronindices": [3, 4]} == mapping(3, [3])
    assert mapping(4, [1, 2])["bronindices"] == [4, 3]
    assert mapping(5, [1])["bronindices"] == []
    assert mapping(9, [10, 11])["bronindices"] == [9, 13, 11]
    assert mapping(13, [0, 1])["bronindices"] == [2]
    assert mapping(15, [7])["bronindices"] == [7]
    assert mapping(15, [8])["bronindices"] == []
    assert mapping(21, [8, 9])["bronindices"] == [9]
    assert [mapping(25, [index])["voorkomen"] for index in (6, 8, 12, 14)] == [1, 2, 3, 4]
    assert mapping(26, [2])["bronindices"] == [1]
    assert mapping(27, [13])["bronindices"] == [12]
    assert mapping(30, [4, 5])["bronindices"] == [7]


def test_philippians_two_publishes_every_link_at_an_atomic_target():
    chapter = json.loads(CHAPTER.read_text(encoding="utf-8"))
    inline = json.loads(INLINE.read_text(encoding="utf-8"))
    inline_verses = inline["chapters"]["2"]

    for verse in chapter["verses"]:
        embedded = verse["woordnummers"]
        projected = inline_verses[str(verse["number"])]
        expected = len(verse["grondtekst"])
        for mappings in (embedded, projected):
            assert sum(len(mapping["strongs"]) for mapping in mappings) == expected
            assert not any(mapping.get("tekst", "").strip() == verse["text2026"].strip() for mapping in mappings)

    assert sum(len(verse["woordnummers"]) for verse in chapter["verses"]) == 390
    assert sum(len(items) for items in inline_verses.values()) == 390
