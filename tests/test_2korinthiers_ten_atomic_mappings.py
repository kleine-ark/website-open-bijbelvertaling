import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CHAPTER = ROOT / "data" / "2korinthiers" / "10.json"
REVIEW = ROOT / "data" / "woordnummers-review" / "2korinthiers-10.json"
INLINE = ROOT / "data" / "woordnummers-inline" / "2korinthiers.json"


def _data(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _ground_hash(chapter):
    payload = {str(v["number"]): v.get("grondtekst", []) for v in chapter["verses"]}
    encoded = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode()
    return hashlib.sha256(encoded).hexdigest().upper()


def _whole_word_count(text, target):
    return len(
        re.findall(
            rf"(?<!\w){re.escape(target)}(?!\w)",
            text,
            flags=re.IGNORECASE,
        )
    )


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


def test_review_is_fully_atomic_and_has_no_proposals():
    review = _data(REVIEW)
    assert "voorstel_" not in json.dumps(review, ensure_ascii=False)
    verses = review["books"][0]["verses"]
    assert len(verses) == 18
    assert sum(len(verse["mappings"]) for verse in verses) == 314
    assert sum(
        len(mapping["grondindices"])
        for verse in verses
        for mapping in verse["mappings"]
    ) == 314
    assert sum(len(verse.get("bronafwijkingen", [])) for verse in verses) == 5
    for verse in verses:
        for mapping in verse["mappings"]:
            assert mapping["reviewstatus"] == "handmatig_gecontroleerd"
            assert mapping["confidence"] == 1
            assert len(mapping["grondindices"]) == 1
            assert not mapping["tekst"] or len(mapping["tekst"].split()) <= 2


def test_all_repeated_targets_and_empty_anchors_are_explicit():
    chapter, review = _data(CHAPTER), _data(REVIEW)
    text_by_verse = {verse["number"]: verse["text2026"] for verse in chapter["verses"]}
    for verse in review["books"][0]["verses"]:
        text = text_by_verse[verse["verse"]]
        for mapping in verse["mappings"]:
            target = mapping["tekst"] or mapping["anker"]
            count = _whole_word_count(text, target)
            assert count >= 1
            if count > 1:
                assert 1 <= mapping["voorkomen"] <= count
            elif "voorkomen" in mapping:
                assert mapping["voorkomen"] == 1
    verses = {verse["verse"]: verse for verse in review["books"][0]["verses"]}
    assert [
        mapping["voorkomen"]
        for mapping in verses[7]["mappings"]
        if mapping["tekst"].casefold() == "christus"
    ] == [1, 2, 3]
    assert [
        mapping["voorkomen"]
        for mapping in verses[12]["mappings"]
        if mapping["tekst"].casefold() == "zichzelf"
    ] == [1, 3, 2, 4, 5]


def test_projected_chapter_has_all_314_atomic_links():
    chapter, review = _data(CHAPTER), _data(REVIEW)
    inline = _data(INLINE)["chapters"]["10"]
    reviewed = review["books"][0]["verses"]
    assert sum(len(verse["mappings"]) for verse in reviewed) == 314
    assert sum(len(verse["woordnummers"]) for verse in chapter["verses"]) == 314
    assert sum(
        len(mapping["strongs"])
        for verse in chapter["verses"]
        for mapping in verse["woordnummers"]
    ) == 314
    assert sum(len(verse) for verse in inline.values()) == 314
    assert sum(
        len(mapping["strongs"])
        for verse in inline.values()
        for mapping in verse
    ) == 314
    for verse in chapter["verses"]:
        assert all(
            mapping["tekst"] != verse["text2026"]
            for mapping in verse["woordnummers"]
        )
