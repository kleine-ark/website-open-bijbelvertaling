"""Genereer audio met XTTS-v2 (voice-cloned vanuit Artlist sample).

Run met .venv-xtts geactiveerd:
    source .venv-xtts/bin/activate
    COQUI_TOS_AGREED=1 python -m scripts.tts.run_xtts --book 1johannes --chapters 1-5
    COQUI_TOS_AGREED=1 python -m scripts.tts.run_xtts --book genesis --chapter 1
"""
from __future__ import annotations
import argparse
import subprocess
import json
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Blackwell patch — MUST be preserved verbatim
# ---------------------------------------------------------------------------

def _patch_torchaudio_for_blackwell() -> None:
    """Patch torchaudio Spectrogram/MelSpectrogram voor RTX 5070 (sm_120 / Blackwell).

    PyTorch cu128 bevat geen nvrtc-kernels voor sm_120, waardoor torchaudio.transforms
    crasht met 'nvrtc: invalid value for --gpu-architecture'. Workaround: spectrogram
    op CPU berekenen en resultaat naar GPU verplaatsen. Overhead is verwaarloosbaar
    (encoder-stap, niet de GPT-inference).
    """
    try:
        import torch
        import torchaudio.transforms as T

        if not torch.cuda.is_available():
            return  # geen GPU, niets te patchen

        cap = torch.cuda.get_device_capability(0)
        if cap < (12, 0):
            return  # niet sm_120+, geen patch nodig

        _orig_spec = T.Spectrogram.forward
        _orig_mel = T.MelSpectrogram.forward

        def _spec_cpu_fallback(self, waveform):  # type: ignore[override]
            dev = waveform.device
            if dev.type == "cuda":
                return _orig_spec(self.to("cpu"), waveform.cpu()).to(dev)
            return _orig_spec(self, waveform)

        def _mel_cpu_fallback(self, waveform):  # type: ignore[override]
            dev = waveform.device
            if dev.type == "cuda":
                return _orig_mel(self.to("cpu"), waveform.cpu()).to(dev)
            return _orig_mel(self, waveform)

        T.Spectrogram.forward = _spec_cpu_fallback  # type: ignore[method-assign]
        T.MelSpectrogram.forward = _mel_cpu_fallback  # type: ignore[method-assign]
        print("Blackwell-patch actief: Spectrogram/MelSpectrogram via CPU proxy.")
    except Exception as exc:
        print(f"Waarschuwing: Blackwell-patch mislukt ({exc}); ga door zonder patch.")


# ---------------------------------------------------------------------------
# Tekst-extractie
# ---------------------------------------------------------------------------

def extract_text(book: str, chapter: int) -> str:
    """Lees text2026 uit data/{book}/{chapter}.json."""
    data_file = Path(f"data/{book}/{chapter}.json")
    if not data_file.exists():
        raise SystemExit(f"Data-bestand ontbreekt: {data_file}")
    data = json.loads(data_file.read_text(encoding="utf-8"))
    return " ".join(v["text2026"].strip() for v in data["verses"] if v.get("text2026"))


# ---------------------------------------------------------------------------
# Argument-parsing
# ---------------------------------------------------------------------------

def _parse_chapters(value: str) -> list[int]:
    """Parseer '1', '1,2,3' of '1-5' naar een lijst integers."""
    if "-" in value and "," not in value:
        start, end = value.split("-", 1)
        return list(range(int(start), int(end) + 1))
    return [int(c.strip()) for c in value.split(",")]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Genereer voorlezing-MP3s met XTTS-v2."
    )
    parser.add_argument("--book", required=True, help="Bijbelboek-ID, bijv. 1johannes of genesis")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--chapter",
        dest="chapters_raw",
        metavar="CHAPTERS",
        help="Hoofdstuknummer(s): '1', '1,2,3' of '1-5'",
    )
    group.add_argument(
        "--chapters",
        dest="chapters_raw",
        metavar="CHAPTERS",
        help="Alias voor --chapter",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overschrijf bestaande MP3s",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Hoofd-logica
# ---------------------------------------------------------------------------

def generate_chapter(
    tts,
    book: str,
    chapter: int,
    sample_wav: Path,
    force: bool,
) -> bool:
    """Genereer audio voor één hoofdstuk. Retourneert True bij succes."""
    out_dir = Path(f"audio/{book}")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_mp3 = out_dir / f"{chapter}.mp3"

    if out_mp3.exists() and not force:
        print(f"  Sla over (bestaat al): {out_mp3}  — gebruik --force om te overschrijven")
        return True

    text = extract_text(book, chapter)
    print(f"  Tekst-lengte: {len(text)} chars")

    out_wav = out_dir / f"{chapter}.wav"
    try:
        tts.tts_to_file(
            text=text,
            speaker_wav=str(sample_wav),
            language="nl",
            file_path=str(out_wav),
            split_sentences=True,
        )

        # WAV → MP3 (128 kbps mono)
        subprocess.run(
            [
                "ffmpeg", "-y", "-i", str(out_wav),
                "-codec:a", "libmp3lame", "-b:a", "128k", "-ac", "1",
                str(out_mp3),
            ],
            check=True,
            capture_output=True,
        )
        out_wav.unlink()
        print(f"  Klaar: {out_mp3}")
        return True
    except Exception as exc:
        print(f"  FOUT bij {book} hfst {chapter}: {exc}", file=sys.stderr)
        if out_wav.exists():
            out_wav.unlink()
        return False


def main() -> None:
    args = parse_args()
    chapters = _parse_chapters(args.chapters_raw)

    sample_wav = Path("audio/_pilot/_sample/sample.wav")
    if not sample_wav.exists():
        raise SystemExit(f"Voice-sample ontbreekt: {sample_wav}. Run eerst Task 2.")

    # Bepaal welke hoofdstukken daadwerkelijk gegenereerd moeten worden
    to_generate = []
    for ch in chapters:
        out_mp3 = Path(f"audio/{args.book}/{ch}.mp3")
        if out_mp3.exists() and not args.force:
            print(f"Sla over (bestaat al): {out_mp3}")
        else:
            to_generate.append(ch)

    if not to_generate:
        print("Alle gevraagde hoofdstukken bestaan al. Klaar.")
        return

    # Model eenmalig laden
    _patch_torchaudio_for_blackwell()
    from TTS.api import TTS  # noqa: PLC0415 — bewust laat importeren (patch eerst)
    print(f"Model laden voor {len(to_generate)} hoofdstuk(ken)…")
    tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2", gpu=True)

    failed: list[int] = []
    for ch in to_generate:
        print(f"\n=== {args.book} / hoofdstuk {ch} ===")
        ok = generate_chapter(tts, args.book, ch, sample_wav, args.force)
        if not ok:
            failed.append(ch)

    if failed:
        print(f"\nMISLUKT voor hoofdstuk(ken): {failed}", file=sys.stderr)
        sys.exit(1)
    else:
        print("\nAlle hoofdstukken succesvol gegenereerd.")


if __name__ == "__main__":
    main()
