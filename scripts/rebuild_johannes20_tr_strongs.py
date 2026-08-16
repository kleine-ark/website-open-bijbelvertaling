#!/usr/bin/env python3
from __future__ import annotations
import argparse,json
from pathlib import Path
from rebuild_nt_tr_strongs import load_tr_chapter
from rebuild_johannes2_tr_strongs import mapping,r
ROOT=Path(__file__).resolve().parents[1]
S={
1:[("En op de eerste dag van de week",r(0,4)),("ging Maria Magdalena vroeg, als het nog donker was, naar het graf",r(5,15)),("en zag de steen van het graf weggenomen",r(16,23))],
2:[("Zij liep dan, en kwam tot Simon Petrus",r(0,6)),("en tot de andere discipel, wie Jezus liefhad",r(7,15)),("en zei tot hen",r(16,18)),("Zij hebben de Heere weggenomen uit het graf",r(19,24)),("en wij weten niet, waar zij Hem gelegd hebben",r(25,30))],
3:[("Petrus dan ging uit",r(0,3)),("en de andere discipel",r(4,7)),("en zij kwamen tot het graf",r(8,12))],
4:[("En deze twee liepen tegelijk",r(0,4)),("en de andere discipel liep vooruit, sneller dan Petrus",r(5,12)),("en kwam eerst tot het graf",r(13,18))],
5:[("En als hij boog neer",r(0,1)),("zag hij de doeken liggen",r(2,5)),("toch ging hij er niet in",r(6,8))],
6:[("Simon Petrus dan kwam en volgde hem",r(0,5)),("en ging in het graf",r(6,10)),("en zag de doeken liggen",r(11,15))],
7:[("En de zweetdoek, die op Zijn hoofd geweest was",r(0,8)),("zag hij niet bij de doeken liggen",r(9,13)),("maar in het bijzonder in een andere plaats samengerold",r(14,19))],
8:[("Toen ging dan ook de andere discipel er in",r(0,6)),("die eerst tot het graf gekomen was",r(7,12)),("en zag het, en geloofde",r(13,16))],
9:[("Want zij wisten nog de Schrift niet",r(0,4)),("dat Hij van de doden moest opstaan",r(5,10))],
10:[("De discipelen dan gingen opnieuw naar huis",r(0,6))],}
S.update({
11:[("En Maria stond buiten bij het graf, huilend",r(0,7)),("Als zij dan huilde",r(8,10)),("bukte zij in het graf",r(11,14))],
12:[("En zag twee engelen in witte kleren zitten",r(0,6)),("één aan het hoofd",r(7,10)),("en één aan de voeten",r(11,15)),("waar het lichaam van Jezus gelegen had",r(16,21))],
13:[("En die zeiden tot haar",r(0,3)),("Vrouw! wat weent u",r(4,6)),("Zij zei tot hen",r(7,8)),("Omdat zij mijn Heere weggenomen hebben",r(9,13)),("en ik weet niet, waar zij Hem gelegd hebben",r(14,19))],
14:[("En als zij dit gezegd had",r(0,2)),("keerde zij zich achteruit",r(3,6)),("en zag Jezus staan",r(7,11)),("en zij wist niet, dat het Jezus was",r(12,18))],
15:[("Jezus zei tot haar",r(0,3)),("Vrouw, wat weent u",r(4,6)),("Wie zoekt u",r(7,8)),("Zij, menende, dat het de hovenier was",r(9,14)),("zei tot Hem",r(15,16)),("Heere, zo u Hem weg gedragen hebt",r(17,21)),("zeg mij, waar u Hem gelegd hebt",r(22,26)),("en ik zal Hem wegnemen",r(27,29))],
16:[("Jezus zei tot haar",r(0,3)),("Maria",r(4)),("Zij, zich omkerende, zei tot Hem",r(5,8)),("Rabbouni",r(9)),("dat is gezegd, Meester",r(10,12))],
17:[("Jezus zei tot haar",r(0,3)),("Raak Mij niet aan",r(4,6)),("want Ik ben nog niet opgevaren tot Mijn Vader",r(7,13)),("maar ga heen tot Mijn broeders",r(14,19)),("en zeg hun",r(20,22)),("Ik vare op tot Mijn Vader en uw Vader",r(23,30)),("en tot Mijn God en uw God",r(31,36))],
18:[("Maria Magdalena ging en boodschapte de discipelen",r(0,6)),("dat zij de Heere gezien had",r(7,10)),("en dat Hij haar dit gezegd had",r(11,14))],
19:[("Als het dan avond was, op deze eerste dag van de week",r(0,9)),("en als de deuren gesloten waren",r(10,13)),("waar de discipelen verzameld waren om de vrees voor de Joden",r(14,23)),("kwam Jezus en stond in het midden",r(24,31)),("en zei tot hen",r(32,34)),("Vrede zij u",r(35,36))],
20:[("En dit gezegd hebbende",r(0,2)),("toonde Hij hun Zijn handen en Zijn zijde",r(3,10)),("De discipelen dan werden verblijd",r(11,14)),("als zij de Heere zagen",r(15,17))],
21:[("Jezus dan zei opnieuw tot hen",r(0,5)),("Vrede zij u",r(6,7)),("zoals Mij de Vader gezonden heeft",r(8,12)),("zend Ik ook u",r(13,15))],
22:[("En als Hij dit gezegd had",r(0,2)),("blies Hij op hen",r(3)),("en zei tot hen",r(4,6)),("Ontvang de Heilige Geest",r(7,9))],
23:[("Zo u iemands zonden vergeeft",r(0,4)),("die worden zij vergeven",r(5,6)),("zo u iemands zonden houdt",r(7,9)),("die zijn zij gehouden",r(10))],
24:[("En Thomas, één van de twaalven, gezegd Didymus",r(0,8)),("was met hen niet",r(9,12)),("toen Jezus daar kwam",r(13,16))],
25:[("De andere discipelen dan zeiden tot hem",r(0,5)),("Wij hebben de Heere gezien",r(6,8)),("Maar hij zei tot hen",r(9,12)),("Als ik in Zijn handen niet zie het teken van de nagelen",r(13,23)),("en mijn vinger steke in het teken van de nagelen",r(24,33)),("en steke mijn hand in Zijn zijde",r(34,42)),("ik zal in geen geval geloven",r(43,45))],
26:[("En na acht dagen waren Zijn discipelen opnieuw binnen",r(0,9)),("en Thomas met hen",r(10,13)),("en Jezus kwam, als de deuren gesloten waren",r(14,19)),("en stond in het midden",r(20,24)),("en zei",r(25,26)),("Vrede zij u",r(27,28))],
27:[("Daarna zei Hij tot Thomas",r(0,3)),("Breng uw vinger hier",r(4,8)),("en zie Mijn handen",r(9,13)),("en breng uw hand",r(14,18)),("en steek ze in Mijn zijde",r(19,24)),("en bent niet ongelovig, maar gelovig",r(25,30))],
28:[("En Thomas antwoordde en zei tot Hem",r(0,6)),("Mijn Heere en mijn God",r(7,13))],
29:[("Jezus zei tot hem",r(0,3)),("Omdat u Mij gezien hebt, Thomas",r(4,7)),("zo hebt u geloofd",r(8)),("zalig zijn zij, die niet zullen gezien hebben, en toch zullen geloofd hebben",r(9,14))],
30:[("Jezus dan heeft nog wel vele andere tekenen in de aanwezigheid Zijn discipelen gedaan",r(0,12)),("die niet zijn geschreven in dit boek",r(13,20))],
31:[("Maar deze zijn geschreven",r(0,2)),("opdat u gelooft",r(3,4)),("dat Jezus is de Christus, de Zoon van God",r(5,14)),("en opdat u, gelovende, het leven hebt in Zijn Naam",r(15,23))],
})
def build(u,o,w=False):
 src=load_tr_chapter(u,o,chapter=20,osis_book='John');p=ROOT/'data/johannes/20.json';d=json.loads(p.read_text(encoding='utf-8'));reviewed_through=max(S);rev={'book':'johannes','chapter':20,'reviewed_through':reviewed_through,'verses':{}}
 for v in d['verses'][:reviewed_through]:
  n=int(v['number']);ts=src[n];gs=S[n];ids=[i for _,x in gs for i in x]
  if sorted(ids)!=list(range(len(ts))) or len(ids)!=len(set(ids)):raise ValueError(n)
  v['grondtekst']=[{'woord':t['woord'],'strongs':t['display_strong'],'lemma_strongs':t['lemma_strong'],'morfologie':t['morphology'],**({'tvm':t['tvm']} if t.get('tvm') else {})} for t in ts];v['woordnummers']=[mapping(a,x,ts,n) for a,x in gs];occ={}
  for x in v['woordnummers']:occ[x['tekst']]=occ.get(x['tekst'],0)+1;x['voorkomen']=occ[x['tekst']];x['herkomst']['referentie']=f'JHN 20:{n}'
  rev['verses'][str(n)]=[{'tekst':a,'bronindices':x,'reviewstatus':'handmatig_gecontroleerd'} for a,x in gs]
 if w:
  p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');(ROOT/'data/woordnummers-review/johannes-20.json').write_text(json.dumps(rev,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');ip=ROOT/'data/woordnummers-inline/johannes.json';z=json.loads(ip.read_text(encoding='utf-8'));z['chapters']['20']={str(v['number']):v['woordnummers'] for v in d['verses'][:reviewed_through]};ip.write_text(json.dumps(z,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 return {'verses':reviewed_through,'tokens':sum(len(src[n]) for n in range(1,reviewed_through+1))}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--utr',type=Path,required=True);p.add_argument('--osis',type=Path,required=True);p.add_argument('--write',action='store_true');a=p.parse_args();print(build(a.utr,a.osis,a.write))
