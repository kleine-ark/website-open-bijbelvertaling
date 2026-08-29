import json
import re
from pathlib import Path

from scripts.import_inline_woordnummers import _grondtekst_sha256


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_GUIDE_SHA = "DCF9A637D5D54AA41949EF54AA780234C54F09EF9B18FD32042A457C5605AAD7"
EXPECTED_GROUND_SHA = "B4FEB3E2D31AC09A9517C785DE214E07AE22F9DCE43A4BA634A65A6BA79123F4"


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _whole_word_occurrences(text: str, target: str):
    pattern = rf"(?<!\w){re.escape(target)}(?!\w)"
    return list(re.finditer(pattern, text, re.IGNORECASE | re.UNICODE))


def test_mattheus_four_review_is_atomic_complete_pinned_and_reachable():
    chapter = _load(ROOT / "data" / "mattheus" / "4.json")
    review_path = ROOT / "data" / "woordnummers-review" / "mattheus-4.json"
    review = _load(review_path)
    book = review["books"][0]
    verses = {int(verse["number"]): verse for verse in chapter["verses"]}

    assert _grondtekst_sha256(chapter) == EXPECTED_GROUND_SHA
    assert book["grondtekst_sha256"] == EXPECTED_GROUND_SHA
    assert review["uitlijngids"]["sha256"] == EXPECTED_GUIDE_SHA
    assert [record["verse"] for record in book["verses"]] == list(range(1, 26))
    assert "voorstel_" not in review_path.read_text(encoding="utf-8")

    mapping_count = 0
    link_count = 0
    runtime_keys = set()
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
        assert all(len(mapping["grondindices"]) == 1 for mapping in mappings)

        for index, mapping in enumerate(mappings):
            target = mapping["tekst"]
            assert target
            assert len(target.split()) <= 3
            occurrences = _whole_word_occurrences(verse["text2026"], target)
            assert occurrences, (record["verse"], index, target)
            occurrence = mapping.get("voorkomen")
            if occurrence is None:
                assert len(occurrences) == 1, (record["verse"], index, target, len(occurrences))
                occurrence = 1
            else:
                assert 1 <= occurrence <= len(occurrences)
            strong = verse["grondtekst"][mapping["grondindices"][0]]["strongs"]
            key = (record["verse"], target.casefold(), occurrence, strong)
            assert key not in runtime_keys, key
            runtime_keys.add(key)

    assert mapping_count == 433
    assert link_count == 433


def test_mattheus_four_projected_records_are_atomic_and_complete():
    chapter = _load(ROOT / "data" / "mattheus" / "4.json")
    records = [mapping for verse in chapter["verses"] for mapping in verse["woordnummers"]]

    assert len(records) == 433
    assert sum(len(mapping["herkomst"]["grondindices"]) for mapping in records) == 433
    assert not any(
        mapping.get("tekst", "").strip() == verse["text2026"].strip()
        for verse in chapter["verses"]
        for mapping in verse["woordnummers"]
    )
