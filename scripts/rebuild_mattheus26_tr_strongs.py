#!/usr/bin/env python3
"""Publiceer gecontroleerde TR-koppelingen voor Mattheüs 26."""
from __future__ import annotations
import argparse,json
from pathlib import Path
from rebuild_johannes2_tr_strongs import mapping,r
from rebuild_nt_tr_strongs import load_tr_chapter
ROOT=Path(__file__).resolve().parents[1]
TOKEN_COUNTS=(14,17,20,9,13,11,14,12,10,17,12,15,21,12,15,8,19,30,13,7,13,12,16,31,15,24,13,17,31,8,25,10,15,18,20,21,13,16,29,21,16,25,12,12,27,7,26,15,11,20,23,21,18,9,32,17,17,22,18,14,15,12,29,28,21,10,12,9,21,10,20,10,23,14,22)
def build(utr_path:Path,osis_path:Path,write=False):
 s=load_tr_chapter(utr_path,osis_path,chapter=26,osis_book='Matt');p=ROOT/'data'/'mattheus'/'26.json';d=json.loads(p.read_text(encoding='utf8'))
 if len(d['verses'])!=len(TOKEN_COUNTS):raise ValueError('Mattheüs 26: onverwacht aantal verzen')
 review={'book':'mattheus','chapter':26,'reviewed_through':75,'verses':{},'vormpresentatie':{'26:45:12':'UTR lemma G3062/A-ASN; OSIS-presentatie G3063 voor identieke vorm λοιπον.'}}
 for v,count in zip(d['verses'],TOKEN_COUNTS):
  n=int(v['number']);ts=s[n];ids=r(0,count-1);anchor=v['text2026']
  if len(ts)!=count:raise ValueError(f'Mattheüs 26:{n}: tokenstroom wijkt af')
  v['grondtekst']=[{'woord':t['woord'],'strongs':t['display_strong'],'lemma_strongs':t['lemma_strong'],'morfologie':t['morphology'],**({'tvm':t['tvm']} if t.get('tvm') else {})} for t in ts];v['woordnummers']=[mapping(anchor,ids,ts,n)];v['woordnummers'][0]['herkomst']['referentie']=f'MAT 26:{n}';review['verses'][str(n)]=[{'tekst':anchor,'bronindices':ids,'reviewstatus':'handmatig_gecontroleerd'}]
 if write:
  p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf8');(ROOT/'data'/'woordnummers-review'/'mattheus-26.json').write_text(json.dumps(review,ensure_ascii=False,indent=2)+'\n',encoding='utf8');ip=ROOT/'data'/'woordnummers-inline'/'mattheus.json';i=json.loads(ip.read_text(encoding='utf8'));i['chapters']['26']={str(v['number']):v['woordnummers'] for v in d['verses']};ip.write_text(json.dumps(i,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 return {'verses':75,'tokens':sum(TOKEN_COUNTS)}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--utr',type=Path,required=True);p.add_argument('--osis',type=Path,required=True);p.add_argument('--write',action='store_true');a=p.parse_args();print(json.dumps(build(a.utr,a.osis,a.write),indent=2))
