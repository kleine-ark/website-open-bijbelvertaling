import json
import re
from pathlib import Path

from scripts.import_inline_woordnummers import _grondtekst_sha256


ROOT = Path(__file__).resolve().parents[1]
GROUND_SHA = "679840A8374D1E18D869BEC60707DC42D080CDB113ED6F967A76CC4E5C3FAB11"
GUIDE_SHA = "2323AFBC34CEAB062E242822252F09662FA6CE589E6F41DB56F239D4C17A311A"


def _load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _occurrences(text, target):
    pattern = rf"(?<!\w){re.escape(target)}(?!\w)"
    return list(re.finditer(pattern, text, re.IGNORECASE | re.UNICODE))


def test_1korinthiers_3_is_atomic_and_covers_every_ground_token():
    chapter = _load(ROOT / "data" / "1korinthiers" / "3.json")
    review_path = ROOT / "data" / "woordnummers-review" / "1korinthiers-3.json"
    review = _load(review_path)
    book = review["books"][0]
    records = {record["verse"]: record for record in book["verses"]}
    chapter_verses = {verse["number"]: verse for verse in chapter["verses"]}

    assert _grondtekst_sha256(chapter) == GROUND_SHA
    assert review["grondtekst_bron"]["lokale_grondtekst_sha256"] == GROUND_SHA
    assert review["source"]["sha256"] == GUIDE_SHA
    assert book["source_file_sha256"] == GUIDE_SHA
    assert list(records) == list(range(1, 24))
    assert book["reviewbeperking"]["verzen"] == list(range(1, 24))
    assert "voorstel_" not in review_path.read_text(encoding="utf-8")
    assert "\ufffd" not in review_path.read_text(encoding="utf-8")

    link_count = 0
    mapping_count = 0
    runtime_keys = set()
    for verse_number, record in records.items():
        verse = chapter_verses[verse_number]
        mappings = record["mappings"]
        indices = [index for mapping in mappings for index in mapping["grondindices"]]
        mapping_count += len(mappings)
        link_count += len(indices)

        assert sorted(indices) == list(range(len(verse["grondtekst"])))
        assert len(indices) == len(set(indices))
        assert all(mapping["reviewstatus"] == "handmatig_gecontroleerd" for mapping in mappings)
        assert all(mapping["confidence"] == 1 for mapping in mappings)
        assert all(1 <= len(mapping["grondindices"]) <= 2 for mapping in mappings)
        assert all(
            len((mapping.get("tekst") or mapping.get("anker")).split()) <= 4
            for mapping in mappings
        )
        assert not any(
            mapping.get("tekst", "").strip() == verse["text2026"].strip()
            for mapping in mappings
        )

        for mapping in mappings:
            target = mapping.get("tekst") or mapping.get("anker")
            occurrences = _occurrences(verse["text2026"], target)
            assert occurrences, (verse_number, target)
            occurrence = mapping.get("voorkomen")
            if occurrence is None:
                assert len(occurrences) == 1, (verse_number, target, len(occurrences))
                occurrence = 1
            else:
                assert 1 <= occurrence <= len(occurrences)
            strongs = tuple(
                verse["grondtekst"][index]["strongs"]
                for index in mapping["grondindices"]
            )
            key = (verse_number, target.casefold(), occurrence, strongs)
            assert key not in runtime_keys, key
            runtime_keys.add(key)

    assert mapping_count == 343
    assert link_count == 347


def test_1korinthiers_3_documents_every_guide_tr_difference():
    review = _load(ROOT / "data" / "woordnummers-review" / "1korinthiers-3.json")
    records = {record["verse"]: record for record in review["books"][0]["verses"]}
    actual = {
        (verse, tuple(item["bron_strongs"]), tuple(item["grondtekst_strongs"]))
        for verse, record in records.items()
        for item in record.get("bronafwijkingen", [])
    }
    expected = {
        (1, ("G2504",), ("G2532", "G1473")),
        (1, ("G4560",), ("G4559",)),
        (2, (), ("G2532",)),
        (2, ("G3761",), ("G3777",)),
        (3, (), ("G2532",)),
        (3, (), ("G1370",)),
        (4, ("G3756",), ("G3780",)),
        (4, ("G444",), ("G4559",)),
        (5, ("G1510", "G1510"), ("G1510",)),
        (5, (), ("G235", "G2228")),
        (11, (), ("G3588",)),
        (12, (), ("G3778",)),
        (13, ("G846", "G2041"), ("G2041",)),
        (22, (), ("G1510",)),
    }
    assert actual == expected
