#!/usr/bin/env python3
"""Genereer data/stats.json — de ENIGE bron voor alle aantallen op de site.

Draai dit na elke inhoudelijke wijziging (nieuwe nagelezen boeken, principes,
diffs). Alle pagina's lezen via js/stats-inject.js uit data/stats.json, zodat
er nooit verschillende aantallen op verschillende pagina's staan.

Gebruik:  python3 scripts/build_stats.py [versie] [datum]
"""
import json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'data')
SKIP = {'speech-v2', 'speech', 'audio', 'tts'}

def parse_verified():
    appjs = open(os.path.join(ROOT, 'js', 'app.js'), encoding='utf-8').read()
    m = re.search(r'VERIFIED_CHAPTERS:\s*\{(.*?)\n    \},', appjs, re.S)
    block = m.group(1)
    verified = {}
    for line in block.splitlines():
        lm = re.match(r"\s*'?([a-z0-9]+)'?\s*:\s*(.+?),?\s*$", line)
        if not lm:
            continue
        key, val = lm.group(1), lm.group(2).strip().rstrip(',')
        if "'all'" in val:
            verified[key] = 'all'
        elif val.startswith('['):
            verified[key] = [int(n) for n in re.findall(r'\d+', val)]
    return verified

def main():
    version = sys.argv[1] if len(sys.argv) > 1 else 'v0.17.0'
    datum = sys.argv[2] if len(sys.argv) > 2 else '7 juni 2026'

    books = json.load(open(os.path.join(DATA, 'books.json'), encoding='utf-8'))['books']
    verified = parse_verified()

    ch_total = verses_total = ch_ver = verses_ver = books_full = diff_total = 0
    for b in books:
        bid = b['id']; chs = b.get('chaptersIncluded', [])
        ch_total += len(chs)
        v = verified.get(bid)
        full = v == 'all' or (isinstance(v, list) and len(chs) > 0 and len(v) >= len(chs))
        if full:
            books_full += 1
        for ch in chs:
            fp = os.path.join(DATA, bid, f'{ch}.json')
            if not os.path.exists(fp):
                continue
            d = json.load(open(fp, encoding='utf-8'))
            vs = [x for x in d.get('verses', []) if isinstance(x, dict)]
            verses_total += len(vs)
            if v == 'all' or (isinstance(v, list) and ch in v):
                ch_ver += 1; verses_ver += len(vs)
            for x in vs:
                diff_total += len(x.get('phraseDiff') or [])

    principes = len(json.load(open(os.path.join(DATA, 'wijzigingsprincipes.json'), encoding='utf-8'))['principes'])

    def pct(a, b):
        return round(100 * a / b, 1) if b else 0

    stats = {
        'version': version,
        'date': datum,
        'books_total': len(books),
        'books_verified': books_full,
        'chapters_total': ch_total,
        'chapters_verified': ch_ver,
        'chapters_verified_pct': pct(ch_ver, ch_total),
        'verses_total': verses_total,
        'verses_verified': verses_ver,
        'verses_verified_pct': pct(verses_ver, verses_total),
        'principes': principes,
        'text_changes': diff_total,
    }
    out = os.path.join(DATA, 'stats.json')
    json.dump(stats, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    open(out, 'a', encoding='utf-8').write('\n')
    print('stats.json geschreven:')
    print(json.dumps(stats, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
