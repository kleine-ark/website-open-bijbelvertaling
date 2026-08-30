import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CHAPTER = ROOT / "data" / "2korinthiers" / "12.json"
REVIEW = ROOT / "data" / "woordnummers-review" / "2korinthiers-12.json"
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
    assert [verse["verse"] for verse in book["verses"]] == list(range(1, 22))

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


def test_review_is_atomic_manual_and_has_no_proposals():
    review = _data(REVIEW)
    assert "voorstel_" not in json.dumps(review, ensure_ascii=False)
    verses = review["books"][0]["verses"]
    assert len(verses) == 21
    assert sum(
        len(mapping["grondindices"])
        for verse in verses
        for mapping in verse["mappings"]
    ) == 415
    assert sum(len(verse["mappings"]) for verse in verses) == 410
    for verse in verses:
        for mapping in verse["mappings"]:
            assert mapping["reviewstatus"] == "handmatig_gecontroleerd"
            assert mapping["confidence"] == 1
            assert 1 <= len(mapping["grondindices"]) <= 2
            assert not mapping["tekst"] or len(mapping["tekst"].split()) <= 4


def test_repeated_targets_and_empty_anchors_are_explicit_and_reachable():
    chapter, review = _data(CHAPTER), _data(REVIEW)
    text_by_verse = {verse["number"]: verse["text2026"] for verse in chapter["verses"]}
    runtime_keys = set()
    for verse in review["books"][0]["verses"]:
        text = text_by_verse[verse["verse"]]
        for mapping in verse["mappings"]:
            target = mapping["tekst"] or mapping["anker"]
            count = _whole_word_count(text, target)
            assert count >= 1, (verse["verse"], target)
            occurrence = mapping.get("voorkomen")
            if count > 1:
                assert occurrence is not None
                assert 1 <= occurrence <= count
            elif occurrence is not None:
                assert occurrence == 1
            key = (
                verse["verse"],
                target.casefold(),
                occurrence or 1,
                mapping.get("plaats", "na"),
            )
            assert key not in runtime_keys
            runtime_keys.add(key)


def test_visible_mapping_ranges_do_not_overlap():
    chapter, review = _data(CHAPTER), _data(REVIEW)
    text_by_verse = {verse["number"]: verse["text2026"] for verse in chapter["verses"]}
    for verse in review["books"][0]["verses"]:
        text = text_by_verse[verse["verse"]]
        ranges = []
        for mapping in verse["mappings"]:
            target = mapping["tekst"] or mapping["anker"]
            matches = list(
                re.finditer(
                    rf"(?<!\w){re.escape(target)}(?!\w)",
                    text,
                    flags=re.IGNORECASE,
                )
            )
            match = matches[mapping.get("voorkomen", 1) - 1]
            ranges.append((match.start(), match.end(), target, not mapping["tekst"]))
        for index, left in enumerate(ranges):
            for right in ranges[index + 1 :]:
                overlap_involves_empty_mapping = left[3] or right[3]
                assert (
                    left[1] <= right[0]
                    or right[1] <= left[0]
                    or overlap_involves_empty_mapping
                ), (
                    verse["verse"],
                    left,
                    right,
                )


def test_local_tr_readings_stay_at_their_visible_targets():
    chapter, review = _data(CHAPTER), _data(REVIEW)
    ground = {verse["number"]: verse["grondtekst"] for verse in chapter["verses"]}
    records = {verse["verse"]: verse for verse in review["books"][0]["verses"]}

    def strongs_for(verse_number, target, occurrence=1):
        mapping = next(
            item
            for item in records[verse_number]["mappings"]
            if item.get("tekst") == target and item.get("voorkomen", 1) == occurrence
        )
        return [ground[verse_number][index]["strongs"] for index in mapping["grondindices"]]

    assert strongs_for(1, "roemen") == ["G2744"]
    assert strongs_for(8, "Hierover") == ["G5228", "G3778"]
    assert strongs_for(20, "ik", 5) == ["G2504"]
    assert strongs_for(20, "ruzie") == ["G2052"]


def test_projected_chapter_has_all_415_atomic_links():
    chapter = _data(CHAPTER)
    inline = _data(INLINE)["chapters"]["12"]
    assert sum(
        len(mapping["strongs"])
        for verse in chapter["verses"]
        for mapping in verse["woordnummers"]
    ) == 415
    assert sum(
        len(mapping["strongs"])
        for verse in inline.values()
        for mapping in verse
    ) == 415
    assert sum(len(verse["woordnummers"]) for verse in chapter["verses"]) == 410
    assert sum(len(items) for items in inline.values()) == 410
    for verse in chapter["verses"]:
        assert all(
            mapping["tekst"] != verse["text2026"]
            for mapping in verse["woordnummers"]
        )
