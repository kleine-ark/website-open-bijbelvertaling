#!/usr/bin/env python3
"""Voer de principes uit de lezersmeldingen door in de boeken die nog niet
definitief zijn.

Bij 2 Samuël vroegen meldingen om een principe "overal": wiens en wier,
wedergekomen als teruggekeerd, bij geval, vertoeven, bekwame. Twee meldingen
wezen erop dat "één" als telwoord werd gelezen waar het dat niet is. En
"kinderen Ammons" is een tweede naamval die elders al "kinderen van" werd.

Afspraak van de eigenaar: de definitieve boeken blijven zoals ze zijn. Het
script weigert daarom elk boek dat in data/verified-chapters.json op "all"
staat. Daardoor staat in de definitieve boeken op een paar plaatsen nog de
oude vorm (Ruth 2:3 en Lukas 10:31 "bij geval", Exodus 15:13 "zachtkens").

Elke vervanging is per vers uitgeschreven, omdat de zin bepaalt wat past:
"wiens naam was Jethra" wordt "van wie de naam Jethra was", maar "aan wiens
middel de inktkoker was" wordt "die de inktkoker aan zijn middel had".

Draaien vanuit de repo-root:  python scripts/apply_opmerkingen_principes_open_boeken.py
"""

from __future__ import annotations

import io
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from review_hulp import registreer_principes, verwerk_correcties  # noqa: E402
from sweep_principe import lees, schrijf  # noqa: E402

NAMEN = {
    "2samuel": "2 Samuël", "3ezra": "3 Ezra", "4ezra": "4 Ezra", "tobit": "Tobit",
    "judith": "Judith", "boekderwijsheid": "Wijsheid", "jezussirach": "Jezus Sirach",
    "estherapocrief": "Esther (apocrief)", "2makkabeeen": "2 Makkabeeën",
    "3makkabeeen": "3 Makkabeeën", "ezechiel": "Ezechiël", "henoch": "Henoch",
    "jubileeen": "Jubileeën", "1meqabyan": "1 Meqabyan", "2meqabyan": "2 Meqabyan",
    "4baruch": "4 Baruch",
}

# --- wiens en wier ----------------------------------------------------------

