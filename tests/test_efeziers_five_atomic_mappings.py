import json
import re
from collections import Counter
from pathlib import Path

from scripts.import_inline_woordnummers import _grondtekst_sha256


ROOT = Path(__file__).resolve().parents[1]
CHAPTER = ROOT / "data" / "efeziers" / "5.json"
REVIEW = ROOT / "data" / "woordnummers-review" / "efeziers-5.json"
GROUND_SHA = "46199E2DFB52811F8C7266213FE1328D5DDC32A0C0E402E9AEA8ECFE21999886"
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


def test_ephesians_five_pins_and_complete_ground_coverage():
    chapter, review, verses, reviewed = _data()
    assert _grondtekst_sha256(chapter) == GROUND_SHA
    assert review["source"]["sha256"] == GUIDE_SHA
    assert review["grondtekst_bron"]["sha256"] == TR_SHA
    assert review["grondtekst_bron"]["lokale_grondtekst_sha256"] == GROUND_SHA
    assert sorted(verses) == list(range(1, 34))
    assert sorted(reviewed) == list(range(1, 34))

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


def test_ephesians_five_review_is_atomic_manual_and_reachable():
    _, _, verses, reviewed = _data()
    mappings = [mapping for verse in reviewed.values() for mapping in verse["mappings"]]
    assert len(mappings) == 456
    assert sum(len(mapping["grondindices"]) for mapping in mappings) == 472
    assert max(len(mapping["grondindices"]) for mapping in mappings) == 2
    assert sorted(
        (verse, mapping.get("tekst") or "<leeg>", mapping.get("anker", ""), mapping["grondindices"])
        for verse, record in reviewed.items()
        for mapping in record["mappings"]
        if len(mapping["grondindices"]) > 1
    ) == [
        (2, "Christus", "", [6, 7]),
        (2, "God", "", [18, 19]),
        (14, "Christus", "", [13, 14]),
        (17, "Daarom", "", [0, 1]),
        (18, "waarin", "", [4, 5]),
        (20, "God", "", [11, 12]),
        (23, "Christus", "", [9, 10]),
        (25, "Christus", "", [8, 9]),
        (27, "dergelijks", "", [14, 15]),
        (30, "Zijn", "", [3, 5]),
        (30, "Zijn", "", [7, 9]),
        (30, "Zijn", "", [12, 14]),
        (31, "Daarom", "", [0, 1]),
        (31, "aanhangen", "", [11, 12]),
        (31, "zijn", "", [4, 6]),
        (31, "zijn", "", [13, 15]),
    ]
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


def test_ephesians_five_documents_all_guide_tr_differences():
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
        4: [(["G3739"], ["G3588"])],
        5: [(["G1492"], ["G1510"])],
        9: [(["G5457"], ["G4151"])],
        21: [(["G5547"], ["G2316"])],
        22: [([], ["G5293"])],
        23: [([], ["G3588"]), ([], ["G2532"]), ([], ["G1510"])],
        24: [(["G5613"], ["G5618"]), ([], ["G2398"])],
        25: [([], ["G1438"])],
        28: [(["G3779", "G2532"], ["G3779"])],
        29: [(["G5547"], ["G2962"])],
        30: [
            ([], ["G1537"]), ([], ["G3588", "G846"]), ([], ["G4561"]),
            ([], ["G2532"]), ([], ["G1537"]),
            ([], ["G3588", "G846"]), ([], ["G3747"]),
        ],
        31: [(["G3588"], ["G3588", "G846"])],
    }


def test_ephesians_five_publishes_every_link_at_an_atomic_target():
    chapter = json.loads(CHAPTER.read_text(encoding="utf-8"))
    inline = json.loads((ROOT / "data" / "woordnummers-inline" / "efeziers.json").read_text(encoding="utf-8"))
    inline_verses = inline["chapters"]["5"]

    for verse in chapter["verses"]:
        embedded = verse["woordnummers"]
        projected = inline_verses[str(verse["number"])]
        expected = len(verse["grondtekst"])
        for mappings in (embedded, projected):
            assert sum(len(mapping["strongs"]) for mapping in mappings) == expected
            assert not any(mapping.get("tekst", "").strip() == verse["text2026"].strip() for mapping in mappings)

    assert sum(len(verse["woordnummers"]) for verse in chapter["verses"]) == 456
    assert sum(len(items) for items in inline_verses.values()) == 456
