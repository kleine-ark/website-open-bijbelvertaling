"""Regressietest voor de korte waarschuwing boven apocriefe boeken."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXPECTED = "<strong>⚠ Apocrief boek - geen onderdeel van de canon van Gods Woord</strong>"


def test_beide_lezers_tonen_alleen_de_korte_apocriefwaarschuwing():
    for relative_path in ("js/app.js", "js/lees.js"):
        source = (ROOT / relative_path).read_text(encoding="utf-8")
        assert EXPECTED in source
        assert "Dit boek behoort tot de apocriefe" not in source
        assert "niet als gezaghebbend Woord van God" not in source
