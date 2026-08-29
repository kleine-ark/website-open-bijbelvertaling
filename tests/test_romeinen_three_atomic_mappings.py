import json
import re
from pathlib import Path

from scripts.import_inline_woordnummers import _grondtekst_sha256


ROOT = Path(__file__).resolve().parents[1]
GROUND_SHA = "3EAC1B08B65CA3820294F8F2791B97E091775A64E148F0E2690968891AC31856"
GUIDE_SHA = "03E6B838F39595459FBC66D010309274D4210B8147B0530B59988DD2EB32A12B"


def _load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _occurrences(text, target):
    pattern = rf"(?<!\w){re.escape(target)}(?!\w)"
    return list(re.finditer(pattern, text, re.IGNORECASE | re.UNICODE))


def test_romeinen_3_is_atomic_complete_pinned_and_reachable():
    chapter = _load(ROOT / "data" / "romeinen" / "3.json")
    review_path = ROOT / "data" / "woordnummers-review" / "romeinen-3.json"
    review = _load(review_path)
    book = review["books"][0]
    chapter_verses = {verse["number"]: verse for verse in chapter["verses"]}

    assert _grondtekst_sha256(chapter) == GROUND_SHA
    assert review["grondtekst_bron"]["lokale_grondtekst_sha256"] == GROUND_SHA
    assert review["source"]["sha256"] == GUIDE_SHA
    assert book["source_file_sha256"] == GUIDE_SHA
    assert [verse["verse"] for verse in book["verses"]] == list(range(1, 32))
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

    assert mapping_count == 425
    assert link_count == 427


def test_romeinen_3_keeps_atomic_compounds_and_local_tr_readings():
    chapter = _load(ROOT / "data" / "romeinen" / "3.json")
    review = _load(ROOT / "data" / "woordnummers-review" / "romeinen-3.json")
    records = {record["verse"]: record for record in review["books"][0]["verses"]}

    def strongs_for(verse_number, target, occurrence=1):
        mapping = next(
            item
            for item in records[verse_number]["mappings"]
            if item.get("tekst") == target and item.get("voorkomen", 1) == occurrence
        )
        ground = chapter["verses"][verse_number - 1]["grondtekst"]
        return [ground[index]["strongs"] for index in mapping["grondindices"]]

    assert strongs_for(3, "niet") == ["G3361"]
    assert strongs_for(3, "doen") == ["G2673"]
    assert strongs_for(13, "slangenvenijn") == ["G2447", "G785"]
    assert strongs_for(20, "geen") == ["G3756", "G3956"]
    assert strongs_for(30, "\u00e9\u00e9n") == ["G1520"]


def test_romeinen_3_records_all_verified_guide_differences():
    review = _load(ROOT / "data" / "woordnummers-review" / "romeinen-3.json")
    deviations = [
        deviation
        for record in review["books"][0]["verses"]
        for deviation in record.get("bronafwijkingen", [])
    ]
    assert len(deviations) == 10
    assert all(deviation["reden"] in {"lemma_afwijking", "gidstekst_afwijking"} for deviation in deviations)


def test_romeinen_3_publishes_every_link_at_an_atomic_target():
    chapter = _load(ROOT / "data" / "romeinen" / "3.json")
    inline = _load(ROOT / "data" / "woordnummers-inline" / "romeinen.json")
    inline_verses = inline["chapters"]["3"]

    for verse in chapter["verses"]:
        embedded = verse["woordnummers"]
        projected = inline_verses[str(verse["number"])]
        expected = len(verse["grondtekst"])

        for mappings in (embedded, projected):
            assert sum(len(mapping["strongs"]) for mapping in mappings) == expected
            assert not any(
                mapping.get("tekst", "").strip() == verse["text2026"].strip()
                for mapping in mappings
            )

    assert sum(len(verse["woordnummers"]) for verse in chapter["verses"]) == 425
    assert sum(len(items) for items in inline_verses.values()) == 425
