#!/usr/bin/env python3
"""Verouderingscheck voor de voorlees-audio.

Vergelijkt per hoofdstuk de tekst met de bijbehorende audio en meldt welke
hoofdstukken opnieuw gegenereerd moeten worden. Zie
docs/superpowers/specs/2026-07-15-chunked-audio-design.md.

Bepaling "verouderd" (in volgorde):
  1. Chunk-manifest aanwezig (audio/<book>/<ch>/<voice>/manifest.json)
     -> verouderd als manifest.textHash != huidige textHash.
  2. Anders (losse MP3 audio/<book>/<ch>-<voice>.mp3):
     -> verouderd als de tekst-JSON in git nieuwer is dan de MP3 (mtime),
        of als de MP3 ontbreekt.

textHash = sha1 van de aaneengeschakelde text2026 van alle verzen (+ kopjes indien
beschikbaar), exact de tekst die voorgelezen zou worden.

Gebruik:
  python3 scripts/audio_staleness.py            # samenvatting + verouderde lijst
  python3 scripts/audio_staleness.py --json out.json
"""
import json, os, sys, hashlib, subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VOICES = ['m', 'v']


def text_hash(book, ch):
    fn = os.path.join(ROOT, 'data', book, f'{ch}.json')
    if not os.path.exists(fn):
        return None
    d = json.load(open(fn, encoding='utf-8'))
    parts = []
    for v in d.get('verses', []):
        t = (v.get('text2026') or '').strip()
        if t:
            parts.append(t)
    # kopjes (pericopen) meenemen indien beschikbaar; structuur defensief afhandelen
    try:
        bookper = PERICOPEN.get(book) if isinstance(PERICOPEN, dict) else None
        per = bookper.get(str(ch)) if isinstance(bookper, dict) else None
        if isinstance(per, list):
            for h in per:
                parts.append(h.get('titel', '') if isinstance(h, dict) else str(h))
    except Exception:
        pass
    return hashlib.sha1('\n'.join(parts).encode('utf-8')).hexdigest()


def git_mtime_iso(relpath):
    try:
        out = subprocess.run(['git', 'log', '-1', '--format=%ct', '--', relpath],
                             cwd=ROOT, capture_output=True, text=True, timeout=20)
        s = out.stdout.strip()
        return int(s) if s else None
    except Exception:
        return None


def file_mtime(path):
    try:
        return int(os.path.getmtime(path))
    except OSError:
        return None


def load_pericopen():
    fn = os.path.join(ROOT, 'data', 'pericopen.json')
    if not os.path.exists(fn):
        return {}
    try:
        return json.load(open(fn, encoding='utf-8'))
    except Exception:
        return {}


PERICOPEN = load_pericopen()


def load_audio_available():
    """Lees window.AUDIO_AVAILABLE uit js/audio-available.js via node."""
    js = os.path.join(ROOT, 'js', 'audio-available.js')
    try:
        out = subprocess.run(
            ['node', '-e',
             f"global.window={{}};require({json.dumps(js)});"
             "process.stdout.write(JSON.stringify(window.AUDIO_AVAILABLE||{}))"],
            capture_output=True, text=True, timeout=20)
        return json.loads(out.stdout)
    except Exception as e:
        print("Kon AUDIO_AVAILABLE niet laden:", e, file=sys.stderr)
        return {}


def main():
    audio_avail = load_audio_available()
    stale = []
    missing = []
    ok = 0
    total = 0
    for book, chapters in sorted(audio_avail.items()):
        for ch in chapters:
            total += 1
            th = text_hash(book, ch)
            if th is None:
                continue
            data_rel = f'data/{book}/{ch}.json'
            reason = None
            # 1) chunk-manifest?
            man_path = os.path.join(ROOT, 'audio', book, str(ch), 'm', 'manifest.json')
            if os.path.exists(man_path):
                try:
                    man = json.load(open(man_path, encoding='utf-8'))
                    if man.get('textHash') != th:
                        reason = 'manifest-textHash-verschilt'
                except Exception:
                    reason = 'manifest-onleesbaar'
            else:
                # 2) losse MP3
                mp3 = os.path.join(ROOT, 'audio', book, f'{ch}-m.mp3')
                if not os.path.exists(mp3):
                    missing.append((book, ch))
                    continue
                text_dt = git_mtime_iso(data_rel)
                audio_dt = file_mtime(mp3)
                if text_dt and audio_dt and text_dt > audio_dt:
                    reason = 'tekst-nieuwer-dan-audio'
            if reason:
                stale.append({'book': book, 'chapter': ch, 'reason': reason, 'textHash': th})
            else:
                ok += 1

    print(f"Hoofdstukken met audio: {total}")
    print(f"  actueel:    {ok}")
    print(f"  verouderd:  {len(stale)}")
    print(f"  ontbrekend: {len(missing)}")
    if stale:
        print("\nVEROUDERD (opnieuw genereren):")
        for s in stale:
            print(f"  {s['book']} {s['chapter']}  [{s['reason']}]")
    if missing:
        print("\nONTBREKENDE MP3 (in AUDIO_AVAILABLE maar geen bestand):")
        for b, c in missing:
            print(f"  {b} {c}")

    if '--json' in sys.argv:
        out = sys.argv[sys.argv.index('--json') + 1]
        json.dump({'stale': stale, 'missing': missing, 'ok': ok, 'total': total},
                  open(out, 'w'), ensure_ascii=False, indent=1)
        print(f"\nRapport geschreven naar {out}")


if __name__ == '__main__':
    main()
