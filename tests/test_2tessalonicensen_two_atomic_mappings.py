import hashlib
import json
import re
from pathlib import Path

from scripts.import_inline_woordnummers import _grondtekst_sha256


ROOT = Path(__file__).resolve().parents[1]
GROUND_SHA = "56CC5F686498EEFF0CA601F136AD5BDDBE40264E89747A18D81C8D3D3609BB4A"
GUIDE_SHA = "EA45AFE632DE214F360716BEE1F1593C15EFCBB83C4BBAA617D3693819ED9840"
TR_SHA = "D73D610D017ED8CC4A2090AA70F0E64838C51D7F870B603306C96C61D85215F5"
GROUND_COUNTS = [17, 30, 24, 25, 10, 13, 15, 21, 16, 21, 15, 13, 28, 16, 17, 25, 13]
GUIDE_COUNTS = [17, 30, 24, 23, 10, 13, 15, 22, 16, 19, 15, 12, 28, 17, 17, 25, 12]
MAPPING_COUNTS = [17, 28, 23, 25, 10, 13, 15, 21, 16, 21, 14, 13, 28, 15, 17, 25, 13]
MAPPING_DIGEST = "6B8326E8E9D91E22CE51C48A2EA94A5632379003AC8C56299448F09B2A5B3DE8"


def _load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _occurrences(text, target):
    return list(re.finditer(rf"(?<!\w){re.escape(target)}(?!\w)", text, re.I | re.U))


