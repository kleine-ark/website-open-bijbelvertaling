#!/usr/bin/env python3
"""Publiceer gecontroleerde TR-koppelingen voor Johannes 13 in versbatches."""
from __future__ import annotations
import argparse, json
from pathlib import Path
from rebuild_nt_tr_strongs import load_tr_chapter
from rebuild_johannes2_tr_strongs import mapping, r

ROOT = Path(__file__).resolve().parents[1]
SPECS = {
  1: [("En voor het feest van het pascha",r(0,5)),("Jezus wetende",r(6,8)),("dat Zijn uur gekomen was",r(9,13)),("dat Hij uit deze wereld zou overgaan tot de Vader",r(14,22)),("zo Hij de Zijn, die in de wereld waren, liefgehad had",r(23,29)),("zo heeft Hij hen liefgehad tot het einde",r(30,33))],
  2: [("En als het avondmaal gedaan was",r(0,2)),("toen nu de duivel",r(3,5)),("in het hart",r(7,9)),("van Judas, Simons zoon, Iskariot",r(10,12)),("gegeven had",r(6)),("dat hij Hem verraden zou",r(13,15))],
  3: [("Jezus, wetende",r(0,2)),("dat de Vader Hem alle dingen",[3,4,6,7,8]),("in de handen gegeven had",[9,10,11,5]),("en dat Hij van God uitgegaan was",r(12,16)),("en tot God heenging",r(17,21))],
  4: [("Stond op van het avondmaal",r(0,3)),("en legde Zijn kleren af",r(4,7)),("en nemende een linnen doek",r(8,10)),("omgordde Zichzelf",r(11,12))],
  5: [("Daarna goot Hij water in het bekken",r(0,5)),("en begon de voeten van de discipelen te wassen",r(6,12)),("en af te drogen met de linnen doek",r(13,16)),("waarmee Hij omgord was",r(17,19))],
  6: [("Hij dan kwam tot Simon Petrus",r(0,4)),("en die zei tot Hem",r(5,8)),("Heere",r(9)),("zult U mij de voeten wassen",r(10,14))],
  7: [("Jezus antwoordde en zei tot hem",r(0,4)),("Wat Ik doe",r(5,7)),("weet u nu niet",r(8,11)),("maar u zult het na deze verstaan",r(12,15))],
  8: [("Petrus zei tot Hem",r(0,2)),("U zult mijn voeten niet wassen in de eeuwigheid",r(3,11)),("Jezus antwoordde hem",r(12,15)),("Als Ik u niet wasse",r(16,19)),("u hebt geen deel met Mij",r(20,24))],
  9: [("Simon Petrus zei tot Hem",r(0,3)),("Heere",r(4)),("niet alleen mijn voeten",r(5,9)),("maar ook de handen en het hoofd",r(10,16))],
 10: [("Jezus zei tot hem",r(0,3)),("Die gewassen is",r(4,5)),("heeft niet nodig",r(6,8)),("dan de voeten te wassen",r(9,12)),("maar is geheel rein",r(13,16)),("En u bent rein",r(17,20)),("maar niet allen",r(21,23))],
 11: [("Want Hij wist",r(0,1)),("wie Hem verraden zou",r(2,4)),("daarom zei Hij",r(5,7)),("U bent niet allen rein",r(8,11))],
 12: [("Als Hij dan hun voeten gewassen",r(0,5)),("en Zijn kleren genomen had",r(6,10)),("zat Hij opnieuw aan",r(11,12)),("en zei tot hen",r(13,14)),("Verstaat u",r(15)),("wat Ik u gedaan heb",r(16,18))],
 13: [("U heet Mij Meester en Heere",r(0,7)),("en u zegt wel",r(8,10)),("want Ik ben het",r(11,12))],
 14: [("Als dan Ik",r(0,2)),("de Heere en de Meester",r(7,11)),("uw voeten gewassen heb",r(3,6)),("zo bent u ook schuldig",r(12,14)),("elkaars voeten te wassen",r(15,18))],
 15: [("Want Ik heb u een voorbeeld gegeven",r(0,3)),("opdat",r(4)),("zoals Ik u gedaan heb",r(5,8)),("u ook doet",r(9,11))],
 16: [("Voorwaar, voorwaar zeg Ik u",r(0,3)),("Een dienaar is niet meerder dan zijn heer",r(4,10)),("noch een gezant meerder",r(11,13)),("dan die hem gezonden heeft",r(14,16))],
 17: [("Als u deze dingen weet",r(0,2)),("zalig bent u",r(3,4)),("zo u dezelfde doet",r(5,7))],
 18: [("Ik zeg niet van u allen",r(0,4)),("Ik weet",r(5,6)),("welke Ik uitverkoren heb",r(7,8)),("maar dit gebeurt, opdat de Schrift vervuld wordt",r(9,13)),("Die met Mij het brood eet",r(14,19)),("heeft tegen Mij zijn hiel opgeheven",r(20,25))],
 19: [("Van nu zeg Ik het u",r(0,3)),("voordat het gebeurd is",r(4,6)),("opdat, wanneer het gebeurd zal zijn",r(7,9)),("u geloven mag",r(10)),("dat Ik het ben",r(11,13))],
 20: [("Voorwaar, voorwaar zeg Ik u",r(0,3)),("Zo Ik iemand zend",r(6,8)),("wie die ontvangt",r(4,5)),("die ontvangt Mij",r(9,10)),("en wie Mij ontvangt",r(11,14)),("die ontvangt Hem, Die Mij gezonden heeft",r(15,18))],
 21: [("Jezus, deze dingen gezegd hebbende",r(0,3)),("werd ontroerd in de geest",r(4,6)),("en betuigde",r(7,8)),("en zei",r(9,10)),("Voorwaar, voorwaar, Ik zeg u",r(11,14)),("dat één van u Mij zal verraden",r(15,20))],
 22: [("De discipelen dan zagen op elkaar",[0,1,2,3,4,5]),("twijfelende",r(6)),("van wie Hij dat zei",r(7,9))],
 23: [("En één van Zijn discipelen was aanzittende",r(0,6)),("in de schoot van Jezus",r(7,11)),("wie Jezus liefhad",r(12,15))],
 24: [("Simon Petrus dan wenkte deze",[0,1,2,3,4]),("dat hij vragen zou",r(5)),("wie hij toch was",r(6,8)),("van wie Hij dit zei",r(9,11))],
 25: [("En deze, vallende",r(0,2)),("op de borst van Jezus",r(3,7)),("zei tot Hem",r(8,9)),("Heere",r(10)),("wie is het",r(11,12))],
 26: [("Jezus antwoordde",r(0,2)),("Deze is het",r(3,4)),("die Ik het brood, als Ik ze ingedoopt heb, geven zal",r(5,10)),("En als Hij het brood ingedoopt had",r(11,14)),("gaf Hij ze Judas, Simons zoon, Iskariot",r(15,18))],
 27: [("En na het brood",r(0,3)),("toen voer de satan in hem",r(4,9)),("Jezus dan zei tot hem",[10,11,12,13,14]),("Wat u doet",r(15,16)),("doe het haastig",r(17,18))],
 28: [("En dit verstond niemand",r(0,3)),("van degenen, die aanzaten",r(4,5)),("waartoe Hij hem dat zei",r(6,9))],
 29: [("Want sommigen meenden",r(0,2)),("omdat Judas de beurs had",r(3,8)),("dat hem Jezus zei",r(9,13)),("Koop, wat wij nodig hebben tot het feest",r(14,20)),("of, dat hij de armen wat geven zou",r(21,26))],
 30: [("Hij dan, het brood genomen hebbende",r(0,4)),("ging meteen uit",r(5,6)),("En het was nacht",r(7,9))],
 31: [("Als hij dan uitgegaan was",r(0,2)),("zei Jezus",r(3,5)),("Nu is de Zoon des mensen verheerlijkt",r(6,11)),("en God is in Hem verheerlijkt",r(12,17))],
 32: [("Als God in Hem verheerlijkt is",r(0,5)),("zo zal ook God Hem verheerlijken in Zichzelf",r(6,12)),("en Hij zal Hem meteen verheerlijken",r(13,16))],
 33: [("Kinderen",r(0)),("nog een kleine tijd ben Ik bij u",r(1,5)),("U zult Mij zoeken",r(6,7)),("en zoals Ik de Joden gezegd heb",r(8,12)),("Waar Ik heenga",r(13,16)),("kunt u niet komen",r(17,20)),("zo zeg Ik u nu ook",r(21,24))],
 34: [("Een nieuw gebod geef Ik u",r(0,3)),("dat u elkaar liefhebt",r(4,6)),("zoals Ik u liefgehad heb",r(7,9)),("dat ook u elkaar liefhebt",r(10,14))],
 35: [("Hieraan zullen zij allen bekennen",r(0,3)),("dat u Mijn discipelen bent",r(4,7)),("zo u liefde hebt onder elkaar",r(8,12))],
 36: [("Simon Petrus zei tot Hem",r(0,3)),("Heere",r(4)),("waar gaat U heen",r(5,6)),("Jezus antwoordde hem",r(7,10)),("Waar Ik heenga",r(11,12)),("kunt u Mij nu niet volgen",r(13,17)),("maar u zult Mij later volgen",r(18,21))],
 37: [("Petrus zei tot Hem",r(0,3)),("Heere",r(4)),("waarom kan ik U nu niet volgen",r(5,11)),("Ik zal mijn leven voor U zetten",r(12,17))],
 38: [("Jezus antwoordde hem",r(0,3)),("Zult u uw leven voor Mij zetten",r(4,9)),("Voorwaar, voorwaar zeg Ik u",r(10,13)),("De haan zal niet kraaien",r(14,17)),("voordat u Mij drie keer verloochend zult hebben",r(18,22))],
}

