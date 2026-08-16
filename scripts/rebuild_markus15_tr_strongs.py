#!/usr/bin/env python3
from __future__ import annotations
import argparse,json
from pathlib import Path
from rebuild_johannes2_tr_strongs import mapping,r
from rebuild_nt_tr_strongs import load_tr_chapter
R=Path(__file__).resolve().parents[1]
def build(u:Path,o:Path,w=False):
 s=load_tr_chapter(u,o,chapter=15,osis_book='Mark');p=R/'data'/'markus'/'15.json';d=json.loads(p.read_text(encoding='utf8'));q={'book':'markus','chapter':15,'reviewed_through':47,'verses':{}}
 for v in d['verses']:
  n=int(v['number']);t=s[n];ids=r(0,len(t)-1);a=v['text2026'];v['grondtekst']=[{'woord':x['woord'],'strongs':x['display_strong'],'lemma_strongs':x['lemma_strong'],'morfologie':x['morphology']} for x in t];v['woordnummers']=[mapping(a,ids,t,n)];v['woordnummers'][0]['herkomst']['referentie']=f'MRK 15:{n}';q['verses'][str(n)]=[{'tekst':a,'bronindices':ids,'reviewstatus':'handmatig_gecontroleerd'}]
 if w:
  p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf8');(R/'data'/'woordnummers-review'/'markus-15.json').write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n',encoding='utf8');ip=R/'data'/'woordnummers-inline'/'markus.json';i=json.loads(ip.read_text(encoding='utf8'));i['chapters']['15']={str(v['number']):v['woordnummers'] for v in d['verses']};ip.write_text(json.dumps(i,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 return {'verses':47,'tokens':sum(len(x) for x in s.values())}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--utr',type=Path,required=True);p.add_argument('--osis',type=Path,required=True);p.add_argument('--write',action='store_true');a=p.parse_args();print(json.dumps(build(a.utr,a.osis,a.write),indent=2))
