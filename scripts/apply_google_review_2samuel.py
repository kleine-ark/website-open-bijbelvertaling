#!/usr/bin/env python3
"""Verwerk de Google-opmerkingen bij 2 Samuël die na de review van augustus
nog openstonden.

De ronde van augustus (apply_review_2samuel_20260813.py) nam alleen de
eenduidige woordvervangingen mee. Wat bleef liggen was vooral citaatopmaak,
een handvol zinnen die na die vervangingen niet meer liepen, en verzoeken om
tags. Die staan hier bij elkaar, omdat ze in dezelfde verzen samenkomen:

1. Woordkeus (CORRECTIES). Elke vervanging hangt aan een principe: aan het
   bestaande principe waarvan zij het werk afmaakt, of aan een nieuw principe
   met een bereik van alleen de beoordeelde verzen (NIEUW).
2. Citaatopmaak (AANKONDIGING, INKORTEN, OMHULLEN, NESTEN, ONTNESTEN). De
   aankondiging hoort buiten de span, het verhalende staartje ook, en een
   geneste span markeert alleen een wisseling van spreker.
3. Tags (TAGS, NIEUWE_TAGS).
4. De reviewlijst (BESLUITEN): per opmerking wat ermee gedaan is.

Wat níet hier staat: de opmerkingen die om een principe voor alle boeken
vroegen (wiens, één als geen telwoord, kinderen Ammons, wederkomen, bij
geval, zachtkens, bekwaam, vertoeven). Die raken meer boeken dan 2 Samuël en
horen in een eigen doorvoering.

Draaien vanuit de repo-root:  python scripts/apply_google_review_2samuel.py
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from sweep_principe import gebalanceerd, kaal, lees, nieuwe_diff, schrijf  # noqa: E402
from synchroniseer_opmaak import bijtrekken  # noqa: E402

BOEK = "2samuel"
NAAM = "2 Samuël"
PREFIX = "MR-2SA-"

# --- 1. woordkeus -----------------------------------------------------------

# (hoofdstuk, vers): [(oud, nieuw, principe)]
CORRECTIES = {
    (1, 9): [("deze maliënkolder", "deze benauwdheid", "MR-2SA-001")],
    # MR-SK-009 zette armgesmijde om, maar liet lidwoord en voornaamwoord staan.
    (1, 10): [("het armband, dat aan zijn arm was", "de armband, die aan zijn arm was",
               "MR-SK-009")],
    (3, 29): [
        (
            "Het blijve op het hoofd van Joab, en op het hele huis van zijn vader; "
            "en er worde van het huis van Joab niet afgesneden, die een vloed hebbe, "
            "en melaats zij, en zich aan de stok houde, en door het zwaard valle, "
            "en broodsgebrek hebbe!",
            "Laat het blijven op het hoofd van Joab, en op het hele huis van zijn "
            "vader; en laat er in het huis van Joab nooit iemand ontbreken die een "
            "vloed heeft, of melaats is, of zich aan de stok vasthoudt, of door het "
            "zwaard valt, of gebrek aan brood heeft!",
            "V779",
        )
    ],
    # MR-SK-007 maakte van "als zullende" "alsof zij", maar het werkwoord ontbrak.
    (4, 6): [("alsof zij tarwe halen", "alsof zij tarwe kwamen halen", "MR-SK-007")],
    # N1 maakte van "den reizenden" "de reizenden" en liet de verbuiging staan.
    (12, 4): [("voor de reizenden man", "voor de reizende man", "N1")],
    (14, 30): [
        ("ga heen, en steekt het aan met vuur", "ga heen, en steek het aan met vuur",
         "V1158"),
        # MR-SK-065 deed de eerste van de twee plaatsen in dit vers.
        ("staken dat stuk akkers aan met vuur", "staken die akker aan met vuur",
         "MR-SK-065"),
    ],
    # MR-SK-026 deed de eerste van de twee plaatsen in dit vers.
    (18, 27): [("als de loop van Ahimaäz", "als die van Ahimaäz", "MR-SK-026")],
    (19, 18): [("Als nu de pont overvoer,", "Als men nu de doorwaadbare plaats overstak,",
                "MR-2SA-002")],
    # Hoofdstuk 22 is dezelfde psalm als Psalm 18, die al is nagekeken. Waar de
    # Statenvertaling in beide gelijk is, volgt 2 Samuël de woordkeus van de psalm.
    (22, 5): [("beken Belials", "beken van Belial", "V448")],
    (22, 19): [("mijn ongeval;", "mijn ongeluk;", "V213"),
               ("een Steunsel.", "een Steun.", "MR-2SA-003")],
    (22, 21): [("de reinigheid van mijn handen", "de reinheid van mijn handen", "N7")],
    (22, 25): [("naar mijn reinigheid,", "naar mijn reinheid,", "MR-2SA-004")],
    (23, 7): [("verbrand worden op die plaats", "verbrand worden ter plekke", "MR-SK-101")],
}

# Nieuwe principes, begrensd tot de verzen waar ze beoordeeld zijn.
NIEUW = [
    {
        "id": "MR-2SA-001", "oud": "maliënkolder", "nieuw": "benauwdheid",
        "bereik": ["1:9"],
        "toelichting": "Het Hebreeuwse woord komt alleen hier voor. De Statenvertaling "
                       "denkt aan een pantser; de samenhang (Saul vraagt om de "
                       "genadeslag) wijst op de doodsstrijd zelf.",
    },
    {
        "id": "MR-2SA-002", "oud": "de pont overvoer", "nieuw": "men de doorwaadbare plaats overstak",
        "bereik": ["19:18"],
        "toelichting": "Het Hebreeuws spreekt van de overgang zelf; een veerboot wordt "
                       "niet genoemd. Keuze van de eigenaar van het project.",
    },
    {
        "id": "MR-2SA-003", "oud": "Steunsel", "nieuw": "Steun",
        "bereik": ["22:19"],
        "toelichting": "Gelijkgetrokken met Psalm 18:19, waar dezelfde zin al zo luidt.",
    },
    {
        "id": "MR-2SA-004", "oud": "reinigheid", "nieuw": "reinheid",
        "bereik": ["22:25"],
        "toelichting": "Gelijkgetrokken met Psalm 18:21 en 18:25; in 22:21 valt het "
                       "woord onder het naamvalprincipe van dezelfde woordgroep.",
    },
]

# De uitkomst van MR-SK-101 is op verzoek vervangen.
BIJGEWERKTE_PRINCIPES = {"MR-SK-101": {"nieuw": "ter plekke"}}

# --- 2. citaatopmaak --------------------------------------------------------

SPAN = '<span class="%s"><i>'
SLUIT = "</i></span>"
GEWOON = SPAN % "direct-speech"
GOD = SPAN % "god-speaks"

# De aankondiging stond binnen de span; zij hoort ervoor.
AANKONDIGING = {
    (1, 5): (GEWOON + "die hem de boodschap bracht: Hoe weet u,",
             "die hem de boodschap bracht: " + GEWOON + "Hoe weet u,"),
    (5, 8): ("Want David zei " + GEWOON + "op diezelfde dag: Al wie",
             "Want David zei op diezelfde dag: " + GEWOON + "Al wie"),
    (17, 14): ("Toen zei Absalom, " + GEWOON + "en alle man van Israël: De raad",
               "Toen zei Absalom, en alle man van Israël: " + GEWOON + "De raad"),
    (24, 16): ("en Hij zei tot de engel, " + GOD
               + "die het verderf onder het volk maakte: Het is genoeg",
               "en Hij zei tot de engel, die het verderf onder het volk maakte: "
               + GOD + "Het is genoeg"),
}

# Het verhalende staartje stond binnen de span; de span sluit ervoor.
INKORTEN = {
    (3, 16): [("keer weer. En hij keerde weer." + SLUIT,
               "keer weer." + SLUIT + " En hij keerde weer.")],
    (3, 31): [("voor Abner heen; en de koning David ging achter de baar." + SLUIT,
               "voor Abner heen;" + SLUIT + " en de koning David ging achter de baar.")],
    (3, 34): [("kinderen van de verkeerdheid. Toen huilde",
               "kinderen van de verkeerdheid." + SLUIT + " Toen huilde"),
              ("meer over hem." + SLUIT, "meer over hem.")],
    # "dat wil zeggen: David zal hier niet inkomen" is de uitleg van de verteller.
    (5, 6): [("zullen u afdrijven; dat wil zeggen: " + GEWOON
              + "David zal hier niet inkomen." + SLUIT + SLUIT,
              "zullen u afdrijven;" + SLUIT
              + " dat wil zeggen: David zal hier niet inkomen.")],
    (5, 8): [("tot een overste zijn; daarom zegt men: " + GEWOON,
              "tot een overste zijn;" + SLUIT + " daarom zegt men: " + GEWOON),
             ("niet komen." + SLUIT + SLUIT, "niet komen." + SLUIT)],
    (13, 16): [("dat u bij mij gedaan hebt; maar hij wilde naar haar niet horen." + SLUIT,
                "dat u bij mij gedaan hebt;" + SLUIT
                + " maar hij wilde naar haar niet horen.")],
    (14, 30): [("steek het aan met vuur, en Absaloms knechten staken die akker aan "
                "met vuur." + SLUIT,
                "steek het aan met vuur," + SLUIT
                + " en Absaloms knechten staken die akker aan met vuur.")],
    (15, 2): [("Uit welke stad bent u? Als hij dan zei: ",
               "Uit welke stad bent u?" + SLUIT + " Als hij dan zei: " + GEWOON)],
    (17, 14): [("is beter dan Achitofels raad. Maar JAHWEH had het geboden",
                "is beter dan Achitofels raad." + SLUIT + " Maar JAHWEH had het geboden"),
               ("het kwaad over Absalom bracht." + SLUIT,
                "het kwaad over Absalom bracht.")],
}

# Een vers dat de rede van het vorige vers voortzet, zonder eigen span.
OMHULLEN = {
    (2, 7): "direct-speech",
    (3, 9): "direct-speech",
    (3, 10): "direct-speech",
    (3, 29): "direct-speech",
    (3, 39): "direct-speech",
    (5, 23): "god-speaks",
    (11, 20): "direct-speech",
    (11, 21): "direct-speech",
    (12, 23): "direct-speech",
    (19, 12): "direct-speech",
    (19, 13): "direct-speech",
    (23, 6): "direct-speech",
    (23, 7): "direct-speech",
}

# Een wisseling van spreker binnen de span: de opener gaat voor het eerste
# anker, de sluiter achter het tweede.
NESTEN = {
    # Joab legt de bode de woorden van de koning in de mond.
    (11, 20): [("Waarom bent u zo na aan de stad", "van de muur zouden schieten?")],
    (11, 21): [("Wie sloeg Abimelech", "tot de muur genaderd?"),
               ("Uw knecht, Uria", "is ook dood.")],
    # Ziba citeert Mefiboseth.
    (16, 3): [("Vandaag zal mij het huis", "van mijn vader wedergeven.")],
    # David geeft de priesters de woorden voor Amasa mee, zoals in 19:11.
    (19, 13): [("Bent u niet mijn", "Joabs plaats.")],
}

# Twee uitspraken van dezelfde spreker stonden in elkaar; nu naast elkaar.
ONTNESTEN = {
    (3, 12): [("Van wie is het land? zeggende verder: ",
               "Van wie is het land?" + SLUIT + " zeggende verder: "),
              ("om te keren." + SLUIT + SLUIT, "om te keren." + SLUIT)],
}

# --- 3. tags ----------------------------------------------------------------

NIEUWE_TAGS = [
    {
        "id": "manipulatie",
        "naam": "Manipulatie",
        "beschrijving": "Mensen die met vleierij, halve waarheden en beloften het hart "
                        "van anderen naar zich toe trekken.",
        "kleur": "#8e44ad",
    },
    {
        "id": "vaderliefde",
        "naam": "Vaderliefde",
        "beschrijving": "De liefde van een vader voor zijn kind, ook als dat kind hem "
                        "kwaad heeft gedaan.",
        "kleur": "#c0392b",
    },
    {
        "id": "opdracht-tegen-geweten",
        "naam": "Een opdracht uitvoeren waar u niet achter staat",
        "beschrijving": "Wie in dienst van een ander staat en een bevel krijgt dat hij "
                        "onverstandig of verkeerd vindt.",
        "kleur": "#16a085",
    },
]

TAGS = [
    ("lhbtq", "2samuel 1:26", 2),
    ("verloren-bijbelse-bronnen", "2samuel 1:18", 1),
    ("liefde-man-vrouw", "2samuel 3:16", 2),
    ("ziekte-van-jahweh", "2samuel 12:15", 1),
    ("vervloekingen", "2samuel 21:1", 2),
    ("vervloekingen", "2samuel 21:3", 2),
    ("jezus-in-het-ot", "2samuel 23:3", 1),
    ("jezus-in-het-ot", "2samuel 23:4", 2),
    ("manipulatie", "2samuel 15:1", 2),
    ("manipulatie", "2samuel 15:2", 1),
    ("manipulatie", "2samuel 15:3", 1),
    ("manipulatie", "2samuel 15:4", 1),
    ("manipulatie", "2samuel 15:5", 2),
    ("manipulatie", "2samuel 15:6", 1),
    ("vaderliefde", "2samuel 18:33", 1),
    ("vaderliefde", "2samuel 19:4", 2),
    ("opdracht-tegen-geweten", "2samuel 24:3", 1),
    ("opdracht-tegen-geweten", "2samuel 24:4", 1),
]

# --- 4. reviewlijst ---------------------------------------------------------

VERWERKT = "verwerkt"
AFGEDEKT = "afgedekt"
GEPLAND = "gepland"
OPEN = "open"
VERVALLEN = "vervallen"

REEDS = "Stond al zo in de leestekst (review van augustus)."
DUBBEL = "Dubbele melding; zie de melding hierboven."
PRINCIPE = ("Vraagt om een principe voor alle boeken; wordt doorgevoerd in de boeken "
            "die nog niet definitief zijn.")

BESLUITEN = [
    ("1:1", "Wedergekomen - teruggekomen", "tekst_eenduidig", AFGEDEKT, REEDS),
    ("1:1", "Wedergekomen - teruggekeerd - principe! Overal", "principe", GEPLAND,
     PRINCIPE + " Wederkomen wordt terugkeren."),
    ("1:2", "Wiens - van wie de", "tekst_eenduidig", AFGEDEKT, REEDS),
    ("1:4", "Verhaal - Vertel", "tekst_eenduidig", AFGEDEKT, REEDS),
    ("1:5", "Citatie nakijken", "citatieopmaak", VERWERKT,
     "'die hem de boodschap bracht:' staat nu buiten het citaat."),
    ("1:6", "Bij geval - toevallig - principe!", "principe", GEPLAND,
     "In 1:6 al verwerkt. " + PRINCIPE),
    ("1:9", "Malienkolder - bnauwdheid", "tekst_eenduidig", VERWERKT,
     "Maliënkolder is benauwdheid geworden."),
    ("1:10", "Armgesmijde - armband", "tekst_eenduidig", VERWERKT,
     "'armband' stond er al; lidwoord en voornaamwoord kloppen nu: 'de armband, die'."),
    ("1:13", "Vreemde man - vreemdeling", "tekst_eenduidig", AFGEDEKT, REEDS),
    ("1:18", "Maak ook een overzicht van alle citaties naar buitenbijbelse bronnen",
     "tag_of_onderwerp", VERWERKT,
     "Het vers staat nu bij het onderwerp 'Niet-bewaarde geschriften die de Bijbel "
     "noemt'; die onderwerppagina is het overzicht."),
    ("1:26", "Tag lhbtq", "tag_of_onderwerp", VERWERKT, "Aan het onderwerp gekoppeld."),
    ("2:7", "Citatie", "citatieopmaak", VERWERKT,
     "Het vers zet Davids boodschap uit 2:5-6 voort en is nu als citaat gemarkeerd."),
    ("2:14", "Spelen - gevecht houden", "tekst_eenduidig", AFGEDEKT,
     "Staat als 'vechten' in de leestekst."),
    ("2:25", "Hoop- eerder al gezegt", "tekst_eenduidig", AFGEDEKT,
     "Staat als 'tot één groep' in de leestekst."),
    ("3:7", "Wier - van wie de", "tekst_eenduidig", AFGEDEKT, REEDS),
    ("3:9-10", "Citatie", "citatieopmaak", VERWERKT,
     "Abners eed loopt door uit 3:8 en is nu als citaat gemarkeerd."),
    ("3:12,17", "Seggendever is geencitatie", "citatieopmaak", VERWERKT,
     "In 3:12 staan nu twee citaten met 'zeggende verder' ertussen; 3:17 klopte al."),
    ("3:16", "Laatste deel geen citatie", "citatieopmaak", VERWERKT,
     "'En hij keerde weer' is nu vertelling."),
    ("3:16", "Tag liefde tussenman envrouw", "tag_of_onderwerp", VERWERKT,
     "Aan het onderwerp gekoppeld."),
    ("3:29", "Citatie", "citatieopmaak", VERWERKT,
     "Davids vervloeking loopt door uit 3:28 en is nu als citaat gemarkeerd."),
    ("3:29", "Maak moderner", "tekst_eenduidig", VERWERKT,
     "De aanvoegende wijs is weg: 'Laat het blijven op het hoofd van Joab ... laat er "
     "in het huis van Joab nooit iemand ontbreken die ...'."),
    ("3:31", "Laatste deel geen citayie", "citatieopmaak", VERWERKT,
     "'en de koning David ging achter de baar' is nu vertelling."),
    ("3:34", "Laatste deel geen citatie", "citatieopmaak", VERWERKT,
     "'Toen huilde het hele volk nog meer over hem' is nu vertelling."),
    ("3:39", "Citatie", "citatieopmaak", VERWERKT,
     "Davids woorden lopen door uit 3:38 en zijn nu als citaat gemarkeerd."),
    ("4:4", "Geslagen was aan beide voeten - verlamd was aan beide voeten",
     "tekst_eenduidig", AFGEDEKT, REEDS),
    ("4:6", "Als zullende - alsof ze", "tekst_eenduidig", VERWERKT,
     "'alsof zij' stond er al, maar de zin liep niet; nu 'alsof zij tarwe kwamen halen'."),
    ("4:7", "Hieuwen - hakten", "tekst_eenduidig", AFGEDEKT, REEDS),
    ("5:6", "Dat is te zeggen - dat wilmzeggen", "tekst_eenduidig", VERWERKT,
     "'dat wil zeggen' stond er al; de uitleg erachter is nu vertelling en geen "
     "tweede citaat meer."),
    ("5:8", "Citatie", "citatieopmaak", VERWERKT,
     "'op diezelfde dag' staat buiten het citaat, en 'daarom zegt men' is vertelling "
     "met een eigen citaat erachter."),
    ("5:23", "Citatie van God", "citatieopmaak", VERWERKT,
     "Als Godsspraak gemarkeerd, zoals het vervolg in 5:24."),
    ("6:1", "Uitgelezenen - beste mannen", "tekst_eenduidig", AFGEDEKT, REEDS),
    ("6:1", "Uitgelezenen - beste mannen", "tekst_eenduidig", AFGEDEKT, DUBBEL),
    ("6:8", "Scheur gescheurd - zware slag toegebracht", "tekst_eenduidig", AFGEDEKT,
     REEDS),
    ("6:20", "Daar geen getL!", "getalweergave", GEPLAND,
     "'één' wordt 'een' waar het geen telwoord is. Dat speelt in veel boeken en "
     "loopt mee in een eigen doorvoering."),
    ("6:21", "Mijninstellende - mij aangesteld heeft", "tekst_eenduidig", AFGEDEKT, REEDS),
    ("7:29", "Zo believe het u nu - zo moge het u nu behagen", "tekst_eenduidig",
     AFGEDEKT, REEDS),
    ("8:8", "Kopers - koper", "tekst_eenduidig", AFGEDEKT, REEDS),
    ("9:1", "Omwille van - vanwege", "tekst_eenduidig", AFGEDEKT, REEDS),
    ("10:1", "Kinderen van Ammon", "principe", GEPLAND,
     "'kinderen Ammons' staat vijftien keer in 2 Samuël en in meer boeken. " + PRINCIPE),
    ("10:5", "Gewassen - gegrieid", "tekst_eenduidig", AFGEDEKT, REEDS),
    ("10:8", "Bijzonder - afzonderlijk", "tekst_eenduidig", AFGEDEKT, REEDS),
    ("11:1", "Wederkomst van het jaar - aanbreken van het nieuwe jaar",
     "tekst_eenduidig", AFGEDEKT, REEDS),
    ("11:1", "Henenzond - heenzond", "tekst_eenduidig", AFGEDEKT, REEDS),
    ("11:1", "Verderven - zouden vernietigen", "tekst_eenduidig", AFGEDEKT, REEDS),
    ("11:2", "Zeer Schoon van aanzien- heel knap om te zien", "tekst_eenduidig",
     AFGEDEKT, REEDS),
    ("11:8", "Volgee - werd  Achterrna gebracht", "tekst_eenduidig", AFGEDEKT, REEDS),
    ("11:17", "Maak een pagina aan over welke volkeren in Israel actief waren - Uria "
     "was een Hethiet", "tag_of_onderwerp", AFGEDEKT,
     "De pagina Volken en naties bestaat; Uria's verzen staan bij de Hethieten."),
    ("11:20", "Citatie", "citatieopmaak", VERWERKT,
     "Joabs opdracht aan de bode loopt door uit 11:19, met de woorden van de koning "
     "als citaat daarbinnen."),
    ("11:20-21", "Citatie van Jiab", "citatieopmaak", VERWERKT,
     "Zie 11:20; in 11:21 is 'Dan zult u zeggen' weer Joab zelf."),
    ("12:1", "Getallen pas boven de 20 pas als cijferr", "getalweergave", AFGEDEKT,
     "De optie 'getallen in cijfers' doet dit al, vanaf 21. De 'één' in dit vers "
     "wordt 'een' in de doorvoering over 'één'."),
    ("12:4", "Overkwam - ontving", "tekst_eenduidig", AFGEDEKT, REEDS),
    ("12:4", "Verschoonde - negeerde", "tekst_eenduidig", AFGEDEKT,
     "Staat als 'zag hij ervan af'; 'negeerde' past niet in deze zin. Wel is 'de "
     "reizenden man' hersteld tot 'de reizende man'."),
    ("12:15", "Over dat God ziek maakt", "tag_of_onderwerp", VERWERKT,
     "Gekoppeld aan het onderwerp 'Wanneer JAHWEH ziekte zendt'."),
    ("12:23", "Citatie", "citatieopmaak", VERWERKT,
     "Davids antwoord loopt door uit 12:22 en is nu als citaat gemarkeerd."),
    ("12:23", "Citatie", "citatieopmaak", AFGEDEKT, DUBBEL),
    ("12:31", "Ticheloven - kleioven", "tekst_eenduidig", AFGEDEKT, REEDS),
    ("13:1", "Schone zus - knappe zus  Wier - van wie - voer dit overal door!",
     "principe", GEPLAND, "In 13:1 al verwerkt. " + PRINCIPE),
    ("13:16", "Oorzaken - redenen", "tekst_eenduidig", AFGEDEKT,
     REEDS + " Daarbij is 'maar hij wilde naar haar niet horen' uit het citaat gehaald."),
    ("14:2", "Droef - draagt", "tekst_eenduidig", AFGEDEKT,
     "Staat als 'alsof u rouw draagt' in de leestekst."),
    ("14:26", "Sikkel als gewicht toevoegen", "eenheden", AFGEDEKT,
     "De leesoptie voor maten rekent dit al om: 'tweehonderd sikkels (ongeveer 2,3 kilo)'."),
    ("14:27", "Wier vervangen start subagent", "principe", GEPLAND,
     "In 14:27 al verwerkt. " + PRINCIPE),
    ("14:30", "Akkers - akker", "tekst_eenduidig", VERWERKT,
     "De tweede plaats in dit vers is nu ook 'die akker'."),
    ("15:1-6", "Tag manipulatie", "tag_of_onderwerp", VERWERKT,
     "Nieuw onderwerp 'Manipulatie' met Absaloms werkwijze in 15:1-6."),
    ("15:2", "Alle man - iedereen", "tekst_eenduidig", AFGEDEKT, REEDS),
    ("15:2", "Citatie", "citatieopmaak", VERWERKT,
     "'Als hij dan zei:' staat nu buiten het citaat; het antwoord is een eigen citaat."),
    ("15:4", "Tot mij kwame - tot mij zou komen", "tekst_eenduidig", AFGEDEKT, REEDS),
    ("15:28", "Vertoe en - verblijven principe", "principe", GEPLAND,
     "In 15:28 al verwerkt. " + PRINCIPE),
    ("16:3", "Dubbele citatie", "citatieopmaak", VERWERKT,
     "Ziba citeert Mefiboseth; dat citaat staat nu binnen het zijne."),
    ("17:1", "Uitlezen - uitzoeken", "tekst_eenduidig", AFGEDEKT, REEDS),
    ("17:1", "Uitlezen - uitzoeken", "tekst_eenduidig", AFGEDEKT, DUBBEL),
    ("17:1", "Test", "test", VERVALLEN, "Controleregel van het formulier."),
    ("17:10", "Wiens overal vervangen met subagent door van wie en andere varaiten "
     "passend bij de zin", "principe", GEPLAND, "In 17:10 al verwerkt. " + PRINCIPE),
    ("17:14", "Citatie", "citatieopmaak", VERWERKT,
     "'en alle man van Israël:' staat buiten het citaat, en 'Maar JAHWEH had het "
     "geboden ...' is vertelling."),
    ("18:5", "Zachtkens - voorzichtig principe", "principe", GEPLAND,
     "In 18:5 al verwerkt. " + PRINCIPE),
    ("18:5", "Zachtkens - voorzichtig principe", "principe", AFGEDEKT, DUBBEL),
    ("18:22", "Bekwame - passende primcipe", "principe", GEPLAND,
     "In 18:22 al verwerkt. " + PRINCIPE),
    ("18:22", "Bekwame - passende", "tekst_eenduidig", AFGEDEKT, REEDS),
    ("18:27", "De loop- de manier van lopen", "tekst_eenduidig", VERWERKT,
     "De eerste plaats stond er al; de tweede is nu 'als die van Ahimaäz'."),
    ("18:33", "Tag vaderliefde", "tag_of_onderwerp", VERWERKT,
     "Nieuw onderwerp 'Vaderliefde', met 18:33 en 19:4."),
    ("19:3", "Steelsgewijze - sluipende", "tekst_eenduidig", AFGEDEKT, REEDS),
    ("19:12-13", "Citatie", "citatieopmaak", VERWERKT,
     "Davids boodschap loopt door uit 19:11; de woorden voor Amasa staan als citaat "
     "daarbinnen."),
    ("19:18", "Pont? Veer is doorwaadbare plaats", "tekst_eenduidig", VERWERKT,
     "Nu: 'Als men nu de doorwaadbare plaats overstak'."),
    ("19:41", "Mannen van David", "tekst_eenduidig", AFGEDEKT, REEDS),
    ("20:3", "Haarlieder - hun", "tekst_eenduidig", AFGEDEKT, REEDS),
    ("20:6", "Kwaads - kwaad", "tekst_eenduidig", AFGEDEKT, REEDS),
    ("21:1", "Vloek die nog voortduurt onder gelovigen", "tag_of_onderwerp", VERWERKT,
     "Gekoppeld aan het onderwerp Vervloekingen."),
    ("21:3", "Tag over de vloek - oplossing zodst zij het kunnen zegenen",
     "tag_of_onderwerp", VERWERKT, "Gekoppeld aan het onderwerp Vervloekingen."),
    ("21:12", "Burgeren - burgers?", "tekst_eenduidig", AFGEDEKT, REEDS),
    ("21:16", "Tag reuzen", "tag_of_onderwerp", AFGEDEKT, "Stond al bij het onderwerp."),
    ("21:18", "Tag reuzen", "tag_of_onderwerp", AFGEDEKT, "Stond al bij het onderwerp."),
    ("21:20", "Tag reuzen", "tag_of_onderwerp", AFGEDEKT, "Stond al bij het onderwerp."),
    ("22:3", "Bekijk de opmerkingen op psalm 18", "verwijzing", VERWERKT,
     "Bij Psalm 18 staan geen meldingen in de lijst. Wel is 2 Samuël 22 naast de al "
     "nagekeken Psalm 18 gelegd: waar de Statenvertaling gelijk is, volgt 2 Samuël "
     "nu dezelfde woordkeus: 'beken van Belial' (22:5), 'ongeluk' en 'Steun' (22:19), "
     "'reinheid' (22:21 en 22:25)."),
    ("23:1", "Als je in een bepaald hoofdstuk zif en je klikt weer op bjbelboek dan "
     "moet het boekmwaar je nzit oplichten en ook opklappen zods je alle hoodstukken "
     "ziet en je snel kunt wisselej naar een ander hoofdstuk", "functionaliteit",
     VERWERKT,
     "In de leesweergave toont de boekkeuze bij het geopende boek nu meteen alle "
     "hoofdstukken, met het huidige hoofdstuk gemarkeerd. De zijbalk van de "
     "hoofdweergave klapte het geopende boek al open."),
    ("23:3-4", "Tag profetie over Jezus in Ot", "tag_of_onderwerp", VERWERKT,
     "Gekoppeld aan het onderwerp 'Jezus in het Oude Testament'."),
    ("23:6-7", "Citatie", "citatieopmaak", VERWERKT,
     "Davids laatste woorden lopen door tot en met 23:7 en zijn nu als citaat "
     "gemarkeerd."),
    ("23:7", "Ter zelver plaats - stel iets beters voor", "tekst_eenduidig", VERWERKT,
     "Nu 'ter plekke'."),
    ("24:4", "Tag ambtenaren die opdrachten moeten vervullen waar ze nuet achternstaan",
     "tag_of_onderwerp", VERWERKT,
     "Nieuw onderwerp 'Een opdracht uitvoeren waar u niet achter staat', met Joab in "
     "24:3-4."),
    ("24:16", "Citatie jahweh nakijken", "citatieopmaak", VERWERKT,
     "'die het verderf onder het volk maakte:' staat nu buiten Gods woorden."),
    ("24:16", "Citatie JAHWEH nakijken", "citatieopmaak", AFGEDEKT, DUBBEL),
    ("24:24", "Eenheden toevoegen", "eenheden", AFGEDEKT,
     "De leesoptie voor maten rekent dit al om: 'vijftig zilveren sikkels (ongeveer "
     "570 gram zilver)'."),
]


# --- uitvoering -------------------------------------------------------------


def herkoppel(oude_diff, diff):
    """Hang een principe dat door hergroepering losraakte aan het nieuwe blok.

    Een woordpaar dat in een groter blok opgaat verliest zijn principe-id: de
    sleutel bestaat niet meer. Het blok dat het oude paar bevat is dezelfde
    wijziging, alleen ruimer opgeschreven, en erft dus dat id. Hetzelfde geldt
    voor een blok met precies dezelfde woorden uit 1888 waarvan alleen de
    uitkomst veranderde.
    """
    bezet = {(e["old"], e["new"]) for e in diff}
    for oud_paar in oude_diff:
        principe = oud_paar.get("principe")
        if not principe or (oud_paar["old"], oud_paar["new"]) in bezet:
            continue
        for blok in diff:
            if blok.get("principe") is not None:
                continue
            if (oud_paar["old"] == blok["old"] and oud_paar["old"]) or (
                    oud_paar["old"] in blok["old"] and oud_paar["new"] in blok["new"]):
                blok["principe"] = principe
                break
    return diff


def kern(oud, nieuw):
    """Het deel van de nieuwe tekst dat werkelijk verschilt van de oude."""
    a, b = oud.split(), nieuw.split()
    while a and b and a[0] == b[0]:
        a, b = a[1:], b[1:]
    while a and b and a[-1] == b[-1]:
        a, b = a[:-1], b[:-1]
    return " ".join(b)


def koppel(oude_diff, diff, correcties):
    """Geef de blokken die door deze correcties ontstaan hun principe."""
    oud = {(e["old"], e["new"]) for e in oude_diff}
    for blok in diff:
        if blok.get("principe") or (blok["old"], blok["new"]) in oud:
            continue
        woorden = blok["new"].strip(" ,.;:!?")
        for oud_tekst, nieuw_tekst, principe in correcties:
            if woorden and woorden in kern(oud_tekst, nieuw_tekst):
                blok["principe"] = principe
                break
    return diff


def pas_tekst_aan(vers, correcties, referentie):
    """Pas exacte vervangingen toe en behoud de zichtbare HTML-opmaak."""
    nieuw = vers["text2026"]
    for oud, vervang, _ in correcties:
        if vervang in nieuw:
            continue
        if oud not in nieuw:
            raise ValueError("%s: niet gevonden: %r" % (referentie, oud))
        nieuw = nieuw.replace(oud, vervang)
    if nieuw == vers["text2026"]:
        return False
    html = bijtrekken(vers["text2026_html"], nieuw)
    if html is None or kaal(html) != kaal(nieuw):
        raise ValueError("%s: HTML kon niet veilig worden bijgewerkt" % referentie)
    oude_diff = vers.get("phraseDiff", [])
    diff = nieuwe_diff(kaal(vers["textSV1888"]), kaal(nieuw), oude_diff, None,
                       referentie.lower())
    vers["text2026"] = nieuw
    vers["text2026_html"] = html
    vers["phraseDiff"] = koppel(oude_diff, herkoppel(oude_diff, diff), correcties)
    return True


def pas_opmaak_aan(vers, paren, referentie):
    """Vervangingen in uitsluitend de HTML; de leestekst blijft gelijk."""
    html = vers["text2026_html"]
    for zoek, vervang in paren:
        if zoek in html:
            html = html.replace(zoek, vervang, 1)
        elif vervang not in html:
            raise ValueError("%s: opmaak niet gevonden: %r" % (referentie, zoek))
    return zet_opmaak(vers, html, referentie)


def zet_opmaak(vers, html, referentie):
    if html == vers["text2026_html"]:
        return False
    if kaal(html) != kaal(vers["text2026"]):
        raise ValueError("%s: de opmaak dekt de leestekst niet meer" % referentie)
    if not gebalanceerd(html):
        raise ValueError("%s: de spans staan niet meer in balans" % referentie)
    vers["text2026_html"] = html
    return True


def omhul(vers, klasse, referentie):
    """Zet de hele verstekst in een span, achter eventuele nootmarkeringen."""
    html = vers["text2026_html"]
    if SPAN % klasse in html:
        return False
    if "<span" in html:
        raise ValueError("%s: er staat al een andere span in dit vers" % referentie)
    kop, rest = "", html
    while rest.startswith("<sup"):
        eind = rest.index("</sup>") + len("</sup>")
        kop, rest = kop + rest[:eind], rest[eind:]
    return zet_opmaak(vers, kop + (SPAN % klasse) + rest + SLUIT, referentie)


def nest_binnen(vers, ankers, referentie):
    """Zet een geneste span om een stuk tekst heen, tussen twee ankers in."""
    html = vers["text2026_html"]
    for begin, eind in ankers:
        if GEWOON + begin in html:
            continue
        if begin not in html:
            raise ValueError("%s: anker niet gevonden: %r" % (referentie, begin))
        i = html.index(begin)
        j = html.index(eind, i) + len(eind)
        html = html[:i] + GEWOON + html[i:j] + SLUIT + html[j:]
    return zet_opmaak(vers, html, referentie)


def registreer_principes():
    pad = ROOT / "data" / "wijzigingsprincipes.json"
    data, vorm = lees(str(pad))
    principes = [p for p in data["principes"] if not p["id"].startswith(PREFIX)]
    for nieuw in NIEUW:
        principes.append({
            "id": nieuw["id"],
            "categorie": "Menselijke review",
            "oud": nieuw["oud"],
            "nieuw": nieuw["nieuw"],
            "toelichting": nieuw["toelichting"] + " Beoordeeld in de review van 2 Samuël; "
                           "niet zonder herbeoordeling buiten dit bereik toepassen.",
            "regex": "",
            "voorbeeld": "%s %s" % (BOEK, nieuw["bereik"][0]),
            "bereik": {BOEK: list(nieuw["bereik"])},
            "bron": "menselijke-review",
        })
    bekend = {p["id"]: p for p in principes}
    for pid, velden in BIJGEWERKTE_PRINCIPES.items():
        bekend[pid].update(velden)
    for correcties in CORRECTIES.values():
        for _, _, pid in correcties:
            if pid not in bekend:
                raise ValueError("principe %s bestaat niet" % pid)
    data["principes"] = principes
    schrijf(str(pad), data, vorm)


def verwerk_verzen():
    per_hoofdstuk = {}
    for tabel in (CORRECTIES, AANKONDIGING, INKORTEN, OMHULLEN, NESTEN, ONTNESTEN):
        for hoofdstuk, nummer in tabel:
            per_hoofdstuk.setdefault(hoofdstuk, set()).add(nummer)
    geraakt = set()
    for hoofdstuk, nummers in sorted(per_hoofdstuk.items()):
        pad = ROOT / "data" / BOEK / ("%d.json" % hoofdstuk)
        data, vorm = lees(str(pad))
        verzen = {item["number"]: item for item in data["verses"]}
        gewijzigd = False
        for nummer in sorted(nummers):
            sleutel = (hoofdstuk, nummer)
            ref = "%s %d:%d" % (NAAM, hoofdstuk, nummer)
            vers = verzen[nummer]
            werk = False
            if sleutel in CORRECTIES:
                werk |= pas_tekst_aan(vers, CORRECTIES[sleutel], ref)
            if sleutel in AANKONDIGING:
                werk |= pas_opmaak_aan(vers, [AANKONDIGING[sleutel]], ref)
            if sleutel in OMHULLEN:
                werk |= omhul(vers, OMHULLEN[sleutel], ref)
            if sleutel in INKORTEN:
                werk |= pas_opmaak_aan(vers, INKORTEN[sleutel], ref)
            if sleutel in ONTNESTEN:
                werk |= pas_opmaak_aan(vers, ONTNESTEN[sleutel], ref)
            if sleutel in NESTEN:
                werk |= nest_binnen(vers, NESTEN[sleutel], ref)
            if werk:
                geraakt.add(sleutel)
                gewijzigd = True
        if gewijzigd:
            schrijf(str(pad), data, vorm)
    return len(geraakt)


def verwerk_tags():
    pad = ROOT / "data" / "tags.json"
    data, vorm = lees(str(pad))
    lijst = data["tags"]
    bestaand = {t["id"] for t in lijst}
    for nieuw in NIEUWE_TAGS:
        if nieuw["id"] not in bestaand:
            lijst.append(dict(nieuw, verzen=[]))
    kaart = {t["id"]: t for t in lijst}
    toegevoegd = 0
    for tag_id, ref, rang in TAGS:
        verzen = kaart[tag_id].setdefault("verzen", [])
        if ref in {v["ref"] for v in verzen}:
            continue
        verzen.append({"ref": ref, "rang": rang})
        toegevoegd += 1
    schrijf(str(pad), data, vorm)
    return toegevoegd


def schrijf_reviewlijst():
    pad = ROOT / "data" / ("google-opmerkingen-%s-reviewqueue.json" % BOEK)
    items = [
        {"ref": "%s %s" % (NAAM, ref), "suggestie": suggestie, "categorie": categorie,
         "status": status, "resultaat": resultaat}
        for ref, suggestie, categorie, status, resultaat in BESLUITEN
    ]
    data = {"source": "Google-opmerkingen, opgehaald 2026-09-14", "book": NAAM,
            "items": items}
    pad.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return len(items)


def main():
    registreer_principes()
    verzen = verwerk_verzen()
    tags = verwerk_tags()
    lijst = schrijf_reviewlijst()
    print("%d verzen in %s bijgewerkt; %d tagkoppelingen toegevoegd; %d opmerkingen "
          "in de reviewlijst." % (verzen, NAAM, tags, lijst))


if __name__ == "__main__":
    main()
