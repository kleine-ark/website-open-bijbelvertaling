import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _chapter():
    return json.loads((ROOT / "data/mattheus/21.json").read_text(encoding="utf-8"))


def _review():
    return json.loads(
        (ROOT / "data/woordnummers-review/mattheus-21.json").read_text(encoding="utf-8")
    )


def test_mattheus_eenentwintig_plaatst_zeggende_tot_hen_in_vers_een():
    chapter = _chapter()
    assert [v["number"] for v in chapter["verses"]] == list(range(1, 47))
    assert sum(len(v.get("grondtekst", [])) for v in chapter["verses"]) == 870
    first, second = chapter["verses"][:2]
    assert [token["strongs"] for token in first["grondtekst"][-2:]] == ["G3004", "G846"]
    assert second["grondtekst"][0]["strongs"] == "G4198"


def test_mattheus_eenentwintig_review_dekt_iedere_grondindex_exact_eenmaal():
    chapter = _chapter()
    reviews = _review()["books"][0]["verses"]
    assert [v["verse"] for v in reviews] == list(range(1, 47))
    for verse, reviewed in zip(chapter["verses"], reviews, strict=True):
        covered = [i for mapping in reviewed["mappings"] for i in mapping["grondindices"]]
        covered += [i for entry in reviewed.get("ongemapt", []) for i in entry["grondindices"]]
        assert sorted(covered) == list(range(len(verse.get("grondtekst", []))))
        assert len(covered) == len(set(covered))


def test_mattheus_eenentwintig_publiceert_atomische_koppelingen():
    for verse in _chapter()["verses"]:
        for mapping in verse["woordnummers"]:
            assert mapping["tekst"] != verse["text2026"]
            assert len(mapping["tekst"].split()) <= 4
