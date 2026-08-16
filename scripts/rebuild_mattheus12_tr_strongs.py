#!/usr/bin/env python3
"""Publiceer gecontroleerde TR-koppelingen voor Mattheüs 12 in versbatches."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from rebuild_nt_tr_strongs import load_tr_chapter
from rebuild_johannes2_tr_strongs import mapping, r

ROOT = Path(__file__).resolve().parents[1]


# Nederlands anker, nulgebaseerde TR-indices. Woordvolgordeverschillen blijven
# binnen de inhoudelijk bijbehorende woordgroep.
SPECS = {
    1: [("In die tijd", r(0, 3)), ("ging Jezus", r(4, 6)),
        ("op een sabbatdag", r(7, 8)), ("door het gezaaide", r(9, 11)),
        ("en Zijn discipelen", r(12, 15)), ("hadden honger", r(16)),
        ("en begonnen", r(17, 18)), ("aren te plukken", r(19, 20)),
        ("en te eten", r(21, 22))],
    2: [("En de Farizeën", r(0, 2)), ("dat ziende", r(3)),
        ("zeiden tot Hem", r(4, 5)), ("Zie", r(6)),
        ("Uw discipelen", r(7, 9)), ("doen", r(10)),
        ("wat niet geoorloofd is te doen", r(11, 14)),
        ("op de sabbat", r(15, 16))],
    3: [("Maar Hij zei tot hen", r(0, 3)), ("Hebt u niet gelezen", r(4, 5)),
        ("wat David gedaan heeft", r(6, 8)), ("toen hem hongerde", r(9, 11)),
        ("en hun, die met hem waren", r(12, 15))],
    4: [("Hoe hij gegaan is", r(0, 1)), ("in het huis van God", r(2, 6)),
        ("en de toonbroden gegeten heeft", r(7, 12)),
        ("die hem niet geoorloofd waren te eten", r(13, 18)),
        ("noch ook hun, die met hem waren", r(19, 22)),
        ("maar de priesters alleen", r(23, 27))],
    5: [("Of hebt u niet gelezen in de wet", r(0, 5)),
        ("dat de priesters", [6, 9, 10]), ("op de sabbatdagen", r(7, 8)),
        ("de sabbat ontheiligen in de tempel", r(11, 16)),
        ("en toch onschuldig zijn", r(17, 19))],
    6: [("En Ik zeg u", r(0, 2)), ("dat Eén", r(3)),
        ("meerder dan de tempel", r(4, 6)), ("hier is", r(7, 8))],
    7: [("Maar zo u geweten had", r(0, 2)), ("wat het zij", r(3, 4)),
        ("Ik wil barmhartigheid", r(5, 6)), ("en niet offergave", r(7, 9)),
        ("u zou de onschuldigen niet veroordeeld hebben", r(10, 14))],
    8: [("Want", r(1)), ("de Zoon des mensen", r(6, 9)),
        ("is een Heere", [0, 2]), ("ook van de sabbat", r(3, 5))],
    9: [("En van daar voortgaande", r(0, 2)), ("kwam Hij", r(3)),
        ("in hun synagoge", r(4, 7))],
    10: [("En ziet", r(0, 1)), ("er was een mens", r(2, 3)),
         ("die een verschrompelde hand had", r(4, 7)),
         ("en zij vraagden Hem", r(8, 10)), ("zeggende", r(11)),
         ("Is het ook geoorloofd", r(12, 13)), ("op de sabbatdagen", r(14, 15)),
         ("te genezen", r(16)), ("opdat zij Hem mochten beschuldigen", r(17, 19))],
    11: [("En Hij zei tot hen", r(0, 3)), ("Wat mens zal er zijn onder u", r(4, 8)),
         ("die een schaap heeft", r(9, 13)),
         ("en zo dat op een sabbatdag in een gracht valt", r(14, 20)),
         ("die hetzelfde niet zal aangrijpen en uitheffen", r(21, 25))],
    12: [("Hoe veel gaat nu een mens een schaap te boven", r(0, 4)),
         ("Zo is het dan", r(5)), ("op de sabbatdagen", r(7, 8)),
         ("geoorloofd wel te doen", [6, 9, 10])],
    13: [("Toen zei Hij tot die mens", r(0, 3)), ("Strek uw hand uit", r(4, 7)),
         ("en hij strekte ze uit", r(8, 9)), ("en zij werd hersteld", r(10, 11)),
         ("gezond zoals de andere", r(12, 15))],
    14: [("En de Farizeën", r(0, 2)), ("uitgegaan zijnde", r(7)),
         ("hielden samen raad", r(3, 4)), ("tegen Hem", r(5, 6)),
         ("hoe zij Hem doden mochten", r(8, 10))],
    15: [("Maar Jezus", r(0, 2)), ("dat wetende", r(3)), ("vertrok van daar", r(4, 5)),
         ("en vele menigten", [6, 9, 10]), ("volgden Hem", r(7, 8)),
         ("en Hij genas ze allen", r(11, 14))],
    16: [("En Hij gebood hun scherp", r(0, 2)),
         ("dat zij Hem niet openbaar maken zouden", r(3, 7))],
    17: [("Opdat vervuld zou worden", r(0, 1)), ("wat gesproken is", r(2, 3)),
         ("door Jesaja, de profeet", r(4, 7)), ("zeggende", r(8))],
    18: [("Zie, Mijn Knecht", r(0, 3)), ("die Ik gekozen heb", r(4, 5)),
         ("Mijn Geliefde", r(6, 8)), ("in Welke Mijn ziel een welbehagen heeft", r(9, 14)),
         ("Ik zal Mijn Geest op Hem leggen", r(15, 20)),
         ("en Hij zal het oordeel de heidenen verkondigen", r(21, 25))],
    19: [("Hij zal niet twisten", r(0, 1)), ("noch roepen", r(2, 3)),
         ("noch zal er iemand Zijn stem op de straten horen", r(4, 12))],
    20: [("Het gekrookte riet", r(0, 1)), ("zal Hij niet verbreken", r(2, 3)),
         ("en het rokende lemmet", r(4, 6)), ("zal Hij niet uitblussen", r(7, 8)),
         ("totdat Hij het oordeel zal uitbrengen", [9, 10, 11, 12, 14, 15]),
         ("tot overwinning", r(13))],
    21: [("En", r(0)), ("in Zijn Naam", r(1, 4)), ("zullen de heidenen hopen", r(5, 6))],
    22: [("Toen", r(0)), ("werd tot Hem gebracht", r(1, 2)),
         ("één van de duivel bezeten", r(3)), ("die blind en stom was", r(4, 7)),
         ("en Hij genas hem", r(8, 9)), ("zo dat", r(10)),
         ("de blinde en stomme", r(11, 15)), ("zowel sprak als zag", r(16, 18))],
    23: [("En al de menigten ontzetten zich", r(0, 4)), ("en zeiden", r(5, 6)),
         ("Is niet Deze", r(7, 9)), ("de Zoon van David", r(10, 12))],
    24: [("Maar de Farizeën", r(0, 2)), ("dit gehoord hebbende", r(3)), ("zeiden", r(4)),
         ("Deze werpt de demonen niet uit", r(5, 9)), ("dan door Beëlzebul", r(10, 14)),
         ("de overste van de demonen", r(15, 17))],
    25: [("Maar Jezus", r(1, 3)), ("kennende hun gedachten", [0, 4, 5, 6]),
         ("zei tot hen", r(7, 8)),
         ("Een ieder koninkrijk, dat tegen zichzelf verdeeld is, wordt verwoest", r(9, 14)),
         ("en een iedere stad, of huis, dat tegen zichzelf verdeeld is, zal niet bestaan", r(15, 24))],
    26: [("En als de satan de satan uitwerpt", r(0, 6)),
         ("zo is hij tegen zichzelf verdeeld", r(7, 9)),
         ("hoe zal dan zijn rijk bestaan", r(10, 15))],
    27: [("En als Ik door Beëlzebul de demonen uitwerp", r(0, 7)),
         ("door wie werpen ze dan uw zonen uit", r(8, 13)),
         ("Daarom zullen die uw rechters zijn", r(14, 19))],
    28: [("Maar als Ik", r(0, 2)), ("door de Geest van God", r(3, 5)),
         ("de demonen uitwerp", r(6, 8)),
         ("zo is dan het Koninkrijk van God tot u gekomen", r(9, 16))],
    29: [("Of hoe kan iemand", r(0, 3)), ("in het huis van een sterke inkomen", r(4, 9)),
         ("en zijn huisraad ontroven", r(10, 14)),
         ("tenzij dat hij eerst de sterke gebonden hebbe", r(15, 20)),
         ("en dan zal hij zijn huis beroven", r(21, 26))],
    30: [("Wie met Mij niet is", r(0, 4)), ("die is tegen Mij", r(5, 7)),
         ("en wie met Mij niet verzamelt", r(8, 13)), ("die verstrooit", r(14))],
    31: [("Daarom zeg Ik u", r(0, 3)), ("Alle zonde en lastering", r(4, 7)),
         ("zal de mensen vergeven worden", r(8, 10)),
         ("maar de lastering tegen de Geest", r(11, 15)),
         ("zal de mensen niet vergeven worden", r(16, 19))],
    32: [("En zo wie enig woord gesproken zal hebben tegen de Zoon des mensen", r(0, 9)),
         ("het zal hem vergeven worden", r(10, 11)),
         ("maar zo wie tegen de Heilige Geest zal gesproken hebben", r(12, 20)),
         ("het zal hem niet vergeven worden", r(21, 23)),
         ("noch in deze eeuw", r(24, 28)), ("noch in de toekomende", r(29, 32))],
    33: [("Of maakt de boom goed en zijn vrucht goed", r(0, 9)),
         ("of maakt de boom kwaad en zijn vrucht kwaad", r(10, 19)),
         ("want uit de vrucht wordt de boom gekend", r(20, 26))],
    34: [("U adderengebroed", r(0, 1)), ("hoe kunt u goede dingen spreken", r(2, 5)),
         ("daar u boos bent", r(6, 7)), ("want uit de overvloed van het hart", r(8, 13)),
         ("spreekt de mond", r(14, 16))],
    35: [("De goede mens", r(0, 2)), ("brengt goede dingen voort", r(9, 11)),
         ("uit de goede schat van het hart", r(3, 8)), ("en de slechte mens", r(12, 15)),
         ("brengt boze dingen voort", r(20, 21)), ("uit de boze schat", r(16, 19))],
    36: [("Maar Ik zeg u", r(0, 2)), ("dat van elk ijdel woord", r(3, 6)),
         ("dat de mensen zullen gesproken hebben", r(7, 11)),
         ("zij van hetzelfde zullen rekenschap geven", r(12, 15)),
         ("in de dag van het oordeel", r(16, 18))],
    37: [("Want uit uw woorden zult u gerechtvaardigd worden", r(0, 5)),
         ("en uit uw woorden zult u veroordeeld worden", r(6, 11))],
    38: [("Toen antwoordden sommigen van de Schriftgeleerden en Farizeën", r(0, 6)),
         ("zeggende", r(7)), ("Meester", r(8)), ("wij willen van U wel een teken zien", r(9, 13))],
    39: [("Maar Hij antwoordde en zei tot hen", r(0, 4)),
         ("Het boos en overspelig geslacht", r(5, 8)), ("verzoekt een teken", r(9, 10)),
         ("en hun zal geen teken gegeven worden", r(11, 15)),
         ("dan het teken van Jona, de profeet", r(16, 22))],
    40: [("Want zoals Jona drie dagen en drie nachten was", [0, 1, 2, 3, 9, 10, 11, 12, 13]),
         ("in de buik van de walvis", r(4, 8)),
         ("zo zal de Zoon des mensen drie dagen en drie nachten wezen", [14, 15, 16, 17, 18, 19, 25, 26, 27, 28, 29]),
         ("in het hart van de aarde", r(20, 24))],
    41: [("De mannen van Nineve", r(0, 1)), ("zullen opstaan in het oordeel", r(2, 5)),
         ("met dit geslacht", r(6, 9)), ("en zullen hetzelfde veroordelen", r(10, 12)),
         ("want zij hebben zich bekeerd", r(13, 14)), ("op de prediking van Jona", r(15, 18)),
         ("en ziet", r(19, 20)), ("meer dan Jona is hier", r(21, 23))],
    42: [("De koningin van het zuiden", r(0, 1)), ("zal opstaan in het oordeel", r(2, 5)),
         ("met dit geslacht", r(6, 9)), ("en hetzelfde veroordelen", r(10, 12)),
         ("want zij is gekomen", r(13, 14)), ("van het einde van de aarde", r(15, 19)),
         ("om te horen de wijsheid van Salomo", r(20, 23)), ("en ziet", r(24, 25)),
         ("meer dan Salomo is hier", r(26, 28))],
    43: [("En wanneer", r(0, 1)), ("de onreine geest", r(2, 4)),
         ("van de mens uitgegaan is", r(5, 8)), ("zo gaat hij door dorre plaatsen", r(9, 12)),
         ("zoekende rust", r(13, 14)), ("en vindt ze niet", r(15, 17))],
    44: [("Dan zegt hij", r(0, 1)), ("Ik zal terugkeren", r(2)), ("in mijn huis", r(3, 6)),
         ("vanwaar ik uitgegaan ben", r(7, 8)), ("en komende", r(9, 10)),
         ("vindt hij het leeg", r(11, 12)), ("met bezemen gekeerd", r(13)), ("en versierd", r(14, 15))],
    45: [("Dan gaat hij heen", r(0, 1)), ("en neemt met zich", r(2, 5)),
         ("zeven andere geesten", r(6, 8)), ("bozer dan hij zelf", r(9, 10)),
         ("en ingegaan zijnde", r(11, 12)), ("wonen zij daar", r(13, 14)),
         ("en het laatste daarvan mens wordt erger dan het eerste", r(15, 24)),
         ("Zo zal het ook met dit boos geslacht zijn", r(25, 32))],
    46: [("En als Hij nog tot de menigten sprak", r(0, 5)), ("ziet", r(6)),
         ("Zijn moeder en broers", r(7, 12)), ("stonden buiten", r(13, 14)),
         ("zoekende Hem te spreken", r(15, 17))],
    47: [("En iemand zei tot Hem", r(0, 3)), ("Zie", r(4)),
         ("Uw moeder en Uw broers", r(5, 11)), ("staan daar buiten", r(12, 13)),
         ("zoekende U", r(14, 15)), ("te spreken", r(16))],
    48: [("Maar Hij, antwoordende, zei tot degene die Hem dat zei", r(0, 6)),
         ("Wie is Mijn moeder", r(7, 11)), ("en wie zijn Mijn broeders", r(12, 17))],
    49: [("En Zijn hand uitstrekkende", r(0, 4)), ("over Zijn discipelen", r(5, 8)),
         ("zei Hij", r(9)), ("Zie", r(10)), ("Mijn moeder en Mijn broeders", r(11, 17))],
    50: [("Want zo wie", r(0, 2)), ("de wil van Mijn Vader doet", r(3, 8)),
         ("Die in de hemelen is", r(9, 11)),
         ("dezelfde is Mijn broeder, en zuster, en moeder", r(12, 19))],
}


def build(utr_path: Path, osis_path: Path, write=False):
    source = load_tr_chapter(utr_path, osis_path, chapter=12, osis_book="Matt")
    chapter_path = ROOT / "data" / "mattheus" / "12.json"
    chapter = json.loads(chapter_path.read_text(encoding="utf-8"))
    reviewed_through = max(SPECS)
    review = {"book": "mattheus", "chapter": 12, "reviewed_through": reviewed_through, "verses": {}}
    for verse in chapter["verses"][:reviewed_through]:
        number = int(verse["number"])
        tokens = source[number]
        groups = SPECS[number]
        covered = [index for _, token_ids in groups for index in token_ids]
        if sorted(covered) != list(range(len(tokens))) or len(set(covered)) != len(tokens):
            raise ValueError(f"Mattheüs 12:{number}: onvolledige of dubbele handmatige review")
        verse["grondtekst"] = [{
            "woord": token["woord"], "strongs": token["display_strong"],
            "lemma_strongs": token["lemma_strong"], "morfologie": token["morphology"],
            **({"tvm": token["tvm"]} if token.get("tvm") else {}),
        } for token in tokens]
        verse["woordnummers"] = [mapping(anchor, ids, tokens, number) for anchor, ids in groups]
        for item in verse["woordnummers"]:
            item["herkomst"]["referentie"] = f"MAT 12:{number}"
        review["verses"][str(number)] = [
            {"tekst": anchor, "bronindices": ids, "reviewstatus": "handmatig_gecontroleerd"}
            for anchor, ids in groups
        ]
    if write:
        chapter_path.write_text(json.dumps(chapter, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        review_path = ROOT / "data" / "woordnummers-review" / "mattheus-12.json"
        review_path.write_text(json.dumps(review, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        inline_path = ROOT / "data" / "woordnummers-inline" / "mattheus.json"
        inline = json.loads(inline_path.read_text(encoding="utf-8"))
        inline["chapters"]["12"] = {
            str(verse["number"]): verse["woordnummers"] for verse in chapter["verses"][:reviewed_through]
        }
        inline_path.write_text(json.dumps(inline, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"verses": reviewed_through, "tokens": sum(len(source[n]) for n in range(1, reviewed_through + 1))}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--utr", type=Path, required=True)
    parser.add_argument("--osis", type=Path, required=True)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    print(json.dumps(build(args.utr, args.osis, args.write), indent=2))
