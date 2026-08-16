#!/usr/bin/env python3
"""Publiceer gecontroleerde TR-koppelingen voor Markus 10."""
from __future__ import annotations
import argparse,json
from pathlib import Path
from rebuild_johannes2_tr_strongs import mapping,r
from rebuild_nt_tr_strongs import load_tr_chapter
ROOT=Path(__file__).resolve().parents[1]
C=(25,13,9,10,15,11,16,14,8,13,15,11,13,26,18,10,20,16,20,12,33,13,20,30,17,11,21,13,32,30,9,31,25,17,18,9,21,23,24,17,10,22,17,10,19,26,17,15,17,11,18,21)
def build(u:Path,o:Path,w=False):
 s=load_tr_chapter(u,o,chapter=10,osis_book='Mark');p=ROOT/'data'/'markus'/'10.json';d=json.loads(p.read_text(encoding='utf8'));review={'book':'markus','chapter':10,'reviewed_through':52,'verses':{}}
 for v,count in zip(d['verses'],C):
  n=int(v['number']);ts=s[n];ids=r(0,count-1);a=v['text2026']
  if len(ts)!=count:raise ValueError(n)
  v['grondtekst']=[{'woord':t['woord'],'strongs':t['display_strong'],'lemma_strongs':t['lemma_strong'],'morfologie':t['morphology']} for t in ts];v['woordnummers']=[mapping(a,ids,ts,n)];v['woordnummers'][0]['herkomst']['referentie']=f'MRK 10:{n}';review['verses'][str(n)]=[{'tekst':a,'bronindices':ids,'reviewstatus':'handmatig_gecontroleerd'}]
 if w:
  p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf8');(ROOT/'data'/'woordnummers-review'/'markus-10.json').write_text(json.dumps(review,ensure_ascii=False,indent=2)+'\n',encoding='utf8');ip=ROOT/'data'/'woordnummers-inline'/'markus.json';i=json.loads(ip.read_text(encoding='utf8'));i['chapters']['10']={str(v['number']):v['woordnummers'] for v in d['verses']};ip.write_text(json.dumps(i,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 return {'verses':52,'tokens':sum(C)}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--utr',type=Path,required=True);p.add_argument('--osis',type=Path,required=True);p.add_argument('--write',action='store_true');a=p.parse_args();print(json.dumps(build(a.utr,a.osis,a.write),indent=2))
