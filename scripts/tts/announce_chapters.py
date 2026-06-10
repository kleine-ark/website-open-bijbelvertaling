"""Genereer korte 'Hoofdstuk N'-aankondigingsclips met DEZELFDE Higgs-v3-stem
als de voorlezing, voor het automatisch doorspelen in de webspeler.

Output: audio/_announce/{voice}/{n}.mp3   (voice = 'm' of 'v')

De webspeler (js/app.js -> _announceThenPlay) speelt audio/_announce/{voice}/{n}.mp3
af vóór het volgende hoofdstuk; ontbreekt de clip, dan valt hij terug op browser-spraak.

Draai vanuit de project root, in dezelfde omgeving als run_higgs_v3, met de
voice-clone-referentie die ook voor die stem gebruikt is:

    # vrouwenstem
    python -m scripts.tts.announce_chapters --voice v --sample audio/_pilot/_sample/sample-v --max 150
    # mannenstem
    python -m scripts.tts.announce_chapters --voice m --sample audio/_pilot/_sample/sample-m --max 150

(--sample = basispad zonder extensie; gebruikt {sample}.wav + {sample}.txt, net als run_higgs_v3.)
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from scripts.tts.run_higgs_v3 import (  # hergebruik de server-machinerie
    PROJECT_ROOT, SERVER_PORT, start_server, wait_for_server,
)


def synth_phrase(text: str, ref_audio: str, ref_text: str, out_mp3: Path,
                 *, temperature: float = 0.3, top_p: float = 0.95, seed: int = 42) -> None:
    import requests
    out_mp3.parent.mkdir(parents=True, exist_ok=True)
    wav = out_mp3.with_suffix(".tmp.wav")
    payload = {
        "model": "higgs-audio-v3-tts",
        "input": text,
        "response_format": "wav",
        "ref_audio": ref_audio,
        "ref_text": ref_text,
        "temperature": temperature,
        "top_p": top_p,
        "seed": seed,
    }
    resp = requests.post(f"http://127.0.0.1:{SERVER_PORT}/v1/audio/speech",
                         json=payload, headers={"Content-Type": "application/json"}, timeout=120)
    resp.raise_for_status()
    wav.write_bytes(resp.content)
    # wav -> mp3 (zelfde codec-keuze als de voorlezing)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(wav),
                    "-codec:a", "libmp3lame", "-q:a", "4", str(out_mp3)], check=True)
    wav.unlink(missing_ok=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--voice", required=True, choices=["m", "v"], help="stem-suffix m/v")
    ap.add_argument("--sample", default=None,
                    help="basispad voice-clone-referentie (zonder extensie); {sample}.wav + {sample}.txt. "
                         "Default: audio/_pilot/_sample/voice-male (m) of voice-female (v).")
    ap.add_argument("--max", type=int, default=150, help="hoogste hoofdstuknummer (Psalmen = 150)")
    ap.add_argument("--min", type=int, default=1)
    ap.add_argument("--overwrite", action="store_true", help="bestaande clips opnieuw genereren")
    args = ap.parse_args()

    sample = args.sample or ("audio/_pilot/_sample/voice-male" if args.voice == "m"
                             else "audio/_pilot/_sample/voice-female")
    ref_wav = PROJECT_ROOT / f"{sample}.wav"
    ref_txt = PROJECT_ROOT / f"{sample}.txt"
    if not ref_wav.exists() or not ref_txt.exists():
        sys.exit(f"Referentie ontbreekt: {ref_wav} / {ref_txt}")
    ref_text = ref_txt.read_text(encoding="utf-8").strip()

    out_dir = PROJECT_ROOT / f"audio/_announce/{args.voice}"
    todo = [n for n in range(args.min, args.max + 1)
            if args.overwrite or not (out_dir / f"{n}.mp3").exists()]
    if not todo:
        print("Niets te doen — alle clips bestaan al.")
        return
    print(f"Te genereren: {len(todo)} clips ({args.voice}) → {out_dir}")

    proc = start_server()
    try:
        wait_for_server(proc)
        for n in todo:
            out = out_dir / f"{n}.mp3"
            t0 = time.time()
            synth_phrase(f"Hoofdstuk {n}.", str(ref_wav), ref_text, out)
            print(f"  Hoofdstuk {n} -> {out.name}  ({time.time()-t0:.1f}s)", flush=True)
    finally:
        try:
            proc.terminate(); proc.wait(timeout=15)
        except Exception:
            proc.kill()
    print("Klaar.")


if __name__ == "__main__":
    main()
