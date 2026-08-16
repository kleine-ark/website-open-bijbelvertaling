#!/usr/bin/env python3
"""Publiceer gecontroleerde TR-koppelingen voor Johannes 8 in versbatches."""

from __future__ import annotations
import argparse, json
from pathlib import Path
from rebuild_nt_tr_strongs import load_tr_chapter
from rebuild_johannes2_tr_strongs import mapping, r

ROOT = Path(__file__).resolve().parents[1]
SPECS = {
    1: [("Maar Jezus ging", [1, 0, 2]), ("naar de Olijfberg", r(3, 7))],
    2: [("En vroeg in de morgen", r(0, 1)), ("kwam Hij opnieuw in de tempel", r(2, 6)),
        ("en al het volk kwam tot Hem", r(7, 13)),
        ("en nedergezeten zijnde, leerde Hij hen", r(14, 17))],
    3: [("En de Schriftgeleerden en de Farizeeën", [1, 2, 3, 4, 5, 6]),
        ("brachten tot Hem een vrouw", [0, 7, 8, 9]), ("in overspel gegrepen", r(10, 12))],
    4: [("zeiden zij tot Hem", r(0, 1)), ("Meester", r(2)), ("deze vrouw", r(3, 5)),
        ("is op de daad zelf gegrepen, overspel begaande", r(6, 8))],
    5: [("En Mozes heeft ons in de wet geboden", [1, 4, 5, 0, 2, 3, 6]),
        ("dat zulke gestenigd zullen worden", r(7, 9)), ("U dan, wat zegt U", r(10, 13))],
    6: [("En dit zeiden zij", r(0, 2)), ("Hem verzoekende", r(3, 4)),
        ("opdat zij iets hadden, om Hem te beschuldigen", r(5, 8)),
        ("Maar Jezus, neerbuigend", r(9, 13)), ("schreef met de vinger in de aarde", r(14, 19))],
    7: [("En als zij Hem bleven vragen", r(0, 4)), ("richtte Hij Zich op", r(5)),
        ("en zei tot hen", r(6, 8)), ("Die van u zonder zonde is", r(9, 11)),
        ("werpe eerst de steen op haar", r(12, 17))],
    8: [("En opnieuw neerbuigend", r(0, 3)), ("schreef Hij in de aarde", r(4, 7))],
    9: [("Maar zij, dit horende", r(0, 2)),
        ("en van hun geweten overtuigd zijnde", r(3, 7)), ("gingen uit", r(8)),
        ("de één na de andere", r(9, 11)), ("beginnende van de oudsten tot de laatsten", r(12, 18)),
        ("en Jezus werd alleen gelaten", r(19, 23)), ("en de vrouw in het midden staande", r(24, 29))],
    10: [("En Jezus, Zich oprichtende", [1, 2, 3, 0]),
         ("en niemand ziende dan de vrouw", r(4, 9)), ("zei tot haar", r(10, 11)),
         ("Vrouw", r(12, 13)), ("waar zijn deze uw beschuldigers", r(14, 19)),
         ("Heeft u niemand veroordeeld", r(20, 22))],
    11: [("En zij zei", r(0, 2)), ("Niemand, Heere", r(3, 4)),
         ("En Jezus zei tot haar", [6, 8, 9, 5, 7]),
         ("Zo veroordeel Ik u ook niet", r(10, 13)),
         ("ga heen, en zondig niet meer", r(14, 17))],
    12: [("Jezus dan sprak opnieuw tot hen", [0, 1, 2, 3, 4, 5]), ("zeggende", r(6)),
         ("Ik ben het licht van de wereld", r(7, 12)), ("die Mij volgt", r(13, 15)),
         ("zal in de duisternis niet wandelen", r(16, 21)),
         ("maar zal het licht van het leven hebben", r(22, 27))],
    13: [("De Farizeeën dan zeiden tot Hem", r(0, 4)),
         ("U getuigt van Uzelf", r(5, 8)), ("Uw getuigenis is niet waarachtig", r(9, 14))],
    14: [("Jezus antwoordde, en zei tot hen", r(0, 4)),
         ("Hoewel Ik van Mijzelf getuig", r(5, 9)),
         ("zo is toch Mijn getuigenis waarachtig", r(10, 14)),
         ("want Ik weet, vanwaar Ik gekomen ben", r(15, 18)),
         ("en waar Ik heenga", r(19, 21)), ("maar u weet niet", r(22, 25)),
         ("vanwaar Ik kom", r(26, 27)), ("en waar Ik heenga", r(28, 30))],
    15: [("U oordeelt naar het vlees", r(0, 4)), ("Ik oordeel niemand", r(5, 8))],
    16: [("En als Ik ook oordeel", [0, 1, 3, 4, 2]),
         ("Mijn oordeel is waarachtig", r(5, 10)), ("want Ik ben niet alleen", r(11, 14)),
         ("maar Ik en de Vader, Die Mij gezonden heeft", r(15, 21))],
    17: [("En er is ook in uw wet geschreven", r(0, 7)),
         ("dat de getuigenis van twee mensen waarachtig is", r(8, 14))],
    18: [("Ik ben het, Die van Mijzelf getuig", r(0, 5)),
         ("en de Vader, Die Mij gezonden heeft", [6, 10, 11, 12, 13]),
         ("getuigt van Mij", r(7, 9))],
    19: [("Zij dan zeiden tot Hem", r(0, 2)), ("Waar is Uw Vader", r(3, 7)),
         ("Jezus antwoordde", r(8, 10)), ("U kent noch Mij, noch Mijn Vader", r(11, 17)),
         ("als u Mij kende", r(18, 20)),
         ("zo zou u ook Mijn Vader kennen", r(21, 26))],
    20: [("Deze woorden sprak Jezus", r(0, 5)), ("bij de schatkist", r(6, 8)),
         ("lerende in de tempel", r(9, 12)), ("en niemand greep Hem", r(13, 16)),
         ("want Zijn uur was nog niet gekomen", r(17, 22))],
    21: [("Jezus dan zei opnieuw tot hen", [0, 1, 2, 3, 4, 5]),
         ("Ik ga heen", r(6, 7)), ("en u zult Mij zoeken", r(8, 10)),
         ("en in uw zonden zult u sterven", r(11, 16)),
         ("waar Ik heenga", r(17, 19)), ("kunt u niet komen", r(20, 23))],
    22: [("De Joden dan zeiden", r(0, 3)), ("Zal Hij ook Zichzelf doden", r(4, 6)),
         ("omdat Hij zegt", r(7, 8)), ("Waar Ik heenga", r(9, 11)),
         ("kunt u niet komen", r(12, 15))],
    23: [("En Hij zei tot hen", r(0, 2)), ("U bent van beneden", r(3, 7)),
         ("Ik ben van boven", r(8, 12)), ("u bent uit deze wereld", r(13, 18)),
         ("Ik ben niet uit deze wereld", r(19, 25))],
    24: [("Ik heb u dan gezegd", r(0, 2)),
         ("dat u in uw zonden zult sterven", r(3, 8)),
         ("want als u niet gelooft", r(9, 12)), ("dat Ik Die ben", r(13, 15)),
         ("u zult in uw zonden sterven", r(16, 20))],
    25: [("Zij zeiden dan tot Hem", r(0, 2)), ("Wie bent U", r(3, 5)),
         ("En Jezus zei tot hen", [6, 9, 10, 7, 8]),
         ("Wat Ik van de beginne u ook zeg", r(11, 17))],
    26: [("Ik heb vele dingen van u te zeggen en te oordelen", r(0, 6)),
         ("maar Die Mij gezonden heeft, is waarachtig", r(7, 12)),
         ("en de dingen, die Ik van Hem gehoord heb", r(13, 17)),
         ("deze spreek Ik tot de wereld", r(18, 22))],
    27: [("Zij verstonden niet", r(0, 1)), ("dat Hij hun van de Vader sprak", r(2, 6))],
    28: [("Jezus dan zei tot hen", r(0, 4)), ("Wanneer u de Zoon des mensen zult verhoogd hebben", r(5, 10)),
         ("dan zult u verstaan", r(11, 12)), ("dat Ik Die ben", r(13, 15)),
         ("en dat Ik van Mijzelf niets doe", r(16, 20)),
         ("maar deze dingen spreek Ik", [21, 28, 29]),
         ("zoals Mijn Vader Mij geleerd heeft", r(22, 27))],
    29: [("En Die Mij gezonden heeft, is met Mij", r(0, 6)),
         ("De Vader heeft Mij niet alleen gelaten", r(7, 12)),
         ("want Ik doe altijd", [13, 14, 18, 19]), ("wat Hem behagelijk is", r(15, 17))],
    30: [("Als Hij deze dingen sprak", r(0, 2)), ("geloofden velen in Hem", r(3, 6))],
    31: [("Jezus dan zei tot de Joden", r(0, 5)), ("die in Hem geloofden", r(6, 8)),
         ("Als u in Mijn woord blijft", r(9, 16)),
         ("zo bent u werkelijk Mijn discipelen", r(17, 20))],
    32: [("En zult de waarheid verstaan", r(0, 3)),
         ("en de waarheid zal u vrijmaken", r(4, 8))],
    33: [("Zij antwoordden Hem", r(0, 1)), ("Wij zijn Abrahams zaad", r(2, 4)),
         ("en hebben nooit iemand gediend", r(5, 8)), ("hoe zegt U dan", r(9, 12)),
         ("U zult vrij worden", r(13, 14))],
    34: [("Jezus antwoordde hun", r(0, 3)), ("Voorwaar, voorwaar zeg Ik u", r(4, 7)),
         ("Een ieder, die de zonde doet", r(8, 13)),
         ("is een dienaar van de zonde", r(14, 17))],
    35: [("En de dienaar blijft niet eeuwig in het huis", r(0, 10)),
         ("de zoon blijft er eeuwig", r(11, 16))],
    36: [("Als dan de Zoon u zal vrijgemaakt hebben", r(0, 5)),
         ("zo zult u werkelijk vrij zijn", r(6, 8))],
    37: [("Ik weet, dat u Abrahams zaad bent", r(0, 4)),
         ("maar u zoekt Mij te doden", r(5, 8)),
         ("want Mijn woord heeft in u geen plaats", r(9, 17))],
    38: [("Ik spreek", [0, 7]), ("wat Ik bij Mijn Vader gezien heb", r(1, 6)),
         ("u doet dan ook", [8, 9, 10, 17]),
         ("wat u bij uw vader gezien hebt", r(11, 16))],
    39: [("Zij antwoordden en zeiden tot Hem", r(0, 3)),
         ("Abraham is onze vader", r(4, 8)), ("Jezus zei tot hen", r(9, 12)),
         ("Als u Abrahams kinderen was", r(13, 17)),
         ("zo zou u de werken van Abraham doen", r(18, 23))],
    40: [("Maar nu zoekt u Mij te doden", r(0, 4)), ("een Mens", r(5)),
         ("Die u de waarheid gesproken heb", r(6, 10)),
         ("die Ik van God gehoord heb", r(11, 15)), ("Dat deed Abraham niet", r(16, 19))],
    41: [("U doet de werken van uw vader", r(0, 6)),
         ("Zij zeiden dan tot Hem", r(7, 9)), ("Wij zijn niet geboren uit hoererij", r(10, 14)),
         ("wij hebben een Vader, namelijk God", r(15, 19))],
    42: [("Jezus dan zei tot hen", r(0, 3)), ("Als God uw Vader was", r(4, 9)),
         ("zo zou u Mij liefhebben", r(10, 12)),
         ("want Ik ben van God uitgegaan", r(13, 18)), ("en kom van Hem", r(19, 20)),
         ("Want Ik ben ook van Mijzelf niet gekomen", r(21, 25)),
         ("maar Hij heeft Mij gezonden", r(26, 29))],
    43: [("Waarom kent u Mijn spraak niet", r(0, 7)),
         ("Het is, omdat u Mijn woord niet kunt horen", r(8, 15))],
    44: [("U bent uit de vader de duivel", r(0, 5)),
         ("en wilt de begeerten van uw vader doen", r(6, 13)),
         ("die was een mensenmoordenaar van de beginne", r(14, 18)),
         ("en is in de waarheid niet staande gebleven", r(19, 24)),
         ("want geen waarheid is in hem", r(25, 30)),
         ("Wanneer hij de leugen spreekt", r(31, 34)),
         ("zo spreekt hij uit zijn eigen", r(35, 38)),
         ("want hij is een leugenaar", r(39, 41)),
         ("en de vader van die leugen", r(42, 45))],
    45: [("Maar Mij", r(0, 1)), ("omdat Ik u de waarheid zeg", r(2, 5)),
         ("gelooft u niet", r(6, 8))],
    46: [("Wie van u overtuigt Mij van zonde", r(0, 6)),
         ("En als Ik de waarheid zeg", r(7, 10)),
         ("waarom gelooft u Mij niet", r(11, 16))],
    47: [("Die uit God is", r(0, 4)), ("hoort de woorden van God", r(5, 9)),
         ("daarom hoort u niet", r(10, 14)), ("omdat u uit God niet bent", r(15, 20))],
    48: [("De Joden dan antwoordden en zeiden tot Hem", r(0, 6)),
         ("Zeggen wij niet wel", r(7, 10)), ("dat U een Samaritaan bent", r(11, 14)),
         ("en de duivel hebt", r(15, 17))],
    49: [("Jezus antwoordde", r(0, 1)), ("Ik heb de duivel niet", r(2, 5)),
         ("maar Ik eer Mijn Vader", r(6, 10)), ("en u onteert Mij", r(11, 14))],
    50: [("Maar Ik zoek Mijn eer niet", r(0, 6)),
         ("er is Een, Die ze zoekt en oordeelt", r(7, 11))],
    51: [("Voorwaar, voorwaar zeg Ik u", r(0, 3)),
         ("Zo iemand Mijn woord zal bewaard hebben", r(4, 10)),
         ("die zal de dood niet zien in de eeuwigheid", r(11, 17))],
    52: [("De Joden dan zeiden tot Hem", r(0, 4)), ("Nu bekennen wij", r(5, 6)),
         ("dat U de duivel hebt", r(7, 9)), ("Abraham is gestorven", r(10, 11)),
         ("en de profeten", r(12, 14)), ("en zegt U", r(15, 17)),
         ("Zo iemand Mijn woord bewaard zal hebben", r(18, 23)),
         ("die zal de dood niet smaken in de eeuwigheid", r(24, 30))],
    53: [("Bent U meerder", r(0, 3)), ("dan onze vader Abraham", r(4, 7)),
         ("die gestorven is", r(8, 9)), ("en de profeten zijn gestorven", r(10, 13)),
         ("wie maakt U Uzelf", r(14, 17))],
    54: [("Jezus antwoordde", r(0, 1)), ("Als Ik Mijzelf eer", r(2, 5)),
         ("zo is Mijn eer niets", r(6, 10)), ("Mijn Vader is het", r(11, 14)),
         ("Die Mij eer", r(15, 17)), ("Wie u zegt", r(18, 20)),
         ("dat uw God is", r(21, 24))],
    55: [("En u kent Hem niet", r(0, 3)), ("maar Ik ken Hem", r(4, 7)),
         ("en als Ik zeg", r(8, 10)), ("dat Ik Hem niet ken", r(11, 14)),
         ("zo zal Ik u gelijk zijn", r(15, 17)), ("dat is een leugenaar", r(18)),
         ("maar Ik ken Hem", r(19, 21)), ("en bewaar Zijn woord", r(22, 26))],
    56: [("Abraham, uw vader", r(0, 3)), ("heeft met verheuging verlangd", r(4)),
         ("opdat hij Mijn dag zien zou", r(5, 10)),
         ("en hij heeft hem gezien", r(11, 12)), ("en is verblijd geweest", r(13, 14))],
    57: [("De Joden dan zeiden tot Hem", r(0, 5)),
         ("U hebt nog geen vijftig jaren", r(6, 9)),
         ("en hebt U Abraham gezien", r(10, 12))],
    58: [("Jezus zei tot hen", r(0, 3)), ("Voorwaar, voorwaar zeg Ik u", r(4, 7)),
         ("Voordat Abraham was", r(8, 10)), ("ben Ik", r(11, 12))],
    59: [("Zij namen dan stenen op", r(0, 2)), ("dat zij ze op Hem wierpen", r(3, 6)),
         ("Maar Jezus verborg Zich", r(7, 9)), ("en ging uit de tempel", r(10, 14)),
         ("gaande door het midden van hen", r(15, 18)), ("en ging zo voorbij", r(19, 21))],
}

