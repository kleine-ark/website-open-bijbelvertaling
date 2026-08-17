import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def vers(c, v):
    data = json.loads((ROOT / "data" / "esther" / f"{c}.json").read_text(encoding="utf-8"))
    return next(x for x in data["verses"] if x["number"] == v)

def test_tekstcorrecties_en_principes():
    matrix = [
        (1, 6, "bekleding", "behangselen"), (2, 3, "opzichters", "toezieners"),
        (2, 7, "die Hadassa opvoedde", "die opvoedde Hadassa"),
        (2, 12, "naderde", "naakte"), (2, 15, "naderde", "naakte"),
        (3, 5, "knielde", "neigde"), (4, 8, "geschreven wet", "geschrevene wet"),
        (9, 27, "zou overtreden", "overtrade"), (10, 3, "nageslacht", "zaad"),
    ]
    for c, v, nieuw, oud in matrix:
        item = vers(c, v)
        assert nieuw in item["text2026"]
        assert not re.search(rf"(?<!\w){re.escape(oud)}(?!\w)", item["text2026"])
        assert any((x.get("principe") or "").startswith("MR-EST-") for x in item.get("phraseDiff", []))

def test_citaten_begrenzen_spraak_en_vertelling():
    assert 'direct-speech' not in vers(1, 10)["text2026_html"]
    assert 'direct-speech' not in vers(2, 10)["text2026_html"]
    assert 'direct-speech' not in vers(4, 8)["text2026_html"]
    assert 'direct-speech' not in vers(6, 12)["text2026_html"]
    assert '</i></span> Deze zaak' in vers(2, 4)["text2026_html"]
    assert '</i></span> Als nu' in vers(5, 5)["text2026_html"]
    assert '</i></span> Toen verschrikte' in vers(7, 6)["text2026_html"]
    assert '</i></span> Het woord ging' in vers(7, 8)["text2026_html"]

def test_esther_is_pas_na_verwerking_afgerond():
    verified = json.loads((ROOT / "data" / "verified-chapters.json").read_text(encoding="utf-8"))
    assert verified.get("esther") == "all"
