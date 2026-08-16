#!/usr/bin/env python3
"""Publiceer gecontroleerde TR-koppelingen voor Johannes 16 in versbatches."""
from __future__ import annotations
import argparse,json
from pathlib import Path
from rebuild_nt_tr_strongs import load_tr_chapter
from rebuild_johannes2_tr_strongs import mapping,r
ROOT=Path(__file__).resolve().parents[1]
S={
1:[("Deze dingen heb Ik tot u gesproken",r(0,2)),("opdat u niet ten val komt",r(3,5))],
2:[("Zij zullen u uit de synagogen werpen",r(0,2)),("ja, het uur komt",r(3,5)),("dat ieder, die u zal doden",r(6,10)),("zal menen voor God een dienst te doen",r(11,15))],
3:[("En deze dingen zullen zij u doen",r(0,3)),("omdat zij de Vader niet gekend hebben",r(4,8)),("noch Mij",r(9,10))],
4:[("Maar deze dingen heb Ik tot u gesproken",r(0,3)),("opdat, wanneer het uur zal gekomen zijn",r(4,8)),("u deze mag gedenken",r(9,10)),("dat Ik ze u gezegd heb",r(11,14)),("maar deze dingen heb Ik u van het begin niet gezegd",r(15,21)),("omdat Ik bij u was",r(22,25))],
5:[("En nu ga Ik heen tot Degene, die Mij gezonden heeft",r(0,6)),("en niemand van u vraagt Mij",r(7,12)),("Waar gaat U heen",r(13,14))],
6:[("Maar omdat Ik deze dingen tot u gesproken heb",r(0,4)),("zo heeft de verdriet uw hart vervuld",r(5,10))],
7:[("Maar Ik zeg u de waarheid",r(0,5)),("Het is u nut, dat Ik wegga",r(6,10)),("want als Ik niet wegga",r(11,14)),("zo zal de Trooster tot u niet komen",r(15,20)),("maar als Ik heenga",r(21,23)),("zo zal Ik Hem tot u zenden",r(24,27))],
8:[("En Die gekomen zijnde",r(0,2)),("zal de wereld overtuigen van zonde",r(3,7)),("en van gerechtigheid",r(8,10)),("en van oordeel",r(11,13))],
9:[("Van zonde",r(0,2)),("omdat zij in Mij niet geloven",r(3,7))],
10:[("En van gerechtigheid",r(0,2)),("omdat Ik tot Mijn Vader heenga",r(3,8)),("en u zult Mij niet meer zien",r(9,13))],}
S.update({
11:[("En van oordeel",r(0,2)),("omdat de overste van deze wereld geoordeeld is",r(3,9))],
12:[("Nog vele dingen heb Ik u te zeggen",r(0,4)),("maar u kunt die nu niet dragen",r(5,9))],
13:[("Maar wanneer Die zal gekomen zijn",r(0,3)),("namelijk de Geest van de waarheid",r(4,7)),("Hij zal u in al de waarheid leiden",r(8,13)),("want Hij zal van Zichzelf niet spreken",r(14,18)),("maar zo wat Hij zal gehoord hebben, zal Hij spreken",r(19,23)),("en de toekomende dingen zal Hij u verkondigen",r(24,28))],
14:[("Die zal Mij verheerlijken",r(0,2)),("want Hij zal het uit het Mijne nemen",r(3,7)),("en zal het u verkondigen",r(8,10))],
15:[("Al wat de Vader heeft, is van Mij",r(0,6)),("daarom heb Ik gezegd",r(7,9)),("dat Hij het uit het Mijne zal nemen",r(10,14)),("en u verkondigen",r(15,17))],
16:[("Een kleine tijd, en u zult Mij niet zien",r(0,4)),("en opnieuw een kleine tijd, en u zult Mij zien",r(5,10)),("want Ik ga heen tot de Vader",r(11,16))],
17:[("Sommigen dan uit Zijn discipelen zeiden tot elkaar",r(0,7)),("Wat is dit, dat Hij tot ons zegt",r(8,13)),("Een kleine tijd, en u zult Mij niet zien",r(14,18)),("en opnieuw een kleine tijd, en u zult Mij zien",r(19,24)),("en: Want Ik ga heen tot de Vader",r(25,31))],
18:[("Zij zeiden dan",r(0,1)),("Wat is dit, dat Hij zegt",r(2,6)),("Een kleine tijd",r(7,8)),("Wij weten niet, wat Hij zegt",r(9,12))],
19:[("Jezus dan bekende",r(0,3)),("dat zij Hem wilden vragen",r(4,7)),("en zei tot hen",r(8,10)),("Vraagt u daarvan onder elkaar",r(11,15)),("dat Ik gezegd heb",r(16,17)),("Een kleine tijd, en u zult Mij niet zien",r(18,22)),("en opnieuw een kleine tijd, en u zult Mij zien",r(23,28))],
20:[("Voorwaar, voorwaar, Ik zeg u",r(0,3)),("dat u zult huilen, en klagelijk huilen",r(4,8)),("maar de wereld zal zich verblijden",r(9,12)),("en u zult bedroefd zijn",r(13,15)),("maar uw verdriet zal tot blijdschap worden",r(16,22))],
21:[("Een vrouw, wanneer zij baart",r(0,3)),("heeft verdriet",r(4,5)),("omdat haar uur gekomen is",r(6,10)),("maar wanneer zij het kind gebaard heeft",r(11,15)),("zo gedenkt zij de benauwdheid niet meer",r(16,20)),("om de blijdschap",r(21,23)),("dat een mens ter wereld geboren is",r(24,29))],
22:[("En u dan hebt nu wel verdriet",r(0,6)),("maar Ik zal u opnieuw zien",r(7,10)),("en uw hart zal zich verblijden",r(11,15)),("en niemand zal uw blijdschap van u wegnemen",r(16,23))],
23:[("En in die dag zult u Mij niets vragen",r(0,8)),("Voorwaar, voorwaar Ik zeg u",r(9,12)),("Al wat u de Vader zult bidden in Mijn Naam",r(13,22)),("dat zal Hij u geven",r(23,24))],
24:[("Tot nog toe hebt u niet gebeden in Mijn Naam",r(0,8)),("bid, en u zult ontvangen",r(9,11)),("opdat uw blijdschap vervuld zij",r(12,17))],
25:[("Deze dingen heb Ik door gelijkenissen tot u gesproken",r(0,4)),("maar het uur komt",r(5,7)),("dat Ik niet meer door gelijkenissen tot u spreken zal",r(8,14)),("maar u vrijuit van de Vader zal verkondigen",r(15,21))],
26:[("In die dag zult u in Mijn Naam bidden",r(0,8)),("en Ik zeg u niet",r(9,12)),("dat Ik de Vader voor u bidden zal",r(13,19))],
27:[("Want de Vader Zelf heeft u lief",r(0,5)),("omdat u Mij liefgehad hebt",r(6,9)),("en hebt geloofd",r(10,11)),("dat Ik van God ben uitgegaan",r(12,17))],
28:[("Ik ben van de Vader uitgegaan",r(0,3)),("en ben in de wereld gekomen",r(4,8)),("opnieuw verlaat Ik de wereld",r(9,12)),("en ga heen tot de Vader",r(13,17))],
29:[("Zijn discipelen zeiden tot Hem",r(0,4)),("Zie, nu spreekt U vrijuit",r(5,8)),("en zegt geen gelijkenis",r(9,12))],
30:[("Nu weten wij, dat U alle dingen weet",r(0,4)),("en U hebt niet nodig",r(5,8)),("dat U iemand vrage",r(9,12)),("Hierom geloven wij",r(13,15)),("dat U van God uitgegaan bent",r(16,19))],
31:[("Jezus antwoordde hun",r(0,3)),("Gelooft u nu",r(4,5))],
32:[("Zie, het uur komt, en is nu gekomen",r(0,5)),("dat u zult verstrooid worden",r(6,7)),("ieder naar het zijne",r(8,11)),("en u Mij alleen zult laten",r(12,15)),("en toch ben Ik niet alleen",r(16,19)),("want de Vader is met Mij",r(20,25))],
33:[("Deze dingen heb Ik tot u gesproken",r(0,2)),("opdat u in Mij vrede hebt",r(3,7)),("In de wereld zult u verdrukking hebben",r(8,12)),("maar hebt goede moed",r(13,14)),("Ik heb de wereld overwonnen",r(15,18))],
})
def build(u,o,w=False):
 src=load_tr_chapter(u,o,chapter=16,osis_book='John');p=ROOT/'data/johannes/16.json';d=json.loads(p.read_text(encoding='utf-8'));reviewed_through=max(S);rev={'book':'johannes','chapter':16,'reviewed_through':reviewed_through,'verses':{}}
 for v in d['verses'][:reviewed_through]:
  n=int(v['number']);ts=src[n];gs=S[n];ids=[i for _,x in gs for i in x]
  if sorted(ids)!=list(range(len(ts))) or len(ids)!=len(set(ids)):raise ValueError(n)
  v['grondtekst']=[{'woord':t['woord'],'strongs':t['display_strong'],'lemma_strongs':t['lemma_strong'],'morfologie':t['morphology'],**({'tvm':t['tvm']} if t.get('tvm') else {}),**({'bronstatus':t['bronstatus']} if t.get('bronstatus') else {})} for t in ts];v['woordnummers']=[mapping(a,x,ts,n) for a,x in gs];occ={}
  for x in v['woordnummers']:occ[x['tekst']]=occ.get(x['tekst'],0)+1;x['voorkomen']=occ[x['tekst']];x['herkomst']['referentie']=f'JHN 16:{n}'
  rev['verses'][str(n)]=[{'tekst':a,'bronindices':x,'reviewstatus':'handmatig_gecontroleerd'} for a,x in gs]
 if w:
  p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');(ROOT/'data/woordnummers-review/johannes-16.json').write_text(json.dumps(rev,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');ip=ROOT/'data/woordnummers-inline/johannes.json';z=json.loads(ip.read_text(encoding='utf-8'));z['chapters']['16']={str(v['number']):v['woordnummers'] for v in d['verses'][:reviewed_through]};ip.write_text(json.dumps(z,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 return {'verses':reviewed_through,'tokens':sum(len(src[n]) for n in range(1,reviewed_through+1))}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--utr',type=Path,required=True);p.add_argument('--osis',type=Path,required=True);p.add_argument('--write',action='store_true');a=p.parse_args();print(build(a.utr,a.osis,a.write))
