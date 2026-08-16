#!/usr/bin/env python3
"""Publiceer handmatig beoordeelde TR-koppelingen voor Mattheüs 1."""
from __future__ import annotations
import argparse,json
from pathlib import Path
from rebuild_nt_tr_strongs import load_tr_chapter
from rebuild_johannes2_tr_strongs import mapping,r

ROOT=Path(__file__).resolve().parents[1]
S={
1:[("Het boek van het geslacht",r(0,1)),("van JEZUS CHRISTUS",r(2,3)),("de Zoon van David",r(4,5)),("de zoon van Abraham",r(6,7))],
2:[("Abraham verwekte Izak",r(0,3)),("en Izak verwekte Jakob",r(4,8)),("en Jakob verwekte Juda",r(9,13)),("en zijn broers",r(14,17))],
3:[("En Juda verwekte Fares en Zara bij Thamar",r(0,10)),("en Fares verwekte Esrom",r(11,15)),("en Esrom verwekte Aram",r(16,20))],
4:[("En Aram verwekte Aminadab",r(0,4)),("en Aminadab verwekte Nahasson",r(5,9)),("en Nahasson verwekte Salmon",r(10,14))],
5:[("En Salmon verwekte Booz bij Rachab",r(0,7)),("en Booz verwekte Obed bij Ruth",r(8,15)),("en Obed verwekte Jessai",r(16,20))],
}
S.update({
6:[("En Jessai verwekte David, de koning",r(0,6)),("en David, de koning, verwekte Salomon",r(7,13)),("bij degene, die Uria's vrouw was geweest",r(14,17))],
7:[("En Salomon verwekte Roboam",r(0,4)),("en Roboam verwekte Abia",r(5,9)),("en Abia verwekte Asa",r(10,14))],
8:[("En Asa verwekte Josafat",r(0,4)),("en Josafat verwekte Joram",r(5,9)),("en Joram verwekte Ozias",r(10,14))],
9:[("En Ozias verwekte Joatham",r(0,4)),("en Joatham verwekte Achaz",r(5,9)),("en Achaz verwekte Ezekias",r(10,14))],
10:[("En Ezekias verwekte Manasse",r(0,4)),("en Manasse verwekte Amon",r(5,9)),("en Amon verwekte Josias",r(10,14))],
})
S.update({
11:[("En Josias verwekte Jechonias",r(0,4)),("en zijn broers",r(5,8)),("ongeveer de Babylonische overvoering",r(9,12))],
12:[("En na de Babylonische overvoering",r(0,4)),("verwekte Jechonias Salathiël",r(5,8)),("en Salathiël verwekte Zorobabel",r(9,13))],
13:[("En Zorobabel verwekte Abiud",r(0,4)),("en Abiud verwekte Eljakim",r(5,9)),("en Eljakim verwekte Azor",r(10,14))],
14:[("En Azor verwekte Sadok",r(0,4)),("en Sadok verwekte Achim",r(5,9)),("en Achim verwekte Elihud",r(10,14))],
15:[("En Elihud verwekte Eleazar",r(0,4)),("en Eleazar verwekte Matthan",r(5,9)),("en Matthan verwekte Jakob",r(10,14))],
})
S.update({
16:[("En Jakob verwekte Jozef, de man van Maria",r(0,7)),("uit wie geboren is JEZUS, gezegd Christus",r(8,14))],
17:[("Al de geslachten dan, van Abraham tot David, zijn veertien geslachten",r(0,9)),("en van David tot de Babylonische overvoering, zijn veertien geslachten",r(10,18)),("en van de Babylonische overvoering tot Christus, zijn veertien geslachten",r(19,28))],
18:[("De geboorte van Jezus Christus was nu zo",r(0,8)),("want als Maria, zijn moeder, met Jozef ondertrouwd was",r(9,15)),("voordat zij samengekomen waren",r(16,19)),("werd zij zwanger bevonden uit de Heilige Geest",r(20,26))],
19:[("Jozef nu, haar man, zo hij rechtvaardig was",r(0,6)),("en haar niet wilde openlijk te schande maken",r(7,11)),("was van wil haar in het geheim te verlaten",r(12,15))],
20:[("En zo hij deze dingen in de zin had",r(0,3)),("ziet",r(4)),("de engel",r(5)),("van de Heere verscheen hem in de droom, zeggende",r(6,11)),("Jozef, u zoon van David",r(12,14)),("wees niet bevreesd Maria, uw vrouw, tot u te nemen",r(15,21)),("want wat in haar ontvangen is, dat is uit de Heilige Geest",r(22,30))],
})
S.update({
21:[("En zij zal een Zoon baren",r(0,2)),("en u zult Zijn naam heten JEZUS",r(3,8)),("want Hij zal Zijn volk zalig maken",r(9,14)),("van hun zonden",r(15,18))],
22:[("En dit alles is gebeurd",r(0,3)),("opdat vervuld zou worden",r(4,7)),("wat van de Heere gesproken is, door de profeet, zeggende",r(8,14))],
23:[("Zie, de maagd zal zwanger worden",r(0,5)),("en een Zoon baren",r(6,8)),("en u zult Zijn naam heten Emmanuël",r(9,14)),("dat is, overgezet zijnde, God met ons",r(15,21))],
24:[("Jozef dan",r(1,3)),("opgewekt zijnde",r(0)),("van de",r(4,5)),("slaap",r(6)),("deed, zoals de engel van de Heere hem bevolen had",r(7,13)),("en heeft zijn vrouw tot zich genomen",r(14,18))],
25:[("En had geen gemeenschap met haar",r(0,3)),("voordat zij deze haar eerstgeboren Zoon gebaard had",r(4,11)),("en heette Zijn naam JEZUS",r(12,17))],
})
def build(u,o,w=False):
 src=load_tr_chapter(u,o,chapter=1,osis_book='Matt');p=ROOT/'data/mattheus/1.json';d=json.loads(p.read_text(encoding='utf-8'));reviewed_through=max(S);rev={'book':'mattheus','chapter':1,'reviewed_through':reviewed_through,'verses':{}}
 for v in d['verses'][:reviewed_through]:
  n=int(v['number']);ts=src[n];gs=S[n];ids=[i for _,x in gs for i in x]
  if sorted(ids)!=list(range(len(ts))) or len(ids)!=len(set(ids)):raise ValueError(n)
  v['grondtekst']=[{'woord':t['woord'],'strongs':t['display_strong'],'lemma_strongs':t['lemma_strong'],'morfologie':t['morphology'],**({'tvm':t['tvm']} if t.get('tvm') else {})} for t in ts];v['woordnummers']=[mapping(a,x,ts,n) for a,x in gs];occ={}
  for x in v['woordnummers']:occ[x['tekst']]=occ.get(x['tekst'],0)+1;x['voorkomen']=occ[x['tekst']];x['herkomst']['referentie']=f'MAT 1:{n}'
  rev['verses'][str(n)]=[{'tekst':a,'bronindices':x,'reviewstatus':'handmatig_gecontroleerd'} for a,x in gs]
 if w:
  p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');(ROOT/'data/woordnummers-review/mattheus-1.json').write_text(json.dumps(rev,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');ip=ROOT/'data/woordnummers-inline/mattheus.json';z=json.loads(ip.read_text(encoding='utf-8'));z['chapters']['1']={str(v['number']):v['woordnummers'] for v in d['verses'][:reviewed_through]};ip.write_text(json.dumps(z,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 return {'verses':reviewed_through,'tokens':sum(len(src[n]) for n in range(1,reviewed_through+1))}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--utr',type=Path,required=True);p.add_argument('--osis',type=Path,required=True);p.add_argument('--write',action='store_true');a=p.parse_args();print(build(a.utr,a.osis,a.write))
