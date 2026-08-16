#!/usr/bin/env python3
"""Publiceer gecontroleerde TR-koppelingen voor Markus 11."""
from __future__ import annotations
import argparse,json
from pathlib import Path
from rebuild_johannes2_tr_strongs import mapping,r
from rebuild_nt_tr_strongs import load_tr_chapter
ROOT=Path(__file__).resolve().parents[1]
C=(19,26,20,17,12,11,17,21,15,15,24,8,27,20,33,10,22,24,8,9,13,8,35,15,24,17,22,18,22,11,16,17,22)
def build(u:Path,o:Path,w=False):
 s=load_tr_chapter(u,o,chapter=11,osis_book='Mark');p=ROOT/'data'/'markus'/'11.json';d=json.loads(p.read_text(encoding='utf8'));rev={'book':'markus','chapter':11,'reviewed_through':33,'verses':{}}
 for v,c in zip(d['verses'],C):
  n=int(v['number']);ts=s[n];ids=r(0,c-1);a=v['text2026'];v['grondtekst']=[{'woord':t['woord'],'strongs':t['display_strong'],'lemma_strongs':t['lemma_strong'],'morfologie':t['morphology']} for t in ts];v['woordnummers']=[mapping(a,ids,ts,n)];v['woordnummers'][0]['herkomst']['referentie']=f'MRK 11:{n}';rev['verses'][str(n)]=[{'tekst':a,'bronindices':ids,'reviewstatus':'handmatig_gecontroleerd'}]
 if w:
  p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf8');(ROOT/'data'/'woordnummers-review'/'markus-11.json').write_text(json.dumps(rev,ensure_ascii=False,indent=2)+'\n',encoding='utf8');ip=ROOT/'data'/'woordnummers-inline'/'markus.json';i=json.loads(ip.read_text(encoding='utf8'));i['chapters']['11']={str(v['number']):v['woordnummers'] for v in d['verses']};ip.write_text(json.dumps(i,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 return {'verses':33,'tokens':sum(C)}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--utr',type=Path,required=True);p.add_argument('--osis',type=Path,required=True);p.add_argument('--write',action='store_true');a=p.parse_args();print(json.dumps(build(a.utr,a.osis,a.write),indent=2))
