"""Gerichte regressietests voor geografische tags in de Torah."""

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
BOOKS = {
    "genesis": 1533,
    "exodus": 1213,
    "leviticus": 859,
    "numeri": 1288,
    "deuteronomium": 959,
}
TYPES = {
    "plaats", "land-streek", "berg", "rivier-water", "woestijn",
    "stad-dorp", "route-legerplaats",
}


def load(book):
    return json.loads((DATA / f"{book}-geo.json").read_text(encoding="utf-8"))


def verse_text(book, key):
    chapter, number = map(int, key.split(":"))
    data = json.loads((DATA / book / f"{chapter}.json").read_text(encoding="utf-8"))
    return next(v["text2026"] for v in data["verses"] if v["number"] == number)


def test_alle_torahverzen_zijn_beoordeeld_zonder_menselijke_reviewclaim():
    for book, expected in BOOKS.items():
        data = load(book)
        assert data["status"] == "agent-reviewed"
        assert data["humanReviewed"] is False
        assert data["dekking"]["verzenBeoordeeld"] == expected


def test_tags_hebben_stabiele_ids_types_links_en_zichtbare_labels():
    for book in BOOKS:
        data = load(book)
        for key, mentions in data["mentions"].items():
            text = verse_text(book, key)
            for mention in mentions:
                assert re.fullmatch(r"geo-[a-z0-9-]+", mention["id"])
                assert mention["type"] in TYPES
                assert mention["status"] == "agent-reviewed"
                assert mention["label"].casefold() in text.casefold()
                assert mention["href"] == f"index.html#{book}/{key.replace(':', '/')}"


def test_bekende_locaties_en_contextuele_typen():
    assert {m["type"] for m in load("exodus")["mentions"]["3:1"] if m["label"] == "Horeb"} == {"berg"}
    assert any(m["id"] == "geo-eskol" for m in load("numeri")["mentions"]["13:23"])
    assert any(m["type"] == "route-legerplaats" for m in load("numeri")["mentions"]["33:44"])
    assert any(m["id"] == "geo-nebo" and m["type"] == "berg" for m in load("deuteronomium")["mentions"]["34:1"])


def test_homoniem_dan_wordt_niet_blind_getagd():
    assert "1:12" not in load("numeri")["mentions"]
    assert any(m["id"] == "geo-dan" for m in load("deuteronomium")["mentions"]["34:1"])


def test_twijfelgevallen_staan_niet_op_human_reviewed():
    queue = [item for book in BOOKS for item in load(book)["reviewQueue"]]
    assert queue
    assert all(item["status"] == "needs-human-review" for item in queue)