def _mapping_digest(verses):
    normalized = [
        (
            record["verse"],
            [
                (
                    mapping.get("tekst", ""),
                    mapping.get("anker", ""),
                    mapping.get("plaats", ""),
                    mapping.get("voorkomen"),
                    mapping["grondindices"],
                    mapping["bronindices"],
                )
                for mapping in record["mappings"]
            ],
        )
        for record in verses
    ]
    payload = json.dumps(
        normalized, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode()
    return hashlib.sha256(payload).hexdigest().upper()


def test_2tessalonicensen_2_review_is_atomic_complete_pinned_and_reachable():
    chapter = _load(ROOT / "data" / "2tessalonicensen" / "2.json")
    review_path = ROOT / "data" / "woordnummers-review" / "2tessalonicensen-2.json"
    review = _load(review_path)
    book = review["books"][0]
    chapter_verses = {verse["number"]: verse for verse in chapter["verses"]}

    assert _grondtekst_sha256(chapter) == GROUND_SHA
    assert review["grondtekst_bron"]["lokale_grondtekst_sha256"] == GROUND_SHA
    assert review["grondtekst_bron"]["sha256"] == TR_SHA
    assert review["source"]["sha256"] == GUIDE_SHA
    assert book["source_file_sha256"] == GUIDE_SHA
    assert [record["verse"] for record in book["verses"]] == list(range(1, 18))
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
        assert record["vervang_bronreferentie"] == f"2THESS 2:{record['verse']}"
        assert all(mapping["reviewstatus"] == "handmatig_gecontroleerd" for mapping in mappings)
        assert all(mapping["confidence"] == 1 for mapping in mappings)
        assert all(1 <= len(mapping["grondindices"]) <= 2 for mapping in mappings)
        assert all(len((mapping.get("tekst") or mapping.get("anker")).split()) <= 3 for mapping in mappings)
        assert not any(mapping.get("tekst", "").strip() == verse["text2026"].strip() for mapping in mappings)

        for mapping in mappings:
            target = mapping.get("tekst") or mapping.get("anker")
            occurrences = _occurrences(verse["text2026"], target)
            assert occurrences, (record["verse"], target)
            assert 1 <= mapping.get("voorkomen", 1) <= len(occurrences)
            if len(occurrences) > 1:
                assert "voorkomen" in mapping, (record["verse"], target)

    assert mapping_total == 314
    assert ground_total == 319
    assert source_total == 315
    assert deviation_total == 17
    assert composite_total == 5
    assert _mapping_digest(book["verses"]) == MAPPING_DIGEST


def test_2tessalonicensen_2_documents_every_guide_tr_difference_atomically():
    review = _load(ROOT / "data" / "woordnummers-review" / "2tessalonicensen-2.json")
    actual = {
        (
            record["verse"],
            tuple(item["grondindices"]),
            tuple(item["bronindices"]),
            tuple(item["grondtekst_strongs"]),
            tuple(item["bron_strongs"]),
        )
        for record in review["books"][0]["verses"]
        for item in record.get("bronafwijkingen", [])
    }
    assert actual == {
        (2, (9,), (9,), ("G3383",), ("G3366",)),
        (2, (29,), (28,), ("G5547",), ("G2962",)),
        (3, (19,), (18,), ("G266",), ("G458",)),
        (4, (17,), (), ("G5613",), ()),
        (4, (18,), (), ("G2316",), ()),
        (5, (8,), (3,), ("G3004",), ("G2036",)),
        (8, (7,), (7, 8), ("G2962",), ("G2962", "G2424")),
        (8, (8,), (9,), ("G355",), ("G337",)),
        (10, (4,), (), ("G3588",), ()),
        (10, (6,), (), ("G1722",), ()),
        (12, (10,), (), ("G1722",), ()),
        (14, (0, 1), (0, 1, 2), ("G1519", "G3739"), ("G1519", "G3739", "G2532")),
        (15, (9,), (9, 10), ("G1321",), ("G1473", "G1321")),
        (15, (16,), (), ("G1473",), ()),
        (16, (10,), (), ("G2532",), ()),
        (16, (11,), (11, 12), ("G3962",), ("G3588", "G3962")),
        (17, (6,), (), ("G4771",), ()),
    }


def test_2tessalonicensen_2_preserves_semantic_repeated_source_occurrences():
    review = _load(ROOT / "data" / "woordnummers-review" / "2tessalonicensen-2.json")
    verses = {record["verse"]: record for record in review["books"][0]["verses"]}

    def pair(verse_number, ground_index):
        mapping = next(
            item for item in verses[verse_number]["mappings"]
            if ground_index in item["grondindices"]
        )
        return tuple(mapping["grondindices"]), tuple(mapping["bronindices"])

    assert pair(2, 9) == ((9,), (9,))
    assert pair(2, 29) == ((29,), (28,))
    assert pair(3, 19) == ((19,), (18,))
    assert pair(5, 6) == ((6,), (9,))
    assert pair(5, 8) == ((8,), (3,))
    assert pair(5, 9) == ((9,), (4,))
    assert pair(8, 7) == ((7,), (7, 8))
    assert pair(8, 8) == ((8,), (9,))
    assert pair(11, 4) == ((4,), (6,))
    assert pair(11, 12) == ((12,), (10,))
    assert pair(13, 15) == ((15,), (17,))
    assert pair(13, 16) == ((16,), (14,))
    assert pair(13, 17) == ((17,), (15,))
    assert pair(14, 1) == ((0, 1), (0, 1, 2))
    assert pair(15, 9) == ((9,), (9, 10))
    assert pair(15, 16) == ((16,), ())
    assert pair(16, 10) == ((10,), ())
    assert pair(16, 11) == ((11,), (11, 12))


def test_2tessalonicensen_2_publishes_every_link_at_an_atomic_target():
    chapter = _load(ROOT / "data" / "2tessalonicensen" / "2.json")
    inline = _load(ROOT / "data" / "woordnummers-inline" / "2tessalonicensen.json")
    inline_verses = inline["chapters"]["2"]

    assert [len(verse["woordnummers"]) for verse in chapter["verses"]] == MAPPING_COUNTS
    assert [len(inline_verses[str(number)]) for number in range(1, 18)] == MAPPING_COUNTS
    for verse in chapter["verses"]:
        expected_links = len(verse["grondtekst"])
        for mappings in (verse["woordnummers"], inline_verses[str(verse["number"])]):
            assert sum(len(mapping["strongs"]) for mapping in mappings) == expected_links
            assert not any(mapping.get("tekst", "").strip() == verse["text2026"].strip() for mapping in mappings)

    assert sum(len(verse["woordnummers"]) for verse in chapter["verses"]) == 314
    assert sum(len(items) for items in inline_verses.values()) == 314
