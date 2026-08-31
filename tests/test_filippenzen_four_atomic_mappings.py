import json
import re
from pathlib import Path

from scripts.import_inline_woordnummers import _grondtekst_sha256


ROOT = Path(__file__).resolve().parents[1]
GROUND_SHA = "9EDBB91BEA509E4031C57832A3A1BB1D83180DAA18CD9A50E144ED1E49473A1B"
GUIDE_SHA = "AA4B83FA5DEAAE7CD012AD92E02ED80DBB44CA78A783E828BC2B444414A172F9"


def _load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _occurrences(text, target):
    pattern = rf"(?<!\w){re.escape(target)}(?!\w)"
    return list(re.finditer(pattern, text, re.IGNORECASE | re.UNICODE))


def test_filippenzen_4_review_is_atomic_complete_pinned_and_reachable():
    chapter = _load(ROOT / "data" / "filippenzen" / "4.json")
    review_path = ROOT / "data" / "woordnummers-review" / "filippenzen-4.json"
    review = _load(review_path)
    book = review["books"][0]
    chapter_verses = {verse["number"]: verse for verse in chapter["verses"]}

    assert _grondtekst_sha256(chapter) == GROUND_SHA
    assert review["grondtekst_bron"]["lokale_grondtekst_sha256"] == GROUND_SHA
    assert review["source"]["sha256"] == GUIDE_SHA
    assert book["source_file_sha256"] == GUIDE_SHA
    assert [verse["verse"] for verse in book["verses"]] == list(range(1, 24))
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
        assert all(mapping["reviewstatus"] == "handmatig_gecontroleerd" for mapping in mappings)
        assert all(mapping["confidence"] == 1 for mapping in mappings)
        assert all(1 <= len(mapping["grondindices"]) <= 2 for mapping in mappings)
        assert all(len((mapping.get("tekst") or mapping.get("anker")).split()) <= 2 for mapping in mappings)
        assert not any(mapping.get("tekst", "").strip() == verse["text2026"].strip() for mapping in mappings)

        for mapping in mappings:
            target = mapping.get("tekst") or mapping.get("anker")
            occurrences = _occurrences(verse["text2026"], target)
            assert occurrences, (record["verse"], target)
            assert 1 <= mapping.get("voorkomen", 1) <= len(occurrences)

    assert mapping_count == 321
    assert link_count == 359
    assert deviation_count == 5


def test_filippenzen_4_keeps_the_local_tr_readings_at_their_words():
    chapter = _load(ROOT / "data" / "filippenzen" / "4.json")
    review = _load(ROOT / "data" / "woordnummers-review" / "filippenzen-4.json")
    records = {record["verse"]: record for record in review["books"][0]["verses"]}

    def strongs_for(verse_number, target, occurrence=1):
        mapping = next(
            item
            for item in records[verse_number]["mappings"]
            if item.get("tekst") == target and item.get("voorkomen", 1) == occurrence
        )
        ground = chapter["verses"][verse_number - 1]["grondtekst"]
        return [ground[index]["strongs"] for index in mapping["grondindices"]]

    assert strongs_for(3, "En") == ["G2532"]
    assert strongs_for(11, "ben") == ["G1510"]
    assert strongs_for(11, "te zijn") == ["G1510"]
    assert strongs_for(13, "Christus") == ["G5547"]
    assert strongs_for(23, "onze") == ["G1473"]
    assert strongs_for(23, "allen") == ["G3956"]
    assert strongs_for(23, "Amen") == ["G281"]


def test_filippenzen_4_publishes_every_link_at_an_atomic_target():
    chapter = _load(ROOT / "data" / "filippenzen" / "4.json")
    inline = _load(ROOT / "data" / "woordnummers-inline" / "filippenzen.json")
    inline_verses = inline["chapters"]["4"]

    for verse in chapter["verses"]:
        embedded = verse["woordnummers"]
        projected = inline_verses[str(verse["number"])]
        expected = len(verse["grondtekst"])
        for mappings in (embedded, projected):
            assert sum(len(mapping["strongs"]) for mapping in mappings) == expected
            assert not any(mapping.get("tekst", "").strip() == verse["text2026"].strip() for mapping in mappings)

    assert sum(len(verse["woordnummers"]) for verse in chapter["verses"]) == 321
    assert sum(len(items) for items in inline_verses.values()) == 321
