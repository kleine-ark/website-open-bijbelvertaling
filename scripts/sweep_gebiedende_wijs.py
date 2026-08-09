#!/usr/bin/env python3
"""Vervangt de oude gebiedende wijs op -t door de moderne vorm.

De Statenvertaling gebruikt voor het meervoud de vorm op -t: "Spreekt tot de
Israëlieten", "Neemt op de som", "Besnijdt u voor JAHWEH". Modern Nederlands
kent dat onderscheid niet meer; enkelvoud en meervoud zijn allebei de stam.

Waarom een tabel en geen patroon: zinsinitiale woorden op -t zijn in dit corpus
voor het overgrote deel geen werkwoord. "Want" komt 2448 keer voor, "Het" 851,
"Dit" 455, "Omdat" 222 — en dan is er nog de koning Josafat. Een regel als
"hoofdletter, eindigt op t, staat vooraan de zin" richt een ravage aan. Daarom
staat hier per werkwoord uitgeschreven wat het worden moet.

Twee soorten werkwoorden staan er met opzet NIET in:

* Werkwoorden waarvan de stam zelf op -t of -d eindigt. Zet, richt, wacht,
  acht, haat, laat, eet, vergeet, verlaat, meet, geniet, sluit, rust: die
  veranderen niet, want de oude en de nieuwe vorm zijn gelijk.
* Vormen die vooraan een zin meestal geen bevel zijn maar een vraag of een
  omkering: "Bent u...", "Zult u...", "Heeft hij...", "Kunt u...". Bij Hebt,
  Weet, Wordt en Zijt kán het allebei; daar kijkt het script naar het woord
  erna. Staat er een onderwerp (u, gij, hij, zij, men, ik, wij), dan is het
  geen bevel en blijft het staan.

Eerstelijnsregel: een vers komt alleen in aanmerking als de oude vorm ook in
textSV1888 staat. Zie CLAUDE.md.

Gebruik:
    python scripts/sweep_gebiedende_wijs.py --droog
    python scripts/sweep_gebiedende_wijs.py --id V1158
"""
import argparse
import collections
import glob
import json
import os
import re
import sys

WORTEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(WORTEL, "scripts"))
from sweep_principe import lees, schrijf, kaal, nieuwe_diff  # noqa: E402

