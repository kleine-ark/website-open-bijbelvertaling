#!/usr/bin/env python3
"""Publiceer handmatig beoordeelde TR-koppelingen voor Mattheüs 7."""
from __future__ import annotations
import argparse,json
from pathlib import Path
from rebuild_nt_tr_strongs import load_tr_chapter
from rebuild_johannes2_tr_strongs import mapping,r
ROOT=Path(__file__).resolve().parents[1]
S={
1:[("Oordeel niet, opdat u niet geoordeeld wordt",r(0,4))],
2:[("Want met welk oordeel u oordeelt, zult u geoordeeld worden",r(0,5)),("en met welke mate u meet, zal u wedergemeten worden",r(6,12))],
3:[("En wat ziet u de splinter, die in het oog van uw broeder is",r(0,11)),("maar de balk, die in uw oog is, merkt u niet",r(12,20))],
4:[("Of, hoe zult u tot uw broeder zeggen",r(0,5)),("Laat toe, dat ik de splinter uit uw oog uitdoe",r(6,13)),("en zie, er is een balk in uw oog",r(14,21))],
5:[("U geveinsde",r(0)),("werp eerst de balk uit uw oog",r(1,8)),("en dan zult u bekijken, om de splinter uit het oog van uw broeder uit te doen",r(9,20))],
}
S.update({
6:[("Geeft het heilige de honden niet",r(0,5)),("noch werpt uw parels voor de zwijnen",r(6,13)),("opdat zij niet te eniger tijd dezelfde met hun voeten vertreden",r(14,20)),("en zich omkerende, u verscheuren",r(21,24))],
7:[("Bid, en u zal gegeven worden",r(0,3)),("zoek, en u zult vinden",r(4,6)),("klopt, en u zal opengedaan worden",r(7,10))],
8:[("Want een ieder die bidt, die ontvangt",r(0,4)),("en die zoekt, die vindt",r(5,8)),("en die klopt, die zal opengedaan worden",r(9,12))],
9:[("Of wat mens is er onder u",r(0,5)),("zo zijn zoon hem zou bidden om brood",r(6,12)),("die hem een steen zal geven",r(13,16))],
10:[("En zo hij hem om een vis zou bidden",r(0,3)),("die hem een slang zal geven",r(4,7))],
11:[("Als dan u, die boos bent, weet uw kinderen goede gaven te geven",r(0,11)),("hoeveel te meer zal uw Vader, Die in de hemelen is, goede gaven geven van hen, die ze van Hem bidden",r(12,25))],
12:[("Alle dingen dan, die u wilt, dat u de mensen zouden doen",r(0,9)),("doet u hun ook zo",r(10,14)),("want dat is de wet en de profeten",r(15,22))],
13:[("Ga in door de nauwe poort",r(0,4)),("want wijd is de poort, en breed is de weg, die tot het verderf leidt",r(5,17)),("en velen zijn er, die daardoor ingaan",r(18,24))],
14:[("Want de poort is nauw, en de weg is nauw, die tot het leven leidt",r(0,12)),("en weinigen zijn er, die dezelfde vinden",r(13,18))],
15:[("Maar wees op uw hoede voor de valse profeten",r(0,4)),("die in schaapsklederen tot u komen",r(5,11)),("maar van binnen zijn zij grijpende wolven",r(12,16))],
})
S.update({
16:[("Aan hun vruchten zult u hen kennen",r(0,5)),("Leest men ook een druif van doornen, of vijgen van distelen",r(6,14))],
17:[("Zo een ieder goede boom brengt voort goede vruchten",r(0,6)),("en een kwade boom brengt voort kwade vruchten",r(7,13))],
18:[("Een goede boom kan geen kwade vruchten voortbrengen",r(0,6)),("noch een kwade boom goede vruchten voortbrengen",r(7,12))],
19:[("Een ieder boom, die geen goede vrucht voortbrengt",r(0,5)),("wordt omgehakt en in het vuur geworpen",r(6,10))],
20:[("Zo zult u dan dezelfde aan hun vruchten kennen",r(0,6))],
21:[("Niet een ieder die tot Mij zegt: Heere, Heere! zal ingaan in het Koninkrijk van de hemelen",r(0,12)),("maar die daar doet de wil van Mijn Vader, Die in de hemelen is",r(13,23))],
22:[("Velen zullen op die dag tot Mij zeggen: Heere, Heere",r(0,8)),("hebben wij niet in Uw Naam geprofeteerd",r(9,13)),("en in Uw Naam demonen uitgeworpen",r(14,19)),("en in Uw Naam vele krachten gedaan",r(20,26))],
23:[("En dan zal Ik hun openlijk aanzeggen",r(0,4)),("Ik heb u nooit gekend",r(5,7)),("ga weg van Mij, u, die de ongerechtigheid werkt",r(8,14))],
24:[("Ieder dan, die deze Mijn woorden hoort en die doet",r(0,10)),("die zal Ik vergelijken bij een voorzichtig man",r(11,14)),("die zijn huis op een steenrots gebouwd heeft",r(15,22))],
25:[("En er is slagregen neergevallen, en de waterstromen zijn gekomen, en de winden hebben gewaaid",r(0,11)),("en zijn tegen dat huis aangevallen",r(12,16)),("en het is niet gevallen, want het was op de steenrots gegrond",r(17,24))],
})
S.update({
26:[("En een ieder die deze Mijn woorden hoort en dezelfde niet doet",r(0,11)),("die zal bij een dwaze man vergeleken worden",r(12,14)),("die zijn huis op het zand gebouwd heeft",r(15,22))],
27:[("En de slagregen is neergevallen, en de waterstromen zijn gekomen, en de winden hebben gewaaid",r(0,11)),("en zijn tegen dat huis aangeslagen",r(12,16)),("en het is gevallen, en zijn val was groot",r(17,24))],
28:[("En het is gebeurd, als Jezus deze woorden geëindigd had",r(0,8)),("dat de menigten zich ontzetten over Zijn leer",r(9,15))],
29:[("Want Hij leerde hen, als macht hebbende",r(0,6)),("en niet als de Schriftgeleerden",r(7,11))],
})
def build(u,o,w=False):
 src=load_tr_chapter(u,o,chapter=7,osis_book='Matt');p=ROOT/'data/mattheus/7.json';d=json.loads(p.read_text(encoding='utf-8'));reviewed_through=max(S);rev={'book':'mattheus','chapter':7,'reviewed_through':reviewed_through,'verses':{}}
 for v in d['verses'][:reviewed_through]:
  n=int(v['number']);ts=src[n];gs=S[n];ids=[i for _,x in gs for i in x]
  if sorted(ids)!=list(range(len(ts))) or len(ids)!=len(set(ids)):raise ValueError(n)
  v['grondtekst']=[{'woord':t['woord'],'strongs':t['display_strong'],'lemma_strongs':t['lemma_strong'],'morfologie':t['morphology'],**({'tvm':t['tvm']} if t.get('tvm') else {})} for t in ts];v['woordnummers']=[mapping(a,x,ts,n) for a,x in gs];occ={}
  for x in v['woordnummers']:occ[x['tekst']]=occ.get(x['tekst'],0)+1;x['voorkomen']=occ[x['tekst']];x['herkomst']['referentie']=f'MAT 7:{n}'
  rev['verses'][str(n)]=[{'tekst':a,'bronindices':x,'reviewstatus':'handmatig_gecontroleerd'} for a,x in gs]
 if w:
  p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');(ROOT/'data/woordnummers-review/mattheus-7.json').write_text(json.dumps(rev,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');ip=ROOT/'data/woordnummers-inline/mattheus.json';z=json.loads(ip.read_text(encoding='utf-8'));z['chapters']['7']={str(v['number']):v['woordnummers'] for v in d['verses'][:reviewed_through]};ip.write_text(json.dumps(z,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 return {'verses':reviewed_through,'tokens':sum(len(src[n]) for n in range(1,reviewed_through+1))}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--utr',type=Path,required=True);p.add_argument('--osis',type=Path,required=True);p.add_argument('--write',action='store_true');a=p.parse_args();print(build(a.utr,a.osis,a.write))
