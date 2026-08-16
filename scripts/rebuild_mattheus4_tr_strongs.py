#!/usr/bin/env python3
"""Publiceer handmatig beoordeelde TR-koppelingen voor Mattheüs 4."""
from __future__ import annotations
import argparse,json
from pathlib import Path
from rebuild_nt_tr_strongs import load_tr_chapter
from rebuild_johannes2_tr_strongs import mapping,r
ROOT=Path(__file__).resolve().parents[1]
S={
1:[("Toen werd Jezus van de Geest weggeleid in de woestijn",r(0,9)),("om verzocht te worden van de duivel",r(10,13))],
2:[("En als Hij veertig dagen en veertig nachten gevast had",r(0,6)),("hongerde Hem ten laatste",r(7,8))],
3:[("En de verzoeker, tot Hem gekomen zijnde, zei",r(0,5)),("Als U Gods Zoon bent",r(6,10)),("zeg, dat deze stenen broden worden",r(11,17))],
4:[("Maar Hij, antwoordende, zei",r(0,3)),("Er is geschreven",r(4)),("De mens zal bij brood alleen niet leven",r(5,10)),("maar bij alle woord, dat door de mond van God uitgaat",r(11,18))],
5:[("Toen nam Hem de duivel mee naar de heilige stad",r(0,8)),("en stelde Hem op de tinne van de tempel",r(9,16))],
}
S.update({
6:[("En zei tot Hem",r(0,2)),("Als U Gods Zoon bent",r(3,7)),("werp Uzelf naar beneden",r(8,10)),("want er is geschreven, dat Hij Zijn engelen van U bevelen zal",r(11,19)),("en dat zij U op de handen zullen nemen",r(20,24)),("opdat U niet te eniger tijd Uw voet aan een steen aanstoot",r(25,31))],
7:[("Jezus zei tot hem",r(0,3)),("Er is opnieuw geschreven",r(4,5)),("U zult de Heere, uw God, niet verzoeken",r(6,11))],
8:[("Opnieuw nam Hem de duivel mee op een zeer hoge berg",r(0,8)),("en toonde Hem al de koninkrijken van de wereld",r(9,16)),("en hun heerlijkheid",r(17,20))],
9:[("En zei tot Hem",r(0,2)),("Al deze dingen zal ik U geven",r(3,6)),("als U, nedervallende, mij zult aanbidden",r(7,10))],
10:[("Toen zei Jezus tot hem",r(0,4)),("Ga weg, satan",r(5,6)),("want er staat geschreven",r(7,8)),("De Heere, uw God, zult u aanbidden",r(9,13)),("en Hem alleen dienen",r(14,17))],
11:[("Toen liet de duivel van Hem af",r(0,4)),("en ziet, de engelen zijn toegekomen",r(5,8)),("en dienden Hem",r(9,11))],
12:[("Als nu Jezus gehoord had, dat Johannes overgeleverd was",r(0,6)),("is Hij teruggekeerd naar Galilea",r(7,10))],
13:[("En Nazareth verlaten hebbende",r(0,3)),("is komen wonen te Kapernaüm, gelegen aan de zee",r(4,9)),("in het gebied van Zebulon en Nafthali",r(10,14))],
14:[("Opdat vervuld zou worden, wat gesproken is door Jesaja, de profeet, zeggende",r(0,8))],
15:[("Het land Zebulon en het land Nafthali",r(0,4)),("aan de weg van de zee over de Jordaan",r(5,9)),("Galilea van de volken",r(10,12))],
})
S.update({
16:[("Het volk, dat in duisternis zat, heeft een groot licht gezien",r(0,8)),("en degenen, die zaten in het land en de schaduwe van de dood",r(9,16)),("dezelfde is een licht opgegaan",r(17,19))],
17:[("Van toen aan heeft Jezus begonnen te prediken en te zeggen",r(0,7)),("Bekeer u",r(8)),("want het Koninkrijk van de hemelen is nabij gekomen",r(9,14))],
18:[("En Jezus, wandelende aan de zee van Galilea",r(0,8)),("zag twee broers, namelijk Simon, gezegd Petrus, en Andreas, zijn broer",r(9,20)),("het net in de zee werpende",r(21,25)),("want zij waren vissers",r(26,28))],
19:[("En Hij zei tot hen",r(0,2)),("Volg Mij na",r(3,5)),("en Ik zal u vissers van de mensen maken",r(6,10))],
20:[("Zij dan, meteen de netten verlatende",r(0,5)),("zijn Hem nagevolgd",r(6,7))],
21:[("En Hij, van daar voortgegaan zijnde",r(0,3)),("zag twee andere broers, namelijk Jakobus, de zoon van Zebedeüs, en Johannes, zijn broer",r(4,15)),("in het schip met hun vader Zebedeüs",r(16,23)),("hun netten vermakende",r(24,27)),("en heeft hen geroepen",r(28,30))],
22:[("Zij dan, meteen verlatende het schip en hun vader",r(0,9)),("zijn Hem nagevolgd",r(10,11))],
23:[("En Jezus omging geheel Galilea",r(0,6)),("lerende in hun synagogen",r(7,11)),("en predikende het Evangelie van het Koninkrijk",r(12,17)),("en genezende alle ziekte en alle kwalen onder het volk",r(18,27))],
24:[("En Zijn gerucht ging van daar uit in geheel Syrië",r(0,8)),("en zij brachten tot Hem allen, die kwalijk gesteld waren",r(9,15)),("met verscheidene ziekten en pijnen bevangen zijnde",r(16,20)),("en van de duivel bezeten, en maanzieken en geraakten",r(21,26)),("en Hij genas hen",r(27,29))],
25:[("En vele menigten volgden Hem na",r(0,4)),("van Galilea en van Dekapolis",r(5,9)),("en van Jeruzalem, en van Judea",r(10,13)),("en van over de Jordaan",r(14,17))],
})
def build(u,o,w=False):
 src=load_tr_chapter(u,o,chapter=4,osis_book='Matt');p=ROOT/'data/mattheus/4.json';d=json.loads(p.read_text(encoding='utf-8'));reviewed_through=max(S);rev={'book':'mattheus','chapter':4,'reviewed_through':reviewed_through,'verses':{}}
 for v in d['verses'][:reviewed_through]:
  n=int(v['number']);ts=src[n];gs=S[n];ids=[i for _,x in gs for i in x]
  if sorted(ids)!=list(range(len(ts))) or len(ids)!=len(set(ids)):raise ValueError(n)
  v['grondtekst']=[{'woord':t['woord'],'strongs':t['display_strong'],'lemma_strongs':t['lemma_strong'],'morfologie':t['morphology'],**({'tvm':t['tvm']} if t.get('tvm') else {})} for t in ts];v['woordnummers']=[mapping(a,x,ts,n) for a,x in gs];occ={}
  for x in v['woordnummers']:occ[x['tekst']]=occ.get(x['tekst'],0)+1;x['voorkomen']=occ[x['tekst']];x['herkomst']['referentie']=f'MAT 4:{n}'
  rev['verses'][str(n)]=[{'tekst':a,'bronindices':x,'reviewstatus':'handmatig_gecontroleerd'} for a,x in gs]
 if w:
  p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');(ROOT/'data/woordnummers-review/mattheus-4.json').write_text(json.dumps(rev,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');ip=ROOT/'data/woordnummers-inline/mattheus.json';z=json.loads(ip.read_text(encoding='utf-8'));z['chapters']['4']={str(v['number']):v['woordnummers'] for v in d['verses'][:reviewed_through]};ip.write_text(json.dumps(z,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 return {'verses':reviewed_through,'tokens':sum(len(src[n]) for n in range(1,reviewed_through+1))}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--utr',type=Path,required=True);p.add_argument('--osis',type=Path,required=True);p.add_argument('--write',action='store_true');a=p.parse_args();print(build(a.utr,a.osis,a.write))
