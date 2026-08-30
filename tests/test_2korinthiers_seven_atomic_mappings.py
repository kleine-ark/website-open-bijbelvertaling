import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CHAPTER = ROOT / "data" / "2korinthiers" / "7.json"
REVIEW = ROOT / "data" / "woordnummers-review" / "2korinthiers-7.json"
INLINE = ROOT / "data" / "woordnummers-inline" / "2korinthiers.json"


def _data(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _ground_hash(chapter):
    payload = {str(v["number"]): v.get("grondtekst", []) for v in chapter["verses"]}
    encoded = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode()
    return hashlib.sha256(encoded).hexdigest().upper()


def test_review_pins_and_ground_coverage_are_exact():
    chapter, review = _data(CHAPTER), _data(REVIEW)
    book = review["books"][0]
    assert review["source"]["sha256"] == (
        "23D82961D8924E4592FFEE2B62504E467A0E9E79725A72512C57127FBDDD1793"
    )
    assert review["grondtekst_bron"]["sha256"] == (
        "BD3EC4A493D06F9173F273FD1E9971623E3A29683C0E0B40963EC8A42AF8A40E"
    )
    assert book["grondtekst_sha256"] == _ground_hash(chapter)
    local = {verse["number"]: verse for verse in chapter["verses"]}
    for verse in book["verses"]:
        indices = [
            index for mapping in verse["mappings"] for index in mapping["grondindices"]
        ]
        indices += [
            index
            for item in verse.get("ongemapt", [])
            for index in item["grondindices"]
        ]
        assert sorted(indices) == list(range(len(local[verse["verse"]]["grondtekst"])))
        assert len(indices) == len(set(indices))


def test_review_is_atomic_and_has_no_proposals():
    review = _data(REVIEW)
    assert "voorstel_" not in json.dumps(review, ensure_ascii=False)
    verses = review["books"][0]["verses"]
    assert len(verses) == 16
    assert sum(len(verse["mappings"]) for verse in verses) == 332
    for verse in verses:
        for mapping in verse["mappings"]:
            assert mapping["reviewstatus"] == "handmatig_gecontroleerd"
            assert mapping["confidence"] == 1
            assert len(mapping["grondindices"]) == 1
            assert len(mapping["tekst"].split()) <= 2


def test_repeated_and_empty_anchors_are_explicit():
    review = _data(REVIEW)
    verses = {verse["verse"]: verse for verse in review["books"][0]["verses"]}
    grieved = [
        mapping
        for mapping in verses[9]["mappings"]
        if mapping["tekst"] == "bedroefd"
    ]
    assert [mapping["voorkomen"] for mapping in grieved] == [1, 2, 3]
    yes = [
        mapping
        for mapping in verses[11]["mappings"]
        if mapping["tekst"].casefold() == "ja"
    ]
    assert [mapping["voorkomen"] for mapping in yes] == [1, 2, 3, 4, 5, 6]
    empty = [
        (verse["verse"], mapping["anker"], mapping["plaats"], mapping["voorkomen"])
        for verse in verses.values()
        for mapping in verse["mappings"]
        if not mapping["tekst"]
    ]
    assert empty == [(3, "samen", "voor", 1), (12, "voor u", "voor", 1)]


def test_projected_chapter_has_all_332_atomic_links():
    chapter, review = _data(CHAPTER), _data(REVIEW)
    inline = _data(INLINE)["chapters"]["7"]
    reviewed = review["books"][0]["verses"]
    assert sum(len(verse["mappings"]) for verse in reviewed) == 332
    assert sum(
        len(mapping["grondindices"])
        for verse in reviewed
        for mapping in verse["mappings"]
    ) == 332
    assert sum(len(verse["woordnummers"]) for verse in chapter["verses"]) == 332
    assert sum(
        len(mapping["strongs"])
        for verse in chapter["verses"]
        for mapping in verse["woordnummers"]
    ) == 332
    assert sum(len(verse) for verse in inline.values()) == 332
    assert sum(
        len(mapping["strongs"])
        for verse in inline.values()
        for mapping in verse
    ) == 332
    for verse in chapter["verses"]:
        assert all(
            mapping["tekst"] != verse["text2026"]
            for mapping in verse["woordnummers"]
        )
