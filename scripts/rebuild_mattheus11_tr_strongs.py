#!/usr/bin/env python3
from __future__ import annotations
import argparse,json
from pathlib import Path
from rebuild_nt_tr_strongs import load_tr_chapter
from rebuild_johannes2_tr_strongs import mapping,r
ROOT=Path(__file__).resolve().parents[1]
S={
1:[("En het is gebeurd, toen Jezus geëindigd had Zijn twaalf discipelen bevelen te geven",r(0,10)),("dat Hij van daar voortging, om te leren en te prediken in hun steden",r(11,20))],
2:[("En Johannes, in de gevangenis gehoord hebbende de werken van Christus",r(0,10)),("zond twee van zijn discipelen",r(11,15))],
3:[("En zei tot hem",r(0,1)),("Bent U Degene, Die komen zou",r(2,5)),("of verwachten wij een andere",r(6,8))],
4:[("En Jezus antwoordde en zei tot hen",r(0,5)),("Ga heen en boodschapt Johannes weer, wat u hoort en ziet",r(6,12))],
5:[("De blinden worden ziende, en de kreupelen wandelen",r(0,4)),("de melaatsen worden gereinigd, en de doven horen",r(5,9)),("de doden worden opgewekt, en de armen wordt het Evangelie verkondigd",r(10,14))],
6:[("En zalig is hij, die aan Mij niet zal struikelen",r(0,8))],
7:[("Als nu deze heengingen",r(0,2)),("heeft Jezus tot de menigten begonnen te zeggen van Johannes",r(3,10)),("Wat bent u uitgegaan in de woestijn te aanschouwen",r(11,16)),("Een riet, dat van de wind ginds en weer bewogen wordt",r(17,20))],
8:[("Maar wat bent u uitgegaan te zien",r(0,3)),("Een mens, met zachte kleren bekleed",r(4,8)),("Zie, die zachte kleren dragen, zijn in de huizen van de koningen",r(9,19))],
9:[("Maar wat bent u uitgegaan te zien",r(0,3)),("Een profeet",r(4)),("Ja, Ik zeg u, ook veel meer dan een profeet",r(5,10))],
10:[("Want deze is het, van wie geschreven staat",r(0,5)),("Zie, Ik zend Mijn engel voor Uw aangezicht",r(6,14)),("die Uw weg bereiden zal voor U heen",r(15,21))],
11:[("Voorwaar zeg Ik u",r(0,2)),("onder degenen, die van vrouwen geboren zijn, is niemand opgestaan meerder dan Johannes de Doper",r(3,11)),("maar die de minste is in het Koninkrijk van de hemelen, is meerder dan hij",r(12,22))],
12:[("En van de dagen van Johannes de Doper tot nu toe",r(0,8)),("wordt het Koninkrijk van de hemelen geweld aangedaan",r(9,13)),("en de geweldigers nemen hetzelfde met geweld",r(14,17))],
13:[("Want al de profeten en de wet hebben tot Johannes toe geprofeteerd",r(0,9))],
14:[("En zo u het wilt aannemen",r(0,3)),("hij is Elia, die komen zou",r(4,9))],
15:[("Wie oren heeft om te horen, die hore",r(0,4))],
16:[("Maar waarbij zal Ik dit geslacht vergelijken",r(0,5)),("Het is gelijk aan de kinderen, die op de markten zitten, en hun gezellen toeroepen",r(6,16))],
17:[("En zeggen: Wij hebben u op de fluit gespeeld, en u hebt niet gedanst",r(0,6)),("wij hebben u klaagliederen gezongen, en u hebt niet geweend",r(7,11))],
18:[("Want Johannes is gekomen, noch etende, noch drinkende",r(0,6)),("en zij zeggen: Hij heeft de duivel",r(7,10))],
19:[("De Zoon des mensen is gekomen, etende en drinkende",r(0,7)),("en zij zeggen: Zie daar, een Mens, Die een vraat en wijnzuiper is, een Vriend van tollenaren en zondaren",r(8,18)),("Maar de Wijsheid is gerechtvaardigd geworden van Haar kinderen",r(19,26))],
20:[("Toen begon Hij de steden, in die Zijn krachten meest gebeurd waren, te verwijten",r(0,11)),("omdat zij zich niet bekeerd hadden",r(12,14))],
21:[("Wee u, Chorazin! wee u Bethsaïda",r(0,5)),("want zo in Tyrus en Sidon de krachten waren gebeurd, die in u gebeurd zijn",r(6,18)),("zij zouden zich vroeger in zak en as bekeerd hebben",r(19,25))],
22:[("Maar Ik zeg u",r(0,2)),("Het zal Tyrus en Sidon verdragelijker zijn in de dag van het oordeel, dan u",r(3,12))],
23:[("En u, Kapernaüm! die tot de hemel toe bent verhoogd, u zult tot de hel toe neergestoten worden",r(0,10)),("Want zo in Sodom die krachten waren gebeurd, die in u gebeurd zijn",r(11,21)),("zij zouden tot op de huidige dag gebleven zijn",r(22,26))],
24:[("Maar Ik zeg u",r(0,3)),("dat het de lande van Sodom verdragelijker zal zijn in de dag van het oordeel, dan u",r(4,12))],
25:[("In diezelfde tijd antwoordde Jezus en zei",r(0,7)),("Ik dank U, Vader! Heere van de hemel en van de aarde",r(8,16)),("dat U deze dingen voor de wijzen en verstandigen verborgen hebt, en hebt dezelfde de kinderen geopenbaard",r(17,27))],
26:[("Ja, Vader",r(0,2)),("Want zo is geweest het welbehagen voor U",r(3,8))],
27:[("Alle dingen zijn Mij overgegeven van Mijn Vader",r(0,6)),("en niemand kent de Zoon dan de Vader",r(7,15)),("noch iemand kent de Vader dan de Zoon",r(16,24)),("en die het de Zoon wil openbaren",r(25,31))],
28:[("Kom herwaarts tot Mij, allen die vermoeid en belast bent",r(0,7)),("en Ik zal u rust geven",r(8,10))],
29:[("Neem Mijn juk op u",r(0,5)),("en leert van Mij, dat Ik zachtmoedig ben en nederig van hart",r(6,17)),("en u zult rust vinden voor uw zielen",r(18,22))],
30:[("Want Mijn juk is zacht, en Mijn last is licht",r(0,10))],
}
def build(u,o,w=False):
 src=load_tr_chapter(u,o,chapter=11,osis_book='Matt');p=ROOT/'data/mattheus/11.json';d=json.loads(p.read_text(encoding='utf-8'));reviewed_through=max(S);rev={'book':'mattheus','chapter':11,'reviewed_through':reviewed_through,'verses':{},'vormpresentatie':{'11:20:10':'UTR lemma G4183/A-NPF-S; OSIS-presentatie G4118 voor dezelfde vorm πλεισται.'}}
 for v in d['verses'][:reviewed_through]:
  n=int(v['number']);ts=src[n];gs=S[n];ids=[i for _,x in gs for i in x]
  if sorted(ids)!=list(range(len(ts))) or len(ids)!=len(set(ids)):raise ValueError(n)
  v['grondtekst']=[{'woord':t['woord'],'strongs':t['display_strong'],'lemma_strongs':t['lemma_strong'],'morfologie':t['morphology'],**({'tvm':t['tvm']} if t.get('tvm') else {})} for t in ts];v['woordnummers']=[mapping(a,x,ts,n) for a,x in gs];occ={}
  for x in v['woordnummers']:occ[x['tekst']]=occ.get(x['tekst'],0)+1;x['voorkomen']=occ[x['tekst']];x['herkomst']['referentie']=f'MAT 11:{n}'
  rev['verses'][str(n)]=[{'tekst':a,'bronindices':x,'reviewstatus':'handmatig_gecontroleerd'} for a,x in gs]
 if w:
  p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');(ROOT/'data/woordnummers-review/mattheus-11.json').write_text(json.dumps(rev,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');ip=ROOT/'data/woordnummers-inline/mattheus.json';z=json.loads(ip.read_text(encoding='utf-8'));z['chapters']['11']={str(v['number']):v['woordnummers'] for v in d['verses'][:reviewed_through]};ip.write_text(json.dumps(z,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 return {'verses':reviewed_through,'tokens':sum(len(src[n]) for n in range(1,reviewed_through+1))}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--utr',type=Path,required=True);p.add_argument('--osis',type=Path,required=True);p.add_argument('--write',action='store_true');a=p.parse_args();print(build(a.utr,a.osis,a.write))
