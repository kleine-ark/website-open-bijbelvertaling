"""Chunked-audio generator voor de Open Staten Vertaling.

Genereert per (boek, hoofdstuk, stem) losse segmenten + manifest.json volgens
docs/superpowers/specs/2026-07-15-chunked-audio-design.md, zodat de speler
optioneel de godsnaam (Heere/Jahweh/Jehova), kopjes en boek-intro kan schakelen.

Output: audio/<book>/<ch>/<voice>/{intro.opus, h<v>.opus, v<N>.opus,
        v<N>__<optie>.opus, manifest.json}

Draaien (met Higgs-v3 venv-env, zoals run_higgs_v3):
    PYTHONDONTWRITEBYTECODE=1 <env> .venv-higgs-v3/bin/python \
        -m scripts.tts.generate_chunks --book genesis --chapters 2 --voice m
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import signal
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from scripts.tts import run_higgs_v3 as H  # server-lifecycle hergebruiken
from scripts.tts.pronunciation import apply_lexicon, load_lexicon

PROJECT_ROOT = H.PROJECT_ROOT
LEXICON = load_lexicon()
MODEL_ID = "higgs-audio-v3"
DIVINE_RE = re.compile(r"\bJAHWEH\b")  # Godsnaam-token in text2026

# De vier Godsnaam-opties matchen js/opties.js (state.godsnaam):
#   ov (JAHWEH) · klassiek (de HEERE) · jehovah (Jehovah) · jhwh (יהוה → "de Naam")
# Per optie de gesproken tekst afleiden met dezelfde transformaties als de app,
# maar met leesbare hoofdletters (Heere i.p.v. HEERE) zodat de TTS niet spelt.
_KLASSIEK_RULES = [
    (re.compile(r"\bGod JAHWEH\b"), "de Heere God"),
    (re.compile(r"\bJAHWEH van de legermachten\b"), "de Heere der heirscharen"),
    (re.compile(r"\b(op|van|aan|voor|tot|door|in|met|bij|over|onder|naast|achter|jegens|uit|na|sinds) JAHWEH\b", re.I), r"\1 de Heere"),
    (re.compile(r"\b([Oo]) JAHWEH\b"), r"\1 Heere"),
    (re.compile(r"\bJAHWEH!"), "Heere!"),
    (re.compile(r"(^|[.!?]\s+)JAHWEH\b"), r"\1De Heere"),
    (re.compile(r"\bJAHWEH\b"), "de Heere"),
    (re.compile(r"\bde de Heere\b"), "de Heere"),
    (re.compile(r"\bDe de Heere\b"), "De Heere"),
]


def _klassiek(text: str) -> str:
    for rgx, repl in _KLASSIEK_RULES:
        text = rgx.sub(repl, text)
    return text


def godsnaam_variants(raw: str) -> dict[str, str]:
    """Gesproken tekst per Godsnaam-optie (canonieke app-sleutels)."""
    return {
        "ov": raw,                                       # JAHWEH → lexicon "Jaawee"
        "klassiek": _klassiek(raw),                      # de Heere (contextueel)
        "jehovah": re.sub(r"\bGod JAHWEH\b", "God Jehovah", raw).replace("JAHWEH", "Jehovah"),
        "jhwh": re.sub(r"\bGod JAHWEH\b", "God de Naam", raw).replace("JAHWEH", "de Naam"),
    }

# Aliassen zodat de huidige speler (sleutels heere/jahweh/jehova) blijft werken.
_ALIAS = {"heere": "klassiek", "jahweh": "ov", "jehova": "jehovah"}


def load_json(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))


def text_hash(book: str, ch: int) -> str:
    """Identiek aan scripts/audio_staleness.py::text_hash (verzen-only)."""
    d = load_json(PROJECT_ROOT / "data" / book / f"{ch}.json")
    parts = [(v.get("text2026") or "").strip() for v in d["verses"]]
    parts = [p for p in parts if p]
    return hashlib.sha1("\n".join(parts).encode("utf-8")).hexdigest()


def book_name(book: str) -> str:
    for b in load_json(PROJECT_ROOT / "data" / "books.json")["books"]:
        if b["id"] == book:
            return b.get("nameDutch") or book
    return book


def headings_for(book: str, ch: int) -> dict[int, str]:
    """{afterVerse: titel} voor dit hoofdstuk uit data/pericopen.json."""
    try:
        per = load_json(PROJECT_ROOT / "data" / "pericopen.json").get(book, [])
    except Exception:
        return {}
    return {h["v"]: h["t"] for h in per if isinstance(h, dict) and h.get("c") == ch}


OPUS_BITRATE = "32k"  # spraak-transparant, ~4x kleiner dan 128k MP3


def synth(text: str, out_opus: Path, ref_audio: str, ref_text: str,
          temperature: float = 0.8) -> float:
    """Synthetiseer één segment → Opus (mono). Retourneer duur in sec."""
    import requests

    tts_text = apply_lexicon(text, LEXICON)
    url = f"http://127.0.0.1:{H.SERVER_PORT}/v1/audio/speech"
    payload = {
        "model": "higgs-audio-v3-tts", "input": tts_text, "response_format": "wav",
        "ref_audio": ref_audio, "ref_text": ref_text,
        "temperature": temperature, "top_p": 0.95, "seed": 42,
    }
    resp = requests.post(url, json=payload, headers={"Content-Type": "application/json"},
                         timeout=120)
    resp.raise_for_status()
    wav = out_opus.with_suffix(".wav")
    wav.write_bytes(resp.content)
    subprocess.run(["ffmpeg", "-y", "-i", str(wav), "-c:a", "libopus",
                    "-b:a", OPUS_BITRATE, "-ac", "1", str(out_opus)],
                   check=True, capture_output=True)
    wav.unlink(missing_ok=True)
    probe = subprocess.run(["ffprobe", "-v", "quiet", "-print_format", "json",
                            "-show_format", str(out_opus)], capture_output=True, text=True)
    dur = float(json.loads(probe.stdout).get("format", {}).get("duration", 0))
    return round(dur, 2)


def generate_chapter(book: str, ch: int, voice: str, ref_audio: str, ref_text: str,
                     force: bool = False) -> None:
    data = load_json(PROJECT_ROOT / "data" / book / f"{ch}.json")
    outdir = PROJECT_ROOT / "audio" / book / str(ch) / voice
    manifest_path = outdir / "manifest.json"
    th = text_hash(book, ch)

    if manifest_path.exists() and not force:
        try:
            if load_json(manifest_path).get("textHash") == th:
                print(f"  overslaan (up-to-date): {book} {ch} {voice}")
                return
        except Exception:
            pass

    outdir.mkdir(parents=True, exist_ok=True)
    heads = headings_for(book, ch)
    segments = []
    print(f"\n=== {book} {ch} stem {voice} ({len(data['verses'])} verzen) ===")

    # 1. intro
    intro_txt = f"Het boek {book_name(book)}, hoofdstuk {ch}."
    dur = synth(intro_txt, outdir / "intro.opus", ref_audio, ref_text)
    segments.append({"type": "intro", "file": "intro.opus", "dur": dur})
    print(f"  intro ({dur}s)")

    # 2. verzen (kopje ervoor indien aanwezig)
    for v in data["verses"]:
        n = v["number"]
        raw = (v.get("text2026") or "").strip()
        if not raw:
            continue
        if n in heads:
            htext = heads[n]
            hdur = synth(htext, outdir / f"h{n}.opus", ref_audio, ref_text)
            segments.append({"type": "heading", "afterVerse": n,
                             "file": f"h{n}.opus", "dur": hdur, "text": htext})
            print(f"  h{n} kopje ({hdur}s)")

        if DIVINE_RE.search(raw):
            variants, durs = {}, {}
            for key, vtext in godsnaam_variants(raw).items():
                f = f"v{n}__{key}.opus"
                durs[key] = synth(vtext, outdir / f, ref_audio, ref_text)
                variants[key] = f
            # aliassen (heere/jahweh/jehova) → dezelfde bestanden voor huidige speler
            for alias, canon in _ALIAS.items():
                variants[alias] = variants[canon]
                durs[alias] = durs[canon]
            segments.append({"type": "verse", "verse": n, "divineName": True,
                             "variants": variants, "dur": durs})
            print(f"  v{n} (godsnaam) ov={durs['ov']} klassiek={durs['klassiek']} jehovah={durs['jehovah']} jhwh={durs['jhwh']}")
        else:
            f = f"v{n}.opus"
            d = synth(raw, outdir / f, ref_audio, ref_text)
            segments.append({"type": "verse", "verse": n, "file": f,
                             "dur": d, "divineName": False})
            print(f"  v{n} ({d}s)")

    manifest = {
        "book": book, "chapter": ch, "voice": voice, "model": MODEL_ID,
        "generatedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "textHash": th, "segments": segments,
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2),
                             encoding="utf-8")
    print(f"  manifest.json ({len(segments)} segmenten)")


def parse_chapters(value: str) -> list[int]:
    if "-" in value and "," not in value:
        a, b = value.split("-", 1)
        return list(range(int(a), int(b) + 1))
    return [int(c) for c in value.split(",")]


def _all_chapters(book: str) -> list[int]:
    import glob, os
    chs = [int(os.path.basename(f)[:-5])
           for f in glob.glob(str(PROJECT_ROOT / "data" / book / "[0-9]*.json"))
           if os.path.basename(f)[:-5].isdigit()]
    return sorted(chs)


def main() -> None:
    ap = argparse.ArgumentParser(description="Chunked-audio generator (Higgs v3).")
    ap.add_argument("--book", help="Eén boek-id")
    ap.add_argument("--books", help="Komma-lijst boek-ids (alle hoofdstukken); "
                                    "één server-sessie voor meerdere boeken")
    ap.add_argument("--chapters", help="'2', '1,2' of '1-5' (alleen met --book)")
    ap.add_argument("--voice", required=True, choices=["m", "v"])
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    sample = "voice-male" if args.voice == "m" else "voice-female"
    ref_audio = str((PROJECT_ROOT / "audio/_pilot/_sample" / f"{sample}.wav").absolute())
    ref_text = (PROJECT_ROOT / "audio/_pilot/_sample" / f"{sample}.txt").read_text(encoding="utf-8").strip()

    # Bouw (boek, hoofdstuk)-job-lijst
    jobs: list[tuple[str, int]] = []
    if args.books:
        for b in args.books.split(","):
            b = b.strip()
            jobs += [(b, ch) for ch in _all_chapters(b)]
    elif args.book and args.chapters:
        jobs = [(args.book, ch) for ch in parse_chapters(args.chapters)]
    else:
        ap.error("geef --book+--chapters of --books")

    server = None
    try:
        server = H.start_server()
        H.wait_for_server(server, timeout=360)
        for book, ch in jobs:
            generate_chapter(book, ch, args.voice, ref_audio, ref_text, args.force)
    finally:
        if server and server.poll() is None:
            server.send_signal(signal.SIGTERM)
            try:
                server.wait(timeout=15)
            except subprocess.TimeoutExpired:
                server.kill()
    print("\nKlaar.")


if __name__ == "__main__":
    main()
