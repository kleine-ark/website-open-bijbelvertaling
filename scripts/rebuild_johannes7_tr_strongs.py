#!/usr/bin/env python3
"""Publiceer gecontroleerde TR-koppelingen voor Johannes 7 in versbatches."""

from __future__ import annotations
import argparse, json
from pathlib import Path
from rebuild_nt_tr_strongs import load_tr_chapter
from rebuild_johannes2_tr_strongs import mapping, r

ROOT = Path(__file__).resolve().parents[1]
SPECS = {
    1: [("En na deze wandelde Jezus", [0, 4, 5, 1, 2, 3]), ("in Galilea", r(6, 8)),
        ("want Hij wilde", r(9, 11)), ("in Judea niet wandelen", r(12, 15)),
        ("omdat de Joden Hem zochten te doden", r(16, 21))],
    2: [("En het feest van de Joden", [1, 3, 4, 5, 6]),
        ("namelijk de loofhuttenzetting", r(7, 8)), ("was nabij", [0, 2])],
    3: [("Zo zeiden dan Zijn broers tot Hem", r(0, 6)), ("Vertrek van hier", r(7, 8)),
        ("en ga heen in Judea", r(9, 13)), ("opdat ook Uw discipelen", r(14, 18)),
        ("Uw werken mogen aanschouwen", r(19, 22)), ("die U doet", r(23, 24))],
    4: [("Want niemand doet iets in het verborgen", r(0, 5)),
        ("en zoekt zelf", r(6, 8)), ("dat men openlijk van hem spreke", r(9, 11)),
        ("Als U deze dingen doet", r(12, 14)), ("zo openbaar Uzelf aan de wereld", r(15, 18))],
    5: [("Want ook Zijn broers", r(0, 4)), ("geloofden niet in Hem", r(5, 7))],
    6: [("Jezus dan zei tot hen", r(0, 4)), ("Mijn tijd is nog niet hier", r(5, 10)),
        ("maar uw tijd", r(11, 15)), ("is altijd bereid", r(16, 18))],
    7: [("De wereld kan u niet haten", r(0, 5)), ("maar Mij haat zij", r(6, 8)),
        ("omdat Ik van deze getuig", r(9, 13)), ("dat haar werken boos zijn", r(14, 19))],
    8: [("Ga u op tot dit feest", r(0, 5)), ("Ik ga nog niet op tot dit feest", r(6, 12)),
        ("want Mijn tijd is nog niet vervuld", r(13, 19))],
    9: [("En als Hij deze dingen tot hen gezegd had", r(0, 3)),
        ("bleef Hij in Galilea", r(4, 7))],
    10: [("Maar als Zijn broers opgegaan waren", r(0, 5)),
         ("toen ging Hij ook Zelf op tot het feest", r(6, 12)),
         ("niet openlijk", r(13, 14)), ("maar als in het verborgen", r(15, 18))],
    11: [("De Joden dan zochten Hem", r(0, 4)), ("in het feest", r(5, 7)),
         ("en zeiden", r(8, 9)), ("Waar is Hij", r(10, 12))],
    12: [("En er was veel gemurmels van Hem", r(0, 5)), ("onder de menigten", r(6, 8)),
         ("Sommigen zeiden", r(9, 11)), ("Hij is goed", r(12, 14)),
         ("en anderen zeiden", r(15, 17)), ("Nee, maar", r(18, 19)),
         ("Hij verleidt de menigte", r(20, 22))],
    13: [("Toch sprak niemand vrijmoedig van Hem", r(0, 5)),
         ("om de vrees van de Joden", r(6, 10))],
    14: [("Maar als het nu in het midden van het feest was", [1, 0, 2, 3, 4]),
         ("zo ging Jezus op in de tempel", r(5, 10)), ("en leerde", r(11, 12))],
    15: [("En de Joden verwonderden zich", r(0, 3)), ("zeggende", r(4)),
         ("Hoe weet Deze de Schriften", r(5, 8)), ("daar Hij ze niet geleerd heeft", r(9, 10))],
    16: [("Jezus antwoordde hun, en zei", r(0, 5)), ("Mijn leer is Mijne niet", r(6, 11)),
         ("maar Van Degene, Die Mij gezonden heeft", r(12, 15))],
    17: [("Zo iemand wil", r(0, 2)), ("Zijn wil doen", r(3, 6)),
         ("die zal van deze leer bekennen", r(7, 10)), ("of zij uit God is", r(11, 15)),
         ("dan of Ik van Mijzelf spreek", r(16, 20))],
    18: [("Die van zichzelf spreekt", r(0, 3)), ("zoekt zijn eigen eer", r(4, 8)),
         ("maar Die de eer zoekt", r(9, 13)), ("Van Degene, Die Hem gezonden heeft", r(14, 16)),
         ("Die is waarachtig", r(17, 19)), ("en geen ongerechtigheid is in Hem", r(20, 25))],
    19: [("Heeft Mozes u niet de wet gegeven", r(0, 5)),
         ("En niemand van u doet de wet", r(6, 12)), ("Wat zoekt u Mij te doden", r(13, 16))],
    20: [("De menigte antwoordde en zei", r(0, 4)), ("U hebt de duivel", r(5, 6)),
         ("wie zoekt U te doden", r(7, 10))],
    21: [("Jezus antwoordde en zei tot hen", r(0, 5)), ("Een werk heb Ik gedaan", r(6, 8)),
         ("en u verwondert u allen", r(9, 11))],
    22: [("Daarom heeft Mozes u de besnijdenis gegeven", r(0, 6)),
         ("niet dat zij uit Mozes is", r(7, 12)), ("maar uit de vaderen", r(13, 16)),
         ("en u besnijdt een mens op de sabbat", [17, 18, 19, 20, 21])],
    23: [("Als een mens de besnijdenis ontvangt op de sabbat", r(0, 5)),
         ("opdat de wet van Mozes niet gebroken wordt", r(6, 11)),
         ("bent u boos op Mij", r(12, 13)),
         ("dat Ik een heel mens gezond gemaakt heb op de sabbat", r(14, 20))],
    24: [("Oordeel niet naar het aanzien", r(0, 3)),
         ("maar oordeelt een rechtvaardig oordeel", r(4, 8))],
    25: [("Sommigen dan uit die van Jeruzalem zeiden", r(0, 5)),
         ("Is Deze niet", r(6, 8)), ("Die zij zoeken te doden", r(9, 11))],
    26: [("En ziet, Hij spreekt vrijmoedig", r(0, 3)), ("en zij zeggen Hem niets", r(4, 7)),
         ("Zouden nu wel de oversten werkelijk weten", r(8, 12)),
         ("dat Deze werkelijk is de Christus", r(13, 18))],
    27: [("Maar van Deze weten wij, vanwaar Hij is", r(0, 4)),
         ("maar de Christus", r(5, 7)), ("wanneer Hij komen zal", r(8, 9)),
         ("zo zal niemand weten, vanwaar Hij is", r(10, 13))],
    28: [("Jezus dan riep in de tempel", [0, 1, 2, 3, 4, 6, 7]),
         ("lerende en zeggende", [5, 8, 9]), ("En u kent Mij", r(10, 11)),
         ("en u weet, vanwaar Ik ben", r(12, 15)),
         ("en Ik ben van Mijzelf niet gekomen", r(16, 20)),
         ("maar Hij is waarachtig, Die Mij gezonden heeft", r(21, 26)),
         ("Wie u niet kent", r(27, 30))],
    29: [("Maar Ik ken Hem", r(0, 3)), ("want Ik ben van Hem", r(4, 7)),
         ("en Hij heeft Mij gezonden", r(8, 10))],
    30: [("Zij zochten Hem dan te grijpen", r(0, 3)),
         ("maar niemand sloeg de hand aan Hem", r(4, 10)),
         ("want Zijn uur was nog niet gekomen", r(11, 16))],
    31: [("En velen uit de menigte geloofden in Hem",r(0,7)),("en zeiden",r(8,10)),("Wanneer de Christus zal gekomen zijn",r(11,14)),("zal Hij ook meer tekenen doen",r(15,19)),("dan die, welke Deze gedaan heeft",r(20,22))],
    32: [("De Farizeeën hoorden",r(0,2)),("dat de menigte dit van Hem murmelde",r(3,8)),("en de Farizeeën en de overpriesters zonden dienaren",r(9,16)),("opdat zij Hem grijpen zouden",r(17,19))],
    33: [("Jezus dan zei tot hen",r(0,4)),("Nog een kleine tijd ben Ik bij u",r(5,10)),("en Ik ga heen tot Degene, Die Mij gezonden heeft",r(11,16))],
    34: [("U zult Mij zoeken",r(0,1)),("en u zult Mij niet vinden",r(2,4)),("en waar Ik ben",r(5,8)),("kunt u niet komen",r(9,12))],
    35: [("De Joden dan zeiden tot elkaar",r(0,5)),("Waar zal Deze heengaan",r(6,9)),("dat wij Hem niet zullen vinden",r(10,14)),("Zal Hij tot de verstrooide Grieken gaan",r(15,22)),("en de Grieken leren",r(23,26))],
    36: [("Wat is dit voor een rede, die Hij gezegd heeft",r(0,6)),("U zult Mij zoeken",r(7,8)),("en zult Mij niet vinden",r(9,11)),("en waar Ik ben",r(12,15)),("kunt u niet komen",r(16,19))],
    37: [("En op de laatste dag, zijnde de grote dag van het feest",r(0,8)),("stond Jezus en riep",r(9,13)),("zeggende",r(14)),("Zo iemand dorst",r(15,17)),("die komt tot Mij en drinkt",r(18,22))],
    38: [("Die in Mij gelooft",r(0,3)),("zoals de Schrift zegt",r(4,7)),("stromen van het levende water zullen uit zijn buik vloeien",r(8,15))],
    39: [("En dit zei Hij van de Geest",r(0,5)),("Die ontvangen zouden",r(6,8)),("die in Hem geloven",r(9,12)),("want de Heilige Geest was nog niet",r(13,17)),("omdat Jezus nog niet verheerlijkt was",r(18,22))],
    40: [("Velen dan uit de menigte",r(0,4)),("deze rede horende",r(5,7)),("zeiden",r(8)),("Deze is werkelijk de Profeet",r(9,13))],
    41: [("Anderen zeiden", r(0, 1)), ("Deze is de Christus", r(2, 5)),
         ("En anderen zeiden", r(6, 8)), ("Zal dan", r(9, 10)),
         ("de Christus uit Galilea komen", r(11, 16))],
    42: [("Zeg de Schrift niet", r(0, 3)), ("dat de Christus komen zal", [4, 17, 18, 19]),
         ("uit de zade Davids", r(5, 8)), ("en van het plaats Bethlehem", r(9, 13)),
         ("waar David was", r(14, 16))],
    43: [("Er werd dan tweedracht onder de menigte", r(0, 5)), ("om Zijnentwil", r(6, 7))],
    44: [("En sommigen van hen wilden Hem grijpen", r(0, 6)),
         ("maar niemand sloeg de handen aan Hem", r(7, 13))],
    45: [("De dienaren dan kwamen tot de overpriesters en Farizeeën", r(0, 8)),
         ("en die zeiden tot hen", r(9, 12)), ("Waarom hebt u Hem niet gebracht", r(13, 17))],
    46: [("De dienaren antwoordden", r(0, 2)),
         ("Nooit heeft een mens zo gesproken", r(3, 6)), ("zoals deze Mens", r(7, 10))],
    47: [("De Farizeën dan antwoordden hun", r(0, 4)), ("Bent ook u verleid", r(5, 8))],
    48: [("Heeft iemand uit de oversten in Hem geloofd", r(0, 7)),
         ("of uit de Farizeeën", r(8, 11))],
    49: [("Maar deze menigte", r(0, 3)), ("die de wet niet weet", r(4, 8)),
         ("is vervloekt", r(9, 10))],
    50: [("Nicodemus zei tot hen", r(0, 3)),
         ("die in de nacht tot Hem gekomen was", r(4, 8)), ("zijnde één uit hen", r(9, 12))],
    51: [("Oordeel ook onze wet de mens", r(0, 6)),
         ("tenzij dat zij eerst van hem gehoord heeft", r(7, 12)),
         ("en verstaat, wat hij doet", r(13, 16))],
    52: [("Zij antwoordden en zeiden tot hem", r(0, 3)),
         ("Bent u ook uit Galilea", r(4, 10)), ("Onderzoek en zie", r(11, 13)),
         ("dat uit Galilea geen profeet opgestaan is", r(14, 20))],
    53: [("En ieder ging heen naar zijn huis", r(0, 6))],
}

