#!/usr/bin/env python3
"""Publiceer gecontroleerde TR-koppelingen voor Johannes 18 in versbatches."""
from __future__ import annotations
import argparse,json
from pathlib import Path
from rebuild_nt_tr_strongs import load_tr_chapter
from rebuild_johannes2_tr_strongs import mapping,r
ROOT=Path(__file__).resolve().parents[1]
S={
1:[("Jezus, dit gezegd hebbende",r(0,3)),("ging uit met Zijn discipelen",r(4,8)),("over de beek Kedron",r(9,13)),("waar een hof was",r(14,16)),("in wie Hij ging, en Zijn discipelen",r(17,24))],
2:[("En Judas, die Hem verraadde",r(0,6)),("wist ook die plaats",r(7,8)),("omdat Jezus daar dikwijls verzameld was geweest met Zijn discipelen",r(9,18))],
3:[("Judas dan, genomen hebbende de bende soldaten",r(0,5)),("en enige dienaren van de overpriesters en Farizeeën",r(6,12)),("kwam daar met lantaarnen, en fakkelen, en wapenen",r(13,20))],
4:[("Jezus dan, wetende alles, wat over Hem komen zou",r(0,7)),("ging uit",r(8)),("en zei tot hen",r(9,10)),("Wie zoekt u",r(11,12))],
5:[("Zij antwoordden Hem",r(0,1)),("Jezus de Nazarener",r(2,4)),("Jezus zei tot hen",r(5,8)),("Ik ben het",r(9,10)),("En Judas, die Hem verraadde, stond ook bij hen",r(11,19))],
6:[("Als Hij dan tot hen zei",r(0,4)),("Ik ben het",r(5,6)),("gingen zij achteruit",r(7,10)),("en vielen ter aarde",r(11,13))],
7:[("Hij vraagde hun dan opnieuw",r(0,3)),("Wie zoekt u",r(4,5)),("En zij zeiden",r(6,8)),("Jezus de Nazarener",r(9,11))],
8:[("Jezus antwoordde",r(0,2)),("Ik heb u gezegd, dat Ik het ben",r(3,7)),("Als u dan Mij zoekt",r(8,11)),("zo laat deze heengaan",r(12,14))],
9:[("Opdat het woord vervuld zou worden",r(0,3)),("dat Hij gezegd had",r(4,5)),("Uit degenen, die U Mij gegeven hebt",r(6,9)),("heb Ik niemand verloren",r(10,14))],
10:[("Simon Petrus dan, hebbende een zwaard",r(0,4)),("trok het uit",r(5,6)),("en sloeg van de hogepriester dienaar",r(7,12)),("en hieuw zijn rechteroor af",r(13,19)),("En de naam van de dienaar was Malchus",r(20,25))],}
S.update({
11:[("Jezus dan zei tot Petrus",r(0,5)),("Steek uw zwaard in de schede",r(6,12)),("De drinkbeker, die Mij de Vader gegeven heeft",r(13,19)),("zal Ik die niet drinken",r(20,23))],
12:[("De bende dan, en de overste over duizend, en de dienaren van de Joden",r(0,10)),("namen Jezus gezamenlijk",r(11,13)),("en bonden Hem",r(14,16))],
13:[("En leidden Hem heen, eerst tot Annas",r(0,5)),("want hij was de vrouws vader van Kajafas",r(6,10)),("die dat jaar hogepriester was",r(11,16))],
14:[("Kajafas nu was degene",r(0,4)),("die de Joden geraden had",r(5,6)),("dat het nut was",r(7,8)),("dat een Mens voor het volk stierve",r(9,14))],
15:[("En Simon Petrus volgde Jezus",r(0,5)),("en een ander discipel",r(6,9)),("Deze discipel nu was de hogepriester bekend",r(10,17)),("en ging met Jezus in van de zaal van de hogepriester",r(18,26))],
16:[("En Petrus stond buiten aan de deur",r(0,7)),("De andere discipel dan, die de hogepriester bekend was",r(8,18)),("ging uit, en sprak met de deurwaarster",r(19,22)),("en bracht Petrus in",r(23,26))],
17:[("De dienstmaagd dan, die de deurwaarster was, zei tot Petrus",r(0,7)),("Bent ook u niet uit de discipelen van deze Mens",r(8,17)),("Hij zei",r(18,19)),("Ik ben niet",r(20,21))],
18:[("En de dienaren en de dienaren stonden",r(0,6)),("hebbende een kolenvuur gemaakt",r(7,8)),("omdat het koud was",r(9,11)),("en warmden zich",r(12,13)),("Petrus stond bij hen, en warmde zich",r(14,22))],
19:[("De hogepriester dan vraagde Jezus",r(0,5)),("van Zijn discipelen",r(6,9)),("en van Zijn leer",r(10,14))],
20:[("Jezus antwoordde hem",r(0,3)),("Ik heb vrijuit gesproken tot de wereld",r(4,8)),("Ik heb alle tijd geleerd in de synagoge en in de tempel",r(9,18)),("waar de Joden van alle plaatsen samenkomen",r(19,23)),("en in het verborgen heb Ik niets gesproken",r(24,28))],
21:[("Wat ondervraagt u Mij",r(0,2)),("Ondervraag degenen, die het gehoord hebben",r(3,5)),("wat Ik tot hen gesproken heb",r(6,8)),("zie, deze weten, wat Ik gezegd heb",r(9,14))],
22:[("En als Hij dit zei",r(0,3)),("gaf één van de dienaren, die daarbij stond",r(4,8)),("Jezus een kinnebakslag",r(9,11)),("zeggende",r(12)),("Antwoordt U zo de hogepriester",r(13,16))],
23:[("Jezus antwoordde hem",r(0,3)),("Als Ik kwalijk gesproken heb",r(4,6)),("betuig van het kwade",r(7,10)),("en als wel",r(11,13)),("waarom slaat u Mij",r(14,16))],
24:[("Annas dan had Hem gebonden gezonden tot Kajafas, de hogepriester",r(0,8))],
25:[("En Simon Petrus stond en warmde zich",r(0,6)),("Zij zeiden dan tot hem",r(7,9)),("Bent u ook niet uit Zijn discipelen",r(10,17)),("Hij ontkende het, en zei",r(18,21)),("Ik ben niet",r(22,23))],
26:[("Één van de dienaren van de hogepriester, die familie was van degene, die Petrus het oor afgehouwen had, zei",r(0,13)),("Heb ik u niet gezien in de hof met Hem",r(14,22))],
27:[("Petrus dan ontkende het opnieuw",r(0,4)),("En meteen kraaide de haan",r(5,8))],
28:[("Zij dan leidden Jezus van Kajafas in het rechthuis",r(0,9)),("En het was 's morgens vroeg",r(10,12)),("en zij gingen niet in het rechthuis",r(13,19)),("opdat zij niet verontreinigd zouden worden",r(20,22)),("maar opdat zij het pascha eten mochten",r(23,27))],
29:[("Pilatus dan ging tot hen uit",r(0,5)),("en zei",r(6,7)),("Wat beschuldiging brengt u tegen deze Mens",r(8,14))],
30:[("Zij antwoordden en zeiden tot hem",r(0,3)),("Als Deze geen kwaaddoener was",r(4,8)),("zo zouden wij Hem u niet overgeleverd hebben",r(9,13))],
31:[("Pilatus dan zei tot hen",r(0,4)),("Neem u Hem",r(5,7)),("en oordeelt Hem naar uw wet",r(8,14)),("De Joden dan zeiden tot hem",r(15,19)),("Het is ons niet geoorloofd iemand te doden",r(20,24))],
32:[("Opdat het woord van Jezus vervuld werd",r(0,5)),("dat Hij gezegd had",r(6,7)),("betekenende, wat voor dood Hij sterven zou",r(8,12))],
33:[("Pilatus dan ging opnieuw in het rechthuis",r(0,7)),("en riep Jezus",r(8,11)),("en zei tot Hem",r(12,14)),("Bent U de Koning van de Joden",r(15,20))],
34:[("Jezus antwoordde hem",r(0,3)),("Zegt u dit van uzelf",r(4,8)),("of hebben het u anderen van Mij gezegd",r(9,14))],
35:[("Pilatus antwoordde",r(0,2)),("Ben ik een Jood",r(3,6)),("Uw volk en de overpriesters hebben U aan mij overgeleverd",r(7,16)),("wat hebt U gedaan",r(17,18))],
36:[("Jezus antwoordde",r(0,2)),("Mijn Koninkrijk is niet van deze wereld",r(3,12)),("Als Mijn Koninkrijk van deze wereld was",r(13,22)),("zo zouden Mijn dienaren gestreden hebben",r(23,28)),("opdat Ik de Joden niet was overgeleverd",r(29,33)),("maar nu is Mijn Koninkrijk niet van hier",r(34,42))],
37:[("Pilatus dan zei tot Hem",r(0,4)),("Bent U dan een Koning",r(5,8)),("Jezus antwoordde",r(9,11)),("U zegt, dat Ik een Koning ben",r(12,17)),("Hiertoe ben Ik geboren en hiertoe ben Ik in de wereld gekomen",r(18,28)),("opdat Ik van de waarheid getuigenis geven zou",r(29,32)),("Ieder, die uit de waarheid is, hoort Mijn stem",r(33,42))],
38:[("Pilatus zei tot Hem",r(0,3)),("Wat is waarheid",r(4,6)),("En als hij dat gezegd had",r(7,9)),("ging hij opnieuw uit tot de Joden",r(10,14)),("en zei tot hen",r(15,17)),("Ik vind geen schuld in Hem",r(18,23))],
39:[("Maar u hebt een gewoonte",r(0,3)),("dat ik u op het pascha een loslate",r(4,10)),("Wilt u dan",r(11,13)),("dat ik u de Koning van de Joden loslate",r(14,18))],
40:[("Zij dan riepen allen opnieuw, zeggende",r(0,4)),("Niet Deze",r(5,6)),("maar Bar-abbas",r(7,9)),("En Bar-abbas was een moordenaar",r(10,14))],
})
def build(u,o,w=False):
 src=load_tr_chapter(u,o,chapter=18,osis_book='John');p=ROOT/'data/johannes/18.json';d=json.loads(p.read_text(encoding='utf-8'));reviewed_through=max(S);rev={'book':'johannes','chapter':18,'reviewed_through':reviewed_through,'verses':{}}
 for v in d['verses'][:reviewed_through]:
  n=int(v['number']);ts=src[n];gs=S[n];ids=[i for _,x in gs for i in x]
  if sorted(ids)!=list(range(len(ts))) or len(ids)!=len(set(ids)):raise ValueError(n)
  v['grondtekst']=[{'woord':t['woord'],'strongs':t['display_strong'],'lemma_strongs':t['lemma_strong'],'morfologie':t['morphology'],**({'tvm':t['tvm']} if t.get('tvm') else {}),**({'bronstatus':t['bronstatus']} if t.get('bronstatus') else {})} for t in ts];v['woordnummers']=[mapping(a,x,ts,n) for a,x in gs];occ={}
  for x in v['woordnummers']:occ[x['tekst']]=occ.get(x['tekst'],0)+1;x['voorkomen']=occ[x['tekst']];x['herkomst']['referentie']=f'JHN 18:{n}'
  rev['verses'][str(n)]=[{'tekst':a,'bronindices':x,'reviewstatus':'handmatig_gecontroleerd'} for a,x in gs]
 if w:
  p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');(ROOT/'data/woordnummers-review/johannes-18.json').write_text(json.dumps(rev,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');ip=ROOT/'data/woordnummers-inline/johannes.json';z=json.loads(ip.read_text(encoding='utf-8'));z['chapters']['18']={str(v['number']):v['woordnummers'] for v in d['verses'][:reviewed_through]};ip.write_text(json.dumps(z,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 return {'verses':reviewed_through,'tokens':sum(len(src[n]) for n in range(1,reviewed_through+1))}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--utr',type=Path,required=True);p.add_argument('--osis',type=Path,required=True);p.add_argument('--write',action='store_true');a=p.parse_args();print(build(a.utr,a.osis,a.write))
