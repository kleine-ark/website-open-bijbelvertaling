import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _chapter():
    return json.loads((ROOT / "data/mattheus/25.json").read_text(encoding="utf-8"))


def _review():
    return json.loads((ROOT / "data/woordnummers-review/mattheus-25.json").read_text(encoding="utf-8"))


def test_mattheus_vijfentwintig_behoudt_alle_grondtokens_per_vers():
    chapter = _chapter()
    assert [verse["number"] for verse in chapter["verses"]] == list(range(1, 47))
    assert sum(len(verse.get("grondtekst", [])) for verse in chapter["verses"]) == 778
    assert chapter["verses"][0]["grondtekst"][0]["strongs"] == "G5119"
    assert chapter["verses"][-1]["grondtekst"][-1]["strongs"] == "G166"


def test_mattheus_vijfentwintig_review_dekt_iedere_grondindex_exact_eenmaal():
    chapter = _chapter()
    reviews = _review()["books"][0]["verses"]
    assert [verse["verse"] for verse in reviews] == list(range(1, 47))
    for verse, reviewed in zip(chapter["verses"], reviews, strict=True):
        covered = [i for mapping in reviewed["mappings"] for i in mapping["grondindices"]]
        covered += [i for entry in reviewed.get("ongemapt", []) for i in entry["grondindices"]]
        assert sorted(covered) == list(range(len(verse.get("grondtekst", []))))
        assert len(covered) == len(set(covered))


def test_mattheus_vijfentwintig_publiceert_atomische_koppelingen():
    for verse in _chapter()["verses"]:
        for mapping in verse["woordnummers"]:
            assert mapping["tekst"] != verse["text2026"]
            assert len(mapping["tekst"].split()) <= 4
