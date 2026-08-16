#!/usr/bin/env python3
"""Publiceer handmatig beoordeelde TR-koppelingen voor Mattheüs 2."""
from __future__ import annotations
import argparse,json
from pathlib import Path
from rebuild_nt_tr_strongs import load_tr_chapter
from rebuild_johannes2_tr_strongs import mapping,r
ROOT=Path(__file__).resolve().parents[1]
S={
1:[("Toen nu Jezus geboren was te Bethlehem, gelegen in Judea",r(0,7)),("in de dagen van de koning Herodes",r(8,12)),("ziet, enige wijzen van het Oosten zijn te Jeruzalem aangekomen",r(13,19))],
2:[("Zeggende",r(0)),("Waar is de geboren Koning van de Joden",r(1,7)),("want wij hebben gezien Zijn ster in het Oosten",r(8,15)),("en zijn gekomen om Hem te aanbidden",r(16,19))],
3:[("De koning Herodes nu, dit gehoord hebbende",r(0,4)),("werd ontroerd",r(5)),("en geheel Jeruzalem, met hem",r(6,10))],
4:[("En bijeenvergaderd hebbende al de overpriesters en Schriftgeleerden van het volk",r(0,8)),("vraagde van hen",r(9,11)),("waar de Christus zou geboren worden",r(12,15))],
5:[("En zij zeiden tot hem",r(0,3)),("Te Bethlehem, in Judea gelegen",r(4,7)),("want zo is geschreven door de profeet",r(8,13))],
}
S.update({
6:[("En u Bethlehem, u land Juda",r(0,4)),("bent in geen geval de minste onder de vorsten van Juda",r(5,11)),("want uit u zal de Leidsman voortkomen",r(12,17)),("Die Mijn volk Israël weiden zal",r(18,23))],
7:[("Toen heeft Herodes de wijzen in het geheim geroepen",r(0,5)),("en vernam ijverig van hen de tijd, wanneer de ster verschenen was",r(6,13))],
8:[("En hen naar Bethlehem zendende, zei",r(0,5)),("Reist heen, en onderzoekt ijverig naar dat Kind",r(6,11)),("en als u Het zult gevonden hebben, boodschapt het mij",r(12,16)),("opdat ik ook kome en Het aanbidde",r(17,21))],
9:[("En zij, de koning gehoord hebbende, zijn heengereisd",r(0,5)),("en ziet, de ster, die zij in het oosten gezien hadden, ging hun voor",r(6,16)),("totdat zij kwam en stond boven de plaats, waar het Kind was",r(17,24))],
10:[("Als zij nu de ster zagen",r(0,3)),("verheugden zij zich met zeer grote vreugde",r(4,7))],
11:[("En in het huis gekomen zijnde",r(0,4)),("vonden zij het Kind met Maria, Zijn moeder",r(5,12)),("en nedervallende hebben zij Hetzelfde aangebeden",r(13,16)),("en hun schatten opengedaan hebbende, brachten zij Hem geschenken",r(17,24)),("goud en wierook, en mirre",r(25,29))],
12:[("En door Goddelijke openbaring vermaand zijnde in de droom",r(0,3)),("dat zij niet zouden terugkeren tot Herodes",r(4,7)),("vertrokken zij door een andere weg weer naar hun land",r(8,15))],
13:[("Toen zij nu vertrokken waren, ziet, de engel van de Heere verschijnt Jozef in de droom, zeggende",r(0,11)),("Sta op, en neem tot u het Kind en Zijn moeder",r(12,19)),("en vlied in Egypte",r(20,23)),("en wees daar, totdat ik het u zeggen zal",r(24,30)),("want Herodes zal het Kind zoeken, om Hetzelfde te doden",r(31,39))],
14:[("Hij dan opgestaan zijnde",r(0,2)),("nam het Kind en Zijn moeder tot zich in de nacht",r(3,10)),("en vertrok naar Egypte",r(11,14))],
15:[("En was daar tot de dood van Herodes",r(0,6)),("opdat vervuld zou worden wat van de Heere gesproken is door de profeet, zeggende",r(7,17)),("Uit Egypte heb Ik Mijn Zoon geroepen",r(18,23))],
})
S.update({
16:[("Als Herodes zag, dat hij van de wijzen bedrogen was",r(0,7)),("toen werd hij zeer boos",r(8,9)),("en enige afgezonden hebbende, heeft omgebracht al de kinderen, die binnen Bethlehem, en in al zijn gebied waren",r(10,24)),("van twee jaar oud en daaronder, naar de tijd, die hij van de wijzen ijverig onderzocht had",r(25,36))],
17:[("Toen is vervuld geworden, wat gesproken is door de profeet Jeremia, zeggende",r(0,8))],
18:[("Een stem is in Rama gehoord",r(0,3)),("geklag, geween en veel gekerm",r(4,9)),("Rachel beweende haar kinderen",r(10,14)),("en wilde niet vertroost wezen, omdat zij niet zijn",r(15,21))],
19:[("Toen Herodes nu gestorven was",r(0,3)),("ziet, de engel van de Heere verschijnt Jozef in de droom, in Egypte",r(4,13))],
20:[("Zeggende",r(0)),("Sta op, neem het Kind en Zijn moeder tot u",r(1,8)),("en trek in het land van Israël",r(9,13)),("want zij zijn gestorven, die de ziel van het Kind zochten",r(14,21))],
21:[("Hij dan",r(0,1)),("opgestaan zijnde",r(2)),("heeft tot zich genomen het Kind en Zijn moeder",r(3,9)),("en is gekomen in het land van Israël",r(10,14))],
22:[("Maar als hij hoorde, dat Archelaüs in Judea koning was, in de plaats van zijn vader Herodes",r(0,12)),("vreesde hij daarheen te gaan",r(13,15)),("maar door Goddelijke openbaring vermaand in de droom",r(16,19)),("is hij vertrokken in de delen van Galilea",r(20,25))],
23:[("En daar gekomen zijnde, nam hij zijn woonplaats in de stad, genoemd Nazareth",r(0,6)),("opdat vervuld zou worden, wat door de profeten gezegd is",r(7,13)),("dat Hij Nazarener zal geheten worden",r(14,16))],
})
def build(u,o,w=False):
 src=load_tr_chapter(u,o,chapter=2,osis_book='Matt');p=ROOT/'data/mattheus/2.json';d=json.loads(p.read_text(encoding='utf-8'));reviewed_through=max(S);rev={'book':'mattheus','chapter':2,'reviewed_through':reviewed_through,'verses':{}}
 for v in d['verses'][:reviewed_through]:
  n=int(v['number']);ts=src[n];gs=S[n];ids=[i for _,x in gs for i in x]
  if sorted(ids)!=list(range(len(ts))) or len(ids)!=len(set(ids)):raise ValueError(n)
  v['grondtekst']=[{'woord':t['woord'],'strongs':t['display_strong'],'lemma_strongs':t['lemma_strong'],'morfologie':t['morphology'],**({'tvm':t['tvm']} if t.get('tvm') else {})} for t in ts];v['woordnummers']=[mapping(a,x,ts,n) for a,x in gs];occ={}
  for x in v['woordnummers']:occ[x['tekst']]=occ.get(x['tekst'],0)+1;x['voorkomen']=occ[x['tekst']];x['herkomst']['referentie']=f'MAT 2:{n}'
  rev['verses'][str(n)]=[{'tekst':a,'bronindices':x,'reviewstatus':'handmatig_gecontroleerd'} for a,x in gs]
 if w:
  p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');(ROOT/'data/woordnummers-review/mattheus-2.json').write_text(json.dumps(rev,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');ip=ROOT/'data/woordnummers-inline/mattheus.json';z=json.loads(ip.read_text(encoding='utf-8'));z['chapters']['2']={str(v['number']):v['woordnummers'] for v in d['verses'][:reviewed_through]};ip.write_text(json.dumps(z,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 return {'verses':reviewed_through,'tokens':sum(len(src[n]) for n in range(1,reviewed_through+1))}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--utr',type=Path,required=True);p.add_argument('--osis',type=Path,required=True);p.add_argument('--write',action='store_true');a=p.parse_args();print(build(a.utr,a.osis,a.write))
