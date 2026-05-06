"""Genereer Genesis 1 met Piper (vaste NL-stem nl_NL-mls-medium).

Run met .venv-piper geactiveerd:
    source .venv-piper/bin/activate
    python -m scripts.tts.run_piper
"""
from __future__ import annotations
import json
import subprocess
from pathlib import Path

MODEL = Path("vendor/piper-voices/nl_NL-mls-medium.onnx")


def extract_genesis_1() -> str:
    data = json.loads(Path("data/genesis/1.json").read_text(encoding="utf-8"))
    return " ".join(v["text2026"].strip() for v in data["verses"] if v.get("text2026"))


def main() -> None:
    if not MODEL.exists():
        raise SystemExit(f"Piper-stem ontbreekt: {MODEL}. Run eerst Task 5 Step 2.")

    text = extract_genesis_1()
    print(f"Tekst-lengte: {len(text)} chars")

    out_dir = Path("audio/_pilot/piper")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_wav = out_dir / "genesis-1.wav"
    out_mp3 = out_dir / "genesis-1.mp3"

    # Piper leest tekst van stdin, schrijft WAV naar bestand
    subprocess.run(
        ["piper", "--model", str(MODEL), "--output_file", str(out_wav)],
        input=text, text=True, check=True,
    )

    subprocess.run([
        "ffmpeg", "-y", "-i", str(out_wav),
        "-codec:a", "libmp3lame", "-b:a", "128k", "-ac", "1",
        str(out_mp3),
    ], check=True)
    out_wav.unlink()
    print(f"Klaar: {out_mp3}")


if __name__ == "__main__":
    main()
