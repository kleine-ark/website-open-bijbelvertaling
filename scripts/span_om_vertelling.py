#!/usr/bin/env python3
"""Zoekt spraak-spans die om vertelling heen staan in plaats van om een citaat.

Derde soort fout in de citaatopmaak, naast de aankondiging-binnen-de-span
(citaat_sweep.py) en de ontbrekende opmaak (citaat_ontbreekt.py): een heel vers
vertelling is in een span gezet, zodat de lezer cursief te zien krijgt wat
niemand uitspreekt.

    <span class="god-speaks"><i>JAHWEH sprak wel tot Manasse en tot zijn volk;
    maar zij merkten daar niet op.</i></span>

Drie soorten, elk met een eigen zekerheid:

  A  de span eindigt op een dubbele punt, meestal na "zeggende:". Dan staat er
     binnen de span geen enkel aangehaald woord -- alles is aankondiging. De
     span kan zonder oordeel weg; het citaat zelf staat in het volgende vers.

  B  binnen de span staat een aankondiging met een dubbele punt en daarachter
     nog echte tekst. Dan hoeft alleen de grens te verschuiven, net als in
     citaat_sweep.py, maar hier ook als het spreekwerkwoord een deelwoord is
     ("waarvan JAHWEH gezegd had:").

  C  de span omvat het hele vers, er staat geen dubbele punt in, en de inhoud
     vertelt over spreken in plaats van te spreken. Om te voorkomen dat een
     echt citaat wordt weggehaald geldt hier de extra eis dat er geen eerste-
     of tweedepersoonsvorm in staat: een spreker zegt vrijwel altijd ergens
     ik, mij, wij, u of uw. "Hij is de zoon van Josafat" -- een citaat in de
     derde persoon -- heeft geen vertellend spreekwerkwoord en valt dus af.

Het script wijzigt de kale tekst niet: na afloop wordt getoetst dat er geen
letter is veranderd en dat de opmaak gebalanceerd blijft.

Gebruik:
    python scripts/span_om_vertelling.py --proef
    python scripts/span_om_vertelling.py --boek 2kronieken
"""
import argparse
import glob
import os
import re
import sys

WORTEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(WORTEL, "scripts"))
from sweep_principe import lees, schrijf, kaal  # noqa: E402

SPREEK = (r"(?:zei|zeide|zeiden|sprak|spraken|riep|riepen|antwoordde|antwoordden|"
          r"gebood|geboden|vroeg|vraagde|gezegd|gesproken|geantwoord|bad|schreef|zeggende)")
# Een deelwoord alleen is niet genoeg om vertelling aan te tonen: "Zeg tot
# Rehabeam ... zeggende:" is zelf een uitgesproken opdracht, en de span hoort
# daar juist te staan. Vertelling herken je aan een persoonsvorm in de
# verleden tijd, met een onderwerp in de derde persoon ervoor.
VERTELD = re.compile(r"\b(?:zei|zeide|zeiden|sprak|spraken|riep|riepen|antwoordde|"
                     r"antwoordden|gebood|geboden|vroeg|vraagde|bad|schreef)\b")
PERSOON = re.compile(r"\b(?:ik|mij|mijn|mijne|me|wij|ons|onze|u|uw|uwe|gij|mijner|onzer)\b", re.I)
# Begint de inhoud met een gebiedende wijs, dan spreekt er iemand, ook al komt
# er geen ik of u in voor: "Spreek tot Aaron ... en zeg tot hen:" is JAHWEH die
# Mozes een opdracht geeft, niet de verteller die vertelt dat er gesproken werd.
GEBIEDEND = re.compile(r"^(?:Spreek|Zeg|Zegt|Ga|Gaat|Kom|Komt|Neem|Neemt|Hoor|Hoort|"
                       r"Zie|Ziet|Gebied|Gebiedt|Roep|Roept|Schrijf|Schrijft|Vraag|"
                       r"Vraagt|Doe|Doet|Maak|Maakt|Breng|Brengt|Antwoord|Antwoordt)\b")
# alles binnen een tag telt niet als tekst; een <sup> is een nootmarkering
NIET_TEKST = re.compile(r"<sup[^>]*>.*?</sup>|<[^>]+>", re.S)

VOLLEDIG = re.compile(
    r'^((?:<sup[^>]*>.*?</sup>|\s)*)'
    r'<span class="([a-z-]+)"><i>(.*?)</i></span>'
    r'((?:<sup[^>]*>.*?</sup>|\s)*)$', re.S)


def plat(html):
    return re.sub(r"\s+", " ", NIET_TEKST.sub("", html)).strip()


