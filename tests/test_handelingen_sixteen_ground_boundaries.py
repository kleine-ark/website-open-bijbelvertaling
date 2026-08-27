import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _chapter():
    return json.loads((ROOT / "data" / "handelingen" / "16.json").read_text(encoding="utf-8"))


def test_handelingen_zestien_behoudt_alle_grondtokens():
    chapter = _chapter()
    assert sum(len(verse.get("grondtekst", [])) for verse in chapter["verses"]) == 723


def test_handelingen_zestien_heeft_veertig_unieke_verzen():
    numbers = [verse["number"] for verse in _chapter()["verses"]]
    assert numbers == list(range(1, 41))


def test_handelingen_zestien_publiceert_vers_39_atomair():
    verse = _chapter()["verses"][38]
    assert [mapping["tekst"] for mapping in verse["woordnummers"]] == [
        "En",
        "komende",
        "baden",
        "hen",
        "en",
        "uitgeleid",
        "verzochten",
        "gaan",
        "de",
        "stad",
    ]
    assert sum(len(mapping["strongs"]) for mapping in verse["woordnummers"]) == 10
    assert [
        mapping.get("voorkomen", 1)
        for mapping in verse["woordnummers"]
        if mapping["tekst"].casefold() == "en"
    ] == [1, 2]
