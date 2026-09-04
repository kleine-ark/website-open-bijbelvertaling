#!/usr/bin/env python3
"""Past voorgestelde citaatopmaak toe, en weigert alles wat niet klopt.

De citaatopmaak van een heel boek nalopen is leeswerk: de spreker is af te
leiden, maar waar een citaat ophoudt niet -- het Nederlands hervat de vertelling
net zo vaak met een komma als met een punt. Dat leeswerk wordt per hoofdstuk
gedaan en levert per vers een nieuwe `text2026_html` op. Dit script zet die
voorstellen weg.

Het is opzet dat het script niets zelf bedenkt. Het is de bewaking, en die is
streng, want een voorstel is tekst die ergens anders vandaan komt:

  * de kále tekst moet letter voor letter gelijk blijven -- alleen opmaak mag
    verschuiven, geen woord mag erbij of eraf;
  * de notenmarkeringen (`<sup class="note-marker">`) moeten er alle nog staan,
    in dezelfde volgorde en met dezelfde nummers;
  * `<span>` en `<i>` moeten in paren staan en netjes genest zijn;
  * alleen de vier bekende sprekersklassen zijn toegestaan;
  * verder mag er geen enkele andere tag in staan.

Wat er per bestand aan opmaak uitziet blijft zoals het was: inspringing van één
of twee spaties, CRLF of LF, en wel of geen slotregel. Dat lijkt een detail,
maar een bestand dat om die reden helemaal opnieuw geschreven wordt maakt de
diff onleesbaar en verbergt de echte wijziging.

Voorstelbestand:

    {"boek": "jeremia",
     "verzen": {"6:14": "<span class=\\"god-speaks\\">...</span>"}}

Gebruik:
    python scripts/citaat_toepassen.py voorstel.json --proef
    python scripts/citaat_toepassen.py voorstel.json
"""
import argparse
import collections
import glob
import io
import json
import os
import re
import sys

WORTEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KLASSEN = ("god-speaks", "direct-speech", "angel-speaks", "devil-speaks",
           "bride-speaks", "groom-speaks", "chorus-speaks")

SUP = re.compile(r'<sup[^>]*>.*?</sup>', re.S)
TAG = re.compile(r'<[^>]+>')
SPAN_OPEN = re.compile(r'<span class="([a-z-]+)">')


def kaal(html):
    """Alleen de leesbare tekst, zonder noten en zonder opmaak."""
    return re.sub(r'\s+', ' ', TAG.sub('', SUP.sub('', html))).strip()


def noten(html):
    """De notenmarkeringen op volgorde -- die mogen niet zoekraken."""
    return SUP.findall(html)


def gebalanceerd(html):
    """Staan span en i in paren, en netjes genest?"""
    stapel = []
    for m in re.finditer(r'</?(span|i)\b[^>]*>', html):
        naam = m.group(1)
        if m.group(0).startswith('</'):
            if not stapel or stapel.pop() != naam:
                return False
        else:
            stapel.append(naam)
    return not stapel


def alleen_bekende_tags(html):
    """Geen andere tags dan span, i en de notenmarkering."""
    for m in TAG.finditer(html):
        t = m.group(0)
        if re.fullmatch(r'</?(i|span)\b[^>]*>', t):
            continue
        if re.fullmatch(r'</?sup\b[^>]*>', t):
            continue
        return t
    return None


def keur(oud, nieuw):
    """Geeft de reden van afkeuring, of None als het voorstel deugt."""
    if kaal(oud) != kaal(nieuw):
        return "de tekst zelf is veranderd"
    if noten(oud) != noten(nieuw):
        return "de notenmarkeringen zijn niet meer dezelfde"
    if not gebalanceerd(nieuw):
        return "de opmaak is niet gebalanceerd"
    vreemd = alleen_bekende_tags(nieuw)
    if vreemd:
        return "onbekende tag %s" % vreemd
    for k in SPAN_OPEN.findall(nieuw):
        if k not in KLASSEN:
            return "onbekende sprekersklasse %s" % k
    # Een span zonder cursief eromheen valt uit de opmaak; dat is altijd een
    # vergissing en niet een keuze.
    if re.search(r'<span class="[a-z-]+">(?!<i>)', nieuw):
        return "span zonder <i> erbinnen"
    return None


def lees_ruw(pad):
    return io.open(pad, encoding="utf-8", newline="").read()


def schrijf(pad, data, ruw):
    """Terugschrijven in precies de vorm die het bestand had."""
    nl = "\r\n" if "\r\n" in ruw else "\n"
    m = re.search(r'\n( +)"', ruw.replace("\r\n", "\n"))
    tekst = json.dumps(data, ensure_ascii=False,
                       indent=len(m.group(1)) if m else 1)
    if ruw.endswith("\n"):
        tekst += "\n"
    io.open(pad, "w", encoding="utf-8", newline="").write(tekst.replace("\n", nl))


def main():
    p = argparse.ArgumentParser(description="Voorgestelde citaatopmaak toepassen.")
    p.add_argument("voorstel", nargs="+", help="een of meer voorstelbestanden")
    p.add_argument("--proef", action="store_true", help="alleen tonen, niets opslaan")
    p.add_argument("--toon", type=int, default=6, help="hoeveel voorbeelden tonen")
    p.add_argument("--wortel", help="andere map met data/ dan de repository zelf; "
                                    "voor werken op een uitgepakte kopie van origin/main")
    args = p.parse_args()

    global WORTEL
    if args.wortel:
        WORTEL = args.wortel

    paden = []
    for v in args.voorstel:
        paden.extend(sorted(glob.glob(v)) or [v])

    tot_ok = tot_af = tot_gelijk = 0
    afgekeurd = collections.Counter()
    for voorstelpad in paden:
        voorstel = json.load(open(voorstelpad, encoding="utf-8"))
        boek = voorstel["boek"]
        per_hoofdstuk = collections.defaultdict(dict)
        for ref, html in voorstel["verzen"].items():
            c, v = ref.split(":")
            per_hoofdstuk[int(c)][int(v)] = html

        for c in sorted(per_hoofdstuk):
            pad = os.path.join(WORTEL, "data", boek, "%d.json" % c)
            if not os.path.exists(pad):
                print("  ontbreekt: %s" % pad)
                continue
            ruw = lees_ruw(pad)
            data = json.loads(ruw)
            vers = {v["number"]: v for v in data["verses"]}
            raak = 0
            for n, html in sorted(per_hoofdstuk[c].items()):
                if n not in vers:
                    print("  %s %d:%d bestaat niet" % (boek, c, n))
                    tot_af += 1
                    continue
                oud = vers[n].get("text2026_html") or ""
                if oud == html:
                    tot_gelijk += 1
                    continue
                reden = keur(oud, html)
                if reden:
                    afgekeurd[reden] += 1
                    tot_af += 1
                    if tot_af <= args.toon:
                        print("  AFGEKEURD %s %d:%d — %s" % (boek, c, n, reden))
                        print("    was: %s" % oud[:150])
                        print("    nu : %s" % html[:150])
                    continue
                vers[n]["text2026_html"] = html
                raak += 1
                tot_ok += 1
            if raak and not args.proef:
                schrijf(pad, data, ruw)

    print("\n%d verzen bijgewerkt, %d ongewijzigd, %d afgekeurd%s"
          % (tot_ok, tot_gelijk, tot_af, "  (proef, niets opgeslagen)" if args.proef else ""))
    for reden, n in afgekeurd.most_common():
        print("  %4d  %s" % (n, reden))
    return 1 if tot_af else 0


if __name__ == "__main__":
    sys.exit(main())
