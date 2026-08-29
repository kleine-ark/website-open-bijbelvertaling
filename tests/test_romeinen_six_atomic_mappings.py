import json
import re
from pathlib import Path

from scripts.import_inline_woordnummers import _grondtekst_sha256


ROOT = Path(__file__).resolve().parents[1]
GROUND_SHA = "AFDD698138E7BDF52B3CA1A1F714BE830FC4F9D1F06FFCF24D5E2E8C45D4B52C"
GUIDE_SHA = "03E6B838F39595459FBC66D010309274D4210B8147B0530B59988DD2EB32A12B"


def _load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _occurrences(text, target):
    pattern = rf"(?<!\w){re.escape(target)}(?!\w)"
    return list(re.finditer(pattern, text, re.IGNORECASE | re.UNICODE))


def _records():
    review = _load(ROOT / "data" / "woordnummers-review" / "romeinen-6.json")
    return review, {record["verse"]: record for record in review["books"][0]["verses"]}


def test_romeinen_6_is_atomic_complete_pinned_and_reachable():
    chapter = _load(ROOT / "data" / "romeinen" / "6.json")
    review_path = ROOT / "data" / "woordnummers-review" / "romeinen-6.json"
    review = _load(review_path)
    book = review["books"][0]
    chapter_verses = {verse["number"]: verse for verse in chapter["verses"]}

    assert _grondtekst_sha256(chapter) == GROUND_SHA
    assert review["grondtekst_bron"]["lokale_grondtekst_sha256"] == GROUND_SHA
    assert review["source"]["sha256"] == GUIDE_SHA
    assert book["source_file_sha256"] == GUIDE_SHA
    assert [verse["verse"] for verse in book["verses"]] == list(range(1, 24))
    assert "voorstel_" not in review_path.read_text(encoding="utf-8")
    assert "\ufffd" not in review_path.read_text(encoding="utf-8")

    mapping_count = 0
    link_count = 0
    grouped_count = 0
    for record in book["verses"]:
        verse = chapter_verses[record["verse"]]
        mappings = record["mappings"]
        mapping_count += len(mappings)
        indices = [index for mapping in mappings for index in mapping["grondindices"]]
        link_count += len(indices)
        grouped_count += sum(len(mapping["grondindices"]) == 2 for mapping in mappings)

        assert sorted(indices) == list(range(len(verse["grondtekst"])))
        assert len(indices) == len(set(indices))
        assert record["source_verse"] == record["verse"]
        assert record["morphhb_verse"] == record["verse"]
        assert all(mapping["reviewstatus"] == "handmatig_gecontroleerd" for mapping in mappings)
        assert all(mapping["confidence"] == 1 for mapping in mappings)
        assert all(1 <= len(mapping["grondindices"]) <= 2 for mapping in mappings)
        assert all(len((mapping.get("tekst") or mapping.get("anker")).split()) <= 3 for mapping in mappings)
        assert not any(mapping.get("tekst", "").strip() == verse["text2026"].strip() for mapping in mappings)

        for mapping in mappings:
            target = mapping.get("tekst") or mapping.get("anker")
            occurrences = _occurrences(verse["text2026"], target)
            assert occurrences, (record["verse"], target)
            occurrence = mapping.get("voorkomen")
            if occurrence is None:
                assert len(occurrences) == 1, (record["verse"], target, len(occurrences))
            else:
                assert 1 <= occurrence <= len(occurrences)

    assert mapping_count == 364
    assert link_count == 372
    assert grouped_count == 8


def test_romeinen_6_keeps_compounds_and_repeated_words_at_their_meanings():
    chapter = _load(ROOT / "data" / "romeinen" / "6.json")
    _, records = _records()

    def strongs_for(verse_number, target, occurrence=1):
        mapping = next(
            item
            for item in records[verse_number]["mappings"]
            if item.get("tekst") == target and item.get("voorkomen", 1) == occurrence
        )
        ground = chapter["verses"][verse_number - 1]["grondtekst"]
        return [ground[index]["strongs"] for index in mapping["grondindices"]]

    assert strongs_for(2, "daarin") == ["G1722", "G846"]
    assert strongs_for(5, "Zijn", 2) == ["G3588", "G846"]
    assert strongs_for(13, "uw", 1) == ["G3588", "G4771"]
    assert strongs_for(19, "uw", 3) == ["G3588", "G4771"]
    assert strongs_for(21, "waarover") == ["G1909", "G3739"]
    assert strongs_for(22, "uw") == ["G3588", "G4771"]
    assert strongs_for(9, "niet meer", 1) == ["G3765"]
    assert strongs_for(9, "niet meer", 2) == ["G3765"]
    assert strongs_for(10, "dat", 1) == ["G3739"]
    assert strongs_for(10, "dat", 3) == ["G3739"]


def test_romeinen_6_records_all_verified_guide_differences():
    _, records = _records()
    deviations = [
        deviation
        for record in records.values()
        for deviation in record.get("bronafwijkingen", [])
    ]

    assert len(deviations) == 6
    assert all(deviation["reden"] == "lemma_afwijking" for deviation in deviations)
    assert all(deviation["bron_strongs"] != deviation["grondtekst_strongs"] for deviation in deviations)
    assert [deviation["grondtekst_strongs"] for deviation in records[11]["bronafwijkingen"]] == [
        ["G3588"],
        ["G2962"],
        ["G1473"],
    ]
    assert [deviation["grondtekst_strongs"] for deviation in records[12]["bronafwijkingen"]] == [
        ["G1722"],
        ["G846"],
    ]
    assert records[13]["bronafwijkingen"][0]["bron_strongs"] == ["G5616"]
    assert records[13]["bronafwijkingen"][0]["grondtekst_strongs"] == ["G5613"]
