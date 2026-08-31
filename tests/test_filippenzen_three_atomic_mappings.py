import hashlib
import json
import re
from collections import Counter
from pathlib import Path

from scripts.import_inline_woordnummers import _grondtekst_sha256


ROOT = Path(__file__).resolve().parents[1]
CHAPTER = ROOT / "data" / "filippenzen" / "3.json"
REVIEW = ROOT / "data" / "woordnummers-review" / "filippenzen-3.json"
INLINE = ROOT / "data" / "woordnummers-inline" / "filippenzen.json"
GROUND_SHA = "BD1653F23ECAC8C8E509B3D0C7F30F38268255EEFEC8BF0F06F23FA000BD752D"
FLAT_GROUND_SHA = "C78BE765388C4235A3AA55EFF684781A6F84A6E3D8DD2E883F8D27CDF7C68829"
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


def _mapping(reviewed, verse, ground_indices):
    return next(
        item
        for item in reviewed[verse]["mappings"]
        if item["grondindices"] == ground_indices
    )


def test_philippians_three_pins_boundary_and_complete_ground_coverage():
    chapter, review, verses, reviewed = _data()
    assert _grondtekst_sha256(chapter) == GROUND_SHA
    assert review["source"]["sha256"] == GUIDE_SHA
    assert review["grondtekst_bron"]["sha256"] == TR_SHA
    assert review["grondtekst_bron"]["lokale_grondtekst_sha256"] == GROUND_SHA
    assert sorted(verses) == list(range(1, 22))
    assert sorted(reviewed) == list(range(1, 22))

    flattened = [token for verse in chapter["verses"] for token in verse["grondtekst"]]
    encoded = json.dumps(
        flattened, ensure_ascii=False, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")
    assert hashlib.sha256(encoded).hexdigest().upper() == FLAT_GROUND_SHA
    assert len(verses[13]["grondtekst"]) == 6
    assert len(verses[14]["grondtekst"]) == 24

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


def test_philippians_three_review_is_atomic_manual_and_reachable():
    _, _, verses, reviewed = _data()
    mappings = [mapping for verse in reviewed.values() for mapping in verse["mappings"]]
    assert len(mappings) == 299
    assert sum(len(mapping["grondindices"]) for mapping in mappings) == 349
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


def test_philippians_three_documents_guide_tr_differences():
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
        7: [(["G1510"], ["G2258"])],
        8: [(["G3303", "G3767", "G1065"], ["G3304"]), ([], ["G1510"])],
        11: [(["G3588", "G3498", "G1537"], ["G3588", "G3498"])],
        12: [(["G5547"], ["G3588", "G5547"])],
        14: [(["G1519"], ["G1909"])],
        16: [([], ["G2583"]), ([], ["G3588", "G846"]), ([], ["G5426"])],
        18: [(["G2036"], ["G3004"])],
        21: [([], ["G1519"]), ([], ["G3588", "G846"]), ([], ["G1096"]), (["G848"], ["G1438"])],
    }


def test_philippians_three_preserves_shifted_source_boundary_semantics():
    _, _, verses, reviewed = _data()
    assert reviewed[13]["source_verse"] == 13
    assert reviewed[14]["source_verse"] == 14
    moved = [_mapping(reviewed, 14, [index]) for index in range(10)]
    assert [mapping["source_verse"] for mapping in moved] == [13] * 10
    assert [mapping["bronindices"] for mapping in moved] == [
        [7], [6], [10], [8], [11], [9], [14], [12], [15], [13]
    ]
    assert _mapping(reviewed, 14, [13])["bronindices"] == [3]
    assert verses[14]["grondtekst"][13]["strongs"] == "G1909"
    assert _mapping(reviewed, 15, [6])["voorkomen"] == 2
    assert _mapping(reviewed, 21, [25])["bronindices"] == [11]


def test_philippians_three_publishes_every_link_at_an_atomic_target():
    chapter = json.loads(CHAPTER.read_text(encoding="utf-8"))
    inline = json.loads(INLINE.read_text(encoding="utf-8"))
    inline_verses = inline["chapters"]["3"]

    for verse in chapter["verses"]:
        embedded = verse["woordnummers"]
        projected = inline_verses[str(verse["number"])]
        expected = len(verse["grondtekst"])
        for mappings in (embedded, projected):
            assert sum(len(mapping["strongs"]) for mapping in mappings) == expected
            assert not any(
                mapping.get("tekst", "").strip() == verse["text2026"].strip()
                for mapping in mappings
            )

    assert sum(len(verse["woordnummers"]) for verse in chapter["verses"]) == 299
    assert sum(len(items) for items in inline_verses.values()) == 299
