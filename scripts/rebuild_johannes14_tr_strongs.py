#!/usr/bin/env python3
from __future__ import annotations
import argparse,json
from pathlib import Path
from rebuild_nt_tr_strongs import load_tr_chapter
from rebuild_johannes2_tr_strongs import mapping,r
ROOT=Path(__file__).resolve().parents[1]
S={
1:[("Uw hart wordt niet ontroerd",r(0,4)),("u gelooft in God",r(5,8)),("gelooft ook in Mij",r(9,12))],
2:[("In het huis van Mijn Vader",r(0,5)),("zijn vele woningen",r(6,8)),("anders zo zou Ik het u gezegd hebben",r(9,14)),("Ik ga heen om u plaats te bereiden",r(15,18))],
3:[("En zo wanneer Ik heen zal gegaan zijn",r(0,2)),("en u plaats zal bereid hebben",r(3,6)),("zo komt Ik weer",r(7,8)),("en zal u tot Mij nemen",r(9,13)),("opdat u ook zijn mag, waar Ik ben",r(14,20))],
4:[("En waar Ik heenga, weet u",r(0,4)),("en de weg weet u",r(5,8))],
5:[("Thomas zei tot Hem",r(0,2)),("Heere",r(3)),("wij weten niet, waar U heengaat",r(4,7)),("en hoe kunnen wij de weg weten",r(8,13))],
6:[("Jezus zei tot hem",r(0,3)),("Ik ben de Weg, en de Waarheid, en het Leven",r(4,13)),("Niemand komt tot de Vader",r(14,18)),("dan door Mij",r(19,22))],
7:[("Als u Mij gekend had",r(0,2)),("zo zou u ook Mijn Vader gekend hebben",r(3,8)),("en van nu kent u Hem",r(9,13)),("en hebt Hem gezien",r(14,16))],
8:[("Filippus zei tot Hem",r(0,2)),("Heere",r(3)),("toon ons de Vader",r(4,7)),("en het is ons genoeg",r(8,10))],
9:[("Jezus zei tot hem",r(0,3)),("Ben Ik zo langen tijd met u",r(4,8)),("en hebt u Mij niet gekend, Filippus",r(9,13)),("Die Mij gezien heeft",r(14,16)),("die heeft de Vader gezien",r(17,19)),("en hoe zegt u",r(20,23)),("Toon ons de Vader",r(24,27))],
10:[("Gelooft u niet",r(0,1)),("dat Ik in de Vader ben",r(2,6)),("en de Vader in Mij is",r(7,12)),("De woorden, die Ik tot u spreek",r(13,18)),("spreek Ik van Mijzelf niet",r(19,22)),("maar de Vader, Die in Mij blijft",r(23,29)),("Deze doet de werken",r(30,33))]}
S.update({
11:[("Geloof Mij",r(0,1)),("dat",r(2)),("Ik in de Vader ben",r(3,6)),("en de Vader in Mij is",r(7,12)),("en als niet",r(13,14)),("zo gelooft Mij om de werken zelf",r(15,20))],
12:[("Voorwaar, voorwaar zeg Ik u",r(0,3)),("Die in Mij gelooft",r(4,7)),("de werken, die Ik doe",r(8,12)),("zal hij ook doen",r(13,14)),("en zal meerder doen, dan deze",r(15,18)),("want Ik ga heen tot Mijn Vader",r(19,25))],
13:[("En zo wat u begeren zult in Mijn Naam",r(0,8)),("dat zal Ik doen",r(9,10)),("opdat de Vader in de Zoon verheerlijkt wordt",r(11,17))],
14:[("Zo u iets begeren zult in Mijn Naam",r(0,6)),("Ik zal het doen",r(7,8))],
15:[("Als",r(0)),("u Mij liefhebt",r(1,2)),("zo bewaart Mijn geboden",r(3,7))],
16:[("En Ik zal de Vader bidden",r(0,4)),("en Hij zal u een andere Trooster geven",r(5,9)),("opdat Hij bij u blijft in de eeuwigheid",r(10,16))],
17:[("Namelijk de Geest van de waarheid",r(0,3)),("Wie",r(4)),("de wereld niet kan ontvangen",r(5,9)),("want zij ziet Hem niet",r(10,13)),("en kent Hem niet",r(14,16)),("maar u kent Hem",r(17,20)),("want Hij blijft bij u",r(21,24)),("en zal in u zijn",r(25,28))],
18:[("Ik zal u geen wezen laten",r(0,3)),("Ik kom weer tot u",r(4,6))],
19:[("Nog een kleine tijd",r(0,1)),("en de wereld zal Mij niet meer zien",r(2,8)),("maar u zult Mij zien",r(9,12)),("want Ik leef",r(13,15)),("en u zult leven",r(16,18))],
20:[("In die dag",r(0,3)),("zult u bekennen",r(4,5)),("dat Ik in Mijn Vader ben",r(6,11)),("en u in Mij",r(12,15)),("en Ik in u",r(16,18))],
21:[("Die Mijn geboden heeft",r(0,4)),("en deze bewaart",r(5,7)),("die is het",r(8,9)),("die Mij liefheeft",r(10,12)),("en die Mij liefheeft",r(13,16)),("zal van Mijn Vader geliefd worden",r(17,21)),("en Ik zal hem liefhebben",r(22,25)),("en Ik zal Mijzelf aan hem openbaren",r(26,29))],
22:[("Judas, niet de Iskariot, zei tot Hem",r(0,5)),("Heere",r(6)),("wat is het",r(7,8)),("dat U Uzelf aan ons zult openbaren",r(9,13)),("en niet aan de wereld",r(14,17))],
23:[("Jezus antwoordde en zei tot hem",r(0,5)),("Zo iemand Mij liefheeft",r(6,9)),("die zal Mijn woord bewaren",r(10,13)),("en Mijn Vader zal hem liefhebben",r(14,19)),("en Wij zullen tot hem komen",r(20,23)),("en zullen woning bij hem maken",r(24,28))],
24:[("Die Mij niet liefheeft",r(0,3)),("die bewaart Mijn woorden niet",r(4,8)),("en het woord dat u hoort",r(9,13)),("is het Mijne niet",r(14,16)),("maar van de Vader, Die Mij gezonden heeft",r(17,21))],
25:[("Deze dingen heb Ik tot u gesproken",r(0,2)),("bij u blijvende",r(3,5))],
26:[("Maar de Trooster",r(0,2)),("de Heilige Geest",r(3,6)),("Wie de Vader zenden zal in Mijn Naam",r(7,14)),("Die zal u alles leren",r(15,18)),("en zal u indachtig maken alles",r(19,22)),("wat Ik u gezegd heb",r(23,25))],
27:[("Vrede laat Ik u",r(0,2)),("Mijn vrede geef Ik u",r(3,7)),("niet zoals de wereld hem geeft",r(8,12)),("geef Ik hem u",r(13,15)),("Uw hart wordt niet ontroerd",r(16,20)),("en zij niet versaagd",r(21,22))],
28:[("U hebt gehoord",r(0)),("dat Ik tot u gezegd heb",r(1,4)),("Ik ga heen",r(5)),("en kom weer tot u",r(6,9)),("Als u Mij liefhadt",r(10,12)),("zo zou u zich verblijden",r(13,14)),("omdat Ik gezegd heb",r(15,16)),("Ik ga heen tot de Vader",r(17,20)),("want Mijn Vader is meerder dan Ik",r(21,27))],
29:[("En nu heb Ik het u gezegd",r(0,3)),("voordat het gebeurd is",r(4,5)),("opdat",r(6)),("wanneer het gebeurd zal zijn",r(7,8)),("u geloven mag",r(9))],
30:[("Ik zal niet meer veel met u spreken",r(0,5)),("want de overste van deze wereld komt",r(6,12)),("en heeft aan Mij niets",r(13,18))],
31:[("Maar opdat de wereld wete",r(0,4)),("dat Ik de Vader liefheb",r(5,8)),("en zo doe, zoals Mij de Vader geboden heeft",r(9,16)),("Sta op",r(17)),("laat ons van hier gaan",r(18,19))],
})
def build(u,o,w=False):
 src=load_tr_chapter(u,o,chapter=14,osis_book='John');p=ROOT/'data/johannes/14.json';d=json.loads(p.read_text(encoding='utf-8'));reviewed_through=max(S);rev={'book':'johannes','chapter':14,'reviewed_through':reviewed_through,'verses':{}}
 for v in d['verses'][:reviewed_through]:
  n=int(v['number']);ts=src[n];gs=S[n];ids=[i for _,x in gs for i in x]
  if sorted(ids)!=list(range(len(ts))) or len(ids)!=len(set(ids)):raise ValueError(n)
  v['grondtekst']=[{'woord':t['woord'],'strongs':t['display_strong'],'lemma_strongs':t['lemma_strong'],'morfologie':t['morphology'],**({'tvm':t['tvm']} if t.get('tvm') else {})} for t in ts];v['woordnummers']=[mapping(a,x,ts,n) for a,x in gs];occ={}
  for x in v['woordnummers']:occ[x['tekst']]=occ.get(x['tekst'],0)+1;x['voorkomen']=occ[x['tekst']];x['herkomst']['referentie']=f'JHN 14:{n}'
  rev['verses'][str(n)]=[{'tekst':a,'bronindices':x,'reviewstatus':'handmatig_gecontroleerd'} for a,x in gs]
 if w:
  p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');(ROOT/'data/woordnummers-review/johannes-14.json').write_text(json.dumps(rev,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');ip=ROOT/'data/woordnummers-inline/johannes.json';z=json.loads(ip.read_text(encoding='utf-8'));z['chapters']['14']={str(v['number']):v['woordnummers'] for v in d['verses'][:reviewed_through]};ip.write_text(json.dumps(z,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 return {'verses':reviewed_through,'tokens':sum(len(src[n]) for n in range(1,reviewed_through+1))}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--utr',type=Path,required=True);p.add_argument('--osis',type=Path,required=True);p.add_argument('--write',action='store_true');a=p.parse_args();print(build(a.utr,a.osis,a.write))
