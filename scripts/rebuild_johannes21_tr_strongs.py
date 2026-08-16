#!/usr/bin/env python3
from __future__ import annotations
import argparse,json
from pathlib import Path
from rebuild_nt_tr_strongs import load_tr_chapter
from rebuild_johannes2_tr_strongs import mapping,r
ROOT=Path(__file__).resolve().parents[1]
S={
1:[("Na deze openbaarde Jezus Zichzelf opnieuw de discipelen aan de zee van Tiberias",r(0,13)),("En Hij openbaarde Zich zo",r(14,16))],
2:[("Er waren samen Simon Petrus",r(0,3)),("en Thomas, gezegd Didymus",r(4,8)),("en Nathanaël, die van Kana in Galilea was",r(9,15)),("en de zonen van Zebedeüs",r(16,19)),("en twee anderen van Zijn discipelen",r(20,26))],
3:[("Simon Petrus zei tot hen",r(0,3)),("Ik ga vissen",r(4,5)),("Zij zeiden tot hem",r(6,7)),("Wij gaan ook met u",r(8,12)),("Zij gingen uit, en traden meteen in het schip",r(13,19)),("en in die nacht vingen zij niets",r(20,26))],
4:[("En als het nu morgenstond geworden was",r(0,3)),("stond Jezus op de oever",r(4,9)),("maar de discipelen wisten niet, dat het Jezus was",r(10,17))],
5:[("Jezus dan zei tot hen",r(0,4)),("Kinderen, hebt u niet enige toespijs",r(5,9)),("Zij antwoordden Hem",r(10,11)),("Nee",r(12))],
6:[("En Hij zei tot hen",r(0,3)),("Werpt het net aan de rechterzijde van het schip",r(4,12)),("en u zult vinden",r(13,14)),("Zij wierpen het dan",r(15,17)),("en konden het niet meer trekken",r(18,22)),("vanwege de menigte van de vissen",r(23,27))],
7:[("De discipel dan, wie Jezus liefhad, zei tot Petrus",r(0,10)),("Het is de Heere",r(11,13)),("Simon Petrus dan, horende, dat het de Heere was",r(14,21)),("omgordde het opperkleed",r(22,24)),("want hij was naakt",r(25,27)),("en wierp zichzelf in de zee",r(28,33))],
8:[("En de andere discipelen kwamen met het scheepje",r(0,6)),("want zij waren niet verre van het land",r(7,13)),("maar ongeveer tweehonderd ellen",r(14,18)),("slepende het net met de vissen",r(19,23))],
9:[("Als zij dan aan het land gegaan waren",r(0,5)),("zagen zij een kolenvuur liggen",r(6,8)),("en vis daarop liggen",r(9,11)),("en brood",r(12,13))],
10:[("Jezus zei tot hen",r(0,3)),("Breng van de vissen, die u nu gevangen hebt",r(4,10))],}
S.update({
11:[("Simon Petrus ging op",r(0,2)),("en trok het net op het land",r(3,9)),("vol grote vissen",r(10,12)),("tot honderd drie en vijftig",r(13,14)),("en hoewel er zovele waren",r(15,17)),("zo scheurde het net niet",r(18,21))],
12:[("Jezus zei tot hen",r(0,3)),("Kom herwaarts, houdt het middagmaal",r(4,5)),("En niemand van de discipelen durfde Hem vragen",r(6,12)),("Wie bent U",r(13,15)),("wetende, dat het de Heere was",r(16,20))],
13:[("Jezus dan kwam",r(0,3)),("en nam het brood",r(4,7)),("en gaf het hun",r(8,10)),("en de vis evenzo",r(11,14))],
14:[("Dit was nu de derde maal",r(0,2)),("dat Jezus Zijn discipelen geopenbaard is",r(3,8)),("nadat Hij van de doden opgewekt was",r(9,11))],
15:[("Toen zij dan het middagmaal gehouden hadden",r(0,2)),("zei Jezus tot Simon Petrus",r(3,8)),("Simon, zoon van Jonas, hebt u Mij liever dan deze",r(9,14)),("Hij zei tot Hem",r(15,16)),("Ja, Heere! U weet, dat ik U liefheb",r(17,23)),("Hij zei tot hem",r(24,25)),("Weid Mijn lammeren",r(26,29))],
16:[("Hij zei opnieuw tot hem ten tweede maal",r(0,3)),("Simon, zoon van Jonas, hebt u Mij lief",r(4,7)),("Hij zei tot Hem",r(8,9)),("Ja, Heere, U weet, dat ik U liefheb",r(10,16)),("Hij zei tot hem",r(17,18)),("Hoed Mijn schapen",r(19,22))],
17:[("Hij zei tot hem ten derden maal",r(0,3)),("Simon, zoon van Jonas, hebt u Mij lief",r(4,7)),("Petrus werd bedroefd",r(8,10)),("omdat Hij ten derden maal tot hem zei: Heb u Mij lief",r(11,17)),("en zei tot Hem",r(18,20)),("Heere! U weet alle dingen, U weet, dat ik U liefheb",r(21,29)),("Jezus zei tot hem",r(30,33)),("Weid Mijn schapen",r(34,37))],
18:[("Voorwaar, voorwaar, zeg Ik u",r(0,3)),("Toen u jonger was, gordde u uzelf, en wandelde, alwaar u wilde",r(4,12)),("maar wanneer u zult oud geworden zijn",r(13,15)),("zo zult u uw handen uitstrekken",r(16,19)),("en een ander zal u gorden, en brengen",r(20,25)),("waar u niet wilt",r(26,28))],
19:[("En dit zei Hij, betekenende, met wat voor dood hij God verheerlijken zou",r(0,8)),("En dit gesproken hebbende, zei Hij tot hem",r(9,13)),("Volg Mij",r(14,15))],
20:[("En Petrus, zich omkerende",r(0,3)),("zag de discipel volgen, wie Jezus liefhad",r(4,11)),("die ook in het avondmaal op Zijn borst gevallen was",r(12,21)),("en gezegd had: Heere! wie is het, die U verraden zal",r(22,29))],
})
S.update({
21:[("Als Petrus deze zag, zei hij tot Jezus: Heere, maar wat zal deze",r(0,10))],
22:[("Jezus zei tot hem",r(0,3)),("Als Ik wil, dat hij blijft, totdat Ik komt",r(4,10)),("wat gaat het u aan",r(11,13)),("Volg u Mij",r(14,15))],
23:[("Dit woord dan ging uit onder de broeders, dat deze discipel niet zou sterven",r(0,13)),("En Jezus had tot hem niet gezegd",r(14,19)),("dat hij niet sterven zou",r(20,22)),("maar: Als Ik wil, dat hij blijft, totdat Ik komt, wat gaat het u aan",r(23,32))],
24:[("Deze is de discipel, die van deze dingen getuigt, en deze dingen geschreven heeft",r(0,10)),("en wij weten, dat zijn getuigenis waarachtig is",r(11,18))],
25:[("En er zijn nog vele andere dingen, die Jezus gedaan heeft",r(0,8)),("die, zo zij elk bijzonder geschreven werden",r(9,15)),("ik acht, dat ook de de wereld zelf de geschrevene boeken niet zou bevatten. Amen",r(16,23))],
})
def build(u,o,w=False):
 src=load_tr_chapter(u,o,chapter=21,osis_book='John');p=ROOT/'data/johannes/21.json';d=json.loads(p.read_text(encoding='utf-8'));reviewed_through=max(S);rev={'book':'johannes','chapter':21,'reviewed_through':reviewed_through,'verses':{}}
 for v in d['verses'][:reviewed_through]:
  n=int(v['number']);ts=src[n];gs=S[n];ids=[i for _,x in gs for i in x]
  if sorted(ids)!=list(range(len(ts))) or len(ids)!=len(set(ids)):raise ValueError(n)
  v['grondtekst']=[{'woord':t['woord'],'strongs':t['display_strong'],'lemma_strongs':t['lemma_strong'],'morfologie':t['morphology'],**({'tvm':t['tvm']} if t.get('tvm') else {})} for t in ts];v['woordnummers']=[mapping(a,x,ts,n) for a,x in gs];occ={}
  for x in v['woordnummers']:occ[x['tekst']]=occ.get(x['tekst'],0)+1;x['voorkomen']=occ[x['tekst']];x['herkomst']['referentie']=f'JHN 21:{n}'
  rev['verses'][str(n)]=[{'tekst':a,'bronindices':x,'reviewstatus':'handmatig_gecontroleerd'} for a,x in gs]
 if w:
  p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');(ROOT/'data/woordnummers-review/johannes-21.json').write_text(json.dumps(rev,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');ip=ROOT/'data/woordnummers-inline/johannes.json';z=json.loads(ip.read_text(encoding='utf-8'));z['chapters']['21']={str(v['number']):v['woordnummers'] for v in d['verses'][:reviewed_through]};ip.write_text(json.dumps(z,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 return {'verses':reviewed_through,'tokens':sum(len(src[n]) for n in range(1,reviewed_through+1))}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--utr',type=Path,required=True);p.add_argument('--osis',type=Path,required=True);p.add_argument('--write',action='store_true');a=p.parse_args();print(build(a.utr,a.osis,a.write))
