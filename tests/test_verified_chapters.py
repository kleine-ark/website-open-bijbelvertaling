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
    assert verified["numeri"] == "all"
    assert verified["deuteronomium"] == [1, 2, 3, 4, 5]
    assert 6 not in verified["deuteronomium"]

    assert set(verified) == {
        "genesis",
        "exodus",
        "leviticus",
        "ruth",
        "prediker",
        "numeri",
        "deuteronomium",
    }

    niet_menselijk_bevestigd = {
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
