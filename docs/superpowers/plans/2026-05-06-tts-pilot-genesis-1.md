# TTS Pilot — Genesis 1 met 3 open-source modellen

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Voor Genesis 1 (text2026, 31 verzen, 4235 chars) drie pilot-MP3's
genereren met XTTS-v2, Higgs Audio v2 en Piper, zodat de gebruiker auditief
kan vergelijken met de bestaande Artlist-versie en kiezen welk model voor
de hele Bijbel uitgerold wordt.

**Architecture:** Eén utility-script `scripts/tts/extract_chapter_text.py`
dat verzen-tekst uit JSON haalt. Drie aparte runner-scripts (één per model),
elk in een eigen venv om dependency-conflicten te vermijden. Voice-sample
en transcript worden eenmalig uit `audio/Genesis 1.mp3` afgeleid en door
XTTS-v2 + Higgs Audio gebruikt voor cloning. Piper gebruikt een vaste NL-
stem.

**Tech Stack:**
- Python 3.12, ffmpeg, faster-whisper (al geïnstalleerd in `.venv`)
- Coqui TTS fork (`coqui-tts`) voor XTTS-v2 in `.venv-xtts`
- Higgs Audio v2 (`boson-ai/higgs-audio`) in `.venv-higgs`
- piper-tts in `.venv-piper`

---

## File Structure

**Nieuwe bestanden:**

| Bestand | Verantwoordelijkheid |
|---|---|
| `scripts/tts/extract_chapter_text.py` | Lees `data/{book}/{ch}.json` → `text2026` verzen joinen tot platte string |
| `scripts/tts/prepare_voice_sample.py` | Knip ~20s schoon fragment uit Artlist Genesis 1, transcribeer met faster-whisper |
| `scripts/tts/run_xtts.py` | Roep XTTS-v2 aan met sample + tekst → MP3 |
| `scripts/tts/run_higgs.py` | Roep Higgs Audio v2 aan met sample + tekst → MP3 |
| `scripts/tts/run_piper.py` | Roep Piper aan met stock NL-stem + tekst → MP3 |
| `tests/tts/test_extract_chapter_text.py` | Unit-test voor de extract-utility |

**Outputs (in `.gitignore`):**
- `audio/_pilot/_sample/sample.wav` — voice-clone-sample (20s, 22050 Hz mono WAV)
- `audio/_pilot/_sample/sample.txt` — transcript van sample
- `audio/_pilot/xtts/genesis-1.mp3`
- `audio/_pilot/higgs/genesis-1.mp3`
- `audio/_pilot/piper/genesis-1.mp3`

---

## Task 1: Text-extractie utility (TDD)

**Files:**
- Create: `scripts/tts/__init__.py` (leeg)
- Create: `scripts/tts/extract_chapter_text.py`
- Create: `tests/tts/__init__.py` (leeg)
- Create: `tests/tts/test_extract_chapter_text.py`

- [ ] **Step 1: Pytest installeren in main venv**

```bash
source .venv/bin/activate
pip install pytest
```

- [ ] **Step 2: Failing test schrijven**

Maak `tests/tts/test_extract_chapter_text.py`:

```python
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
```

- [ ] **Step 3: Run test, verifieer dat het faalt**

```bash
source .venv/bin/activate
pytest tests/tts/test_extract_chapter_text.py -v
```
Expected: `ModuleNotFoundError: No module named 'scripts.tts.extract_chapter_text'`

- [ ] **Step 4: Implementeer extract_chapter_text.py**

Maak `scripts/tts/extract_chapter_text.py`:

