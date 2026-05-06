"""Knip 20s sample uit audio/Genesis 1.mp3 en transcribeer met faster-whisper.

Output: audio/_pilot/_sample/sample.wav (22050 Hz mono) + sample.txt.
"""
from __future__ import annotations
import subprocess
from pathlib import Path

SOURCE = Path("audio/Genesis 1.mp3")
OUT_DIR = Path("audio/_pilot/_sample")
OUT_WAV = OUT_DIR / "sample.wav"
OUT_TXT = OUT_DIR / "sample.txt"

# Skip eerste 30s (eventuele intro/inademing) en pak 20s.
START_SEC = 30
DURATION_SEC = 20


def cut_sample() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg", "-y",
        "-ss", str(START_SEC),
        "-t", str(DURATION_SEC),
        "-i", str(SOURCE),
        "-ar", "22050",
        "-ac", "1",
        "-c:a", "pcm_s16le",
        str(OUT_WAV),
    ]
    subprocess.run(cmd, check=True)
    print(f"Sample geschreven: {OUT_WAV}")


def transcribe() -> None:
    from faster_whisper import WhisperModel
    # large-v3 voor beste NL-kwaliteit; valt terug op CPU als CUDA niet werkt
    model = None
    try:
        model = WhisperModel("large-v3", device="cuda", compute_type="float16")
        segments, info = model.transcribe(str(OUT_WAV), language="nl", beam_size=5)
        text = " ".join(seg.text.strip() for seg in segments).strip()
    except Exception as e:
        print(f"CUDA niet beschikbaar ({e}); valt terug op CPU")
        model = WhisperModel("large-v3", device="cpu", compute_type="int8")
        segments, info = model.transcribe(str(OUT_WAV), language="nl", beam_size=5)
        text = " ".join(seg.text.strip() for seg in segments).strip()

    OUT_TXT.write_text(text, encoding="utf-8")
    print(f"Transcript geschreven: {OUT_TXT}")
    print(f"Inhoud: {text}")


if __name__ == "__main__":
    cut_sample()
    transcribe()
