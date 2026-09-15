#!/usr/bin/env python3
"""Verwerk de Google-opmerkingen bij Ezechiël.

Het grootste deel van de 33 meldingen was al verwerkt: de woorden die als
principe waren gemeld (daags, mensendrek, barbieren, statuur, verwelfsel,
onverzadelijk, boelen, tepelen, opzieden, vloten) staan sinds eerdere rondes
anders in de tekst. Wat overbleef:

1. Citaatopmaak. De meldingen bij 2:2, 3:2 en 9:2 wezen op verzen die zelf
   vertelling zijn, maar waar Gods woorden er vlak omheen ongemarkeerd
   stonden. De werklijst van citaat_ontbreekt.py gaf voor dit boek negentien
   van zulke verzen; die zijn hier één voor één beslist, met de verzen die
   dezelfde rede voortzetten.
2. Op het scherm stond in 23:7, 24:4 en 24:5 nog "de keur(e)", terwijl de
   leestekst al "het beste" had (principe V1625): de opmaak was bij die
   vervanging achtergebleven. Die wordt hier bijgetrokken.
3. "mat" (van meten) wordt "meette", als nieuw principe V1641. Volgens de
   afspraak alleen in de boeken die nog niet definitief zijn: Ezechiël en
   2 Samuël 8:2.

Draaien vanuit de repo-root:  python scripts/apply_google_review_ezechiel.py
"""

from __future__ import annotations

import io
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from citaatopmaak import Hoofdstuk  # noqa: E402
from review_hulp import registreer_principes, schrijf_reviewlijst, verwerk_correcties  # noqa: E402
from sweep_principe import gebalanceerd, kaal, lees, schrijf  # noqa: E402
from synchroniseer_opmaak import bijtrekken  # noqa: E402

BOEK = "ezechiel"
NAAM = "Ezechiël"

# --- 1. woordkeus -----------------------------------------------------------


def trek_opmaak_bij(boek):
    """Zet de opmaak gelijk aan de leestekst waar een eerdere sweep die oversloeg."""
    geraakt = []
    for pad in sorted((ROOT / "data" / boek).glob("*.json"), key=lambda p: int(p.stem)):
        data, vorm = lees(str(pad))
        gewijzigd = False
        for vers in data["verses"]:
            if kaal(vers["text2026_html"]) == kaal(vers["text2026"]):
                continue
            html = bijtrekken(vers["text2026_html"], vers["text2026"])
            if html is None or kaal(html) != kaal(vers["text2026"]) or not gebalanceerd(html):
                raise ValueError("%s %s:%d: opmaak niet veilig bij te trekken"
                                 % (boek, pad.stem, vers["number"]))
            vers["text2026_html"] = html
            geraakt.append("%s:%d" % (pad.stem, vers["number"]))
            gewijzigd = True
        if gewijzigd:
            schrijf(str(pad), data, vorm)
    return geraakt


MAT = re.compile(r"\bmat\b")
MEETTE_BOEKEN = ("ezechiel", "2samuel")
MEETTE = "V1641"


def meette_correcties(boek):
    """Waar 1888 'mat' (van meten) heeft, wordt dat 'meette'.

    De keuze valt op 1888, niet op de huidige tekst; per vers moet het aantal
    keer 'mat' in beide gelijk zijn, anders is er iets anders aan de hand en
    stopt het script.
    """
    correcties = {}
    for pad in sorted((ROOT / "data" / boek).glob("*.json"), key=lambda p: int(p.stem)):
        data = json.loads(io.open(pad, encoding="utf-8").read())
        for vers in data["verses"]:
            in_1888 = len(MAT.findall(vers.get("textSV1888") or ""))
            if not in_1888:
                continue
            tekst = vers["text2026"]
            if len(MAT.findall(tekst)) != in_1888:
                if "meette" in tekst:
                    continue
                raise ValueError("%s %s:%d: 'mat' niet gelijk aan 1888" % (boek, pad.stem, vers["number"]))
            correcties[(int(pad.stem), vers["number"])] = [(tekst, MAT.sub("meette", tekst), MEETTE)]
    return correcties


