#!/usr/bin/env python3
"""Publiceer gecontroleerde TR-koppelingen voor Johannes 15 in versbatches."""
from __future__ import annotations
import argparse,json
from pathlib import Path
from rebuild_nt_tr_strongs import load_tr_chapter
from rebuild_johannes2_tr_strongs import mapping,r
ROOT=Path(__file__).resolve().parents[1]
S={
1:[("Ik ben de ware Wijnstok",r(0,5)),("en Mijn Vader is de Landman",r(6,12))],
2:[("Alle rank, die in Mij geen vrucht draagt",r(0,6)),("die neemt Hij weg",r(7,8)),("en al wie vrucht draagt",r(9,13)),("die reinigt Hij",r(14,15)),("opdat zij meer vrucht drage",r(16,19))],
3:[("U bent nu rein",r(0,3)),("om het woord, dat Ik tot u gesproken heb",r(4,9))],
4:[("Blijf in Mij",r(0,2)),("en Ik in u",r(3,5)),("Zoals de rank geen vrucht kan dragen van zichzelf",r(6,14)),("zo zij niet in de wijnstok blijft",r(15,20)),("zo ook u niet",r(21,23)),("zo u in Mij niet blijft",r(24,28))],
5:[("Ik ben de Wijnstok",r(0,3)),("en u de ranken",r(4,6)),("die in Mij blijft",r(7,10)),("en Ik in hem",r(11,13)),("die draagt veel vrucht",r(14,17)),("want zonder Mij kunt u niets doen",r(18,24))],
6:[("Zo iemand in Mij niet blijft",r(0,5)),("die is buiten geworpen",r(6,7)),("zoals de rank",r(8,10)),("en is verdord",r(11,12)),("en men verzamelt deze",r(13,15)),("en men werpt ze in het vuur",r(16,19)),("en zij worden verbrand",r(20,21))],
7:[("Als u in Mij blijft",r(0,3)),("en Mijn woorden in u blijven",r(4,10)),("zo wat u wilt",r(11,13)),("zult u begeren",r(14)),("en het zal u gebeuren",r(15,17))],
8:[("Hierin is Mijn Vader verheerlijkt",r(0,5)),("dat u veel vrucht draagt",r(6,9)),("en u zult Mijn discipelen zijn",r(10,13))],
9:[("Zoals de Vader Mij liefgehad heeft",r(0,4)),("heb Ik ook u liefgehad",r(5,7)),("blijf in deze Mijn liefde",r(8,13))],
10:[("Als u Mijn geboden bewaart",r(0,4)),("zo zult u in Mijn liefde blijven",r(5,9)),("zoals Ik de geboden van Mijn Vader bewaard heb",r(10,17)),("en blijf in Zijn liefde",r(18,23))],}
S.update({
11:[("Deze dingen heb Ik tot u gesproken",r(0,2)),("opdat Mijn blijdschap in u blijft",r(3,10)),("en uw blijdschap vervuld wordt",r(11,15))],
12:[("Dit is Mijn gebod",r(0,5)),("dat u elkaar liefhebt",r(6,8)),("zoals Ik u liefgehad heb",r(9,11))],
13:[("Niemand heeft meerder liefde dan deze",r(0,4)),("dat iemand zijn leven zette voor zijn vrienden",r(5,14))],
14:[("U bent Mijn vrienden",r(0,3)),("zo u doet wat Ik u gebied",r(4,9))],
15:[("Ik heet u niet meer dienaren",r(0,3)),("want de dienaar weet niet, wat zijn heer doet",r(4,13)),("maar Ik heb u vrienden genoemd",r(14,17)),("want al wat Ik van Mijn Vader gehoord heb",r(18,25)),("dat heb Ik u bekend gemaakt",r(26,27))],
16:[("U hebt Mij niet uitverkoren",r(0,3)),("maar Ik heb u uitverkoren",r(4,7)),("en Ik heb u gesteld",r(8,10)),("dat u zou heengaan en vrucht dragen",r(11,16)),("en dat uw vrucht blijft",r(17,21)),("opdat, zo wat u van de Vader begeren zult in Mijn Naam",r(22,32)),("Hij u dat geeft",r(33,34))],
17:[("Dit gebied Ik u",r(0,2)),("opdat u elkaar liefhebt",r(3,5))],
18:[("Als u de wereld haat",r(0,4)),("zo weet",r(5)),("dat zij Mij eer dan u gehaat heeft",r(6,10))],
19:[("Als u van de wereld was",r(0,4)),("zo zou de wereld het haar liefhebben",r(5,10)),("maar omdat u van de wereld niet bent",r(11,17)),("maar Ik u uit de wereld heb uitverkoren",r(18,24)),("daarom haat u de wereld",r(25,30))],
20:[("Gedenk van het woord, dat Ik u gezegd heb",r(0,6)),("Een dienaar is niet meerder dan zijn heer",r(7,13)),("Als zij Mij vervolgd hebben",r(14,16)),("zij zullen ook u vervolgen",r(17,19)),("als zij Mijn woord bewaard hebben",r(20,24)),("zij zullen ook het uwe bewaren",r(25,28))],
21:[("Maar al deze dingen zullen zij doen",r(0,4)),("omwille van Mijn Naam",r(5,8)),("omdat zij Hem niet kennen, Die Mij gezonden heeft",r(9,14))],
22:[("Als Ik niet gekomen was, en tot hen gesproken had",r(0,5)),("zij hadden geen zonde",r(6,8)),("maar nu hebben zij geen voorwendsel voor hun zonde",r(9,17))],
23:[("Die Mij haat",r(0,2)),("die haat ook Mijn Vader",r(3,7))],
24:[("Als Ik de werken onder hen niet had gedaan",r(0,6)),("die niemand anders gedaan heeft",r(7,10)),("zij hadden geen zonde",r(11,13)),("maar nu hebben zij ze gezien",r(14,17)),("en zowel Mij als Mijn Vader gehaat",r(18,25))],
25:[("Maar dit gebeurt, opdat het woord vervuld wordt",r(0,4)),("dat in hun wet geschreven is",r(5,10)),("Zij hebben mij zonder oorzaak gehaat",r(11,14))],
26:[("Maar wanneer de Trooster zal gekomen zijn",r(0,4)),("Die Ik u zenden zal van de Vader",r(5,11)),("namelijk de Geest van de waarheid",r(12,15)),("Die van de Vader uitgaat",r(16,20)),("Die zal van Mij getuigen",r(21,24))],
27:[("En u zult ook getuigen",r(0,3)),("want u bent van de beginne met Mij geweest",r(4,9))],
})
def build(u,o,w=False):
 src=load_tr_chapter(u,o,chapter=15,osis_book='John');p=ROOT/'data/johannes/15.json';d=json.loads(p.read_text(encoding='utf-8'));reviewed_through=max(S);rev={'book':'johannes','chapter':15,'reviewed_through':reviewed_through,'verses':{}}
 for v in d['verses'][:reviewed_through]:
  n=int(v['number']);ts=src[n];gs=S[n];ids=[i for _,x in gs for i in x]
  if sorted(ids)!=list(range(len(ts))) or len(ids)!=len(set(ids)):raise ValueError(n)
  v['grondtekst']=[{'woord':t['woord'],'strongs':t['display_strong'],'lemma_strongs':t['lemma_strong'],'morfologie':t['morphology'],**({'tvm':t['tvm']} if t.get('tvm') else {}),**({'bronstatus':t['bronstatus']} if t.get('bronstatus') else {})} for t in ts];v['woordnummers']=[mapping(a,x,ts,n) for a,x in gs];occ={}
  for x in v['woordnummers']:occ[x['tekst']]=occ.get(x['tekst'],0)+1;x['voorkomen']=occ[x['tekst']];x['herkomst']['referentie']=f'JHN 15:{n}'
  rev['verses'][str(n)]=[{'tekst':a,'bronindices':x,'reviewstatus':'handmatig_gecontroleerd'} for a,x in gs]
 if w:
  p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');(ROOT/'data/woordnummers-review/johannes-15.json').write_text(json.dumps(rev,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');ip=ROOT/'data/woordnummers-inline/johannes.json';z=json.loads(ip.read_text(encoding='utf-8'));z['chapters']['15']={str(v['number']):v['woordnummers'] for v in d['verses'][:reviewed_through]};ip.write_text(json.dumps(z,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 return {'verses':reviewed_through,'tokens':sum(len(src[n]) for n in range(1,reviewed_through+1))}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--utr',type=Path,required=True);p.add_argument('--osis',type=Path,required=True);p.add_argument('--write',action='store_true');a=p.parse_args();print(build(a.utr,a.osis,a.write))
