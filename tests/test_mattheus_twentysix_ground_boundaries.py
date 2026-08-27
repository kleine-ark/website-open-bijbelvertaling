import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _chapter():
    return json.loads((ROOT / "data/mattheus/26.json").read_text(encoding="utf-8"))


def _review():
    return json.loads((ROOT / "data/woordnummers-review/mattheus-26.json").read_text(encoding="utf-8"))


def test_mattheus_zesentwintig_behoudt_alle_grondtokens_bij_herstelde_versgrenzen():
    chapter = _chapter()
    verses = chapter["verses"]
    assert [verse["number"] for verse in verses] == list(range(1, 76))
    assert sum(len(verse.get("grondtekst", [])) for verse in verses) == 1275
    assert verses[59]["grondtekst"][-1]["strongs"] == "G2147"
    assert verses[60]["grondtekst"][0]["strongs"] == "G5305"
    assert verses[60]["grondtekst"][5]["strongs"] == "G3004"
    assert verses[66]["grondtekst"][-1]["strongs"] == "G846"
    assert verses[67]["grondtekst"][0]["strongs"] == "G3588"
    assert verses[67]["grondtekst"][3]["strongs"] == "G3004"
    assert verses[73]["grondtekst"][-1]["strongs"] == "G444"
    assert verses[74]["grondtekst"][0]["strongs"] == "G2532"
    assert verses[74]["grondtekst"][2]["strongs"] == "G220"


def test_mattheus_zesentwintig_review_dekt_iedere_grondindex_exact_eenmaal():
    chapter = _chapter()
    reviews = _review()["books"][0]["verses"]
    assert [verse["verse"] for verse in reviews] == list(range(1, 76))
    for verse, reviewed in zip(chapter["verses"], reviews, strict=True):
        covered = [i for mapping in reviewed["mappings"] for i in mapping["grondindices"]]
        covered += [i for entry in reviewed.get("ongemapt", []) for i in entry["grondindices"]]
        assert sorted(covered) == list(range(len(verse.get("grondtekst", []))))
        assert len(covered) == len(set(covered))


def test_mattheus_zesentwintig_publiceert_atomische_koppelingen():
    for verse in _chapter()["verses"]:
        for mapping in verse["woordnummers"]:
            assert mapping["tekst"] != verse["text2026"]
            assert len(mapping["tekst"].split()) <= 4