UNMAPPED = {
    3: {"bronindices": r(13, 17), "reden": "versgrens_afwijking",
        "toelichting": "Deze TR-woorden corresponderen met het begin van de Nederlandse tekst in Johannes 8:4."},
}

def build(utr_path: Path, osis_path: Path, write=False):
    source = load_tr_chapter(utr_path, osis_path, chapter=8, osis_book="John")
    chapter_path = ROOT / "data" / "johannes" / "8.json"
    chapter = json.loads(chapter_path.read_text(encoding="utf-8"))
    review = {"book": "johannes", "chapter": 8, "reviewed_through": 59, "verses": {}}
    for verse in chapter["verses"][:59]:
        number = int(verse["number"]); tokens = source[number]; groups = SPECS[number]
        covered = [index for _, ids in groups for index in ids]
        excluded = UNMAPPED.get(number, {}).get("bronindices", [])
        if sorted(covered + excluded) != list(range(len(tokens))) or len(set(covered + excluded)) != len(tokens):
            raise ValueError(f"Johannes 8:{number}: onvolledige of dubbele handmatige review")
        verse["grondtekst"] = [{"woord": t["woord"], "strongs": t["display_strong"],
            "lemma_strongs": t["lemma_strong"], "morfologie": t["morphology"],
            **({"tvm": t["tvm"]} if t.get("tvm") else {})} for t in tokens]
        verse["woordnummers"] = [mapping(anchor, ids, tokens, number) for anchor, ids in groups]
        occurrences = {}
        for item in verse["woordnummers"]:
            occurrences[item["tekst"]] = occurrences.get(item["tekst"], 0) + 1
            item["voorkomen"] = occurrences[item["tekst"]]
        for item in verse["woordnummers"]: item["herkomst"]["referentie"] = f"JHN 8:{number}"
        review["verses"][str(number)] = {
            "koppelingen": [{"tekst": a, "bronindices": ids,
                "reviewstatus": "handmatig_gecontroleerd"} for a, ids in groups],
            "ongemapt": [UNMAPPED[number]] if number in UNMAPPED else [],
        }
    if write:
        chapter_path.write_text(json.dumps(chapter, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        review_dir = ROOT / "data" / "woordnummers-review"; review_dir.mkdir(exist_ok=True)
        (review_dir / "johannes-8.json").write_text(json.dumps(review, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        inline_path = ROOT / "data" / "woordnummers-inline" / "johannes.json"
        inline = json.loads(inline_path.read_text(encoding="utf-8")); inline["chapters"]["8"] = {
            str(v["number"]): v["woordnummers"] for v in chapter["verses"][:59]}
        inline_path.write_text(json.dumps(inline, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"verses": 59, "tokens": sum(len(source[n]) for n in range(1, 60)),
            "mapped_tokens": sum(len(source[n]) for n in range(1, 60)) - 5}

def main():
    p=argparse.ArgumentParser(); p.add_argument("--utr",type=Path,required=True); p.add_argument("--osis",type=Path,required=True); p.add_argument("--write",action="store_true")
    a=p.parse_args(); print(json.dumps(build(a.utr,a.osis,a.write),indent=2))
if __name__ == "__main__": main()
