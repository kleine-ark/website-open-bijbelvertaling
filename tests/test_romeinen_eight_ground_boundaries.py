import json
from pathlib import Path

from scripts.import_inline_woordnummers import _grondtekst_sha256


ROOT = Path(__file__).resolve().parents[1]
GROUND_SHA = "6153B4BCFAC467EEF952B8DBDA33D7B336C33EE360C33095EC8541BAD4A6E82D"
EXPECTED_COUNTS = [
    15, 20, 30, 16, 16, 14, 18, 9, 26, 17,
    31, 12, 16, 9, 18, 11, 16, 17, 12, 12,
    22, 12, 24, 17, 9, 26, 17, 16, 19, 18,
    13, 22, 8, 22, 21, 13, 9, 17, 23,
]


def _load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_romeinen_8_ground_layer_places_op_hoop_in_local_verse_21():
    chapter = _load(ROOT / "data" / "romeinen" / "8.json")
    verses = {verse["number"]: verse for verse in chapter["verses"]}

    assert _grondtekst_sha256(chapter) == GROUND_SHA
    assert [verse["number"] for verse in chapter["verses"]] == list(range(1, 40))
    assert [len(verse["grondtekst"]) for verse in chapter["verses"]] == EXPECTED_COUNTS
    assert sum(EXPECTED_COUNTS) == 663

    assert verses[20]["grondtekst"][-1]["strongs"] == "G5293"
    assert [token["strongs"] for token in verses[21]["grondtekst"][:3]] == [
        "G1909",
        "G1680",
        "G3754",
    ]
    assert verses[21]["text2026"].startswith("Op hoop")


def test_romeinen_8_review_documents_the_shifted_source_boundary():
    review = _load(ROOT / "data" / "woordnummers-review" / "romeinen-8.json")
    records = {record["verse"]: record for record in review["books"][0]["verses"]}

    assert records[20]["source_verse"] == 20
    assert records[21]["source_verse"] == 21
    assert records[21]["mappings"][0]["bronindices"] == []
    assert records[21]["mappings"][1]["bronindices"] == []
