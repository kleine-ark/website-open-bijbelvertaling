"""Regressietests voor het corpusbrede onderwerp Engelen."""

import json
from pathlib import Path

import pytest

from scripts.build_onderwerp_engelen import build_engelen


ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def built():
    return build_engelen(ROOT, write=False)


def test_engelenbouw_is_deterministisch_en_scant_alle_boeken():
    first = build_engelen(ROOT, write=False)
    second = build_engelen(ROOT, write=False)

    assert first == second
    assert first["report"]["boekenGescand"] == 88
    assert first["report"]["verzenGescand"] == 41132
    assert len(first["report"]["perBoek"]) == 88


def test_tag_bevat_hoofdtypen_en_exacte_verwijzingen(built):
    tag = built["tag"]
    by_ref = {item["ref"]: item for item in tag["verzen"]}

    expected = {
        "genesis 16:7": "engel-van-jahweh",
        "exodus 25:18": "cherubim",
        "jesaja 6:2": "serafim",
        "daniel 8:16": "genoemde-engel",
        "tobit 12:15": "genoemde-engel",
        "efeziers 6:12": "geestelijke-machten",
        "judas 1:6": "gevallen-demonisch",
        "henoch 12:4": "wachters",
        "openbaring 12:7": "genoemde-engel",
    }
    assert expected.items() <= {
        ref: item["subcategorie"] for ref, item in by_ref.items()
    }.items()
    assert all(item["ref"].count(":") == 1 for item in tag["verzen"])
    assert len(by_ref) == len(tag["verzen"])


def test_menselijke_boden_worden_niet_blind_gepubliceerd(built):
    refs = {item["ref"] for item in built["tag"]["verzen"]}
    review_refs = {item.get("ref") for item in built["reviewqueue"]}

    assert "maleachi 2:7" not in refs  # priester als bode
    assert "markus 1:2" not in refs  # Johannes de Doper
    assert "mattheus 11:10" not in refs
    assert {"maleachi 2:7", "markus 1:2", "mattheus 11:10"} <= review_refs


def test_theofanie_en_onzekere_hemelwezens_staan_in_reviewqueue(built):
    queue = built["reviewqueue"]

    assert any(item.get("ref") == "genesis 16:7" and item["type"] == "theofanie-vraagstuk" for item in queue)
    assert any(item.get("ref") == "richteren 6:11" and item["type"] == "theofanie-vraagstuk" for item in queue)
    assert any(item.get("ref") == "jozua 5:14" and item["type"] == "onzeker-hemelwezen" for item in queue)
    assert any(item.get("ref") == "openbaring 1:20" and item["type"] == "mogelijke-menselijke-bode" for item in queue)
    assert all(item["humanReviewed"] is False for item in queue)


def test_alle_publicaties_hebben_classificatie_en_ai_reviewstatus(built):
    tag = built["tag"]

    assert tag["reviewStatus"] == "agent-reviewed"
    assert tag["humanReviewed"] is False
    assert tag["aliassen"]
    assert all(item["weergave"] in {
        "verschijning-handeling", "onderwijs", "visioen-symboliek", "twijfelgeval"
    } for item in tag["verzen"])
    assert all(item["zekerheid"] in {"zeker", "waarschijnlijk", "onzeker"} for item in tag["verzen"])
    assert all(item["reviewStatus"] == "agent-reviewed" for item in tag["verzen"])
    assert all(item["humanReviewed"] is False for item in tag["verzen"])


def test_alle_refs_bestaan_in_het_88_boekencorpus(built):
    from scripts.build_corpus_naslag import load_corpus

    valid = {verse.ref for verse in load_corpus(ROOT, include_ethiopic=True)}
    assert {item["ref"] for item in built["tag"]["verzen"]} <= valid
    assert {item["ref"] for item in built["reviewqueue"] if item.get("ref")} <= valid


def test_schrijvende_build_integreert_met_bestaande_tags(built):
    tags = json.loads((ROOT / "data" / "tags.json").read_text(encoding="utf-8"))["tags"]

    merged = [tag for tag in tags if tag["id"] != "engelen"] + [built["tag"]]
    assert len([tag for tag in merged if tag["id"] == "engelen"]) == 1
    assert len(merged) == len(tags) + (0 if any(tag["id"] == "engelen" for tag in tags) else 1)


def test_onderwerpenpagina_plaatst_engelen_in_een_zichtbare_rubriek():
    html = (ROOT / "onderwerpen.html").read_text(encoding="utf-8")

    assert "'engelen'" in html
    assert "'verzen'" in html
    assert "vers${" not in html
