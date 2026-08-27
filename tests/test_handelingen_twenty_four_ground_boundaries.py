import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_FLAT_TOKEN_SHA256 = "24B6083D64A0F5E48A8FB65A1FB58F0BA03964AED3A55B65FC8F4D7590BAA457"


def _chapter():
    return json.loads((ROOT / "data" / "handelingen" / "24.json").read_text(encoding="utf-8"))


def _review():
    return json.loads(
        (ROOT / "data" / "woordnummers-review" / "handelingen-24.json").read_text(
            encoding="utf-8"
        )
    )


def test_handelingen_vierentwintig_behoudt_de_volledige_tr_tokenreeks():
    tokens = [token for verse in _chapter()["verses"] for token in verse.get("grondtekst", [])]
    payload = json.dumps(tokens, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    assert len(tokens) == 495
    assert hashlib.sha256(payload).hexdigest().upper() == EXPECTED_FLAT_TOKEN_SHA256


def test_handelingen_vierentwintig_splitst_de_rede_correct_over_vers_twee_en_drie():
    verses = {verse["number"]: verse for verse in _chapter()["verses"]}
    assert len(verses[2]["grondtekst"]) == 8
    assert verses[2]["grondtekst"][-1]["woord"] == "λεγων"
    assert len(verses[3]["grondtekst"]) == 25
    assert verses[3]["grondtekst"][0]["woord"] == "πολλης"
    assert verses[3]["grondtekst"][-1]["woord"] == "ευχαριστιας"


def test_handelingen_vierentwintig_review_dekt_iedere_grondindex_exact_eenmaal():
    chapter = _chapter()
    review_verses = _review()["books"][0]["verses"]
    assert [verse["verse"] for verse in review_verses] == list(range(1, 28))

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


def test_handelingen_vierentwintig_publiceert_atomische_koppelingen():
    for verse in _chapter()["verses"]:
        for mapping in verse["woordnummers"]:
            assert mapping["tekst"] != verse["text2026"]
            assert len(mapping["tekst"].split()) <= 4
