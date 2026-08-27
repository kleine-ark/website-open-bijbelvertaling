import json
import re
from pathlib import Path

from scripts.import_inline_woordnummers import _grondtekst_sha256


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_GROUND_SHA = "546A42F336FAF6E460DA2194B055755DF5BD6CFA1B77CD5B1471A137EDBC4F58"
EXPECTED_GUIDE_SHA = "B80A504D1DDF0A7E63A4CFCD8B85D246A6C3422813461D5B6D792F76479B9EC5"


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _whole_word_occurrences(text: str, target: str):
    pattern = rf"(?<!\w){re.escape(target)}(?!\w)"
    return list(re.finditer(pattern, text, re.IGNORECASE | re.UNICODE))


def test_markus_eight_review_is_atomic_complete_pinned_and_reachable():
    chapter = _load(ROOT / "data" / "markus" / "8.json")
    review_path = ROOT / "data" / "woordnummers-review" / "markus-8.json"
    review = _load(review_path)
    book = review["books"][0]
    verses = {int(verse["number"]): verse for verse in chapter["verses"]}

    assert _grondtekst_sha256(chapter) == EXPECTED_GROUND_SHA
    assert book["grondtekst_sha256"] == EXPECTED_GROUND_SHA
    assert review["uitlijngids"]["sha256"] == EXPECTED_GUIDE_SHA
    assert [record["verse"] for record in book["verses"]] == list(range(1, 39))
    assert "voorstel_" not in review_path.read_text(encoding="utf-8")

    mapping_count = 0
    link_count = 0
    for record in book["verses"]:
        verse = verses[record["verse"]]
        mappings = record["mappings"]
        mapping_count += len(mappings)
        indices = [index for mapping in mappings for index in mapping["grondindices"]]
        link_count += len(indices)

        assert sorted(indices) == list(range(len(verse["grondtekst"])))
        assert len(indices) == len(set(indices))
        assert all(mapping["bronindices"] == mapping["grondindices"] for mapping in mappings)
        assert all(mapping["reviewstatus"] == "handmatig_gecontroleerd" for mapping in mappings)
        assert all(mapping["confidence"] == 1 for mapping in mappings)
        assert all(len(mapping["grondindices"]) == 1 for mapping in mappings)
        assert all(len((mapping.get("tekst") or mapping.get("anker")).split()) <= 3 for mapping in mappings)
        assert not any(mapping.get("tekst", "").strip() == verse["text2026"].strip() for mapping in mappings)

        for mapping in mappings:
            target = mapping.get("tekst") or mapping.get("anker")
            occurrences = _whole_word_occurrences(verse["text2026"], target)
            assert occurrences, (record["verse"], target)
            occurrence = mapping.get("voorkomen")
            if occurrence is None:
                assert len(occurrences) == 1, (record["verse"], target, len(occurrences))
            else:
                assert 1 <= occurrence <= len(occurrences)

    assert mapping_count == 645
    assert link_count == 645


def test_markus_eight_remember_clause_belongs_to_visible_verse_nineteen():
    chapter = _load(ROOT / "data" / "markus" / "8.json")
    verses = {int(verse["number"]): verse for verse in chapter["verses"]}

    assert len(verses[18]["grondtekst"]) == 9
    assert verses[18]["grondtekst"][-1]["woord"] == "ακουετε"
    assert len(verses[19]["grondtekst"]) == 19
    assert [token["woord"] for token in verses[19]["grondtekst"][:3]] == [
        "και",
        "ου",
        "μνημονευετε",
    ]
    assert verses[19]["text2026"].startswith("En gedenkt u niet")
