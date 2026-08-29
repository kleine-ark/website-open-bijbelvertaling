import json
import re
from pathlib import Path

from scripts.import_inline_woordnummers import _grondtekst_sha256


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_GROUND_SHA = "D77DE9D8007510BEEF988FDE7C82278430C36BE16B56C6569119169E41FA9036"
EXPECTED_GUIDE_SHA = "03E6B838F39595459FBC66D010309274D4210B8147B0530B59988DD2EB32A12B"
EXPECTED_COUNTS = [
    22, 15, 21, 23, 19, 7, 14, 16, 16, 16, 7, 15, 16, 19, 24,
    17, 12, 12, 10, 15, 12, 10, 12, 13, 17, 16, 17, 16, 23,
]


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _whole_word_occurrences(text: str, target: str):
    pattern = rf"(?<!\w){re.escape(target)}(?!\w)"
    return list(re.finditer(pattern, text, re.IGNORECASE | re.UNICODE))


def test_romeinen_two_ground_layer_matches_the_review_pin():
    chapter = _load(ROOT / "data" / "romeinen" / "2.json")
    assert _grondtekst_sha256(chapter) == EXPECTED_GROUND_SHA
    assert [verse["number"] for verse in chapter["verses"]] == list(range(1, 30))
    assert [len(verse["grondtekst"]) for verse in chapter["verses"]] == EXPECTED_COUNTS
    assert sum(EXPECTED_COUNTS) == 452


def test_romeinen_two_review_is_atomic_complete_pinned_and_reachable():
    chapter = _load(ROOT / "data" / "romeinen" / "2.json")
    review_path = ROOT / "data" / "woordnummers-review" / "romeinen-2.json"
    review = _load(review_path)
    book = review["books"][0]
    verses = {verse["number"]: verse for verse in chapter["verses"]}

    assert book["grondtekst_sha256"] == EXPECTED_GROUND_SHA
    assert review["uitlijngids"]["sha256"] == EXPECTED_GUIDE_SHA
    assert [record["verse"] for record in book["verses"]] == list(range(1, 30))
    assert "voorstel_" not in review_path.read_text(encoding="utf-8")

    mapping_count = 0
    runtime_keys = set()
    for record in book["verses"]:
        verse = verses[record["verse"]]
        mappings = record["mappings"]
        mapping_count += len(mappings)
        indices = [index for mapping in mappings for index in mapping["grondindices"]]

        assert sorted(indices) == list(range(len(verse["grondtekst"])))
        assert len(indices) == len(set(indices))
        assert all(mapping["bronindices"] == mapping["grondindices"] for mapping in mappings)
        assert all(mapping["reviewstatus"] == "handmatig_gecontroleerd" for mapping in mappings)
        assert all(mapping["confidence"] == 1 for mapping in mappings)
        assert all(len(mapping["grondindices"]) == 1 for mapping in mappings)

        for index, mapping in enumerate(mappings):
            target = mapping.get("tekst") or mapping.get("anker")
            occurrences = _whole_word_occurrences(verse["text2026"], target)
            assert occurrences, (record["verse"], index, target)
            occurrence = mapping.get("voorkomen", 1)
            assert 1 <= occurrence <= len(occurrences)
            strong = verse["grondtekst"][mapping["grondindices"][0]]["strongs"]
            key = (record["verse"], target.casefold(), occurrence, strong)
            assert key not in runtime_keys, key
            runtime_keys.add(key)

    assert mapping_count == 452


def test_romeinen_two_records_the_verified_guide_differences():
    review = _load(ROOT / "data" / "woordnummers-review" / "romeinen-2.json")
    records = {record["verse"]: record for record in review["books"][0]["verses"]}
    assert records[8]["bronafwijkingen"][0]["grondindices"] == [6]
    assert records[13]["bronafwijkingen"][0]["grondindices"] == [4, 13]
    assert records[26]["bronafwijkingen"][0]["grondindices"] == [9]
