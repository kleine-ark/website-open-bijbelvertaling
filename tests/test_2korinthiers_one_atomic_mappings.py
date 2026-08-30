import json
import re
from pathlib import Path

from scripts.import_inline_woordnummers import _grondtekst_sha256


ROOT = Path(__file__).resolve().parents[1]
GROUND_SHA = "44392EA444FAF412AFB52FA3AFADA1E4DA70A2C24EE27E1CA8837A97D7BFACAA"
GUIDE_SHA = "23D82961D8924E4592FFEE2B62504E467A0E9E79725A72512C57127FBDDD1793"


def _load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _occurrences(text, target):
    pattern = rf"(?<!\w){re.escape(target)}(?!\w)"
    return list(re.finditer(pattern, text, re.IGNORECASE | re.UNICODE))


def test_2korinthiers_1_review_is_atomic_complete_pinned_and_reachable():
    chapter = _load(ROOT / "data" / "2korinthiers" / "1.json")
    review_path = ROOT / "data" / "woordnummers-review" / "2korinthiers-1.json"
    review = _load(review_path)

    assert "books" in review, "legacy hele-versreview moet atomair worden vervangen"
    book = review["books"][0]
    chapter_verses = {verse["number"]: verse for verse in chapter["verses"]}

    assert _grondtekst_sha256(chapter) == GROUND_SHA
    assert review["grondtekst_bron"]["lokale_grondtekst_sha256"] == GROUND_SHA
    assert review["source"]["sha256"] == GUIDE_SHA
    assert book["source_file_sha256"] == GUIDE_SHA
    assert [record["verse"] for record in book["verses"]] == list(range(1, 25))
    assert "voorstel_" not in review_path.read_text(encoding="utf-8")

    linked = 0
    for record in book["verses"]:
        verse = chapter_verses[record["verse"]]
        mappings = record["mappings"]
        indices = [index for mapping in mappings for index in mapping["grondindices"]]
        linked += len(indices)

        assert sorted(indices) == list(range(len(verse["grondtekst"])))
        assert len(indices) == len(set(indices))
        assert record["source_verse"] == record["verse"]
        assert record["morphhb_verse"] == record["verse"]
        assert all(mapping["reviewstatus"] == "handmatig_gecontroleerd" for mapping in mappings)
        assert all(mapping["confidence"] == 1 for mapping in mappings)
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

    assert linked == 488


def test_2korinthiers_1_verse_7_restores_the_cross_verse_tr_clause():
    chapter = _load(ROOT / "data" / "2korinthiers" / "1.json")
    verse = next(record for record in chapter["verses"] if record["number"] == 7)

    assert [token["woord"] for token in verse["grondtekst"][:7]] == [
        "και",
        "η",
        "ελπις",
        "ημων",
        "βεβαια",
        "υπερ",
        "υμων",
    ]
    assert [token["strongs"] for token in verse["grondtekst"][:7]] == [
        "G2532",
        "G3588",
        "G1680",
        "G1473",
        "G949",
        "G5228",
        "G4771",
    ]


def test_2korinthiers_1_publishes_all_488_links_at_atomic_targets():
    chapter = _load(ROOT / "data" / "2korinthiers" / "1.json")
    inline = _load(ROOT / "data" / "woordnummers-inline" / "2korinthiers.json")
    inline_verses = inline["chapters"]["1"]

    for verse in chapter["verses"]:
        embedded = verse["woordnummers"]
        projected = inline_verses[str(verse["number"])]
        expected = len(verse["grondtekst"])

        for mappings in (embedded, projected):
            ground_indices = [
                index
                for mapping in mappings
                for index in mapping["herkomst"].get(
                    "grondindices",
                    mapping["herkomst"].get("bronindices", []),
                )
            ]
            assert sorted(ground_indices) == list(range(expected))
            assert len(ground_indices) == len(set(ground_indices))
            assert not any(mapping.get("tekst", "").strip() == verse["text2026"].strip() for mapping in mappings)
