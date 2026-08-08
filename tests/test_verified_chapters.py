"""Regressietests voor de menselijke reviewstatus van Bijbelboeken."""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_alleen_menselijk_bevestigde_boeken_krijgen_reviewstatus():
    verified = json.loads(
        (ROOT / "data" / "verified-chapters.json").read_text(encoding="utf-8")
    )

    assert verified["genesis"] == "all"
    assert verified["exodus"] == "all"
    assert verified["leviticus"] == "all"
    assert verified["prediker"] == "all"
    assert verified["ruth"] == "all"
    assert verified["numeri"] == list(range(1, 21))

    niet_menselijk_bevestigd = {
        "deuteronomium",
        "jozua",
        "jeremia",
        "richteren",
        "1samuel",
        "2samuel",
        "1koningen",
        "2koningen",
        "1kronieken",
        "2kronieken",
        "nehemia",
        "esther",
        "job",
        "spreuken",
        "hooglied",
        "jesaja",
        "klaagliederen",
        "ezechiel",
        "daniel",
        "zacharia",
    }
    assert niet_menselijk_bevestigd.isdisjoint(verified)
