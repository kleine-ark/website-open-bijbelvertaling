import json
import re
from pathlib import Path

from scripts.import_inline_woordnummers import _grondtekst_sha256


ROOT = Path(__file__).resolve().parents[1]
GROUND_SHA = "72839C7F05BFFA6C0E49BF6F93C8C98D3D172CB9E7C93944647EB23C18495CD4"
GUIDE_SHA = "C9D7489DCEC2B7C4DB64158651FCF5C62B282147038B2633D4F79F83266679B5"
TR_SHA = "1C1BA0F30DBE30D972E42241672DFE641F372EB182B26A2620556DEE8CB17186"
GROUND_COUNTS = [26, 10, 14, 11, 13, 24, 11, 19, 18, 19, 16, 10, 20, 20, 23, 23, 24, 7]
GUIDE_COUNTS = [29, 10, 14, 11, 13, 23, 11, 19, 18, 19, 16, 10, 20, 20, 23, 23, 24, 7]
MAPPING_COUNTS = [26, 10, 14, 11, 13, 24, 11, 19, 18, 19, 16, 10, 20, 20, 22, 23, 24, 7]


def _load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _occurrences(text, target):
    return list(re.finditer(rf"(?<!\w){re.escape(target)}(?!\w)", text, re.I | re.U))


def test_1tessalonicensen_4_review_is_atomic_complete_pinned_and_reachable():
    chapter = _load(ROOT / "data" / "1tessalonicensen" / "4.json")
    review_path = ROOT / "data" / "woordnummers-review" / "1tessalonicensen-4.json"
    review = _load(review_path)
    book = review["books"][0]
    chapter_verses = {verse["number"]: verse for verse in chapter["verses"]}

    assert _grondtekst_sha256(chapter) == GROUND_SHA
    assert review["grondtekst_bron"]["lokale_grondtekst_sha256"] == GROUND_SHA
    assert review["grondtekst_bron"]["sha256"] == TR_SHA
    assert review["source"]["sha256"] == GUIDE_SHA
    assert book["source_file_sha256"] == GUIDE_SHA
    assert [verse["verse"] for verse in book["verses"]] == list(range(1, 19))
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
        assert record["vervang_bronreferentie"] == f"1THESS 4:{record['verse']}"
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

    assert mapping_total == 307
    assert ground_total == 308
    assert source_total == 310
    assert deviation_total == 7
    assert composite_total == 1


def test_1tessalonicensen_4_documents_all_seven_guide_tr_differences_atomically():
    review = _load(ROOT / "data" / "woordnummers-review" / "1tessalonicensen-4.json")
    records = review["books"][0]["verses"]
    actual = {
        (
            record["verse"], tuple(item["grondindices"]), tuple(item["bronindices"]),
            tuple(item["grondtekst_strongs"]), tuple(item["bron_strongs"]),
        )
        for record in records
        for item in record.get("bronafwijkingen", [])
    }
    expected = {
        (1, (0,), (), ("G3588",), ()),
        (1, (11,), (19, 23), ("G2531",), ("G2531", "G2531")),
        (1, (19,), (12, 25), ("G4043",), ("G4043", "G4043")),
        (1, (20,), (15, 24), ("G2532",), ("G2532", "G2532")),
        (1, (23,), (10, 26), ("G2443",), ("G2443", "G2443")),
        (6, (13,), (), ("G3588",), ()),
        (8, (18,), (13,), ("G1473",), ("G4771",)),
    }
    assert actual == expected


def test_1tessalonicensen_4_publishes_every_link_at_an_atomic_target():
    chapter = _load(ROOT / "data" / "1tessalonicensen" / "4.json")
    inline = _load(ROOT / "data" / "woordnummers-inline" / "1tessalonicensen.json")
    inline_verses = inline["chapters"]["4"]

    assert [len(verse["woordnummers"]) for verse in chapter["verses"]] == MAPPING_COUNTS
    assert [len(inline_verses[str(number)]) for number in range(1, 19)] == MAPPING_COUNTS
    for verse in chapter["verses"]:
        expected_links = len(verse["grondtekst"])
        for mappings in (verse["woordnummers"], inline_verses[str(verse["number"])]):
            assert sum(len(mapping["strongs"]) for mapping in mappings) == expected_links
            assert not any(mapping.get("tekst", "").strip() == verse["text2026"].strip() for mapping in mappings)

    assert sum(len(verse["woordnummers"]) for verse in chapter["verses"]) == 307
    assert sum(len(items) for items in inline_verses.values()) == 307