# Oude meervoudsvorm -> moderne vorm. Alleen werkwoorden waar de vorm echt
# verandert; onregelmatige gevallen (gaan, staan, slaan, zien, doen, zijn)
# staan gewoon uitgeschreven.
WERKWOORDEN = {
    "Ziet": "Zie", "Hoort": "Hoor", "Gaat": "Ga", "Komt": "Kom",
    "Neemt": "Neem", "Doet": "Doe", "Geeft": "Geef", "Vreest": "Vrees",
    "Brengt": "Breng", "Maakt": "Maak", "Looft": "Loof", "Zegt": "Zeg",
    "Gedenkt": "Gedenk", "Staat": "Sta", "Trekt": "Trek",
    "Verzamelt": "Verzamel", "Spreekt": "Spreek", "Keert": "Keer",
    "Houdt": "Houd", "Roept": "Roep", "Bidt": "Bid", "Gelooft": "Geloof",
    "Waakt": "Waak", "Zoekt": "Zoek", "Bekeert": "Bekeer", "Denkt": "Denk",
    "Verkondigt": "Verkondig", "Zingt": "Zing", "Verblijdt": "Verblijd",
    "Heiligt": "Heilig", "Blijft": "Blijf", "Wijkt": "Wijk",
    "Aanschouwt": "Aanschouw", "Heft": "Hef", "Oordeelt": "Oordeel",
    "Vertrouwt": "Vertrouw", "Onderhoudt": "Onderhoud", "Werpt": "Werp",
    "Dankt": "Dank", "Weest": "Wees", "Zijt": "Wees", "Schaamt": "Schaam",
    "Verstaat": "Versta", "Merkt": "Merk", "Legt": "Leg", "Bereidt": "Bereid",
    "Vliedt": "Vlied", "Antwoordt": "Antwoord", "Nadert": "Nader",
    "Dwaalt": "Dwaal", "Vergeldt": "Vergeld", "Klimt": "Klim",
    "Zendt": "Zend", "Slaat": "Sla", "Zwijgt": "Zwijg", "Juicht": "Juich",
    "Verheft": "Verhef", "Kent": "Ken", "Grijpt": "Grijp", "Kiest": "Kies",
    "Vult": "Vul", "Leeft": "Leef", "Toont": "Toon", "Reinigt": "Reinig",
    "Onderzoekt": "Onderzoek", "Houwt": "Houw", "Wandelt": "Wandel",
    "Huilt": "Huil", "Doodt": "Dood", "Verontreinigt": "Verontreinig",
    "Draagt": "Draag", "Stelt": "Stel", "Opent": "Open", "Valt": "Val",
    "Blaast": "Blaas", "Leert": "Leer", "Vraagt": "Vraag", "Drinkt": "Drink",
    "Verhoogt": "Verhoog", "Breekt": "Breek", "Aanbidt": "Aanbid",
    "Volgt": "Volg", "Verwondert": "Verwonder", "Zadelt": "Zadel",
    "Haalt": "Haal", "Jaagt": "Jaag", "Zuivert": "Zuiver", "Tast": "Tas",
    "Eert": "Eer", "Omgordt": "Omgord", "Begeert": "Begeer",
    "Strijdt": "Strijd", "Offert": "Offer", "Beroemt": "Beroem",
    "Weidt": "Weid", "Vernedert": "Verneder", "Veracht": "Veracht",
    "Handelt": "Handel", "Verhardt": "Verhard", "Voert": "Voer",
    "Hoedt": "Hoed", "Ontbindt": "Ontbind", "Weent": "Ween",
    "Troost": "Troost", "Meet": "Meet", "Besnijdt": "Besnijd",
    "Behoudt": "Behoud", "Luistert": "Luister", "Schrijft": "Schrijf",
    "Leest": "Lees", "Ontvangt": "Ontvang", "Vertelt": "Vertel",
    "Bedekt": "Bedek", "Bouwt": "Bouw", "Ploegt": "Ploeg", "Werkt": "Werk",
    "Treedt": "Treed", "Zegent": "Zegen", "Slaapt": "Slaap",
    "Zweert": "Zweer", "Scheidt": "Scheid", "Verbergt": "Verberg",
    "Doorsnijdt": "Doorsnijd", "Erkent": "Erken", "Zorgt": "Zorg",
    "Loopt": "Loop", "Verstrooit": "Verstrooi", "Wendt": "Wend",
    "Blust": "Blus", "Beproeft": "Beproef", "Onthoudt": "Onthoud",
    "Stoot": "Stoot", "Vergeeft": "Vergeef", "Bewijst": "Bewijs",
    "Plant": "Plant", "Spaart": "Spaar", "Scheurt": "Scheur", "Redt": "Red",
    "Begraaft": "Begraaf", "Betuigt": "Betuig", "Neigt": "Neig",
    "Mengt": "Meng", "Rukt": "Ruk", "Leidt": "Leid", "Knielt": "Kniel",
    "Meldt": "Meld", "Zondert": "Zonder", "Betert": "Beter",
    "Beschouwt": "Beschouw", "Verheugt": "Verheug",
    "Ondersteunt": "Ondersteun", "Vangt": "Vang", "Zaait": "Zaai",
    "Gedraagt": "Gedraag", "Belijdt": "Belijd", "Spant": "Span",
    "Beklimt": "Beklim", "Sluit": "Sluit", "Verheerlijkt": "Verheerlijk",
    "Ontfermt": "Ontferm", "Verdraagt": "Verdraag", "Bindt": "Bind",
    "Vertrekt": "Vertrek", "Profeteert": "Profeteer", "Rooft": "Roof",
    "Straft": "Straf", "Psalmzingt": "Psalmzing", "Vloekt": "Vloek",
    "Volhardt": "Volhard", "Deelt": "Deel", "Wreekt": "Wreek",
    "Noemt": "Noem", "Vertoont": "Vertoon", "Wenkt": "Wenk",
    "Beveelt": "Beveel", "Bedenkt": "Bedenk", "Verkoopt": "Verkoop",
    "Eist": "Eis", "Bemerkt": "Bemerk", "Verbiedt": "Verbied",
    "Geneest": "Genees", "Bezorgt": "Bezorg", "Groet": "Groet",
}

# Waar de vorm niet verandert hoeft er niets te gebeuren.
WERKWOORDEN = {o: n for o, n in WERKWOORDEN.items() if o != n}

# Hier kan de vorm ook een vraag of omkering zijn: "Hebt u ...?"
TWIJFEL = {"Hebt": "Heb"}

