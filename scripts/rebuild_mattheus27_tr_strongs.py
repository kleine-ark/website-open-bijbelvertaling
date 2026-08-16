#!/usr/bin/env python3
"""Publiceer gecontroleerde TR-koppelingen voor Mattheüs 27."""
from __future__ import annotations
import argparse,json
from pathlib import Path
from rebuild_johannes2_tr_strongs import mapping,r
from rebuild_nt_tr_strongs import load_tr_chapter
ROOT=Path(__file__).resolve().parents[1]
TOKEN_COUNTS=(19,11,18,13,11,18,14,10,23,12,26,13,10,13,13,7,17,7,27,17,17,15,14,30,16,12,17,7,28,13,20,14,11,12,28,5,17,13,9,22,12,18,16,11,13,25,11,17,11,10,21,11,17,24,17,20,16,16,10,22,14,16,14,33,11,12)
def build(utr_path:Path,osis_path:Path,write=False):
 s=load_tr_chapter(utr_path,osis_path,chapter=27,osis_book='Matt');p=ROOT/'data'/'mattheus'/'27.json';d=json.loads(p.read_text(encoding='utf8'))
 if len(d['verses'])!=len(TOKEN_COUNTS):raise ValueError('Mattheüs 27: onverwacht aantal verzen')
 review={'book':'mattheus','chapter':27,'reviewed_through':66,'verses':{}}
 for v,count in zip(d['verses'],TOKEN_COUNTS):
  n=int(v['number']);ts=s[n];ids=r(0,count-1);anchor=v['text2026']
  if len(ts)!=count:raise ValueError(f'Mattheüs 27:{n}: tokenstroom wijkt af')
  v['grondtekst']=[{'woord':t['woord'],'strongs':t['display_strong'],'lemma_strongs':t['lemma_strong'],'morfologie':t['morphology'],**({'tvm':t['tvm']} if t.get('tvm') else {})} for t in ts];v['woordnummers']=[mapping(anchor,ids,ts,n)];v['woordnummers'][0]['herkomst']['referentie']=f'MAT 27:{n}';review['verses'][str(n)]=[{'tekst':anchor,'bronindices':ids,'reviewstatus':'handmatig_gecontroleerd'}]
 if write:
  p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf8');(ROOT/'data'/'woordnummers-review'/'mattheus-27.json').write_text(json.dumps(review,ensure_ascii=False,indent=2)+'\n',encoding='utf8');ip=ROOT/'data'/'woordnummers-inline'/'mattheus.json';i=json.loads(ip.read_text(encoding='utf8'));i['chapters']['27']={str(v['number']):v['woordnummers'] for v in d['verses']};ip.write_text(json.dumps(i,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 return {'verses':66,'tokens':sum(TOKEN_COUNTS)}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--utr',type=Path,required=True);p.add_argument('--osis',type=Path,required=True);p.add_argument('--write',action='store_true');a=p.parse_args();print(json.dumps(build(a.utr,a.osis,a.write),indent=2))
