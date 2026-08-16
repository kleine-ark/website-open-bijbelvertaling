#!/usr/bin/env python3
"""Publiceer gecontroleerde TR-koppelingen voor Mattheüs 20 in versbatches."""
from __future__ import annotations
import argparse, json
from pathlib import Path
from rebuild_nt_tr_strongs import load_tr_chapter
from rebuild_johannes2_tr_strongs import mapping, r
ROOT = Path(__file__).resolve().parents[1]
SPECS = {
1:[("Want het Koninkrijk van de hemelen is gelijk aan een heer van het huis, die met de morgenstond uitging, om arbeiders te huren in zijn wijngaard",r(0,18))],
2:[("En als hij met de arbeiders eens geworden was, voor een penning overdag, zond hij hen heen in zijn wijngaard",r(0,14))],
3:[("En uitgegaan zijnde ongeveer het derde uur, zag hij anderen, werkloos staande op de markt",r(0,12))],
4:[("En hij zei daartoe: Ga ook u heen in de wijngaard, en zo wat recht is, zal ik u geven. En zij gingen",r(0,17))],
5:[("Opnieuw uitgegaan zijnde ongeveer het zesde en het negende uur, deed hij evenzo",r(0,8))],
6:[("En uitgegaan zijnde ongeveer het elfde uur, vond hij anderen werkloos staande, en zei tot hen: Wat staat u hier de hele dag werkloos?",r(0,19))],
7:[("Zij zeiden tot hem: Omdat ons niemand gehuurd heeft. Hij zei tot hen: Ga ook u heen in de wijngaard, en zo wat recht is, zult u ontvangen",r(0,19))],
8:[("Als het nu avond geworden was, zei de heer van de wijngaard, tot zijn rentmeester: Roep de arbeiders, en geef hun het loon, beginnende van de laatsten tot de eersten",r(0,25))],
9:[("En als zij kwamen, die op het elfde uur gehuurd waren, ontvingen zij ieder een penning",r(0,9))],
10:[("En de eerste komende, meenden, dat zij meer ontvangen zouden; en zij zelf ontvingen ook elk een penning",r(0,13))],
11:[("En die ontvangen hebbende, morden zij tegen de heer van het huis",r(0,5))],
12:[("Zeggende: Deze laatsten hebben maar één uur gewerkt, en u hebt ze ons gelijk gemaakt, die de last overdag en de hitte gedragen hebben",r(0,21))],
13:[("Maar hij, antwoordende, zei tot één van hen: Vriend! ik doe u geen onrecht; bent u niet met mij eens geworden voor een penning?",r(0,13))],
14:[("Neem het uwe en ga heen. Ik wil deze laatsten ook geven, gelijk als u",r(0,13))],
15:[("Of is het mij niet geoorloofd, te doen met het mijne, wat ik wil? Of is uw oog boos, omdat ik goed ben?",r(0,19))],
16:[("Zo zullen de laatsten de eersten zijn, en de eersten de laatsten; want velen zijn geroepen, maar weinigen uitverkoren",r(0,15))],
17:[("En Jezus, opgaande naar Jeruzalem, nam tot Zich de twaalf discipelen alleen op de weg, en zei tot hen:",r(0,17))],
18:[("Zie, wij gaan op naar Jeruzalem, en de Zoon des mensen zal de overpriesteren en Schriftgeleerden overgeleverd worden, en zij zullen Hem ter dood veroordelen",r(0,17))],
19:[("En zij zullen Hem de heidenen overleveren, om Hem te bespotten en te geselen, en te kruisigen; en op de derde dag zal Hij weer opstaan",r(0,16))],
20:[("Toen kwam de moeder van de zonen van Zebedeüs tot Hem met haar zonen, Hem aanbiddende, en begerende wat van Hem",r(0,17))],
21:[("En Hij zei tot haar: Wat wilt u? Zij zei tot Hem: Zeg, dat deze mijn twee zonen zitten mogen, de één tot Uw rechter- en de ander tot Uw linkerhand in Uw Koninkrijk",r(0,27))],22:[("Maar Jezus antwoordde en zei: U weet niet wat u begeert; kunt u de drinkbeker drinken, die Ik drinken zal, en met de doop gedoopt worden, waarmee Ik gedoopt word? Zij zeiden tot Hem: Wij kunnen",r(0,26))],23:[("En Hij zei tot hen: Mijn drinkbeker zult u wel drinken, en met de doop, waarmee Ik gedoopt word, zult u gedoopt worden; maar het zitten tot Mijn rechter-, en tot Mijn linkerhand, staat bij Mij niet te geven, maar het zal gegeven worden die het bereid is van Mijn Vader",r(0,35))],24:[("En als de andere tien dat hoorden, namen zij het zeer kwalijk van de twee broers",r(0,8))],25:[("En als Jezus hen tot Zich geroepen had, zei Hij: U weet, dat de oversten van de volken heerschappij voeren over hen, en de grote gebruiken macht over hen",r(0,18))],26:[("Maar zo zal het onder u niet zijn; maar zo wie onder u zal willen groot worden, die zij uw dienaar;",r(0,16))],27:[("En zo wie onder u zal willen de eerste zijn, die zij uw dienaar",r(0,10))],28:[("Zoals de Zoon des mensen niet is gekomen om gediend te worden, maar om te dienen, en Zijn ziel te geven tot een losprijs voor velen",r(0,17))],29:[("En als zij van Jericho uitgingen, is Hem een grote menigte gevolgd",r(0,8))],30:[("En ziet, twee blinden, zittende aan de weg, als zij hoorden, dat Jezus voorbijging, riepen, zeggende: Heere, U Zoon van David! ontferm U over ons",r(0,18))],31:[("En de menigte bestrafte hen, opdat zij zwijgen zouden; maar zij riepen te meer, zeggende: Ontferm U over ons, Heere, U Zoon van David!",r(0,16))],32:[("En Jezus, stil staande, riep hen en zei: Wat wilt u, dat Ik u doe?",r(0,11))],33:[("Zij zeiden tot Hem: Heere! dat onze ogen geopend worden",r(0,7))],34:[("En Jezus, innerlijk bewogen zijnde met barmhartigheid, raakte hun ogen aan; en meteen werden hun ogen ziende, en zij volgden Hem",r(0,16))],}
def build(utr_path:Path,osis_path:Path,write=False):
 source=load_tr_chapter(utr_path,osis_path,chapter=20,osis_book='Matt'); chapter_path=ROOT/'data'/'mattheus'/'20.json'; chapter=json.loads(chapter_path.read_text(encoding='utf8')); reviewed_through=max(SPECS); review={'book':'mattheus','chapter':20,'reviewed_through':reviewed_through,'verses':{}}
 for verse in chapter['verses'][:reviewed_through]:
  number=int(verse['number']); tokens=source[number]; groups=SPECS[number]; covered=[i for _,ids in groups for i in ids]
  if sorted(covered)!=list(range(len(tokens))) or len(set(covered))!=len(tokens): raise ValueError(f'Mattheüs 20:{number}: onvolledige of dubbele handmatige review')
  verse['grondtekst']=[{'woord':t['woord'],'strongs':t['display_strong'],'lemma_strongs':t['lemma_strong'],'morfologie':t['morphology'],**({'tvm':t['tvm']} if t.get('tvm') else {})} for t in tokens]; verse['woordnummers']=[mapping(a,ids,tokens,number) for a,ids in groups]
  for item in verse['woordnummers']: item['herkomst']['referentie']=f'MAT 20:{number}'
  review['verses'][str(number)]=[{'tekst':a,'bronindices':ids,'reviewstatus':'handmatig_gecontroleerd'} for a,ids in groups]
 if write:
  chapter_path.write_text(json.dumps(chapter,ensure_ascii=False,indent=2)+'\n',encoding='utf8'); (ROOT/'data'/'woordnummers-review'/'mattheus-20.json').write_text(json.dumps(review,ensure_ascii=False,indent=2)+'\n',encoding='utf8'); inline_path=ROOT/'data'/'woordnummers-inline'/'mattheus.json'; inline=json.loads(inline_path.read_text(encoding='utf8')); inline['chapters']['20']={str(v['number']):v['woordnummers'] for v in chapter['verses'][:reviewed_through]}; inline_path.write_text(json.dumps(inline,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 return {'verses':reviewed_through,'tokens':sum(len(source[n]) for n in range(1,reviewed_through+1))}
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--utr',type=Path,required=True);parser.add_argument('--osis',type=Path,required=True);parser.add_argument('--write',action='store_true');args=parser.parse_args();print(json.dumps(build(args.utr,args.osis,args.write),indent=2))
