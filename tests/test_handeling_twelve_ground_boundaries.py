import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _chapter():
    return json.loads((ROOT / "data" / "handelingen" / "12.json").read_text(encoding="utf-8"))


def test_handelingen_twaalf_behoudt_alle_grondtokens():
    chapter = _chapter()
    assert sum(len(verse.get("grondtekst", [])) for verse in chapter["verses"]) == 496


def test_handelingen_twaalf_heeft_vijfentwintig_unieke_verzen():
    numbers = [verse["number"] for verse in _chapter()["verses"]]
    assert numbers == list(range(1, 26))


def test_handelingen_twaalf_begin_en_einde_zijn_grensvast():
    verses = {verse["number"]: verse for verse in _chapter()["verses"]}
    verse_1 = [token["woord"] for token in verses[1]["grondtekst"]]
    verse_25 = [token["woord"] for token in verses[25]["grondtekst"]]

    assert len(verse_1) == 17
    assert verse_1[:4] == ["κατ", "εκεινον", "δε", "τον"]
    assert verse_1[-4:] == ["των", "απο", "της", "εκκλησιας"]
    assert len(verse_25) == 16
    assert verse_25[:4] == ["βαρναβας", "δε", "και", "σαυλος"]
    assert verse_25[-4:] == ["ιωαννην", "τον", "επικληθεντα", "μαρκον"]
