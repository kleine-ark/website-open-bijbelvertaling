"""Extracteer text2026 verzen uit data/{book}/{chapter}.json."""
from __future__ import annotations
import json
from pathlib import Path


def extract_chapter_text(data_dir: Path, book: str, chapter: int) -> str:
    """Lees text2026 van alle verzen in een hoofdstuk en join met spaties.

    Verwacht structuur: data/{book}/{chapter}.json met {"verses": [{"text2026": ...}, ...]}
    """
    path = data_dir / book / f"{chapter}.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    parts = []
    for verse in data["verses"]:
        text = verse.get("text2026", "").strip()
        if text:
            parts.append(text)
    return " ".join(parts)


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        print("Gebruik: python -m scripts.tts.extract_chapter_text <book> <chapter>")
        sys.exit(1)
    book, chapter = sys.argv[1], int(sys.argv[2])
    print(extract_chapter_text(Path("data"), book, chapter))
