"""Regressietests voor het onderwerp Doop door onderdompeling."""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _tag():
    data = json.loads((ROOT / "data" / "tags.json").read_text(encoding="utf-8"))
    return next(tag for tag in data["tags"] if tag["id"] == "doop-door-onderdompeling")


def test_doop_door_onderdompeling_bevat_de_kernteksten_en_top_tien():
    """De pagina moet de expliciete doopteksten en een redactionele Top 10 tonen."""
    tag = _tag()
    refs = {item["ref"] for item in tag["verzen"]}

    assert {
        "mattheus 3:16",
        "johannes 3:23",
        "handelingen 8:38",
        "romeinen 6:4",
        "kolossenzen 2:12",
        "1petrus 3:21",
    } <= refs
    assert tag["topTien"] == [
        "mattheus 3:16",
        "markus 1:9",
        "johannes 3:23",
        "mattheus 28:19",
        "handelingen 2:38",
        "handelingen 8:38",
        "handelingen 10:47",
        "handelingen 16:33",
        "romeinen 6:3",
        "kolossenzen 2:12",
    ]


def test_doop_door_onderdompeling_blijft_redactioneel_te_controleren():
    """De PDF is bron voor selectie, maar de leerstellige duiding blijft controleerbaar."""
    tag = _tag()

    assert tag["selectiemethode"] == "bronlijst-waterdoop-pdf-en-aanvullende-doopteksten"
    assert tag["reviewStatus"] == "agent-reviewed"
    assert tag["humanReviewed"] is False
    assert {item["zekerheid"] for item in tag["verzen"]} <= {"zeker", "verwant"}
    assert any(item["zekerheid"] == "verwant" for item in tag["verzen"])