def build(utr_path:Path,osis_path:Path,write=False):
 source=load_tr_chapter(utr_path,osis_path,chapter=13,osis_book="John"); p=ROOT/"data"/"johannes"/"13.json"; ch=json.loads(p.read_text(encoding="utf-8")); rp=ROOT/"data"/"woordnummers-review"/"johannes-13.json"; review={"book":"johannes","chapter":13,"reviewed_through":38,"verses":{}}
 for verse in ch["verses"][:38]:
  n=int(verse["number"]); tokens=source[n]; groups=SPECS[n]; covered=[i for _,ids in groups for i in ids]
  if sorted(covered)!=list(range(len(tokens))) or len(set(covered))!=len(tokens): raise ValueError(f"Johannes 13:{n}: onvolledige of dubbele handmatige review")
  verse["grondtekst"]=[{"woord":t["woord"],"strongs":t["display_strong"],"lemma_strongs":t["lemma_strong"],"morfologie":t["morphology"],**({"tvm":t["tvm"]} if t.get("tvm") else {}),**({"bronstatus":t["bronstatus"]} if t.get("bronstatus") else {})} for t in tokens]
  verse["woordnummers"]=[mapping(a,ids,tokens,n) for a,ids in groups]; occ={}
  for item in verse["woordnummers"]: occ[item["tekst"]]=occ.get(item["tekst"],0)+1; item["voorkomen"]=occ[item["tekst"]]; item["herkomst"]["referentie"]=f"JHN 13:{n}"
  review["verses"][str(n)]=[{"tekst":a,"bronindices":ids,"reviewstatus":"handmatig_gecontroleerd"} for a,ids in groups]
 if write:
  p.write_text(json.dumps(ch,ensure_ascii=False,indent=2)+"\n",encoding="utf-8"); rp.write_text(json.dumps(review,ensure_ascii=False,indent=2)+"\n",encoding="utf-8"); ip=ROOT/"data"/"woordnummers-inline"/"johannes.json"; inline=json.loads(ip.read_text(encoding="utf-8")); inline["chapters"]["13"]={str(v["number"]):v["woordnummers"] for v in ch["verses"][:38]}; ip.write_text(json.dumps(inline,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 return {"verses":38,"tokens":sum(len(source[n]) for n in range(1,39))}

def main():
 p=argparse.ArgumentParser();p.add_argument("--utr",type=Path,required=True);p.add_argument("--osis",type=Path,required=True);p.add_argument("--write",action="store_true");a=p.parse_args();print(json.dumps(build(a.utr,a.osis,a.write),indent=2))
if __name__=="__main__": main()
