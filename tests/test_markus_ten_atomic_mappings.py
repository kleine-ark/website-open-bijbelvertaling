import json
import re
from pathlib import Path

from scripts.import_inline_woordnummers import _grondtekst_sha256


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_GROUND_SHA = "5A4611732606D8BDF8C8D1C734E83FF417BBA77BB80A963602BC14E2DC33DB4C"
EXPECTED_GUIDE_SHA = "B80A504D1DDF0A7E63A4CFCD8B85D246A6C3422813461D5B6D792F76479B9EC5"


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _whole_word_occurrences(text: str, target: str):
    pattern = rf"(?<!\w){re.escape(target)}(?!\w)"
    return list(re.finditer(pattern, text, re.IGNORECASE | re.UNICODE))


def test_markus_ten_review_is_atomic_complete_pinned_and_reachable():
    chapter = _load(ROOT / "data" / "markus" / "10.json")
    review_path = ROOT / "data" / "woordnummers-review" / "markus-10.json"
    review = _load(review_path)
    book = review["books"][0]
    verses = {int(verse["number"]): verse for verse in chapter["verses"]}

    assert _grondtekst_sha256(chapter) == EXPECTED_GROUND_SHA
    assert book["grondtekst_sha256"] == EXPECTED_GROUND_SHA
    assert review["uitlijngids"]["sha256"] == EXPECTED_GUIDE_SHA
    assert [record["verse"] for record in book["verses"]] == list(range(1, 53))
    assert "voorstel_" not in review_path.read_text(encoding="utf-8")

    mapping_count = 0
    link_count = 0
    for record in book["verses"]:
        verse = verses[record["verse"]]
        mappings = record["mappings"]
        mapping_count += len(mappings)
        indices = [index for mapping in mappings for index in mapping["grondindices"]]
        link_count += len(indices)

        assert sorted(indices) == list(range(len(verse["grondtekst"])))
        assert len(indices) == len(set(indices))
        assert all(mapping["bronindices"] == mapping["grondindices"] for mapping in mappings)
        assert all(mapping["reviewstatus"] == "handmatig_gecontroleerd" for mapping in mappings)
        assert all(mapping["confidence"] == 1 for mapping in mappings)
        assert all(1 <= len(mapping["grondindices"]) <= 2 for mapping in mappings)
        assert all(len((mapping.get("tekst") or mapping.get("anker")).split()) <= 3 for mapping in mappings)
        assert not any(mapping.get("tekst", "").strip() == verse["text2026"].strip() for mapping in mappings)

        for mapping in mappings:
            target = mapping.get("tekst") or mapping.get("anker")
            occurrences = _whole_word_occurrences(verse["text2026"], target)
            assert occurrences, (record["verse"], target)
            occurrence = mapping.get("voorkomen")
            if occurrence is None:
                assert len(occurrences) == 1, (record["verse"], target, len(occurrences))
            else:
                assert 1 <= occurrence <= len(occurrences)

    assert mapping_count == 900
    assert link_count == 912


def test_markus_ten_tr_additions_missing_from_the_guide_remain_explicit():
    review = _load(ROOT / "data" / "woordnummers-review" / "markus-10.json")
    records = {record["verse"]: record for record in review["books"][0]["verses"]}

    verse_21 = records[21]
    missing_21 = {
        tuple(item["grondindices"])
        for item in verse_21["gidsafwijkingen"]
        if not item["bronindices"]
    }
    assert {(30,), (31,), (32,)} <= missing_21

    verse_24 = records[24]
    missing_24 = {
        tuple(item["grondindices"])
        for item in verse_24["gidsafwijkingen"]
        if not item["bronindices"]
    }
    assert {(19,), (20,), (21,), (22,), (23,)} <= missing_24
