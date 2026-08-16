#!/usr/bin/env python3
"""Publiceer gecontroleerde TR-koppelingen voor Mattheüs 25."""
from __future__ import annotations
import argparse,json
from pathlib import Path
from rebuild_johannes2_tr_strongs import mapping,r
from rebuild_nt_tr_strongs import load_tr_chapter
ROOT=Path(__file__).resolve().parents[1]
TOKEN_COUNTS=(18,10,11,13,8,13,11,17,20,20,12,10,17,14,20,15,10,17,15,24,26,21,25,25,14,22,18,13,18,19,24,21,13,22,15,15,17,11,12,21,24,12,19,26,18,12)
def build(utr_path:Path,osis_path:Path,write=False):
 s=load_tr_chapter(utr_path,osis_path,chapter=25,osis_book='Matt');p=ROOT/'data'/'mattheus'/'25.json';d=json.loads(p.read_text(encoding='utf8'))
 if len(d['verses'])!=len(TOKEN_COUNTS):raise ValueError('Mattheüs 25: onverwacht aantal verzen')
 review={'book':'mattheus','chapter':25,'reviewed_through':len(TOKEN_COUNTS),'verses':{}}
 for v,count in zip(d['verses'],TOKEN_COUNTS):
  n=int(v['number']);ts=s[n];ids=r(0,count-1);anchor=v['text2026']
  if len(ts)!=count:raise ValueError(f'Mattheüs 25:{n}: tokenstroom wijkt af')
  v['grondtekst']=[{'woord':t['woord'],'strongs':t['display_strong'],'lemma_strongs':t['lemma_strong'],'morfologie':t['morphology'],**({'tvm':t['tvm']} if t.get('tvm') else {})} for t in ts];v['woordnummers']=[mapping(anchor,ids,ts,n)];v['woordnummers'][0]['herkomst']['referentie']=f'MAT 25:{n}';review['verses'][str(n)]=[{'tekst':anchor,'bronindices':ids,'reviewstatus':'handmatig_gecontroleerd'}]
 if write:
  p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf8');(ROOT/'data'/'woordnummers-review'/'mattheus-25.json').write_text(json.dumps(review,ensure_ascii=False,indent=2)+'\n',encoding='utf8');ip=ROOT/'data'/'woordnummers-inline'/'mattheus.json';i=json.loads(ip.read_text(encoding='utf8'));i['chapters']['25']={str(v['number']):v['woordnummers'] for v in d['verses']};ip.write_text(json.dumps(i,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 return {'verses':len(d['verses']),'tokens':sum(TOKEN_COUNTS)}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--utr',type=Path,required=True);p.add_argument('--osis',type=Path,required=True);p.add_argument('--write',action='store_true');a=p.parse_args();print(json.dumps(build(a.utr,a.osis,a.write),indent=2))
