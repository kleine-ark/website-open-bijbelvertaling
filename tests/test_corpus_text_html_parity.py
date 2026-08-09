"""Bewaar inhoudelijke pariteit tussen de platte en opgemaakte leestekst."""

import html
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"


def _visible_text(markup: str) -> str:
    markup = re.sub(
        r"<sup\b[^>]*>.*?</sup>", "", markup or "", flags=re.IGNORECASE | re.DOTALL
    )
    markup = re.sub(r"<[^>]+>", "", markup)
    return re.sub(r"\s+", " ", html.unescape(markup).replace("\u00a0", " ")).strip()


def _content_text(text: str) -> str:
    # Aanhalingstekens worden alleen in de opgemaakte citaatlaag toegevoegd.
    text = text.replace("“", "").replace("”", "").replace('"', "")
    # Enkele oude datasets bewaren een perikoopkop alleen in de HTML-laag.
    text = re.sub(r"^<<[^>]+>>\s*", "", text)
    return text.removeprefix("> ").strip()


def test_zichtbare_html_heeft_dezelfde_woorden_als_de_platte_tekst():
    verschillen = []

    for chapter_path in DATA.glob("*/*.json"):
        if chapter_path.parent.name in {"definitief", "naslag-teksten"}:
            continue
        try:
            chapter = json.loads(chapter_path.read_text(encoding="utf-8-sig"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            continue
        if not isinstance(chapter, dict) or not isinstance(chapter.get("verses"), list):
            continue

        for verse in chapter["verses"]:
            if not isinstance(verse, dict):
                continue
            plain = verse.get("text2026")
            markup = verse.get("text2026_html")
            # Een lege HTML-laag valt in de lezer bewust terug op text2026.
            if not isinstance(plain, str) or not isinstance(markup, str) or not markup:
                continue
            visible = _visible_text(markup)
            if _content_text(plain) != _content_text(visible):
                verschillen.append(
                    f"{chapter_path.parent.name} {chapter_path.stem}:"
                    f"{verse.get('number', '?')}\n  tekst: {plain}\n  html:  {visible}"
                )

    assert not verschillen, "\n\n".join(verschillen)
