import json
import re
from pathlib import Path

from scripts.import_inline_woordnummers import _grondtekst_sha256


ROOT = Path(__file__).resolve().parents[1]
GROUND_SHA = "018545C5621E40940EF8317A62185BD9F79C3853529044CDB375D2A082DE8CF2"
GUIDE_SHA = "C9D7489DCEC2B7C4DB64158651FCF5C62B282147038B2633D4F79F83266679B5"
TR_SHA = "1C1BA0F30DBE30D972E42241672DFE641F372EB182B26A2620556DEE8CB17186"
GROUND_COUNTS = [8, 29, 14, 16, 24, 31, 17, 8, 21, 19, 19, 19, 28]
GUIDE_COUNTS = [8, 25, 14, 16, 25, 31, 17, 8, 21, 18, 18, 19, 28]
MAPPING_COUNTS = [8, 29, 13, 16, 23, 31, 16, 8, 21, 19, 19, 19, 28]


def _load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _occurrences(text, target):
    pattern = rf"(?<!\w){re.escape(target)}(?!\w)"
    return list(re.finditer(pattern, text, re.IGNORECASE | re.UNICODE))


def test_1tessalonicensen_3_review_is_atomic_complete_pinned_and_reachable():
    chapter = _load(ROOT / "data" / "1tessalonicensen" / "3.json")
    review_path = ROOT / "data" / "woordnummers-review" / "1tessalonicensen-3.json"
    review = _load(review_path)
    book = review["books"][0]
    chapter_verses = {verse["number"]: verse for verse in chapter["verses"]}

    assert _grondtekst_sha256(chapter) == GROUND_SHA
    assert review["grondtekst_bron"]["lokale_grondtekst_sha256"] == GROUND_SHA
    assert review["grondtekst_bron"]["sha256"] == TR_SHA
    assert review["source"]["sha256"] == GUIDE_SHA
    assert book["source_file_sha256"] == GUIDE_SHA
    assert [verse["verse"] for verse in book["verses"]] == list(range(1, 14))
    assert "voorstel_" not in review_path.read_text(encoding="utf-8")

    mapping_count = 0
    ground_link_count = 0
    source_link_count = 0
    deviation_count = 0
    composite_count = 0
    for record, expected_ground, expected_source, expected_mappings in zip(
        book["verses"], GROUND_COUNTS, GUIDE_COUNTS, MAPPING_COUNTS
    ):
        verse = chapter_verses[record["verse"]]
        mappings = record["mappings"]
        ground_indices = [index for mapping in mappings for index in mapping["grondindices"]]
        source_indices = [index for mapping in mappings for index in mapping["bronindices"]]
        mapping_count += len(mappings)
        ground_link_count += len(ground_indices)
        source_link_count += len(source_indices)
        deviation_count += len(record.get("bronafwijkingen", []))
        composite_count += sum(len(mapping["grondindices"]) > 1 for mapping in mappings)

        assert len(verse["grondtekst"]) == expected_ground
        assert len(mappings) == expected_mappings
        assert sorted(ground_indices) == list(range(expected_ground))
        assert len(ground_indices) == len(set(ground_indices))
        assert sorted(source_indices) == list(range(expected_source))
        assert len(source_indices) == len(set(source_indices))
        assert record["morphhb_verse"] == record["verse"]
        assert record["vervang_bronreferentie"] == f"1THESS 3:{record['verse']}"
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

    assert mapping_count == 250
    assert ground_link_count == 253
    assert source_link_count == 248
    assert deviation_count == 9
    assert composite_count == 3


def test_1tessalonicensen_3_documents_all_nine_guide_tr_differences_atomically():
    review = _load(ROOT / "data" / "woordnummers-review" / "1tessalonicensen-3.json")
    records = {record["verse"]: record for record in review["books"][0]["verses"]}

    actual = set()
    for verse_number, record in records.items():
        for item in record.get("bronafwijkingen", []):
            actual.add(
                (
                    verse_number,
                    tuple(item["grondindices"]),
                    tuple(item["bronindices"]),
                    tuple(item["grondtekst_strongs"]),
                    tuple(item["bron_strongs"]),
                )
            )

    expected = {
        (2, (6,), (), ("G2532",), ()),
        (2, (7,), (), ("G1249",), ()),
        (2, (12,), (), ("G1473",), ()),
        (2, (21,), (), ("G4771",), ()),
        (2, (25,), (21,), ("G4012",), ("G5228",)),
        (5, (12,), (12, 15), ("G3381",), ("G3361", "G4459")),
        (10, (4,), (), ("G4053",), ()),
        (11, (12,), (), ("G5547",), ()),
        (13, (22,), (27,), ("G5547",), ("G281",)),
    }
    assert actual == expected


def test_1tessalonicensen_3_publishes_every_link_at_an_atomic_target():
    chapter = _load(ROOT / "data" / "1tessalonicensen" / "3.json")
    inline = _load(ROOT / "data" / "woordnummers-inline" / "1tessalonicensen.json")
    inline_verses = inline["chapters"]["3"]

    assert [len(verse["woordnummers"]) for verse in chapter["verses"]] == MAPPING_COUNTS
    assert [len(inline_verses[str(number)]) for number in range(1, 14)] == MAPPING_COUNTS

    for verse in chapter["verses"]:
        embedded = verse["woordnummers"]
        projected = inline_verses[str(verse["number"])]
        expected_links = len(verse["grondtekst"])
        for mappings in (embedded, projected):
            assert sum(len(mapping["strongs"]) for mapping in mappings) == expected_links
            assert not any(mapping.get("tekst", "").strip() == verse["text2026"].strip() for mapping in mappings)

    assert sum(len(verse["woordnummers"]) for verse in chapter["verses"]) == 250
    assert sum(len(items) for items in inline_verses.values()) == 250
