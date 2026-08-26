import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_titus_1_address_belongs_to_local_verse_3():
    chapter = json.loads((ROOT / "data" / "titus" / "1.json").read_text(encoding="utf-8"))
    verses = {verse["number"]: verse for verse in chapter["verses"]}

    assert [token["strongs"] for token in verses[3]["grondtekst"][-6:]] == [
        "G5103",
        "G1103",
        "G5043",
        "G2596",
        "G2839",
        "G4102",
    ]
    assert verses[4]["grondtekst"][0]["strongs"] == "G5485"


def test_titus_1_revelation_clause_belongs_to_local_verse_2():
    chapter = json.loads((ROOT / "data" / "titus" / "1.json").read_text(encoding="utf-8"))
    verses = {verse["number"]: verse for verse in chapter["verses"]}

    assert [token["strongs"] for token in verses[2]["grondtekst"][-4:]] == [
        "G5319",
        "G1161",
        "G2540",
        "G2398",
    ]
    assert verses[3]["grondtekst"][0]["strongs"] == "G3588"


def test_titus_1_boundary_repair_is_lossless():
    chapter = json.loads((ROOT / "data" / "titus" / "1.json").read_text(encoding="utf-8"))
    verses = {verse["number"]: verse for verse in chapter["verses"]}

    assert len(verses[2]["grondtekst"]) == 16
    assert len(verses[3]["grondtekst"]) == 20
    assert len(verses[4]["grondtekst"]) == 13
