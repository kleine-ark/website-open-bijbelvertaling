from pathlib import Path
from scripts.tts.extract_chapter_text import extract_chapter_text

DATA = Path("data")

def test_genesis_1_starts_correctly():
    text = extract_chapter_text(DATA, "genesis", 1)
    assert text.startswith("In de beginne schiep God de hemel en de aarde.")

def test_genesis_1_joins_all_31_verses():
    text = extract_chapter_text(DATA, "genesis", 1)
    # Vers 31 eindigt op "zeer goed."
    assert "zeer goed." in text
    # Length-sanity: ~4200 chars verwacht
    assert 3500 < len(text) < 5000

def test_verses_separated_by_single_space():
    text = extract_chapter_text(DATA, "genesis", 1)
    # Geen dubbele spaties
    assert "  " not in text
    # Geen newlines (we willen één string voor TTS)
    assert "\n" not in text
