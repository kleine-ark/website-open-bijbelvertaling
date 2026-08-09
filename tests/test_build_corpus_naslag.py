"""Regressietests voor de corpusbrede wiki-naslaggenerator."""

import json
from pathlib import Path

import pytest

from scripts.build_corpus_naslag import build_all, find_refs, load_corpus


ROOT = Path(__file__).resolve().parents[1]


def read_json(relative):
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def built_naslag():
    return build_all(ROOT, write=False)


def test_corpus_bevat_alleen_echte_verzen():
    corpus = load_corpus(ROOT)

    assert len(corpus) == read_json("data/stats.json")["verses_total"]
    assert all(item.text and item.chapter > 0 and item.verse > 0 for item in corpus)
    assert {item.testament for item in corpus} == {"OT", "NT", "AP"}


def test_bouwen_zonder_schrijven_is_deterministisch():
    assert build_all(ROOT, write=False) == build_all(ROOT, write=False)


def test_zoekvormen_raken_hele_woorden_en_behouden_canonieke_volgorde():
    item = {
        "zoekvormen": ["ram", "rammen"],
        "expliciet": [],
        "uitsluiten": [],
    }

    refs = find_refs(load_corpus(ROOT), item)

    assert "genesis 15:9" in refs
    assert len(refs) == len(set(refs))


def test_explicit_refs_worden_toegevoegd_en_uitsluitingen_verwijderd():
    item = {
        "zoekvormen": ["boom van het leven"],
        "expliciet": ["openbaring 22:2"],
        "uitsluiten": ["genesis 2:9"],
    }

    refs = find_refs(load_corpus(ROOT), item)

    assert "openbaring 22:2" in refs
    assert "genesis 2:9" not in refs


@pytest.mark.parametrize(
    ("category", "minimum"),
    (("materialen", 35), ("dieren", 55), ("bomen-planten", 45)),
)
def test_natuurlijke_naslag_is_corpusbreed(category, minimum, built_naslag):
    data = built_naslag[category]

    assert len(data["items"]) >= minimum
    refs = [ref for item in data["items"] for ref in item["verzen"]]
    assert any(ref.startswith("genesis ") for ref in refs)
    assert any(
        ref.startswith("mattheus ") or ref.startswith("markus ") for ref in refs
    )
    assert any(
        ref.startswith("boekderwijsheid ") or ref.startswith("jezussirach ")
        for ref in refs
    )
    assert "Voorlopig alleen Genesis" not in data["intro"]


def test_alle_gegenereerde_verwijzingen_zijn_volledig(built_naslag):
    for category in ("materialen", "dieren", "bomen-planten"):
        for item in built_naslag[category]["items"]:
            assert all(" " in ref and ":" in ref for ref in item["verzen"])


def test_personen_behouden_identiteit_en_beslaan_het_hele_corpus(built_naslag):
    people = built_naslag["personen"]["items"]

    assert len(people) >= 385
    assert len([person for person in people if person["naam"] == "Azaria"]) >= 2
    assert all(
        person.get("onderscheiding")
        for person in people
        if person["naam"] == "Azaria"
    )
    assert len({person["id"] for person in people}) == len(people)
    refs = [ref for person in people for ref in person["verzen"]]
    assert any(ref.startswith("genesis ") for ref in refs)
    assert any(ref.startswith("johannes ") for ref in refs)
    assert any(ref.startswith("tobit ") or ref.startswith("judith ") for ref in refs)

    jesus = next(person for person in people if person["id"] == "jezus")
    assert jesus["beschrijving"] == "De Zoon, God geopenbaard in het vlees."

    lazarus = next(person for person in people if person["id"] == "lazarus")
    parable_lazarus = next(
        person for person in people if person["id"] == "lazarus-gelijkenis"
    )
    assert all(ref.startswith("johannes ") for ref in lazarus["verzen"])
    assert all(ref.startswith("lukas 16:") for ref in parable_lazarus["verzen"])

    eunuch = next(
        person for person in people if person["id"] == "ethiopische-kamerling"
    )
    assert all(ref.startswith("handelingen 8:") for ref in eunuch["verzen"])


def test_muziekinstrumenten_vormen_een_eigen_corpusbrede_naslag(built_naslag):
    instruments = built_naslag["muziekinstrumenten"]["items"]

    assert len(instruments) >= 12
    names = {item["naam"] for item in instruments}
    assert {"Harp", "Fluit", "Trompet", "Cimbalen"} <= names
    refs = [ref for item in instruments for ref in item["verzen"]]
    assert any(ref.startswith("genesis ") for ref in refs)
    assert any(
        ref.startswith("1korinthiers ") or ref.startswith("openbaring ")
        for ref in refs
    )
    assert any(ref.startswith("jezussirach ") or ref.startswith("1makkabeeen ") for ref in refs)


@pytest.mark.parametrize("category", ("dieren", "bomen-planten"))
def test_natuurnaslag_scannt_alle_88_boeken_met_reviewmetadata(category, built_naslag):
    data = built_naslag[category]

    assert data["dekking"]["boekenGescand"] == 88
    assert len(data["dekking"]["perBoek"]) == 88
    assert data["reviewStatus"] == "agent-reviewed"
    assert data["humanReviewed"] is False
    assert all(book["gescand"] for book in data["dekking"]["perBoek"])


@pytest.mark.parametrize("category", ("dieren", "bomen-planten"))
def test_natuurvermeldingen_hebben_context_alias_en_geldige_verwijzing(category, built_naslag):
    data = built_naslag[category]
    geldige_refs = {verse.ref for verse in load_corpus(ROOT, include_ethiopic=True)}
    vermeldingen = [mention for item in data["items"] for mention in item["vermeldingen"]]

    assert vermeldingen
    assert all(mention["ref"] in geldige_refs for mention in vermeldingen)
    assert all(mention["tekstvorm"] for mention in vermeldingen)
    assert {mention["gebruik"] for mention in vermeldingen} <= {
        "letterlijk", "beeldend-symbolisch", "vergelijkend"
    }
    assert all(mention["reviewStatus"] != "human-reviewed" for mention in vermeldingen)
    assert all(item["zekerheid"] in {"zeker", "waarschijnlijk", "onzeker"} for item in data["items"])


def test_natuurrapport_bevat_tellingen_en_aparte_reviewqueue(tmp_path):
    build_all(ROOT, write=True)
    report = read_json("data/naslag-natuur-controle.json")

    assert report["boekenGescand"] == 88
    assert len(report["perBoek"]) == 88
    assert set(report["totalen"]) == {"dieren", "bomen-planten"}
    assert isinstance(report["reviewqueue"], list)


def test_ontbrekende_concrete_soorten_en_gewassen_krijgen_een_stabiel_item(built_naslag):
    animal_ids = {item["id"] for item in built_naslag["dieren"]["items"]}
    plant_ids = {item["id"] for item in built_naslag["bomen-planten"]["items"]}

    assert {"havik", "sperwer", "hyena", "basilisk", "buffel", "steenbok"} <= animal_ids
    assert {"papyrus", "terebint", "graan-en-koren", "wikke"} <= plant_ids


def test_persoonsnaam_ram_wordt_niet_als_dier_gepubliceerd(built_naslag):
    ram = next(item for item in built_naslag["dieren"]["items"] if item["id"] == "rammen")

    assert "1kronieken 2:9" not in ram["verzen"]
