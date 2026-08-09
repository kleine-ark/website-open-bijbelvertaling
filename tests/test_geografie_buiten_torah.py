"""Validatie van de afgeschermde geografische stagingdata buiten de Torah."""

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STAGING = ROOT / "data" / "geografie-staging" / "buiten-torah"
TORAH = {"genesis", "exodus", "leviticus", "numeri", "deuteronomium"}
CONFIDENCE = {"zeker", "waarschijnlijk", "onzeker"}
STATUSES = {"agent-reviewed", "needs-human-review"}


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def verse_text(book, key):
    chapter, number = map(int, key.split(":"))
    data = load(ROOT / "data" / book / f"{chapter}.json")
    return next(verse["text2026"] for verse in data["verses"] if verse["number"] == number)


def test_manifest_bestrijkt_alle_83_boeken_buiten_torah():
    manifest = load(STAGING / "manifest.json")
    assert manifest["status"] == "agent-reviewed"
    assert manifest["humanReviewed"] is False
    assert manifest["publicatieStatus"] == "staging-niet-samenvoegen-zonder-afstemming"
    assert len(manifest["boeken"]) == 83
    assert not TORAH.intersection(manifest["boeken"])


def test_entiteiten_hebben_unieke_ids_punten_bronnen_en_zekerheid():
    entities = load(STAGING / "entities.json")["entities"]
    ids = [entity["id"] for entity in entities]
    assert len(ids) == len(set(ids))
    for entity in entities:
        assert re.fullmatch(r"geo-[a-z0-9-]+", entity["id"])
        assert entity["zekerheid"] in CONFIDENCE
        assert -90 <= entity["punt"]["lat"] <= 90
        assert -180 <= entity["punt"]["lon"] <= 180
        assert entity["coordinatenBron"]["url"].startswith("https://")
        assert entity["status"] in STATUSES
        assert entity["humanReviewed"] is False


def test_alle_vermeldingen_verwijzen_naar_entiteit_en_bestaand_vers():
    entity_ids = {e["id"] for e in load(STAGING / "entities.json")["entities"]}
    for path in (STAGING / "boeken").glob("*.json"):
        data = load(path)
        assert data["boek"] == path.stem
        assert data["humanReviewed"] is False
        for key, mentions in data["mentions"].items():
            text = verse_text(path.stem, key)
            for mention in mentions:
                assert mention["entityId"] in entity_ids
                assert mention["status"] in STATUSES
                assert mention["href"] == f"index.html#{path.stem}/{key.replace(':', '/')}"
                if mention["status"] == "agent-reviewed":
                    assert mention["label"]
                    assert mention["label"].casefold() in text.casefold()


def test_synoniemvormen_hebben_eigen_vindplaatsen():
    entities = load(STAGING / "entities.json")["entities"]
    for entity in entities:
        forms = [item["vorm"].casefold() for item in entity["synoniemenInTekst"]]
        assert len(forms) == len(set(forms))
        for alias in entity["synoniemenInTekst"]:
            assert alias["vindplaatsen"]


def test_reviewqueue_claimt_nooit_menselijke_controle():
    for path in (STAGING / "boeken").glob("*.json"):
        queue = load(path)["reviewQueue"]
        assert all(item["status"] == "needs-human-review" for item in queue)


def test_aliasbotsingen_zijn_expliciet_als_reviewwerk_geregistreerd():
    entities = load(STAGING / "entities.json")["entities"]
    owners = {}
    for entity in entities:
        for alias in entity["synoniemenInTekst"]:
            owners.setdefault(alias["vorm"].casefold(), set()).add(entity["id"])
    expected = {form: ids for form, ids in owners.items() if len(ids) > 1}
    collisions = load(STAGING / "alias-botsingen.json")["botsingen"]
    actual = {item["vorm"]: set(item["entityIds"]) for item in collisions}
    assert actual == expected
    assert all(item["status"] == "needs-human-review" for item in collisions)
