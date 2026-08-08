#!/usr/bin/env python3
"""Bouw corpusbrede wiki-naslagdata uit de zichtbare Open Vertaling."""

from __future__ import annotations

from dataclasses import dataclass
import html
import json
from pathlib import Path
import re
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
CATALOG_PATH = DATA / "naslag-catalogus.json"
OUTPUTS = {
    "materialen": "naslag-materialen.json",
    "dieren": "naslag-dieren.json",
    "bomen-planten": "naslag-bomen-planten.json",
    "personen": "naslag-personen.json",
    "muziekinstrumenten": "naslag-muziekinstrumenten.json",
}


@dataclass(frozen=True)
class VerseRef:
    book_id: str
    book_name: str
    testament: str
    chapter: int
    verse: int
    text: str

    @property
    def ref(self) -> str:
        return f"{self.book_id} {self.chapter}:{self.verse}"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def normalize_visible_text(markup: str) -> str:
    """Projecteer site-HTML op zichtbare tekst zonder kanttekeningnummers."""
    text = re.sub(r"<sup\b[^>]*>.*?</sup>", "", markup or "", flags=re.I | re.S)
    text = re.sub(r"<[^>]+>", "", text)
    return re.sub(r"\s+", " ", html.unescape(text)).strip()


def load_books(root: Path = ROOT) -> list[dict[str, Any]]:
    return read_json(root / "data" / "books.json")["books"]


def load_corpus(root: Path = ROOT) -> list[VerseRef]:
    """Lees alle echte versteksten in de vaste boek-, hoofdstuk- en versvolgorde."""
    corpus: list[VerseRef] = []
    for book in load_books(root):
        if book.get("ethiopic"):
            continue
        for chapter in book.get("chaptersIncluded", []):
            path = root / "data" / book["id"] / f"{chapter}.json"
            if not path.exists():
                continue
            data = read_json(path)
            for verse in data.get("verses", []):
                if not isinstance(verse, dict):
                    continue
                raw = verse.get("text2026_html") or verse.get("text2026") or ""
                text = normalize_visible_text(raw)
                if not text:
                    continue
                corpus.append(
                    VerseRef(
                        book_id=book["id"],
                        book_name=book["nameDutch"],
                        testament=book.get("testament", ""),
                        chapter=int(chapter),
                        verse=int(verse["number"]),
                        text=text,
                    )
                )
    return corpus


def _base_dataset(title: str, intro: str, books: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "titel": title,
        "bron": "de hele Bijbel",
        "corpusbreed": True,
        "intro": intro,
        "boeknamen": {
            book["id"]: book["nameDutch"]
            for book in books
            if book.get("chaptersIncluded") and not book.get("ethiopic")
        },
        "items": [],
    }


def build_all(root: Path = ROOT, write: bool = True) -> dict[str, dict[str, Any]]:
    """Bouw alle vijf gegevenssets; `write=False` is puur en testbaar."""
    catalog = read_json(root / "data" / "naslag-catalogus.json")
    books = load_books(root)
    built: dict[str, dict[str, Any]] = {}
    for category, definition in catalog["categorieen"].items():
        built[category] = _base_dataset(
            definition["titel"], definition.get("intro", ""), books
        )
    people = catalog["personen"]
    built["personen"] = _base_dataset(
        people["titel"], people.get("intro", ""), books
    )

    if write:
        for category, filename in OUTPUTS.items():
            target = root / "data" / filename
            target.write_text(
                json.dumps(built[category], ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
    return built


def main() -> int:
    corpus = load_corpus(ROOT)
    built = build_all(ROOT, write=True)
    counts = ", ".join(f"{name}: {len(data['items'])}" for name, data in built.items())
    print(f"Corpusnaslag gebouwd uit 82 boeken en {len(corpus)} verzen ({counts})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
