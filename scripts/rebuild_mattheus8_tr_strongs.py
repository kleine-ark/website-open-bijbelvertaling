#!/usr/bin/env python3
"""Publiceer handmatig beoordeelde TR-koppelingen voor Mattheüs 8."""
from __future__ import annotations
import argparse,json
from pathlib import Path
from rebuild_nt_tr_strongs import load_tr_chapter
from rebuild_johannes2_tr_strongs import mapping,r
ROOT=Path(__file__).resolve().parents[1]
S={
1:[("Toen Hij nu van de berg afgeklommen was",r(0,5)),("zijn Hem vele menigten gevolgd",r(6,9))],
2:[("En ziet, een melaatse kwam, en aanbad Hem, zeggende",r(0,6)),("Heere! als U wilt, U kunt mij reinigen",r(7,12))],
3:[("En Jezus, de hand uitstrekkende, heeft hem aangeraakt, zeggende",r(0,8)),("Ik wil, word gereinigd",r(9,10)),("En meteen werd hij van zijn melaatsheid gereinigd",r(11,16))],
4:[("En Jezus zei tot hem",r(0,4)),("Zie, dat u dit niemand zegt",r(5,7)),("maar ga heen, toon uzelf aan de priester",r(8,13)),("en offer de gave, die Mozes geboden heeft, hun tot een getuigenis",r(14,23))],
5:[("Als nu Jezus te Kapernaüm ingegaan was",r(0,5)),("kwam tot Hem een hoofdman over honderd, biddende Hem",r(6,10))],
}
S.update({
6:[("En zeggende",r(0,1)),("Heere! mijn knecht ligt te huis geraakt, en lijdt zware pijnen",r(2,12))],
7:[("En Jezus zei tot hem",r(0,4)),("Ik zal komen en hem genezen",r(5,8))],
8:[("En de hoofdman over honderd, antwoordende, zei",r(0,4)),("Heere! ik ben niet waard, dat U onder mijn dak zou inkomen",r(5,14)),("maar spreek alleen een woord, en mijn knecht zal genezen worden",r(15,23))],
9:[("Want ik ben ook een mens onder de macht van anderen, hebbende onder mij soldaten",r(0,10)),("en ik zeg tot deze: Ga! en hij gaat",r(11,16)),("en tot de anderen: Kom! en hij komt",r(17,21)),("en tot mijn dienaar: Doe dat! en hij doet het",r(22,29))],
10:[("Jezus nu, dit horende, heeft Zich verwonderd",r(0,4)),("en zei tot degenen, die Hem volgden",r(5,8)),("Voorwaar zeg Ik u, Ik heb zelfs in Israël zo groot een geloof niet gevonden",r(9,18))],
11:[("Maar Ik zeg u",r(0,3)),("dat velen zullen komen van oosten en westen",r(4,9)),("en zullen met Abraham, en Izak, en Jakob, aanzitten in het Koninkrijk van de hemelen",r(10,22))],
12:[("En de kinderen van het Koninkrijk zullen uitgeworpen worden in de buitenste duisternis",r(0,10)),("daar zal gehuil zijn, en knersing van de tanden",r(11,19))],
13:[("En Jezus zei tot de hoofdman over honderd",r(0,5)),("Ga heen, en u gebeure, zoals u geloofd hebt",r(6,11)),("En zijn knecht is gezond geworden op dat moment",r(12,20))],
14:[("En Jezus gekomen zijnde in het huis van Petrus",r(0,7)),("zag zijn vrouws moeder te bed liggen, hebbende de koorts",r(8,14))],
15:[("En Hij raakte haar hand aan",r(0,4)),("en de koorts verliet haar",r(5,9)),("en zij stond op, en diende hen",r(10,14))],
})
S.update({
16:[("En als het laat geworden was",r(0,2)),("hebben zij velen, van de duivel bezeten, tot Hem gebracht",r(3,6)),("en Hij wierp de boze geesten uit met de woorde",r(7,11)),("en Hij genas allen, die er slecht aan toe waren",r(12,17))],
17:[("Opdat vervuld zou worden, dat gesproken was door Jesaja, de profeet, zeggende",r(0,8)),("Hij heeft onze ziekten op Zich genomen, en onze ziekten gedragen",r(9,17))],
18:[("En Jezus, vele menigten ziende rondom Zich",r(0,7)),("beval aan de andere zijde over te varen",r(8,12))],
19:[("En er kwam een zeker Schriftgeleerde tot Hem, en zei tot Hem",r(0,5)),("Meester! ik zal U volgen, waar U ook heengaat",r(6,11))],
20:[("En Jezus zei tot hem",r(0,4)),("De vossen hebben holen, en de vogels des hemels nesten",r(5,14)),("maar de Zoon des mensen heeft niet, waar Hij het hoofd nederlegge",r(15,25))],
21:[("En een ander uit Zijn discipelen zei tot Hem",r(0,6)),("Heere! laat mij toe, dat ik eerst heenga, en mijn vader begrave",r(7,16))],
22:[("Maar Jezus zei tot hem",r(0,4)),("Volg Mij",r(5,6)),("en laat de doden hun doden begraven",r(7,14))],
23:[("En als Hij in het schip gegaan was",r(0,5)),("zijn Hem Zijn discipelen gevolgd",r(6,10))],
24:[("En ziet, er ontstond een grote onstuimigheid in de zee",r(0,7)),("zo dat het schip van de golven bedekt werd",r(8,14)),("maar Hij sliep",r(15,17))],
25:[("En Zijn discipelen, bij Hem komende, hebben Hem opgewekt, zeggende",r(0,7)),("Heere, behoed ons, wij vergaan",r(8,11))],
})
S.update({
26:[("En Hij zei tot hen",r(0,2)),("Wat bent u vreesachtig, u kleingelovigen",r(3,6)),("Toen stond Hij op, en bestrafte de winden en de zee",r(7,14)),("en er werd grote stilte",r(15,18))],
27:[("En de mensen verwonderden zich, zeggende",r(0,4)),("Wat voor Een is Deze, dat ook de winden en de zee Hem gehoorzaam zijn",r(5,16))],
28:[("En als Hij over aan de andere zijde was gekomen in het land van de Gergesenen",r(0,10)),("zijn Hem twee, van de duivel bezeten, ontmoet, komende uit de graven",r(11,18)),("die zeer wreed waren, zo dat niemand door die weg kon voorbij gaan",r(19,29))],
29:[("En ziet, zij riepen, zeggende",r(0,3)),("Jezus, U Zoon van God! wat hebben wij met U te doen",r(4,11)),("Bent U hier gekomen om ons te pijnigen voor de tijd",r(12,17))],
30:[("En verre van hen was een kudde met veel zwijnen, weidende",r(0,8))],
31:[("En de demonen baden Hem, zeggende",r(0,5)),("Als U ons uitwerpt, laat ons toe, dat wij in die kudde zwijnen varen",r(6,16))],
32:[("En Hij zei tot hen: Ga heen",r(0,3)),("En zij uitgaande, voeren heen in de kudde zwijnen",r(4,12)),("en ziet, de hele kudde zwijnen stortte van de steilte af in de zee",r(13,26)),("en zij stierven in het water",r(27,31))],
33:[("En die ze weidden, zijn gevlucht",r(0,3)),("en als zij in de stad gekomen waren, boodschapten zij al deze dingen",r(4,10)),("en wat de bezetenen gebeurd was",r(11,14))],
34:[("En ziet, de hele stad ging uit, Jezus tegemoet",r(0,9)),("en als zij Hem zagen, baden zij, dat Hij uit hun gebied wilde vertrekken",r(10,19))],
})
def build(u,o,w=False):
 src=load_tr_chapter(u,o,chapter=8,osis_book='Matt');p=ROOT/'data/mattheus/8.json';d=json.loads(p.read_text(encoding='utf-8'));reviewed_through=max(S);rev={'book':'mattheus','chapter':8,'reviewed_through':reviewed_through,'verses':{}}
 for v in d['verses'][:reviewed_through]:
  n=int(v['number']);ts=src[n];gs=S[n];ids=[i for _,x in gs for i in x]
  if sorted(ids)!=list(range(len(ts))) or len(ids)!=len(set(ids)):raise ValueError(n)
  v['grondtekst']=[{'woord':t['woord'],'strongs':t['display_strong'],'lemma_strongs':t['lemma_strong'],'morfologie':t['morphology'],**({'tvm':t['tvm']} if t.get('tvm') else {})} for t in ts];v['woordnummers']=[mapping(a,x,ts,n) for a,x in gs];occ={}
  for x in v['woordnummers']:occ[x['tekst']]=occ.get(x['tekst'],0)+1;x['voorkomen']=occ[x['tekst']];x['herkomst']['referentie']=f'MAT 8:{n}'
  rev['verses'][str(n)]=[{'tekst':a,'bronindices':x,'reviewstatus':'handmatig_gecontroleerd'} for a,x in gs]
 if w:
  p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');(ROOT/'data/woordnummers-review/mattheus-8.json').write_text(json.dumps(rev,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');ip=ROOT/'data/woordnummers-inline/mattheus.json';z=json.loads(ip.read_text(encoding='utf-8'));z['chapters']['8']={str(v['number']):v['woordnummers'] for v in d['verses'][:reviewed_through]};ip.write_text(json.dumps(z,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 return {'verses':reviewed_through,'tokens':sum(len(src[n]) for n in range(1,reviewed_through+1))}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--utr',type=Path,required=True);p.add_argument('--osis',type=Path,required=True);p.add_argument('--write',action='store_true');a=p.parse_args();print(build(a.utr,a.osis,a.write))
