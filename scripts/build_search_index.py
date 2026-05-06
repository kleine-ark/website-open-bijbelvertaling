#!/usr/bin/env python3
"""Bouw data/search-index.json — een flat array met alle bijbelverzen
voor de client-side zoekfunctie.

Bron: data/{boek}/{nr}.json voor elk boek dat in data/books.json staat.
Voorkeur voor 'text2026' (moderne tekst). Als leeg, fallback naar 'textSV1888'.

Output formaat (compact):
    [{"b": "genesis", "c": 1, "v": 1, "t": "In de beginne schiep God de hemel en de aarde."}, ...]

Korte keys (b/c/v/t) houden de bestandsgrootte beperkt.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
BOOKS_JSON = DATA_DIR / "books.json"
OUT_PATH = DATA_DIR / "search-index.json"


_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")


def strip_html(text: str) -> str:
    """Strip HTML-tags en normaliseer whitespace.

    De text2026/textSV1888 velden zijn doorgaans plain text, maar voor
    de zekerheid filteren we eventuele tags weg en collapsen we whitespace.
    """
    if not text:
        return ""
    s = _TAG_RE.sub("", text)
    s = s.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    s = s.replace("&quot;", '"').replace("&#39;", "'").replace("&nbsp;", " ")
    return _WS_RE.sub(" ", s).strip()


def load_books() -> list[dict]:
    with BOOKS_JSON.open("r", encoding="utf-8") as f:
        return json.load(f)["books"]


def iter_chapters(book_id: str):
    """Yield (chapter_num, chapter_data) voor alle hoofdstukken van een boek.

    Probeert eerst data/{book_id}/*.json (per-hoofdstuk-files), wat het
    canonieke formaat is. Als die niet bestaan, valt terug op de
    boek-bundel data/{book_id}.json (met chapters-array).
    """
    book_dir = DATA_DIR / book_id
    if book_dir.is_dir():
        files = sorted(
            book_dir.glob("*.json"),
            key=lambda p: int(p.stem) if p.stem.isdigit() else 9999,
        )
        for fp in files:
            if not fp.stem.isdigit():
                continue
            try:
                with fp.open("r", encoding="utf-8") as f:
                    chapter = json.load(f)
            except (OSError, json.JSONDecodeError) as e:
                print(f"  ! kan {fp} niet lezen: {e}", file=sys.stderr)
                continue
            yield int(fp.stem), chapter
        return

    # Fallback: full-book bundle
    bundle = DATA_DIR / f"{book_id}.json"
    if not bundle.exists():
        return
    try:
        with bundle.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        print(f"  ! kan {bundle} niet lezen: {e}", file=sys.stderr)
        return
    for ch in data.get("chapters", []):
        yield ch.get("number"), ch


def main() -> int:
    if not BOOKS_JSON.exists():
        print(f"books.json niet gevonden: {BOOKS_JSON}", file=sys.stderr)
        return 1

    books = load_books()
    print(f"Index bouwen van {len(books)} boeken...")

    entries: list[dict] = []
    book_count = 0
    skipped_books: list[str] = []

    for book in books:
        book_id = book["id"]
        added_for_book = 0
        for ch_num, chapter in iter_chapters(book_id):
            if ch_num is None:
                continue
            for verse in chapter.get("verses", []) or []:
                v_num = verse.get("number")
                if v_num is None:
                    continue
                text = strip_html(verse.get("text2026") or "")
                if not text:
                    text = strip_html(verse.get("textSV1888") or "")
                if not text:
                    continue
                entries.append({"b": book_id, "c": ch_num, "v": v_num, "t": text})
                added_for_book += 1

        if added_for_book == 0:
            skipped_books.append(book_id)
        else:
            book_count += 1
            print(f"  {book_id}: {added_for_book} verzen")

    if skipped_books:
        print(f"\n!! Geen verzen gevonden voor: {', '.join(skipped_books)}")

    print(f"\nTotaal: {len(entries)} verzen uit {book_count} boeken")

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    # Compact JSON (geen indent, geen spaties) houdt het bestand klein.
    with OUT_PATH.open("w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, separators=(",", ":"))

    size = OUT_PATH.stat().st_size
    print(f"Geschreven naar {OUT_PATH} ({size:,} bytes / {size / 1024 / 1024:.2f} MB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
