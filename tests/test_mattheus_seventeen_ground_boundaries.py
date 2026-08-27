import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def _chapter():
    return json.loads((ROOT / "data/mattheus/17.json").read_text(encoding="utf-8"))

def _review():
    return json.loads((ROOT / "data/woordnummers-review/mattheus-17.json").read_text(encoding="utf-8"))

def test_mattheus_zeventien_behoudt_alle_grondtokens_en_verzen():
    chapter = _chapter()
    assert [v["number"] for v in chapter["verses"]] == list(range(1, 28))
    assert sum(len(v.get("grondtekst", [])) for v in chapter["verses"]) == 517

def test_mattheus_zeventien_review_dekt_iedere_grondindex_exact_eenmaal():
    chapter = _chapter(); reviews = _review()["books"][0]["verses"]
    assert [v["verse"] for v in reviews] == list(range(1, 28))
    for verse, reviewed in zip(chapter["verses"], reviews, strict=True):
        covered = [i for m in reviewed["mappings"] for i in m["grondindices"]]
        covered += [i for e in reviewed.get("ongemapt", []) for i in e["grondindices"]]
        assert sorted(covered) == list(range(len(verse.get("grondtekst", []))))
        assert len(covered) == len(set(covered))

def test_mattheus_zeventien_publiceert_atomische_koppelingen():
    for verse in _chapter()["verses"]:
        for mapping in verse["woordnummers"]:
            assert mapping["tekst"] != verse["text2026"]
            assert len(mapping["tekst"].split()) <= 4
