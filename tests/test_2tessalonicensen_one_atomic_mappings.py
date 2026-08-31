import json
import re
from pathlib import Path

from scripts.import_inline_woordnummers import _grondtekst_sha256


ROOT = Path(__file__).resolve().parents[1]
GROUND_SHA = "8903DB75B353C80BFBA5F711AEF43DB9BC1866E0F40CB8ACBD15009692AABE71"
GUIDE_SHA = "EA45AFE632DE214F360716BEE1F1593C15EFCBB83C4BBAA617D3693819ED9840"
TR_SHA = "D73D610D017ED8CC4A2090AA70F0E64838C51D7F870B603306C96C61D85215F5"
GROUND_COUNTS = [16, 12, 26, 27, 18, 9, 19, 20, 16, 24, 25, 25]
GUIDE_COUNTS = [16, 12, 26, 27, 18, 9, 19, 19, 16, 24, 25, 24]
MAPPING_COUNTS = [16, 12, 25, 27, 18, 9, 19, 20, 16, 24, 24, 25]


def _load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _occurrences(text, target):
    return list(re.finditer(rf"(?<!\w){re.escape(target)}(?!\w)", text, re.I | re.U))


def test_2tessalonicensen_1_review_is_atomic_complete_pinned_and_reachable():
    chapter = _load(ROOT / "data" / "2tessalonicensen" / "1.json")
    review_path = ROOT / "data" / "woordnummers-review" / "2tessalonicensen-1.json"
    review = _load(review_path)
    book = review["books"][0]
    chapter_verses = {verse["number"]: verse for verse in chapter["verses"]}

    assert _grondtekst_sha256(chapter) == GROUND_SHA
    assert review["grondtekst_bron"]["lokale_grondtekst_sha256"] == GROUND_SHA
    assert review["grondtekst_bron"]["sha256"] == TR_SHA
    assert review["source"]["sha256"] == GUIDE_SHA
    assert book["source_file_sha256"] == GUIDE_SHA
    assert [verse["verse"] for verse in book["verses"]] == list(range(1, 13))
    assert "voorstel_" not in review_path.read_text(encoding="utf-8")

    mapping_total = ground_total = source_total = deviation_total = composite_total = 0
    for record, ground_count, guide_count, mapping_count in zip(
        book["verses"], GROUND_COUNTS, GUIDE_COUNTS, MAPPING_COUNTS
    ):
        verse = chapter_verses[record["verse"]]
        mappings = record["mappings"]
        ground_indices = [index for mapping in mappings for index in mapping["grondindices"]]
        source_indices = [index for mapping in mappings for index in mapping["bronindices"]]
        mapping_total += len(mappings)
        ground_total += len(ground_indices)
        source_total += len(source_indices)
        deviation_total += len(record.get("bronafwijkingen", []))
        composite_total += sum(len(mapping["grondindices"]) > 1 for mapping in mappings)

        assert len(verse["grondtekst"]) == ground_count
        assert len(mappings) == mapping_count
        assert sorted(ground_indices) == list(range(ground_count))
        assert len(ground_indices) == len(set(ground_indices))
        assert sorted(source_indices) == list(range(guide_count))
        assert len(source_indices) == len(set(source_indices))
        assert record["morphhb_verse"] == record["verse"]
        assert record["vervang_bronreferentie"] == f"2THESS 1:{record['verse']}"
        assert all(mapping["reviewstatus"] == "handmatig_gecontroleerd" for mapping in mappings)
        assert all(mapping["confidence"] == 1 for mapping in mappings)
        assert all(len(mapping["grondindices"]) <= 2 for mapping in mappings)
        assert all(len((mapping.get("tekst") or mapping.get("anker")).split()) <= 3 for mapping in mappings)
        assert not any(mapping.get("tekst", "").strip() == verse["text2026"].strip() for mapping in mappings)

        for mapping in mappings:
            target = mapping.get("tekst") or mapping.get("anker")
            occurrences = _occurrences(verse["text2026"], target)
            assert occurrences, (record["verse"], target)
            assert 1 <= mapping.get("voorkomen", 1) <= len(occurrences)
            if len(occurrences) > 1:
                assert "voorkomen" in mapping, (record["verse"], target)

    assert mapping_total == 235
    assert ground_total == 237
    assert source_total == 235
    assert deviation_total == 2
    assert composite_total == 2


def test_2tessalonicensen_1_documents_both_guide_tr_differences_atomically():
    review = _load(ROOT / "data" / "woordnummers-review" / "2tessalonicensen-1.json")
    actual = {
        (
            record["verse"], tuple(item["grondindices"]), tuple(item["bronindices"]),
            tuple(item["grondtekst_strongs"]), tuple(item["bron_strongs"]),
        )
        for record in review["books"][0]["verses"]
        for item in record.get("bronafwijkingen", [])
    }
    assert actual == {
        (8, (19,), (), ("G5547",), ()),
        (12, (8,), (), ("G5547",), ()),
    }


def test_2tessalonicensen_1_preserves_semantic_guide_occurrences_in_verses_10_and_11():
    review = _load(ROOT / "data" / "woordnummers-review" / "2tessalonicensen-1.json")
    verses = {record["verse"]: record for record in review["books"][0]["verses"]}

    def source_by_ground(verse_number):
        result = {}
        for mapping in verses[verse_number]["mappings"]:
            assert len(mapping["grondindices"]) == len(mapping["bronindices"])
            result.update(zip(mapping["grondindices"], mapping["bronindices"]))
        return result

    verse_10 = source_by_ground(10)
    assert {index: verse_10[index] for index in (3, 4, 9, 11, 15, 20, 21)} == {
        3: 7,
        4: 9,
        9: 13,
        11: 15,
        15: 22,
        20: 0,
        21: 2,
    }
    verse_11 = source_by_ground(11)
    assert {index: verse_11[index] for index in (10, 12)} == {10: 13, 12: 9}


def test_2tessalonicensen_1_publishes_every_link_at_an_atomic_target():
    chapter = _load(ROOT / "data" / "2tessalonicensen" / "1.json")
    inline = _load(ROOT / "data" / "woordnummers-inline" / "2tessalonicensen.json")
    inline_verses = inline["chapters"]["1"]

    assert [len(verse["woordnummers"]) for verse in chapter["verses"]] == MAPPING_COUNTS
    assert [len(inline_verses[str(number)]) for number in range(1, 13)] == MAPPING_COUNTS
    for verse in chapter["verses"]:
        expected_links = len(verse["grondtekst"])
        for mappings in (verse["woordnummers"], inline_verses[str(verse["number"])]):
            assert sum(len(mapping["strongs"]) for mapping in mappings) == expected_links
            assert not any(mapping.get("tekst", "").strip() == verse["text2026"].strip() for mapping in mappings)

    assert sum(len(verse["woordnummers"]) for verse in chapter["verses"]) == 235
    assert sum(len(items) for items in inline_verses.values()) == 235
