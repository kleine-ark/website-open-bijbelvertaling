#!/usr/bin/env python3
"""Publiceer handmatig beoordeelde TR-koppelingen voor Mattheüs 10."""
from __future__ import annotations
import argparse,json
from pathlib import Path
from rebuild_nt_tr_strongs import load_tr_chapter
from rebuild_johannes2_tr_strongs import mapping,r
ROOT=Path(__file__).resolve().parents[1]
S={
1:[("En Zijn twaalf discipelen tot Zich geroepen hebbende",r(0,5)),("heeft Hij hun macht gegeven over de onreine geesten",r(6,10)),("om hen uit te werpen",r(11,13)),("en om alle ziekte en alle kwalen te genezen",r(14,20))],
2:[("De namen nu van de twaalf apostelen zijn deze",r(0,7)),("de eerste, Simon, gezegd Petrus, en Andreas, zijn broer",r(8,17)),("Jakobus, de zoon van Zebedeüs, en Johannes, zijn broer",r(18,26))],
3:[("Filippus en Bartholomeüs",r(0,2)),("Thomas en Mattheüs, de tollenaar",r(3,7)),("Jakobus, de zoon van Alfeüs, en Lebbeüs, toegenaamd Thaddeüs",r(8,16))],
4:[("Simon Kananites, en Judas Iskariot",r(0,5)),("die Hem ook verraden heeft",r(6,9))],
5:[("Deze twaalf heeft Jezus uitgezonden, en hun bevel gegeven, zeggende",r(0,8)),("U zult niet heengaan op de weg van de heidenen",r(9,13)),("en u zult niet ingaan in enige stad van de Samaritanen",r(14,19))],
6:[("Maar gaat veel meer heen tot de verloren schapen van het huis van Israël",r(0,9))],
7:[("En heengaande predikt, zeggende",r(0,3)),("Het Koninkrijk van de hemelen is nabij gekomen",r(4,9))],
8:[("Genees de zieken; reinig de melaatsen; wekt de doden op; werp de demonen uit",r(0,7)),("U hebt het om niet ontvangen, geeft het om niet",r(8,11))],
9:[("Verkrijgt u noch goud, noch zilver, noch koper geld in uw gordels",r(0,10))],
10:[("Noch reiszak tot de weg, noch twee rokken, noch schoenen, noch staf",r(0,10)),("want de arbeider is zijn voedsel waard",r(11,18))],
}
S.update({
11:[("En in wat stad of plaats u zult inkomen",r(0,7)),("onderzoekt, wie daarin waard is",r(8,13)),("en blijft daar, totdat u daar uitgaat",r(14,18))],
12:[("En als u in het huis gaat, zo groet hetzelfde",r(0,6))],
13:[("En als dat huis waard is, zo kome uw vrede over hetzelfde",r(0,12)),("maar als het niet waard is, zo kere uw vrede weer tot u",r(13,23))],
14:[("En zo iemand u niet zal ontvangen, noch uw woorden horen",r(0,10)),("uitgaande uit dat huis of daaruit stad",r(11,17)),("schudt het stof van uw voeten af",r(18,23))],
15:[("Voorwaar zeg Ik u",r(0,2)),("Het zal de lande van Sodom en Gomorra verdragelijker zijn in de dag van het oordeel, dan die stad",r(3,15))],
16:[("Zie, Ik zend u als schapen in het midden van de wolven",r(0,8)),("wees dan voorzichtig gelijk de slangen",r(9,14)),("en oprecht gelijk de duiven",r(15,19))],
17:[("Maar wees op uw hoede voor de mensen",r(0,4)),("want zij zullen u overleveren in de raadsvergaderingen",r(5,9)),("en in hun synagogen zullen zij u geselen",r(10,16))],
18:[("En u zult ook voor stadhouders en koningen geleid worden",r(0,6)),("om Mijnentwil, hun en de heidenen tot getuigenis",r(7,14))],
19:[("Maar wanneer zij u overleveren",r(0,3)),("zo zult u niet bezorgd zijn, hoe of wat u spreken zult",r(4,9)),("want het zal u op dat moment gegeven worden, wat u spreken zult",r(10,18))],
20:[("Want u bent het niet, die spreekt",r(0,5)),("maar het is de Geest van uw Vader, Die in u spreekt",r(6,15))],
})
S.update({
21:[("En de ene broer zal de andere broer overleveren tot de dood, en de vader het kind",r(0,8)),("en de kinderen zullen opstaan tegen de ouders, en zullen hen doden",r(9,16))],
22:[("En u zult van allen gehaat worden om Mijn Naam",r(0,8)),("maar die volstandig zal blijven tot het einde, die zal zalig worden",r(9,15))],
23:[("Wanneer zij u dan in deze stad vervolgen, vlucht in de andere",r(0,11)),("want werkelijk zeg ik u",r(12,15)),("U zult uw reis door de steden van Israël niet geëindigd hebben, of de Zoon des mensen zal gekomen zijn",r(16,29))],
24:[("De discipel is niet boven de meester, noch de dienaar boven zijn heer",r(0,11))],
25:[("Het zij de discipel genoeg, dat hij wordt zoals zijn meester, en de dienaar zoals zijn heer",r(0,15)),("Als zij de Heere van het huis Beëlzebul hebben geheten, hoeveel te meer Zijn huisgenoten",r(16,25))],
26:[("Vrees dan hen niet",r(0,3)),("want er is niets bedekt, dat niet zal ontdekt worden, en verborgen, dat niet zal geweten worden",r(4,15))],
27:[("Wat Ik u zeg in de duisternis, zegt het in het licht",r(0,9)),("en wat u hoort in het oor, predikt dat op de daken",r(10,19))],
28:[("En vreest u niet voor degenen, die het lichaam doden, en de ziel niet kunnen doden",r(0,13)),("maar vreest veel meer Hem, Die zowel ziel als lichaam kan verderven in de hel",r(14,25))],
29:[("Worden niet twee musjes om een penninkje verkocht",r(0,4)),("En niet één van deze zal op de aarde vallen zonder uw Vader",r(5,17))],
30:[("En ook uw haar van het hoofd zijn alle geteld",r(0,9))],
})
S.update({
31:[("Vrees dan niet; u gaat vele musjes te boven",r(0,6))],
32:[("Ieder dan, die Mij belijden zal voor de mensen",r(0,8)),("die zal Ik ook belijden voor Mijn Vader, Die in de hemelen is",r(9,19))],
33:[("Maar zo wie Mij verloochend zal hebben voor de mensen",r(0,7)),("die zal Ik ook verloochenen voor Mijn Vader, Die in de hemelen is",r(8,17))],
34:[("Denk niet, dat Ik gekomen ben, om vrede te brengen op de aarde",r(0,8)),("Ik ben niet gekomen om vrede te brengen, maar het zwaard",r(9,14))],
35:[("Want Ik ben gekomen, om de mens tweedrachtig te maken tegen zijn vader",r(0,7)),("en de dochter tegen haar moeder",r(8,13)),("en de schoondochter tegen haar schoonmoeder",r(14,19))],
36:[("En zij zullen van de mensen vijanden worden, die zijn huisgenoten zijn",r(0,6))],
37:[("Die vader of moeder liefheeft boven Mij, is Mij niet waard",r(0,10)),("en die zoon of dochter liefheeft boven Mij, is Mij niet waard",r(11,22))],
38:[("En die zijn kruis niet op zich neemt, en Mij navolgt, is Mij niet waard",r(0,14))],
39:[("Die zijn ziel vindt, zal dezelfde verliezen",r(0,6)),("en die zijn ziel zal verloren hebben om Mijnentwil, zal dezelfde vinden",r(7,16))],
40:[("Die u ontvangt, ontvangt Mij",r(0,4)),("en die Mij ontvangt, ontvangt Hem, Die Mij gezonden heeft",r(5,12))],
41:[("Die een profeet ontvangt in de naam van de profeten, zal het loon van de profeten ontvangen",r(0,8)),("en die een rechtvaardige ontvangt in de naam van de rechtvaardigen, zal het loon van de rechtvaardigen ontvangen",r(9,18))],
42:[("En zo wie één van deze kleinen te drinken geeft alleen een beker koud water, in de naam van een discipel",r(0,13)),("voorwaar zeg Ik u, hij zal zijn loon in geen geval verliezen",r(14,22))],
})
def build(u,o,w=False):
 src=load_tr_chapter(u,o,chapter=10,osis_book='Matt');p=ROOT/'data/mattheus/10.json';d=json.loads(p.read_text(encoding='utf-8'));reviewed_through=max(S);rev={'book':'mattheus','chapter':10,'reviewed_through':reviewed_through,'verses':{}}
 for v in d['verses'][:reviewed_through]:
  n=int(v['number']);ts=src[n];gs=S[n];ids=[i for _,x in gs for i in x]
  if sorted(ids)!=list(range(len(ts))) or len(ids)!=len(set(ids)):raise ValueError(n)
  v['grondtekst']=[{'woord':t['woord'],'strongs':t['display_strong'],'lemma_strongs':t['lemma_strong'],'morfologie':t['morphology'],**({'tvm':t['tvm']} if t.get('tvm') else {})} for t in ts];v['woordnummers']=[mapping(a,x,ts,n) for a,x in gs];occ={}
  for x in v['woordnummers']:occ[x['tekst']]=occ.get(x['tekst'],0)+1;x['voorkomen']=occ[x['tekst']];x['herkomst']['referentie']=f'MAT 10:{n}'
  rev['verses'][str(n)]=[{'tekst':a,'bronindices':x,'reviewstatus':'handmatig_gecontroleerd'} for a,x in gs]
 if w:
  p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');(ROOT/'data/woordnummers-review/mattheus-10.json').write_text(json.dumps(rev,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');ip=ROOT/'data/woordnummers-inline/mattheus.json';z=json.loads(ip.read_text(encoding='utf-8'));z['chapters']['10']={str(v['number']):v['woordnummers'] for v in d['verses'][:reviewed_through]};ip.write_text(json.dumps(z,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 return {'verses':reviewed_through,'tokens':sum(len(src[n]) for n in range(1,reviewed_through+1))}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--utr',type=Path,required=True);p.add_argument('--osis',type=Path,required=True);p.add_argument('--write',action='store_true');a=p.parse_args();print(build(a.utr,a.osis,a.write))
