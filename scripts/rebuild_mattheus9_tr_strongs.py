#!/usr/bin/env python3
"""Publiceer handmatig beoordeelde TR-koppelingen voor Mattheüs 9."""
from __future__ import annotations
import argparse,json
from pathlib import Path
from rebuild_nt_tr_strongs import load_tr_chapter
from rebuild_johannes2_tr_strongs import mapping,r
ROOT=Path(__file__).resolve().parents[1]
S={
1:[("En in het schip gegaan zijnde",r(0,4)),("voer Hij over",r(5)),("en kwam in Zijn stad",r(6,11)),("En ziet",r(12,13)),("zij brachten tot Hem een geraakte",r(14,16)),("op een bed liggende",r(17,19))],
2:[("En Jezus, hun geloof ziende",r(0,6)),("zei tot de geraakte",r(7,9)),("Zoon! heb goede moed",r(10,11)),("uw zonden zijn u vergeven",r(12,16))],
3:[("En ziet, sommigen van de Schriftgeleerden zeiden in zichzelf",r(0,7)),("Deze lastert God",r(8,9))],
4:[("En Jezus, ziende hun gedachten, zei",r(0,7)),("Waarom overdenkt u kwaad in uw harten",r(8,16))],
5:[("Want wat is lichter te zeggen",r(0,4)),("De zonden zijn u vergeven",r(5,8)),("of te zeggen: Sta op en wandel",r(9,13))],
}
S.update({
6:[("Maar opdat u mag weten, dat de Zoon des mensen macht heeft op de aarde, de zonden te vergeven",r(0,14)),("toen zei Hij tot de geraakte",r(15,18)),("Sta op, neem uw bed op, en ga heen naar uw huis",r(19,29))],
7:[("En hij opgestaan zijnde, ging heen naar zijn huis",r(0,6))],
8:[("De menigten nu dat ziende, hebben zich verwonderd",r(0,4)),("en God verheerlijkt, die zulke macht de mensen gegeven had",r(5,14))],
9:[("En Jezus, van daar voortgaande",r(0,4)),("zag een mens in het tolhuis zitten, genoemd Mattheüs",r(5,12)),("en zei tot hem: Volg Mij",r(13,17)),("En hij opstaande, volgde Hem",r(18,21))],
10:[("En het gebeurde, als Hij in het huis van Mattheüs aanzat",r(0,6)),("ziet, vele tollenaars en zondaars kwamen en zaten mee aan, met Jezus en Zijn discipelen",r(7,20))],
11:[("En de Farizeën, dat ziende, zeiden tot Zijn discipelen",r(0,7)),("Waarom eet uw Meester met de tollenaren en de zondaren",r(8,18))],
12:[("Maar Jezus, dat horende, zei tot hen",r(0,5)),("Die gezond zijn hebben de dokter niet nodig",r(6,11)),("maar die ziek zijn",r(12,15))],
13:[("Maar gaat heen en leert, wat het zij",r(0,4)),("Ik wil barmhartigheid, en niet offergave",r(5,9)),("want Ik ben niet gekomen om te roepen rechtvaardigen, maar zondaars tot bekering",r(10,18))],
14:[("Toen kwamen de discipelen van Johannes tot Hem, zeggende",r(0,6)),("Waarom vasten wij en de Farizeën veel",r(7,14)),("en Uw discipelen vasten niet",r(15,20))],
15:[("En Jezus zei tot hen",r(0,4)),("Kunnen ook de bruiloftskinderen treuren, zolang de Bruidegom bij hen is",r(5,18)),("Maar de dagen zullen komen, wanneer de Bruidegom van hen zal weggenomen zijn",r(19,27)),("en dan zullen zij vasten",r(28,30))],
})
S.update({
16:[("Ook zet niemand een lap niet gekrompen laken op een oud kleed",r(0,8)),("want zijn aangezette lap scheurt af van het kleed",r(9,16)),("en er wordt een ergere scheur",r(17,20))],
17:[("Noch doet men nieuwe wijn in oude lederen zakken",r(0,6)),("anders zo barsten de lederen zakken, en de wijn wordt uitgestort, en de lederen zakken verderven",r(7,20)),("maar men doet nieuwe wijn in nieuwe lederen zakken, en beide samen worden behouden",r(21,30))],
18:[("Als Hij deze dingen tot hen sprak",r(0,3)),("ziet, een overste kwam en aanbad Hem, zeggende",r(4,9)),("Mijn dochter is nu meteen gestorven",r(10,15)),("maar kom en leg Uw hand op haar, en zij zal leven",r(16,25))],
19:[("En Jezus opgestaan zijnde, volgde hem, en Zijn discipelen",r(0,9))],
20:[("En ziet, een vrouw die twaalf jaren het bloedvloeien gehad had",r(0,5)),("komende tot Hem van achteren, raakte de zoom van Zijn kleed aan",r(6,13))],
21:[("Want zij zei in zichzelf",r(0,3)),("Als ik alleen Zijn kleed aanraak, zo zal ik gezond worden",r(4,10))],
22:[("En Jezus, Zich omkerende, en haar ziende, zei",r(0,7)),("Heb goede moed, dochter! uw geloof heeft u behouden",r(8,14)),("En de vrouw werd gezond vanaf dat moment",r(15,22))],
23:[("En als Jezus in het huis van de oversten kwam",r(0,8)),("en zag de pijpers en de woelende menigte",r(9,16))],
24:[("Zei Hij tot hen: Vertrek",r(0,2)),("want het dochtertje is niet dood, maar slaapt",r(3,9)),("En zij belachten Hem",r(10,12))],
25:[("Als nu de menigte uitgedreven was",r(0,4)),("ging Hij in, en greep haar hand",r(5,9)),("en het dochtertje stond op",r(10,13))],
})
S.update({
26:[("En dit gerucht ging uit door dat hele land",r(0,9))],
27:[("En als Jezus van daar voortging",r(0,4)),("zijn Hem twee blinden gevolgd, roepende en zeggende",r(5,11)),("U Zoon van David, ontferm U over ons",r(12,15))],
28:[("En als Hij in huis gekomen was, kwamen de blinden tot Hem",r(0,8)),("En Jezus zei tot hen: Gelooft u, dat Ik dat doen kan",r(9,18)),("Zij zeiden tot Hem: Ja, Heere",r(19,22))],
29:[("Toen raakte Hij hun ogen aan, zeggende",r(0,5)),("U gebeure naar uw geloof",r(6,11))],
30:[("En hun ogen zijn geopend geworden",r(0,4)),("En Jezus heeft hun zeer streng verboden, zeggende",r(5,10)),("Zie, dat niemand het wete",r(11,13))],
31:[("Maar zij, uitgegaan zijnde, hebben Hem bekend gemaakt door dat hele land",r(0,9))],
32:[("Als deze nu uitgingen, ziet",r(0,3)),("zo brachten zij tot Hem een mens, die stom en van de duivel bezeten was",r(4,8))],
33:[("En als de duivel uitgeworpen was, sprak de stomme",r(0,6)),("En de menigten verwonderden zich, zeggende",r(7,11)),("Er is nooit zoiets in Israël gezien",r(12,18))],
34:[("Maar de Farizeën zeiden",r(0,3)),("Hij werpt de demonen uit door de overste van de demonen",r(4,11))],
35:[("En Jezus omging al de steden en plaatsen",r(0,9)),("lerende in hun synagogen",r(10,14)),("en predikende het Evangelie van het Koninkrijk",r(15,20)),("en genezende alle ziekte en alle kwalen onder het volk",r(21,30))],
36:[("En Hij, de menigten ziende, werd innerlijk met ontferming bewogen over hen",r(0,6)),("omdat zij vermoeid en verstrooid waren, gelijk schapen, die geen herder hebben",r(7,16))],
37:[("Toen zei Hij tot Zijn discipelen",r(0,4)),("De oogst is wel groot",r(5,8)),("maar de arbeiders zijn weinige",r(9,12))],
38:[("Bid dan de Heere van de oogst",r(0,5)),("dat Hij arbeiders in Zijn oogst uitstote",r(6,12))],
})
def build(u,o,w=False):
 src=load_tr_chapter(u,o,chapter=9,osis_book='Matt');p=ROOT/'data/mattheus/9.json';d=json.loads(p.read_text(encoding='utf-8'));token_sets={n:src[n] for n in S};token_sets.update({1:src[1]+src[2][:8],2:src[2][8:]});reviewed_through=max(S);rev={'book':'mattheus','chapter':9,'reviewed_through':reviewed_through,'versgrens_afwijking':{'1':'De tweede Nederlandse zin volgt bronvast uit MAT 9:2 tokens 1-8; MAT 9:2 start vervolgens bij token 9.'},'verses':{}}
 for v in d['verses'][:reviewed_through]:
  n=int(v['number']);ts=token_sets[n];gs=S[n];ids=[i for _,x in gs for i in x]
  if sorted(ids)!=list(range(len(ts))) or len(ids)!=len(set(ids)):raise ValueError(n)
  v['grondtekst']=[{'woord':t['woord'],'strongs':t['display_strong'],'lemma_strongs':t['lemma_strong'],'morfologie':t['morphology'],**({'tvm':t['tvm']} if t.get('tvm') else {})} for t in ts];v['woordnummers']=[mapping(a,x,ts,n) for a,x in gs];occ={}
  for x in v['woordnummers']:occ[x['tekst']]=occ.get(x['tekst'],0)+1;x['voorkomen']=occ[x['tekst']];x['herkomst']['referentie']=f'MAT 9:{n}'
  rev['verses'][str(n)]=[{'tekst':a,'bronindices':x,'reviewstatus':'handmatig_gecontroleerd'} for a,x in gs]
 if w:
  p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');(ROOT/'data/woordnummers-review/mattheus-9.json').write_text(json.dumps(rev,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');ip=ROOT/'data/woordnummers-inline/mattheus.json';z=json.loads(ip.read_text(encoding='utf-8'));z['chapters']['9']={str(v['number']):v['woordnummers'] for v in d['verses'][:reviewed_through]};ip.write_text(json.dumps(z,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 return {'verses':reviewed_through,'tokens':sum(len(token_sets[n]) for n in range(1,reviewed_through+1))}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--utr',type=Path,required=True);p.add_argument('--osis',type=Path,required=True);p.add_argument('--write',action='store_true');a=p.parse_args();print(build(a.utr,a.osis,a.write))
