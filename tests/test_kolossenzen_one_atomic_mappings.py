import json
import re
from pathlib import Path

from scripts.import_inline_woordnummers import _grondtekst_sha256


ROOT = Path(__file__).resolve().parents[1]
GROUND_SHA = "7226B261E43B58E6E5DB06AA0D9E0C16606F56FB2E1271FDBD26095CD3A2D0A3"
GUIDE_SHA = "55E93B76B56DE00A5BBFF47EDD687D7F535B08E83ED07EE9A8E6D095215011D3"
TR_SHA = "43E74492989EBADA1B4ECEB1FF7CC7C80F1923E0702A021549B90EF24E348153"


def _load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _occurrences(text, target):
    pattern = rf"(?<!\w){re.escape(target)}(?!\w)"
    return list(re.finditer(pattern, text, re.IGNORECASE | re.UNICODE))


def test_kolossenzen_1_review_is_atomic_complete_pinned_and_reachable():
    chapter = _load(ROOT / "data" / "kolossenzen" / "1.json")
    review_path = ROOT / "data" / "woordnummers-review" / "kolossenzen-1.json"
    review = _load(review_path)
    book = review["books"][0]
    chapter_verses = {verse["number"]: verse for verse in chapter["verses"]}

    assert _grondtekst_sha256(chapter) == GROUND_SHA
    assert review["grondtekst_bron"]["lokale_grondtekst_sha256"] == GROUND_SHA
    assert review["grondtekst_bron"]["sha256"] == TR_SHA
    assert review["source"]["sha256"] == GUIDE_SHA
    assert book["source_file_sha256"] == GUIDE_SHA
    assert [verse["verse"] for verse in book["verses"]] == list(range(1, 30))
    assert "voorstel_" not in review_path.read_text(encoding="utf-8")

    mapping_count = 0
    link_count = 0
    deviation_count = 0
    for record in book["verses"]:
        verse = chapter_verses[record["verse"]]
        mappings = record["mappings"]
        indices = [index for mapping in mappings for index in mapping["grondindices"]]
        mapping_count += len(mappings)
        link_count += len(indices)
        deviation_count += len(record.get("bronafwijkingen", []))

        assert sorted(indices) == list(range(len(verse["grondtekst"])))
        assert len(indices) == len(set(indices))
        assert record["source_verse"] == record["verse"]
        assert record["morphhb_verse"] == record["verse"]
        assert record["vervang_bronreferentie"] == f"COL {record['verse']}"
        assert all(mapping["reviewstatus"] == "handmatig_gecontroleerd" for mapping in mappings)
        assert all(mapping["confidence"] == 1 for mapping in mappings)
        assert all(len(mapping["grondindices"]) == 1 for mapping in mappings)
        assert all(len((mapping.get("tekst") or mapping.get("anker")).split()) <= 2 for mapping in mappings)
        assert not any(mapping.get("tekst", "").strip() == verse["text2026"].strip() for mapping in mappings)

        for mapping in mappings:
            target = mapping.get("tekst") or mapping.get("anker")
            occurrences = _occurrences(verse["text2026"], target)
            assert occurrences, (record["verse"], target)
            assert 1 <= mapping.get("voorkomen", 1) <= len(occurrences)

    assert mapping_count == 553
    assert link_count == 553
    assert deviation_count == 29


def test_kolossenzen_1_keeps_boundary_and_tr_readings_at_their_words():
    chapter = _load(ROOT / "data" / "kolossenzen" / "1.json")
    review = _load(ROOT / "data" / "woordnummers-review" / "kolossenzen-1.json")
    records = {record["verse"]: record for record in review["books"][0]["verses"]}

    def strongs_for(verse_number, target, occurrence=1):
        mapping = next(
            item
            for item in records[verse_number]["mappings"]
            if item.get("tekst") == target and item.get("voorkomen", 1) == occurrence
        )
        ground = chapter["verses"][verse_number - 1]["grondtekst"]
        return [ground[index]["strongs"] for index in mapping["grondindices"]]

    assert strongs_for(14, "bloed") == ["G129"]
    assert strongs_for(21, "nu") == ["G3570"]
    assert strongs_for(21, "ook") == ["G1161"]
    assert strongs_for(21, "verzoend") == ["G604"]
    assert strongs_for(22, "In") == ["G1722"]
    assert strongs_for(23, "Als") == ["G1489"]
    assert strongs_for(28, "Jezus") == ["G2424"]


def test_kolossenzen_1_publishes_every_link_at_an_atomic_target():
    chapter = _load(ROOT / "data" / "kolossenzen" / "1.json")
    inline = _load(ROOT / "data" / "woordnummers-inline" / "kolossenzen.json")
    inline_verses = inline["chapters"]["1"]

    for verse in chapter["verses"]:
        embedded = verse["woordnummers"]
        projected = inline_verses[str(verse["number"])]
        expected = len(verse["grondtekst"])
        for mappings in (embedded, projected):
            assert sum(len(mapping["strongs"]) for mapping in mappings) == expected
            assert not any(mapping.get("tekst", "").strip() == verse["text2026"].strip() for mapping in mappings)

    assert sum(len(verse["woordnummers"]) for verse in chapter["verses"]) == 553
    assert sum(len(items) for items in inline_verses.values()) == 553
