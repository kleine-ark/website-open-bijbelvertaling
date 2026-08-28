import json
import re
from pathlib import Path

from scripts.import_inline_woordnummers import _grondtekst_sha256


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_GUIDE_SHA = "B128A928256CA6B9E206731B3CF0B83F40003FFB4814E9C573E5EFCB12223EA7"
EXPECTED_GROUND_SHA = "07B80F448008419493352642684BFCA2A1812B1978C2647FDB401CC65B664277"


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _whole_word_occurrences(text: str, target: str):
    pattern = rf"(?<!\w){re.escape(target)}(?!\w)"
    return list(re.finditer(pattern, text, re.IGNORECASE | re.UNICODE))


def test_lukas_twenty_three_review_is_atomic_complete_pinned_and_reachable():
    chapter = _load(ROOT / "data" / "lukas" / "23.json")
    review_path = ROOT / "data" / "woordnummers-review" / "lukas-23.json"
    review = _load(review_path)
    book = review["books"][0]
    verses = {int(verse["number"]): verse for verse in chapter["verses"]}

    assert _grondtekst_sha256(chapter) == EXPECTED_GROUND_SHA
    assert book["grondtekst_sha256"] == EXPECTED_GROUND_SHA
    assert review["uitlijngids"]["sha256"] == EXPECTED_GUIDE_SHA
    assert [record["verse"] for record in book["verses"]] == list(range(1, 57))
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
        assert all(1 <= len(mapping["grondindices"]) <= 4 for mapping in mappings)
        assert all(len(mapping["tekst"].split()) <= 4 for mapping in mappings)
        assert not any(mapping["tekst"].strip() == verse["text2026"].strip() for mapping in mappings)

        for mapping in mappings:
            target = mapping["tekst"] or mapping["anker"]
            occurrences = _whole_word_occurrences(verse["text2026"], target)
            assert occurrences, (record["verse"], target)
            occurrence = mapping.get("voorkomen")
            if occurrence is None:
                assert len(occurrences) == 1, (record["verse"], target, len(occurrences))
            else:
                assert 1 <= occurrence <= len(occurrences)
            if not mapping["tekst"]:
                assert mapping["plaats"] in {"voor", "na"}
                assert mapping["status"] == "niet_afzonderlijk_weergegeven"

    assert mapping_count == 732
    assert link_count == 879


def test_lukas_twenty_three_projected_records_are_atomic_and_complete():
    chapter = _load(ROOT / "data" / "lukas" / "23.json")
    records = [mapping for verse in chapter["verses"] for mapping in verse["woordnummers"]]

    assert len(records) == 732
    assert sum(len(mapping["herkomst"]["grondindices"]) for mapping in records) == 879
    assert not any(
        mapping.get("tekst", "").strip() == verse["text2026"].strip()
        for verse in chapter["verses"]
        for mapping in verse["woordnummers"]
    )