WIENS = {
    "2samuel": {
        (12, 24): [("en zij baarde een zoon, wiens naam zij noemde Salomo",
                    "en zij baarde een zoon, die zij Salomo noemde", "V312")],
        (16, 8): [("in wiens plaats u geregeerd hebt", "in plaats van wie u geregeerd hebt", "V312")],
        (17, 25): [("wiens naam was Jethra", "van wie de naam Jethra was", "N18")],
        (20, 21): [("wiens naam is Seba", "van wie de naam Seba is", "N18")],
        (21, 19): [("wiens spiesenhout was als een weversboom",
                    "van wie de speerschacht was als een weversboom", "V312")],
    },
    "3ezra": {
        (3, 5): [("en wiens woord wijzer zal schijnen", "en van wie het woord wijzer zal schijnen", "V312")],
        (6, 33): [("wiens naam daar aangeroepen wordt", "van wie de naam daar aangeroepen wordt", "N18")],
    },
    "4ezra": {
        (1, 37): [("wiens kleine kinderen zich", "van wie de kleine kinderen zich", "V312")],
        (2, 18): [("naar wier raad Ik voor u geheiligd en bereid heb",
                   "op hun raad heb Ik voor u geheiligd en bereid", "V1543")],
        (4, 1): [("wiens naam is Uriël", "van wie de naam Uriël is", "N18")],
        (8, 20): [("wiens ogen in de hoogte verheven zijn", "van wie de ogen in de hoogte verheven zijn", "V312")],
        (8, 21): [("Wiens troon onmetelijk, en wiens heerlijkheid onbegrijpelijk is",
                   "Van wie de troon onmetelijk, en van wie de heerlijkheid onbegrijpelijk is", "V312")],
        (8, 22): [("wiens woord waarachtig, en wiens redenen standvastig zijn",
                   "van wie het woord waarachtig, en van wie de redenen standvastig zijn", "V312")],
        (8, 23): [("Wiens bevel sterk, en wiens ordening verschrikkelijk is; wiens aanschouwen de "
                   "afgronden uitdroogt; en wiens toorn",
                   "Van wie het bevel sterk, en van wie de ordening verschrikkelijk is; van wie het "
                   "aanschouwen de afgronden uitdroogt; en van wie de toorn", "V312")],
    },
    "boekderwijsheid": {
        (12, 21): [("met wier vaders u", "met de vaders van wie u", "V1543")],
    },
    "jezussirach": {
        (34, 26): [("wiens stem zal Heere verhoren?", "van wie zal de Heere de stem verhoren?", "V312")],
        (45, 1): [("wiens herinnering is in zegening", "van wie de herinnering is in zegening", "V312")],
        (49, 15): [("wiens herinnering vele keren wordt verhaald",
                    "van wie de herinnering vele keren wordt verhaald", "V312")],
    },
    "ezechiel": {
        (9, 11): [("aan wiens middel de inktkoker was", "die de inktkoker aan zijn middel had", "V312")],
        (17, 16): [("wiens eed hij veracht, en wiens verbond hij gebroken heeft",
                    "van wie hij de eed veracht, en van wie hij het verbond gebroken heeft", "V312")],
        (20, 9): [("in wier midden zij waren", "te midden van wie zij waren", "V1543")],
        (20, 14): [("voor wier ogen Ik hen uitvoerde", "voor de ogen van wie Ik hen uitvoerde", "V1543")],
        (20, 22): [("voor wier ogen Ik hen uitgevoerd had", "voor de ogen van wie Ik hen uitgevoerd had", "V1543")],
        (21, 25): [("wiens dag komen zal", "van wie de dag komen zal", "V312")],
        (40, 3): [("een man, wiens gedaante was als", "een man, van wie de gedaante was als", "V312")],
    },
    "henoch": {
        (1, 2): [("wiens ogen door God geopend waren", "van wie de ogen door God geopend waren", "V312")],
        (16, 1): [("uit de zielen van wier vlees de geesten zijn uitgegaan",
                   "uit de zielen van wie de geesten uit het vlees zijn uitgegaan", "V1543")],
        (22, 6): [("wiens stem zo omhoog reikt", "van wie de stem zo omhoog reikt", "V312")],
        (46, 1): [("een ander, wiens aangezicht was als", "een ander, van wie het aangezicht was als", "V312")],
        (68, 3): [("wiens hart niet verzacht wordt daarover, en wiens nieren",
                   "van wie het hart niet verzacht wordt daarover, en van wie de nieren", "V312")],
        (76, 5): [("wiens naam is de oostenwind", "die de oostenwind heet", "N18")],
        (76, 10): [('wiens naam "zee" is', 'waarvan de naam "zee" is', "N18")],
        (77, 3): [("wiens naam het noorden is", "die het noorden heet", "N18")],
        (82, 15): [("wiens naam Tem'ani en de zon genoemd wordt", "die Tem'ani en de zon genoemd wordt", "N18")],
        (82, 17): [("wiens naam Heloyaseph is", "van wie de naam Heloyaseph is", "N18")],
        (82, 18): [("wiens naam men de blinkende zon noemt", "die men de blinkende zon noemt", "N18")],
        (89, 44): [("dat schaap wiens ogen geopend waren", "dat schaap waarvan de ogen geopend waren", "V312")],
        (106, 10): [("wiens gelijke er niet is, en wiens aard niet is als",
                     "die zijn gelijke niet heeft, en van wie de aard niet is als", "V312")],
    },
    "1meqabyan": {
        (1, 1): [("een man wiens naam Tsiruts'aidan was", "een man van wie de naam Tsiruts'aidan was", "N18")],
        (2, 1): [("wiens naam Meqabyos was", "van wie de naam Meqabyos was", "N18")],
        (17, 1): [("in Wiens hand het oordeel van hemel en aarde is",
                   "Die het oordeel van hemel en aarde in Zijn hand heeft", "V312")],
    },
    "2meqabyan": {
        (5, 12): [("een afgod wiens naam Baäl-Peor is", "een afgod die Baäl-Peor heet", "N18")],
        (12, 13): [("wiens naam Telmyakos is", "die Telmyakos heet", "N18")],
    },
    "4baruch": {
        (9, 7): [("als een mens wiens ziel van hem geweken was", "als een mens van wie de ziel geweken was", "V312")],
    },
}

# --- wederkomen, bij geval, vertoeven, bekwaam ------------------------------

TERUGKEREN = {
    "2samuel": {
        (1, 1): [("was teruggekomen", "was teruggekeerd", "MR-SK-137")],
        (12, 23): [("hij zal tot mij niet terugkomen", "hij zal tot mij niet terugkeren", "MR-OPM-001")],
    },
    "tobit": {(6, 20): [("niet terugkomen", "niet terugkeren", "MR-OPM-001")]},
    "2makkabeeen": {(6, 17): [("terugkomen tot ons verhaal", "terugkeren tot ons verhaal", "MR-OPM-001")]},
    "ezechiel": {(20, 38): [("niet terugkomen", "niet terugkeren", "MR-OPM-001")]},
    "jubileeen": {(42, 12): [("was teruggekomen", "was teruggekeerd", "MR-OPM-001")]},
}

