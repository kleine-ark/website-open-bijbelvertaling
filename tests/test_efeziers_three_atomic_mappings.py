import json
import re
from collections import Counter
from pathlib import Path

from scripts.import_inline_woordnummers import _grondtekst_sha256


ROOT = Path(__file__).resolve().parents[1]
CHAPTER = ROOT / "data" / "efeziers" / "3.json"
REVIEW = ROOT / "data" / "woordnummers-review" / "efeziers-3.json"
GROUND_SHA = "D7F7DFCE3153A471BCF90458075A8FFD42BC90638E07743D2E1EDBC80CBF40CF"
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


def test_ephesians_three_pins_and_complete_ground_coverage():
    chapter, review, verses, reviewed = _data()
    assert _grondtekst_sha256(chapter) == GROUND_SHA
    assert review["source"]["sha256"] == GUIDE_SHA
    assert review["grondtekst_bron"]["sha256"] == TR_SHA
    assert review["grondtekst_bron"]["lokale_grondtekst_sha256"] == GROUND_SHA
    assert sorted(verses) == list(range(1, 22))
    assert sorted(reviewed) == list(range(1, 22))

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


def test_ephesians_three_review_is_atomic_manual_and_reachable():
    _, _, verses, reviewed = _data()
    mappings = [mapping for verse in reviewed.values() for mapping in verse["mappings"]]
    assert len(mappings) == 325
    assert sum(len(mapping["grondindices"]) for mapping in mappings) == 337
    assert max(len(mapping["grondindices"]) for mapping in mappings) == 3
    assert sorted(
        (
            verse,
            mapping.get("tekst") or "<leeg>",
            mapping.get("anker", ""),
            mapping["grondindices"],
        )
        for verse, record in reviewed.items()
        for mapping in record["mappings"]
        if len(mapping["grondindices"]) > 1
    ) == [
        (4, "Waaraan", "", [0, 1]),
        (9, "alle dingen", "", [17, 18]),
        (9, "alle eeuwen", "", [11, 12]),
        (11, "Heere", "", [9, 10]),
        (11, "eeuwig", "", [2, 3]),
        (14, "Heere", "", [9, 10]),
        (19, "Gods", "", [15, 16]),
        (20, "dan overvloedig", "", [7, 8]),
        (21, "<leeg>", "eeuwigheid", [13, 14]),
        (21, "alle eeuwigheid", "", [15, 16]),
        (21, "alle geslachten", "", [10, 11, 12]),
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
        tuple(mapping["grondindices"]): (mapping["tekst"], mapping.get("voorkomen", 1))
        for mapping in reviewed[10]["mappings"]
        if mapping["grondindices"] in ([3], [6], [9], [12], [14])
    } == {
        (3,): ("de", 2),
        (6,): ("de", 3),
        (9,): ("de", 4),
        (12,): ("de", 1),
        (14,): ("de", 5),
    }
    assert {
        tuple(mapping["grondindices"]): (mapping["tekst"], mapping.get("voorkomen", 1))
        for mapping in reviewed[20]["mappings"]
        if mapping["grondindices"] in ([7, 8], [16])
    } == {(7, 8): ("dan overvloedig", 1), (16,): ("die", 2)}


def test_ephesians_three_documents_all_guide_tr_differences():
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
        2: [(["G1487", "G1065"], ["G1489"])],
        5: [([], ["G1722"])],
        6: [([], ["G846"]), ([], ["G3588"]), (["G5547", "G2424"], ["G5547"])],
        8: [([], ["G3588"]), ([], ["G1722"])],
        9: [(["G3622"], ["G2842"]), ([], ["G1223"]), ([], ["G2424"]), ([], ["G5547"])],
        11: [(["G3588", "G5547"], ["G5547"])],
        12: [([], ["G3588"])],
        14: [([], ["G3588", "G2962"]), ([], ["G1473"]), ([], ["G2424"]), ([], ["G5547"])],
        20: [([], ["G1537", "G4053"])],
        21: [(["G2532", "G1722"], ["G1722"])],
    }
