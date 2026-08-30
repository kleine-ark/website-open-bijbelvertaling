import json
import re
from pathlib import Path

from scripts.import_inline_woordnummers import _grondtekst_sha256


ROOT = Path(__file__).resolve().parents[1]
GROUND_SHA = "96BF6B65E879F41A8F94A3AA505AB4EE1BE53EF91F7A1B0D04D9BB748EC05DC1"
GUIDE_SHA = "2323AFBC34CEAB062E242822252F09662FA6CE589E6F41DB56F239D4C17A311A"


def _load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _occurrences(text, target):
    pattern = rf"(?<!\w){re.escape(target)}(?!\w)"
    return list(re.finditer(pattern, text, re.IGNORECASE | re.UNICODE))


def test_1korinthiers_2_is_atomic_and_covers_every_ground_token():
    chapter = _load(ROOT / "data" / "1korinthiers" / "2.json")
    review_path = ROOT / "data" / "woordnummers-review" / "1korinthiers-2.json"
    review = _load(review_path)
    book = review["books"][0]
    records = {record["verse"]: record for record in book["verses"]}
    chapter_verses = {verse["number"]: verse for verse in chapter["verses"]}

    assert _grondtekst_sha256(chapter) == GROUND_SHA
    assert review["grondtekst_bron"]["lokale_grondtekst_sha256"] == GROUND_SHA
    assert review["source"]["sha256"] == GUIDE_SHA
    assert book["source_file_sha256"] == GUIDE_SHA
    assert list(records) == list(range(1, 17))
    assert book["reviewbeperking"]["verzen"] == list(range(1, 17))
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

    assert mapping_count == 289
    assert link_count == 293


def test_1korinthiers_2_documents_every_guide_tr_difference():
    review = _load(ROOT / "data" / "woordnummers-review" / "1korinthiers-2.json")
    records = {record["verse"]: record for record in review["books"][0]["verses"]}
    actual = {
        (verse, tuple(item["bron_strongs"]), tuple(item["grondtekst_strongs"]))
        for verse, record in records.items()
        for item in record.get("bronafwijkingen", [])
    }
    expected = {
        (2, (), ("G3588",)),
        (3, ("G2504",), ("G2532", "G1473")),
        (4, (), ("G442",)),
        (9, ("G3745",), ("G3739",)),
        (10, ("G1063",), ("G1161",)),
        (10, (), ("G846",)),
        (11, ("G1097",), ("G1492",)),
        (13, (), ("G40",)),
        (15, ("G3588",), ("G3303",)),
    }
    assert actual == expected
