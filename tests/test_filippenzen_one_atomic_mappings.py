import json
import re
from collections import Counter
from pathlib import Path

from scripts.import_inline_woordnummers import _grondtekst_sha256


ROOT = Path(__file__).resolve().parents[1]
CHAPTER = ROOT / "data" / "filippenzen" / "1.json"
REVIEW = ROOT / "data" / "woordnummers-review" / "filippenzen-1.json"
INLINE = ROOT / "data" / "woordnummers-inline" / "filippenzen.json"
GROUND_SHA = "7DEB45807CA4003749461FA5C33F8F4E77F9AF704ADCBD0A035055AF5A23FA6E"
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


def test_philippians_one_pins_and_complete_ground_coverage():
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


def test_philippians_one_review_is_atomic_manual_and_reachable():
    _, _, verses, reviewed = _data()
    mappings = [mapping for verse in reviewed.values() for mapping in verse["mappings"]]
    assert len(mappings) == 447
    assert sum(len(mapping["grondindices"]) for mapping in mappings) == 499
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


def test_philippians_one_documents_guide_tr_differences():
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
        5: [(["G3588", "G4413"], ["G4413"])],
        7: [(["G1722", "G3588"], ["G3588"])],
        8: [([], ["G1510"])],
        16: [(["G1161"], ["G3303"]), (["G1453"], ["G2018"])],
        17: [(["G3303"], ["G1161"])],
        18: [(["G4133", "G3754"], ["G4133"]), (["G1722", "G3778"], ["G1722", "G5129"])],
        23: [(["G1161", "G1063"], ["G1063"])],
        25: [(["G3887"], ["G4839"])],
        28: [([], ["G3303"])],
    }


def test_philippians_one_keeps_verses_and_occurrences_semantically_aligned():
    _, _, _, reviewed = _data()

    def mapping(verse, ground_indices):
        return next(
            item
            for item in reviewed[verse]["mappings"]
            if item["grondindices"] == ground_indices
        )

    assert reviewed[16]["source_verse"] == 17
    assert reviewed[16]["vervang_bronreferentie"] == "PHP 1:16"
    assert reviewed[17]["source_verse"] == 16
    assert reviewed[17]["vervang_bronreferentie"] == "PHP 1:17"
    assert mapping(7, [12])["tekst"] == "ik"
    assert mapping(7, [12])["voorkomen"] == 2
    assert mapping(7, [23]) | {"tekst": "in", "voorkomen": 3, "bronindices": [23, 24]} == mapping(7, [23])
    assert mapping(16, [1])["bronindices"] == [1]
    assert mapping(16, [11])["bronindices"] == [10]
    assert mapping(18, [12, 13]) | {"tekst": "daarin", "bronindices": [13, 14]} == mapping(18, [12, 13])
    assert mapping(23, [1])["bronindices"] == [0, 18]
    assert mapping(25, [6])["voorkomen"] == 3
    assert mapping(25, [14])["voorkomen"] == 4
    assert mapping(27, [17])["voorkomen"] == 2
    assert mapping(28, [14])["voorkomen"] == 2
    assert mapping(29, [10])["voorkomen"] == 1
    assert mapping(29, [16])["voorkomen"] == 2


def test_philippians_one_publishes_every_link_at_an_atomic_target():
    chapter = json.loads(CHAPTER.read_text(encoding="utf-8"))
    inline = json.loads(INLINE.read_text(encoding="utf-8"))
    inline_verses = inline["chapters"]["1"]

    for verse in chapter["verses"]:
        embedded = verse["woordnummers"]
        projected = inline_verses[str(verse["number"])]
        expected = len(verse["grondtekst"])
        for mappings in (embedded, projected):
            assert sum(len(mapping["strongs"]) for mapping in mappings) == expected
            assert not any(mapping.get("tekst", "").strip() == verse["text2026"].strip() for mapping in mappings)

    assert sum(len(verse["woordnummers"]) for verse in chapter["verses"]) == 447
    assert sum(len(items) for items in inline_verses.values()) == 447
