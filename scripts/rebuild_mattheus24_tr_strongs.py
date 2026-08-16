#!/usr/bin/env python3
"""Publiceer gecontroleerde TR-koppelingen voor Mattheüs 24."""
from __future__ import annotations
import argparse, json
from pathlib import Path
from rebuild_johannes2_tr_strongs import mapping, r
from rebuild_nt_tr_strongs import load_tr_chapter
ROOT = Path(__file__).resolve().parents[1]
# Handmatig gecontroleerde TR-tokenaantallen per volledig Nederlands versanker.
TOKEN_COUNTS = (19,23,32,11,15,19,18,5,19,10,7,11,7,21,20,9,12,12,13,12,18,20,13,18,3,17,20,10,32,37,24,23,13,14,13,21,15,24,19,13,10,11,23,16,24,12,11,16,12,17,20)
def build(utr_path:Path,osis_path:Path,write=False):
 source=load_tr_chapter(utr_path,osis_path,chapter=24,osis_book='Matt');p=ROOT/'data'/'mattheus'/'24.json';d=json.loads(p.read_text(encoding='utf8'))
 if len(d['verses'])!=len(TOKEN_COUNTS):raise ValueError('Mattheüs 24: onverwacht aantal verzen')
 review={'book':'mattheus','chapter':24,'reviewed_through':len(TOKEN_COUNTS),'verses':{}}
 for v,count in zip(d['verses'],TOKEN_COUNTS):
  n=int(v['number']);ts=source[n];anchor=v['text2026'];ids=r(0,count-1)
  if len(ts)!=count or ids!=list(range(len(ts))):raise ValueError(f'Mattheüs 24:{n}: tokenstroom wijkt af van handmatige review')
  v['grondtekst']=[{'woord':t['woord'],'strongs':t['display_strong'],'lemma_strongs':t['lemma_strong'],'morfologie':t['morphology'],**({'tvm':t['tvm']} if t.get('tvm') else {})} for t in ts];v['woordnummers']=[mapping(anchor,ids,ts,n)]
  v['woordnummers'][0]['herkomst']['referentie']=f'MAT 24:{n}';review['verses'][str(n)]=[{'tekst':anchor,'bronindices':ids,'reviewstatus':'handmatig_gecontroleerd'}]
 if write:
  p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf8');(ROOT/'data'/'woordnummers-review'/'mattheus-24.json').write_text(json.dumps(review,ensure_ascii=False,indent=2)+'\n',encoding='utf8');ip=ROOT/'data'/'woordnummers-inline'/'mattheus.json';i=json.loads(ip.read_text(encoding='utf8'));i['chapters']['24']={str(v['number']):v['woordnummers'] for v in d['verses']};ip.write_text(json.dumps(i,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 return {'verses':len(d['verses']),'tokens':sum(TOKEN_COUNTS)}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--utr',type=Path,required=True);p.add_argument('--osis',type=Path,required=True);p.add_argument('--write',action='store_true');a=p.parse_args();print(json.dumps(build(a.utr,a.osis,a.write),indent=2))
