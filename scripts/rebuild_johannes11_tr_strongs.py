#!/usr/bin/env python3
"""Publiceer gecontroleerde TR-koppelingen voor Johannes 11 in versbatches."""

from __future__ import annotations
import argparse, json
from pathlib import Path
from rebuild_nt_tr_strongs import load_tr_chapter
from rebuild_johannes2_tr_strongs import mapping, r

ROOT = Path(__file__).resolve().parents[1]
SPECS = {
    1: [("En er was een zeker man ziek", r(0, 3)), ("genoemd Lazarus", r(4)),
        ("van Bethanië", r(5, 6)), ("uit het dorp van Maria", r(7, 10)),
        ("en haar zus Martha", r(11, 15))],
    2: [("Maria nu was degene", r(0, 3)), ("die de Heere gezalfd heeft met zalf", r(4, 7)),
        ("en Zijn voeten afgedroogd heeft met haar haar", r(8, 15)),
        ("wier broer Lazarus ziek was", r(16, 20))],
    3: [("Zijn zussen dan zonden tot Hem", r(0, 5)), ("zeggende", r(6)),
        ("Heere", r(7)), ("zie", r(8)), ("die U liefhebt", r(9, 10)), ("is ziek", r(11))],
    4: [("En Jezus, dat horende, zei", r(0, 4)),
        ("Deze ziekte is niet tot de dood", r(5, 11)),
        ("maar tot heerlijkheid van God", r(12, 17)),
        ("opdat de Zoon van God door deze verheerlijkt wordt", r(18, 25))],
    5: [("Jezus nu had Martha", r(0, 5)), ("en haar zus", r(6, 9)),
        ("en Lazarus lief", r(10, 12))],
    6: [("Als Hij dan gehoord had", r(0, 2)), ("dat hij ziek was", r(3, 4)),
        ("toen bleef Hij", r(5, 7)), ("nog twee dagen", r(12, 13)),
        ("in de plaats, waar Hij was", r(8, 11))],
    7: [("Daarna", r(0, 2)), ("zei Hij verder tot de discipelen", r(3, 5)),
        ("Laat ons opnieuw naar Judea gaan", r(6, 10))],
    8: [("De discipelen zeiden tot Hem", r(0, 3)), ("Rabbi", r(4)),
        ("de Joden hebben U nu onlangs gezocht te stenigen", r(5, 10)),
        ("en gaat U opnieuw daarheen", r(11, 14))],
    9: [("Jezus antwoordde", r(0, 2)), ("Zijn er niet twaalf uren in de dag", r(3, 8)),
        ("Als iemand in de dag wandelt", r(9, 14)), ("zo stoot hij zich niet", r(15, 16)),
        ("omdat hij het licht van deze wereld ziet", r(17, 23))],
    10: [("Maar als iemand in de nacht wandelt", r(0, 6)),
         ("zo stoot hij zich", r(7)), ("omdat het licht in hem niet is", r(8, 14))],
    11: [("Dit sprak Hij", r(0, 1)), ("en daarna zei Hij tot hen", r(2, 6)),
         ("Lazarus, onze vriend", r(7, 10)), ("slaapt", r(11)),
         ("maar Ik ga heen", r(12, 13)), ("om hem uit de slaap op te wekken", r(14, 16))],
    12: [("Zijn discipelen dan zeiden", r(0, 4)), ("Heere", r(5)),
         ("als hij slaapt", r(6, 7)), ("zo zal hij gezond worden", r(8))],
    13: [("Maar Jezus had gesproken van zijn dood", r(0, 7)),
         ("maar zij meenden", r(8, 10)),
         ("dat Hij sprak van de rust van de slaap", r(11, 17))],
    14: [("Toen zei dan Jezus tot hen vrijuit", r(0, 6)), ("Lazarus is gestorven", r(7, 8))],
    15: [("En Ik ben blij om uwentwil", r(0, 3)),
         ("dat Ik daar niet geweest ben", r(6, 9)), ("opdat u geloven mag", r(4, 5)),
         ("maar laat ons tot hem gaan", r(10, 13))],
    16: [("Thomas dan, genoemd Didymus", r(0, 5)),
         ("zei tot zijn medediscipelen", r(6, 7)), ("Laat ons ook gaan", r(8, 10)),
         ("opdat wij met Hem sterven", r(11, 14))],
    17: [("Jezus dan, gekomen zijnde", r(0, 3)), ("vond", r(4)),
         ("dat hij nu vier dagen", r(5, 9)), ("in het graf geweest was", r(10, 12))],
    18: [("Bethanië nu was nabij Jeruzalem", r(0, 6)),
         ("ongeveer vijftien stadiën van daar", r(7, 10))],
    19: [("En velen uit de Joden waren gekomen", r(0, 5)),
         ("tot Martha en Maria", r(6, 11)),
         ("opdat zij haar troosten zouden", r(12, 14)), ("over haar broer", r(15, 18))],
    20: [("Martha dan, als zij hoorde", r(0, 4)), ("dat Jezus kwam", r(5, 8)),
         ("ging Hem tegemoet", r(9, 10)), ("maar Maria bleef in huis zitten", r(11, 16))],
    21: [("Zo zei Martha dan tot Jezus", r(0, 6)), ("Heere", r(7)),
         ("was U hier geweest", r(8, 10)), ("zo was mijn broer niet gestorven", r(11, 16))],
    22: [("Maar ook nu weet ik", r(0, 3)), ("dat alles", r(4, 5)),
         ("wat U van God begeren zult", r(6, 9)), ("God U het geven zal", r(10, 13))],
    23: [("Jezus zei tot haar", r(0, 3)), ("Uw broer zal wederopstaan", r(4, 7))],
    24: [("Martha zei tot Hem", r(0, 2)), ("Ik weet", r(3)),
         ("dat hij opstaan zal", r(4, 5)), ("in de opstanding", r(6, 8)),
         ("op de laatste dag", r(9, 12))],
    25: [("Jezus zei tot haar", r(0, 3)), ("Ik ben de Opstanding en het Leven", r(4, 10)),
         ("die in Mij gelooft", r(11, 14)), ("zal leven", r(17)),
         ("al was hij ook gestorven", r(15, 16))],
    26: [("En een ieder, die leeft", r(0, 3)), ("en in Mij gelooft", r(4, 7)),
         ("zal niet sterven in de eeuwigheid", r(8, 13)), ("Gelooft u dat", r(14, 15))],
    27: [("Zij zei tot Hem", r(0, 1)), ("Ja, Heere", r(2, 3)),
         ("ik heb geloofd", r(4, 5)), ("dat U bent de Christus", r(6, 10)),
         ("de Zoon van God", r(11, 14)), ("Die in de wereld komen zou", r(15, 19))],
    28: [("En dit gezegd hebbende", r(0, 2)), ("ging zij heen", r(3)),
         ("en riep Maria, haar zus", r(4, 9)), ("in het geheim", r(10)),
         ("zeggende", r(11)), ("De Meester is daar", r(12, 14)),
         ("en Hij roept u", r(15, 17))],
    29: [("Deze, als zij dat hoorde", r(0, 2)), ("stond haastig op", r(3, 4)),
         ("en ging tot Hem", r(5, 8))],
    30: [("Jezus nu was nog in het plaats niet gekomen", r(0, 7)),
         ("maar was in de plaats", r(8, 12)),
         ("waar Hem Martha tegemoet gekomen was", r(13, 17))],
    31: [("De Joden dan, die met haar in het huis waren", r(0, 9)),
         ("en haar troostten", r(10, 12)), ("ziende Maria", r(13, 15)),
         ("dat zij haastig opstond en uitging", r(16, 20)), ("volgden haar", r(21, 22)),
         ("zeggende", r(23)), ("Zij gaat naar het graf", r(24, 28)),
         ("opdat zij daar wene", r(29, 31))],
    32: [("Maria dan, als zij kwam", r(0, 4)), ("waar Jezus was", r(5, 8)),
         ("en Hem zag", r(9, 10)), ("viel aan Zijn voeten", r(11, 15)),
         ("zeggende tot Hem", r(16, 17)), ("Heere", r(18)),
         ("als U hier geweest was", r(19, 21)),
         ("zo was mijn broer niet gestorven", r(22, 27))],
    33: [("Jezus dan, als Hij haar zag huilen", r(0, 5)),
         ("en de Joden, die met haar kwamen, ook huilen", r(6, 11)),
         ("werd zeer bewogen in de geest", r(12, 14)),
         ("en ontroerde Zichzelf", r(15, 17))],
    34: [("En zei", r(0, 1)), ("Waar hebt u hem gelegd", r(2, 4)),
         ("Zij zeiden tot Hem", r(5, 6)), ("Heere", r(7)),
         ("kom en zie het", r(8, 10))],
    35: [("Jezus huilde", r(0, 2))],
    36: [("De Joden dan zeiden", r(0, 3)), ("Zie, hoe lief Hij hem had", r(4, 7))],
    37: [("En sommigen uit hen zeiden", r(0, 4)), ("Kon Hij", r(5, 7)),
         ("Die de ogen van de blinde geopend heeft", r(8, 13)),
         ("niet maken", r(14, 15)), ("dat ook deze niet gestorven was", r(16, 19))],
    38: [("Jezus dan opnieuw in Zichzelf zeer bewogen zijnde", r(0, 5)),
         ("kwam tot het graf", r(6, 9)), ("en het was een grot", r(10, 12)),
         ("en een steen was daarop gelegd", r(13, 17))],
    39: [("Jezus zei", r(0, 2)), ("Neem de steen weg", r(3, 5)),
         ("Martha, de zus van de gestorvene, zei tot Hem", r(6, 12)),
         ("Heere", r(13)), ("hij ruikt nu al", r(14, 15)),
         ("want hij heeft vier dagen daar gelegen", r(16, 18))],
    40: [("Jezus zei tot haar", r(0, 3)), ("Heb Ik u niet gezegd", r(4, 6)),
         ("dat, zo u gelooft", r(7, 9)), ("u de heerlijkheid van God zien zult", r(10, 14))],
    41: [("Zij namen dan de steen weg",r(0,3)),("waar de gestorvene lag",r(4,8)),("En Jezus hief de ogen omhoog",r(9,15)),("en zei",r(16,17)),("Vader",r(18)),("Ik dank U",r(19,20)),("dat U Mij gehoord hebt",r(21,23))],
    42: [("Maar Ik wist",r(0,2)),("dat U Mij altijd hoort",r(3,6)),("maar omwille van de menigte, die rondom staat",r(7,12)),("heb Ik dit gezegd",r(13)),("opdat zij zouden geloven",r(14,15)),("dat U Mij gezonden hebt",r(16,19))],
    43: [("En als Hij dit gezegd had",r(0,2)),("riep Hij met luide stem",r(3,5)),("Lazarus",r(6)),("kom uit",r(7,8))],
    44: [("En de gestorvene kwam uit",r(0,3)),("gebonden aan handen en voeten met grafdoeken",r(4,10)),("en zijn aangezicht was omwonden met een zweetdoek",r(11,16)),("Jezus zei tot hen",r(17,20)),("Ontbind hem",r(21,22)),("en laat hem heengaan",r(23,25))],
    45: [("Velen dan uit de Joden",r(0,4)),("die tot Maria gekomen waren",r(5,9)),("en aanschouwd hadden",r(10,11)),("wat Jezus gedaan had",r(12,15)),("geloofden in Hem",r(16,18))],
    46: [("Maar sommigen van hen gingen tot de Farizeeën",r(0,7)),("en zeiden tot hen",r(8,10)),("wat Jezus gedaan had",r(11,14))],
    47: [("De overpriesters dan en de Farizeeën verzamelden de raad",r(0,7)),("en zeiden",r(8,9)),("Wat zullen wij doen",r(10,11)),("want deze Mens doet vele tekenen",r(12,18))],
    48: [("Als wij Hem zo laten geworden",r(0,3)),("zij zullen allen in Hem geloven",r(4,7)),("en de Romeinen zullen komen",r(8,11)),("en wegnemen zowel onze plaats als volk",r(12,20))],
    49: [("En één uit hen",r(0,4)),("namelijk Kajafas",r(5)),("die dat jaar hogepriester was",r(6,10)),("zei tot hen",r(11,12)),("U verstaat niets",r(13,16))],
    50: [("En u overlegt niet",r(0,1)),("dat het ons nut is",r(2,4)),("dat een mens sterft voor het volk",r(5,11)),("en het hele volk niet verloren ga",r(12,17))],
    51: [("En dit zei hij niet uit zichzelf",r(0,5)),("maar, zijnde hogepriester in dat jaar",r(6,11)),("profeteerde hij",r(12)),("dat Jezus sterven zou voor het volk",r(13,20))],
    52: [("En niet alleen voor dat volk",r(0,5)),("maar opdat Hij ook de kinderen van God, die verstrooid waren",r(6,14)),("tot één zou verzamelen",r(15,17))],
    53: [("Van die dag dan af",r(0,4)),("beraadslaagden zij samen",r(5)),("dat zij Hem doden zouden",r(6,8))],
    54: [("Jezus dan wandelde niet meer vrij onder de Joden",r(0,8)),("maar ging van daar",r(9,11)),("naar het land bij de woestijn",r(12,17)),("naar de stad, genoemd Efraïm",r(18,21)),("en verkeerde daar met Zijn discipelen",r(22,27))],
    55: [("En het pascha van de Joden was nabij",r(0,6)),("en velen uit dat land gingen op naar Jeruzalem",r(7,14)),("voor het pascha",r(15,17)),("opdat zij zichzelf reinigden",r(18,20))],
    56: [("Zij zochten dan Jezus",r(0,3)),("en zeiden onder elkaar",r(4,7)),("staande in de tempel",r(8,11)),("Wat denkt u",r(12,14)),("Denkt u, dat Hij niet komen zal tot het feest",r(15,21))],
    57: [("De overpriesters nu en de Farizeeën hadden een gebod gegeven",r(0,8)),("dat, zo iemand wist",r(9,12)),("waar Hij was",r(13,14)),("hij het zou te kennen geven",r(15)),("opdat zij Hem mochten vangen",r(16,18))],
}