OVERIG = {
    "2samuel": {(20, 1): [("daar bij geval een Belials man", "daar toevallig een Belials man", "MR-OPM-002")]},
    "boekderwijsheid": {
        (2, 2): [("Want bij geval zijn wij geboren", "Want toevallig zijn wij geboren", "MR-OPM-002")],
        (16, 20): [("en allerlei bekwame smaak", "en geschikt voor elke smaak", "MR-OPM-003")],
    },
    "4baruch": {(3, 1): [("zij vertoefden daar, wachtende", "zij bleven daar, wachtende", "V385")]},
    "jezussirach": {
        (18, 22): [("ter bekwamer tijd", "op de juiste tijd", "MR-OPM-003")],
        (20, 20): [("op de bekwame tijd", "op de juiste tijd", "MR-OPM-003")],
    },
    "estherapocrief": {(14, 13): [("Geef mij bekwame rede in mijn mond", "Geef mij passende woorden in mijn mond",
                                   "MR-OPM-003")]},
    "2makkabeeen": {
        (13, 26): [("verantwoordde dat bekwaam", "verantwoordde dat op gepaste wijze", "MR-OPM-004")],
        (14, 22): [("in bekwame plaatsen", "op geschikte plaatsen", "MR-OPM-003")],
        (15, 40): [("een bekwame beschrijving", "een goed geschreven beschrijving", "MR-OPM-003")],
    },
}

# --- één waar het geen telwoord is -------------------------------------------

# Hier is "één" wel een telwoord of heeft het nadruk: "niet één van hen",
# "één van deze, en één van de andere zijde", "maar één van duizenden".
EEN_BLIJFT = {
    ("2samuel", 13, 30), ("2samuel", 14, 11), ("4ezra", 5, 40), ("4ezra", 11, 6),
    ("4ezra", 12, 26), ("tobit", 3, 10), ("judith", 2, 6), ("jezussirach", 6, 6),
    ("jezussirach", 17, 12), ("2makkabeeen", 3, 26), ("ezechiel", 26, 11), ("ezechiel", 40, 26),
    ("ezechiel", 40, 49), ("henoch", 18, 7), ("henoch", 85, 3), ("henoch", 89, 9),
    ("jubileeen", 5, 11), ("1meqabyan", 4, 22),
}

GENITIEVEN = [
    ("kinderen Ammons", "kinderen van Ammon"),
    ("kinderen Moabs", "kinderen van Moab"),
    ("kinderen Ezau's", "kinderen van Ezau"),
    ("Verlosser Israëls", "Verlosser van Israël"),
]


def open_boeken():
    verified = json.loads((ROOT / "data" / "verified-chapters.json").read_text(encoding="utf-8"))
    return {boek for boek in NAMEN if verified.get(boek) != "all"}


def verzen(boek):
    for pad in sorted((ROOT / "data" / boek).glob("*.json"), key=lambda p: int(p.stem)):
        for vers in json.loads(io.open(pad, encoding="utf-8").read())["verses"]:
            yield int(pad.stem), vers


def patroon_correcties(boek):
    """'één van' en de tweede naamval bij namen, vers voor vers opgezocht."""
    uit = {}
    for hoofdstuk, vers in verzen(boek):
        tekst, bron = vers["text2026"], vers.get("textSV1888") or ""
        paren = []
        if (boek, hoofdstuk, vers["number"]) not in EEN_BLIJFT:
            for oud, nieuw in (("één van", "een van"), ("Één van", "Een van")):
                if oud in tekst:
                    paren.append((oud, nieuw, "V735"))
        for oud, nieuw in GENITIEVEN:
            # Eerste linie: alleen waar 1888 dezelfde naamval heeft.
            if oud in tekst and oud.split()[1] in bron:
                paren.append((oud, nieuw, "V448"))
        if paren:
            uit[(hoofdstuk, vers["number"])] = paren
    return uit


