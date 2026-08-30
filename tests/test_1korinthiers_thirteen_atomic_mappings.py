import json
import re
from pathlib import Path

from scripts.import_inline_woordnummers import _grondtekst_sha256


ROOT = Path(__file__).resolve().parents[1]
GROUND_SHA = "E849D78FC1503089AE055CA4C7421058A36EAED060ED2614716B4AC05F7AAC9F"
GUIDE_SHA = "2323AFBC34CEAB062E242822252F09662FA6CE589E6F41DB56F239D4C17A311A"


def _load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _occurrences(text, target):
    pattern = rf"(?<!\w){re.escape(target)}(?!\w)"
    return list(re.finditer(pattern, text, re.IGNORECASE | re.UNICODE))


def test_1korinthiers_13_review_is_atomic_complete_pinned_and_reachable():
    chapter = _load(ROOT / "data" / "1korinthiers" / "13.json")
    review_path = ROOT / "data" / "woordnummers-review" / "1korinthiers-13.json"
    review = _load(review_path)
    book = review["books"][0]
    chapter_verses = {verse["number"]: verse for verse in chapter["verses"]}

    assert _grondtekst_sha256(chapter) == GROUND_SHA
    assert review["grondtekst_bron"]["lokale_grondtekst_sha256"] == GROUND_SHA
    assert review["source"]["sha256"] == GUIDE_SHA
    assert book["source_file_sha256"] == GUIDE_SHA
    assert [verse["verse"] for verse in book["verses"]] == list(range(1, 14))
    assert "voorstel_" not in review_path.read_text(encoding="utf-8")

    link_count = 0
    for record in book["verses"]:
        verse = chapter_verses[record["verse"]]
        mappings = record["mappings"]
        indices = [index for mapping in mappings for index in mapping["grondindices"]]
        link_count += len(indices)

        assert sorted(indices) == list(range(len(verse["grondtekst"])))
        assert len(indices) == len(set(indices))
        assert record["source_verse"] == record["verse"]
        assert record["morphhb_verse"] == record["verse"]
        assert all(mapping["reviewstatus"] == "handmatig_gecontroleerd" for mapping in mappings)
        assert all(mapping["confidence"] == 1 for mapping in mappings)
        assert all(1 <= len(mapping["grondindices"]) <= 2 for mapping in mappings)
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

    assert link_count == 199


def test_1korinthiers_13_publishes_all_199_links_at_atomic_targets():
    chapter = _load(ROOT / "data" / "1korinthiers" / "13.json")
    inline = _load(ROOT / "data" / "woordnummers-inline" / "1korinthiers.json")
    inline_verses = inline["chapters"]["13"]

    for verse in chapter["verses"]:
        embedded = verse["woordnummers"]
        projected = inline_verses[str(verse["number"])]
        expected = len(verse["grondtekst"])
        for mappings in (embedded, projected):
            assert sum(len(mapping["strongs"]) for mapping in mappings) == expected
            assert not any(mapping.get("tekst", "").strip() == verse["text2026"].strip() for mapping in mappings)


def test_1korinthiers_13_keeps_every_runtime_target_unambiguous():
    chapter = _load(ROOT / "data" / "1korinthiers" / "13.json")
    for verse in chapter["verses"]:
        for mapping in verse["woordnummers"]:
            target = mapping.get("tekst") or mapping.get("anker")
            occurrences = _occurrences(verse["text2026"], target)
            assert occurrences, (verse["number"], target)
            occurrence = mapping.get("voorkomen")
            if occurrence is None:
                assert len(occurrences) == 1, (verse["number"], target, len(occurrences))
            else:
                assert 1 <= occurrence <= len(occurrences)
