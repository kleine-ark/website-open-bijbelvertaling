#!/usr/bin/env python3
"""Somt de citaten op die helemaal geen opmaak hebben.

Dit script wijzigt niets. Het maakt de werklijst.

Tweede soort fout in de citaatopmaak: er staat een aankondiging met een dubbele
punt, en de woorden erachter zijn nergens als rede gemarkeerd.

    Maar Farao zei: Wie is JAHWEH, wiens stem ik gehoorzamen zou?

Waaróm dit niet automatisch gaat, terwijl het verleggen van een grens dat wel
kan (zie citaat_sweep.py): de spreker is nog wel af te leiden, maar het einde
van het citaat niet. Het Nederlands hervat de vertelling net zo vaak met een
puntkomma als met een punt, en dan is aan de vorm niets te zien:

    2 Koningen 2:15   "De geest van Elia rust op Elisa; en zij kwamen hem
                       tegemoet, en bogen zich voor hem neer ter aarde."
    1 Koningen 22:32  "Zeker, die is de koning van Israël, en zij keerden zich
                       naar hem, om te strijden; maar Josafat riep uit."

Alles achter de dubbele punt omhullen zou hier vertelling het citaat in
trekken — precies de fout die dit opruimwerk moet wegnemen. Een proef op 207
verzen liet zien dat dat ongeveer een derde van de gevallen treft. Vandaar deze
opsomming, met een voorstel voor de spreker erbij, om met de hand na te lopen.

Voor de spreker geldt één signaal: staat er in de aankondigende zin zélf dat
God, JAHWEH of de HEERE spreekt, dan is het Godsspraak, anders mensenspraak.
Alleen díe zin telt, niet het hele vers — 2 Koningen 6:15 luidt "…een leger
omringde de stad… Toen zei zijn jongen tot hem:", en wie het hele vers afzoekt
op godsnamen zet die knecht per ongeluk als God neer.

    python scripts/citaat_ontbreekt.py                de hele werklijst
    python scripts/citaat_ontbreekt.py --boek lukas   één boek
    python scripts/citaat_ontbreekt.py --tellen       alleen de aantallen
"""
import argparse
import collections
import json
import os
import re
import sys

WORTEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SPAN = re.compile(r'<span class="[a-z-]+"><i>.*?</i></span>', re.S)
SPREEK = (r'(?:zei|zeide|zeiden|sprak|spraken|riep|riepen|antwoordde|antwoordden'
          r'|gebood|vroeg|vraagde|zeggende)')
# In de aankondiging mag alleen een notenmarkering staan; zodra er een span
# begint zitten we al in een gemarkeerd citaat.
STUK = r'(?:[^<:]|<sup[^>]*>.*?</sup>)'
AANK = re.compile(r'^(' + STUK + r'{0,220}?\b' + SPREEK + r'\b' + STUK + r'{0,70}:)\s*(.+)$', re.S)

GOD = re.compile(r'\b(JAHWEH|God|Gods|de HEERE|de Heere|Heere HEERE)\b')
ENGEL = re.compile(r'\bEngel\b')          # spreekt namens God, maar eigen kleur

TWEEDE = re.compile(r'\b' + SPREEK + r'\b[^:]{0,70}:')
HERVAT = re.compile(r'[.!?;]\s+(?:en|En|Toen|Doch|Maar|Zo|Daarna|Alzo|Verder)\s+\w[\w\' ]{0,34}?\b'
                    r'(?:zei|sprak|zeiden|spraken|riep|antwoordde|ging|gingen|nam|namen|deed|deden|'
                    r'kwam|kwamen|keerde|keerden|stond|stonden|was|waren|werd|werden|hoorde|zag|zagen)\b')


def kaal(html):
    zonder = re.sub(r'<sup[^>]*>.*?</sup>', '', html)
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', zonder)).strip()


def spreker(aankondiging):
    """God of mens, op grond van de aankondigende zin alleen."""
    zin = kaal(aankondiging)
    knip = max(zin.rfind('. '), zin.rfind('; '), zin.rfind('! '), zin.rfind('? '))
    if knip >= 0:
        zin = zin[knip + 1:]
    if ENGEL.search(zin):
        return "?"
    return "God" if GOD.search(zin) else "mens"


def grens_onzeker(rede):
    """Loopt er vertelling of een tweede spreker achter het citaat aan?

    Een hint, geen uitsluitsel. De vlag vangt 2 Koningen 2:15 ("…rust op
    Elisa; en zij kwamen hem tegemoet") maar niet 1 Koningen 22:32 ("…de
    koning van Israël, en zij keerden zich naar hem"), want daar hervat de
    vertelling met een komma. Zonder vlag is een vers dus niet veilig; élk
    vers in deze lijst moet gelezen worden."""
    t = kaal(rede)
    return bool(TWEEDE.search(t) or HERVAT.search(t))


def main():
    p = argparse.ArgumentParser(description="Werklijst van ontbrekende citaatopmaak.")
    p.add_argument("--boek", help="beperk tot één boek")
    p.add_argument("--tellen", action="store_true", help="alleen de aantallen per boek")
    a = p.parse_args()

    data = os.path.join(WORTEL, "data")
    boeken = [a.boek] if a.boek else sorted(os.listdir(data))
    tel = collections.Counter()
    perboek = collections.Counter()

    for b in boeken:
        map_ = os.path.join(data, b)
        if not os.path.isdir(map_) or not os.path.exists(os.path.join(map_, "1.json")):
            continue
        for fn in sorted(os.listdir(map_), key=lambda x: int(x[:-5]) if x[:-5].isdigit() else 0):
            if not fn.endswith(".json"):
                continue
            d = json.load(open(os.path.join(map_, fn), encoding="utf-8"))
            for v in d.get("verses", []):
                h = v.get("text2026_html")
                if not h or SPAN.search(h):
                    continue                          # heeft al opmaak
                m = AANK.match(h)
                if not m:
                    continue
                aankondiging, rede = m.groups()
                if len(kaal(rede)) < 12:
                    continue
                wie = spreker(aankondiging)
                onzeker = grens_onzeker(rede)
                tel[wie] += 1
                if onzeker:
                    tel["grens onzeker"] += 1
                perboek[b] += 1
                if not a.tellen:
                    merk = "   <-- ook de grens is onzeker" if onzeker else ""
                    print(f'{b} {d.get("number")}:{v["number"]}   [{wie}]{merk}')
                    print(f'   buiten: ...{kaal(aankondiging)[-64:]}')
                    print(f'   citaat: {kaal(rede)[:118]}')

    totaal = tel["God"] + tel["mens"] + tel["?"]
    print(f'\n{totaal} verzen zonder citaatopmaak, in {len(perboek)} boeken.')
    print(f'  voorstel spreker : {tel["God"]} Godsspraak, {tel["mens"]} mensenspraak, '
          f'{tel["?"]} onduidelijk')
    print(f'  grens onzeker    : {tel["grens onzeker"]} — daar loopt er vertelling of een '
          f'tweede spreker achteraan')
    for b, n in perboek.most_common(15):
        print(f'    {b:<18} {n}')
    return 0


if __name__ == "__main__":
    sys.exit(main())
