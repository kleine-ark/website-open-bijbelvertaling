#!/usr/bin/env python3
"""Publiceer gecontroleerde TR-koppelingen voor Johannes 9 in versbatches."""

from __future__ import annotations
import argparse, json
from pathlib import Path
from rebuild_nt_tr_strongs import load_tr_chapter
from rebuild_johannes2_tr_strongs import mapping, r

ROOT = Path(__file__).resolve().parents[1]
SPECS = {
    1: [("En voorbijgaande", r(0, 1)), ("zag Hij een mens", r(2, 3)),
        ("blind van de geboorte af", r(4, 6))],
    2: [("En Zijn discipelen vraagden Hem", r(0, 5)), ("zeggende", r(6)),
        ("Rabbi", r(7)), ("wie heeft er gezondigd", r(8, 9)), ("deze", r(10)),
        ("of zijn ouders", r(11, 14)), ("dat hij blind zou geboren worden", r(15, 17))],
    3: [("Jezus antwoordde", r(0, 2)), ("Noch deze heeft gezondigd", r(3, 5)),
        ("noch zijn ouders", r(6, 9)), ("maar dit is gebeurd", r(10)),
        ("opdat de werken van God", [11, 13, 14, 15, 16]),
        ("in hem zouden geopenbaard worden", [17, 18, 12])],
    4: [("Ik moet werken", r(0, 2)), ("de werken Van Degene, Die Mij gezonden heeft", r(3, 7)),
        ("zolang het dag is", r(8, 10)), ("de nacht komt", r(11, 12)),
        ("wanneer niemand werken kan", r(13, 16))],
    5: [("Zolang Ik in de wereld ben", r(0, 4)), ("zo ben Ik het Licht van de wereld", r(5, 8))],
    6: [("Dit gezegd hebbende", r(0, 1)), ("spoog Hij op de aarde", r(2, 3)),
        ("en maakte slijk uit dat speeksel", r(4, 9)),
        ("en streek dat slijk op de ogen van de blinde", r(10, 18))],
    7: [("En zei tot hem", r(0, 2)), ("Ga heen", r(3)),
        ("was u in het badwater Siloam", r(4, 9)),
        ("dat overgezet wordt: uitgezonden", r(10, 12)),
        ("Hij dan ging heen en waste zich", r(13, 16)), ("en kwam ziende", r(17, 19))],
    8: [("De geburen dan", r(0, 2)), ("en die hem te voren gezien hadden", r(3, 8)),
        ("dat hij blind was", r(9, 11)), ("zeiden", r(12)),
        ("Is deze niet", r(13, 15)), ("die zat en bedelde", r(16, 19))],
    9: [("Anderen zeiden", r(0, 1)), ("Hij is het", r(2, 4)),
        ("en anderen", r(5, 7)), ("Hij is hem gelijk", r(8, 10)),
        ("Hij zei", r(11, 12)), ("Ik ben het", r(13, 15))],
    10: [("Zij dan zeiden tot hem", r(0, 2)), ("Hoe zijn u de ogen geopend", r(3, 7))],
    11: [("Hij antwoordde en zei", r(0, 3)), ("De Mens, genoemd Jezus", r(4, 6)),
         ("maakte slijk", r(7, 8)), ("en bestreek mijn ogen", r(9, 13)),
         ("en zei tot mij", r(14, 16)), ("Ga heen naar het badwater Siloam", r(17, 22)),
         ("en was u", r(23, 24)), ("En ik ging heen", r(25, 27)),
         ("en waste mij", r(28)), ("en ik werd ziende", r(29))],
    12: [("Zij dan zeiden tot hem", r(0, 2)), ("Waar is Die", r(3, 5)),
         ("Hij zei", r(6)), ("Ik weet het niet", r(7, 8))],
    13: [("Zij brachten hem tot de Farizeeën", r(0, 4)),
         ("hem namelijk, die te voren blind geweest was", r(5, 7))],
    14: [("En het was sabbat", r(0, 2)), ("als Jezus het slijk maakte", r(3, 8)),
         ("en zijn ogen opende", r(9, 13))],
    15: [("De Farizeeën dan vraagden hem ook opnieuw", r(0, 6)),
         ("hoe hij ziende geworden was", r(7, 8)), ("En hij zei tot hen", r(9, 12)),
         ("Hij legde slijk op mijn ogen", r(13, 18)), ("en ik waste mij", r(19, 20)),
         ("en ik zie", r(21, 22))],
    16: [("Sommigen dan uit de Farizeeën zeiden", [0, 1, 2, 3, 4, 5]),
         ("Deze Mens is van God niet", r(6, 13)),
         ("want Hij houdt de sabbat niet", r(14, 18)), ("Anderen zeiden", r(19, 20)),
         ("Hoe kan een mens, die een zondaar is", r(21, 24)),
         ("zulke tekenen doen", r(25, 27)), ("En er was tweedracht onder hen", r(28, 32))],
    17: [("Zij zeiden opnieuw tot de blinde", r(0, 3)), ("U, wat zegt u van Hem", r(4, 8)),
         ("omdat Hij uw ogen geopend heeft", r(9, 13)), ("En hij zei", r(14, 16)),
         ("Hij is een Profeet", r(17, 19))],
    18: [("De Joden dan geloofden van hem niet", r(0, 6)),
         ("dat hij blind geweest was", r(7, 9)), ("en ziende was geworden", r(10, 11)),
         ("voordat zij geroepen hadden", r(12, 14)), ("de ouders", r(15, 16)),
         ("van degene, die ziende geworden was", r(17, 19))],
    19: [("En zij vraagden hun", r(0, 2)), ("zeggende", r(3)),
         ("Is deze uw zoon", r(4, 8)), ("wie u zegt", r(9, 11)),
         ("dat blind geboren is", r(12, 14)), ("Hoe ziet hij dan nu", r(15, 18))],
    20: [("Zijn ouders antwoordden hun en zeiden", r(0, 6)),
         ("Wij weten", r(7)), ("dat deze onze zoon is", r(8, 13)),
         ("en dat hij blind geboren is", r(14, 17))],
    21: [("Maar hoe hij nu ziet", r(0, 3)), ("weten wij niet", r(4, 5)),
         ("of wie zijn ogen geopend heeft", r(6, 11)), ("weten wij niet", r(12, 14)),
         ("hij heeft zijn ouderdom", r(15, 17)), ("vraagt hemzelf", r(18, 19)),
         ("hij zal van zichzelf spreken", r(20, 23))],
    22: [("Dit zeiden zijn ouders", r(0, 4)), ("omdat zij de Joden vreesden", r(5, 8)),
         ("want de Joden hadden al samen een besluit gemaakt", r(9, 13)),
         ("zo iemand Hem beleed Christus te zijn", r(14, 19)),
         ("dat die uit de synagoge zou geworpen worden", r(20, 21))],
    23: [("Daarom zeiden zijn ouders", r(0, 5)),
         ("Hij heeft zijn ouderdom", r(6, 8)), ("vraagt hemzelf", r(9, 10))],
    24: [("Zij dan riepen voor de tweede maal", r(0, 3)),
         ("de mens, die blind geweest was", r(4, 8)), ("en zeiden tot hem", r(9, 11)),
         ("Geef God de eer", r(12, 15)), ("wij weten", r(16, 17)),
         ("dat deze Mens een zondaar is", r(18, 23))],
    25: [("Hij dan antwoordde en zei", r(0, 4)),
         ("Of Hij een zondaar is", r(5, 7)), ("weet ik niet", r(8, 9)),
         ("één ding weet ik", r(10, 11)), ("dat ik blind was", r(12, 14)),
         ("en nu zie", r(15, 16))],
    26: [("En zij zeiden opnieuw tot hem", r(0, 3)), ("Wat heeft Hij u gedaan", r(4, 6)),
         ("Hoe heeft Hij uw ogen geopend", r(7, 11))],
    27: [("Hij antwoordde hun", r(0, 1)), ("Ik heb het u al gezegd", r(2, 4)),
         ("en u hebt het niet gehoord", r(5, 7)),
         ("wat wilt u het opnieuw horen", r(8, 11)),
         ("Wilt u ook Zijn discipelen worden", r(12, 18))],
    28: [("Zij gaven hem dan scheldwoorden", r(0, 2)), ("en zeiden", r(3, 4)),
         ("U bent Zijn discipel", r(5, 8)),
         ("maar wij zijn discipelen van Mozes", r(9, 14))],
    29: [("Wij weten", r(0, 1)), ("dat God tot Mozes gesproken heeft", r(2, 6)),
         ("maar Deze weten wij niet", r(7, 10)), ("vanwaar Hij is", r(11, 12))],
    30: [("De mens antwoordde, en zei tot hen", r(0, 5)),
         ("Hierin is immers wat wonders", r(6, 10)),
         ("dat u niet weet, vanwaar Hij is", r(11, 16)),
         ("en toch heeft Hij mijn ogen geopend", r(17, 21))],
    31: [("En wij weten", r(0, 1)), ("dat God de zondaars niet hoort", r(2, 7)),
         ("maar zo iemand godvruchtig is", r(8, 12)), ("en Zijn wil doet", r(13, 17)),
         ("die hoort Hij", r(18, 19))],
    32: [("Van alle eeuw is het niet gehoord", r(0, 4)),
         ("dat iemand de ogen van een blindgeborene geopend heeft", r(5, 10))],
    33: [("Als Deze van God niet was", r(0, 5)), ("Hij zou niets kunnen doen", r(6, 9))],
    34: [("Zij antwoordden, en zeiden tot hem", r(0, 3)),
         ("U bent geheel in zonden geboren", r(4, 8)), ("en leert u ons", r(9, 12)),
         ("En zij wierpen hem uit", r(13, 16))],
    35: [("Jezus hoorde", r(0, 2)), ("dat zij hem uitgeworpen hadden", r(3, 6)),
         ("en hem vindende", r(7, 9)), ("zei Hij tot hem", r(10, 11)),
         ("Gelooft u in de Zoon van God", r(12, 18))],
    36: [("Hij antwoordde en zei", r(0, 3)), ("Wie is Hij, Heere", r(4, 6)),
         ("opdat ik in Hem mag geloven", r(7, 10))],
    37: [("En Jezus zei tot Hem", r(0, 4)), ("En u hebt Hem gezien", r(5, 7)),
         ("en Die met u spreekt", r(8, 12)), ("Deze is het", r(13, 14))],
    38: [("En hij zei", r(0, 2)), ("Ik geloof, Heere", r(3, 4)),
         ("En hij aanbad Hem", r(5, 7))],
    39: [("En Jezus zei", r(0, 3)), ("Ik ben tot een oordeel", [4, 5, 6]),
         ("in deze wereld gekomen", r(7, 11)),
         ("opdat degenen, die niet zien, zien mogen", r(12, 16)),
         ("en die zien, blind worden", r(17, 21))],
    40: [("En dit hoorden enige uit de Farizeeën", r(0, 5)),
         ("die bij Hem waren", r(6, 9)), ("en zeiden tot Hem", r(10, 12)),
         ("Zijn wij dan ook blind", r(13, 17))],
    41: [("Jezus zei tot hen", r(0, 3)), ("Als u blind was", r(4, 6)),
         ("zo zou u geen zonde hebben", r(7, 10)), ("maar nu zegt u", r(11, 14)),
         ("Wij zien", r(15)), ("zo blijft dan uw zonde", r(16, 20))],
}

