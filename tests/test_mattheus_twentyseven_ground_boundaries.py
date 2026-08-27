import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _chapter():
    return json.loads((ROOT / "data/mattheus/27.json").read_text(encoding="utf-8"))


def _review():
    return json.loads((ROOT / "data/woordnummers-review/mattheus-27.json").read_text(encoding="utf-8"))


def test_mattheus_zevenentwintig_behoudt_alle_grondtokens_per_vers():
    verses = _chapter()["verses"]
    assert [verse["number"] for verse in verses] == list(range(1, 67))
    assert sum(len(verse.get("grondtekst", [])) for verse in verses) == 1037
    assert all(verse.get("grondtekst") for verse in verses)


def test_mattheus_zevenentwintig_review_dekt_iedere_grondindex_exact_eenmaal():
    chapter = _chapter()
    reviews = _review()["books"][0]["verses"]
    assert [verse["verse"] for verse in reviews] == list(range(1, 67))
    for verse, reviewed in zip(chapter["verses"], reviews, strict=True):
        covered = [i for mapping in reviewed["mappings"] for i in mapping["grondindices"]]
        covered += [i for entry in reviewed.get("ongemapt", []) for i in entry["grondindices"]]
        assert sorted(covered) == list(range(len(verse.get("grondtekst", []))))
        assert len(covered) == len(set(covered))


def test_mattheus_zevenentwintig_publiceert_atomische_koppelingen():
    for verse in _chapter()["verses"]:
        for mapping in verse["woordnummers"]:
            assert mapping["tekst"] != verse["text2026"]
            assert len(mapping["tekst"].split()) <= 4
