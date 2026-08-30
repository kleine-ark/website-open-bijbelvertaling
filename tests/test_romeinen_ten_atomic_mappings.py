import json
import re
from pathlib import Path

from scripts.import_inline_woordnummers import _grondtekst_sha256


ROOT = Path(__file__).resolve().parents[1]
GROUND_SHA = "2CB1E42FA536B5D88825C5E5F38AB6C8D11DC5B4087C0856FA144C029AD39DB5"
GUIDE_SHA = "03E6B838F39595459FBC66D010309274D4210B8147B0530B59988DD2EB32A12B"


def _load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _occurrences(text, target):
    pattern = rf"(?<!\w){re.escape(target)}(?!\w)"
    return list(re.finditer(pattern, text, re.IGNORECASE | re.UNICODE))


def _review_records():
    review = _load(ROOT / "data" / "woordnummers-review" / "romeinen-10.json")
    return review, {record["verse"]: record for record in review["books"][0]["verses"]}


def test_romeinen_10_is_atomically_complete_pinned_and_reachable():
    chapter = _load(ROOT / "data" / "romeinen" / "10.json")
    review_path = ROOT / "data" / "woordnummers-review" / "romeinen-10.json"
    review, records = _review_records()
    book = review["books"][0]
    chapter_verses = {verse["number"]: verse for verse in chapter["verses"]}

    assert _grondtekst_sha256(chapter) == GROUND_SHA
    assert review["grondtekst_bron"]["lokale_grondtekst_sha256"] == GROUND_SHA
    assert review["source"]["sha256"] == GUIDE_SHA
    assert book["source_file_sha256"] == GUIDE_SHA
    assert list(records) == list(range(1, 22))
    assert book["reviewbeperking"]["verzen"] == list(range(1, 22))
    assert "voorstel_" not in review_path.read_text(encoding="utf-8")
    assert "\ufffd" not in review_path.read_text(encoding="utf-8")

    mapping_count = 0
    link_count = 0
    empty_count = 0
    runtime_keys = set()
    for verse_number, record in records.items():
        verse = chapter_verses[verse_number]
        mappings = record["mappings"]
        indices = [index for mapping in mappings for index in mapping["grondindices"]]
        mapping_count += len(mappings)
        link_count += len(indices)
        empty_count += sum(not mapping["tekst"] for mapping in mappings)

        assert sorted(indices) == list(range(len(verse["grondtekst"])))
        assert len(indices) == len(set(indices))
        assert all(mapping["reviewstatus"] == "handmatig_gecontroleerd" for mapping in mappings)
        assert all(mapping["confidence"] == 1 for mapping in mappings)
        assert all(1 <= len(mapping["grondindices"]) <= 2 for mapping in mappings)
        assert all(
            len((mapping.get("tekst") or mapping.get("anker")).split()) <= 3
            for mapping in mappings
        )
        assert not any(
            mapping.get("tekst", "").strip() == verse["text2026"].strip()
            for mapping in mappings
        )

        for mapping in mappings:
            target = mapping.get("tekst") or mapping.get("anker")
            occurrences = _occurrences(verse["text2026"], target)
            assert occurrences, (verse_number, target)
            occurrence = mapping.get("voorkomen")
            if occurrence is None:
                assert len(occurrences) == 1, (verse_number, target, len(occurrences))
                occurrence = 1
            else:
                assert 1 <= occurrence <= len(occurrences)
            strongs = tuple(
                verse["grondtekst"][index]["strongs"]
                for index in mapping["grondindices"]
            )
            key = (verse_number, target.casefold(), occurrence, strongs)
            assert key not in runtime_keys, key
            runtime_keys.add(key)

    assert mapping_count == 342
    assert link_count == 345
    assert empty_count == 19


def test_romeinen_10_records_tr_guide_differences_at_the_atomic_mapping():
    _, records = _review_records()

    def mapping_for(verse_number, ground_index):
        return next(
            mapping
            for mapping in records[verse_number]["mappings"]
            if ground_index in mapping["grondindices"]
        )

    assert mapping_for(12, 8)["grondindices"] == [8, 10]
    assert mapping_for(12, 8)["tekst"] == "eenzelfde"
    assert mapping_for(17, 10)["gids_strongs"] == ["G5547"]
    assert mapping_for(17, 10)["tekst"] == "God"
    assert mapping_for(20, 6)["bronindices"] == [6, 7]
    assert mapping_for(20, 6)["gids_strongs"] == ["G1722", "G3588"]

    deviations = [
        deviation
        for record in records.values()
        for deviation in record.get("bronafwijkingen", [])
    ]
    assert len(deviations) == 10
    assert all(deviation["reden"] == "lemma_afwijking" for deviation in deviations)
