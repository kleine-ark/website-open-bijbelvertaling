import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _chapter():
    return json.loads((ROOT / "data" / "handelingen" / "14.json").read_text(encoding="utf-8"))


def test_handelingen_veertien_behoudt_alle_grondtokens():
    chapter = _chapter()
    assert sum(len(verse.get("grondtekst", [])) for verse in chapter["verses"]) == 479


def test_handelingen_veertien_heeft_achtentwintig_unieke_verzen():
    numbers = [verse["number"] for verse in _chapter()["verses"]]
    assert numbers == list(range(1, 29))


def test_handelingen_veertien_behoudt_de_grondtekstuiteinden():
    verses = _chapter()["verses"]
    assert verses[0]["grondtekst"][0]["woord"] == "εγενετο"
    assert verses[0]["grondtekst"][0]["strongs"] == "G1096"
    assert len(verses[-1]["grondtekst"]) == 9
    assert verses[-1]["grondtekst"][-1]["woord"] == "μαθηταις"
    assert verses[-1]["grondtekst"][-1]["strongs"] == "G3101"
