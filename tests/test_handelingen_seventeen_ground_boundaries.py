import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _chapter():
    return json.loads((ROOT / "data" / "handelingen" / "17.json").read_text(encoding="utf-8"))


def test_handelingen_zeventien_behoudt_alle_grondtokens():
    chapter = _chapter()
    assert sum(len(verse.get("grondtekst", [])) for verse in chapter["verses"]) == 678


def test_handelingen_zeventien_heeft_vierendertig_unieke_verzen():
    numbers = [verse["number"] for verse in _chapter()["verses"]]
    assert numbers == list(range(1, 35))


def test_handelingen_zeventien_publiceert_vers_34_atomair():
    verse = _chapter()["verses"][33]
    assert [mapping["tekst"] for mapping in verse["woordnummers"]] == [
        "sommige",
        "Maar",
        "mannen",
        "hingen",
        "hem",
        "geloofden",
        "onder",
        "wie",
        "ook",
        "Dionysius",
        "de",
        "Areopagiet",
        "en",
        "vrouw",
        "naam",
        "Damaris",
        "en",
        "anderen",
        "daarmee",
    ]
    assert sum(len(mapping["strongs"]) for mapping in verse["woordnummers"]) == 20
    assert [
        mapping.get("voorkomen", 1)
        for mapping in verse["woordnummers"]
        if mapping["tekst"].casefold() == "en"
    ] == [2, 3]


def test_handelingen_zeventien_heeft_geen_hele_versankers():
    for verse in _chapter()["verses"]:
        for mapping in verse["woordnummers"]:
            assert mapping["tekst"] != verse["text2026"]
            assert len(mapping["tekst"].split()) <= 4