```python
"""Extracteer text2026 verzen uit data/{book}/{chapter}.json."""
from __future__ import annotations
import json
from pathlib import Path


def extract_chapter_text(data_dir: Path, book: str, chapter: int) -> str:
    """Lees text2026 van alle verzen in een hoofdstuk en join met spaties.

    Verwacht structuur: data/{book}/{chapter}.json met {"verses": [{"text2026": ...}, ...]}
    """
    path = data_dir / book / f"{chapter}.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    parts = []
    for verse in data["verses"]:
        text = verse.get("text2026", "").strip()
        if text:
            parts.append(text)
    return " ".join(parts)


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        print("Gebruik: python -m scripts.tts.extract_chapter_text <book> <chapter>")
        sys.exit(1)
    book, chapter = sys.argv[1], int(sys.argv[2])
    print(extract_chapter_text(Path("data"), book, chapter))
```

Maak ook lege init-bestanden:

```bash
touch scripts/tts/__init__.py tests/__init__.py tests/tts/__init__.py
```

Voor pytest moet `scripts/__init__.py` ook bestaan:

```bash
touch scripts/__init__.py
```

- [ ] **Step 5: Run test, verifieer dat het slaagt**

```bash
source .venv/bin/activate
pytest tests/tts/test_extract_chapter_text.py -v
```
Expected: 3 passed.

- [ ] **Step 6: Commit**

```bash
git add scripts/__init__.py scripts/tts/__init__.py scripts/tts/extract_chapter_text.py tests/__init__.py tests/tts/__init__.py tests/tts/test_extract_chapter_text.py
git commit -m "feat(tts): tekst-extractie utility voor hoofdstuk-verzen (text2026)"
```

---

## Task 2: Voice-sample voorbereiden uit Artlist Genesis 1

**Files:**
- Create: `scripts/tts/prepare_voice_sample.py`
- Output: `audio/_pilot/_sample/sample.wav` + `sample.txt`

- [ ] **Step 1: Output-map aanmaken**

```bash
mkdir -p audio/_pilot/_sample
```

- [ ] **Step 2: Script schrijven**

Maak `scripts/tts/prepare_voice_sample.py`:

```python
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
    try:
        model = WhisperModel("large-v3", device="cuda", compute_type="float16")
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
```

- [ ] **Step 3: Script draaien**

```bash
source .venv/bin/activate
python -m scripts.tts.prepare_voice_sample
```

Expected:
- Output `audio/_pilot/_sample/sample.wav` (~880 KB voor 20s @ 22050 Hz mono)
- Output `audio/_pilot/_sample/sample.txt` met Nederlandse zin(nen) uit Genesis 1
- Eerste run downloadt het Whisper-model (~3 GB) — duurt 1-2 min

- [ ] **Step 4: Sample-kwaliteit verifiëren**

```bash
ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1 audio/_pilot/_sample/sample.wav
cat audio/_pilot/_sample/sample.txt
```

Expected:
- Duration tussen 19.5 en 20.5 seconden
- Transcript bevat herkenbaar Nederlands (bv. "scheiding", "wateren", "zaad", afhankelijk van waar in Genesis 1 we hebben gesneden)

Als het transcript onzinnig is (bv. random Engels): pas `START_SEC` aan
naar bv. 60 of 120 en herhaal — sommige delen van het audiofragment zijn
mogelijk minder schoon.

- [ ] **Step 5: Commit (script alleen, niet de samples — die staan in `.gitignore`)**

```bash
git add scripts/tts/prepare_voice_sample.py
git commit -m "feat(tts): voice-sample uit Artlist Genesis 1 knippen + transcriberen"
```

---

## Task 3: XTTS-v2 pilot

**Files:**
- Create: `scripts/tts/run_xtts.py`
- Create: `.venv-xtts/` (eigen venv voor XTTS-dependencies)
- Output: `audio/_pilot/xtts/genesis-1.mp3`

- [ ] **Step 1: XTTS venv aanmaken**

```bash
python3 -m venv .venv-xtts
source .venv-xtts/bin/activate
pip install --upgrade pip wheel
pip install coqui-tts
```

Expected: `coqui-tts` installeert succesvol (~2-3 min, trekt torch + dependencies).
Als pip 'TTS' niet vindt of conflicten geeft, alternatief: `pip install git+https://github.com/idiap/coqui-ai-TTS.git`.