# "Wordt" staat er met opzet niet bij. Naast het bevel ("Wordt boos, en zondigt
# niet", Efeze 4:26) is het ook de lijdende vorm in een vraag: "Wordt daarvan
# hout genomen, om een stuk werk te maken?" (Ezechiël 15:3). Daar staat geen
# onderwerp achter, dus geen toets vangt het verschil. Zeven plaatsen; met de
# hand te doen.

ONDERWERPEN = {"u", "gij", "hij", "zij", "men", "ik", "wij", "het", "ge"}

# "u" en "gij" tellen alleen als onderwerp binnen een vraag. Anders halen ze de
# wederkerende bevelen onderuit: "Besnijdt u voor JAHWEH", "Bekeert u" en
# "Wacht u" zijn geen vragen maar bevelen aan uzelf.
WEDERKEREND = {"u", "gij"}

# Een zinsgrens: begin van het vers, of na een sluitend leesteken. Na een
# puntkomma of dubbele punt gaat dit corpus vaak door met een kleine letter
# ("de tijd is vervuld; bekeert u"), dus beide schrijfwijzen moeten mee.
ZINSBEGIN = r"(?:(?<=^)|(?<=[.!?;:] ))"

# Vervolg van een opsomming: "Wees vruchtbaar, en vermenigvuldigt, en vervult".
# Alleen toegepast in verzen waar op een zinsgrens al een bevel is omgezet.
# Zonder die voorwaarde zou "als hij komt, ..." meegaan, en dat is geen bevel.
REEKS = r"(?:(?<=, )|(?<=, en )|(?<= en ))"


