"""Genereer audio met Higgs Audio v3 TTS (voice-cloned vanuit Artlist sample).

Vereisten:
  - .venv-higgs-v3/ is al aangemaakt met sglang-omni + torch 2.9.1+cu130
  - Higgs Audio v3 model: bosonai/higgs-audio-v3-tts-4b (~8 GB HF cache)

Run vanuit de project root:
    python -m scripts.tts.run_higgs_v3

De server wordt automatisch gestart en gestopt.

Architectuurnoten:
  - v3 is NIET afhankelijk van vendor/higgs-audio (dat is v2-code)
  - v3 wordt geserveerd via sglang-omni (OpenAI-compatible /v1/audio/speech API)
  - Voice cloning via ref_audio + ref_text parameters

Blackwell / sm_120 / CUDA-13 situatie:
  - sgl_kernel sm100/common_ops.abi3.so is gecompileerd tegen CUDA 12
  - Fix: LD_LIBRARY_PATH bevat CUDA-12 libs (nvrtc, cublas) uit lokale/Ollama-installatie
  - Torch 2.9.1+cu130 draait prima; alleen sgl_kernel heeft de workaround nodig
"""
from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

# ---------------------------------------------------------------------------
# Constanten
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).parent.parent.parent
VENV = PROJECT_ROOT / ".venv-higgs-v3"

SAMPLE_WAV = PROJECT_ROOT / "audio/_pilot/_sample/sample.wav"
SAMPLE_TXT = PROJECT_ROOT / "audio/_pilot/_sample/sample.txt"

MODEL_ID = "bosonai/higgs-audio-v3-tts-4b"
SERVER_PORT = 8765  # gebruik niet-standaard poort zodat we niet conflicteren

# Chunking: v3 max tokens per call is onbekend, maar we zijn voorzichtig
MAX_CHUNK_WORDS = 80   # ~400–600 chars per chunk; korter = veiliger voor eerste run

CHAPTERS = [
    {
        "book": "genesis",
        "chapter": 1,
        "data_path": "data/genesis/1.json",
        "out_mp3": "audio/_pilot/higgs-v3/genesis-1.mp3",
    },
    {
        "book": "jakobus",
        "chapter": 1,
        "data_path": "data/jakobus/1.json",
        "out_mp3": "audio/_pilot/higgs-v3/jakobus-1.mp3",
    },
]

# ---------------------------------------------------------------------------
# Hulpfuncties
# ---------------------------------------------------------------------------


def _make_env() -> dict[str, str]:
    """Bouw omgevingsvariabelen voor de sgl-omni server en API-calls.

    De sm100/common_ops.abi3.so in sgl_kernel is gecompileerd tegen CUDA 12.
    We voegen CUDA-12-libs toe aan LD_LIBRARY_PATH zodat de .so laadt.
    """
    env = os.environ.copy()

    nvrtc12 = "/home/maarten/.local/lib/python3.12/site-packages/nvidia/cuda_nvrtc/lib"
    cuda12_ollama = "/usr/local/lib/ollama/cuda_v12"

    existing_ld = env.get("LD_LIBRARY_PATH", "")
    parts = [p for p in [nvrtc12, cuda12_ollama, existing_ld] if p]
    env["LD_LIBRARY_PATH"] = ":".join(parts)

    # deep_gemm verwacht een nvcc-binary; cu13/include volstaat als stub
    if "CUDA_HOME" not in env:
        cu13 = str(VENV / "lib/python3.12/site-packages/nvidia/cu13")
        if Path(cu13).is_dir():
            env["CUDA_HOME"] = cu13

    return env


def extract_chapter_text(data_path: str) -> str:
    data = json.loads((PROJECT_ROOT / data_path).read_text(encoding="utf-8"))
    return " ".join(v["text2026"].strip() for v in data["verses"] if v.get("text2026"))


def normalize_text(text: str) -> str:
    lines = text.split("\n")
    text = " ".join(" ".join(line.split()) for line in lines if line.strip())
    text = text.strip()
    if not text.endswith((".", "!", "?", ",", ";", '"', "'")):
        text += "."
    return text


def chunk_text(text: str, max_words: int = MAX_CHUNK_WORDS) -> list[str]:
    words = text.split()
    chunks = []
    for i in range(0, len(words), max_words):
        chunk = " ".join(words[i : i + max_words])
        if not chunk.endswith((".", "!", "?", ",", ";", '"', "'")):
            chunk += "."
        chunks.append(chunk)
    return chunks


# ---------------------------------------------------------------------------
# Server lifecycle
# ---------------------------------------------------------------------------


