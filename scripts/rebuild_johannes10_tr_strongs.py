#!/usr/bin/env python3
"""Publiceer gecontroleerde TR-koppelingen voor Johannes 10 in versbatches."""

from __future__ import annotations
import argparse, json
from pathlib import Path
from rebuild_nt_tr_strongs import load_tr_chapter
from rebuild_johannes2_tr_strongs import mapping, r

ROOT = Path(__file__).resolve().parents[1]
SPECS = {
    1: [("Voorwaar, voorwaar zeg Ik u", r(0, 3)),
        ("Die niet ingaat door de deur", r(4, 9)), ("in de stal van de schapen", r(10, 14)),
        ("maar van elders inklimt", r(15, 17)), ("die is een dief en moordenaar", r(18, 22))],
    2: [("Maar die door de deur ingaat", r(0, 5)), ("is een herder van de schapen", r(6, 9))],
    3: [("Deze doet de deurwachter open", r(0, 3)),
        ("en de schapen horen zijn stem", r(4, 10)),
        ("en hij roept zijn schapen bij name", r(11, 17)), ("en leidt ze uit", r(18, 20))],
    4: [("En wanneer hij zijn schapen uitgedreven heeft", r(0, 5)),
        ("zo gaat hij voor hen heen", r(6, 8)), ("en de schapen volgen hem", r(9, 13)),
        ("omdat zij zijn stem kennen", r(14, 18))],
    5: [("Maar een vreemde zullen zij in geen geval volgen", r(0, 4)),
        ("maar zullen van hem vluchten", r(5, 8)),
        ("omdat zij de stem van de vreemde niet kennen", r(9, 15))],
    6: [("Deze gelijkenis zei Jezus tot hen", r(0, 6)),
        ("maar zij verstonden niet", r(7, 10)), ("wat het was", r(11, 12)),
        ("dat Hij tot hen sprak", r(13, 15))],
    7: [("Jezus dan zei opnieuw tot hen", r(0, 5)),
        ("Voorwaar, voorwaar zeg Ik u", r(6, 9)),
        ("Ik ben de Deur van de schapen", r(10, 16))],
    8: [("Allen, zovelen als er voor Mij zijn gekomen", r(0, 4)),
        ("zijn dieven en moordenaars", r(5, 8)),
        ("maar de schapen hebben hen niet gehoord", r(9, 14))],
    9: [("Ik ben de Deur", r(0, 3)), ("als iemand door Mij ingaat", r(4, 8)),
        ("die zal behouden worden", r(9)), ("en hij zal ingaan en uitgaan", r(10, 13)),
        ("en weide vinden", r(14, 16))],
    10: [("De dief komt niet", r(0, 3)), ("dan opdat hij stele", r(4, 7)),
         ("en slachte", r(8, 9)), ("en verderft", r(10, 11)),
         ("Ik ben gekomen", r(12, 13)), ("opdat zij het leven hebben", r(14, 16)),
         ("en overvloed hebben", r(17, 19))],
    11: [("Ik ben de goede Herder", r(0, 5)),
         ("de goede herder stelt zijn leven voor de schapen", r(6, 16))],
    12: [("Maar de huurling", r(0, 2)), ("en die geen herder is", r(3, 6)),
         ("wie de schapen niet eigen zijn", r(7, 12)), ("ziet de wolf komen", r(13, 16)),
         ("en verlaat de schapen", r(17, 20)), ("en vlucht", r(21, 22)),
         ("en de wolf grijpt ze", r(23, 27)), ("en verstrooit de schapen", r(28, 31))],
    13: [("En de huurling vlucht", r(0, 3)), ("omdat hij een huurling is", r(4, 6)),
         ("en heeft geen zorg voor de schapen", r(7, 13))],
    14: [("Ik ben de goede Herder", r(0, 5)), ("en Ik ken de Mijn", r(6, 9)),
         ("en wordt van de Mijn gekend", r(10, 14))],
    15: [("Zoals de Vader Mij kent", r(0, 4)), ("zo ken Ik ook de Vader", r(5, 8)),
         ("en Ik stel Mijn leven voor de schapen", r(9, 16))],
    16: [("Ik heb nog andere schapen", r(0, 3)), ("die van deze stal niet zijn", r(4, 10)),
         ("deze moet Ik ook toebrengen", r(11, 14)),
         ("en zij zullen Mijn stem horen", r(15, 19)),
         ("en het zal worden één kudde", r(20, 23)), ("en één Herder", r(24, 25))],
    17: [("Daarom heeft mij de Vader lief", r(0, 5)),
         ("omdat Ik Mijn leven afleg", r(6, 11)), ("opdat Ik het opnieuw neme", r(12, 15))],
    18: [("Niemand neemt hetzelfde van Mij", r(0, 4)),
         ("maar Ik leg het van Mijzelf af", r(5, 10)),
         ("Ik heb macht hetzelfde af te leggen", r(11, 14)),
         ("en heb macht hetzelfde opnieuw te nemen", r(15, 20)),
         ("Dit gebod heb Ik van Mijn Vader ontvangen", r(21, 28))],
    19: [("Er werd dan opnieuw tweedracht onder de Joden", r(0, 6)),
         ("vanwege deze woorden", r(7, 10))],
    20: [("En velen van hen zeiden", r(0, 4)), ("Hij heeft de duivel", r(5, 6)),
         ("en is waanzinnig", r(7, 8)), ("wat hoort u Hem", r(9, 11))],
    21: [("Anderen zeiden", r(0, 1)),
         ("Dit zijn geen woorden van een bezetene", r(2, 7)),
         ("kan ook de duivel van de blinden ogen openen", r(8, 13))],
    22: [("En het was het feest van de vernieuwing van de tempel", r(0, 3)),
         ("te Jeruzalem", r(4, 6)), ("en het was winter", r(7, 9))],
    23: [("En Jezus wandelde in de tempel", r(0, 6)),
         ("in het voorhof van Salomo", r(7, 11))],
    24: [("De Joden dan omringden Hem", r(0, 4)), ("en zeiden tot Hem", r(5, 7)),
         ("Hoe lang houdt U onze ziel op", r(8, 13)),
         ("Als U de Christus bent", r(14, 18)), ("zeg het ons vrijuit", r(19, 21))],
    25: [("Jezus antwoordde hun", r(0, 3)), ("Ik heb het u gezegd", r(4, 5)),
         ("en u gelooft het niet", r(6, 8)), ("De werken", r(9, 10)),
         ("die Ik doe in de Naam van Mijn Vader", r(11, 19)),
         ("die getuigen van Mij", r(20, 23))],
    26: [("Maar u gelooft niet", r(0, 3)),
         ("want u bent niet van Mijn schapen", r(4, 11)),
         ("zoals Ik u gezegd heb", r(12, 14))],
    27: [("Mijn schapen horen Mijn stem", r(0, 7)),
         ("en Ik ken deze", r(8, 10)), ("en zij volgen Mij", r(11, 13))],
    28: [("En Ik geef hun het eeuwige leven", r(0, 4)),
         ("en zij zullen niet verloren gaan in de eeuwigheid", r(5, 11)),
         ("en niemand zal deze uit Mijn hand rukken", r(12, 20))],
    29: [("Mijn Vader", r(0, 2)), ("die ze Mij gegeven heeft", r(3, 5)),
         ("is meerder dan allen", r(6, 8)),
         ("en niemand kan ze rukken uit de hand van Mijn Vader", r(9, 18))],
    30: [("Ik en de Vader zijn één", r(0, 5))],
    31: [("De Joden dan namen opnieuw stenen op", r(0, 5)),
         ("om Hem te stenigen", r(6, 8))],
    32: [("Jezus antwoordde hun", r(0, 3)),
         ("Ik heb u vele treffelijke werken getoond", r(4, 8)), ("van Mijn Vader", r(9, 12)),
         ("om welk werk van die stenigt u Mij", r(13, 18))],
    33: [("De Joden antwoordden Hem, zeggende", r(0, 4)),
         ("Wij stenigen U niet over enig goed werk", r(5, 10)),
         ("maar over godslastering", r(11, 13)), ("en omdat U", r(14, 16)),
         ("een Mens zijnde", r(17, 18)), ("Uzelf God maakt", r(19, 21))],
    34: [("Jezus antwoordde hun", r(0, 3)), ("Is er niet geschreven in uw wet", r(4, 10)),
         ("Ik heb gezegd", r(11, 12)), ("u bent goden", r(13, 14))],
    35: [("Als de wet die goden genoemd heeft", r(0, 3)),
         ("tot wie het woord van God gebeurd is", r(4, 10)),
         ("en de Schrift niet kan gebroken worden", r(11, 16))],
    36: [("Zegt u tot Mij", r(9, 10)), ("Die de Vader geheiligd", r(0, 3)),
         ("en in de wereld gezonden heeft", r(4, 8)), ("U lastert God", r(11, 12)),
         ("omdat Ik gezegd heb", r(13, 14)), ("Ik ben Gods Zoon", r(15, 18))],
    37: [("Als Ik niet doe de werken van Mijn Vader", r(0, 7)),
         ("zo gelooft Mij niet", r(8, 10))],
    38: [("Maar als Ik ze doe", r(0, 2)), ("en zo u Mij niet gelooft", r(3, 6)),
         ("zo gelooft de werken", r(7, 9)),
         ("opdat u mag bekennen en geloven", r(10, 13)),
         ("dat de Vader in Mij is", r(14, 18)), ("en Ik in Hem", r(19, 21))],
    39: [("Zij zochten dan opnieuw Hem te grijpen", r(0, 4)),
         ("en Hij ontging uit hun hand", r(5, 10))],
    40: [("En Hij ging opnieuw over de Jordaan", r(0, 5)), ("tot de plaats", r(6, 8)),
         ("waar Johannes eerst doopte", r(9, 14)), ("en Hij bleef daar", r(15, 17))],
    41: [("En velen kwamen tot Hem", r(0, 4)), ("en zeiden", r(5, 7)),
         ("Johannes deed wel geen teken", r(8, 12)),
         ("maar alles, wat Johannes van Deze zei", r(13, 19)), ("was waar", r(20, 21))],
    42: [("En velen geloofden daar in Hem", r(0, 5))],
}

