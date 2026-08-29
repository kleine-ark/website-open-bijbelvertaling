import json
import re
from pathlib import Path

from scripts.import_inline_woordnummers import _grondtekst_sha256


ROOT = Path(__file__).resolve().parents[1]
GROUND_SHA = "6B93FB4EF71FD59B8DB9B33DAC6D015BE2B83E3293D9BB6E4C26631D81B11245"
GUIDE_SHA = "03E6B838F39595459FBC66D010309274D4210B8147B0530B59988DD2EB32A12B"


def _load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _occurrences(text, target):
    pattern = rf"(?<!\w){re.escape(target)}(?!\w)"
    return list(re.finditer(pattern, text, re.IGNORECASE | re.UNICODE))


def _records():
    review = _load(ROOT / "data" / "woordnummers-review" / "romeinen-7.json")
    return review, {record["verse"]: record for record in review["books"][0]["verses"]}


def test_romeinen_7_is_atomic_complete_pinned_and_reachable():
    chapter = _load(ROOT / "data" / "romeinen" / "7.json")
    review_path = ROOT / "data" / "woordnummers-review" / "romeinen-7.json"
    review = _load(review_path)
    book = review["books"][0]
    chapter_verses = {verse["number"]: verse for verse in chapter["verses"]}

    assert _grondtekst_sha256(chapter) == GROUND_SHA
    assert review["grondtekst_bron"]["lokale_grondtekst_sha256"] == GROUND_SHA
    assert review["source"]["sha256"] == GUIDE_SHA
    assert book["source_file_sha256"] == GUIDE_SHA
    assert [record["verse"] for record in book["verses"]] == list(range(1, 27))
    assert "voorstel_" not in review_path.read_text(encoding="utf-8")
    assert "\ufffd" not in review_path.read_text(encoding="utf-8")

    mapping_count = 0
    link_count = 0
    grouped_count = 0
    empty_count = 0
    runtime_keys = set()
    for record in book["verses"]:
        verse = chapter_verses[record["verse"]]
        mappings = record["mappings"]
        indices = [index for mapping in mappings for index in mapping["grondindices"]]
        mapping_count += len(mappings)
        link_count += len(indices)
        grouped_count += sum(len(mapping["grondindices"]) == 2 for mapping in mappings)
        empty_count += sum(not mapping["tekst"] for mapping in mappings)

        assert sorted(indices) == list(range(len(verse["grondtekst"])))
        assert len(indices) == len(set(indices))
        assert all(mapping["reviewstatus"] == "handmatig_gecontroleerd" for mapping in mappings)
        assert all(mapping["confidence"] == 1 for mapping in mappings)
        assert all(1 <= len(mapping["grondindices"]) <= 2 for mapping in mappings)
        assert all(len((mapping.get("tekst") or mapping.get("anker")).split()) <= 2 for mapping in mappings)
        assert not any(mapping.get("tekst", "").strip() == verse["text2026"].strip() for mapping in mappings)

        for mapping in mappings:
            target = mapping.get("tekst") or mapping.get("anker")
            occurrences = _occurrences(verse["text2026"], target)
            assert occurrences, (record["verse"], target)
            occurrence = mapping.get("voorkomen")
            if occurrence is None:
                assert len(occurrences) == 1, (record["verse"], target, len(occurrences))
                occurrence = 1
            else:
                assert 1 <= occurrence <= len(occurrences)
            strongs = tuple(
                verse["grondtekst"][index]["strongs"]
                for index in mapping["grondindices"]
            )
            key = (record["verse"], target.casefold(), occurrence, strongs)
            assert key not in runtime_keys, key
            runtime_keys.add(key)

    assert mapping_count == 461
    assert link_count == 468
    assert grouped_count == 7
    assert empty_count == 6


def test_romeinen_7_preserves_meaningful_compounds_and_guide_differences():
    chapter = _load(ROOT / "data" / "romeinen" / "7.json")
    _, records = _records()

    def strongs_for(verse_number, target, occurrence=1):
        mapping = next(
            item
            for item in records[verse_number]["mappings"]
            if item.get("tekst") == target
            and item.get("voorkomen", 1) == occurrence
        )
        ground = chapter["verses"][verse_number - 1]["grondtekst"]
        return [ground[index]["strongs"] for index in mapping["grondindices"]]

    assert strongs_for(1, "zolang") == ["G3745", "G5550"]
    assert strongs_for(13, "boven mate") == ["G2596", "G5236"]
    assert strongs_for(23, "mijn", 1) == ["G3588", "G1473"]
    assert strongs_for(23, "mijn", 3) == ["G3588", "G1473"]
    assert strongs_for(26, "wet", 1) == ["G3551"]

    deviations = [
        deviation
        for record in records.values()
        for deviation in record.get("bronafwijkingen", [])
    ]
    assert len(deviations) == 5
    assert records[7]["bronafwijkingen"][0]["bron_strongs"] == ["G2036"]
    assert records[7]["bronafwijkingen"][0]["grondtekst_strongs"] == ["G3004"]
    assert records[14]["bronafwijkingen"][0]["bron_strongs"] == ["G4560"]
    assert records[14]["bronafwijkingen"][0]["grondtekst_strongs"] == ["G4559"]
    assert records[18]["bronafwijkingen"][0]["bron_strongs"] == []
    assert records[18]["bronafwijkingen"][0]["grondtekst_strongs"] == ["G2147"]
    assert records[25]["bronafwijkingen"][0]["bron_strongs"] == ["G5485", "G1161"]
    assert records[25]["bronafwijkingen"][0]["grondtekst_strongs"] == ["G2168"]
