import json
from pathlib import Path

from scripts.import_inline_woordnummers import _grondtekst_sha256


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_GROUND_SHA = "BDAE9E3CCA31BF420BA40BD2EE5329E8A08A145518864BC1D9A93583BC021CE2"
EXPECTED_COUNTS = [
    10, 9, 11, 17, 17, 8, 21, 21, 23, 18, 14, 15, 30, 10, 11, 21,
    18, 18, 14, 23, 22, 4, 18, 21, 25, 22, 35, 20, 13, 10, 5, 23,
]


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_romeinen_one_ground_layer_has_the_verified_tr_boundaries():
    chapter = _load(ROOT / "data" / "romeinen" / "1.json")
    assert _grondtekst_sha256(chapter) == EXPECTED_GROUND_SHA
    assert [verse["number"] for verse in chapter["verses"]] == list(range(1, 33))
    assert [len(verse["grondtekst"]) for verse in chapter["verses"]] == EXPECTED_COUNTS
    assert sum(EXPECTED_COUNTS) == 547


def test_romeinen_one_restored_ground_boundaries_are_explicit():
    chapter = _load(ROOT / "data" / "romeinen" / "1.json")
    verses = {verse["number"]: verse for verse in chapter["verses"]}

    assert [token["strongs"] for token in verses[4]["grondtekst"][-5:]] == [
        "G2424",
        "G5547",
        "G3588",
        "G2962",
        "G1473",
    ]
    assert [token["strongs"] for token in verses[10]["grondtekst"][:5]] == [
        "G3842",
        "G1909",
        "G3588",
        "G4335",
        "G1473",
    ]
    assert verses[29]["grondtekst"][-1]["strongs"] == "G2550"
    assert verses[30]["grondtekst"][0]["strongs"] == "G5588"