def build(utr_path: Path, osis_path: Path, write=False):
    source = load_tr_chapter(utr_path, osis_path, chapter=10, osis_book="John")
    chapter_path = ROOT / "data" / "johannes" / "10.json"
    chapter = json.loads(chapter_path.read_text(encoding="utf-8"))
    review = {"book": "johannes", "chapter": 10, "reviewed_through": 42, "verses": {}}
    for verse in chapter["verses"][:42]:
        number = int(verse["number"]); tokens = source[number]; groups = SPECS[number]
        covered = [index for _, ids in groups for index in ids]
        if sorted(covered) != list(range(len(tokens))) or len(set(covered)) != len(tokens):
            raise ValueError(f"Johannes 10:{number}: onvolledige of dubbele handmatige review")
        verse["grondtekst"] = [{"woord": t["woord"], "strongs": t["display_strong"],
            "lemma_strongs": t["lemma_strong"], "morfologie": t["morphology"],
            **({"tvm": t["tvm"]} if t.get("tvm") else {}),
            **({"bronstatus": t["bronstatus"]} if t.get("bronstatus") else {})} for t in tokens]
        verse["woordnummers"] = [mapping(anchor, ids, tokens, number) for anchor, ids in groups]
        occurrences = {}
        for item in verse["woordnummers"]:
            occurrences[item["tekst"]] = occurrences.get(item["tekst"], 0) + 1
            item["voorkomen"] = occurrences[item["tekst"]]
            item["herkomst"]["referentie"] = f"JHN 10:{number}"
        review["verses"][str(number)] = [{"tekst": a, "bronindices": ids,
            "reviewstatus": "handmatig_gecontroleerd"} for a, ids in groups]
    if write:
        chapter_path.write_text(json.dumps(chapter, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        review_dir = ROOT / "data" / "woordnummers-review"; review_dir.mkdir(exist_ok=True)
        (review_dir / "johannes-10.json").write_text(json.dumps(review, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        inline_path = ROOT / "data" / "woordnummers-inline" / "johannes.json"
        inline = json.loads(inline_path.read_text(encoding="utf-8")); inline["chapters"]["10"] = {
            str(v["number"]): v["woordnummers"] for v in chapter["verses"][:42]}
        inline_path.write_text(json.dumps(inline, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"verses": 42, "tokens": sum(len(source[n]) for n in range(1, 43))}

def main():
    p=argparse.ArgumentParser(); p.add_argument("--utr",type=Path,required=True); p.add_argument("--osis",type=Path,required=True); p.add_argument("--write",action="store_true")
    a=p.parse_args(); print(json.dumps(build(a.utr,a.osis,a.write),indent=2))
if __name__ == "__main__": main()
