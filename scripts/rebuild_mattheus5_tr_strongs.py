#!/usr/bin/env python3
"""Publiceer handmatig beoordeelde TR-koppelingen voor Mattheüs 5."""
from __future__ import annotations
import argparse,json
from pathlib import Path
from rebuild_nt_tr_strongs import load_tr_chapter
from rebuild_johannes2_tr_strongs import mapping,r
ROOT=Path(__file__).resolve().parents[1]
S={
1:[("En Jezus, de menigte ziende",r(0,3)),("is geklommen op een berg",r(4,7)),("en als Hij nedergezeten was",r(8,10)),("kwamen Zijn discipelen tot Hem",r(11,15))],
2:[("En Zijn mond geopend hebbende",r(0,4)),("leerde Hij hen, zeggende",r(5,7))],
3:[("Zalig zijn de armen van geest",r(0,4)),("want van hun is het Koninkrijk van de hemelen",r(5,11))],
4:[("Zalig zijn die treuren",r(0,2)),("want zij zullen vertroost worden",r(3,5))],
5:[("Zalig zijn de zachtmoedigen",r(0,2)),("want zij zullen het aarde beërven",r(3,7))],
}
S.update({
6:[("Zalig zijn die hongeren en dorsten naar de gerechtigheid",r(0,6)),("want zij zullen verzadigd worden",r(7,9))],
7:[("Zalig zijn de barmhartigen",r(0,2)),("want hun zal barmhartigheid bewezen worden",r(3,5))],
8:[("Zalig zijn de reinen van hart",r(0,4)),("want zij zullen God zien",r(5,9))],
9:[("Zalig zijn de vreedzamen",r(0,2)),("want zij zullen Gods kinderen genoemd worden",r(3,7))],
10:[("Zalig zijn die vervolgd worden omwille van de gerechtigheid",r(0,4)),("want van hun is het Koninkrijk van de hemelen",r(5,11))],
11:[("Zalig bent u, als u de mensen smaden, en vervolgen, en liegende alle kwaad tegen u spreken, om Mijnentwil",r(0,16))],
12:[("Verblijd en verheugt u",r(0,2)),("want uw loon is groot in de hemelen",r(3,10)),("want zo hebben zij vervolgd de profeten, die voor u geweest zijn",r(11,18))],
13:[("U bent het zout van de aarde",r(0,5)),("als nu het zout smakeloos wordt, waarmee zal het gezouten worden",r(6,13)),("Het deugt nergens meer toe",r(14,19)),("dan om buiten geworpen, en van de mensen vertreden te worden",r(20,26))],
14:[("U bent het licht van de wereld",r(0,5)),("een stad boven op een berg liggend, kan niet verborgen zijn",r(6,12))],
15:[("Noch steekt men een kaars aan, en zet die onder een korenmaat",r(0,8)),("maar op een kandelaar",r(9,12)),("en zij schijnt allen, die in het huis zijn",r(13,19))],
})
S.update({
16:[("Laat uw licht zo schijnen voor de mensen",r(0,7)),("dat zij uw goede werken mogen zien",r(8,13)),("en uw Vader, Die in de hemelen is, verheerlijken",r(14,22))],
17:[("Denk niet, dat Ik gekomen ben, om de wet of de profeten te ontbinden",r(0,9)),("Ik ben niet gekomen, om die te ontbinden",r(10,12)),("maar te vervullen",r(13,14))],
18:[("Want voorwaar zeg Ik u",r(0,3)),("Totdat de hemel en de aarde voorbijgaan",r(4,11)),("zal er niet één jota noch één tittel van de wet voorbijgaan",r(12,22)),("totdat het alles zal zijn gebeurd",r(23,26))],
19:[("Zo wie dan één van deze minste geboden zal ontbonden, en de mensen zo zal geleerd hebben",r(0,14)),("die zal de minste genoemd worden in het Koninkrijk van de hemelen",r(15,21)),("maar zo wie dezelfde zal gedaan en geleerd hebben",r(22,27)),("die zal groot genoemd worden in het Koninkrijk van de hemelen",r(28,35))],
20:[("Want Ik zeg u",r(0,3)),("Tenzij uw gerechtigheid overvloediger zij, dan van de Schriftgeleerden en van de Farizeën",r(4,14)),("dat u in het Koninkrijk van de hemelen in geen geval zult ingaan",r(15,22))],
21:[("U hebt gehoord, dat tot de ouden gezegd is",r(0,4)),("U zult niet doden",r(5,6)),("maar zo wie doodt, die zal strafbaar zijn door het gericht",r(7,14))],
22:[("Maar Ik zeg u",r(0,4)),("Zo wie te onrecht op zijn broeder boos is, die zal strafbaar zijn door het gericht",r(5,15)),("en wie tot zijn broeder zegt: Raka! die zal strafbaar zijn door de grote raad",r(16,27)),("maar wie zegt: U dwaas! die zal strafbaar zijn door het helse vuur",r(28,39))],
23:[("Zo u dan uw gave zult op het altaar offeren",r(0,8)),("en daar gedachtig wordt, dat uw broeder iets tegen u heeft",r(9,18))],
24:[("Laat daar uw gave voor het altaar",r(0,7)),("en gaat heen, verzoent u eerst met uw broeder",r(8,14)),("en komt dan en offert uw gave",r(15,21))],
25:[("Wees haastig welgezind tegenover uw tegenpartij, terwijl u nog met hem op de weg bent",r(0,13)),("opdat de tegenpartij niet misschien u de rechter overlevere",r(14,20)),("en de rechter u de dienaar overlevere",r(21,27)),("en u in de gevangenis geworpen wordt",r(28,31))],
})
S.update({
26:[("Voorwaar, Ik zeg u",r(0,2)),("U zult daar in geen geval uitkomen",r(3,6)),("voordat u de laatste penning zult betaald hebben",r(7,12))],
27:[("U hebt gehoord, dat van de oude gezegd is",r(0,4)),("U zult geen overspel doen",r(5,6))],
28:[("Maar Ik zeg u",r(0,4)),("dat zo wie een vrouw aan ziet, daarom te begeren",r(5,12)),("die heeft al overspel in zijn hart met haar gedaan",r(13,19))],
29:[("Als dan uw rechteroog u doet struikelen",r(0,8)),("trekt het uit, en werpt het van u",r(9,14)),("want het is u nut, dat één van uw leden verga",r(15,23)),("en niet uw hele lichaam in de hel geworpen wordt",r(24,32))],
30:[("En als uw rechterhand u doet struikelen",r(0,7)),("houwt ze af, en werpt ze van u",r(8,13)),("want het is u nut, dat één van uw leden verga",r(14,22)),("en niet uw hele lichaam in de hel geworpen wordt",r(23,31))],
31:[("Er is ook gezegd",r(0,2)),("Zo wie zijn vrouw verlaten zal",r(3,8)),("die geve haar een scheidbrief",r(9,11))],
32:[("Maar Ik zeg u",r(0,4)),("dat zo wie zijn vrouw verlaten zal, anders dan uit oorzake van hoererij",r(5,13)),("die maakt, dat zij overspel doet",r(14,16)),("en zo wie de verlatene zal trouwen, die doet overspel",r(17,22))],
33:[("Opnieuw hebt u gehoord, dat van de oude gezegd is",r(0,5)),("U zult de eed niet breken",r(6,7)),("maar u zult de Heere uw eden houden",r(8,14))],
34:[("Maar Ik zeg u",r(0,3)),("Zweer geheel niet",r(4,6)),("noch bij de hemel, omdat hij is de troon van God",r(7,15))],
35:[("Noch bij de aarde, omdat zij is de voetbank van Zijn voeten",r(0,9)),("noch bij Jeruzalem, omdat zij is de stad van de grote Koning",r(10,18))],
})
S.update({
36:[("Noch bij uw hoofd zult u zweren",r(0,5)),("omdat u niet één haar kunt wit of zwart maken",r(6,14))],
37:[("Maar laat zijn uw woord ja, ja; neen, neen",r(0,8)),("wat boven deze is, dat is uit de boze",r(9,16))],
38:[("U hebt gehoord, dat gezegd is",r(0,2)),("Oog om oog, en tand om tand",r(3,9))],
39:[("Maar Ik zeg u",r(0,3)),("dat u de boze niet wederstaat",r(4,7)),("maar, zo wie u op de rechterwang slaat",r(8,16)),("keert hem ook de andere toe",r(17,21))],
40:[("En zo iemand met u rechten wil, en uw rok nemen",r(0,9)),("laat hem ook de mantel",r(10,14))],
41:[("En zo wie u zal dwingen een mijl te gaan",r(0,5)),("gaat met hem twee mijlen",r(6,9))],
42:[("Geef degene, die iets van u bidt",r(0,3)),("en keert u niet af van degene, die van u lenen wil",r(4,11))],
43:[("U hebt gehoord, dat er gezegd is",r(0,2)),("U zult uw naaste liefhebben",r(3,6)),("en uw vijand zult u haten",r(7,11))],
44:[("Maar Ik zeg u",r(0,3)),("Heb uw vijanden lief",r(4,7)),("zegen ze, die u vervloeken",r(8,11)),("doe wel van hen, die u haten",r(12,16)),("en bidt voor degenen, die u geweld doen, en die u vervolgen",r(17,25))],
45:[("Opdat u mag kinderen zijn van uw Vader, Die in de hemelen is",r(0,8)),("want Hij doet Zijn zon opgaan over bozen en goeden",r(9,17)),("en regent over rechtvaardigen en onrechtvaardigen",r(18,23))],
46:[("Want als u liefhebt, die u liefhebben",r(0,5)),("wat loon hebt u",r(6,8)),("Doen ook de tollenaars niet hetzelfde",r(9,15))],
47:[("En als u uw broeders alleen groet",r(0,6)),("wat doet u boven anderen",r(7,9)),("Doen ook niet de tollenaars zo",r(10,15))],
48:[("Wees dan u volmaakt",r(0,3)),("zoals uw Vader, Die in de hemelen is, volmaakt is",r(4,13))],
})
def build(u,o,w=False):
 src=load_tr_chapter(u,o,chapter=5,osis_book='Matt');p=ROOT/'data/mattheus/5.json';d=json.loads(p.read_text(encoding='utf-8'));reviewed_through=max(S);rev={'book':'mattheus','chapter':5,'reviewed_through':reviewed_through,'verses':{}}
 for v in d['verses'][:reviewed_through]:
  n=int(v['number']);ts=src[n];gs=S[n];ids=[i for _,x in gs for i in x]
  if sorted(ids)!=list(range(len(ts))) or len(ids)!=len(set(ids)):raise ValueError(n)
  v['grondtekst']=[{'woord':t['woord'],'strongs':t['display_strong'],'lemma_strongs':t['lemma_strong'],'morfologie':t['morphology'],**({'tvm':t['tvm']} if t.get('tvm') else {})} for t in ts];v['woordnummers']=[mapping(a,x,ts,n) for a,x in gs];occ={}
  for x in v['woordnummers']:occ[x['tekst']]=occ.get(x['tekst'],0)+1;x['voorkomen']=occ[x['tekst']];x['herkomst']['referentie']=f'MAT 5:{n}'
  rev['verses'][str(n)]=[{'tekst':a,'bronindices':x,'reviewstatus':'handmatig_gecontroleerd'} for a,x in gs]
 if w:
  p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');(ROOT/'data/woordnummers-review/mattheus-5.json').write_text(json.dumps(rev,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');ip=ROOT/'data/woordnummers-inline/mattheus.json';z=json.loads(ip.read_text(encoding='utf-8'));z['chapters']['5']={str(v['number']):v['woordnummers'] for v in d['verses'][:reviewed_through]};ip.write_text(json.dumps(z,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 return {'verses':reviewed_through,'tokens':sum(len(src[n]) for n in range(1,reviewed_through+1))}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--utr',type=Path,required=True);p.add_argument('--osis',type=Path,required=True);p.add_argument('--write',action='store_true');a=p.parse_args();print(build(a.utr,a.osis,a.write))
