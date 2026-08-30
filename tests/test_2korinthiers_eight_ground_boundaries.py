import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _chapter():
    return json.loads(
        (ROOT / "data" / "2korinthiers" / "8.json").read_text(encoding="utf-8")
    )


def _tokens(verse):
    return [
        (
            token["woord"],
            token["strongs"],
            token["lemma_strongs"],
            token["morfologie"],
        )
        for token in verse["grondtekst"]
    ]


def test_2korinthiers_8_14_bewaart_de_tr_voortzetting_van_8_13():
    verses = {verse["number"]: verse for verse in _chapter()["verses"]}

    expected_continuation = [
        ("αλλ", "G235", "G235", "CONJ"),
        ("εξ", "G1537", "G1537", "PREP"),
        ("ισοτητος", "G2471", "G2471", "N-GSF"),
        ("εν", "G1722", "G1722", "PREP"),
        ("τω", "G3588", "G3588", "T-DSM"),
        ("νυν", "G3568", "G3568", "ADV"),
        ("καιρω", "G2540", "G2540", "N-DSM"),
        ("το", "G3588", "G3588", "T-NSN"),
        ("υμων", "G4771", "G4771", "P-2GP"),
        ("περισσευμα", "G4051", "G4051", "N-NSN"),
        ("εις", "G1519", "G1519", "PREP"),
        ("το", "G3588", "G3588", "T-ASN"),
        ("εκεινων", "G1565", "G1565", "D-GPM"),
        ("υστερημα", "G5303", "G5303", "N-ASN"),
    ]

    assert len(verses[13]["grondtekst"]) == 8
    assert _tokens(verses[14])[:14] == expected_continuation
    assert _tokens(verses[14])[14] == ("ινα", "G2443", "G2443", "CONJ")
    assert len(verses[14]["grondtekst"]) == 27
    assert sum(len(verse["grondtekst"]) for verse in verses.values()) == 414
