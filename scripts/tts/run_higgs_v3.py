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

Blackwell / sm_120 / CUDA-13 situatie (RTX 5070, CUDA 13.0 driver):
  sgl_kernel:
    - sm100/common_ops.abi3.so is gecompileerd tegen CUDA 12
    - Fix: LD_LIBRARY_PATH bevat CUDA-12 libs (nvrtc, cublas) uit lokale/Ollama-installatie

  flashinfer JIT-compilatie:
    - ninja in venv/bin (niet op systeem-PATH) — fix: venv/bin op PATH van server-env
    - nvcc 13.3.33 via pip install nvidia-cuda-nvcc
    - CCCL headers 13.3 vs CUDART_VERSION 13.0 → mismatch check → fix: FLASHINFER_EXTRA_CUDAFLAGS
    - linker zoekt libcudart in lib64/, maar de .so staat in lib/ → fix: FLASHINFER_EXTRA_LDFLAGS
    - libcudart.so symlink aanmaken in nvidia/cu13/lib/ (libcudart.so → libcudart.so.13)

  Overig:
    - nvidia-cuda-cccl installeren (geeft nv/target header die ontbrak)
    - qwen-vl-utils installeren (sglang_omni dependency)
"""
from __future__ import annotations

import json
import os
import re
import signal
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from scripts.tts.pronunciation import apply_lexicon, load_lexicon

# ---------------------------------------------------------------------------
# Constanten
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).parent.parent.parent
VENV = PROJECT_ROOT / ".venv-higgs-v3"

SAMPLE_WAV = PROJECT_ROOT / "audio/_pilot/_sample/sample.wav"
SAMPLE_TXT = PROJECT_ROOT / "audio/_pilot/_sample/sample.txt"

MODEL_ID = "bosonai/higgs-audio-v3-tts-4b"
SERVER_PORT = 8765  # gebruik niet-standaard poort zodat we niet conflicteren

# Uitspraak-lexicon eenmalig laden (woord -> herspelling voor betere klemtoon)
LEXICON = load_lexicon()

# Chunking: kleiner = vaker een zinsgrens = vaker een pauze tussen zinnen.
MAX_CHUNK_WORDS = 40
# Stilte (ms) die tussen opeenvolgende chunks wordt geplakt → pauze tussen zinnen.
PAUSE_MS = 500

def _parse_chapters(value: str) -> list[int]:
    """Parseer '1', '1,2,3' of '1-5' naar een lijst integers."""
    if "-" in value and "," not in value:
        start, end = value.split("-", 1)
        return list(range(int(start), int(end) + 1))
    return [int(c.strip()) for c in value.split(",")]


def build_chapter_jobs(
    book: str,
    chapters: list[int],
    pilot: bool,
    voice: str = "",
    label: str = "",
) -> list[dict]:
    """Bouw chapter-job dicts voor de gegeven hoofdstukken.

    pilot=True schrijft naar audio/_pilot/higgs-v3/{book}-{ch}[-label].mp3,
    anders naar de productie-locatie audio/{book}/{ch}[-voice].mp3.

    voice = stem-suffix voor productie ('m' of 'v'); label = vrije suffix
    voor pilot-vergelijkingen.
    """
    jobs = []
    for ch in chapters:
        if pilot:
            suffix = f"-{label}" if label else ""
            out = f"audio/_pilot/higgs-v3/{book}-{ch}{suffix}.mp3"
        else:
            suffix = f"-{voice}" if voice else ""
            out = f"audio/{book}/{ch}{suffix}.mp3"
        jobs.append({
            "book": book,
            "chapter": ch,
            "data_path": f"data/{book}/{ch}.json",
            "out_mp3": out,
        })
    return jobs

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

    # flashinfer JIT-compileert CUDA-kernels via ninja; ninja zit in venv/bin
    # nvcc zit in nvidia/cu13/bin (geïnstalleerd via nvidia-cuda-nvcc package)
    venv_bin = str(VENV / "bin")
    nvcc_bin = str(VENV / "lib/python3.12/site-packages/nvidia/cu13/bin")
    existing_path = env.get("PATH", "")
    path_parts = [p for p in [venv_bin, nvcc_bin, existing_path] if p]
    env["PATH"] = ":".join(path_parts)

    # nvcc 13.3 vs CUDART headers 13.0 versie-mismatch: CCCL-check uitschakelen.
    # FLASHINFER_EXTRA_CUDAFLAGS wordt door flashinfer toegevoegd aan nvcc-aanroepen.
    if "FLASHINFER_EXTRA_CUDAFLAGS" not in env:
        env["FLASHINFER_EXTRA_CUDAFLAGS"] = "-DCCCL_DISABLE_CTK_COMPATIBILITY_CHECK"

    # flashinfer linkt tegen -lcudart maar zoekt in cu13/lib64 terwijl de .so
    # in cu13/lib staat. FLASHINFER_EXTRA_LDFLAGS voegt de juiste lib-dir toe.
    cu13_lib = str(VENV / "lib/python3.12/site-packages/nvidia/cu13/lib")
    if "FLASHINFER_EXTRA_LDFLAGS" not in env:
        env["FLASHINFER_EXTRA_LDFLAGS"] = f"-L{cu13_lib}"
    else:
        env["FLASHINFER_EXTRA_LDFLAGS"] += f" -L{cu13_lib}"

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


_SENT_SPLIT = re.compile(r"(?<=[.!?])\s+")


def chunk_text(text: str, max_words: int = MAX_CHUNK_WORDS) -> list[str]:
    """Splits in chunks die ALTIJD op een zinsgrens eindigen.

    Zinnen worden gegroepeerd tot ~max_words; we breken nooit middenin een zin.
    Hierdoor valt elke chunk-grens (waar we straks stilte tussen plakken) samen
    met een zinseinde → natuurlijke, langere pauzes tussen zinnen.
    Een enkele zin langer dan max_words wordt alsnog op woorden gehakt (zeldzaam).
    """
    sentences = [s.strip() for s in _SENT_SPLIT.split(text.strip()) if s.strip()]
    chunks: list[str] = []
    cur: list[str] = []
    cur_words = 0
    for sent in sentences:
        n = len(sent.split())
        if n > max_words and not cur:
            # losse zin te lang → op woorden hakken
            w = sent.split()
            for i in range(0, len(w), max_words):
                chunks.append(" ".join(w[i : i + max_words]))
            continue
        if cur_words + n > max_words and cur:
            chunks.append(" ".join(cur))
            cur, cur_words = [], 0
        cur.append(sent)
        cur_words += n
    if cur:
        chunks.append(" ".join(cur))
    # garandeer eind-leesteken per chunk
    out = []
    for c in chunks:
        if not c.endswith((".", "!", "?", ",", ";", '"', "'")):
            c += "."
        out.append(c)
    return out


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
    # Uitspraak-lexicon toepassen op de TTS-input (raakt de site-tekst niet)
    raw_text = apply_lexicon(raw_text, LEXICON)
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
        # 120s ruim voldoende voor één chunk van 80 woorden (~10-30s gezond);
        # korter = vastgelopen server wordt sneller gedetecteerd door de supervisor.
        resp = requests.post(url, json=payload, headers=headers, timeout=120)
        resp.raise_for_status()

        chunk_wav.write_bytes(resp.content)
        print(f"ok ({time.time()-t0:.1f}s)", flush=True)
        wav_chunks.append(chunk_wav)

    total_gen = time.time() - start_time

    # Aaneenschakelen met ffmpeg, met stilte tussen de chunks (pauze tussen zinnen)
    print(f"  Aaneenschakelen {len(wav_chunks)} chunks (pauze {PAUSE_MS}ms)...")
    silence_wav = out_mp3.with_suffix(".silence.wav")
    if PAUSE_MS > 0 and wav_chunks:
        # Stilte in exact hetzelfde formaat als de chunks (anders faalt -c copy)
        probe = subprocess.run(
            ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_streams",
             str(wav_chunks[0])],
            capture_output=True, text=True,
        )
        st = (json.loads(probe.stdout).get("streams", [{}])[0]) if probe.stdout else {}
        sr = st.get("sample_rate", "24000")
        ch = st.get("channels", 1)
        codec = st.get("codec_name", "pcm_s16le")
        subprocess.run(
            ["ffmpeg", "-y", "-f", "lavfi",
             "-i", f"anullsrc=r={sr}:cl={'mono' if ch == 1 else 'stereo'}",
             "-t", f"{PAUSE_MS / 1000:.3f}", "-c:a", codec, str(silence_wav)],
            check=True, capture_output=True,
        )

    concat_list = out_mp3.with_suffix(".concat.txt")
    lines = []
    for idx, w in enumerate(wav_chunks):
        lines.append(f"file '{str(w.absolute())}'")
        if PAUSE_MS > 0 and idx < len(wav_chunks) - 1 and silence_wav.exists():
            lines.append(f"file '{str(silence_wav.absolute())}'")
    concat_list.write_text("\n".join(lines), encoding="utf-8")

    out_wav = out_mp3.with_suffix(".wav")
    subprocess.run(
        ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_list),
         "-c", "copy", str(out_wav)],
        check=True, capture_output=True,
    )
    silence_wav.unlink(missing_ok=True)

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


def _parse_args() -> "argparse.Namespace":
    import argparse

    p = argparse.ArgumentParser(description="Higgs Audio v3 TTS — hoofdstuk-rollout.")
    p.add_argument("--book", help="Boek-id, bijv. genesis of 1johannes")
    p.add_argument("--chapters", help="Hoofdstukken: '1', '1,2,3' of '1-5'")
    p.add_argument("--pilot", action="store_true",
                   help="Schrijf naar audio/_pilot/higgs-v3/ i.p.v. productie")
    p.add_argument("--force", action="store_true",
                   help="Overschrijf bestaande MP3's (default: skip)")
    p.add_argument("--sample", default="audio/_pilot/_sample/sample",
                   help="Basispad van voice-clone-referentie (zonder extensie); "
                        "gebruikt {sample}.wav + {sample}.txt")
    p.add_argument("--voice", default="",
                   help="Stem-suffix voor productie-output: 'm' of 'v' "
                        "→ audio/{book}/{ch}-{voice}.mp3")
    p.add_argument("--label", default="",
                   help="Vrije suffix voor pilot-output (vergelijkingen)")
    p.add_argument("--temperature", type=float, default=0.3,
                   help="Generatie-temperature; hoger = meer intonatie/variatie "
                        "(default 0.3)")
    p.add_argument("--manifest",
                   help="JSON-bestand [{book, chapters:[...]}] — verwerk veel "
                        "boeken in één server-sessie (voor grote rollout)")
    return p.parse_args()


def main() -> None:
    args = _parse_args()

    sample_wav = PROJECT_ROOT / f"{args.sample}.wav"
    sample_txt = PROJECT_ROOT / f"{args.sample}.txt"
    if not sample_wav.exists() or not sample_txt.exists():
        raise SystemExit(
            f"Voice-sample ontbreekt: {sample_wav} of {sample_txt}\n"
            "Run eerst prepare_voice_sample.py of geef --sample <basispad>."
        )

    if args.manifest:
        # Manifest = JSON-lijst [{"book":..., "chapters":[...]}, ...]
        # Eén server-sessie verwerkt alle boeken (efficiënt voor grote rollout).
        manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
        jobs = []
        for entry in manifest:
            jobs += build_chapter_jobs(
                entry["book"], entry["chapters"], pilot=args.pilot,
                voice=args.voice, label=args.label,
            )
    elif args.book and args.chapters:
        chapters = _parse_chapters(args.chapters)
        jobs = build_chapter_jobs(
            args.book, chapters, pilot=args.pilot,
            voice=args.voice, label=args.label,
        )
    else:
        # Geen args → pilot-default (Genesis 1 + Jakobus 1)
        jobs = (
            build_chapter_jobs("genesis", [1], pilot=True)
            + build_chapter_jobs("jakobus", [1], pilot=True)
        )

    # Idempotent: bestaande output overslaan tenzij --force
    todo = []
    for job in jobs:
        out = PROJECT_ROOT / job["out_mp3"]
        if out.exists() and not args.force:
            print(f"Sla over (bestaat al): {job['out_mp3']}")
        else:
            todo.append(job)

    if not todo:
        print("Alle gevraagde hoofdstukken bestaan al. Klaar.")
        return

    ref_text = sample_txt.read_text(encoding="utf-8").strip()
    ref_audio = str(sample_wav.absolute())

    print(f"Voice sample: {sample_wav}")
    print(f"Model: {MODEL_ID}")
    print(f"Server poort: {SERVER_PORT}")
    print(f"Te genereren: {len(todo)} hoofdstuk(ken)")

    server_proc = None
    failed: list[str] = []
    try:
        server_proc = start_server()

        # Lees server-output asynchroon terwijl we wachten
        wait_for_server(server_proc, timeout=360)

        for chapter in todo:
            try:
                generate_chapter(
                    chapter,
                    ref_audio_path=ref_audio,
                    ref_text=ref_text,
                    temperature=args.temperature,
                )
            except Exception as exc:  # noqa: BLE001 — laat één hoofdstuk de run niet killen
                label = f"{chapter['book']} {chapter['chapter']}"
                print(f"  FOUT bij {label}: {exc}", file=sys.stderr)
                failed.append(label)

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

    if failed:
        print(f"\nMISLUKT voor: {failed}", file=sys.stderr)
        sys.exit(1)
    print("\nKlaar.")


if __name__ == "__main__":
    main()
