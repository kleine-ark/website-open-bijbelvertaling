#!/usr/bin/env python3
"""Genereer data/stats.json — de ENIGE bron voor alle aantallen op de site.

Draai dit na elke inhoudelijke wijziging (nieuwe nagelezen boeken, principes,
diffs). Alle pagina's lezen via js/stats-inject.js uit data/stats.json, zodat
er nooit verschillende aantallen op verschillende pagina's staan.

Gebruik:  python3 scripts/build_stats.py [versie] [datum]
"""
import json, os, re, sys, datetime

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

    ch_total = verses_total = ch_ver = verses_ver = books_full = diff_total = diff_via_principe = 0
    verified_books = []   # weergavelabels van (deels) nagekeken boeken, in canonieke volgorde
    by_test = {'OT': [0, 0], 'NT': [0, 0], 'AP': [0, 0]}   # testament -> [verzen_totaal, verzen_nagekeken]
    for b in books:
        bid = b['id']; chs = b.get('chaptersIncluded', [])
        test = b.get('testament')
        ch_total += len(chs)
        v = verified.get(bid)
        full = v == 'all' or (isinstance(v, list) and len(chs) > 0 and len(v) >= len(chs))
        if full:
            books_full += 1
            verified_books.append(b['nameDutch'])
        elif isinstance(v, list) and len(v) > 0:
            # gedeeltelijk nagekeken → naam + hoofdstukbereik (bv. "Genesis 1–20")
            verified_books.append(f"{b['nameDutch']} {min(v)}–{max(v)}")
        for ch in chs:
            fp = os.path.join(DATA, bid, f'{ch}.json')
            if not os.path.exists(fp):
                continue
            d = json.load(open(fp, encoding='utf-8'))
            vs = [x for x in d.get('verses', []) if isinstance(x, dict)]
            verses_total += len(vs)
            if test in by_test:
                by_test[test][0] += len(vs)
            verified_ch = v == 'all' or (isinstance(v, list) and ch in v)
            if verified_ch:
                ch_ver += 1; verses_ver += len(vs)
                if test in by_test:
                    by_test[test][1] += len(vs)
            for x in vs:
                pds = x.get('phraseDiff') or []
                # Tel het AANTAL GEWIJZIGDE WOORDEN t.o.v. SV1888 (niet het aantal
                # diff-segmenten): per segment het maximum van oud/nieuw aantal woorden.
                for pd in pds:
                    nw = max(len(str(pd.get('old', '')).split()),
                             len(str(pd.get('new', '')).split())) or 1
                    diff_total += nw
                    if pd.get('principe'):
                        diff_via_principe += nw

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
        'changes_via_principe': diff_via_principe,
        'changes_via_principe_pct': pct(diff_via_principe, diff_total),
        'changes_los': diff_total - diff_via_principe,
        'verified_books': verified_books,
        'ot_verses_total': by_test['OT'][0],
        'ot_verses_verified': by_test['OT'][1],
        'ot_verses_verified_pct': pct(by_test['OT'][1], by_test['OT'][0]),
        'nt_verses_total': by_test['NT'][0],
        'nt_verses_verified': by_test['NT'][1],
        'nt_verses_verified_pct': pct(by_test['NT'][1], by_test['NT'][0]),
        'ap_verses_total': by_test['AP'][0],
        'ap_verses_verified': by_test['AP'][1],
        'ap_verses_verified_pct': pct(by_test['AP'][1], by_test['AP'][0]),
    }

    # === Nakijksnelheid + verwachte einddatum (zelf-bijwerkend) ===
    # data/review-history.json houdt per datum het aantal nagekeken verzen bij.
    # Elke build voegt de stand van vandaag toe; de snelheid is de lineaire trend
    # (kleinste-kwadraten) over de hele historie, de ETA de projectie naar 100%.
    NL_M = ['', 'januari', 'februari', 'maart', 'april', 'mei', 'juni', 'juli',
            'augustus', 'september', 'oktober', 'november', 'december']
    hist_fp = os.path.join(DATA, 'review-history.json')
    try:
        hist = json.load(open(hist_fp, encoding='utf-8'))
    except Exception:
        hist = {}
    today = datetime.date.today()
    hist[today.isoformat()] = verses_ver
    json.dump(hist, open(hist_fp, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    open(hist_fp, 'a', encoding='utf-8').write('\n')

    pts = sorted((datetime.date.fromisoformat(d), v) for d, v in hist.items())
    if len(pts) >= 2:
        x0 = pts[0][0].toordinal()
        xs = [p[0].toordinal() - x0 for p in pts]
        ys = [p[1] for p in pts]
        n = len(xs); sx = sum(xs); sy = sum(ys)
        sxx = sum(x * x for x in xs); sxy = sum(x * y for x, y in zip(xs, ys))
        denom = n * sxx - sx * sx
        slope = (n * sxy - sx * sy) / denom if denom else 0.0   # verzen/dag
        remaining = verses_total - verses_ver
        stats['review_verses_per_day'] = round(slope, 1)
        stats['review_verses_per_week'] = round(slope * 7)
        stats['review_remaining_verses'] = remaining
        stats['review_since'] = f"{pts[0][0].day} {NL_M[pts[0][0].month]} {pts[0][0].year}"
        if slope > 0:
            eta = today + datetime.timedelta(days=remaining / slope)
            stats['review_eta'] = f"{eta.day} {NL_M[eta.month]} {eta.year}"
            stats['review_eta_month'] = f"{NL_M[eta.month]} {eta.year}"
        else:
            stats['review_eta'] = stats['review_eta_month'] = 'onbekend'

    out = os.path.join(DATA, 'stats.json')
    json.dump(stats, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    open(out, 'a', encoding='utf-8').write('\n')
    print('stats.json geschreven:')
    print(json.dumps(stats, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
