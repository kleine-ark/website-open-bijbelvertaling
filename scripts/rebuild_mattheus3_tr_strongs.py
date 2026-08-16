#!/usr/bin/env python3
"""Publiceer handmatig beoordeelde TR-koppelingen voor Mattheüs 3."""
from __future__ import annotations
import argparse,json
from pathlib import Path
from rebuild_nt_tr_strongs import load_tr_chapter
from rebuild_johannes2_tr_strongs import mapping,r
ROOT=Path(__file__).resolve().parents[1]
S={
1:[("En in die dagen kwam Johannes de Doper",r(0,8)),("predikende in de woestijn van Judea",r(9,14))],
2:[("En zeggende",r(0,1)),("Bekeer u",r(2)),("want het Koninkrijk van de hemelen is nabij gekomen",r(3,8))],
3:[("Want deze is het, van die gesproken is door Jesaja, de profeet, zeggende",r(0,9)),("De stem van de roependen in de woestijn",r(10,14)),("Bereid de weg van de Heere",r(15,18)),("maakt Zijn paden recht",r(19,23))],
4:[("En dezelfde Johannes had zijn kleding van kameelhaar",r(0,10)),("en een leren gordel om zijn middel",r(11,17)),("en zijn voedsel was sprinkhanen en wilde honing",r(18,26))],
5:[("Toen is tot hem uitgegaan Jeruzalem en geheel Judea",r(0,8)),("en het hele land rondom de Jordaan",r(9,14))],
6:[("En werden van hem gedoopt in de Jordaan",r(0,6)),("belijdende hun zonden",r(7,10))],
7:[("Hij dan, ziende velen van de Farizeën en Sadduceën tot zijn doop komen",r(0,11)),("sprak tot hen",r(12,13)),("U adderengebroed",r(14,15)),("wie heeft u aangewezen te vluchten van de komende toorn",r(16,23))],
8:[("Breng dan vruchten voort, van de bekering waard",r(0,5))],
}
S.update({
9:[("En denk niet bij u zelf te zeggen: Wij hebben Abraham tot een vader",r(0,9)),("want ik zeg u, dat God zelfs uit deze stenen Abraham kinderen kan verwekken",r(10,24))],
10:[("En ook is al de bijl aan de wortel van de bomen gelegd",r(0,10)),("alle boom dan, die geen goede vrucht voortbrengt",r(11,17)),("wordt omgehakt en in het vuur geworpen",r(18,22))],
11:[("Ik doop u wel met water tot bekering",r(0,7)),("maar Die na mij komt, is sterker dan ik",r(8,15)),("Wiens schoenen ik niet waard ben Hem na te dragen",r(16,22)),("Die zal u met de Heilige Geest en met vuur dopen",r(23,30))],
12:[("Wiens wan in Zijn hand is",r(0,6)),("en Hij zal Zijn dorsvloer doorzuiveren",r(7,12)),("en Zijn tarwe in Zijn schuur samenbrengen",r(13,19)),("en zal het kaf met onuitblusselijk vuur verbranden",r(20,25))],
13:[("Toen kwam Jezus",r(0,3)),("van Galilea naar de Jordaan",r(4,9)),("tot Johannes, om van hem gedoopt te worden",r(10,16))],
14:[("Maar Johannes weigerde Hem zeer, zeggende",r(0,5)),("Mij is nodig van U gedoopt te worden",r(6,11)),("en komt U tot mij",r(12,16))],
15:[("Maar Jezus, antwoordende, zei tot hem",r(0,6)),("Laat nu af",r(7,8)),("want zo past ons alle gerechtigheid te vervullen",r(9,16)),("Toen liet hij van Hem af",r(17,19))],
16:[("En Jezus, gedoopt zijnde, is meteen opgeklommen uit het water",r(0,8)),("en ziet, de hemelen werden Hem geopend",r(9,14)),("en hij zag de Geest van God nederdalen, gelijk een duif",r(15,23)),("en op Hem komen",r(24,27))],
17:[("En ziet, een stem uit de hemelen, zeggende",r(0,6)),("Deze is Mijn Zoon, Mijn Geliefde, in Wie Ik Mijn welbehagen heb",r(7,16))],
})
def build(u,o,w=False):
 src=load_tr_chapter(u,o,chapter=3,osis_book='Matt');p=ROOT/'data/mattheus/3.json';d=json.loads(p.read_text(encoding='utf-8'));reviewed_through=max(S);rev={'book':'mattheus','chapter':3,'reviewed_through':reviewed_through,'verses':{}}
 for v in d['verses'][:reviewed_through]:
  n=int(v['number']);ts=src[n];gs=S[n];ids=[i for _,x in gs for i in x]
  if sorted(ids)!=list(range(len(ts))) or len(ids)!=len(set(ids)):raise ValueError(n)
  v['grondtekst']=[{'woord':t['woord'],'strongs':t['display_strong'],'lemma_strongs':t['lemma_strong'],'morfologie':t['morphology'],**({'tvm':t['tvm']} if t.get('tvm') else {})} for t in ts];v['woordnummers']=[mapping(a,x,ts,n) for a,x in gs];occ={}
  for x in v['woordnummers']:occ[x['tekst']]=occ.get(x['tekst'],0)+1;x['voorkomen']=occ[x['tekst']];x['herkomst']['referentie']=f'MAT 3:{n}'
  rev['verses'][str(n)]=[{'tekst':a,'bronindices':x,'reviewstatus':'handmatig_gecontroleerd'} for a,x in gs]
 if w:
  p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');(ROOT/'data/woordnummers-review/mattheus-3.json').write_text(json.dumps(rev,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');ip=ROOT/'data/woordnummers-inline/mattheus.json';z=json.loads(ip.read_text(encoding='utf-8'));z['chapters']['3']={str(v['number']):v['woordnummers'] for v in d['verses'][:reviewed_through]};ip.write_text(json.dumps(z,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 return {'verses':reviewed_through,'tokens':sum(len(src[n]) for n in range(1,reviewed_through+1))}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--utr',type=Path,required=True);p.add_argument('--osis',type=Path,required=True);p.add_argument('--write',action='store_true');a=p.parse_args();print(build(a.utr,a.osis,a.write))
