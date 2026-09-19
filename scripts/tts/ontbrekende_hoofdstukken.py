#!/usr/bin/env python3
"""Schrijf een manifest van de hoofdstukken die nog geen voorlezing hebben.

De lijst met beschikbare audio staat in js/audio-available.js (window.AUDIO_AVAILABLE);
de volledige boekenlijst in data/books-index.json. Wat daar wel in staat maar niet in de
audio-lijst, moet nog gegenereerd worden.

Gebruik vanuit de repo-root:
    python scripts/tts/ontbrekende_hoofdstukken.py            # schrijft scripts/tts/ontbrekend.json
    python scripts/tts/ontbrekende_hoofdstukken.py --boeken genesis,exodus

Daarna per stem genereren (op de machine met .venv-higgs-v3):
    python -m scripts.tts.run_higgs_v3 --manifest scripts/tts/ontbrekend.json --voice m --sample audio/_pilot/_sample/sample
    python -m scripts.tts.run_higgs_v3 --manifest scripts/tts/ontbrekend.json --voice v --sample audio/_pilot/_sample/sample-v

Een hoofdstuk telt pas mee in js/audio-available.js als beide stemmen op de server staan.
"""
import argparse
import json
import subprocess
from pathlib import Path

WORTEL = Path(__file__).resolve().parents[2]


def beschikbaar():
    """Lees window.AUDIO_AVAILABLE uit js/audio-available.js — door node, niet met regels."""
    uit = subprocess.run(
        ["node", "-e",
         "global.window = {}; require(process.argv[1]); "
         "process.stdout.write(JSON.stringify(window.AUDIO_AVAILABLE || {}))",
         str(WORTEL / "js" / "audio-available.js")],
        capture_output=True, check=True)
    return json.loads(uit.stdout.decode("utf-8"))


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--boeken", help="alleen deze boek-ids, met komma's gescheiden")
    p.add_argument("--uit", default=str(WORTEL / "scripts" / "tts" / "ontbrekend.json"))
    a = p.parse_args()

    audio = beschikbaar()
    boeken = json.loads((WORTEL / "data" / "books-index.json").read_text(encoding="utf-8"))["boeken"]
    keuze = set(a.boeken.split(",")) if a.boeken else None
    manifest, totaal = [], 0
    for boek in boeken:
        if keuze and boek["id"] not in keuze:
            continue
        eerste = boek.get("eerste_hoofdstuk", 1)
        alle = list(range(eerste, eerste + boek["hoofdstukken"]))
        heeft = set(audio.get(boek["id"]) or [])
        mist = [n for n in alle if n not in heeft]
        if mist:
            manifest.append({"book": boek["id"], "chapters": mist})
            totaal += len(mist)
    Path(a.uit).write_text(json.dumps(manifest, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(f"{totaal} hoofdstukken zonder voorlezing in {len(manifest)} boeken → {a.uit}")
    for entry in manifest[:10]:
        print(f"  {entry['book']}: {len(entry['chapters'])}")
    if len(manifest) > 10:
        print(f"  … en nog {len(manifest) - 10} boeken")


if __name__ == "__main__":
    main()
