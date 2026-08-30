import json
import re
from pathlib import Path

from scripts.import_inline_woordnummers import _grondtekst_sha256


ROOT = Path(__file__).resolve().parents[1]
GROUND_SHA = "D66F8D75405E179FF5D1536F1DFA1A6FE7351157F6214D306BB012289EE3AACD"
GUIDE_SHA = "2323AFBC34CEAB062E242822252F09662FA6CE589E6F41DB56F239D4C17A311A"


def _load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _occurrences(text, target):
    pattern = rf"(?<!\w){re.escape(target)}(?!\w)"
    return list(re.finditer(pattern, text, re.IGNORECASE | re.UNICODE))


def test_1korinthiers_5_is_atomic_complete_pinned_and_reachable():
    chapter = _load(ROOT / "data" / "1korinthiers" / "5.json")
    review_path = ROOT / "data" / "woordnummers-review" / "1korinthiers-5.json"
    review = _load(review_path)
    book = review["books"][0]
    chapter_verses = {verse["number"]: verse for verse in chapter["verses"]}

    assert _grondtekst_sha256(chapter) == GROUND_SHA
    assert review["grondtekst_bron"]["lokale_grondtekst_sha256"] == GROUND_SHA
    assert review["source"]["sha256"] == GUIDE_SHA
    assert book["source_file_sha256"] == GUIDE_SHA
    assert [verse["verse"] for verse in book["verses"]] == list(range(1, 14))
    assert "voorstel_" not in review_path.read_text(encoding="utf-8")

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
            else:
                assert 1 <= occurrence <= len(occurrences)

    assert mapping_count == 232
    assert link_count == 232


def test_1korinthiers_5_keeps_local_tr_readings_at_their_words():
    chapter = _load(ROOT / "data" / "1korinthiers" / "5.json")
    review = _load(ROOT / "data" / "woordnummers-review" / "1korinthiers-5.json")
    records = {record["verse"]: record for record in review["books"][0]["verses"]}

    def strongs_for(verse_number, target, occurrence=1):
        mapping = next(
            item
            for item in records[verse_number]["mappings"]
            if item.get("tekst") == target and item.get("voorkomen", 1) == occurrence
        )
        ground = chapter["verses"][verse_number - 1]["grondtekst"]
        return [ground[index]["strongs"] for index in mapping["grondindices"]]

    assert strongs_for(1, "genoemd wordt") == ["G3687"]
    assert strongs_for(2, "weggedaan wordt") == ["G1808"]
    assert strongs_for(4, "Christus", 2) == ["G5547"]
    assert strongs_for(7, "voor") == ["G5228"]
    assert strongs_for(11, "nu") == ["G3570"]


def test_1korinthiers_5_publishes_every_link_at_an_atomic_target():
    chapter = _load(ROOT / "data" / "1korinthiers" / "5.json")
    inline = _load(ROOT / "data" / "woordnummers-inline" / "1korinthiers.json")
    inline_verses = inline["chapters"]["5"]

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

    assert sum(len(verse["woordnummers"]) for verse in chapter["verses"]) == 232
    assert sum(len(items) for items in inline_verses.values()) == 232
