import json
from pathlib import Path

from scripts.import_inline_woordnummers import _grondtekst_sha256


ROOT = Path(__file__).resolve().parents[1]
GROUND_SHA = "6B93FB4EF71FD59B8DB9B33DAC6D015BE2B83E3293D9BB6E4C26631D81B11245"
EXPECTED_COUNTS = [
    17, 20, 29, 26, 24, 20, 30, 18, 16, 11, 14, 13, 30,
    15, 16, 12, 12, 26, 13, 18, 15, 10, 27, 12, 9, 15,
]


def _load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_romeinen_7_ground_layer_has_the_verified_split_final_verse():
    chapter = _load(ROOT / "data" / "romeinen" / "7.json")
    verses = {verse["number"]: verse for verse in chapter["verses"]}

    assert _grondtekst_sha256(chapter) == GROUND_SHA
    assert [verse["number"] for verse in chapter["verses"]] == list(range(1, 27))
    assert [len(verse["grondtekst"]) for verse in chapter["verses"]] == EXPECTED_COUNTS
    assert sum(EXPECTED_COUNTS) == 468

    assert [token["strongs"] for token in verses[25]["grondtekst"]] == [
        "G2168", "G3588", "G2316", "G1223", "G2424", "G5547",
        "G3588", "G2962", "G1473",
    ]
    assert [token["strongs"] for token in verses[26]["grondtekst"]] == [
        "G686", "G3767", "G846", "G1473", "G3588", "G3303",
        "G3563", "G1398", "G3551", "G2316", "G3588", "G1161",
        "G4561", "G3551", "G266",
    ]


def test_romeinen_7_review_records_the_shared_source_verse_explicitly():
    review = _load(ROOT / "data" / "woordnummers-review" / "romeinen-7.json")
    records = {record["verse"]: record for record in review["books"][0]["verses"]}

    assert records[24]["source_verse"] == 24
    assert records[25]["source_verse"] == 25
    assert records[26]["source_verse"] == 25
    assert records[25]["morphhb_verse"] == 25
    assert records[26]["morphhb_verse"] == 25

    source_indices = [
        index
        for number in (25, 26)
        for mapping in records[number]["mappings"]
        for index in mapping["bronindices"]
    ]
    assert sorted(source_indices) == list(range(25))
    assert len(source_indices) == len(set(source_indices))
