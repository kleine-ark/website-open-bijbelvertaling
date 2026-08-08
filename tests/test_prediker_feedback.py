"""Regressietests voor de verwerkte lezersopmerkingen bij Prediker."""

import html
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

VERWACHTE_TEKSTEN = {
    (4, 15): "Ik zag al de levenden wandelen onder de zon, met de jongeman, de tweede, die in diens plaats staan zal.",
    (5, 16): "Dat hij ook al zijn dagen in duisternis gegeten heeft; en dat hij veel verdriet gehad heeft, ook zijn ziekte en hevige toorn?",
    (7, 29): "Alleen zie, dit heb ik gevonden, dat God de mens recht gemaakt heeft, maar zij hebben allerlei kwade plannen bedacht.",
    (8, 2): "Ik zeg: Neem acht op het bevel van de koning, vanwege de eed aan God.",
    (8, 12): "Hoewel een zondaar honderd keer kwaad doet, en God hem de dagen verlengt; zo weet ik toch, dat het die zal welgaan, die God vrezen, die voor Zijn aangezicht vrezen.",
    (9, 7): "Ga dan heen, eet uw brood met vreugde, en drink uw wijn met een vrolijk hart; want God heeft al een behagen aan uw werken.",
    (9, 12): "Ook weet de mens zijn tijd niet. Zoals de vissen die in een schadelijk net gevangen worden, en zoals de vogels die met de strik gevangen worden, zo worden de kinderen van de mensen in een kwade tijd verstrikt, wanneer die hen plotseling overvalt.",
    (9, 14): "Er was een kleine stad, en weinig mensen waren daarin; en een groot koning kwam tegen haar, en hij omsingelde ze, en hij bouwde grote belegeringswerken tegen haar.",
    (9, 18): "De wijsheid is beter dan de oorlogswapenen, maar één enig zondaar verderft veel goede dingen.",
    (10, 16): "Wee u, land! waarvan de koning een kind is, en waarvan de vorsten 's morgens eten!",
    (10, 17): "Welgelukzalig bent u, land! waarvan de koning een zoon van de edelen is, en waarvan de vorsten op de juiste tijd eten, om zich te versterken en niet om zich te bedrinken.",
    (10, 18): "Door grote luiheid verzwakt het gebint, en door slapheid van de handen wordt het huis lek.",
    (12, 2): "Voordat de zon, en het licht, en de maan, en de sterren verduisterd worden, en de wolken terugkomen na de regen.",
    (12, 6): "Voordat het zilveren koord ontketend wordt, en de gulden schaal in stukken gestoten wordt, en de kruik aan de springader gebroken wordt, en het rad aan de waterput in stukken gestoten wordt;",
    (12, 11): "De woorden van de wijzen zijn als prikkels en als spijkers, diep ingeslagen door de meesters van de verzamelingen; zij zijn gegeven door de enige Herder.",
    (12, 12): "En wat daarboven is, mijn zoon! wees gewaarschuwd; aan het maken van veel boeken is geen einde, en veel lezen is vermoeiing van het vlees.",
}


def zichtbare_tekst(tekst_html):
    zonder_noten = re.sub(r"<sup\b[^>]*>.*?</sup>", "", tekst_html)
    return html.unescape(re.sub(r"<[^>]+>", "", zonder_noten)).strip()


def test_prediker_opmerkingen_staan_in_de_leestekst_en_html():
    hoofdstukken = {}
    for (hoofdstuk, vers), verwacht in VERWACHTE_TEKSTEN.items():
        if hoofdstuk not in hoofdstukken:
            hoofdstukken[hoofdstuk] = json.loads(
                (ROOT / "data" / "prediker" / f"{hoofdstuk}.json").read_text(encoding="utf-8")
            )
        versdata = next(v for v in hoofdstukken[hoofdstuk]["verses"] if v["number"] == vers)
        assert versdata["text2026"] == verwacht, f"Prediker {hoofdstuk}:{vers}"
        assert zichtbare_tekst(versdata["text2026_html"]) == verwacht, f"Prediker {hoofdstuk}:{vers} HTML"