- [ ] **Step 2: Script schrijven**

Maak `scripts/tts/run_xtts.py`:

```python
"""Genereer Genesis 1 met XTTS-v2 (voice-cloned vanuit Artlist sample).

Run met .venv-xtts geactiveerd:
    source .venv-xtts/bin/activate
    python -m scripts.tts.run_xtts
"""
from __future__ import annotations
import subprocess
import tempfile
from pathlib import Path

# We importeren niet via "scripts.tts.extract_chapter_text" omdat
# .venv-xtts geen pytest setup heeft — directe file-import.
import json


def extract_genesis_1() -> str:
    data = json.loads(Path("data/genesis/1.json").read_text(encoding="utf-8"))
    return " ".join(v["text2026"].strip() for v in data["verses"] if v.get("text2026"))


def main() -> None:
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
```

- [ ] **Step 3: Script draaien**

```bash
source .venv-xtts/bin/activate
python -m scripts.tts.run_xtts
```

Expected:
- Eerste run: download van xtts_v2 model (~1.8 GB) — duurt 1-3 min
- Generatie: 2-5 min op RTX 5070
- Output: `audio/_pilot/xtts/genesis-1.mp3` (~5 MB)

Als het model XTTS-v2 license-akkoord vraagt op stdin: `COQUI_TOS_AGREED=1` env var zetten:
```bash
COQUI_TOS_AGREED=1 python -m scripts.tts.run_xtts
```

- [ ] **Step 4: Output verifiëren**

```bash
ffprobe -v error -show_entries format=duration,bit_rate -of default=noprint_wrappers=1 audio/_pilot/xtts/genesis-1.mp3
```

Expected:
- duration tussen 240 en 480 seconden (4-8 minuten)
- bit_rate ~128000

Als duration < 60s: model is gestopt halverwege — check console-output voor errors. Vaak helpt `split_sentences=True` (al gezet) of korter chunken.

- [ ] **Step 5: Commit (alleen het script)**

```bash
git add scripts/tts/run_xtts.py
git commit -m "feat(tts): pilot-runner XTTS-v2 voor Genesis 1"
```

---

## Task 4: Higgs Audio v2 pilot

**Files:**
- Create: `scripts/tts/run_higgs.py`
- Create: `.venv-higgs/`
- Output: `audio/_pilot/higgs/genesis-1.mp3`

- [ ] **Step 1: Higgs venv aanmaken en repo clonen**

Higgs Audio v2 is niet als PyPI-package beschikbaar — installeren vanuit de
repo:

```bash
mkdir -p vendor && cd vendor
git clone https://github.com/boson-ai/higgs-audio.git
cd ..
python3 -m venv .venv-higgs
source .venv-higgs/bin/activate
pip install --upgrade pip wheel
pip install -e vendor/higgs-audio
```

Als de install faalt op een specifieke dependency (flash-attn, vllm), check
het README van vendor/higgs-audio en volg hun voorgeschreven volgorde.
Mogelijk is `pip install torch==2.5.1` vooraf nodig.

- [ ] **Step 2: Script schrijven**

Maak `scripts/tts/run_higgs.py`:

```python
"""Genereer Genesis 1 met Higgs Audio v2 (voice-cloned vanuit Artlist sample).

Run met .venv-higgs geactiveerd:
    source .venv-higgs/bin/activate
    python -m scripts.tts.run_higgs
"""
from __future__ import annotations
import json
import subprocess
from pathlib import Path


def extract_genesis_1() -> str:
    data = json.loads(Path("data/genesis/1.json").read_text(encoding="utf-8"))
    return " ".join(v["text2026"].strip() for v in data["verses"] if v.get("text2026"))


def main() -> None:
    from boson_multimodal.serve.serve_engine import HiggsAudioServeEngine
    from boson_multimodal.data_types import ChatMLSample, Message, AudioContent

    sample_wav = Path("audio/_pilot/_sample/sample.wav")
    sample_txt = Path("audio/_pilot/_sample/sample.txt")
    if not sample_wav.exists() or not sample_txt.exists():
        raise SystemExit("Voice-sample of transcript ontbreekt. Run eerst Task 2.")

    reference_text = sample_txt.read_text(encoding="utf-8").strip()
    text = extract_genesis_1()
    print(f"Tekst-lengte: {len(text)} chars")

    engine = HiggsAudioServeEngine(
        model_name_or_path="bosonai/higgs-audio-v2-generation-3B-base",
        audio_tokenizer_name_or_path="bosonai/higgs-audio-v2-tokenizer",
        device="cuda",
    )

    # Voice-clone via reference: spraakvoorbeeld + transcript-tekst.
    messages = [
        Message(
            role="user",
            content=[
                AudioContent(audio_url=str(sample_wav), transcript=reference_text),
            ],
        ),
        Message(role="user", content=text),
    ]
    sample = ChatMLSample(messages=messages)

    out_dir = Path("audio/_pilot/higgs")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_wav = out_dir / "genesis-1.wav"
    out_mp3 = out_dir / "genesis-1.mp3"

    response = engine.generate(chat_ml_sample=sample, max_new_tokens=4096)
    response.save_audio(str(out_wav))

    subprocess.run([
        "ffmpeg", "-y", "-i", str(out_wav),
        "-codec:a", "libmp3lame", "-b:a", "128k", "-ac", "1",
        str(out_mp3),
    ], check=True)
    out_wav.unlink()
    print(f"Klaar: {out_mp3}")


if __name__ == "__main__":
    main()
```

**Let op:** de exacte API-namen van Higgs Audio v2 (`HiggsAudioServeEngine`,
`ChatMLSample`, `Message`, `AudioContent`) zijn gebaseerd op hun publieke
README. Check `vendor/higgs-audio/examples/generation.py` als referentie en
pas import-paden / functienamen aan als de API afwijkt. Hou de structuur
gelijk: 1) sample-clip + transcript meegeven als reference, 2) doel-tekst
genereren, 3) WAV opslaan, 4) ffmpeg → MP3.

- [ ] **Step 3: Script draaien**

```bash
source .venv-higgs/bin/activate
python -m scripts.tts.run_higgs
```

Expected:
- Eerste run: model-download (~6-12 GB) — duurt 5-15 min
- Generatie: 5-15 min op RTX 5070
- Output: `audio/_pilot/higgs/genesis-1.mp3`

Als out-of-memory: probeer model in 8-bit te laden of in chunks van 500-1000
chars te genereren en daarna te concat'en met ffmpeg.

Als de import-paden niet kloppen: check `examples/` in vendor/higgs-audio
en herschrijf script-body op basis van werkend voorbeeld. Dit is de meest
risicovolle stap van de pilot.

- [ ] **Step 4: Output verifiëren**

```bash
ffprobe -v error -show_entries format=duration,bit_rate -of default=noprint_wrappers=1 audio/_pilot/higgs/genesis-1.mp3
```

Expected: duration 240-600s, bit_rate ~128000.

- [ ] **Step 5: Commit**

```bash
git add scripts/tts/run_higgs.py
echo "vendor/" >> .gitignore
git add .gitignore
git commit -m "feat(tts): pilot-runner Higgs Audio v2 voor Genesis 1"
```

---

## Task 5: Piper pilot

**Files:**
- Create: `scripts/tts/run_piper.py`
- Create: `.venv-piper/`
- Output: `audio/_pilot/piper/genesis-1.mp3`

- [ ] **Step 1: Piper venv aanmaken**

```bash
python3 -m venv .venv-piper
source .venv-piper/bin/activate
pip install --upgrade pip wheel
pip install piper-tts
```

- [ ] **Step 2: NL-stem downloaden**