def verzen(d):
    v = d.get("verses")
    if isinstance(v, list):
        return [x for x in v if isinstance(x, dict)]
    if isinstance(v, dict):
        return [x for x in v.values() if isinstance(x, dict)]
    return []


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--id", default="V1158")
    p.add_argument("--droog", action="store_true")
    p.add_argument("--toon", type=int, default=25)
    a = p.parse_args()

    alle = dict(WERKWOORDEN)
    alle.update({k: v for k, v in TWIJFEL.items() if k != v})

    tel = collections.Counter()
    voorbeeld = {}
    twijfel_overgeslagen = collections.Counter()
    bestanden = 0
    verzen_geraakt = 0

    for pad in sorted(glob.glob(os.path.join(WORTEL, "data", "*", "*.json"))):
        boek = os.path.basename(os.path.dirname(pad))
        try:
            d, vorm = lees(pad)
        except Exception:
            continue
        if not isinstance(d, dict) or "verses" not in d:
            continue
        hs = d.get("number")
        gewijzigd = False

        for v in verzen(d):
            ov = v.get("text2026") or ""
            sv = v.get("textSV1888") or ""
            if not ov or not sv:
                continue
            nieuw_ov, nieuw_html = ov, v.get("text2026_html") or ""
            iets = False

            def is_vraag(tekst, treffer):
                """Loopt de zin waarin dit staat uit op een vraagteken?"""
                staart = tekst[treffer:]
                eind = re.search(r"[.!?]", staart)
                return bool(eind) and staart[eind.start()] == "?"

            def probeer(oud, modern, patroon, teller):
                nonlocal nieuw_ov, nieuw_html, iets
                m = re.search(patroon + r"\b" + oud + r"\b", nieuw_ov)
                if not m:
                    return False
                # eerstelijnstoets: stond de oude vorm ook in 1888?
                if not re.search(r"\b" + oud + r"\b", sv, re.I):
                    return False
                # Staat er een onderwerp achter, dan kan het een vraag zijn:
                # "Hebt U dan Juda verworpen?" Let op de hoofdletter, de U van
                # God, anders glipt die er doorheen. Maar "u" is ook het
                # wederkerend voornaamwoord, en "Besnijdt u voor JAHWEH" is wel
                # degelijk een bevel. Voor u en gij beslist daarom het
                # vraagteken; voor hij, zij en men is het nooit een bevel.
                volgend = re.match(r" ([A-Za-zÀ-ÿ]+)", nieuw_ov[m.end():])
                if volgend:
                    w = volgend.group(1).lower()
                    if w in ONDERWERPEN:
                        if w not in WEDERKEREND or is_vraag(nieuw_ov, m.start()):
                            teller[oud] += 1
                            return False
                # In de opmaak staat vóór het woord vaak nog een span of een
                # sup — <span class="god-speaks"><i>Ziet ... — en daar grijpt de
                # zinsgrens-toets niet. Zou je hetzelfde patroon op de opmaak
                # loslaten, dan mislukt de vervanging stil en gaan tekst en
                # opmaak uit elkaar lopen. Daarom in de opmaak op woordniveau
                # vervangen, en achteraf controleren of beide hetzelfde zeggen.
                # Welke voorkomen van dit woord is het, geteld vanaf het begin
                # van het vers? De opmaak bevat dezelfde woorden in dezelfde
                # volgorde, dus datzelfde nummer wijst daar hetzelfde woord aan.
                # Globaal vervangen zou fout gaan waar het woord twee keer
                # staat en maar een ervan een bevel is: "zeg tot hen ...,
                # zegt JAHWEH".
                woordpat = re.compile(r"\b" + oud + r"\b")
                nummer = len(woordpat.findall(nieuw_ov[:m.start()]))
                nieuw_ov = nieuw_ov[:m.start()] + modern + nieuw_ov[m.end():]
                teller_html = [-1]

                def eenmaal(mm):
                    teller_html[0] += 1
                    return modern if teller_html[0] == nummer else mm.group(0)

                nieuw_html = woordpat.sub(eenmaal, nieuw_html)
                tel[oud] += 1
                voorbeeld.setdefault(oud, f"{boek} {hs}:{v.get('number')}")
                iets = True
                return True

            # Eerst de zinsgrenzen, in beide schrijfwijzen.
            for _ in range(6):
                iets_deze_ronde = False
                for oud, modern in alle.items():
                    for vorm_oud, vorm_nieuw in ((oud, modern),
                                                 (oud.lower(), modern.lower())):
                        if probeer(vorm_oud, vorm_nieuw, ZINSBEGIN,
                                   twijfel_overgeslagen):
                            iets_deze_ronde = True
                if not iets_deze_ronde:
                    break

            # De opsomming binnen een vers -- "Wees vruchtbaar, en
            # vermenigvuldigt, en vervult" -- is met opzet NIET meegenomen.
            # Op die plaats staan door elkaar heen bevelen, tussenwerpsels en
            # gewone mededelingen: "en ziet zijn broeder gebrek hebben"
            # (1 Johannes 3:17) en "een kleine wolk gaat op van de zee"
            # (1 Koningen 18:44) zijn geen bevelen. Een regel ziet dat verschil
            # niet; een lezer wel. Zet REEKS_AAN op True om het toch te doen.
            REEKS_AAN = False
            if iets and REEKS_AAN:
                for _ in range(8):
                    iets_deze_ronde = False
                    for oud, modern in alle.items():
                        for vorm_oud, vorm_nieuw in ((oud.lower(), modern.lower()),
                                                     (oud, modern)):
                            if probeer(vorm_oud, vorm_nieuw, REEKS,
                                       twijfel_overgeslagen):
                                iets_deze_ronde = True
                    if not iets_deze_ronde:
                        break

            if iets:
                verzen_geraakt += 1
                if not a.droog:
                    v["text2026"] = nieuw_ov
                    v["text2026_html"] = nieuw_html
                    v["phraseDiff"] = nieuwe_diff(
                        kaal(sv), kaal(nieuw_ov), v.get("phraseDiff", []),
                        a.id, f"{boek}:{hs}:{v.get('number')}")
                    gewijzigd = True

        if gewijzigd:
            schrijf(pad, d, vorm)
            bestanden += 1

    print(f"{'ZOU WIJZIGEN' if a.droog else 'GEWIJZIGD'}: {verzen_geraakt} verzen, "
          f"{sum(tel.values())} vormen"
          + ("" if a.droog else f", {bestanden} bestanden"))
    print()
    for w, c in tel.most_common(a.toon):
        doel = alle.get(w) or alle.get(w.capitalize(), "?").lower()
        print(f"  {c:5}x  {w:16} -> {doel:16} ({voorbeeld[w]})")
    if len(tel) > a.toon:
        print(f"  ... en nog {len(tel) - a.toon} werkwoorden")
    if twijfel_overgeslagen:
        print()
        print("overgeslagen omdat er een onderwerp achter staat (geen bevel):")
        for w, c in twijfel_overgeslagen.most_common():
            print(f"  {c:5}x  {w}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
