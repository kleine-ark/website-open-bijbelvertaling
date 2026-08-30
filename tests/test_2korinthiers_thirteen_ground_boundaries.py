import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CHAPTER = ROOT / "data" / "2korinthiers" / "13.json"


def _verses():
    chapter = json.loads(CHAPTER.read_text(encoding="utf-8"))
    return {verse["number"]: verse for verse in chapter["verses"]}


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


def test_visible_verse_12_combines_tr_verses_12_and_13():
    verses = _verses()
    assert len(verses[12]["grondtekst"]) == 10
    assert _tokens(verses[12])[-5:] == [
        ("ασπαζονται", "G782", "G782", "V-PNI-3P"),
        ("υμας", "G4771", "G4771", "P-2AP"),
        ("οι", "G3588", "G3588", "T-NPM"),
        ("αγιοι", "G40", "G40", "A-NPM"),
        ("παντες", "G3956", "G3956", "A-NPM"),
    ]


def test_visible_verse_13_contains_the_complete_tr_benediction():
    verses = _verses()
    assert len(verses[13]["grondtekst"]) == 21
    assert _tokens(verses[13]) == [
        ("η", "G3588", "G3588", "T-NSF"),
        ("χαρις", "G5485", "G5485", "N-NSF"),
        ("του", "G3588", "G3588", "T-GSM"),
        ("κυριου", "G2962", "G2962", "N-GSM"),
        ("ιησου", "G2424", "G2424", "N-GSM"),
        ("χριστου", "G5547", "G5547", "N-GSM"),
        ("και", "G2532", "G2532", "CONJ"),
        ("η", "G3588", "G3588", "T-NSF"),
        ("αγαπη", "G26", "G26", "N-NSF"),
        ("του", "G3588", "G3588", "T-GSM"),
        ("θεου", "G2316", "G2316", "N-GSM"),
        ("και", "G2532", "G2532", "CONJ"),
        ("η", "G3588", "G3588", "T-NSF"),
        ("κοινωνια", "G2842", "G2842", "N-NSF"),
        ("του", "G3588", "G3588", "T-GSN"),
        ("αγιου", "G40", "G40", "A-GSN"),
        ("πνευματος", "G4151", "G4151", "N-GSN"),
        ("μετα", "G3326", "G3326", "PREP"),
        ("παντων", "G3956", "G3956", "A-GPM"),
        ("υμων", "G4771", "G4771", "P-2GP"),
        ("αμην", "G281", "G281", "HEB"),
    ]


def test_chapter_has_the_complete_242_token_tr_stream():
    verses = _verses()
    assert sorted(verses) == list(range(1, 14))
    assert sum(len(verse["grondtekst"]) for verse in verses.values()) == 242