NIEUWE_PRINCIPES = [
    {
        "id": "MR-OPM-001", "categorie": "Menselijke review",
        "oud": "wederkomen", "nieuw": "terugkeren",
        "toelichting": "Op verzoek 'terugkeren' in plaats van 'terugkomen' (V769), in de "
                       "boeken die nog niet definitief waren.",
        "regex": "", "bron": "menselijke-review",
    },
    {
        "id": "MR-OPM-002", "categorie": "Menselijke review",
        "oud": "bij geval", "nieuw": "toevallig",
        "toelichting": "Zoals MR-SK-015 in 2 Samuël 1:6, in de boeken die nog niet "
                       "definitief waren.",
        "regex": "", "bron": "menselijke-review",
    },
    {
        "id": "MR-OPM-003", "categorie": "Menselijke review",
        "oud": "bekwaam (in de zin van passend of geschikt)", "nieuw": "passend / geschikt / juist",
        "toelichting": "Zoals MR-SK-012 in 2 Samuël 18:22. Waar 'bekwaam' 'in staat' "
                       "betekent (4 Ezra 4:44, Jezus Sirach 50:29), blijft het staan.",
        "regex": "", "bron": "menselijke-review",
    },
    {
        "id": "MR-OPM-004", "categorie": "Menselijke review",
        "oud": "bekwamelijk", "nieuw": "op gepaste wijze",
        "toelichting": "V155 maakte hier 'bekwaam' van, wat als bijwoord 'kundig' zou "
                       "betekenen; Lysias verantwoordde de zaak op gepaste wijze.",
        "regex": "", "bron": "menselijke-review",
    },
]


def werk_eerdere_review_bij():
    """MR-SK-137 en de augustusreview van 2 Samuël volgen 'teruggekeerd'."""
    pad = ROOT / "scripts" / "apply_review_2samuel_20260813.py"
    with io.open(pad, encoding="utf-8", newline="") as bestand:
        tekst = bestand.read()
    oud = '(1, 1): [("wedergekomen", "teruggekomen")]'
    if oud in tekst:
        with io.open(pad, "w", encoding="utf-8", newline="") as bestand:
            bestand.write(tekst.replace(oud, '(1, 1): [("wedergekomen", "teruggekeerd")]'))


def werk_v735_bij(principes):
    toevoeging = (" Niet bij 'een van' zonder nadruk: daar is 'een' geen telwoord "
                  "('een van de jongens').")
    v735 = next(p for p in principes if p["id"] == "V735")
    if toevoeging not in (v735.get("toelichting") or ""):
        v735["toelichting"] = (v735.get("toelichting") or "") + toevoeging


def main():
    open_ = open_boeken()
    alle = {}
    for tabel in (WIENS, TERUGKEREN, OVERIG):
        for boek, correcties in tabel.items():
            if boek not in open_:
                raise ValueError("%s staat op definitief" % boek)
            for sleutel, paren in correcties.items():
                alle.setdefault(boek, {}).setdefault(sleutel, []).extend(paren)
    for boek in sorted(open_):
        for sleutel, paren in patroon_correcties(boek).items():
            alle.setdefault(boek, {}).setdefault(sleutel, []).extend(paren)

    bereik = {}
    for boek, correcties in alle.items():
        for (hoofdstuk, nummer), paren in correcties.items():
            for _, _, pid in paren:
                if pid.startswith("MR-OPM-"):
                    bereik.setdefault(pid, {}).setdefault(boek, []).append("%d:%d" % (hoofdstuk, nummer))
    nieuwe = []
    for principe in NIEUWE_PRINCIPES:
        plaatsen = {b: sorted(set(r), key=lambda x: tuple(map(int, x.split(":"))))
                    for b, r in sorted(bereik.get(principe["id"], {}).items())}
        eerste = next(iter(plaatsen.items()))
        nieuwe.append(dict(principe, bereik=plaatsen, voorbeeld="%s %s" % (eerste[0], eerste[1][0])))
    gebruikt = {pid for c in alle.values() for paren in c.values() for _, _, pid in paren}
    registreer_principes("MR-OPM-", nieuwe, bijgewerkt={"MR-SK-137": {"nieuw": "teruggekeerd"}},
                         gebruikt=gebruikt)
    pad = ROOT / "data" / "wijzigingsprincipes.json"
    data, vorm = lees(str(pad))
    werk_v735_bij(data["principes"])
    schrijf(str(pad), data, vorm)
    werk_eerdere_review_bij()

    totaal = 0
    for boek in sorted(alle):
        totaal += verwerk_correcties(boek, NAMEN[boek], alle[boek])

    resten = []
    for boek in sorted(open_):
        for hoofdstuk, vers in verzen(boek):
            t = vers["text2026"]
            for m in re.finditer(r"\b[Ww]iens\b|\b[Ww]ier\b|\b[Bb]ij geval\b|kinderen Ammons|[Éé]én van", t):
                if m.group(0).lower() == "één van" and (boek, hoofdstuk, vers["number"]) in EEN_BLIJFT:
                    continue
                resten.append("%s %d:%d %s" % (boek, hoofdstuk, vers["number"], m.group(0)))
    if resten:
        raise ValueError("nog over: %s" % resten)
    print("%d verzen bijgewerkt in %d boeken." % (totaal, len(alle)))


if __name__ == "__main__":
    main()
