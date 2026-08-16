#!/usr/bin/env python3
"""Herstel de nagekeken citaatopmaak van 2 Koningen zonder tekst te wijzigen."""

from __future__ import annotations

import re
from pathlib import Path

from citaatopmaak import kaal
from sweep_principe import lees, schrijf


ROOT = Path(__file__).resolve().parents[1]
OPEN = re.compile(r'<span class="(?:god-speaks|direct-speech|angel-speaks|devil-speaks)"><i>')


# (spreker, eerste woorden, laatste woorden). Vertelling blijft buiten de span.
RANGES = {
    (1, 4): [("god", "U zult niet afkomen", "maar u zult de dood sterven.")],
    (1, 8): [("mens", "Hij was een man", "om zijn middel."), ("mens", "Het is Elia", "de Thisbiet.")],
    (1, 9): [("mens", "U, man van God", "Kom af.")],
    (2, 2): [("mens", "Blijf toch hier", "naar Beth-el gezonden."), ("mens", "Zo waarachtig", "ik zal u niet verlaten!")],
    (2, 17): [("mens", "Zend.", "Zend.")],
    (3, 12): [("mens", "Het woord van JAHWEH", "bij hem.")],
    (3, 17): [("god", "U zult geen wind", "en uw beesten.")],
    (3, 18): [("god", "Daartoe is dat slecht", "in uw hand geven.")],
    (3, 19): [("god", "En u zult alle", "met stenen verderven.")],
    (4, 4): [("mens", "Kom dan in", "dat vol is.")],
    (4, 10): [("mens", "Laat ons toch", "daar inwijke.")],
    (4, 13): [("mens", "Zeg nu tot haar", "tot de oorlogsoverste?"), ("mens", "Ik woon in", "midden van mijn volk.")],
    (4, 14): [("mens", "Wat is er dan", "haar te doen?"), ("mens", "Zij heeft toch", "man is oud.")],
    (4, 15): [("mens", "Roep haar.", "Roep haar.")],
    (5, 18): [("mens", "In deze zaak", "in deze zaak.")],
    (5, 19): [("mens", "Ga in vrede.", "Ga in vrede.")],
    (6, 2): [("mens", "Laat ons toch", "om er te wonen."), ("mens", "Ga heen.", "Ga heen.")],
    (6, 3): [("mens", "Het believe u", "uw knechten."), ("mens", "Ik zal gaan.", "Ik zal gaan.")],
    (6, 6): [("mens", "Waar is het gevallen?", "Waar is het gevallen?")],
    (6, 7): [("mens", "Neem het tot u op.", "Neem het tot u op.")],
    (6, 18): [("mens", "Sla toch dit volk", "met verblindheden.")],
    (6, 20): [("mens", "JAHWEH, open", "dat zij zien!")],
    (9, 3): [("god", "Ik heb u", "wacht niet langer.")],
    (9, 7): [("god", "En u zult", "van Izebel.")],
    (9, 8): [("god", "En het hele", "in IsraÃ«l.")],
    (9, 9): [("god", "Want Ik zal", "zoon van Ahia.")],
    (9, 10): [("god", "Ook zullen", "haar begrave.")],
    (9, 11): [("mens", "Is het al wel?", "tot u gekomen?"), ("mens", "U kent de man", "zijn spraak.")],
    (9, 17): [("mens", "Ik zie", "Ã©Ã©n hoop."), ("mens", "Neem een ruiter", "Is het vrede?")],
    (9, 19): [("mens", "Zo zegt de koning", "Is het vrede?"), ("mens", "Wat hebt u", "naar achter mij.")],
    (9, 22): [("mens", "Is het ook vrede", "zo vele zijn?")],
    (9, 26): [("mens", "Zo Ik gisteravond", "woord van JAHWEH.")],
    (9, 27): [("mens", "Sla hem ook", "bij Jibleam is;")],
    (9, 32): [("mens", "Wie is met mij?", "Wie?")],
    (10, 6): [("mens", "Zo u van mij", "naar JizreÃ«l.")],
    (10, 8): [("mens", "Zij hebben de hoofden", "koning gebracht."), ("mens", "Leg ze in", "tot morgen.")],
    (10, 10): [("mens", "Weet nu", "gesproken heeft.")],
    (10, 13): [("mens", "Wie bent u?", "Wie bent u?"), ("mens", "Wij zijn", "te groeten.")],
    (10, 15): [("mens", "Is uw hart recht", "met uw hart is?"), ("mens", "Het is, ja", "geef uw hand.")],
    (10, 16): [("mens", "Ga met mij", "voor JAHWEH.")],
    (11, 14): [("mens", "Verraad, verraad!", "Verraad, verraad!")],
    (11, 15): [("mens", "Breng haar uit", "met het zwaard;"), ("mens", "Laat ze", "niet gedood worden.")],
    (12, 5): [("mens", "Zullen de priesters", "gevonden zal worden.")],
    (13, 14): [("mens", "Mijn vader", "en zijn ruiteren!")],
    (13, 16): [("mens", "Leg uw hand", "de handen van de koning.")],
    (13, 17): [("mens", "Doe het venster", "tegen het oosten."), ("mens", "Schiet.", "Schiet."), ("mens", "Het is een pijl", "tot hun vernietiging.")],
    (17, 36): [("god", "Maar JAHWEH", "Hem zult u offergave doen;")],
    (17, 37): [("god", "En de voorschriften", "andere goden niet vrezen.")],
    (17, 38): [("god", "En het verbond", "andere goden niet vrezen.")],
    (17, 39): [("god", "Maar JAHWEH", "al uw vijanden.")],
    (18, 20): [("mens", "U zegt", "tegen mij rebelleert?")],
    (18, 21): [("mens", "Zie nu", "op hem vertrouwen.")],
    (18, 22): [("mens", "Maar zo u", "te Jeruzalem?")],
    (18, 23): [("mens", "Nu dan, wed", "kunnen geven.")],
    (18, 24): [("mens", "Hoe zou u", "en om de ruiteren.")],
    (18, 25): [("mens", "Nu, ben ik", "en verderf het.")],
    (18, 29): [("mens", "Dat Hizkia", "uit zijn hand.")],
    (19, 4): [("mens", "Misschien zal", "dat gevonden wordt.")],
    (19, 7): [("god", "Zie, Ik zal", "in zijn land vellen.")],
    (19, 15): [("mens", "O JAHWEH", "aarde gemaakt.")],
    (19, 16): [("mens", "O, JAHWEH", "te honen.")],
    (19, 18): [("mens", "En hebben hun goden", "die verdorven.")],
    (19, 19): [("mens", "Nu dan, JAHWEH", "alleen God bent.")],
    (19, 23): [("god", "Ik heb met", "van zijn schone veld.")],
    (20, 3): [("mens", "Och, JAHWEH", "huilde heel erg.")],
    (20, 5): [("god", "Ik heb uw gebed", "huis van JAHWEH;")],
    (20, 6): [("god", "En Ik zal", "Mijn knecht David.")],
    (20, 17): [("mens", "Zie, de dagen", "zegt JAHWEH.")],
    (20, 18): [("mens", "Daartoe zullen zij", "van Babel.")],
    (21, 4): [("god", "Te Jeruzalem", "Mijn Naam zetten.")],
    (21, 12): [("god", "Zie, Ik zal", "oren klinken zullen.")],
    (21, 13): [("god", "En Ik zal", "op zijn holligheid.")],
    (21, 14): [("god", "En Ik zal", "al hun vijanden.")],
    (21, 15): [("god", "Daarom, dat zij", "op deze dag toe.")],
    (22, 4): [("mens", "Ga op tot Hilkia", "verzameld hebben;")],
    (22, 5): [("mens", "En dat zij dat", "huis te beteren;")],
    (22, 6): [("mens", "Aan de timmerlieden", "huis te beteren.")],
    (22, 10): [("mens", "De priester Hilkia", "een boek gegeven.")],
    (22, 13): [("mens", "Ga heen", "voor ons geschreven is.")],
    (22, 16): [("god", "Zie, Ik zal", "Juda gelezen heeft.")],
    (22, 17): [("god", "Daarom dat zij", "niet uitgeblust worden.")],
    (22, 18): [("god", "Voor wat betreft", "die u gehoord hebt;")],
    (22, 19): [("god", "Omdat uw hart", "spreekt JAHWEH.")],
    (22, 20): [("god", "Daarom zie", "brengen zal.")],
    (23, 18): [("mens", "Laat hem liggen", "verroere.")],
}