```bash
mkdir -p vendor/piper-voices
cd vendor/piper-voices
# nl_NL-mls-medium: gentle vrouwenstem, hoogste kwaliteit NL in piper
wget -q https://huggingface.co/rhasspy/piper-voices/resolve/main/nl/nl_NL/mls/medium/nl_NL-mls-medium.onnx
wget -q https://huggingface.co/rhasspy/piper-voices/resolve/main/nl/nl_NL/mls/medium/nl_NL-mls-medium.onnx.json
ls -lh nl_NL-mls-medium.*
cd ../..
```

Expected: twee bestanden (`.onnx` ~60 MB, `.onnx.json` paar KB).

- [ ] **Step 3: Script schrijven**

Maak `scripts/tts/run_piper.py`:

```python
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
```

- [ ] **Step 4: Script draaien**

```bash
source .venv-piper/bin/activate
python -m scripts.tts.run_piper
```

Expected:
- Generatie: 10-30 seconden (Piper is razendsnel — CPU-only ONNX)
- Output: `audio/_pilot/piper/genesis-1.mp3`

- [ ] **Step 5: Output verifiëren**

```bash
ffprobe -v error -show_entries format=duration,bit_rate -of default=noprint_wrappers=1 audio/_pilot/piper/genesis-1.mp3
```

Expected: duration 240-360s, bit_rate ~128000.

- [ ] **Step 6: Commit**

```bash
git add scripts/tts/run_piper.py
git commit -m "feat(tts): pilot-runner Piper (nl_NL-mls-medium) voor Genesis 1"
```

---

## Task 6: Audities + beslismoment

- [ ] **Step 1: Bestanden tonen**

```bash
ls -lh audio/Genesis\ 1.mp3 audio/_pilot/xtts/genesis-1.mp3 audio/_pilot/higgs/genesis-1.mp3 audio/_pilot/piper/genesis-1.mp3
```

- [ ] **Step 2: Vraag aan gebruiker**

Stop hier. Stel de gebruiker de volgende vraag:

> Ik heb Genesis 1 gegenereerd met XTTS-v2, Higgs Audio v2 en Piper. De
> bestanden staan in `audio/_pilot/{xtts,higgs,piper}/genesis-1.mp3`,
> naast je referentie `audio/Genesis 1.mp3` (Artlist).
>
> Luister naar alle vier en kies:
>
> A. **XTTS-v2** wint — voldoende kwaliteit, uitrol voor hele Bijbel
> B. **Higgs Audio v2** wint — idem
> C. **Piper** is al goed genoeg — eenvoudigste optie, uitrol
> D. Geen van drieën komt dichtbij Artlist — schakel over op betaalde API
>    (ElevenLabs / Google Chirp HD)
> E. Probeer een ander model (welke?)
>
> Welke wordt het?

Wacht op het antwoord. **Niet** zelf doorgaan met productie-rollout —
daarvoor wordt een nieuw plan geschreven op basis van deze keuze.

---

## Self-Review Notes

- **Spec-coverage:** Alle pilot-onderdelen uit het design-doc gedekt
  (3 modellen, voice-cloning sample, Genesis 1 als testcase, output-paden,
  beslismoment). Productie-rollout (alle hoofdstukken) is bewust buiten dit
  plan gehouden — komt na de keuze in een vervolg-plan.
- **Geen placeholders:** alle code is concreet, alle commands zijn
  draaibaar. Enige risicogebied: Higgs Audio v2 API-namen — daar staat
  expliciet "verifieer in vendor README" als instructie.
- **Type-consistentie:** `extract_chapter_text(data_dir, book, chapter)`
  signature consistent in test en implementatie. `extract_genesis_1()` is
  in elke runner een lokale duplicaat (DRY-bewust gekozen — runners draaien
  in aparte venvs en kunnen niet elkaars modules importeren).
- **Bekende onzekerheid:** Higgs Audio installatiestappen kunnen afwijken;
  flash-attn-compatibiliteit met RTX 5070 (sm_120) moet bij eerste run
  blijken. Als dat blokkeert: noteren in commit-message en doorgaan met de
  andere twee modellen. De pilot kan met 2 van de 3 modellen ook valide
  beslissen.
