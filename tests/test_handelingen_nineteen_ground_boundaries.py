import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _chapter():
    return json.loads((ROOT / "data" / "handelingen" / "19.json").read_text(encoding="utf-8"))


def test_handelingen_negentien_behoudt_alle_grondtokens():
    chapter = _chapter()
    assert sum(len(verse.get("grondtekst", [])) for verse in chapter["verses"]) == 767


def test_handelingen_negentien_heeft_eenenveertig_unieke_verzen():
    numbers = [verse["number"] for verse in _chapter()["verses"]]
    assert numbers == list(range(1, 42))


def test_handelingen_negentien_publiceert_slotvers_atomair():
    verse = _chapter()["verses"][40]
    assert [mapping["tekst"] for mapping in verse["woordnummers"]] == [
        "En",
        "dit",
        "gezegd hebbende",
        "liet",
        "de",
        "vergadering",
    ]
    assert sum(len(mapping["strongs"]) for mapping in verse["woordnummers"]) == 6


def test_handelingen_negentien_heeft_geen_hele_versankers():
    for verse in _chapter()["verses"]:
        for mapping in verse["woordnummers"]:
            assert mapping["tekst"] != verse["text2026"]
            assert len(mapping["tekst"].split()) <= 4