# Schrijf accenttekens als Unicode-escapes. Dat houdt deze grenswaarden
# onafhankelijk van de actieve Windows-codepagina.
RANGES.update({
    (9, 8): [("god", "En het hele", "in Isra\u00ebl.")],
    (9, 17): [("mens", "Ik zie", "\u00e9\u00e9n hoop."), ("mens", "Neem een ruiter", "Is het vrede?")],
    (10, 6): [("mens", "Zo u van mij", "naar Jizre\u00ebl.")],
    # De review vroeg om een expliciete controle van deze hoofdstukken;
    # daarom zijn ook de niet-afzonderlijk gemelde directe redes opgenomen.
    (9, 1): [("mens", "Gord uw middel", "naar Ramoth in Gilead.")],
    (9, 5): [("mens", "Ik heb een woord", "o hoofdman!"), ("mens", "Tot wie", "ons allen?"), ("mens", "Tot u", "o hoofdman!")],
    (9, 13): [("mens", "Jehu is koning geworden!", "Jehu is koning geworden!")],
    (9, 15): [("mens", "Zo het uw wil", "te gaan verkondigen.")],
    (9, 18): [("mens", "Zo zegt de koning", "Is het vrede?"), ("mens", "Wat hebt u", "naar achter mij.")],
    (9, 21): [("mens", "Span aan.", "Span aan.")],
    (9, 22): [("mens", "Is het ook vrede, Jehu?", "Is het ook vrede, Jehu?"), ("mens", "Wat vrede", "zo vele zijn?")],
    (9, 23): [("mens", "Het is bedrog, Ahazia!", "Het is bedrog, Ahazia!")],
    (9, 31): [("mens", "Is het wel", "zijn heer?")],
    (9, 33): [("mens", "Stoot ze van boven neer.", "Stoot ze van boven neer.")],
    (9, 34): [("mens", "Zie nu", "dochter van een koning.")],
    (14, 10): [("mens", "U hebt de Edomieten", "Juda met u?")],
    (18, 26): [("mens", "Spreek toch", "op de muur is.")],
    (18, 27): [("mens", "Heeft mijn heer", "water drinken zullen?")],
    (18, 28): [("mens", "Hoort het woord", "van Assyrië!")],
    (18, 30): [("mens", "JAHWEH zal ons", "gegeven worden.")],
    (18, 31): [("mens", "Hoor naar Hizkia niet", "water van zijn bornput;")],
    (18, 32): [("mens", "Totdat ik kom", "JAHWEH zal ons redden.")],
    (18, 36): [("mens", "U zult hem niet antwoorden.", "U zult hem niet antwoorden.")],
    (19, 3): [("mens", "Zo zegt Hizkia", "kracht om te baren.")],
    (19, 6): [("god", "Vrees niet", "gelasterd hebben.")],
    (19, 10): [("mens", "Laat u uw God", "niet gegeven worden.")],
    (19, 20): [("god", "Dat u tot Mij", "heb Ik gehoord.")],
    (19, 21): [("god", "De jonkvrouw", "het hoofd achter u.")],
    (19, 22): [("god", "Wie hebt u", "van Israël!")],
    (19, 24): [("god", "Ik heb gegraven", "plaatsen verdroogd.")],
    (19, 25): [("god", "Hebt u niet gehoord", "woeste hopen.")],
    (19, 26): [("god", "Daarom waren", "overeind staat.")],
    (19, 27): [("god", "Maar Ik weet", "woeden tegen Mij.")],
    (19, 28): [("god", "Om uw woeden", "u gekomen bent.")],
    (19, 29): [("god", "En dat zij u", "eet hun vruchten.")],
    (19, 30): [("god", "Want het ontkomene", "vrucht dragen.")],
    (19, 31): [("god", "Want van Jeruzalem", "dit doen.")],
    (19, 32): [("god", "Hij zal in deze stad", "wal daartegen opwerpen.")],
    (19, 33): [("god", "Door de weg", "zegt JAHWEH." )],
    (19, 34): [("god", "Want Ik zal", "Mijn knecht.")],
    (22, 8): [("mens", "Ik heb het wetboek", "gevonden;")],
    (22, 9): [("mens", "Uw knechten", "huis van JAHWEH.")],
    (22, 13): [("mens", "Ga heen", "ons geschreven is.")],
    (22, 15): [("god", "Zeg tot de man", "gezonden heeft:")],
})


