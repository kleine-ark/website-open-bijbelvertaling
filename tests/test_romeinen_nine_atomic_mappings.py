import json
import re
from pathlib import Path

from scripts.import_inline_woordnummers import _grondtekst_sha256


ROOT = Path(__file__).resolve().parents[1]
GROUND_SHA = "C5663297C0A2FB2E6B1D1A7F387A8CE5CB2BD73F539E7667649C685B5DE86035"
GUIDE_SHA = "03E6B838F39595459FBC66D010309274D4210B8147B0530B59988DD2EB32A12B"


def _load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _occurrences(text, target):
    pattern = rf"(?<!\w){re.escape(target)}(?!\w)"
    return list(re.finditer(pattern, text, re.IGNORECASE | re.UNICODE))


def _records():
    review = _load(ROOT / "data" / "woordnummers-review" / "romeinen-9.json")
    return review, {record["verse"]: record for record in review["books"][0]["verses"]}


def test_romeinen_9_is_atomic_complete_pinned_and_reachable():
    chapter = _load(ROOT / "data" / "romeinen" / "9.json")
    review_path = ROOT / "data" / "woordnummers-review" / "romeinen-9.json"
    review = _load(review_path)
    book = review["books"][0]
    chapter_verses = {verse["number"]: verse for verse in chapter["verses"]}

    assert _grondtekst_sha256(chapter) == GROUND_SHA
    assert review["grondtekst_bron"]["lokale_grondtekst_sha256"] == GROUND_SHA
    assert review["source"]["sha256"] == GUIDE_SHA
    assert book["source_file_sha256"] == GUIDE_SHA
    assert [record["verse"] for record in book["verses"]] == list(range(1, 34))
    assert "voorstel_" not in review_path.read_text(encoding="utf-8")
    assert "\ufffd" not in review_path.read_text(encoding="utf-8")

    mapping_count = 0
    link_count = 0
    empty_count = 0
    runtime_keys = set()
    for record in book["verses"]:
        verse = chapter_verses[record["verse"]]
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

    assert mapping_count == 530
    assert link_count == 533
    assert empty_count == 28


def test_romeinen_9_preserves_guide_boundary_and_differences_atomically():
    _, records = _records()

    def mapping_for(verse_number, ground_index):
        return next(
            mapping
            for mapping in records[verse_number]["mappings"]
            if ground_index in mapping["grondindices"]
        )

    boundary = [mapping_for(11, index) for index in range(17, 24)]
    assert [mapping["source_verse"] for mapping in boundary] == [12] * 7
    assert [mapping["bronindices"] for mapping in boundary] == [[index] for index in range(7)]
    assert sorted(
        index
        for mapping in records[12]["mappings"]
        for index in mapping["bronindices"]
    ) == list(range(7, 15))

    assert mapping_for(19, 1)["bronindices"] == [0, 3]
    assert [mapping_for(28, index)["bronindices"] for index in range(5, 10)] == [
        [],
        [],
        [],
        [],
        [],
    ]
    assert mapping_for(32, 0)["grondindices"] == [0, 1]
    assert mapping_for(32, 0)["tekst"] == "Waarom"

    deviations = [
        deviation
        for record in records.values()
        for deviation in record.get("bronafwijkingen", [])
    ]
    assert len(deviations) == 14
    assert all(deviation["reden"] == "lemma_afwijking" for deviation in deviations)
