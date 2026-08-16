#!/usr/bin/env python3
"""Publiceer gecontroleerde TR-koppelingen voor Mattheüs 13 in versbatches."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from rebuild_nt_tr_strongs import load_tr_chapter
from rebuild_johannes2_tr_strongs import mapping, r

ROOT = Path(__file__).resolve().parents[1]

SPECS = {
    1: [("En op die dag", r(0, 4)), ("Jezus", r(5, 7)),
        ("uit het huis gegaan zijnde", r(8, 10)), ("zat bij de zee", r(11, 14))],
    2: [("En tot Hem verzamelden vele menigten", r(0, 5)),
        ("zodat Hij in een schip ging en nederzat", r(6, 12)),
        ("en al de menigte stond op de oever", r(13, 20))],
    3: [("En Hij sprak tot hen vele dingen door gelijkenissen", r(0, 5)),
        ("zeggende", r(6)), ("Zie", r(7)), ("een zaaier ging uit om te zaaien", r(8, 12))],
    4: [("En als hij zaaide", r(0, 4)), ("viel een deel van het zaad", r(5, 7)),
        ("bij de weg", r(8, 10)), ("en de vogels kwamen", r(11, 14)),
        ("en aten het op", r(15, 17))],
    5: [("En een ander deel viel", r(0, 2)), ("op steenachtige plaatsen", r(3, 5)),
        ("waar het niet veel aarde had", r(6, 10)), ("en het ging meteen op", r(11, 13)),
        ("omdat het geen diepte van aarde had", r(14, 19))],
    6: [("Maar als de zon opgegaan was", r(0, 2)), ("zo is het verbrand geworden", r(3)),
        ("en omdat het geen wortel had", r(4, 9)), ("is het verdord", r(10))],
    7: [("En een ander deel viel in de doornen", r(0, 5)),
        ("en de doornen groeiden op", r(6, 9)), ("en verstikten hetzelfde", r(10, 12))],
    8: [("En een ander deel viel in de goede aarde", r(0, 7)), ("en gaf vrucht", r(8, 10)),
        ("het één honderd", r(11, 13)), ("het ander zestig", r(14, 16)),
        ("en het ander dertigvoud", r(17, 19))],
    9: [("Wie oren heeft om te horen, die hore", r(0, 4))],
    10: [("En de discipelen tot Hem komende", r(0, 3)), ("zeiden tot Hem", r(4, 5)),
         ("Waarom spreekt U tot hen door gelijkenissen", r(6, 11))],
    11: [("En Hij, antwoordende, zei tot hen", r(0, 4)), ("Omdat het u gegeven is", r(5, 8)),
         ("de geheimen van het Koninkrijk van de hemelen te weten", r(9, 14)),
         ("maar die is het niet gegeven", r(15, 18))],
    12: [("Want wie heeft", r(0, 2)), ("die zal gegeven worden", r(3, 4)),
         ("en hij zal overvloedig hebben", r(5, 6)), ("maar wie niet heeft", r(7, 10)),
         ("van die zal genomen worden, ook dat hij heeft", r(11, 16))],
    13: [("Daarom spreek Ik tot hen door gelijkenissen", r(0, 5)),
         ("omdat zij ziende niet zien", r(6, 9)), ("en horende niet horen", r(10, 13)),
         ("noch ook verstaan", r(14, 15))],
    14: [("En in hen wordt de profetie van Jesaja vervuld, die zegt", r(0, 8)),
         ("Met het gehoor zult u horen, en in geen geval verstaan", r(9, 14)),
         ("en ziende zult u zien, en in geen geval bemerken", r(15, 21))],
    15: [("Want het hart van dit volk is dik geworden", r(0, 6)),
         ("en zij hebben met de oren moeizaam gehoord", r(7, 11)),
         ("en hun ogen hebben zij toegedaan", r(12, 16)),
         ("opdat zij niet te eniger tijd met de ogen zouden zien", r(17, 20)),
         ("en met de oren horen", r(21, 24)), ("en met het hart verstaan", r(25, 28)),
         ("en zich bekeren", r(29, 30)), ("en Ik hen geneze", r(31, 33))],
    16: [("Maar uw ogen zijn zalig", r(0, 4)), ("omdat zij zien", r(5, 6)),
         ("en uw oren", r(7, 10)), ("omdat zij horen", r(11, 12))],
    17: [("Want voorwaar zeg Ik u", r(0, 3)), ("dat vele profeten en rechtvaardigen", r(4, 8)),
         ("hebben begeerd te zien", r(9, 10)), ("de dingen, die u ziet", r(11, 12)),
         ("en hebben ze niet gezien", r(13, 15)), ("en te horen de dingen, die u hoort", r(16, 19)),
         ("en hebben ze niet gehoord", r(20, 22))],
    18: [("U dan", r(0, 1)), ("hoort", r(2)), ("de gelijkenis van de zaaier", r(3, 6))],
    19: [("Als iemand dat Woord van het Koninkrijk hoort", r(0, 6)), ("en niet verstaat", r(7, 8)),
         ("zo komt de boze", r(9, 11)), ("en rukt weg", r(12, 13)),
         ("wat in zijn hart gezaaid was", r(14, 19)), ("deze is degene", r(20, 22)),
         ("die bij de weg bezaaid is", r(23, 26))],
    20: [("Maar die in steenachtige plaatsen bezaaid is", r(0, 5)), ("deze is degene", r(6, 8)),
         ("die het Woord hoort", r(9, 11)), ("en dat meteen met vreugde ontvangt", r(12, 17))],
    21: [("Maar hij heeft geen wortel in zichzelf", r(0, 5)), ("maar is voor een tijd", r(6, 8)),
         ("en als verdrukking of vervolging komt", r(9, 13)), ("omwille van het Woord", r(14, 16)),
         ("zo wordt hij meteen ten val komt", r(17, 18))],
    22: [("En die in de doornen bezaaid is", r(0, 5)), ("deze is degene", r(6, 8)),
         ("die het Woord hoort", r(9, 11)), ("en de zorgen van deze wereld", r(12, 17)),
         ("en de verleiding van de rijkdom", r(18, 22)), ("verstikt het Woord", r(23, 25)),
         ("en het wordt onvruchtbaar", r(26, 28))],
    23: [("Die nu in de goede aarde bezaaid is", r(0, 7)), ("deze is degene", r(8, 10)),
         ("die het Woord hoort en verstaat", r(11, 15)),
         ("die ook vrucht draagt en voortbrengt", r(16, 20)),
         ("de één honderd", r(21, 23)), ("de ander zestig", r(24, 26)),
         ("en de ander dertigvoud", r(27, 29))],
    24: [("Een andere gelijkenis heeft Hij hun voorgesteld", r(0, 3)), ("zeggende", r(4)),
         ("Het Koninkrijk van de hemelen is gelijk aan een mens", r(5, 10)),
         ("die goed zaad zaaide in zijn akker", r(11, 17))],
    25: [("En als de mensen sliepen", r(0, 5)), ("kwam zijn vijand", r(6, 9)),
         ("en zaaide onkruid", r(10, 12)), ("midden in de tarwe", r(13, 16)),
         ("en ging weg", r(17, 18))],
    26: [("Toen het nu tot kruid opgeschoten was", r(0, 4)), ("en vrucht voortbracht", r(5, 7)),
         ("toen openbaarde zich ook het onkruid", r(8, 12))],
    27: [("En de dienaren van de heer van het huis gingen en zeiden tot hem", r(0, 7)),
         ("Heere", r(8)), ("hebt u niet goed zaad in uw akker gezaaid", r(9, 16)),
         ("Vanwaar heeft hij dan dit onkruid", r(17, 21))],
    28: [("En hij zei tot hen", r(0, 3)), ("Een vijandig mens", r(4, 5)),
         ("heeft dat gedaan", r(6, 7)), ("En de dienaren zeiden tot hem", r(8, 12)),
         ("Wilt u dan", r(13, 14)), ("dat wij heengaan en het verzamelen", r(15, 17))],
    29: [("Maar hij zei", r(0, 2)), ("Nee", r(3)),
         ("opdat u, het onkruid vergaderende, ook mogelijk met hetzelfde de tarwe niet uittrekt", r(4, 12))],
    30: [("Laat ze beiden samen opgroeien tot de oogst", r(0, 5)),
         ("en in de tijd van de oogst", r(6, 11)), ("zal ik tot de maaiers zeggen", r(12, 14)),
         ("Verzamelt eerst dat onkruid", r(15, 18)), ("en bindt het in bossen", r(19, 23)),
         ("om hetzelfde te verbranden", r(24, 27)),
         ("maar brengt de tarwe samen in mijn schuur", r(28, 35))],
    31: [("Een andere gelijkenis heeft Hij hun voorgesteld", r(0, 3)), ("zeggende", r(4)),
         ("Het Koninkrijk van de hemelen is gelijk aan het mosterdzaad", r(5, 12)),
         ("dat een mens heeft genomen en in zijn akker gezaaid", r(13, 20))],
    32: [("Dat wel het minste is onder al de zaden", r(0, 6)),
         ("maar wanneer het opgegroeid is, dan is 't het meeste van de moeskruiden", r(7, 13)),
         ("en het wordt een boom", r(14, 16)),
         ("zo dat de vogels des hemels komen en nestelen in zijn takken", r(17, 28))],
    33: [("Een andere gelijkenis sprak Hij tot hen", r(0, 3)), ("zeggende", r(4)),
         ("Het Koninkrijk van de hemelen is gelijk aan een zuurdesem", r(5, 10)),
         ("die een vrouw nam en verborg in drie maten meel", r(11, 18)),
         ("totdat het geheel gezuurd was", r(19, 22))],
    34: [("Al deze dingen heeft Jezus tot de menigten gesproken door gelijkenissen", r(0, 8)),
         ("en zonder gelijkenis sprak Hij tot hen niet", r(9, 14))],
    35: [("Opdat vervuld zou worden, wat gesproken is door de profeet, zeggende", r(0, 7)),
         ("Ik zal Mijn mond opendoen door gelijkenissen", r(8, 13)),
         ("Ik zal voortbrengen dingen, die verborgen waren van de grondlegging van de wereld", r(14, 18))],
    36: [("Toen nu Jezus de menigten van Zich gelaten had", r(0, 4)), ("ging Hij naar huis", r(5, 9)),
         ("En Zijn discipelen kwamen tot Hem", r(10, 15)), ("zeggende", r(16)),
         ("Verklaar ons de gelijkenis van het onkruid van de akker", r(17, 24))],
    37: [("En Hij, antwoordende, zei tot hen", r(0, 4)),
         ("Die het goede zaad zaait", r(5, 9)), ("is de Zoon des mensen", r(10, 14))],
    38: [("En de akker is de wereld", r(0, 5)),
         ("en het goede zaad zijn de kinderen van het Koninkrijk", r(6, 15)),
         ("en het onkruid zijn de kinderen van de bozen", r(16, 23))],
    39: [("En de vijand, die hetzelfde gezaaid heeft, is de duivel", r(0, 8)),
         ("en de oogst is de voleinding van de wereld", r(9, 15)),
         ("en de maaiers zijn de engelen", r(16, 20))],
    40: [("Zoals dan het onkruid verzameld, en met vuur verbrand wordt", r(0, 7)),
         ("zo zal het ook zijn in de voleinding van deze wereld", r(8, 15))],
    41: [("De Zoon des mensen zal Zijn engelen uitzenden", r(0, 7)),
         ("en zij zullen uit Zijn Koninkrijk verzamelen", r(8, 13)),
         ("al de struikelblokken", r(14, 16)), ("en degenen, die de ongerechtigheid doen", r(17, 21))],
    42: [("En zullen dezelfde in de vurige oven werpen", r(0, 7)),
         ("daar zal gehuil zijn en knersing van de tanden", r(8, 16))],
    43: [("Dan zullen de rechtvaardigen blinken, gelijk de zon", r(0, 6)),
         ("in het Koninkrijk van hun Vader", r(7, 12)),
         ("Die oren heeft om te horen, die hore", r(13, 17))],
    44: [("Opnieuw is het Koninkrijk van de hemelen gelijk aan een schat", r(0, 8)),
         ("in de akker verborgen", r(9, 11)), ("die een mens gevonden hebbende, verborg die", r(12, 15)),
         ("en van blijdschap daarover", r(16, 20)), ("gaat hij heen", r(21)),
         ("en verkoopt al wat hij heeft", r(22, 26)), ("en koopt die akker", r(27, 31))],
    45: [("Opnieuw is het Koninkrijk van de hemelen gelijk aan een koopman", r(0, 8)),
         ("die schone parels zoekt", r(9, 11))],
    46: [("Die, hebbende een parel van grote waarde gevonden", r(0, 4)), ("ging heen", r(5)),
         ("en verkocht al wat hij had", r(6, 9)), ("en kocht dezelfde", r(10, 12))],
    47: [("Opnieuw is het Koninkrijk van de hemelen gelijk aan een net", r(0, 8)),
         ("geworpen in de zee", r(9, 11)), ("en dat allerlei soorten van vissen samenbrengt", r(12, 16))],
    48: [("Dat, wanneer het vol geworden is", r(0, 2)), ("de vissers aan de oever optrekken", r(3, 6)),
         ("en nederzittende", r(7, 8)), ("lezen het goede uit in hun manden", r(9, 13)),
         ("maar het kwade werpen zij weg", r(14, 18))],
    49: [("Zo zal het in de voleinding van de eeuwen wezen", r(0, 6)), ("de engelen zullen uitgaan", r(7, 9)),
         ("en de bozen uit het midden van de rechtvaardigen afscheiden", r(10, 17))],
    50: [("En zullen dezelfde in de vurige oven werpen", r(0, 7)),
         ("daar zal zijn gehuil en knersing van de tanden", r(8, 16))],
    51: [("En Jezus zei tot hen", r(0, 3)), ("Hebt u dit alles verstaan", r(4, 6)),
         ("Zij zeiden tot Hem", r(7, 8)), ("Ja, Heere", r(9, 10))],
    52: [("En Hij zei tot hen", r(0, 3)), ("Daarom", r(4, 5)),
         ("ieder Schriftgeleerde, in het Koninkrijk van de hemelen onderwezen", r(6, 13)),
         ("is gelijk aan een heer van het huis", r(14, 17)),
         ("die uit zijn schat nieuwe en oude dingen voortbrengt", r(18, 26))],
    53: [("En het is gebeurd", r(0, 1)), ("als Jezus deze gelijkenissen geëindigd had", r(2, 8)),
         ("vertrok Hij van daar", r(9, 10))],
    54: [("En gekomen zijnde in Zijn vaderland", r(0, 5)), ("leerde Hij hen in hun synagoge", r(6, 11)),
         ("zodat zij zich ontzetten", r(12, 14)), ("en zeiden", r(15, 16)),
         ("Vanwaar komt Deze die wijsheid en die krachten", r(17, 24))],
    55: [("Is Deze niet de Zoon van de timmerman", r(0, 6)),
         ("en is Zijn moeder niet genoemd Maria", r(7, 12)),
         ("en Zijn broers Jakobus en Joses, en Simon en Judas", r(13, 23))],
    56: [("En Zijn zussen, zijn zij niet allen bij ons", r(0, 8)),
         ("Vanwaar komt dan Deze dit alles", r(9, 13))],
    57: [("En zij namen aanstoot aan Hem", r(0, 3)), ("Maar Jezus zei tot hen", r(4, 8)),
         ("Een profeet is niet ongeëerd", r(9, 12)), ("dan in zijn vaderland, en in zijn huis", r(13, 23))],
    58: [("En Hij heeft daar niet vele krachten gedaan", r(0, 5)), ("vanwege hun ongeloof", r(6, 9))],
}


def build(utr_path: Path, osis_path: Path, write=False):
    source = load_tr_chapter(utr_path, osis_path, chapter=13, osis_book="Matt")
    chapter_path = ROOT / "data" / "mattheus" / "13.json"
    chapter = json.loads(chapter_path.read_text(encoding="utf-8"))
    reviewed_through = max(SPECS)
    review = {"book": "mattheus", "chapter": 13, "reviewed_through": reviewed_through, "verses": {}}
    for verse in chapter["verses"][:reviewed_through]:
        number = int(verse["number"]); tokens = source[number]; groups = SPECS[number]
        covered = [index for _, ids in groups for index in ids]
        if sorted(covered) != list(range(len(tokens))) or len(set(covered)) != len(tokens):
            raise ValueError(f"Mattheüs 13:{number}: onvolledige of dubbele handmatige review")
        verse["grondtekst"] = [{
            "woord": token["woord"], "strongs": token["display_strong"],
            "lemma_strongs": token["lemma_strong"], "morfologie": token["morphology"],
            **({"tvm": token["tvm"]} if token.get("tvm") else {}),
        } for token in tokens]
        verse["woordnummers"] = [mapping(anchor, ids, tokens, number) for anchor, ids in groups]
        for item in verse["woordnummers"]: item["herkomst"]["referentie"] = f"MAT 13:{number}"
        review["verses"][str(number)] = [
            {"tekst": anchor, "bronindices": ids, "reviewstatus": "handmatig_gecontroleerd"}
            for anchor, ids in groups
        ]
    if write:
        chapter_path.write_text(json.dumps(chapter, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        (ROOT / "data" / "woordnummers-review" / "mattheus-13.json").write_text(
            json.dumps(review, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        inline_path = ROOT / "data" / "woordnummers-inline" / "mattheus.json"
        inline = json.loads(inline_path.read_text(encoding="utf-8"))
        inline["chapters"]["13"] = {str(v["number"]): v["woordnummers"] for v in chapter["verses"][:reviewed_through]}
        inline_path.write_text(json.dumps(inline, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"verses": reviewed_through, "tokens": sum(len(source[n]) for n in range(1, reviewed_through + 1))}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(); parser.add_argument("--utr", type=Path, required=True)
    parser.add_argument("--osis", type=Path, required=True); parser.add_argument("--write", action="store_true")
    args = parser.parse_args(); print(json.dumps(build(args.utr, args.osis, args.write), indent=2))
