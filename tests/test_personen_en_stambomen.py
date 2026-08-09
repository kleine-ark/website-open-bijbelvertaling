"""Regressietests voor het corpusbrede personen- en stambomenregister."""

import json
from pathlib import Path

import pytest

from scripts.build_personen_en_stambomen import build_register, validate_register


ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def result():
    return build_register(ROOT, write=False)


def test_alle_88_boeken_worden_vers_voor_vers_geinventariseerd(result):
    coverage = result["coverage"]

    assert coverage["boekenTotaal"] == 88
    assert coverage["verzenTotaal"] == 41132
    assert len(coverage["perBoek"]) == 88
    assert all(book["status"] == "agent-reviewed" for book in coverage["perBoek"])
    assert {book["id"] for book in coverage["perBoek"] if book["testament"] == "ET"} == {
        "henoch",
        "jubileeen",
        "1meqabyan",
        "2meqabyan",
        "3meqabyan",
        "4baruch",
    }


def test_bestaande_personen_en_homoniemen_behouden_hun_stabiele_id(result):
    entities = {item["id"]: item for item in result["register"]["personen"]}

    assert {"adam", "jezus", "lazarus", "lazarus-gelijkenis"} <= entities.keys()
    assert entities["lazarus"]["id"] != entities["lazarus-gelijkenis"]["id"]
    assert entities["lazarus"]["soort"] == "mens"
    assert entities["lazarus-gelijkenis"]["soort"] == "gelijkenis"
    assert entities["adam"]["reviewStatus"] != "human-reviewed"


def test_familierelaties_hebben_bron_en_zekerheid(result):
    relationships = result["register"]["relaties"]

    assert relationships
    assert all(rel["refs"] for rel in relationships)
    assert all(rel["zekerheid"] in {"expliciet", "waarschijnlijk", "onzeker"} for rel in relationships)
    assert all(rel["reviewStatus"] == "agent-reviewed" for rel in relationships)


def test_twijfelgevallen_staan_per_boek_in_reviewqueues(result):
    queues = result["reviewQueues"]

    assert len(queues) == 88
    assert all(queue["boek"] and "gevallen" in queue for queue in queues.values())
    assert any(
        case["reden"] in {"homoniem", "mogelijke-kernferentie", "categorie-onzeker"}
        for queue in queues.values()
        for case in queue["gevallen"]
    )
    assert all(
        case["reviewStatus"] == "agent-reviewed"
        for queue in queues.values()
        for case in queue["gevallen"]
    )


def test_schema_ids_relaties_en_refs_valideren(result):
    assert validate_register(result["register"], ROOT) == []


def test_gepubliceerde_data_is_gelijk_aan_deterministische_build(result):
    published = json.loads(
        (ROOT / "data" / "personen-register.json").read_text(encoding="utf-8")
    )

    assert published == result["register"]


def test_wiki_gebruikt_een_rubriek_personen_en_stambomen():
    wiki = (ROOT / "wiki.html").read_text(encoding="utf-8")
    overview = (ROOT / "wiki-overzicht.html").read_text(encoding="utf-8")
    people = (ROOT / "personen.html").read_text(encoding="utf-8")

    assert "Personen en stambomen" in wiki
    assert "Personen en stambomen" in overview
    assert 'data-naslag="data/personen-register.json"' in people
    assert "stamboom.html" in people
