import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _chapter():
    return json.loads((ROOT / "data" / "handelingen" / "15.json").read_text(encoding="utf-8"))


def test_handelingen_vijftien_behoudt_alle_grondtokens():
    chapter = _chapter()
    assert sum(len(verse.get("grondtekst", [])) for verse in chapter["verses"]) == 716


def test_handelingen_vijftien_heeft_eenenveertig_unieke_verzen():
    numbers = [verse["number"] for verse in _chapter()["verses"]]
    assert numbers == list(range(1, 42))


def test_handelingen_vijftien_publiceert_vers_34_atomair():
    verse = _chapter()["verses"][33]
    assert [mapping["tekst"] for mapping in verse["woordnummers"]] == [
        "dacht",
        "Maar",
        "",
        "Silas",
        "blijven",
        "daar",
    ]
    assert sum(len(mapping["strongs"]) for mapping in verse["woordnummers"]) == 6
