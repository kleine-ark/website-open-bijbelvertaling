import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _chapter():
    return json.loads((ROOT / "data" / "handelingen" / "11.json").read_text(encoding="utf-8"))


def test_handelingen_elf_behoudt_alle_grondtokens():
    chapter = _chapter()
    assert sum(len(verse.get("grondtekst", [])) for verse in chapter["verses"]) == 533


def test_handelingen_elf_verzen_vijfentwintig_en_zesentwintig_zijn_grensvast():
    verses = {verse["number"]: verse for verse in _chapter()["verses"]}
    verse_25 = [token["woord"] for token in verses[25]["grondtekst"]]
    verse_26 = [token["woord"] for token in verses[26]["grondtekst"]]

    assert len(verse_25) == 15
    assert verse_25[-7:] == [
        "και",
        "ευρων",
        "αυτον",
        "ηγαγεν",
        "αυτον",
        "εις",
        "αντιοχειαν",
    ]
    assert len(verse_26) == 21
    assert verse_26[:5] == ["εγενετο", "δε", "αυτους", "ενιαυτον", "ολον"]


def test_handelingen_elf_heeft_dertig_unieke_verzen():
    numbers = [verse["number"] for verse in _chapter()["verses"]]
    assert numbers == list(range(1, 31))
