import hashlib
import json
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
CHAPTER = REPO / "data" / "mattheus" / "28.json"
FLAT_TOKEN_SHA256 = "0D1114AF37AE2F96AEEE7A4CA712DC2DEC24DBB30ED9000ADF56F09618F4CE97"


def load_chapter():
    return json.loads(CHAPTER.read_text(encoding="utf-8"))


def test_ground_token_sequence_is_lossless():
    chapter = load_chapter()
    tokens = [token for verse in chapter["verses"] for token in verse["grondtekst"]]
    payload = json.dumps(tokens, ensure_ascii=False, separators=(",", ":")).encode()

    assert len(tokens) == 341
    assert hashlib.sha256(payload).hexdigest().upper() == FLAT_TOKEN_SHA256


def test_teaching_clause_belongs_to_visible_verse_nineteen():
    chapter = load_chapter()
    verse_19 = chapter["verses"][18]
    verse_20 = chapter["verses"][19]

    assert [token["woord"] for token in verse_19["grondtekst"][-7:]] == [
        "διδασκοντες",
        "αυτους",
        "τηρειν",
        "παντα",
        "οσα",
        "ενετειλαμην",
        "υμιν",
    ]
    assert verse_20["grondtekst"][0]["woord"] == "και"


def test_visible_verse_ground_counts_are_stable():
    chapter = load_chapter()

    assert len(chapter["verses"]) == 20
    assert len(chapter["verses"][18]["grondtekst"]) == 27
    assert len(chapter["verses"][19]["grondtekst"]) == 15
