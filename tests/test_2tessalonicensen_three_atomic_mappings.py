import hashlib
import json
import re
from pathlib import Path

from scripts.import_inline_woordnummers import _grondtekst_sha256


ROOT = Path(__file__).resolve().parents[1]
GROUND_SHA = "2CB2CF4F56A00C457A81F3FCDC2A5883399E43F9576377F50945033F8CC2E8FB"
GUIDE_SHA = "EA45AFE632DE214F360716BEE1F1593C15EFCBB83C4BBAA617D3693819ED9840"
TR_SHA = "D73D610D017ED8CC4A2090AA70F0E64838C51D7F870B603306C96C61D85215F5"
GROUND_COUNTS = [18, 14, 13, 14, 18, 27, 12, 21, 15, 17, 11, 20, 6, 19, 9, 20, 14, 11]
GUIDE_COUNTS = [18, 14, 13, 13, 18, 27, 12, 21, 15, 17, 11, 18, 6, 18, 9, 20, 14, 10]
MAPPING_COUNTS = [18, 14, 13, 14, 18, 27, 12, 21, 15, 17, 11, 20, 6, 19, 9, 19, 14, 11]
MAPPING_DIGEST = "AB239AC9BD8C4FD48D109B12F18EC9DD3CB376FA46344943ADF57850C02D8DA4"


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


def test_2tessalonicensen_3_review_is_atomic_complete_pinned_and_reachable():
    chapter = _load(ROOT / "data" / "2tessalonicensen" / "3.json")
    review_path = ROOT / "data" / "woordnummers-review" / "2tessalonicensen-3.json"
    review = _load(review_path)
    book = review["books"][0]
    chapter_verses = {verse["number"]: verse for verse in chapter["verses"]}

    assert _grondtekst_sha256(chapter) == GROUND_SHA
    assert review["grondtekst_bron"]["lokale_grondtekst_sha256"] == GROUND_SHA
    assert review["grondtekst_bron"]["sha256"] == TR_SHA
    assert review["source"]["sha256"] == GUIDE_SHA
    assert book["source_file_sha256"] == GUIDE_SHA
    assert [record["verse"] for record in book["verses"]] == list(range(1, 19))
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
        assert record["vervang_bronreferentie"] == f"2THESS 3:{record['verse']}"
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

    assert mapping_total == 278
    assert ground_total == 279
    assert source_total == 274
    assert deviation_total == 6
    assert composite_total == 1
    assert _mapping_digest(book["verses"]) == MAPPING_DIGEST


def test_2tessalonicensen_3_documents_every_guide_tr_difference_atomically():
    review = _load(ROOT / "data" / "woordnummers-review" / "2tessalonicensen-3.json")
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
        (4, (9,), (), ("G4771",), ()),
        (12, (6,), (6,), ("G1223",), ("G1722",)),
        (12, (7,), (), ("G3588",), ()),
        (12, (9,), (), ("G1473",), ()),
        (14, (13,), (), ("G2532",), ()),
        (18, (10,), (), ("G281",), ()),
    }


def test_2tessalonicensen_3_preserves_semantic_source_occurrences():
    review = _load(ROOT / "data" / "woordnummers-review" / "2tessalonicensen-3.json")
    verses = {record["verse"]: record for record in review["books"][0]["verses"]}

    def pair(verse_number, ground_index):
        mapping = next(
            item for item in verses[verse_number]["mappings"]
            if ground_index in item["grondindices"]
        )
        return tuple(mapping["grondindices"]), tuple(mapping["bronindices"])

    assert pair(4, 5) == ((5,), (5,))
    assert pair(4, 9) == ((9,), ())
    assert pair(4, 10) == ((10,), (7,))
    assert pair(4, 12) == ((12,), (9,))
    assert pair(5, 9) == ((9,), (11,))
    assert pair(5, 11) == ((11,), (9,))
    assert pair(5, 15) == ((15,), (17,))
    assert pair(5, 17) == ((17,), (15,))
    assert pair(6, 2) == ((2,), (2,))
    assert pair(6, 12) == ((12,), (11,))
    assert pair(8, 5) == ((5,), (3,))
    assert pair(8, 19) == ((19,), (19,))
    assert pair(12, 6) == ((6,), (6,))
    assert pair(12, 7) == ((7,), ())
    assert pair(12, 9) == ((9,), ())
    assert pair(14, 11) == ((11,), (2,))
    assert pair(14, 12) == ((12,), (1,))
    assert pair(14, 13) == ((13,), ())
    assert pair(16, 10) == ((10, 11), (10, 11))
    assert pair(17, 2) == ((2,), (3,))
    assert pair(18, 10) == ((10,), ())


def test_2tessalonicensen_3_places_articles_at_their_own_infinitive_and_noun_groups():
    review = _load(ROOT / "data" / "woordnummers-review" / "2tessalonicensen-3.json")
    chapter = _load(ROOT / "data" / "2tessalonicensen" / "3.json")
    inline = _load(ROOT / "data" / "woordnummers-inline" / "2tessalonicensen.json")
    review_verses = {
        record["verse"]: record["mappings"]
        for record in review["books"][0]["verses"]
    }
    chapter_verses = {
        verse["number"]: verse["woordnummers"]
        for verse in chapter["verses"]
    }
    inline_verses = {
        int(number): mappings
        for number, mappings in inline["chapters"]["3"].items()
    }

    def target(mappings, ground_index):
        mapping = next(
            item
            for item in mappings
            if ground_index in item["herkomst"]["grondindices"]
        )
        return {
            "tekst": mapping.get("tekst", ""),
            "anker": mapping.get("anker", ""),
            "plaats": mapping.get("plaats", ""),
        }

    expected = {
        (9, 11): {"tekst": "om", "anker": "", "plaats": ""},
        (9, 12): {"tekst": "", "anker": "na te volgen", "plaats": "voor"},
        (12, 16): {"tekst": "", "anker": "brood", "plaats": "voor"},
        (12, 17): {"tekst": "hun eigen", "anker": "", "plaats": ""},
    }
    for (verse, ground_index), wanted in expected.items():
        review_mapping = next(
            item
            for item in review_verses[verse]
            if ground_index in item["grondindices"]
        )
        review_target = {
            "tekst": review_mapping.get("tekst", ""),
            "anker": review_mapping.get("anker", ""),
            "plaats": review_mapping.get("plaats", ""),
        }
        assert review_target == wanted
        assert target(chapter_verses[verse], ground_index) == wanted
        assert target(inline_verses[verse], ground_index) == wanted


def test_2tessalonicensen_3_publishes_every_link_at_an_atomic_target():
    chapter = _load(ROOT / "data" / "2tessalonicensen" / "3.json")
    inline = _load(ROOT / "data" / "woordnummers-inline" / "2tessalonicensen.json")
    inline_verses = inline["chapters"]["3"]

    assert [len(verse["woordnummers"]) for verse in chapter["verses"]] == MAPPING_COUNTS
    assert [len(inline_verses[str(number)]) for number in range(1, 19)] == MAPPING_COUNTS
    for verse in chapter["verses"]:
        expected_links = len(verse["grondtekst"])
        for mappings in (verse["woordnummers"], inline_verses[str(verse["number"])]):
            assert sum(len(mapping["strongs"]) for mapping in mappings) == expected_links
            assert not any(mapping.get("tekst", "").strip() == verse["text2026"].strip() for mapping in mappings)

    assert sum(len(verse["woordnummers"]) for verse in chapter["verses"]) == 278
    assert sum(len(items) for items in inline_verses.values()) == 278