def zonder_spraak(html: str) -> str:
    aantal = len(OPEN.findall(html))
    html = OPEN.sub("", html)
    for _ in range(aantal):
        html = html.replace("</i></span>", "", 1)
    return html


def zichtbare_indexen(html: str):
    tekst, posities = [], []
    index = 0
    while index < len(html):
        if html.startswith("<sup", index):
            einde = html.find("</sup>", index)
            if einde < 0:
                raise ValueError("onafgesloten nootmarkering")
            index = einde + len("</sup>")
        elif html[index] == "<":
            einde = html.find(">", index)
            if einde < 0:
                raise ValueError("onafgesloten HTML-markering")
            index = einde + 1
        else:
            tekst.append(html[index])
            posities.append(index)
            index += 1
    return "".join(tekst), posities


def markeer(html: str, bereiken):
    basis = zonder_spraak(html)
    zichtbaar, posities = zichtbare_indexen(basis)
    invoegingen = []
    zoek_vanaf = 0
    for spreker, begin, einde in bereiken:
        start = zichtbaar.find(begin, zoek_vanaf)
        stop_begin = zichtbaar.find(einde, start)
        if start < 0 or stop_begin < 0:
            raise ValueError(f"citaatgrens niet gevonden: {begin!r} ... {einde!r}")
        stop = stop_begin + len(einde)
        klasse = "god-speaks" if spreker == "god" else "direct-speech"
        invoegingen.append((posities[start], posities[stop - 1] + 1, klasse))
        zoek_vanaf = stop
    resultaat = basis
    for start, stop, klasse in sorted(invoegingen, reverse=True):
        resultaat = resultaat[:stop] + "</i></span>" + resultaat[stop:]
        resultaat = resultaat[:start] + f'<span class="{klasse}"><i>' + resultaat[start:]
    return resultaat


def main() -> None:
    per_hoofdstuk = {}
    for (hoofdstuk, vers), bereiken in RANGES.items():
        per_hoofdstuk.setdefault(hoofdstuk, {})[vers] = bereiken
    geraakt = 0
    for hoofdstuk, opdrachten in per_hoofdstuk.items():
        pad = ROOT / "data" / "2koningen" / f"{hoofdstuk}.json"
        data, vorm = lees(str(pad))
        for vers in data["verses"]:
            if vers["number"] not in opdrachten:
                continue
            oud = vers["text2026_html"]
            nieuw = markeer(oud, opdrachten[vers["number"]])
            if kaal(oud) != kaal(nieuw):
                raise AssertionError(f"2 Koningen {hoofdstuk}:{vers['number']}: tekst gewijzigd")
            if nieuw != oud:
                vers["text2026_html"] = nieuw
                geraakt += 1
        schrijf(str(pad), data, vorm)
    print(f"Citaatopmaak in {geraakt} verzen van 2 Koningen hersteld.")


if __name__ == "__main__":
    main()
