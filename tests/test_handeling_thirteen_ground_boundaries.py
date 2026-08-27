import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _chapter():
    return json.loads((ROOT / "data" / "handelingen" / "13.json").read_text(encoding="utf-8"))


def test_handelingen_dertien_behoudt_alle_grondtokens():
    chapter = _chapter()
    assert sum(len(verse.get("grondtekst", [])) for verse in chapter["verses"]) == 955


def test_handelingen_dertien_heeft_tweeenvijftig_unieke_verzen():
    numbers = [verse["number"] for verse in _chapter()["verses"]]
    assert numbers == list(range(1, 53))


def test_handelingen_dertien_zei_staat_bij_de_zichtbare_tekst_van_vers_negen():
    verses = {verse["number"]: verse for verse in _chapter()["verses"]}
    verse_9 = verses[9]["grondtekst"]
    verse_10 = verses[10]["grondtekst"]

    assert len(verse_9) == 13
    assert verse_9[-1] == {
        "woord": "ειπεν",
        "strongs": "G3004",
        "lemma_strongs": "G3004",
        "morfologie": "V-2AAI-3S",
    }
    assert len(verse_10) == 20
    assert verse_10[0]["woord"] == "ω"
    assert verse_10[0]["strongs"] == "G5599"


def test_handelingen_dertien_beloftevervulling_staat_volledig_in_vers_tweeendertig():
    verses = {verse["number"]: verse for verse in _chapter()["verses"]}
    verse_32 = verses[32]["grondtekst"]
    verse_33 = verses[33]["grondtekst"]

    assert len(verse_32) == 21
    assert [token["woord"] for token in verse_32[-4:]] == [
        "αυτων",
        "ημιν",
        "αναστησας",
        "ιησουν",
    ]
    assert len(verse_33) == 16
    assert verse_33[0]["woord"] == "ως"
    assert verse_33[0]["strongs"] == "G5613"
