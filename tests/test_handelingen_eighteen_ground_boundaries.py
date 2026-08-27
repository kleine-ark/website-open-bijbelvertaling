import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _chapter():
    return json.loads((ROOT / "data" / "handelingen" / "18.json").read_text(encoding="utf-8"))


def test_handelingen_achttien_behoudt_alle_grondtokens():
    chapter = _chapter()
    assert sum(len(verse.get("grondtekst", [])) for verse in chapter["verses"]) == 528


def test_handelingen_achttien_heeft_achtentwintig_unieke_verzen():
    numbers = [verse["number"] for verse in _chapter()["verses"]]
    assert numbers == list(range(1, 29))


def test_handelingen_achttien_publiceert_slotvers_atomair():
    verse = _chapter()["verses"][27]
    assert [mapping["tekst"] for mapping in verse["woordnummers"]] == [
        "grote ernst",
        "Want",
        "de",
        "Joden",
        "overtuigde",
        "openbaar",
        "bewijzende",
        "door",
        "de",
        "Schriften",
        "was",
        "de",
        "Christus",
        "Jezus",
    ]
    assert sum(len(mapping["strongs"]) for mapping in verse["woordnummers"]) == 14


def test_handelingen_achttien_heeft_geen_hele_versankers():
    for verse in _chapter()["verses"]:
        for mapping in verse["woordnummers"]:
            assert mapping["tekst"] != verse["text2026"]
            assert len(mapping["tekst"].split()) <= 4