def build(utr_path: Path, osis_path: Path, write=False):
    source = load_tr_chapter(utr_path, osis_path, chapter=9, osis_book="John")
    chapter_path = ROOT / "data" / "johannes" / "9.json"
    chapter = json.loads(chapter_path.read_text(encoding="utf-8"))
    review = {"book": "johannes", "chapter": 9, "reviewed_through": 41, "verses": {}}
    for verse in chapter["verses"][:41]:
        number = int(verse["number"]); tokens = source[number]; groups = SPECS[number]
        covered = [index for _, ids in groups for index in ids]
        if sorted(covered) != list(range(len(tokens))) or len(set(covered)) != len(tokens):
            raise ValueError(f"Johannes 9:{number}: onvolledige of dubbele handmatige review")
        verse["grondtekst"] = [{"woord": t["woord"], "strongs": t["display_strong"],
            "lemma_strongs": t["lemma_strong"], "morfologie": t["morphology"],
            **({"tvm": t["tvm"]} if t.get("tvm") else {}),
            **({"bronstatus": t["bronstatus"]} if t.get("bronstatus") else {})} for t in tokens]
        verse["woordnummers"] = [mapping(anchor, ids, tokens, number) for anchor, ids in groups]
        occurrences = {}
        for item in verse["woordnummers"]:
            occurrences[item["tekst"]] = occurrences.get(item["tekst"], 0) + 1
            item["voorkomen"] = occurrences[item["tekst"]]
        for item in verse["woordnummers"]: item["herkomst"]["referentie"] = f"JHN 9:{number}"
        review["verses"][str(number)] = [{"tekst": a, "bronindices": ids,
            "reviewstatus": "handmatig_gecontroleerd"} for a, ids in groups]
    if write:
        chapter_path.write_text(json.dumps(chapter, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        review_dir = ROOT / "data" / "woordnummers-review"; review_dir.mkdir(exist_ok=True)
        (review_dir / "johannes-9.json").write_text(json.dumps(review, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        inline_path = ROOT / "data" / "woordnummers-inline" / "johannes.json"
        inline = json.loads(inline_path.read_text(encoding="utf-8")); inline["chapters"]["9"] = {
            str(v["number"]): v["woordnummers"] for v in chapter["verses"][:41]}
        inline_path.write_text(json.dumps(inline, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"verses": 41, "tokens": sum(len(source[n]) for n in range(1, 42))}

def main():
    p=argparse.ArgumentParser(); p.add_argument("--utr",type=Path,required=True); p.add_argument("--osis",type=Path,required=True); p.add_argument("--write",action="store_true")
    a=p.parse_args(); print(json.dumps(build(a.utr,a.osis,a.write),indent=2))
if __name__ == "__main__": main()
