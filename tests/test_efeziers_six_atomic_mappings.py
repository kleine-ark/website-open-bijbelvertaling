import json
import re
from collections import Counter
from pathlib import Path

from scripts.import_inline_woordnummers import _grondtekst_sha256


ROOT = Path(__file__).resolve().parents[1]
CHAPTER = ROOT / "data" / "efeziers" / "6.json"
REVIEW = ROOT / "data" / "woordnummers-review" / "efeziers-6.json"
GROUND_SHA = "CDBAD6FA7C670A155FE1C9935B4BBADBEDBB0402E822E79343958E548C00CAFD"
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


def test_ephesians_six_pins_and_complete_ground_coverage():
    chapter, review, verses, reviewed = _data()
    assert _grondtekst_sha256(chapter) == GROUND_SHA
    assert review["source"]["sha256"] == GUIDE_SHA
    assert review["grondtekst_bron"]["sha256"] == TR_SHA
    assert review["grondtekst_bron"]["lokale_grondtekst_sha256"] == GROUND_SHA
    assert sorted(verses) == list(range(1, 25))
    assert sorted(reviewed) == list(range(1, 25))

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


def test_ephesians_six_review_is_atomic_manual_and_reachable():
    _, _, verses, reviewed = _data()
    mappings = [mapping for verse in reviewed.values() for mapping in verse["mappings"]]
    assert len(mappings) == 333
    assert sum(len(mapping["grondindices"]) for mapping in mappings) == 402
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


def test_ephesians_six_documents_all_guide_tr_differences():
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
        6: [(["G5547"], ["G3588", "G5547"])],
        8: [(["G5100"], ["G3739", "G5100"]), (["G2962"], ["G3588", "G2962"])],
        9: [(["G2532", "G2532"], ["G2532"])],
        10: [(["G3588", "G3064"], ["G3588", "G3063"]), ([], ["G80"]), ([], ["G1473"])],
        12: [([], ["G3588", "G165"])],
        16: [(["G1722", "G3956"], ["G1909", "G3956"])],
        18: [(["G846"], ["G846", "G3778"])],
        24: [([], ["G281"])],
    }


def test_ephesians_six_keeps_critical_reordered_tokens_on_the_right_words():
    _, _, _, reviewed = _data()

    def mapping(verse, ground_indices):
        return next(
            item
            for item in reviewed[verse]["mappings"]
            if item["grondindices"] == ground_indices
        )

    assert mapping(7, [3]) | {"confidence": 1, "reviewstatus": "handmatig_gecontroleerd"} == mapping(7, [3])
    assert mapping(7, [3])["tekst"] == ""
    assert mapping(7, [3])["anker"] == "Heere"
    assert mapping(9, [13])["bronindices"] == [13, 17]
    assert mapping(10, [11, 13])["tekst"] == "Zijn"
    assert mapping(10, [11, 13])["bronindices"] == [9, 8]
    assert mapping(16, [9])["tekst"] == "kunnen"
    assert mapping(18, [6])["tekst"] == ""
    assert mapping(18, [6])["anker"] == "altijd"
    assert mapping(19, [4]) == mapping(19, [4]) | {"tekst": "mij", "voorkomen": 2, "bronindices": [11]}
    assert mapping(19, [11]) == mapping(19, [11]) | {"tekst": "mijn", "bronindices": [7]}
    assert mapping(21, [5])["bronindices"] == [17]
    assert mapping(21, [14, 15])["bronindices"] == [1, 2]
    assert mapping(24, [6, 8])["bronindices"] == [7, 6]


def test_ephesians_six_publishes_every_link_at_an_atomic_target():
    chapter = json.loads(CHAPTER.read_text(encoding="utf-8"))
    inline = json.loads((ROOT / "data" / "woordnummers-inline" / "efeziers.json").read_text(encoding="utf-8"))
    inline_verses = inline["chapters"]["6"]

    for verse in chapter["verses"]:
        embedded = verse["woordnummers"]
        projected = inline_verses[str(verse["number"])]
        expected = len(verse["grondtekst"])
        for mappings in (embedded, projected):
            assert sum(len(mapping["strongs"]) for mapping in mappings) == expected
            assert not any(mapping.get("tekst", "").strip() == verse["text2026"].strip() for mapping in mappings)

    assert sum(len(verse["woordnummers"]) for verse in chapter["verses"]) == 333
    assert sum(len(items) for items in inline_verses.values()) == 333