def soort(inhoud):
    """Geeft ('A'|'B'|'C', aankondiging, rest) terug, of None."""
    tekst = plat(inhoud)
    if not tekst or GEBIEDEND.match(tekst):
        return None
    # A: alles is aankondiging, er volgt geen aangehaald woord meer. Alleen als
    # er ook echt verteld wordt -- een persoonsvorm in de verleden tijd -- en
    # niemand binnen de span ik of u zegt.
    if tekst.endswith(":") and VERTELD.search(tekst) and not PERSOON.search(tekst):
        return ("A", inhoud, "")
    # B: aankondiging met dubbele punt, daarachter nog echte tekst. Staat er in
    # de aankondiging zelf een ik, mij of u, dan is het de spreker die iemand
    # aanhaalt -- "God heeft tot mij gezegd:" -- en hoort de aankondiging juist
    # binnen de span. Daar is een geneste span nodig, geen grensverlegging, en
    # dat is geen werk voor dit script.
    m = re.search(r"^((?:[^<:]|<sup[^>]*>.*?</sup>)*?\b" + SPREEK + r"\b(?:[^<:]|<sup[^>]*>.*?</sup>)*?:)"
                  r"\s*(.+)$", inhoud, re.S)
    if (m and len(kaal(m.group(2))) >= 10 and not m.group(2).lstrip().startswith("<span")
            and not PERSOON.search(plat(m.group(1)))):
        return ("B", m.group(1), m.group(2))
    # C: geen dubbele punt, en er wordt over spreken verteld in plaats van
    # gesproken. De persoonsvorm moet naar een toegesproken partij wijzen --
    # "sprak tot", "riepen tegen" -- want dat is de vorm van vertelling. Zonder
    # die eis glipt een citaat in de derde persoon erdoor: "Die JAHWEH voor hem
    # vraagde, en gaf hem proviant" is Doeg die vertelt over Achimelech, niet
    # de verteller die over Doeg vertelt.
    if (":" not in tekst and not PERSOON.search(tekst)
            and re.search(VERTELD.pattern + r"[^.;:]{0,45}?\b(?:tot|tegen)\b", tekst)):
        return ("C", inhoud, "")
    return None


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--proef", action="store_true")
    p.add_argument("--boek")
    p.add_argument("--soorten", default="ABC", help="welke soorten toepassen")
    p.add_argument("--toon", type=int, default=10)
    a = p.parse_args()

    tel = {"A": 0, "B": 0, "C": 0}
    per = {}
    getoond = 0
    mislukt = []

    for pad in sorted(glob.glob(os.path.join(WORTEL, "data", "*", "*.json"))):
        boek = os.path.basename(os.path.dirname(pad))
        if a.boek and boek != a.boek:
            continue
        try:
            d, vorm = lees(pad)
        except Exception:
            continue
        if not isinstance(d, dict) or "verses" not in d:
            continue
        gewijzigd = False
        VORIG = {}
        for v in d["verses"]:
            if not isinstance(v, dict):
                continue
            html = v.get("text2026_html") or ""
            hier = VOLLEDIG.match(html)
            straks = {"klasse": hier.group(2), "heel_vers": True} if hier else {}
            m = VOLLEDIG.match(html)
            if not m:
                VORIG = {}
                continue
            kop, klasse, inhoud, staart = m.groups()
            # Staat er vóór dit vers al een heel vers in een span van dezelfde
            # klasse, dan loopt er een rede door en is de vertelling hierbinnen
            # vertelling binnen die rede. Zo vertelt Jezus in Lukas 19 een
            # gelijkenis: "En het gebeurde, toen hij wederkwam..." is vertelling,
            # maar wel vertelling die Hij uitspreekt, en de span hoort te staan.
            # In Markus 11:6 begint het vorige vers juist met vertelling buiten
            # de span, en dan is de rede afgelopen.
            if VORIG.get("klasse") == klasse and VORIG.get("heel_vers"):
                VORIG = straks
                continue
            uitslag = soort(inhoud)
            if not uitslag:
                VORIG = straks
                continue
            s, aankondiging, rest = uitslag
            if s not in a.soorten:
                VORIG = straks
                continue
            if s in ("A", "C"):
                nieuw = kop + inhoud + staart
            else:
                nieuw = f'{kop}{aankondiging} <span class="{klasse}"><i>{rest}</i></span>{staart}'
            merk = f"{boek} {d.get('number')}:{v.get('number')}"
            if kaal(nieuw) != kaal(html):
                mislukt.append(merk + " (tekst zou veranderen)")
                VORIG = straks
                continue
            if nieuw.count("<span") != nieuw.count("</span>") or nieuw.count("<i>") != nieuw.count("</i>"):
                mislukt.append(merk + " (ongebalanceerd)")
                VORIG = straks
                continue
            tel[s] += 1
            per[boek] = per.get(boek, 0) + 1
            if getoond < a.toon:
                getoond += 1
                print(f"[{s}] {merk}\n   {plat(html)[:150]}")
            if not a.proef:
                v["text2026_html"] = re.sub(r"  +", " ", nieuw)
                gewijzigd = True
            VORIG = {}      # deze span is net weggehaald of verlegd
        if gewijzigd and not a.proef:
            schrijf(pad, d, vorm)

    print()
    print(f"{'ZOU HERSTELLEN' if a.proef else 'HERSTELD'}: "
          f"A={tel['A']} (span helemaal weg, alles was aankondiging), "
          f"B={tel['B']} (grens verlegd), C={tel['C']} (span om vertelling weg)")
    print(f"in {len(per)} boeken: " + ", ".join(f"{b} {n}" for b, n in sorted(per.items(), key=lambda x: -x[1])[:12]))
    if mislukt:
        print(f"overgeslagen: {len(mislukt)}")
        for x in mislukt[:10]:
            print("  " + x)
    return 0


if __name__ == "__main__":
    sys.exit(main())
