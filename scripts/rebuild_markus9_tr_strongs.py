#!/usr/bin/env python3
"""Publiceer gecontroleerde TR-koppelingen voor Markus 9."""
from __future__ import annotations
import argparse,json
from pathlib import Path
from rebuild_johannes2_tr_strongs import mapping,r
from rebuild_nt_tr_strongs import load_tr_chapter
ROOT=Path(__file__).resolve().parents[1]
COUNTS=(27,28,18,11,25,8,21,12,23,13,13,24,16,14,12,8,17,27,21,20,16,22,13,16,31,16,11,18,16,13,26,9,18,12,19,13,25,25,22,9,23,28,31,11,31,11,29,11,9,21)
def build(u:Path,o:Path,w=False):
 s=load_tr_chapter(u,o,chapter=9,osis_book='Mark');p=ROOT/'data'/'markus'/'9.json';d=json.loads(p.read_text(encoding='utf8'));review={'book':'markus','chapter':9,'reviewed_through':50,'verses':{}}
 for v,count in zip(d['verses'],COUNTS):
  n=int(v['number']);ts=s[n];ids=r(0,count-1);a=v['text2026']
  if len(ts)!=count:raise ValueError(n)
  v['grondtekst']=[{'woord':t['woord'],'strongs':t['display_strong'],'lemma_strongs':t['lemma_strong'],'morfologie':t['morphology']} for t in ts];v['woordnummers']=[mapping(a,ids,ts,n)];v['woordnummers'][0]['herkomst']['referentie']=f'MRK 9:{n}';review['verses'][str(n)]=[{'tekst':a,'bronindices':ids,'reviewstatus':'handmatig_gecontroleerd'}]
 if w:
  p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf8');(ROOT/'data'/'woordnummers-review'/'markus-9.json').write_text(json.dumps(review,ensure_ascii=False,indent=2)+'\n',encoding='utf8');ip=ROOT/'data'/'woordnummers-inline'/'markus.json';i=json.loads(ip.read_text(encoding='utf8'));i['chapters']['9']={str(v['number']):v['woordnummers'] for v in d['verses']};ip.write_text(json.dumps(i,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 return {'verses':50,'tokens':sum(COUNTS)}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--utr',type=Path,required=True);p.add_argument('--osis',type=Path,required=True);p.add_argument('--write',action='store_true');a=p.parse_args();print(json.dumps(build(a.utr,a.osis,a.write),indent=2))
