"""Genereer Genesis 1 met XTTS-v2 (voice-cloned vanuit Artlist sample).

Run met .venv-xtts geactiveerd:
    source .venv-xtts/bin/activate
    python -m scripts.tts.run_xtts
"""
from __future__ import annotations
import subprocess
import json
from pathlib import Path


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


def extract_genesis_1() -> str:
    data = json.loads(Path("data/genesis/1.json").read_text(encoding="utf-8"))
    return " ".join(v["text2026"].strip() for v in data["verses"] if v.get("text2026"))


def main() -> None:
    _patch_torchaudio_for_blackwell()

    from TTS.api import TTS

    sample_wav = Path("audio/_pilot/_sample/sample.wav")
    if not sample_wav.exists():
        raise SystemExit(f"Voice-sample ontbreekt: {sample_wav}. Run eerst Task 2.")

    text = extract_genesis_1()
    print(f"Tekst-lengte: {len(text)} chars")

    out_dir = Path("audio/_pilot/xtts")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_wav = out_dir / "genesis-1.wav"
    out_mp3 = out_dir / "genesis-1.mp3"

    tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2", gpu=True)
    tts.tts_to_file(
        text=text,
        speaker_wav=str(sample_wav),
        language="nl",
        file_path=str(out_wav),
        split_sentences=True,
    )

    # WAV → MP3 (128 kbps mono) om te matchen met Artlist baseline
    subprocess.run([
        "ffmpeg", "-y", "-i", str(out_wav),
        "-codec:a", "libmp3lame", "-b:a", "128k", "-ac", "1",
        str(out_mp3),
    ], check=True)
    out_wav.unlink()  # Tussenbestand opruimen
    print(f"Klaar: {out_mp3}")


if __name__ == "__main__":
    main()
