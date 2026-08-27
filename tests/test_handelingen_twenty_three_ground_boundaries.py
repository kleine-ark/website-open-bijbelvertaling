import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _chapter():
    return json.loads((ROOT / "data" / "handelingen" / "23.json").read_text(encoding="utf-8"))


def _review():
    return json.loads(
        (ROOT / "data" / "woordnummers-review" / "handelingen-23.json").read_text(
            encoding="utf-8"
        )
    )


def test_handelingen_drieentwintig_behoudt_alle_grondtokens():
    chapter = _chapter()
    assert sum(len(verse.get("grondtekst", [])) for verse in chapter["verses"]) == 677


def test_handelingen_drieentwintig_heeft_vijfendertig_unieke_verzen():
    numbers = [verse["number"] for verse in _chapter()["verses"]]
    assert numbers == list(range(1, 36))


def test_handelingen_drieentwintig_review_dekt_iedere_grondindex_exact_eenmaal():
    chapter = _chapter()
    review_verses = _review()["books"][0]["verses"]
    assert [verse["verse"] for verse in review_verses] == list(range(1, 36))

    for verse, reviewed in zip(chapter["verses"], review_verses, strict=True):
        covered = [
            index
            for mapping in reviewed["mappings"]
            for index in mapping["grondindices"]
        ]
        covered.extend(
            index
            for entry in reviewed.get("ongemapt", [])
            for index in entry["grondindices"]
        )
        assert sorted(covered) == list(range(len(verse.get("grondtekst", []))))
        assert len(covered) == len(set(covered))


def test_handelingen_drieentwintig_publiceert_atomische_koppelingen():
    for verse in _chapter()["verses"]:
        for mapping in verse["woordnummers"]:
            assert mapping["tekst"] != verse["text2026"]
            assert len(mapping["tekst"].split()) <= 4
