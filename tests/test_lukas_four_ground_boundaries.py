import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_lukas_four_18_19_ground_boundary_matches_visible_verses():
    chapter = json.loads((ROOT / "data" / "lukas" / "4.json").read_text(encoding="utf-8"))
    verses = {int(verse["number"]): verse for verse in chapter["verses"]}

    assert sum(len(verse.get("grondtekst", [])) for verse in chapter["verses"]) == 799
    assert len(verses[18]["grondtekst"]) == 17
    assert verses[18]["grondtekst"][-1]["woord"] == "καρδιαν"
    assert verses[18]["grondtekst"][-1]["strongs"] == "G2588"

    assert len(verses[19]["grondtekst"]) == 14
    assert verses[19]["grondtekst"][0]["woord"] == "κηρυξαι"
    assert verses[19]["grondtekst"][0]["strongs"] == "G2784"
    assert verses[19]["grondtekst"][-1]["woord"] == "δεκτον"
    assert verses[19]["grondtekst"][-1]["strongs"] == "G1184"
