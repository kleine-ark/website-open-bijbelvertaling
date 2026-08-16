#!/usr/bin/env python3
"""Publiceer gecontroleerde TR-koppelingen voor Mattheüs 15 in versbatches."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from rebuild_nt_tr_strongs import load_tr_chapter
from rebuild_johannes2_tr_strongs import mapping, r

ROOT = Path(__file__).resolve().parents[1]

SPECS = {
    1: [("Toen kwamen tot Jezus enige Schriftgeleerden en Farizeën, die van Jeruzalem waren, zeggende", r(0, 10))],
    2: [("Waarom overtreden Uw discipelen de inzetting van de ouden? Want zij wassen hun handen niet, wanneer zij brood zullen eten", r(0, 18))],
    3: [("Maar Hij, antwoordende, zei tot hen: Waarom overtreedt ook u het gebod van God, door uw inzetting?", r(0, 17))],
    4: [("Want God heeft geboden, zeggende: Eer uw vader en moeder, en: Wie vader of moeder vloekt, die zal de dood sterven", r(0, 19))],
    5: [("Maar u zegt: Zo wie tot vader of moeder zal zeggen: Het is een gave, zo wat u van mij zou kunnen ten nutte komen; en zijn vader of zijn moeder in geen geval zal eren, die voldoet", r(0, 16))],
    6: [("En u hebt zo Gods gebod krachteloos gemaakt door uw inzetting", r(0, 20))],
    7: [("U huichelaars! Wel heeft Jesaja van u geprofeteerd, zeggende", r(0, 6))],
    8: [("Dit volk nadert Mij met hun mond, en eer Mij met de lippen, maar hun hart houdt zich verre van Mij", r(0, 20))],
    9: [("Maar tevergeefs eren zij Mij, lerende onderwijzingen, die geboden van mensen zijn", r(0, 7))],
    10: [("En als Hij de menigte tot Zich geroepen had, zei Hij tot hen: Hoor en verstaat", r(0, 8))],
    11: [("Wat in de mond ingaat, ontreinigt de mens niet; maar wat in de mond uitgaat, dat ontreinigt de mens", r(0, 18))],
    12: [("Toen kwamen Zijn discipelen tot Hem, en zeiden tot Hem: Weet U wel, dat de Farizeën deze rede horende, aanstoot hebben genomen?", r(0, 14))],
    13: [("Maar Hij, antwoordende zei: Alle plant, die Mijn hemelse Vader niet geplant heeft, zal uitgeroeid worden", r(0, 14))],
    14: [("Laat hen varen; zij zijn blinde leidslieden van de blinden. Als nu de blinde de blinde leidt, zo zullen zij beiden in de gracht vallen", r(0, 14))],
    15: [("En Petrus, antwoordende, zei tot Hem: Verklaar ons deze gelijkenis", r(0, 10))],
    16: [("Maar Jezus zei: Bent ook u alsnog onwetend?", r(0, 8))],
    17: [("Verstaat u nog niet, dat al wat in de mond ingaat, in de buik komt, en in de heimelijkheid wordt uitgeworpen?", r(0, 16))],
    18: [("Maar die dingen, die in de mond uitgaan, komen voort uit het hart, en dezelfde ontreinigen de mens", r(0, 13))],
    19: [("Want uit het hart komen voort boze bedenkingen, doodslagen, overspelen, hoererijen, dieverijen, valse getuigenissen, lasteringen", r(0, 12))],
    20: [("Deze dingen zijn het, die de mens ontreinigen; maar het eten met ongewassen handen ontreinigt de mens niet", r(0, 14))],
    21: [("En Jezus van daar gaande, vertrok naar de delen van Tyrus en Sidon", r(0, 11))],
    22: [("En ziet, een Kananese vrouw, uit die gebied komende, riep tot Hem, zeggende: Heere! U Zoon van David, ontferm U mijn! mijn dochter is ernstig van de duivel bezeten", r(0, 21))],
    23: [("Maar Hij antwoordde haar niet één woord. En Zijn discipelen, tot Hem komende, baden Hem, zeggende: Laat haar van U; want zij roept ons na", r(0, 19))],
    24: [("Maar Hij, antwoordende, zei: Ik ben niet gezonden, dan tot de verloren schapen van het huis van Israël", r(0, 14))],
    25: [("En zij kwam en aanbad Hem, zeggende: Heere, help mij!", r(0, 8))],
    26: [("Maar Hij antwoordde en zei: Het is niet passend het brood van de kinderen te nemen, en de hondjes voor te werpen", r(0, 15))],
    27: [("En zij zei: Ja, Heere! maar de hondjes eten ook van de brokjes die er vallen van de tafel van hun heren", r(0, 20))],
    28: [("Toen antwoordde Jezus, en zei tot haar: O vrouw! groot is uw geloof; u gebeure, zoals u wilt. En haar dochter werd gezond vanaf dat moment", r(0, 24))],
    29: [("En Jezus, van daar vertrekkende, kwam aan de zee van Galilea, en klom op de berg, en zat daar neer", r(0, 17))],
    30: [("En vele menigten zijn tot Hem gekomen, hebbende bij zich kreupelen, blinden, stommen, lammen, en vele anderen, en wierpen ze voor de voeten van Jezus; en Hij genas dezelfde", r(0, 25))],
    31: [("Zo dat de menigten zich verwonderden, ziende de stommen sprekende, de lammen gezond, de kreupelen wandelende, en de blinden ziende; en zij verheerlijkten de God van Israël", r(0, 18))],
    32: [("En Jezus, Zijn discipelen tot Zich geroepen hebbende, zei: Ik word innerlijk met ontferming bewogen over de menigte, omdat zij nu drie dagen bij Mij gebleven zijn, en hebben niet wat zij eten zouden; en Ik wil hen niet nuchter van Mij laten, opdat zij op de weg niet bezwijken", r(0, 33))],
    33: [("En Zijn discipelen zeiden tot Hem: Vanwaar zullen wij zovele broden in de woestijn bekomen, dat wij zulk een grote menigte zouden verzadigen?", r(0, 15))],
    34: [("En Jezus zei tot hen: Hoevele broden hebt u? Zij zeiden: Zeven, en weinige visjes", r(0, 14))],
    35: [("En Hij gebood de menigten neer te zitten op de aarde", r(0, 7))],
    36: [("En Hij nam de zeven broden en de vissen, en als Hij gedankt had, brak Hij ze, en gaf ze Zijn discipelen; en de discipelen gaven ze aan de menigte", r(0, 19))],
    37: [("En zij aten allen en werden verzadigd, en zij namen op, het overschot van de stukken brood, zeven volle manden", r(0, 13))],
    38: [("En die daar gegeten hadden, waren vier duizend mannen, zonder de vrouwen en kinderen", r(0, 9))],
    39: [("En de menigten van Zich gelaten hebbende, ging Hij in het schip, en kwam in het gebied van Magdala", r(0, 13))],
}


def build(utr_path: Path, osis_path: Path, write=False):
    source = load_tr_chapter(utr_path, osis_path, chapter=15, osis_book="Matt")
    chapter_path = ROOT / "data" / "mattheus" / "15.json"
    chapter = json.loads(chapter_path.read_text(encoding="utf-8"))
    reviewed_through = max(SPECS)
    review = {"book": "mattheus", "chapter": 15, "reviewed_through": reviewed_through, "verses": {}}
    for verse in chapter["verses"][:reviewed_through]:
        number = int(verse["number"]); tokens = source[number]; groups = SPECS[number]
        covered = [index for _, ids in groups for index in ids]
        if sorted(covered) != list(range(len(tokens))) or len(set(covered)) != len(tokens):
            raise ValueError(f"Mattheüs 15:{number}: onvolledige of dubbele handmatige review")
        verse["grondtekst"] = [{"woord": t["woord"], "strongs": t["display_strong"], "lemma_strongs": t["lemma_strong"], "morfologie": t["morphology"], **({"tvm": t["tvm"]} if t.get("tvm") else {})} for t in tokens]
        verse["woordnummers"] = [mapping(anchor, ids, tokens, number) for anchor, ids in groups]
        for item in verse["woordnummers"]: item["herkomst"]["referentie"] = f"MAT 15:{number}"
        review["verses"][str(number)] = [{"tekst": a, "bronindices": ids, "reviewstatus": "handmatig_gecontroleerd"} for a, ids in groups]
    if write:
        chapter_path.write_text(json.dumps(chapter, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        (ROOT / "data" / "woordnummers-review" / "mattheus-15.json").write_text(json.dumps(review, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        inline_path = ROOT / "data" / "woordnummers-inline" / "mattheus.json"; inline = json.loads(inline_path.read_text(encoding="utf-8"))
        inline["chapters"]["15"] = {str(v["number"]): v["woordnummers"] for v in chapter["verses"][:reviewed_through]}
        inline_path.write_text(json.dumps(inline, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"verses": reviewed_through, "tokens": sum(len(source[n]) for n in range(1, reviewed_through + 1))}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(); parser.add_argument("--utr", type=Path, required=True); parser.add_argument("--osis", type=Path, required=True); parser.add_argument("--write", action="store_true")
    args = parser.parse_args(); print(json.dumps(build(args.utr, args.osis, args.write), indent=2))