def build(utr_path: Path, osis_path: Path, write=False):
    source = load_tr_chapter(utr_path, osis_path, chapter=11, osis_book="John")
    chapter_path = ROOT / "data" / "johannes" / "11.json"
    chapter = json.loads(chapter_path.read_text(encoding="utf-8"))
    review = {"book": "johannes", "chapter": 11, "reviewed_through": 57, "verses": {}}
    for verse in chapter["verses"][:57]:
        number = int(verse["number"]); tokens = source[number]; groups = SPECS[number]
        covered = [index for _, ids in groups for index in ids]
        if sorted(covered) != list(range(len(tokens))) or len(set(covered)) != len(tokens):
            raise ValueError(f"Johannes 11:{number}: onvolledige of dubbele handmatige review")
        verse["grondtekst"] = [{"woord": t["woord"], "strongs": t["display_strong"],
            "lemma_strongs": t["lemma_strong"], "morfologie": t["morphology"],
            **({"tvm": t["tvm"]} if t.get("tvm") else {}),
            **({"bronstatus": t["bronstatus"]} if t.get("bronstatus") else {})} for t in tokens]
        verse["woordnummers"] = [mapping(anchor, ids, tokens, number) for anchor, ids in groups]
        occurrences = {}
        for item in verse["woordnummers"]:
            occurrences[item["tekst"]] = occurrences.get(item["tekst"], 0) + 1
            item["voorkomen"] = occurrences[item["tekst"]]
            item["herkomst"]["referentie"] = f"JHN 11:{number}"
        review["verses"][str(number)] = [{"tekst": a, "bronindices": ids,
            "reviewstatus": "handmatig_gecontroleerd"} for a, ids in groups]
    if write:
        chapter_path.write_text(json.dumps(chapter, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        review_dir = ROOT / "data" / "woordnummers-review"; review_dir.mkdir(exist_ok=True)
        (review_dir / "johannes-11.json").write_text(json.dumps(review, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        inline_path = ROOT / "data" / "woordnummers-inline" / "johannes.json"
        inline = json.loads(inline_path.read_text(encoding="utf-8")); inline["chapters"]["11"] = {
            str(v["number"]): v["woordnummers"] for v in chapter["verses"][:57]}
        inline_path.write_text(json.dumps(inline, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"verses": 57, "tokens": sum(len(source[n]) for n in range(1, 58))}

def main():
    p=argparse.ArgumentParser(); p.add_argument("--utr",type=Path,required=True); p.add_argument("--osis",type=Path,required=True); p.add_argument("--write",action="store_true")
    a=p.parse_args(); print(json.dumps(build(a.utr,a.osis,a.write),indent=2))
if __name__ == "__main__": main()
