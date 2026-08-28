import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_FLAT_SHA256 = "F239E5A177984D411C5082AC3CE86CE230BF2D1C889ABB57B1C7D9D36191297D"


def test_lukas_six_keeps_all_tokens_and_places_verse_18_at_its_visible_boundary():
    chapter = json.loads((ROOT / "data" / "lukas" / "6.json").read_text(encoding="utf-8"))
    verses = {int(verse["number"]): verse for verse in chapter["verses"]}
    flat = [token for verse in chapter["verses"] for token in verse.get("grondtekst", [])]
    digest = hashlib.sha256(
        json.dumps(flat, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    ).hexdigest().upper()

    assert len(flat) == 957
    assert digest == EXPECTED_FLAT_SHA256
    assert len(verses[17]["grondtekst"]) == 29
    assert verses[17]["grondtekst"][-1]["strongs"] == "G4605"
    assert len(verses[18]["grondtekst"]) == 18
    assert verses[18]["grondtekst"][0]["strongs"] == "G3739"
    assert verses[18]["grondtekst"][-1]["strongs"] == "G2323"
