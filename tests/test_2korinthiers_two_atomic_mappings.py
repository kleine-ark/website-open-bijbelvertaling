import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CHAPTER = ROOT / "data" / "2korinthiers" / "2.json"
REVIEW = ROOT / "data" / "woordnummers-review" / "2korinthiers-2.json"
INLINE = ROOT / "data" / "woordnummers-inline" / "2korinthiers.json"


def _chapter():
    return json.loads(CHAPTER.read_text(encoding="utf-8"))


def _ground_hash(data):
    payload = {
        str(verse["number"]): verse.get("grondtekst", [])
        for verse in data["verses"]
    }
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest().upper()


def test_ground_boundaries_keep_the_two_closing_clauses_with_their_dutch_verses():
    verses = {verse["number"]: verse for verse in _chapter()["verses"]}
    assert [token["strongs"] for token in verses[10]["grondtekst"][-6:]] == [
        "G2443", "G3361", "G4122", "G5259", "G3588", "G4567"
    ]
    assert [token["strongs"] for token in verses[12]["grondtekst"][-14:]] == [
        "G3756", "G2192", "G425", "G3588", "G4151", "G1473", "G3588",
        "G3361", "G2147", "G1473", "G5103", "G3588", "G80", "G1473"
    ]
    assert [token["strongs"] for token in verses[11]["grondtekst"]] == [
        "G3756", "G1063", "G846", "G3588", "G3540", "G50"
    ]
    assert [token["strongs"] for token in verses[13]["grondtekst"]] == [
        "G235", "G657", "G846", "G1831", "G1519", "G3109"
    ]


def test_review_pin_and_ground_coverage_are_exact():
    data = _chapter()
    review = json.loads(REVIEW.read_text(encoding="utf-8"))
    book = review["books"][0]
    assert review["source"]["sha256"] == "23D82961D8924E4592FFEE2B62504E467A0E9E79725A72512C57127FBDDD1793"
    assert review["grondtekst_bron"]["sha256"] == "BD3EC4A493D06F9173F273FD1E9971623E3A29683C0E0B40963EC8A42AF8A40E"
    assert book["grondtekst_sha256"] == _ground_hash(data)
    by_number = {verse["number"]: verse for verse in data["verses"]}
    for reviewed in book["verses"]:
        mapped = [index for mapping in reviewed["mappings"] for index in mapping["grondindices"]]
        unmapped = [index for item in reviewed.get("ongemapt", []) for index in item["grondindices"]]
        expected = list(range(len(by_number[reviewed["verse"]]["grondtekst"])))
        assert sorted(mapped + unmapped) == expected
        assert len(mapped + unmapped) == len(set(mapped + unmapped))


def test_review_is_atomic_and_contains_no_proposals():
    review = json.loads(REVIEW.read_text(encoding="utf-8"))
    serialized = json.dumps(review, ensure_ascii=False)
    assert "voorstel_" not in serialized
    for verse in review["books"][0]["verses"]:
        for mapping in verse["mappings"]:
            assert mapping["reviewstatus"] == "handmatig_gecontroleerd"
            assert mapping["confidence"] == 1
            assert len(mapping["grondindices"]) <= 3
            assert len(mapping["tekst"].split()) <= 4


def test_atomic_projection_has_every_ground_link_at_a_word_anchor():
    data = _chapter()
    review = json.loads(REVIEW.read_text(encoding="utf-8"))
    inline = json.loads(INLINE.read_text(encoding="utf-8"))["chapters"]["2"]
    reviewed = review["books"][0]["verses"]
    assert sum(len(verse["mappings"]) for verse in reviewed) == 225
    assert sum(len(mapping["grondindices"]) for verse in reviewed for mapping in verse["mappings"]) == 286
    assert sum(len(verse["woordnummers"]) for verse in data["verses"]) == 225
    assert sum(len(mapping["strongs"]) for verse in data["verses"] for mapping in verse["woordnummers"]) == 286
    assert sum(len(mappings) for mappings in inline.values()) == 225
    assert sum(len(mapping["strongs"]) for mappings in inline.values() for mapping in mappings) == 286
    assert any(mapping.get("source_verse") == 11 for mapping in reviewed[9]["mappings"])
    assert any(mapping.get("source_verse") == 13 for mapping in reviewed[11]["mappings"])
    for verse in data["verses"]:
        assert all(mapping["tekst"] != verse["text2026"] for mapping in verse["woordnummers"])
