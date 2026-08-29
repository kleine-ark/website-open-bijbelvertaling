import json
import re
from pathlib import Path

from scripts.import_inline_woordnummers import _grondtekst_sha256


ROOT = Path(__file__).resolve().parents[1]
GROUND_SHA = "CEAD08D540137B54D9CB84262263FFC1C6FB333990D8DBC1423040A1D850C4FA"
GUIDE_SHA = "03E6B838F39595459FBC66D010309274D4210B8147B0530B59988DD2EB32A12B"


def _load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _occurrences(text, target):
    pattern = rf"(?<!\w){re.escape(target)}(?!\w)"
    return list(re.finditer(pattern, text, re.IGNORECASE | re.UNICODE))


def test_romeinen_4_is_atomic_complete_pinned_and_reachable():
    chapter = _load(ROOT / "data" / "romeinen" / "4.json")
    review_path = ROOT / "data" / "woordnummers-review" / "romeinen-4.json"
    review = _load(review_path)
    book = review["books"][0]
    chapter_verses = {verse["number"]: verse for verse in chapter["verses"]}

    assert _grondtekst_sha256(chapter) == GROUND_SHA
    assert review["grondtekst_bron"]["lokale_grondtekst_sha256"] == GROUND_SHA
    assert review["source"]["sha256"] == GUIDE_SHA
    assert book["source_file_sha256"] == GUIDE_SHA
    assert [verse["verse"] for verse in book["verses"]] == list(range(1, 26))
    assert "voorstel_" not in review_path.read_text(encoding="utf-8")
    assert "\ufffd" not in review_path.read_text(encoding="utf-8")

    mapping_count = 0
    link_count = 0
    for record in book["verses"]:
        verse = chapter_verses[record["verse"]]
        mappings = record["mappings"]
        mapping_count += len(mappings)
        indices = [index for mapping in mappings for index in mapping["grondindices"]]
        link_count += len(indices)

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

    assert mapping_count == 404
    assert link_count == 408


def test_romeinen_4_keeps_compounds_and_repeated_words_at_their_meanings():
    chapter = _load(ROOT / "data" / "romeinen" / "4.json")
    review = _load(ROOT / "data" / "woordnummers-review" / "romeinen-4.json")
    records = {record["verse"]: record for record in review["books"][0]["verses"]}

    def strongs_for(verse_number, target, occurrence=1):
        mapping = next(
            item
            for item in records[verse_number]["mappings"]
            if item.get("tekst") == target and item.get("voorkomen", 1) == occurrence
        )
        ground = chapter["verses"][verse_number - 1]["grondtekst"]
        return [ground[index]["strongs"] for index in mapping["grondindices"]]

    assert strongs_for(8, "niet") == ["G3756", "G3361"]
    assert strongs_for(16, "Daarom") == ["G1223", "G3778"]
    assert strongs_for(16, "ten einde") == ["G1519", "G3588"]
    assert strongs_for(18, "dat") == ["G1519", "G3588"]
    assert strongs_for(24, "opgewekt") == ["G1453"]

    assert next(item for item in records[7]["mappings"] if item["grondindices"] == [1])["voorkomen"] == 1
    assert next(item for item in records[7]["mappings"] if item["grondindices"] == [6])["voorkomen"] == 2
    assert [
        next(item for item in records[10]["mappings"] if item["grondindices"] == [index])["voorkomen"]
        for index in (3, 7, 10, 13)
    ] == [1, 2, 3, 4]


def test_romeinen_4_records_all_verified_guide_differences():
    review = _load(ROOT / "data" / "woordnummers-review" / "romeinen-4.json")
    deviations = [
        deviation
        for record in review["books"][0]["verses"]
        for deviation in record.get("bronafwijkingen", [])
    ]
    assert len(deviations) == 7
    assert all(deviation["reden"] == "lemma_afwijking" for deviation in deviations)