def meette_principe(bereik):
    return {
        "id": MEETTE,
        "categorie": "Werkwoordsvormen",
        "oud": "mat (verleden tijd van meten)",
        "nieuw": "meette",
        "toelichting": "Beide vormen zijn goed Nederlands, maar 'mat' leest snel als het "
                       "zelfstandig of bijvoeglijk naamwoord, en in Ezechiël 40-47 staat "
                       "het tientallen keren achter elkaar. Toegepast in de boeken die bij "
                       "het doorvoeren nog niet definitief waren.",
        "regex": r"\bmat\b",
        "voorbeeld": "ezechiel 41:13",
        "bereik": bereik,
    }


# --- 2. citaatopmaak --------------------------------------------------------

# (hoofdstuk, handeling, vers, argumenten) voor citaatopmaak.Hoofdstuk.
CITATEN = [
    (3, "na", 1, ("Daarna zei Hij tot mij:", "god")),
    (3, "na", 24, ("en Hij zei tot mij:", "god")),
    (3, "rede", 25, ("god",)),
    (8, "na", 5, ("En Hij zei tot mij:", "god", "naar de weg van het noorden;")),
    (8, "na", 8, ("En Hij zei tot mij:", "god", "graaf nu in die wand.")),
    (8, "na", 9, ("Toen zei Hij tot mij:", "god")),
    (8, "na", 13, ("En Hij zei tot mij:", "god")),
    (8, "na", 15, ("En Hij zei tot mij:", "god")),
    (9, "na", 1, ("zeggende:", "god")),
    (9, "na", 4, ("En JAHWEH zei tot hem:", "god")),
    (9, "na", 5, ("zei Hij voor mijn oren:", "god")),
    (9, "na", 7, ("En Hij zei tot hen:", "god", "ga heen uit.")),
    (10, "na", 2, ("en Hij zei:", "god", "strooi ze over de stad;")),
    (10, "na", 6, ("zeggende:", "god", "van tussen de cherubs,")),
    (11, "na", 2, ("En Hij zei tot mij:", "god")),
    # God beschrijft de mannen en citeert ze: hun woorden staan binnen de Zijne.
    (11, "rede", 3, ("god",)),
    (11, "rede", 4, ("god",)),
    (23, "na", 36, ("En JAHWEH zei tot mij:", "god")),
    # De profeet krijgt woorden mee om uit te spreken; die staan binnen Gods rede.
    (37, "na", 4, ("Toen zei Hij tot mij:", "god")),
    (37, "nest", 4, ("en zeg daartoe:", "mens")),
    (37, "na", 9, ("En Hij zei tot mij:", "god")),
    (37, "nest", 9, ("en zeg tot de geest:", "mens")),
    (43, "na", 18, ("En Hij zei tot mij:", "god")),
    (44, "na", 2, ("En JAHWEH zei tot mij:", "god")),
    (44, "rede", 3, ("god",)),
]


def verwerk_citaten():
    per_hoofdstuk = {}
    for hoofdstuk, handeling, vers, argumenten in CITATEN:
        per_hoofdstuk.setdefault(hoofdstuk, []).append((handeling, vers, argumenten))
    gewijzigd = 0
    for hoofdstuk, handelingen in sorted(per_hoofdstuk.items()):
        h = Hoofdstuk(BOEK, hoofdstuk)
        for handeling, vers, argumenten in handelingen:
            html = h.vers[vers]["text2026_html"]
            if handeling == "rede" and 'class="god-speaks"' in html.split("<i>", 1)[0]:
                continue  # al gedaan
            if handeling == "na" and '<span class="god-speaks">' in html:
                continue
            if handeling == "nest" and html.count("<span") > 1:
                continue
            getattr(h, handeling)(vers, *argumenten)
        gewijzigd += len(h.bewaar())
    return gewijzigd


