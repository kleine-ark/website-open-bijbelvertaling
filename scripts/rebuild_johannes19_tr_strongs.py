#!/usr/bin/env python3
"""Publiceer gecontroleerde TR-koppelingen voor Johannes 19 in versbatches."""
from __future__ import annotations
import argparse,json
from pathlib import Path
from rebuild_nt_tr_strongs import load_tr_chapter
from rebuild_johannes2_tr_strongs import mapping,r
ROOT=Path(__file__).resolve().parents[1]
S={
1:[("Toen nam Pilatus dan Jezus",r(0,6)),("en geselde Hem",r(7,8))],
2:[("En de soldaten, een kroon van doornen gevlochten hebbende",r(0,6)),("zetten die op Zijn hoofd",r(7,10)),("en wierpen Hem een purperen kleed om",r(11,15))],
3:[("En zeiden",r(0,1)),("Wees gegroet, U Koning van de Joden",r(2,6)),("En zij gaven Hem kinnebakslagen",r(7,10))],
4:[("Pilatus dan kwam opnieuw uit",r(0,5)),("en zei tot hen",r(6,8)),("Zie, ik breng Hem tot u uit",r(9,13)),("opdat u weet, dat ik in Hem geen schuld vinde",r(14,21))],
5:[("Jezus dan kwam uit",r(0,4)),("dragende de doornenkroon",r(5,8)),("en het purperen kleed",r(9,12)),("En Pilatus zei tot hen",r(13,15)),("Zie, de Mens",r(16,18))],
6:[("Als Hem dan de overpriesters en de dienaren zagen",r(0,8)),("riepen zij, zeggende",r(9,10)),("Kruis Hem, kruis Hem",r(11,12)),("Pilatus zei tot hen",r(13,16)),("Neem u Hem en kruist Hem",r(17,21)),("want ik vind in Hem geen schuld",r(22,28))],
7:[("De Joden antwoordden hem",r(0,3)),("Wij hebben een wet",r(4,6)),("en naar onze wet moet Hij sterven",r(7,13)),("want Hij heeft Zichzelf Gods Zoon gemaakt",r(14,18))],
8:[("Toen Pilatus dan dit woord hoorde",r(0,7)),("werd hij meer bevreesd",r(8,9))],
9:[("En ging opnieuw in het rechthuis",r(0,5)),("en zei tot Jezus",r(6,9)),("Vanwaar bent U",r(10,12)),("Maar Jezus gaf hem geen antwoord",r(13,19))],
10:[("Pilatus dan zei tot Hem",r(0,4)),("Spreekt U tot mij niet",r(5,7)),("Weet U niet",r(8,9)),("dat ik macht heb U te kruisigen",r(10,14)),("en macht heb U los te laten",r(15,19))],}
S.update({
11:[("Jezus antwoordde",r(0,2)),("U zou geen macht hebben tegen Mij",r(3,8)),("als het u niet van boven gegeven was",r(9,14)),("daarom die Mij aan u heeft overgeleverd",r(15,20)),("heeft groter zonde",r(21,23))],
12:[("Van toen af zocht Pilatus Hem los te laten",r(0,6)),("maar de Joden riepen, zeggende",r(7,11)),("Als u Deze loslaat",r(12,14)),("zo bent u niet de vriend van de keizer",r(15,19)),("ieder, die zichzelf koning maakt",r(20,24)),("wederspreekt de keizer",r(25,27))],
13:[("Als Pilatus dan dit woord hoorde",r(0,6)),("bracht hij Jezus uit",r(7,10)),("en zat neer op de rechterstoel",r(11,15)),("in de plaats, genoemd Lithostrotos",r(16,19)),("en in het Hebreeuws Gabbatha",r(20,22))],
14:[("En het was de voorbereiding van het pascha",r(0,4)),("en ongeveer het zesde uur",r(5,8)),("en hij zei tot de Joden",r(9,12)),("Zie, uw Koning",r(13,16))],
15:[("Maar zij riepen",r(0,2)),("Neem weg, neem weg, kruis Hem",r(3,6)),("Pilatus zei tot hen",r(7,10)),("Zal ik uw Koning kruisigen",r(11,14)),("De overpriesters antwoordden",r(15,17)),("Wij hebben geen koning, dan de keizer",r(18,23))],
16:[("Toen gaf hij Hem dan hun over",r(0,4)),("opdat Hij gekruist zou worden",r(5,6)),("En zij namen Jezus, en leidden Hem weg",r(7,12))],
17:[("En Hij, dragende Zijn kruis",r(0,4)),("ging uit naar de plaats, genoemd Hoofdschedelplaats",r(5,10)),("die in het Hebreeuws genoemd wordt Golgotha",r(11,14))],
18:[("Alwaar zij Hem kruisten",r(0,2)),("en met Hem twee anderen",r(3,7)),("aan elke zijde een",r(8,10)),("en Jezus in het midden",r(11,14))],
19:[("En Pilatus schreef ook een opschrift",r(0,5)),("en zette dat op het kruis",r(6,10)),("en er was geschreven",r(11,13)),("JEZUS, DE NAZARENER, DE KONING DER JODEN",r(14,20))],
20:[("Dit opschrift dan lazen velen van de Joden",r(0,7)),("want de plaats, waar Jezus gekruist werd, was nabij de stad",r(8,18)),("en het was geschreven in het Hebreeuws, in het Grieks, en in het Latijn",r(19,24))],
21:[("De overpriesters dan van de Joden zeiden tot Pilatus",r(0,7)),("Schrijf niet",r(8,9)),("De Koning van de Joden",r(10,13)),("maar, dat Hij gezegd heeft",r(14,17)),("Ik ben de Koning van de Joden",r(18,21))],
22:[("Pilatus antwoordde",r(0,2)),("Wat ik geschreven heb, dat heb ik geschreven",r(3,5))],
23:[("De soldaten dan, als zij Jezus gekruist hadden",r(0,6)),("namen Zijn kleren",r(7,10)),("en maakten vier delen, voor elke soldaat een deel",r(11,17)),("en de rok",r(18,20)),("De rok nu was zonder naad, van boven af geheel geweven",r(21,31))],
24:[("Zij dan zeiden tot elkaar",r(0,3)),("Laat ons die niet scheuren",r(4,6)),("maar laat ons daarover loten, wiens die zijn zal",r(7,12)),("opdat de Schrift vervuld wordt, die zegt",r(13,18)),("Zij hebben Mijn kleren onder zich verdeeld",r(19,23)),("en over Mijn kleding hebben zij het lot geworpen",r(24,30)),("Dit hebben dan de soldaten gedaan",r(31,36))],
25:[("En bij het kruis van Jezus stonden Zijn moeder",r(0,9)),("en van Zijn moeders zus, Maria, de vrouw van Klopas",r(10,19)),("en Maria Magdalena",r(20,23))],
26:[("Jezus nu, ziende Zijn moeder",r(0,4)),("en de discipel, die Hij liefhad, daarbij staande",r(5,10)),("zei tot Zijn moeder",r(11,14)),("Vrouw, zie, uw zoon",r(15,19))],
27:[("Daarna zei Hij tot de discipel",r(0,3)),("Zie, uw moeder",r(4,7)),("En van dat uur af aan",r(8,12)),("nam haar de discipel in zijn huis",r(13,19))],
28:[("Hierna Jezus, wetende",r(0,4)),("dat nu alles volbracht was",r(5,8)),("opdat de Schrift zou vervuld worden",r(9,12)),("zei",r(13)),("Mij dorst",r(14))],
29:[("Daar stond dan een kruik vol azijn",r(0,4)),("en zij vulden een spons met azijn",r(5,9)),("en omlegden ze met hysop",r(10,12)),("en brachten ze aan Zijn mond",r(13,16))],
30:[("Toen Jezus dan de azijn genomen had",r(0,6)),("zei Hij",r(7)),("Het is volbracht",r(8)),("En het hoofd buigende",r(9,12)),("gaf de geest",r(13,15))],
31:[("De Joden dan",r(0,2)),("opdat de lichamen niet aan het kruis zouden blijven op de sabbat",r(3,13)),("omdat het de voorbereiding was",r(14,16)),("want die dag van de sabbat was groot",r(17,24)),("baden Pilatus",r(25,27)),("dat hun benen zouden gebroken, en zij weggenomen worden",r(28,34))],
32:[("De soldaten dan kwamen",r(0,3)),("en braken wel de benen van de eerste",r(4,10)),("en van de andere, die met Hem gekruist was",r(11,16))],
33:[("Maar komende tot Jezus",r(0,4)),("als zij zagen, dat Hij nu gestorven was",r(5,9)),("zo braken zij Zijn benen niet",r(10,14))],
34:[("Maar één van de soldaten",r(0,3)),("doorstak Zijn zijde met een speer",r(4,8)),("en meteen kwam er bloed en water uit",r(9,14))],
35:[("En die het gezien heeft, die heeft het getuigd",r(0,3)),("en zijn getuigenis is waarachtig",r(4,9)),("en hij weet, dat hij zegt, wat waar is",r(10,14)),("opdat ook u geloven mag",r(15,17))],
36:[("Want deze dingen zijn gebeurd",r(0,2)),("opdat de Schrift vervuld wordt",r(3,6)),("Geen been van Hem zal verbroken worden",r(7,10))],
37:[("En opnieuw zegt een andere Schrift",r(0,4)),("Zij zullen zien, in Wie zij gestoken hebben",r(5,8))],
38:[("En daarna Jozef van Arimathea",r(0,10)),("die een discipel van Jezus was, maar bedekt om de vrees voor de Joden",r(11,21)),("bad Pilatus, dat hij mocht het lichaam van Jezus wegnemen",r(22,27)),("en Pilatus liet het toe",r(28,31)),("Hij dan ging en nam het lichaam van Jezus weg",r(32,39))],
39:[("En Nicodemus kwam ook",r(0,3)),("die in de nacht tot Jezus eerst gekomen was",r(4,11)),("en brachten een mengsel van mirre en aloë",r(12,16)),("ongeveer honderd ponden gewichts",r(17,19))],
40:[("Zij namen dan het lichaam van Jezus",r(0,5)),("en bonden dat in linnen doeken met de specerijen",r(6,12)),("zoals de Joden de gewoonte hebben van begraven",r(13,18))],
41:[("En er was in de plaats, waar Hij gekruist was, een hof",r(0,7)),("en in de hof een nieuw graf",r(8,13)),("in dat nog nooit iemand gelegd was geweest",r(14,18))],
42:[("Daar dan legden zij Jezus, om de voorbereiding van de Joden, omdat het graf nabij was",r(0,14))],
})
def build(u,o,w=False):
 src=load_tr_chapter(u,o,chapter=19,osis_book='John');p=ROOT/'data/johannes/19.json';d=json.loads(p.read_text(encoding='utf-8'));reviewed_through=max(S);rev={'book':'johannes','chapter':19,'reviewed_through':reviewed_through,'verses':{}}
 for v in d['verses'][:reviewed_through]:
  n=int(v['number']);ts=src[n];gs=S[n];ids=[i for _,x in gs for i in x]
  if sorted(ids)!=list(range(len(ts))) or len(ids)!=len(set(ids)):raise ValueError(n)
  v['grondtekst']=[{'woord':t['woord'],'strongs':t['display_strong'],'lemma_strongs':t['lemma_strong'],'morfologie':t['morphology'],**({'tvm':t['tvm']} if t.get('tvm') else {}),**({'bronstatus':t['bronstatus']} if t.get('bronstatus') else {})} for t in ts];v['woordnummers']=[mapping(a,x,ts,n) for a,x in gs];occ={}
  for x in v['woordnummers']:occ[x['tekst']]=occ.get(x['tekst'],0)+1;x['voorkomen']=occ[x['tekst']];x['herkomst']['referentie']=f'JHN 19:{n}'
  rev['verses'][str(n)]=[{'tekst':a,'bronindices':x,'reviewstatus':'handmatig_gecontroleerd'} for a,x in gs]
 if w:
  p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');(ROOT/'data/woordnummers-review/johannes-19.json').write_text(json.dumps(rev,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');ip=ROOT/'data/woordnummers-inline/johannes.json';z=json.loads(ip.read_text(encoding='utf-8'));z['chapters']['19']={str(v['number']):v['woordnummers'] for v in d['verses'][:reviewed_through]};ip.write_text(json.dumps(z,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 return {'verses':reviewed_through,'tokens':sum(len(src[n]) for n in range(1,reviewed_through+1))}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--utr',type=Path,required=True);p.add_argument('--osis',type=Path,required=True);p.add_argument('--write',action='store_true');a=p.parse_args();print(build(a.utr,a.osis,a.write))
