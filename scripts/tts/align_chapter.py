#!/usr/bin/env python3
"""Forced-alignment van een hoofdstuk-MP3 → per-vers starttijden.

Gebruikt faster-whisper (word-timestamps) om de voorlezing te transcriberen en
lijnt die uit tegen de bekende verstekst (text2026). Output:
  data/audio-timing/{boek}/{hoofdstuk}-{m|v}.json  =  [{"v":1,"t":0.0}, ...]

De reader (js/app.js) leest dit bestand en zet de versmarkering exact op het vers
dat klinkt. Geen tijdsbestand → geen markering (geen gok).

Gebruik:
  .venv/bin/python scripts/tts/align_chapter.py <boek> <hoofdstuk> <m|v> [model]
Voorbeeld:
  .venv/bin/python scripts/tts/align_chapter.py johannes 1 m small
"""
import json, re, sys, os
from difflib import SequenceMatcher

def strip_html(s):
    s = re.sub(r'<sup[^>]*>.*?</sup>', '', s)
    s = re.sub(r'<[^>]+>', '', s)
    return re.sub(r'\s+', ' ', s).strip()

def norm_word(w):
    return re.sub(r'[^\wà-ÿ]', '', w.lower())

def main():
    book, chap, voice = sys.argv[1], sys.argv[2], sys.argv[3]
    model_size = sys.argv[4] if len(sys.argv) > 4 else "small"
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    data_path = os.path.join(root, "data", book, f"{chap}.json")
    audio_path = os.path.join(root, "audio", book, f"{chap}-{voice}.mp3")
    if not os.path.exists(audio_path):
        print(f"GEEN AUDIO: {audio_path}"); return 2
    d = json.load(open(data_path, encoding="utf-8"))

    # Referentie-woordenlijst met vers-grenzen
    ref = []   # (verse_number, norm_word)
    for v in d["verses"]:
        for w in strip_html(v.get("text2026", "")).split():
            nw = norm_word(w)
            if nw:
                ref.append((v["number"], nw))
    if not ref:
        print("GEEN TEKST"); return 2

    # Transcriptie met woord-timestamps
    from faster_whisper import WhisperModel
    model = WhisperModel(model_size, device="cpu", compute_type="int8")
    segments, _ = model.transcribe(audio_path, language="nl", word_timestamps=True,
                                   vad_filter=True, beam_size=5)
    hyp = []   # (start_time, norm_word)
    for seg in segments:
        for w in (seg.words or []):
            nw = norm_word(w.word)
            if nw:
                hyp.append((float(w.start), nw))
    if not hyp:
        print("GEEN TRANSCRIPTIE"); return 2

    # Uitlijnen referentie ↔ transcriptie
    ref_words = [w for _, w in ref]
    hyp_words = [w for _, w in hyp]
    sm = SequenceMatcher(None, ref_words, hyp_words, autojunk=False)
    ref_time = {}   # ref-index -> starttijd
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == 'equal':
            for k in range(i2 - i1):
                ref_time[i1 + k] = hyp[j1 + k][0]

    # Per vers: starttijd = vroegste bekende tijd van een woord in dat vers
    verse_first_idx = {}
    for idx, (vnum, _) in enumerate(ref):
        verse_first_idx.setdefault(vnum, idx)
    verses_sorted = [v["number"] for v in d["verses"]]

    # bekende tijden per vers (eerste gematchte woord)
    raw = {}
    cur_v = None
    for idx, (vnum, _) in enumerate(ref):
        if idx in ref_time and vnum not in raw:
            raw[vnum] = ref_time[idx]

    # Interpoleer ontbrekende verzen + forceer monotoon stijgend
    out = []
    last_t = 0.0
    for vnum in verses_sorted:
        t = raw.get(vnum)
        if t is None:
            t = last_t            # geen match → neem vorige tijd (markering blijft staan)
        t = max(t, last_t)        # monotoon
        out.append({"v": vnum, "t": round(t, 2)})
        last_t = t

    out_dir = os.path.join(root, "data", "audio-timing", book)
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{chap}-{voice}.json")
    json.dump(out, open(out_path, "w", encoding="utf-8"), ensure_ascii=False)
    matched = len(raw); total = len(verses_sorted)
    print(f"OK {book} {chap}-{voice}: {matched}/{total} verzen gematcht → {out_path}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
