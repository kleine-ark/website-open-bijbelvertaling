#!/usr/bin/env python3
"""Verwerk de menselijke tekst- en citaatreview van Esther."""
from __future__ import annotations
import json, re, sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from sweep_principe import kaal, lees, nieuwe_diff, schrijf
from synchroniseer_opmaak import bijtrekken
from apply_citations_2koningen import markeer, zonder_spraak

CORRECTIES = {
 (1,6): [("behangselen", "bekleding")],
 (2,3): [("toezieners", "opzichters")],
 (2,7): [("die opvoedde Hadassa", "die Hadassa opvoedde")],
 (2,12): [("naakte", "naderde")], (2,15): [("naakte", "naderde")],
 (3,5): [("zich niet neigde", "niet knielde")],
 (4,8): [("geschrevene wet", "geschreven wet")],
 (9,27): [("het niet overtrade", "het niet zou overtreden")],
 (10,3): [("zijn hele zaad", "zijn hele nageslacht")],
}

# Alleen werkelijk uitgesproken/geciteerde woorden; vertelling blijft erbuiten.
CITATEN = {
 (1,10): [], (1,11): [("mens","Dat zij Vasthi","schoon van aangezicht.")], (1,13): [],
 (2,4): [("mens","En het meisje","in stede van Vasthi.")], (2,10): [], (2,20): [], (2,22): [],
 (3,2): [],
 (4,4): [], (4,5): [], (4,8): [], (4,10): [], (4,12): [], (4,15): [],
 (5,5): [("mens","Doe Haman spoeden","van Esther doe.")],
 (5,14): [("mens","Men make een galg","tot die maaltijd.")],
 (6,2): [],
 (6,3): [("mens","Wat eer en verhoging","hierover gedaan?"),("mens","Aan hem is niets gedaan.","Aan hem is niets gedaan.")],
 (6,4): [("mens","Wie is in het voorhof?","Wie is in het voorhof?")],
 (6,5): [("mens","Zie, Haman staat","in het voorhof."),("mens","Dat hij inkome.","Dat hij inkome.")],
 (6,11): [("mens","Zo zal men","welbehagen heeft!")], (6,12): [],
 (7,6): [("mens","De man, de onderdrukker","slechte Haman!")],
 (7,8): [("mens","Zou hij ook wel","in het huis?")],
 (8,3): [],
}

def norm(s): return re.sub(r"\s+", " ", s.strip().lower())

def principes():
 p = ROOT/'data'/'wijzigingsprincipes.json'; data=json.loads(p.read_text(encoding='utf8'))
 data['principes']=[x for x in data['principes'] if not x.get('id','').startswith('MR-EST-')]
 ids={}; n=1
 for (c,v), pairs in sorted(CORRECTIES.items()):
  for oud,nieuw in pairs:
   pid=f'MR-EST-{n:03d}'; n+=1; ids[(norm(oud),norm(nieuw))]=pid
   data['principes'].append({'id':pid,'categorie':'Menselijke review','oud':oud,'nieuw':nieuw,
    'toelichting':'Contextueel beoordeeld tijdens de menselijke review van Esther.','regex':'',
    'voorbeeld':f'Esther {c}:{v}','bereik':{'esther':[f'{c}:{v}']},'bron':'menselijke-review'})
 p.write_text(json.dumps(data,ensure_ascii=False,indent=1)+'\n',encoding='utf8'); return ids

def main():
 ids=principes(); per=defaultdict(list)
 for (c,v),pairs in CORRECTIES.items(): per[c].append((v,pairs))
 for c, rows in per.items():
  pad=ROOT/'data'/'esther'/f'{c}.json'; data,vorm=lees(str(pad)); by={x['number']:x for x in data['verses']}
  for v,pairs in rows:
   item=by[v]; original=item['text2026']; text=original
   for oud,nieuw in pairs:
    pat=re.compile(rf'(?<!\w){re.escape(oud)}(?!\w)')
    if pat.search(text): text=pat.sub(nieuw,text)
    elif not re.search(rf'(?<!\w){re.escape(nieuw)}(?!\w)',text): raise ValueError(f'Esther {c}:{v}: {oud}')
   if text != original:
    item['text2026']=text; html=bijtrekken(item['text2026_html'],text)
    if html is None or kaal(html)!=kaal(text): raise ValueError(f'HTML Esther {c}:{v}')
    item['text2026_html']=html; item['phraseDiff']=nieuwe_diff(kaal(item['textSV1888']),kaal(text),item.get('phraseDiff',[]),None,f'esther {c}:{v}')
   for oud,nieuw in pairs:
    pid=ids[(norm(oud),norm(nieuw))]; diffs=item.setdefault('phraseDiff',[])
    if not any(d.get('principe')==pid for d in diffs):
     d=next((d for d in diffs if norm(nieuw) in norm(d.get('new','')) and not d.get('principe')),None)
     if d is None: d={'old':oud,'new':nieuw}; diffs.append(d)
     d['principe']=pid
  schrijf(str(pad),data,vorm)
 per=defaultdict(dict)
 for (c,v),ranges in CITATEN.items(): per[c][v]=ranges
 for c, rows in per.items():
  pad=ROOT/'data'/'esther'/f'{c}.json'; data,vorm=lees(str(pad))
  for item in data['verses']:
   if item['number'] not in rows: continue
   old=item['text2026_html']; base=zonder_spraak(old); new=markeer(base,rows[item['number']]) if rows[item['number']] else base
   if kaal(old)!=kaal(new): raise ValueError(f'Citaat Esther {c}:{item["number"]}')
   item['text2026_html']=new
  schrijf(str(pad),data,vorm)

if __name__=='__main__': main()
