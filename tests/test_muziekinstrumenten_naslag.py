"""Gerichte dekkingstests voor de corpusbrede muziekinstrumentenindex."""

import json
from pathlib import Path

import pytest

from scripts.build_corpus_naslag import _build_instruments, load_books, load_corpus


ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def instruments_data():
    catalog = json.loads(
        (ROOT / "data" / "naslag-catalogus.json").read_text(encoding="utf-8")
    )["categorieen"]["muziekinstrumenten"]
    return _build_instruments(
        catalog,
        load_books(ROOT),
        load_corpus(ROOT, include_ethiopic=True),
        [],
        [],
    )


def test_alle_afzonderlijke_instrumentnamen_worden_gepubliceerd(instruments_data):
    ids = {item["id"] for item in instruments_data["items"]}

    assert {
        "harp", "fluit", "trompet", "cimbalen", "bazuin", "luit", "citer",
        "trommel", "ramshoorn", "orgel", "pijp", "vedel", "psalter",
        "hoorn", "schellen", "tiensnarig-instrument", "lier",
    } <= ids


def test_alle_88_boeken_worden_gescand_en_corpusdelen_blijven_onderscheiden(instruments_data):
    assert instruments_data["dekking"] == {
        "boekenGescand": 88,
        "verzenGescand": 41132,
    }
    assert instruments_data["reviewStatus"] == "agent-reviewed"
    assert instruments_data["humanReviewed"] is False
    assert all(
        item["zekerheid"] in {"zeker", "waarschijnlijk", "onzeker"}
        for item in instruments_data["items"]
    )
    assert all(
        item["verzen"]
        == item["canoniekeVerzen"]
        + item["apocriefeVerzen"]
        + item["ethiopischeVerzen"]
        for item in instruments_data["items"]
    )


def test_naamvarianten_worden_gevonden_zonder_werkwoordelijke_homoniemen(instruments_data):
    items = {item["id"]: item for item in instruments_data["items"]}

    assert {"openbaring 18:22", "1meqabyan 19:1"} <= set(items["fluit"]["verzen"])
    assert {
        "1koningen 9:8", "job 27:23", "jeremia 19:8", "klaagliederen 2:15",
        "1meqabyan 35:5",
    }.isdisjoint(items["fluit"]["verzen"])
    assert {"openbaring 5:8", "openbaring 18:22"} <= set(items["citer"]["verzen"])
    assert "3ezra 5:59" in items["cimbalen"]["verzen"]
    assert {"psalmen 68:26", "1meqabyan 19:1"} <= set(items["trommel"]["verzen"])
    assert {"job 17:6", "nahum 2:7"}.isdisjoint(items["trommel"]["verzen"])
    assert {"mattheus 9:23", "daniel 3:5"} <= set(items["pijp"]["verzen"])
    assert {"zacharia 4:2", "job 31:22"}.isdisjoint(items["pijp"]["verzen"])