# --- 3. reviewlijst ---------------------------------------------------------

REEDS = "Stond al zo in de leestekst."
MATEN = "De leesoptie voor maten rekent dit al om"

BESLUITEN = [
    ("1:1", "Is vhebar als locatie genoemd?", "onderzoek", "afgedekt",
     "Ja. Chebar staat op de kaart, met de ligging als onzeker, en in de begrippenlijst "
     "van Ezechiël: een groot kanaal van de Eufraat in Babylonië, waar de ballingen "
     "woonden."),
    ("2:2", "[Citatie]", "citatieopmaak", "afgedekt",
     "2:2 is vertelling; Gods woorden in 2:1 en 2:3 staan gemarkeerd."),
    ("3:2", "[Citatie]", "citatieopmaak", "verwerkt",
     "3:2 is vertelling, maar in 3:1 ontbrak de markering van Gods woorden. Die staat "
     "er nu, net als in 3:24-25."),
    ("3:3", "[Citatie]", "citatieopmaak", "afgedekt", "Klopte al."),
    ("3:12", "Die citatie is van een engel", "citatieopmaak", "afgedekt",
     "Staat als engelenspraak gemarkeerd."),
    ("4:10", "[Principe] Daags - per dag", "principe", "afgedekt",
     REEDS + " Principe V1612."),
    ("4:14", "[Citatie]", "citatieopmaak", "afgedekt", "Klopte al."),
    ("4:15", "[Principe] Mensendrek  - mensenpoep", "principe", "afgedekt",
     REEDS + " Principe V1613."),
    ("5:1", "[Principe] Barbier- kapper", "principe", "afgedekt",
     REEDS + " Principe V1615."),
    ("5:5", "[Citatie]", "citatieopmaak", "afgedekt", "Klopte al."),
    ("7:17", "[Oude woorden vervangen]", "tekst_eenduidig", "afgedekt",
     "'henenvlieten' staat als 'wegvloeien'."),
    ("7:18", "Gruwen", "tekst_eenduidig", "afgedekt",
     "'gruwen' staat als 'huivering' (principe V1617)."),
    ("8:2", "Materialen - verf van Hasmal", "tekst_eenduidig", "afgedekt",
     "'de verf van Hasmal' staat als 'de kleur van glanzend metaal' (principe V1620)."),
    ("8:5", "[Citatie]", "citatieopmaak", "verwerkt",
     "Gods woorden in 8:5 zijn nu gemarkeerd, en de vertelling erna niet; hetzelfde in "
     "8:8, 8:9, 8:13 en 8:15."),
    ("9:2", "[Citatie]", "citatieopmaak", "verwerkt",
     "9:2 is vertelling; de opdrachten eromheen in 9:1, 9:4, 9:5 en 9:7 zijn nu als "
     "Godsspraak gemarkeerd, net als 10:2 en 10:6."),
    ("13:18", "statuur --> soorten aanzien ? principe", "principe", "afgedekt",
     "'statuur' staat als 'gestalte' (principe V1626)."),
    ("16:24", "verwelfsel? --> verhoging ? of een gewelf? --> principe", "principe",
     "afgedekt", "'verwelfsel' staat als 'gewelf' (principe V1623)."),
    ("16:28", "onverzadelijk --> onverzadigbaar ( principe)", "principe", "afgedekt",
     REEDS + " Principe V1622."),
    ("23:5", "boelen - alternatief met princeip?", "principe", "afgedekt",
     "'boelen' staat als 'minnaars' (principe V891)."),
    ("23:8", "tepelen --> tepels", "tekst_eenduidig", "afgedekt",
     REEDS + " Principe V1621."),
    ("24:4", "keur -> beste (principe)", "principe", "verwerkt",
     "De leestekst had al 'het beste' (principe V1625), maar op het scherm stond nog "
     "'de keur': de opmaak was bij die vervanging achtergebleven. Nu bijgetrokken, net "
     "als in 24:5 en 23:7."),
    ("24:5", "opzieden - opkoken (principe)", "principe", "verwerkt",
     "'opzieden' staat als 'doorkoken' (principe V1624). Op het scherm stond hier nog "
     "'de keur van de kudde'; dat is nu 'het beste van de kudde'."),
    ("34:4", "Onderwerp - barmhsrtigheid", "tag_of_onderwerp", "afgedekt",
     "Het vers staat al bij het onderwerp Barmhartigheid."),
    ("34:27", "Maak in de wiki nog een pagina met overige voorwerpen uit het dsgelijks "
     "leven - disselbomen en juk", "wiki", "afgedekt",
     "De pagina Gereedschap en voorwerpen heeft het lemma Juk, met disselbomen als "
     "naamvorm en dit vers erbij."),
    ("40:13", "Meet eenheid", "eenheden", "afgedekt",
     MATEN + ": 'vijf en twintig ellen (ongeveer 13 meter)', met de lange el van "
     "Ezechiël."),
    ("40:14", "Alles nagaan op meeteenheden", "eenheden", "afgedekt",
     MATEN + ": 'zestig ellen (ongeveer 31 meter)'."),
    ("41:13", "[Principe] Mat - meette", "principe", "verwerkt",
     "'mat' is nu 'meette' (principe V1641): 33 keer in Ezechiël en 2 keer in "
     "2 Samuël 8:2, de boeken die nog niet definitief waren."),
    ("42:2", "Veelveenheden ontbreken nog", "eenheden", "afgedekt",
     MATEN + ": 'honderd ellen (ongeveer 52 meter)' en 'vijftig ellen (ongeveer "
     "26 meter)'."),
    ("43:13", "Wat is een boezem van een el?", "onderzoek", "afgedekt",
     "De 'boezem' is de voet of goot onderaan het altaar; er staat nu 'het voetstuk van "
     "een el'. De maten rekent de leesoptie om."),
    ("45:1", "Meetriet was hier 6 ellen toch? Dan ook maat berekenen", "eenheden",
     "afgedekt",
     "Ja, het meetriet is zes lange ellen. " + MATEN + ": 'vijf en twintig duizend "
     "meetrieten (ongeveer 78 km)'."),
    ("45:6", "In dit deel de metrietbals eenheid omrekenen", "eenheden", "afgedekt",
     MATEN + ", ook waar het woord meetriet niet herhaald wordt, met een uitleg in de "
     "tooltip."),
    ("45:10-14", "Ook eenheden toevoegen", "eenheden", "afgedekt",
     "Deze verzen omschrijven de maten zelf (efa, bath, homer, gera); de omrekening "
     "laat zulke definities bewust staan, anders worden ze onleesbaar."),
    ("47:1", "[Principe] Vloten - stroomden", "principe", "afgedekt",
     REEDS + " Principe V506."),
]


def main():
    meette = {boek: meette_correcties(boek) for boek in MEETTE_BOEKEN}
    bereik = {boek: ["%d:%d" % sleutel for sleutel in sorted(correcties)]
              for boek, correcties in meette.items() if correcties}
    if any(meette.values()):
        registreer_principes(MEETTE, [meette_principe(bereik)], gebruikt=[MEETTE])
    bijgetrokken = trek_opmaak_bij(BOEK)
    tekst = verwerk_correcties("ezechiel", NAAM, meette["ezechiel"])
    tekst += verwerk_correcties("2samuel", "2 Samuël", meette["2samuel"])
    citaten = verwerk_citaten()
    lijst = schrijf_reviewlijst(BOEK, NAAM, BESLUITEN)
    print("opmaak bijgetrokken: %s; %d verzen tekst, %d verzen citaatopmaak, %d meldingen "
          "in de reviewlijst." % (", ".join(bijgetrokken) or "-", tekst, citaten, lijst))


if __name__ == "__main__":
    main()
