#!/usr/bin/env python3
"""Publiceer handmatig beoordeelde TR-koppelingen voor Mattheüs 6."""
from __future__ import annotations
import argparse,json
from pathlib import Path
from rebuild_nt_tr_strongs import load_tr_chapter
from rebuild_johannes2_tr_strongs import mapping,r
ROOT=Path(__file__).resolve().parents[1]
S={
1:[("Heb acht, dat u uw aalmoes niet doet voor de mensen, om van hen gezien te worden",r(0,12)),("anders zo hebt u geen loon bij uw Vader, Die in de hemelen is",r(13,26))],
2:[("Wanneer u dan aalmoes doet, zo laat voor u niet trompetten",r(0,7)),("gelijk de huichelaars in de synagogen en op de straten doen",r(8,18)),("opdat zij van de mensen geëerd mogen worden",r(19,23)),("Voorwaar zeg Ik u: Zij hebben hun loon weg",r(24,30))],
3:[("Maar als u aalmoes doet",r(0,3)),("zo laat uw linkerhand niet weten, wat uw rechter doet",r(4,13))],
4:[("Opdat uw aalmoes in het verborgen zij",r(0,7)),("en uw Vader, Die in het verborgen ziet",r(8,16)),("Die zal het u in het openbaar vergelden",r(17,22))],
5:[("En wanneer u bidt, zo zult u niet zijn gelijk de huichelaars",r(0,7)),("want die plegen graag, in de synagogen en op de hoeken van de straten staande, te bidden",r(8,20)),("opdat zij van de mensen mogen gezien worden",r(21,25)),("Voorwaar, Ik zeg u, dat zij hun loon weg hebben",r(26,33))],
6:[("Maar u, wanneer u bidt",r(0,3)),("gaat in uw binnenkamer, en uw deur gesloten hebbende",r(4,13)),("bidt uw Vader, Die in het verborgen is",r(14,21)),("en uw Vader, Die in het verborgen ziet, zal het u in het openbaar vergelden",r(22,35))],
7:[("En als u bidt, zo gebruikt geen ijdel verhaal van woorden, gelijk de heidenen",r(0,6)),("want zij menen, dat zij door hun veelheid van woorden zullen verhoord worden",r(7,14))],
8:[("Wordt dan hun niet gelijk",r(0,3)),("want uw Vader weet, wat u nodig hebt, voordat u Hem bidt",r(4,16))],
9:[("U dan bidt zo",r(0,3)),("Onze Vader, Die in de hemelen bent",r(4,9)),("Uw Naam worde geheiligd",r(10,13))],
10:[("Uw Koninkrijk kome",r(0,3)),("Uw wil gebeure, gelijk in de hemel zo ook op de aarde",r(4,14))],
}
S.update({
11:[("Geef ons vandaag ons dagelijks brood",r(0,7))],
12:[("En vergeef ons onze schulden",r(0,5)),("gelijk ook wij vergeven onze schuldenaren",r(6,12))],
13:[("En leid ons niet in verzoeking",r(0,5)),("maar verlos ons van de boze",r(6,11)),("Want Uw is het Koninkrijk, en de kracht, en de heerlijkheid, in de eeuwigheid, amen",r(12,26))],
14:[("Want als u de mensen hun misdaden vergeeft",r(0,7)),("zo zal uw hemelse Vader ook u vergeven",r(8,15))],
15:[("Maar als u de mensen hun misdaden niet vergeeft",r(0,8)),("zo zal ook uw Vader uw misdaden niet vergeven",r(9,16))],
16:[("En wanneer u vast, toont geen droevig gezicht, gelijk de huichelaars",r(0,8)),("want zij mismaken hun gezichten",r(9,13)),("opdat zij van de mensen mogen gezien worden, als zij vasten",r(14,18)),("Voorwaar, Ik zeg u, dat zij hun loon weg hebben",r(19,26))],
17:[("Maar u, als u vast",r(0,2)),("zalft uw hoofd",r(3,6)),("en wast uw aangezicht",r(7,11))],
18:[("Opdat het van de mensen niet gezien wordt, als u vast",r(0,5)),("maar van uw Vader, Die in het verborgen is",r(6,13)),("en uw Vader, Die in het verborgen ziet, zal het u in het openbaar vergelden",r(14,27))],
19:[("Verzamelt u geen schatten op de aarde",r(0,6)),("waar ze de mot en de roest verderft",r(7,11)),("en waar de dieven doorgraven en stelen",r(12,17))],
20:[("Maar verzamelt u schatten in de hemel",r(0,5)),("waar ze noch mot noch roest verderft",r(6,11)),("en waar de dieven niet doorgraven noch stelen",r(12,18))],
})
S.update({
21:[("Want waar uw schat is, daar zal ook uw hart zijn",r(0,11))],
22:[("De kaars van het lichaam is het oog",r(0,6)),("als dan uw oog eenvoudig is",r(7,13)),("zo zal uw hele lichaam verlicht wezen",r(14,19))],
23:[("Maar als uw oog boos is, zo zal geheel uw lichaam duister zijn",r(0,12)),("Als dan het licht, dat in u is, duisternis is",r(13,21)),("hoe groot zal de duisternis zelf zijn",r(22,24))],
24:[("Niemand kan twee heren dienen",r(0,4)),("want of hij zal de één haten en de anderen liefhebben",r(5,13)),("of hij zal de één aanhangen en de anderen verachten",r(14,20)),("u kunt niet God dienen en de mammon",r(21,26))],
25:[("Daarom zeg Ik u",r(0,3)),("Wees niet bezorgd voor uw leven, wat u eten, en wat u drinken zult",r(4,13)),("noch voor uw lichaam, waarmee u zich kleden zult",r(14,19)),("is het leven niet meer dan het voedsel, en het lichaam dan de kleding",r(20,31))],
26:[("Aanziet de vogels des hemels",r(0,5)),("dat zij niet zaaien, noch maaien, noch verzamelen in de schuren",r(6,14)),("en uw hemelse Vader voedt toch dezelfde",r(15,22)),("gaat u dezelfde niet zeer veel te boven",r(23,27))],
27:[("Wie toch van u kan, met bezorgd te zijn, een el tot zijn lengte toedoen",r(0,12))],
28:[("En wat bent u bezorgd voor de kleding",r(0,4)),("Let op de leliën van het veld, hoe zij groeien",r(5,11)),("zij arbeiden niet, en spinnen niet",r(12,15))],
29:[("En Ik zeg u, dat ook Salomo, in al zijn heerlijkheid, niet is bekleed geweest",r(0,11)),("gelijk één van deze",r(12,14))],
30:[("Als nu God het gras van het veld, dat vandaag is, en morgen in de oven geworpen wordt, zo bekleedt",r(0,16)),("zal Hij u niet veel meer kleden, u kleingelovigen",r(17,21))],
31:[("Daarom wees niet bezorgd, zeggende",r(0,3)),("Wat zullen wij eten, of wat zullen wij drinken, of waarmee zullen wij ons kleden",r(4,11))],
32:[("Want al deze dingen zoeken de heidenen",r(0,5)),("want uw hemelse Vader weet, dat u al deze dingen nodig hebt",r(6,16))],
33:[("Maar zoekt eerst het Koninkrijk van God en Zijn gerechtigheid",r(0,10)),("en al deze dingen zullen u toegeworpen worden",r(11,15))],
34:[("Wees dan niet bezorgd tegen de morgen",r(0,5)),("want de morgen zal voor het zijne zorgen",r(6,11)),("elke dag heeft genoeg aan zijn eigen kwaad",r(12,17))],
})
def build(u,o,w=False):
 src=load_tr_chapter(u,o,chapter=6,osis_book='Matt');p=ROOT/'data/mattheus/6.json';d=json.loads(p.read_text(encoding='utf-8'));reviewed_through=max(S);rev={'book':'mattheus','chapter':6,'reviewed_through':reviewed_through,'verses':{}}
 for v in d['verses'][:reviewed_through]:
  n=int(v['number']);ts=src[n];gs=S[n];ids=[i for _,x in gs for i in x]
  if sorted(ids)!=list(range(len(ts))) or len(ids)!=len(set(ids)):raise ValueError(n)
  v['grondtekst']=[{'woord':t['woord'],'strongs':t['display_strong'],'lemma_strongs':t['lemma_strong'],'morfologie':t['morphology'],**({'tvm':t['tvm']} if t.get('tvm') else {})} for t in ts];v['woordnummers']=[mapping(a,x,ts,n) for a,x in gs];occ={}
  for x in v['woordnummers']:occ[x['tekst']]=occ.get(x['tekst'],0)+1;x['voorkomen']=occ[x['tekst']];x['herkomst']['referentie']=f'MAT 6:{n}'
  rev['verses'][str(n)]=[{'tekst':a,'bronindices':x,'reviewstatus':'handmatig_gecontroleerd'} for a,x in gs]
 if w:
  p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');(ROOT/'data/woordnummers-review/mattheus-6.json').write_text(json.dumps(rev,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');ip=ROOT/'data/woordnummers-inline/mattheus.json';z=json.loads(ip.read_text(encoding='utf-8'));z['chapters']['6']={str(v['number']):v['woordnummers'] for v in d['verses'][:reviewed_through]};ip.write_text(json.dumps(z,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 return {'verses':reviewed_through,'tokens':sum(len(src[n]) for n in range(1,reviewed_through+1))}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--utr',type=Path,required=True);p.add_argument('--osis',type=Path,required=True);p.add_argument('--write',action='store_true');a=p.parse_args();print(build(a.utr,a.osis,a.write))
