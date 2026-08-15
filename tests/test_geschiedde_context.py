import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

CONTEXTUAL_EXPECTATIONS = {
    ("2koningen", 20, 4): ("woord van JAHWEH tot hem kwam", "V1230"),
    ("ezechiel", 1, 25): ("een stem van boven het uitspansel", "V1238"),
    ("ezechiel", 3, 16): ("woord van JAHWEH tot mij kwam", "V1230"),
    ("ezechiel", 26, 1): ("woord van JAHWEH tot mij kwam", "V1230"),
    ("ezechiel", 29, 17): ("woord van JAHWEH tot mij kwam", "V1230"),
    ("ezechiel", 30, 20): ("woord van JAHWEH tot mij kwam", "V1230"),
    ("ezechiel", 31, 1): ("woord van JAHWEH tot mij kwam", "V1230"),
    ("ezechiel", 32, 1): ("woord van JAHWEH tot mij kwam", "V1230"),
    ("ezechiel", 32, 17): ("woord van JAHWEH tot mij kwam", "V1230"),
    ("haggai", 2, 21): ("woord van JAHWEH nu kwam", "V1230"),
    ("jeremia", 1, 4): ("woord van JAHWEH dan kwam", "V1230"),
    ("jeremia", 26, 1): ("kwam dit woord van JAHWEH", "V1230"),
    ("jeremia", 27, 1): ("kwam dit woord tot Jeremia", "V1230"),
    ("jeremia", 36, 1): ("dit woord van JAHWEH tot Jeremia kwam", "V1230"),
    ("jeremia", 42, 7): ("woord van JAHWEH tot Jeremia kwam", "V1230"),
    ("jeremia", 44, 1): ("woord, dat tot Jeremia kwam", "V1230"),
    ("jeremia", 47, 1): ("woord van JAHWEH, dat tot de profeet Jeremia kwam", "V1230"),
    ("lukas", 1, 44): ("stem van uw groetenis in mijn oren klonk", "V1238"),
    ("lukas", 9, 35): ("een stem uit de wolk", "V1238"),
    ("lukas", 9, 36): ("toen de stem geklonken had", "V1238"),
    ("4ezra", 14, 38): ("riep een stem mij", "V1238"),
    ("openbaring", 8, 5): ("er klonken stemmen", "V1238"),
    ("openbaring", 11, 15): ("er klonken grote stemmen", "V1238"),
    ("openbaring", 16, 18): ("er klonken stemmen", "V1238"),
}


def iter_verses():
    for path in (ROOT / "data").glob("*/*.json"):
        try:
            chapter = json.loads(path.read_text(encoding="utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            continue
        for verse in chapter.get("verses", []):
            if isinstance(verse, dict):
                yield path, verse


def test_geschiedde_is_not_used_as_unexamined_narrative_formula():
    remaining = []
    for path, verse in iter_verses():
        text = verse.get("text2026", "")
        if "geschiedde" in text.lower():
            remaining.append(f"{path.parent.name} {path.stem}:{verse['number']}: {text}")

    assert remaining == [], "\n".join(remaining)


def test_revelatory_word_or_voice_comes_instead_of_happens():
    invalid = []
    for path, verse in iter_verses():
        text = verse.get("text2026", "").lower()
        if "woord van jahweh gebeurde" in text or "een stem gebeurde" in text:
            invalid.append(f"{path.parent.name} {path.stem}:{verse['number']}: {text}")

    assert invalid == [], "\n".join(invalid)


def test_contextual_principles_distinguish_gebeurde_kwam_and_exceptions():
    principles = json.loads(
        (ROOT / "data" / "wijzigingsprincipes.json").read_text(encoding="utf-8")
    )["principes"]
    by_id = {principle["id"]: principle for principle in principles}

    assert by_id["V199"]["nieuw"] == "gebeurde"
    assert "context" in by_id["V199"]["toelichting"].lower()
    assert by_id["V1230"]["nieuw"] == "kwam het woord van JAHWEH"
    assert "blijven" in by_id["V776"]["toelichting"].lower()


def test_remaining_apocryphal_occurrence_is_linked_to_the_principle():
    chapter = json.loads(
        (ROOT / "data" / "estherapocrief" / "15.json").read_text(encoding="utf-8")
    )
    verse = chapter["verses"][0]
    assert "het gebeurde op de derde dag" in verse["text2026"]
    assert {
        "old": "geschiedde",
        "new": "gebeurde",
        "principe": "V199",
    } in verse["phraseDiff"]


def test_all_certain_contextual_corrections_are_applied_and_linked():
    for (book, chapter_number, verse_number), (expected, principle) in CONTEXTUAL_EXPECTATIONS.items():
        chapter = json.loads(
            (ROOT / "data" / book / f"{chapter_number}.json").read_text(encoding="utf-8")
        )
        verse = next(item for item in chapter["verses"] if item.get("number") == verse_number)
        assert expected in verse["text2026"], f"{book} {chapter_number}:{verse_number}"
        assert any(diff.get("principe") == principle for diff in verse.get("phraseDiff", [])), (
            f"{book} {chapter_number}:{verse_number} mist {principle}"
        )