def start_server() -> subprocess.Popen:
    """Start de sgl-omni server als achtergrondproces.

    Returns het Popen-object. De aanroeper is verantwoordelijk voor cleanup.
    """
    sgl_omni_bin = str(VENV / "bin/sgl-omni")
    cmd = [
        sgl_omni_bin,
        "serve",
        "--model-path", MODEL_ID,
        "--port", str(SERVER_PORT),
        "--host", "127.0.0.1",
        "--model-name", "higgs-audio-v3-tts",
    ]

    env = _make_env()

    print(f"Server starten: {' '.join(cmd)}")
    proc = subprocess.Popen(
        cmd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    return proc


def wait_for_server(proc: subprocess.Popen, timeout: int = 300) -> None:
    """Wacht tot de server klaar is (luistert op poort) of timeout."""
    import socket

    start = time.time()
    print(f"Wachten op server (max {timeout}s)...")

    while time.time() - start < timeout:
        # Check of proces nog leeft
        if proc.poll() is not None:
            # Lees resterende output
            remaining = proc.stdout.read() if proc.stdout else ""
            raise RuntimeError(
                f"Server gestopt met code {proc.returncode}.\n{remaining}"
            )

        # Druk serveroutput af terwijl we wachten
        if proc.stdout:
            line = proc.stdout.readline()
            if line:
                print(f"[server] {line.rstrip()}", flush=True)
                if "Application startup complete" in line or "Uvicorn running" in line:
                    print("Server is klaar.")
                    return

        # Probeer TCP-verbinding
        try:
            with socket.create_connection(("127.0.0.1", SERVER_PORT), timeout=1):
                # Extra wacht zodat de app volledig gestart is
                time.sleep(2)
                print("Server luistert op poort.")
                return
        except (ConnectionRefusedError, OSError):
            pass

        time.sleep(1)

    raise TimeoutError(f"Server niet klaar binnen {timeout}s.")


# ---------------------------------------------------------------------------
# Audio generatie
# ---------------------------------------------------------------------------


def generate_chapter(
    chapter_info: dict,
    ref_audio_path: str,
    ref_text: str,
    *,
    temperature: float = 0.3,
    top_p: float = 0.95,
    seed: int = 42,
) -> None:
    """Genereer één hoofdstuk en sla op als MP3."""
    import requests

    out_mp3 = PROJECT_ROOT / chapter_info["out_mp3"]
    out_mp3.parent.mkdir(parents=True, exist_ok=True)

    raw_text = extract_chapter_text(chapter_info["data_path"])
    text = normalize_text(raw_text)
    print(f"\nHoofdstuk: {chapter_info['book']} {chapter_info['chapter']}")
    print(f"Tekst: {len(text)} chars")

    chunks = chunk_text(text)
    print(f"Chunks: {len(chunks)}")

    url = f"http://127.0.0.1:{SERVER_PORT}/v1/audio/speech"
    headers = {"Content-Type": "application/json"}

    wav_chunks: list[Path] = []
    start_time = time.time()

    for idx, chunk in enumerate(chunks, start=1):
        print(f"  [{idx}/{len(chunks)}] {len(chunk.split())} woorden...", end=" ", flush=True)
        chunk_wav = out_mp3.with_suffix(f".chunk{idx:03d}.wav")

        payload = {
            "model": "higgs-audio-v3-tts",
            "input": chunk,
            "response_format": "wav",
            "ref_audio": ref_audio_path,
            "ref_text": ref_text,
            "temperature": temperature,
            "top_p": top_p,
            "seed": seed,
        }

        t0 = time.time()
        resp = requests.post(url, json=payload, headers=headers, timeout=300)
        resp.raise_for_status()

        chunk_wav.write_bytes(resp.content)
        print(f"ok ({time.time()-t0:.1f}s)", flush=True)
        wav_chunks.append(chunk_wav)

    total_gen = time.time() - start_time

    # Aaneenschakelen met ffmpeg
    print(f"  Aaneenschakelen {len(wav_chunks)} chunks...")
    concat_list = out_mp3.with_suffix(".concat.txt")
    concat_list.write_text(
        "\n".join(f"file '{str(w.absolute())}'" for w in wav_chunks), encoding="utf-8"
    )

    out_wav = out_mp3.with_suffix(".wav")
    subprocess.run(
        ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_list),
         "-c", "copy", str(out_wav)],
        check=True, capture_output=True,
    )

    # WAV → MP3 128k mono
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(out_wav),
         "-codec:a", "libmp3lame", "-b:a", "128k", "-ac", "1",
         str(out_mp3)],
        check=True, capture_output=True,
    )

    # Opruimen
    out_wav.unlink(missing_ok=True)
    concat_list.unlink(missing_ok=True)
    for w in wav_chunks:
        w.unlink(missing_ok=True)

    # Stats
    probe = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format",
         str(out_mp3)],
        capture_output=True, text=True,
    )
    probe_data = json.loads(probe.stdout) if probe.stdout else {}
    duration = float(probe_data.get("format", {}).get("duration", 0))
    size_kb = out_mp3.stat().st_size // 1024

    print(f"  Klaar: {out_mp3}")
    print(f"  Duur: {duration:.1f}s | Grootte: {size_kb} KB | Generatietijd: {total_gen:.1f}s")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    if not SAMPLE_WAV.exists() or not SAMPLE_TXT.exists():
        raise SystemExit(
            f"Voice-sample ontbreekt: {SAMPLE_WAV} of {SAMPLE_TXT}\n"
            "Run eerst prepare_voice_sample.py."
        )

    ref_text = SAMPLE_TXT.read_text(encoding="utf-8").strip()
    ref_audio = str(SAMPLE_WAV.absolute())

    print(f"Voice sample: {SAMPLE_WAV}")
    print(f"Model: {MODEL_ID}")
    print(f"Server poort: {SERVER_PORT}")

    server_proc = None
    try:
        server_proc = start_server()

        # Lees server-output asynchroon terwijl we wachten
        wait_for_server(server_proc, timeout=360)

        for chapter in CHAPTERS:
            generate_chapter(
                chapter,
                ref_audio_path=ref_audio,
                ref_text=ref_text,
            )

    except KeyboardInterrupt:
        print("\nAfgebroken door gebruiker.")
    finally:
        if server_proc and server_proc.poll() is None:
            print("Server stoppen...")
            server_proc.send_signal(signal.SIGTERM)
            try:
                server_proc.wait(timeout=15)
            except subprocess.TimeoutExpired:
                server_proc.kill()

    print("\nKlaar.")


if __name__ == "__main__":
    main()
