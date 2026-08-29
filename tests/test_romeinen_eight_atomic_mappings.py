import json
import re
from pathlib import Path

from scripts.import_inline_woordnummers import _grondtekst_sha256


ROOT = Path(__file__).resolve().parents[1]
GROUND_SHA = "6153B4BCFAC467EEF952B8DBDA33D7B336C33EE360C33095EC8541BAD4A6E82D"
GUIDE_SHA = "03E6B838F39595459FBC66D010309274D4210B8147B0530B59988DD2EB32A12B"


def _load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _occurrences(text, target):
    pattern = rf"(?<!\w){re.escape(target)}(?!\w)"
    return list(re.finditer(pattern, text, re.IGNORECASE | re.UNICODE))


def _records():
    review = _load(ROOT / "data" / "woordnummers-review" / "romeinen-8.json")
    return review, {record["verse"]: record for record in review["books"][0]["verses"]}


def test_romeinen_8_is_atomic_complete_pinned_and_reachable():
    chapter = _load(ROOT / "data" / "romeinen" / "8.json")
    review_path = ROOT / "data" / "woordnummers-review" / "romeinen-8.json"
    review = _load(review_path)
    book = review["books"][0]
    chapter_verses = {verse["number"]: verse for verse in chapter["verses"]}

    assert _grondtekst_sha256(chapter) == GROUND_SHA
    assert review["grondtekst_bron"]["lokale_grondtekst_sha256"] == GROUND_SHA
    assert review["source"]["sha256"] == GUIDE_SHA
    assert book["source_file_sha256"] == GUIDE_SHA
    assert [record["verse"] for record in book["verses"]] == list(range(1, 40))
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
        assert all(len(mapping["grondindices"]) == 1 for mapping in mappings)
        assert all(len((mapping.get("tekst") or mapping.get("anker")).split()) <= 4 for mapping in mappings)
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

    assert mapping_count == 663
    assert link_count == 663
    assert empty_count == 25


def test_romeinen_8_preserves_boundary_and_guide_differences_atomically():
    chapter = _load(ROOT / "data" / "romeinen" / "8.json")
    _, records = _records()

    def mapping_for(verse_number, ground_index):
        return next(
            mapping
            for mapping in records[verse_number]["mappings"]
            if mapping["grondindices"] == [ground_index]
        )

    assert mapping_for(20, 11)["bronindices"] == [11, 12, 13]
    assert mapping_for(21, 0)["tekst"] == "Op"
    assert mapping_for(21, 0)["bronindices"] == []
    assert mapping_for(21, 1)["tekst"] == "hoop"
    assert mapping_for(21, 1)["bronindices"] == []
    assert [token["strongs"] for token in chapter["verses"][20]["grondtekst"][:2]] == [
        "G1909",
        "G1680",
    ]

    assert mapping_for(28, 6)["tekst"] == "God"
    assert mapping_for(28, 6)["bronindices"] == [3, 4, 12]
    assert mapping_for(34, 4)["tekst"] == "Die"
    assert mapping_for(34, 4)["voorkomen"] == 2
    assert mapping_for(34, 4)["bronindices"] == [4, 5]
    assert mapping_for(35, 15)["tekst"] == ""
    assert mapping_for(35, 15)["anker"] == "naaktheid"
    assert mapping_for(39, 20)["tekst"] == ""
    assert mapping_for(39, 20)["anker"] == "Heere"

    deviations = [
        deviation
        for record in records.values()
        for deviation in record.get("bronafwijkingen", [])
    ]
    assert len(deviations) == 19
    assert records[20]["bronafwijkingen"][0]["bron_strongs"] == [
        "G5293",
        "G1909",
        "G1680",
    ]
    assert records[20]["bronafwijkingen"][0]["grondtekst_strongs"] == ["G5293"]
    assert records[34]["bronafwijkingen"][0]["bron_strongs"] == ["G2424", "G3588"]
    assert records[34]["bronafwijkingen"][0]["grondtekst_strongs"] == ["G3588"]
