import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _chapter():
    return json.loads((ROOT / "data" / "handelingen" / "10.json").read_text(encoding="utf-8"))


def test_handelingen_tien_behoudt_alle_grondtokens():
    chapter = _chapter()
    assert sum(len(verse.get("grondtekst", [])) for verse in chapter["verses"]) == 871


def test_handelingen_tien_verzen_dertig_en_eenendertig_zijn_grensvast():
    verses = {verse["number"]: verse for verse in _chapter()["verses"]}
    verse_30 = [token["woord"] for token in verses[30]["grondtekst"]]
    verse_31 = [token["woord"] for token in verses[31]["grondtekst"]]

    assert len(verse_30) == 22
    assert verse_30[-4:] == ["εν", "τω", "οικω", "μου"]
    assert len(verse_31) == 24
    assert verse_31[:9] == [
        "και",
        "ιδου",
        "ανηρ",
        "εστη",
        "ενωπιον",
        "μου",
        "εν",
        "εσθητι",
        "λαμπρα",
    ]


def test_handelingen_tien_heeft_achtenveertig_unieke_verzen():
    numbers = [verse["number"] for verse in _chapter()["verses"]]
    assert numbers == list(range(1, 49))
