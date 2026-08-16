#!/usr/bin/env python3
"""Publiceer gecontroleerde TR-koppelingen voor Johannes 17 in versbatches."""
from __future__ import annotations
import argparse,json
from pathlib import Path
from rebuild_nt_tr_strongs import load_tr_chapter
from rebuild_johannes2_tr_strongs import mapping,r
ROOT=Path(__file__).resolve().parents[1]
S={
1:[("Dit heeft Jezus gesproken",r(0,3)),("en Hij hief Zijn ogen op naar de hemel",r(4,11)),("en zei",r(12,13)),("Vader",r(14)),("het uur is gekomen",r(15,17)),("verheerlijk Uw Zoon",r(18,21)),("opdat ook Uw Zoon U verheerlijke",r(22,28))],
2:[("Zoals U Hem macht gegeven hebt over alle vlees",r(0,5)),("opdat al wat U Hem gegeven hebt",r(6,10)),("Hij hun het eeuwige leven geeft",r(11,14))],
3:[("En dit is het eeuwige leven",r(0,5)),("dat zij U kennen",r(6,8)),("de enige waarachtigen God",r(9,12)),("en Jezus Christus, Die U gezonden hebt",r(13,17))],
4:[("Ik heb U verheerlijkt op de aarde",r(0,5)),("Ik heb voltooid het werk",r(6,8)),("dat U Mij gegeven hebt om te doen",r(9,13))],
5:[("En nu verheerlijk Mij, U Vader",r(0,5)),("bij Uzelf",r(6,7)),("met de heerlijkheid, die Ik bij U had, voordat de wereld was",r(8,18))],
6:[("Ik heb Uw Naam geopenbaard de mensen",r(0,5)),("die U Mij uit de wereld gegeven hebt",r(6,11)),("Zij waren Uw",r(12,13)),("en U hebt Mij deze gegeven",r(14,17)),("en zij hebben Uw woord bewaard",r(18,22))],
7:[("Nu hebben zij bekend",r(0,1)),("dat alles, wat U Mij gegeven hebt",r(2,6)),("van U is",r(7,9))],
8:[("Want de woorden, die U Mij gegeven hebt",r(0,5)),("heb Ik hun gegeven",r(6,7)),("en zij hebben ze ontvangen",r(8,10)),("en zij hebben werkelijk bekend",r(11,13)),("dat Ik van U uitgegaan ben",r(14,17)),("en hebben geloofd",r(18,19)),("dat U Mij gezonden hebt",r(20,23))],
9:[("Ik bid voor hen",r(0,3)),("Ik bid niet voor de wereld",r(4,8)),("maar voor degenen, die U Mij gegeven hebt",r(9,13)),("want ze zijn van U",r(14,16))],
10:[("En al het Mijne is Uw",r(0,5)),("en het van U is van Mij",r(6,9)),("en Ik ben in hen verheerlijkt",r(10,13))],}
S.update({
11:[("En Ik ben niet meer in de wereld",r(0,6)),("maar deze zijn in de wereld",r(7,12)),("en Ik komt tot U",r(13,17)),("Heilige Vader",r(18,19)),("bewaar ze in Uw Naam",r(20,25)),("die U Mij gegeven hebt",r(26,28)),("opdat zij één zijn, gelijk als Wij",r(29,33))],
12:[("Toen Ik met hen in de wereld was",r(0,6)),("bewaarde Ik ze in Uw Naam",r(7,13)),("Die U Mij gegeven hebt, heb Ik bewaard",r(14,17)),("en niemand uit hen is verloren gegaan",r(18,22)),("dan de zoon van de verderfenis",r(23,28)),("opdat de Schrift vervuld wordt",r(29,32))],
13:[("Maar nu kom Ik tot U",r(0,4)),("en spreek dit in de wereld",r(5,10)),("opdat zij Mijn blijdschap vervuld mogen hebben in zichzelf",r(11,19))],
14:[("Ik heb hun Uw woord gegeven",r(0,5)),("en de wereld heeft ze gehaat",r(6,10)),("omdat zij van de wereld niet zijn",r(11,16)),("gelijk als Ik van de wereld niet ben",r(17,23))],
15:[("Ik bid niet",r(0,1)),("dat U hen uit de wereld wegneemt",r(2,7)),("maar dat U hen bewaart van de boze",r(8,14))],
16:[("Zij zijn niet van de wereld",r(0,4)),("zoals Ik van de wereld niet ben",r(5,11))],
17:[("Heilig ze in Uw waarheid",r(0,5)),("Uw woord is de waarheid",r(6,11))],
18:[("Zoals U Mij gezonden hebt in de wereld",r(0,5)),("zo heb Ik hen ook in de wereld gezonden",r(6,11))],
19:[("En Ik heilige Mijzelf voor hen",r(0,5)),("opdat ook zij geheiligd mogen zijn in waarheid",r(6,12))],
20:[("En Ik bid niet alleen voor deze",r(0,5)),("maar ook voor degenen, die door hun woord in Mij geloven zullen",r(6,16))],
21:[("Opdat zij allen één zijn",r(0,3)),("zoals U, Vader, in Mij, en Ik in U",r(4,11)),("dat ook zij in Ons één zijn",r(12,18)),("opdat de wereld gelooft",r(19,22)),("dat U Mij gezonden hebt",r(23,26))],
22:[("En Ik heb hun de heerlijkheid gegeven, die U Mij gegeven hebt",r(0,8)),("opdat zij één zijn",r(9,11)),("gelijk als Wij Één zijn",r(12,15))],
23:[("Ik in hen, en U in Mij",r(0,6)),("opdat zij volmaakt zijn in één",r(7,11)),("en opdat de wereld bekenne",r(12,16)),("dat U Mij gezonden hebt",r(17,20)),("en hen liefgehad hebt",r(21,23)),("zoals U Mij liefgehad hebt",r(24,26))],
24:[("Vader, Ik wil, dat waar Ik ben, ook die bij Mij zijn, die U Mij gegeven hebt",r(0,12)),("opdat zij Mijn heerlijkheid mogen aanschouwen, die U Mij gegeven hebt",r(13,21)),("want U hebt Mij liefgehad",r(22,24)),("voor de grondlegging van de wereld",r(25,27))],
25:[("Rechtvaardige Vader",r(0,1)),("de wereld heeft U niet gekend",r(2,7)),("maar Ik heb U gekend",r(8,11)),("en deze hebben bekend",r(12,14)),("dat U Mij gezonden hebt",r(15,18))],
26:[("En Ik heb hun Uw Naam bekend gemaakt",r(0,5)),("en zal Hem bekend maken",r(6,7)),("opdat de liefde, waarmee U Mij liefgehad hebt, in hen zij",r(8,16)),("en Ik in hen",r(17,19))],
})
def build(u,o,w=False):
 src=load_tr_chapter(u,o,chapter=17,osis_book='John');p=ROOT/'data/johannes/17.json';d=json.loads(p.read_text(encoding='utf-8'));reviewed_through=max(S);rev={'book':'johannes','chapter':17,'reviewed_through':reviewed_through,'verses':{}}
 for v in d['verses'][:reviewed_through]:
  n=int(v['number']);ts=src[n];gs=S[n];ids=[i for _,x in gs for i in x]
  if sorted(ids)!=list(range(len(ts))) or len(ids)!=len(set(ids)):raise ValueError(n)
  v['grondtekst']=[{'woord':t['woord'],'strongs':t['display_strong'],'lemma_strongs':t['lemma_strong'],'morfologie':t['morphology'],**({'tvm':t['tvm']} if t.get('tvm') else {}),**({'bronstatus':t['bronstatus']} if t.get('bronstatus') else {})} for t in ts];v['woordnummers']=[mapping(a,x,ts,n) for a,x in gs];occ={}
  for x in v['woordnummers']:occ[x['tekst']]=occ.get(x['tekst'],0)+1;x['voorkomen']=occ[x['tekst']];x['herkomst']['referentie']=f'JHN 17:{n}'
  rev['verses'][str(n)]=[{'tekst':a,'bronindices':x,'reviewstatus':'handmatig_gecontroleerd'} for a,x in gs]
 if w:
  p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');(ROOT/'data/woordnummers-review/johannes-17.json').write_text(json.dumps(rev,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');ip=ROOT/'data/woordnummers-inline/johannes.json';z=json.loads(ip.read_text(encoding='utf-8'));z['chapters']['17']={str(v['number']):v['woordnummers'] for v in d['verses'][:reviewed_through]};ip.write_text(json.dumps(z,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 return {'verses':reviewed_through,'tokens':sum(len(src[n]) for n in range(1,reviewed_through+1))}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--utr',type=Path,required=True);p.add_argument('--osis',type=Path,required=True);p.add_argument('--write',action='store_true');a=p.parse_args();print(build(a.utr,a.osis,a.write))
