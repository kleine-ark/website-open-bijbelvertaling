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
    assert verified["deuteronomium"] == "all"
    assert verified["jozua"] == "all"
    assert verified["richteren"] == "all"

    nieuw_testament = {
        "mattheus", "markus", "lukas", "johannes", "handelingen", "romeinen",
        "1korinthiers", "2korinthiers", "galaten", "efeziers", "filippenzen",
        "kolossenzen", "1tessalonicensen", "2tessalonicensen", "1timotheus",
        "2timotheus", "titus", "filemon", "hebreeen", "jakobus", "1petrus",
        "2petrus", "1johannes", "2johannes", "3johannes", "judas", "openbaring",
    }
    assert all(verified.get(boek) == "all" for boek in nieuw_testament)

    eerder_menselijk_nagekeken_ot = {
        "psalmen", "ezra", "prediker", "hosea", "joel", "amos", "obadja",
        "jona", "micha", "nahum", "habakuk", "zefanja", "haggai",
        "zacharia", "maleachi",
    }
    nagekeken_apocrieven = {
        "1makkabeeen", "baruch", "gebedvanmanasse", "susanna",
    }
    assert all(verified.get(boek) == "all" for boek in eerder_menselijk_nagekeken_ot)
    assert all(verified.get(boek) == "all" for boek in nagekeken_apocrieven)

    assert set(verified) == {
        "genesis",
        "exodus",
        "leviticus",
        "ruth",
        "prediker",
        "numeri",
        "deuteronomium",
        "jozua",
        "richteren",
        "1samuel",
        "1koningen",
        "2koningen",
        "esther",
        "nehemia",
        "1kronieken",
        "2kronieken",
    } | nieuw_testament | eerder_menselijk_nagekeken_ot | nagekeken_apocrieven

    niet_menselijk_bevestigd = {
        "jeremia",
        "2samuel",
        "job",
        "spreuken",
        "hooglied",
        "jesaja",
        "klaagliederen",
        "ezechiel",
        "daniel",
    }
    assert niet_menselijk_bevestigd.isdisjoint(verified)