def build(utr_path: Path, osis_path: Path, write=False):
    source = load_tr_chapter(utr_path, osis_path, chapter=7, osis_book="John")
    chapter_path = ROOT / "data" / "johannes" / "7.json"
    chapter = json.loads(chapter_path.read_text(encoding="utf-8"))
    review = {"book": "johannes", "chapter": 7, "reviewed_through": 53, "verses": {}}
    for verse in chapter["verses"][:53]:
        number = int(verse["number"]); tokens = source[number]; groups = SPECS[number]
        covered = [index for _, ids in groups for index in ids]
        if sorted(covered) != list(range(len(tokens))) or len(set(covered)) != len(tokens):
            raise ValueError(f"Johannes 7:{number}: onvolledige of dubbele handmatige review")
        verse["grondtekst"] = [{"woord": t["woord"], "strongs": t["display_strong"],
            "lemma_strongs": t["lemma_strong"], "morfologie": t["morphology"],
            **({"tvm": t["tvm"]} if t.get("tvm") else {})} for t in tokens]
        verse["woordnummers"] = [mapping(anchor, ids, tokens, number) for anchor, ids in groups]
        for item in verse["woordnummers"]: item["herkomst"]["referentie"] = f"JHN 7:{number}"
        review["verses"][str(number)] = [{"tekst": a, "bronindices": ids,
            "reviewstatus": "handmatig_gecontroleerd"} for a, ids in groups]
    if write:
        chapter_path.write_text(json.dumps(chapter, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        review_dir = ROOT / "data" / "woordnummers-review"; review_dir.mkdir(exist_ok=True)
        (review_dir / "johannes-7.json").write_text(json.dumps(review, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        inline_path = ROOT / "data" / "woordnummers-inline" / "johannes.json"
        inline = json.loads(inline_path.read_text(encoding="utf-8")); inline["chapters"]["7"] = {
            str(v["number"]): v["woordnummers"] for v in chapter["verses"][:53]}
        inline_path.write_text(json.dumps(inline, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"verses": 53, "tokens": sum(len(source[n]) for n in range(1, 54))}

def main():
    p=argparse.ArgumentParser(); p.add_argument("--utr",type=Path,required=True); p.add_argument("--osis",type=Path,required=True); p.add_argument("--write",action="store_true")
    a=p.parse_args(); print(json.dumps(build(a.utr,a.osis,a.write),indent=2))
if __name__ == "__main__": main()
