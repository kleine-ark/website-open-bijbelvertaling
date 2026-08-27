import json
from pathlib import Path

from scripts.import_inline_woordnummers import _grondtekst_sha256


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_GROUND_SHA = "0B29CBBE37E0DD303F034ED508DC2BEEF99639B6F04CE5D901003F9AEAA81099"


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_markus_one_review_is_atomic_complete_and_pinned():
    chapter = _load(ROOT / "data" / "markus" / "1.json")
    review = _load(ROOT / "data" / "woordnummers-review" / "markus-1.json")
    book = review["books"][0]
    verses = {int(verse["number"]): verse for verse in chapter["verses"]}

    assert _grondtekst_sha256(chapter) == EXPECTED_GROUND_SHA
    assert book["grondtekst_sha256"] == EXPECTED_GROUND_SHA
    assert [record["verse"] for record in book["verses"]] == list(range(1, 46))

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
        assert all(len(mapping["grondindices"]) <= 2 for mapping in mappings)
        assert not any(mapping.get("tekst", "").strip() == verse["text2026"].strip() for mapping in mappings)

    assert mapping_count == 718
    assert link_count == 723
