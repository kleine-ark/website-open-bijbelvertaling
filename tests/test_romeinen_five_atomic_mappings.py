import json
import re
from pathlib import Path

from scripts.import_inline_woordnummers import _grondtekst_sha256


ROOT = Path(__file__).resolve().parents[1]
GROUND_SHA = "8BA77F892DE7D70EB538BABCDD03723168980A0234A892C66BDA713DB87AD518"
GUIDE_SHA = "03E6B838F39595459FBC66D010309274D4210B8147B0530B59988DD2EB32A12B"


def _load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _occurrences(text, target):
    pattern = rf"(?<!\w){re.escape(target)}(?!\w)"
    return list(re.finditer(pattern, text, re.IGNORECASE | re.UNICODE))


def test_romeinen_5_is_atomic_complete_pinned_and_reachable():
    chapter = _load(ROOT / "data" / "romeinen" / "5.json")
    review_path = ROOT / "data" / "woordnummers-review" / "romeinen-5.json"
    review = _load(review_path)
    book = review["books"][0]
    chapter_verses = {verse["number"]: verse for verse in chapter["verses"]}

    assert _grondtekst_sha256(chapter) == GROUND_SHA
    assert review["grondtekst_bron"]["lokale_grondtekst_sha256"] == GROUND_SHA
    assert review["source"]["sha256"] == GUIDE_SHA
    assert book["source_file_sha256"] == GUIDE_SHA
    assert [verse["verse"] for verse in book["verses"]] == list(range(1, 22))
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

    assert mapping_count == 428
    assert link_count == 431


def test_romeinen_5_keeps_compounds_and_repeated_words_at_their_meanings():
    chapter = _load(ROOT / "data" / "romeinen" / "5.json")
    review = _load(ROOT / "data" / "woordnummers-review" / "romeinen-5.json")
    records = {record["verse"]: record for record in review["books"][0]["verses"]}

    def strongs_for(verse_number, target, occurrence=1):
        mapping = next(
            item
            for item in records[verse_number]["mappings"]
            if item.get("tekst") == target and item.get("voorkomen", 1) == occurrence
        )
        ground = chapter["verses"][verse_number - 1]["grondtekst"]
        return [ground[index]["strongs"] for index in mapping["grondindices"]]

    assert strongs_for(2, "waarin") == ["G1722", "G3739"]
    assert strongs_for(12, "Daarom") == ["G1223", "G3778"]
    assert strongs_for(12, "waarin") == ["G1909", "G3739"]
    assert strongs_for(6, "nog") == ["G2089"]
    assert strongs_for(13, "was") == ["G2258"]
    assert strongs_for(9, "door", 1) == ["G1722"]
    assert strongs_for(9, "door", 2) == ["G1223"]

    assert next(item for item in records[17]["mappings"] if item["grondindices"] == [10])["voorkomen"] == 1
    assert next(item for item in records[17]["mappings"] if item["grondindices"] == [29])["voorkomen"] == 3


def test_romeinen_5_records_all_verified_guide_differences():
    review = _load(ROOT / "data" / "woordnummers-review" / "romeinen-5.json")
    deviations = [
        deviation
        for record in review["books"][0]["verses"]
        for deviation in record.get("bronafwijkingen", [])
    ]

    assert len(deviations) == 2
    assert all(deviation["reden"] == "lemma_afwijking" for deviation in deviations)
    assert deviations[0]["bron_strongs"] == ["G2089", "G2089"]
    assert deviations[0]["grondtekst_strongs"] == ["G2089"]
    assert deviations[1]["bron_strongs"] == ["G1510"]
    assert deviations[1]["grondtekst_strongs"] == ["G2258"]
