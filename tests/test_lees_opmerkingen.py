"""Regressies voor het selecteren van feedback uit de opmerkingen-sheet."""

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from lees_opmerkingen import zelfde_boek  # noqa: E402


def test_boekfilter_accepteert_spaties_en_diacritische_varianten():
    """Een intern boek-id moet dezelfde sheet-verwijzing vinden."""
    assert zelfde_boek("1 Koningen 5:2", "1koningen")
    assert zelfde_boek("1 Koningen 5:2", "1 Koningen")
    assert zelfde_boek("Mattheüs 1:1", "mattheus")
    assert not zelfde_boek("2 Koningen 5:2", "1koningen")
