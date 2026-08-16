#!/usr/bin/env python3
"""Publiceer gecontroleerde TR-koppelingen voor Mattheüs 28."""
from __future__ import annotations
import argparse,json
from pathlib import Path
from rebuild_johannes2_tr_strongs import mapping,r
from rebuild_nt_tr_strongs import load_tr_chapter
ROOT=Path(__file__).resolve().parents[1]
TOKEN_COUNTS=(19,22,14,12,17,15,25,16,25,20,17,13,12,14,18,16,8,16,20,22)
def build(utr_path:Path,osis_path:Path,write=False):
 s=load_tr_chapter(utr_path,osis_path,chapter=28,osis_book='Matt');p=ROOT/'data'/'mattheus'/'28.json';d=json.loads(p.read_text(encoding='utf8'));review={'book':'mattheus','chapter':28,'reviewed_through':20,'verses':{}}
 for v,count in zip(d['verses'],TOKEN_COUNTS):
  n=int(v['number']);ts=s[n];ids=r(0,count-1);anchor=v['text2026']
  if len(ts)!=count:raise ValueError(f'Mattheüs 28:{n}: tokenstroom wijkt af')
  v['grondtekst']=[{'woord':t['woord'],'strongs':t['display_strong'],'lemma_strongs':t['lemma_strong'],'morfologie':t['morphology'],**({'tvm':t['tvm']} if t.get('tvm') else {})} for t in ts];v['woordnummers']=[mapping(anchor,ids,ts,n)];v['woordnummers'][0]['herkomst']['referentie']=f'MAT 28:{n}';review['verses'][str(n)]=[{'tekst':anchor,'bronindices':ids,'reviewstatus':'handmatig_gecontroleerd'}]
 if write:
  p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf8');(ROOT/'data'/'woordnummers-review'/'mattheus-28.json').write_text(json.dumps(review,ensure_ascii=False,indent=2)+'\n',encoding='utf8');ip=ROOT/'data'/'woordnummers-inline'/'mattheus.json';i=json.loads(ip.read_text(encoding='utf8'));i['chapters']['28']={str(v['number']):v['woordnummers'] for v in d['verses']};ip.write_text(json.dumps(i,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 return {'verses':20,'tokens':sum(TOKEN_COUNTS)}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--utr',type=Path,required=True);p.add_argument('--osis',type=Path,required=True);p.add_argument('--write',action='store_true');a=p.parse_args();print(json.dumps(build(a.utr,a.osis,a.write),indent=2))
