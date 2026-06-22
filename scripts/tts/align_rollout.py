#!/usr/bin/env python3
"""Bulk forced-alignment over alle voorgelezen hoofdstukken.

Laadt het whisper-model ÉÉN keer en verwerkt elk hoofdstuk uit window.AUDIO_AVAILABLE
(beide stemmen m/v) waarvoor nog geen tijdsbestand bestaat. Output per hoofdstuk:
  data/audio-timing/{boek}/{hoofdstuk}-{m|v}.json  =  [{"v":n,"t":sec}, ...]

Idempotent/hervatbaar: bestaande tijdsbestanden worden overgeslagen.

Gebruik:
  .venv/bin/python scripts/tts/align_rollout.py [model] [boek1 boek2 ...]
  (zonder boeken = alle boeken uit AUDIO_AVAILABLE)
"""
import json, re, sys, os
from difflib import SequenceMatcher

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def strip_html(s):
    s = re.sub(r'<sup[^>]*>.*?</sup>', '', s)
    s = re.sub(r'<[^>]+>', '', s)
    return re.sub(r'\s+', ' ', s).strip()

def norm_word(w):
    return re.sub(r'[^\wà-ÿ]', '', w.lower())

def load_audio_available():
    txt = open(os.path.join(ROOT, "js", "audio-available.js"), encoding="utf-8").read()
    m = re.search(r'window\.AUDIO_AVAILABLE\s*=\s*(\{.*?\});', txt, re.S)
    raw = m.group(1)
    raw = re.sub(r"'", '"', raw)
    raw = re.sub(r',(\s*[}\]])', r'\1', raw)   # trailing commas weg
    return json.loads(raw)

def align_one(model, book, chap, voice):
    data_path = os.path.join(ROOT, "data", book, f"{chap}.json")
    audio_path = os.path.join(ROOT, "audio", book, f"{chap}-{voice}.mp3")
    if not (os.path.exists(data_path) and os.path.exists(audio_path)):
        return None
    d = json.load(open(data_path, encoding="utf-8"))
    ref = []
    for v in d["verses"]:
        for w in strip_html(v.get("text2026", "")).split():
            nw = norm_word(w)
            if nw:
                ref.append((v["number"], nw))
    if not ref:
        return None
    segments, _ = model.transcribe(audio_path, language="nl", word_timestamps=True,
                                   vad_filter=True, beam_size=5)
    hyp = []
    for seg in segments:
        for w in (seg.words or []):
            nw = norm_word(w.word)
            if nw:
                hyp.append((float(w.start), nw))
    if not hyp:
        return None
    sm = SequenceMatcher(None, [w for _, w in ref], [w for _, w in hyp], autojunk=False)
    ref_time = {}
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == 'equal':
            for k in range(i2 - i1):
                ref_time[i1 + k] = hyp[j1 + k][0]
    raw = {}
    for idx, (vnum, _) in enumerate(ref):
        if idx in ref_time and vnum not in raw:
            raw[vnum] = ref_time[idx]
    out, last_t = [], 0.0
    for v in d["verses"]:
        t = raw.get(v["number"], last_t)
        t = max(t, last_t)
        out.append({"v": v["number"], "t": round(t, 2)})
        last_t = t
    out_dir = os.path.join(ROOT, "data", "audio-timing", book)
    os.makedirs(out_dir, exist_ok=True)
    json.dump(out, open(os.path.join(out_dir, f"{chap}-{voice}.json"), "w", encoding="utf-8"),
              ensure_ascii=False)
    return len(raw), len(d["verses"])

def main():
    model_size = sys.argv[1] if len(sys.argv) > 1 else "small"
    only_books = set(sys.argv[2:]) if len(sys.argv) > 2 else None
    avail = load_audio_available()
    from faster_whisper import WhisperModel
    model = WhisperModel(model_size, device="cpu", compute_type="int8")
    done = skipped = failed = 0
    for book in sorted(avail):
        if only_books and book not in only_books:
            continue
        for chap in avail[book]:
            for voice in ("m", "v"):
                out_path = os.path.join(ROOT, "data", "audio-timing", book, f"{chap}-{voice}.json")
                if os.path.exists(out_path):
                    skipped += 1
                    continue
                try:
                    r = align_one(model, book, str(chap), voice)
                    if r:
                        done += 1
                        print(f"OK {book} {chap}-{voice}: {r[0]}/{r[1]}", flush=True)
                    else:
                        failed += 1
                except Exception as e:
                    failed += 1
                    print(f"FAIL {book} {chap}-{voice}: {e}", flush=True)
    print(f"KLAAR: {done} nieuw, {skipped} overgeslagen, {failed} mislukt", flush=True)

if __name__ == "__main__":
    main()
