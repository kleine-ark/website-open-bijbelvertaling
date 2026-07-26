#!/usr/bin/env python3
"""Bereken per bijbelvers het oudste bewaarde handschrift (origineel + überhaupt).
Uitvoer: data/verse-witnesses.json. Herbruikbaar; ranges mogen per boek (dict) of globaal (list)."""
import json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
d = json.load(open(os.path.join(ROOT, 'data/manuscripts.json'), encoding='utf-8'))
M, B = d['manuscripten'], d['boeken']
books = json.load(open(os.path.join(ROOT, 'data/books.json'), encoding='utf-8'))
tc = {b['id']: b.get('totalChapters', 0) for b in books.get('books', [])}

OT = set("genesis exodus leviticus numeri deuteronomium jozua richteren ruth 1samuel 2samuel 1koningen 2koningen 1kronieken 2kronieken ezra nehemia esther job psalmen spreuken prediker hooglied jesaja jeremia klaagliederen ezechiel daniel hosea joel amos obadja jona micha nahum habakuk zefanja haggai zacharia maleachi".split())
NT = set("mattheus markus lukas johannes handelingen romeinen 1korinthiers 2korinthiers galaten efeziers filippenzen kolossenzen 1tessalonicensen 2tessalonicensen 1timotheus 2timotheus titus filemon hebreeen jakobus 1petrus 2petrus 1johannes 2johannes 3johannes judas openbaring".split())
ETH = set("henoch jubileeen 4baruch 1meqabyan 2meqabyan 3meqabyan".split())

def origlangs(b):
    if b in OT: return {'he', 'arc'}
    if b in NT: return {'grc'}
    if b == '4ezra': return {'la'}
    if b in ('henoch', 'jubileeen'): return {'he', 'gez'}
    if b in ETH: return {'gez'}
    return {'grc'}

yr = lambda m: M[m].get('jaar', 3000)
naam = lambda m: M[m]['naam']

def ranges_for(mid, book):
    r = M[mid].get('ranges')
    if not r: return None
    if isinstance(r, dict): return r.get(book)
    return r

def maxverse(book, ch):
    try:
        dd = json.load(open(os.path.join(ROOT, f'data/{book}/{ch}.json'), encoding='utf-8'))
        return max((v.get('number', 0) for v in dd.get('verses', []) if isinstance(v, dict)), default=0)
    except Exception:
        return 0

def is_whole(book, rngs):
    if not rngs or len(rngs) != 1: return False
    c1, v1, c2, v2 = rngs[0]
    return c1 == 1 and v1 == 1 and c2 >= tc.get(book, 999)

out = {}
for bid, bk in B.items():
    vol = [m for m in bk.get('volledig', []) if m in M]
    frags = [m for m in bk.get('fragmenten', []) if m in M]
    ol = origlangs(bid)
    whole_frag, exc_frag = [], []
    for f in frags:
        rr = ranges_for(f, bid)
        if not rr: continue                     # fragment zonder ranges voor dit boek: niet per-vers toe te wijzen
        (whole_frag if is_whole(bid, rr) else exc_frag).append(f)
    whole = vol + whole_frag or vol[:]
    oc = [m for m in whole if M[m].get('taal') in ol]
    def_orig = min(oc, key=yr) if oc else (min(whole, key=yr) if whole else None)
    alle = [(yr(m), m, naam(m)) for m in whole]
    if bid in OT:
        lxx = ('alexandrinus', 420, 'Codex Alexandrinus (Septuaginta)') if bid == 'genesis' else ('vaticanus', 340, 'Codex Vaticanus (Septuaginta)')
        alle.append((lxx[1], lxx[0], lxx[2]))
    da = min(alle) if alle else None
    entry = {"origineel": {"ms": def_orig, "jaar": yr(def_orig), "naam": naam(def_orig)} if def_orig else None,
             "alle": {"ms": da[1], "jaar": da[0], "naam": da[2]} if da else None, "uitzonderingen": {}}
    for rf in exc_frag:
        rj, rt, rn = yr(rf), M[rf].get('taal'), naam(rf)
        for c1, v1, c2, v2 in ranges_for(rf, bid):
            for ch in range(c1, c2 + 1):
                mv = maxverse(bid, ch) or v2
                lo = v1 if ch == c1 else 1
                hi = v2 if ch == c2 else mv
                for v in range(lo, min(hi, mv if mv else hi) + 1):
                    key = f"{ch}:{v}"; ex = entry["uitzonderingen"].get(key, {})
                    if rt in ol and (not entry["origineel"] or rj < entry["origineel"]["jaar"]):
                        if 'origineel' not in ex or rj < ex['origineel']['jaar']: ex['origineel'] = {"ms": rf, "jaar": rj, "naam": rn}
                    if (not entry["alle"]) or rj < entry["alle"]["jaar"]:
                        if 'alle' not in ex or rj < ex['alle']['jaar']: ex['alle'] = {"ms": rf, "jaar": rj, "naam": rn}
                    if ex: entry["uitzonderingen"][key] = ex
    out[bid] = entry

res = {"_bron": "Berekend uit data/manuscripts.json. 'origineel'=oudste handschrift in de oorspronkelijke taal (Hebreeuws/Grieks); 'alle'=oudste überhaupt incl. Septuaginta. Volledige codices dekken het hele boek; Dode Zee-rollen/papyri/fragmenten dekken specifieke verzen (uitzonderingen). Datering bij benadering.",
       "boeken": out}
json.dump(res, open(os.path.join(ROOT, 'data/verse-witnesses.json'), 'w'), ensure_ascii=False)
print("bestand:", round(os.path.getsize(os.path.join(ROOT, 'data/verse-witnesses.json')) / 1024, 1), "KB")
for b in ['romeinen', 'hebreeen', '1korinthiers', 'johannes', 'lukas', 'genesis', 'jesaja']:
    e = out[b]; print(f"{b}: orig={e['origineel']['naam']}({e['origineel']['jaar']}) uitz={len(e['uitzonderingen'])}")
