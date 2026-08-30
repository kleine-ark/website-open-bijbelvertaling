import json
import re
from collections import Counter
from pathlib import Path

from scripts.import_inline_woordnummers import _grondtekst_sha256


ROOT = Path(__file__).resolve().parents[1]
CHAPTER = ROOT / "data" / "efeziers" / "2.json"
REVIEW = ROOT / "data" / "woordnummers-review" / "efeziers-2.json"
GROUND_SHA = "BDB3E4DDE12B71A9C0931D080C35C3F1C14040AD4FCBF13EF3C656BF92D7BCEB"
GUIDE_SHA = "6FAE4C585DE1D229E8F9A2E01722C995B9CA96B10902BC1EB264E4144D9CDF7F"
TR_SHA = "BC2D3631DE9B311C03BCFAED5D1B4F0C1E6DF4812C852FF54B3274AC03A7A0D1"


def _data():
    chapter = json.loads(CHAPTER.read_text(encoding="utf-8"))
    review = json.loads(REVIEW.read_text(encoding="utf-8"))
    verses = {verse["number"]: verse for verse in chapter["verses"]}
    reviewed = {verse["verse"]: verse for verse in review["books"][0]["verses"]}
    return chapter, review, verses, reviewed


def _matches(text, target):
    pattern = rf"(?<!\w){re.escape(target)}(?!\w)"
    return list(re.finditer(pattern, text, flags=re.IGNORECASE | re.UNICODE))


def test_ephesians_two_pins_and_complete_ground_coverage():
    chapter, review, verses, reviewed = _data()
    assert _grondtekst_sha256(chapter) == GROUND_SHA
    assert review["source"]["sha256"] == GUIDE_SHA
    assert review["grondtekst_bron"]["sha256"] == TR_SHA
    assert review["grondtekst_bron"]["lokale_grondtekst_sha256"] == GROUND_SHA
    assert sorted(verses) == list(range(1, 23))
    assert sorted(reviewed) == list(range(1, 23))

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


def test_ephesians_two_review_is_atomic_manual_and_reachable():
    _, _, verses, reviewed = _data()
    mappings = [mapping for verse in reviewed.values() for mapping in verse["mappings"]]
    assert len(mappings) == 358
    assert sum(len(mapping["grondindices"]) for mapping in mappings) == 362
    assert max(len(mapping["grondindices"]) for mapping in mappings) == 2
    assert sorted(
        (verse, mapping["tekst"], mapping["grondindices"])
        for verse, record in reviewed.items()
        for mapping in record["mappings"]
        if len(mapping["grondindices"]) == 2
    ) == [
        (3, "Waaronder", [0, 1]),
        (9, "niemand", [4, 5]),
        (10, "daarin", [16, 17]),
        (15, "Zijn", [3, 5]),
    ]
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

    assert {
        tuple(mapping["grondindices"]): (mapping["tekst"], mapping["voorkomen"])
        for mapping in reviewed[8]["mappings"]
        if mapping["grondindices"] in ([12], [14])
    } == {tuple([12]): ("u", 2), tuple([14]): ("het", 2)}
    assert {
        tuple(mapping["grondindices"]): (mapping["tekst"], mapping["voorkomen"])
        for mapping in reviewed[10]["mappings"]
        if mapping["grondindices"] in ([0], [2])
    } == {tuple([0]): ("Zijn", 2), tuple([2]): ("zijn", 1)}


def test_ephesians_two_documents_all_guide_tr_differences():
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
        1: [(["G4771", "G3900"], ["G3900"])],
        8: [([], ["G3588"])],
        12: [([], ["G1722"])],
        14: [(["G5418", "G3588", "G2189"], ["G5418"])],
        15: [([], ["G3588"]), ([], ["G2189"]), (["G848"], ["G1438"])],
        17: [(["G1515", "G3588"], ["G3588"])],
        19: [(["G1510", "G4847"], ["G4847"])],
        21: [([], ["G3588"])],
    }
