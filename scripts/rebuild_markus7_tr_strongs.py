#!/usr/bin/env python3
"""Publiceer gecontroleerde TR-koppelingen voor Markus 7."""
from __future__ import annotations
import argparse,json
from pathlib import Path
from rebuild_johannes2_tr_strongs import mapping,r
from rebuild_nt_tr_strongs import load_tr_chapter
ROOT=Path(__file__).resolve().parents[1]
TOKEN_COUNTS=(13,14,20,23,26,30,8,21,14,19,20,13,15,12,23,6,16,22,20,12,15,10,10,22,18,19,23,21,15,17,20,13,22,13,16,14,16)
def build(utr_path:Path,osis_path:Path,write=False):
 s=load_tr_chapter(utr_path,osis_path,chapter=7,osis_book='Mark');p=ROOT/'data'/'markus'/'7.json';d=json.loads(p.read_text(encoding='utf8'));review={'book':'markus','chapter':7,'reviewed_through':37,'verses':{}}
 for v,count in zip(d['verses'],TOKEN_COUNTS):
  n=int(v['number']);ts=s[n];ids=r(0,count-1);anchor=v['text2026']
  if len(ts)!=count:raise ValueError(f'Markus 7:{n}: tokenstroom wijkt af')
  v['grondtekst']=[{'woord':t['woord'],'strongs':t['display_strong'],'lemma_strongs':t['lemma_strong'],'morfologie':t['morphology']} for t in ts];v['woordnummers']=[mapping(anchor,ids,ts,n)];v['woordnummers'][0]['herkomst']['referentie']=f'MRK 7:{n}';review['verses'][str(n)]=[{'tekst':anchor,'bronindices':ids,'reviewstatus':'handmatig_gecontroleerd'}]
 if write:
  p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf8');(ROOT/'data'/'woordnummers-review'/'markus-7.json').write_text(json.dumps(review,ensure_ascii=False,indent=2)+'\n',encoding='utf8');ip=ROOT/'data'/'woordnummers-inline'/'markus.json';i=json.loads(ip.read_text(encoding='utf8'));i['chapters']['7']={str(v['number']):v['woordnummers'] for v in d['verses']};ip.write_text(json.dumps(i,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 return {'verses':37,'tokens':sum(TOKEN_COUNTS)}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--utr',type=Path,required=True);p.add_argument('--osis',type=Path,required=True);p.add_argument('--write',action='store_true');a=p.parse_args();print(json.dumps(build(a.utr,a.osis,a.write),indent=2))
