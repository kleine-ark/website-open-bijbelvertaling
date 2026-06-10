"""Uitspraak-lexicon voor TTS.

Vervangt probleemwoorden door een herspelling die het TTS-model beter
uitspreekt (bijv. klemtoon via accent-aigu: 'begere' -> 'begére').

BELANGRIJK: dit wordt ALLEEN toegepast op de tekst die naar de TTS gaat,
nooit op de tekst die op de website staat. De website toont gewoon 'begere'.

Gebruik:
    from scripts.tts.pronunciation import load_lexicon, apply_lexicon
    lex = load_lexicon()
    tts_text = apply_lexicon(raw_text, lex)
"""
from __future__ import annotations

import json
import re
from pathlib import Path

LEXICON_PATH = Path(__file__).parent / "pronunciation_lexicon.json"

# Een 'woord' = aaneengesloten letters incl. Nederlandse/Latijnse diakrieten.
_WORD_RE = re.compile(r"[A-Za-zÀ-ÿ]+")


def load_lexicon(path: Path | str = LEXICON_PATH) -> dict[str, str]:
    """Laad het lexicon; negeer _comment en normaliseer keys naar kleine letters."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return {
        k.lower(): v
        for k, v in data.items()
        if not k.startswith("_") and isinstance(v, str)
    }


def _match_case(original: str, replacement: str) -> str:
    """Neem de hoofdletter-vorm van het origineel over op de vervanging.

    - 'Begere'  -> 'Begére'   (eerste letter hoofdletter)
    - 'BEGERE'  -> 'BEGÉRE'   (volledig hoofdletters)
    - 'begere'  -> 'begére'   (kleine letters, ongewijzigd)

    Uitzondering: als de vervanging zélf al een hoofdletter bevat, is de
    schrijfwijze bewust gekozen (bijv. 'Jaawee', 'Ka-in') en gebruiken we die
    letterlijk — zo wordt 'JAHWEH' niet 'JAAWEE' (dat zou TTS kunnen spellen).
    """
    if any(c.isupper() for c in replacement):
        return replacement
    if original.isupper():
        return replacement.upper()
    if original[:1].isupper():
        return replacement[:1].upper() + replacement[1:]
    return replacement


def apply_lexicon(text: str, lexicon: dict[str, str]) -> str:
    """Vervang elk heel woord dat in het lexicon staat, met behoud van hoofdletters."""
    if not lexicon:
        return text

    def _sub(m: re.Match[str]) -> str:
        word = m.group(0)
        repl = lexicon.get(word.lower())
        if repl is None:
            return word
        return _match_case(word, repl)

    return _WORD_RE.sub(_sub, text)


if __name__ == "__main__":
    import sys

    lex = load_lexicon()
    sample = " ".join(sys.argv[1:]) or "Wie begere te leven, die begeren het goede; begerig zijn."
    print("Lexicon-entries:", len(lex))
    print("In: ", sample)
    print("Uit:", apply_lexicon(sample, lex))
