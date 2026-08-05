#!/usr/bin/env python3
"""Markeer geneste citaten in data/<boek>/<hoofdstuk>.json (`text2026_html`).

Een citaat binnen een citaat krijgt een eigen <span>, zodat de site het geel
kan weergeven (css/style.css `span.direct-speech span.direct-speech`,
css/lees.css `--citaat-genest`).

Voorbeeld — Exodus 4:1. De omhullende span is Mozes' antwoord; daarbinnen
citeert Mozes wat het volk zal zeggen:

    ... want zij zullen zeggen: <span class="direct-speech"><i>JAHWEH is u
    niet verschenen!</i></span>

Gebruik
-------
    python scripts/markeer_geneste_citaten.py                # proefdraai
    python scripts/markeer_geneste_citaten.py --toepassen    # schrijft weg
    python scripts/markeer_geneste_citaten.py --boek exodus --details

Werkwijze en waarborgen
-----------------------
* Alleen `text2026_html` wordt aangeraakt; `text2026` blijft ongemoeid en
  wordt na afloop gecontroleerd (html zonder tags == platte tekst).
* De inspringing van elk bestand wordt uit het bestand zelf gelezen — de
  hoofdstukbestanden staan gemengd op 1 en 2 spaties. Schrijven met één
  vaste waarde herformatteert de halve repo.
* Kanttekening-markers (`<sup class="note-marker">`) tellen niet mee als
  tekst en er wordt nooit een span-grens middenin gezet.
* Verzen met bestaande onbalans in de markup (Genesis 1–20) worden
  overgeslagen en geteld, niet gerepareerd.
* Idempotent: een span die al een geneste span bevat wordt niet opnieuw
  bewerkt, dus een tweede run verandert niets.
* Terughoudend: bij twijfel wordt niets gemarkeerd en telt het geval mee in
  de rubriek "bewust overgeslagen".
"""
import argparse
import json
import os
import re
import sys
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'data')

# --------------------------------------------------------------------------
# HTML-hulpjes
# --------------------------------------------------------------------------
TAG = re.compile(r'<[^>]+>|&[a-zA-Z#0-9]+;')
SUP_OPEN = re.compile(r'<sup\b[^>]*>')


def ontleed(html):
    """Splits html in zichtbare tekst + een positiekaart.

    Retourneert (plat, kaart). `plat` bevat de zichtbare tekst zonder tags;
    de inhoud van <sup class="note-marker"> telt niet mee, want dat is een
    kanttekening-cijfer en geen leestekst. `kaart[i]` = (start, eind) van het
    i-de platte teken in de oorspronkelijke html, zodat een span-grens altijd
    op een veilige plek terechtkomt (nooit middenin een tag of een marker).
    """
    plat, kaart, i, in_sup = [], [], 0, 0
    while i < len(html):
        m = TAG.match(html, i)
        if m:
            t = m.group(0)
            if SUP_OPEN.match(t):
                in_sup += 1
            elif t == '</sup>':
                in_sup -= 1
            elif t.startswith('&') and not in_sup:
                plat.append(t[1])          # entity telt als één teken
                kaart.append((i, m.end()))
            i = m.end()
            continue
        if not in_sup:
            plat.append(html[i])
            kaart.append((i, i + 1))
        i += 1
    return ''.join(plat), kaart


def buitenste_spans(html):
    """(klasse, inhoud_start, inhoud_eind) van elke span op het hoogste niveau.

    Geeft None terug als de spans niet netjes genest zijn.
    """
    res, diepte, stack = [], 0, []
    for m in re.finditer(r'<span class="([^"]+)">|</span>', html):
        if m.group(0) == '</span>':
            diepte -= 1
            if diepte < 0 or not stack:
                return None
            klasse, start = stack.pop()
            if diepte == 0:
                res.append((klasse, start, m.start()))
        else:
            stack.append((m.group(1), m.end()))
            diepte += 1
    return None if diepte else res


def balans(html):
    """True als spans én cursief netjes in balans zijn."""
    if html.count('<i>') != html.count('</i>'):
        return False
    return buitenste_spans(html) is not None


def strip_tags(html):
    return TAG.sub(lambda m: m.group(0)[1] if m.group(0).startswith('&') else '', html)


def _wit(s):
    """Vergelijk teksten zonder over dubbele spaties te struikelen."""
    return re.sub(r'\s+', ' ', s).strip()


# --------------------------------------------------------------------------
# Herkenning van een inleidende formule
# --------------------------------------------------------------------------
# Alleen formules waarvan de spreker aantoonbaar de omhullende spreker zélf is:
# deelwoorden, tegenwoordige tijd, toekomende tijd, voltooide tijd, en de
# eerste/tweede persoon in de verleden tijd. De verhalende derde persoon
# verleden tijd ("En hij zei:", "Toen zei God:") blijft er bewust buiten: dat
# is de verteller, en die staat op het eerste niveau, niet op het tweede.
DEELW = r'(?:zeggende|sprekende|roepende|gebiedende|zwerende)'
INF = r'(?:zeggen|spreken|antwoorden|roepen|zweren|gebieden|denken|vragen)'
MODAAL = (r'(?:zal|zult|zullen|zou|zoudt|zouden|moet|moeten|wil|wilt|willen'
          r'|kan|kunt|kunnen|mag|moogt|durft|durven|laat|laten)')
TT = r'(?:zeg|zegt|zeggen|spreek|spreekt|spreken|roept|antwoordt|gebiedt|zweer|zweert|denk|denkt)'
VD = r'(?:gezegd|gesproken|geantwoord|geroepen|geboden|gezworen)'
HULP = r'(?:heb|hebt|heeft|hebben|had|hadden|hebbende|is|zijn|was|waren|wordt|werd|werden)'
VT = (r'(?:zei|zeide|zeiden|sprak|spraken|antwoordde|antwoordden|riep|riepen'
      r'|zwoer|zwoeren|dacht|dachten|gebood|vraagde|vroeg)')
P12 = r'(?:ik|wij|we|gij|u|je|jij|jullie)'
# tussen werkwoord en dubbele punt mag alleen bijwerk staan, geen nieuwe zin
GAT = r'[^.;!?:…]{0,70}'

PATRONEN = [
    ('deelwoord', re.compile(r'\b' + DEELW + r'\b' + GAT + r':')),
    ('modaal',    re.compile(r'\b' + MODAAL + r'\b[^.;!?:]{0,40}?\b' + INF + r'\b' + GAT + r':')),
    ('tt',        re.compile(r'\b' + TT + r'\b' + GAT + r':')),
    ('voltooid',  re.compile(r'\b' + HULP + r'\b(?:\s+\w+){0,5}\s+' + VD + r'\b' + GAT + r':')),
    ('pers12a',   re.compile(r'\b' + P12 + r'\s+(?:\w+\s+){0,2}' + VT + r'\b' + GAT + r':')),
    ('pers12b',   re.compile(r'\b' + VT + r'\s+' + P12 + r'\b' + GAT + r':')),
]

# "Voorwaar, Ik zeg u:" — de spreker kondigt zijn eigen woorden aan; dat is
# geen citaat binnen een citaat.
ZELFCITAAT = re.compile(
    r'\b(?:ik|wij|we)\s+(?:\w+\s+){0,2}(?:zeg|zeggen|vraag|vragen)\b'
    r'|\b(?:zeg|zeggen|vraag|vragen)\s+(?:ik|wij|we)\b', re.I)

GODNAAM = re.compile(r'\b(?:JAHWEH|Adonai|HEERE|Heilige Geest|God|GOD)\b')
# "Maar Mozes sprak voor JAHWEH, zeggende:" — hier is de Godsnaam voorwerp,
# geen onderwerp; de ingebedde spreker is dan Mozes en niet God.
VOORZETSEL = re.compile(r'\b(?:voor|tot|van|bij|aan|met|naar|in|op|over|jegens|door|tegen|onder)\s+'
                        r'(?:de\s+|het\s+)?$')


def god_spreekt(clausule):
    """True als de Godsnaam in de rapporterende clausule onderwerp kan zijn."""
    for m in GODNAAM.finditer(clausule):
        if not VOORZETSEL.search(clausule[:m.start()]):
            return True
    return False

# de verteller pakt de draad weer op: ". En hij ging uit van Farao …"
VERLEDEN = (r'(?:zei|zeide|zeiden|ging|gingen|nam|namen|antwoordde|antwoordden|deed|deden'
            r'|kwam|kwamen|stak|trok|trokken|keerde|keerden|hoorde|hoorden|zag|zagen|gaf|gaven'
            r'|sprak|spraken|riep|riepen|stond|stonden|verhief|zond|zonden|loog|dacht|dachten'
            r'|wierp|zette|bracht|brachten|liet|lieten|begon|begonnen|vond|vonden|bleef|bleven'
            r'|werd|werden|was|waren|had|hadden|hief|viel|vielen|\w{4,}(?:de|den|te|ten))')
VERTELLER_HERVAT = re.compile(
    r'[.!?]\s+(?:En|Maar|Toen|Daarna|Zo|Alzo|Doe|Nu)\b[^.!?]{0,70}?\b' + VERLEDEN + r'\b')

# korte uitroep/antwoord gevolgd door veel meer tekst: het ingebedde citaat
# houdt dan vrijwel zeker eerder op dan de omhullende span
KORT_ANTWOORD = re.compile(r'^(.{1,32}?[.!?])\s+(.+)$', re.S)

MIN_VOOR = 20    # zoveel citaattekst moet er vóór de inleiding staan
MIN_NA = 15      # en zoveel ingebed citaat erachter
BEGIN_CITAAT = re.compile(r'[A-ZÀ-ÖØ-Þ0-9‘“\'"(]')


def rapporterende_clausule(plat, vstart, colon):
    """De clausule waarin de inleiding staat: vanaf de vorige harde grens."""
    grens = max(plat.rfind(c, 0, vstart) for c in '.;!?:')
    return plat[grens + 1: colon]


def zoek_inleidingen(plat):
    """Alle (dubbelepunt, werkwoordstart, soort) in de platte spaninhoud."""
    ruw = {}
    for soort, pat in PATRONEN:
        for m in pat.finditer(plat):
            colon = m.end() - 1
            if colon not in ruw or m.start() < ruw[colon][0]:
                ruw[colon] = (m.start(), soort)
    return sorted((c, v[0], v[1]) for c, v in ruw.items())


def kies_inleiding(plat, tellers, ref):
    """Kies de inleiding van het ingebedde citaat, of None.

    De láátste bruikbare inleiding wint. Bij opeenvolgende citaten op
    hetzelfde niveau ("… zeggende: A; … zij zeggen: B") voorkomt dat dat de
    tussenliggende tekst van de omhullende spreker ook geel wordt; bij een
    keten van citaten in elkaar markeert het het binnenste citaat.
    """
    bruikbaar = []
    for colon, vstart, soort in zoek_inleidingen(plat):
        clausule = rapporterende_clausule(plat, vstart, colon)
        if ZELFCITAAT.search(clausule):
            tellers['over_zelfcitaat'] += 1
            continue
        if len(plat[:vstart].strip()) < MIN_VOOR:
            # de span begint mét de inleiding: dan is wat volgt het eerste
            # niveau (bv. "Zo zegt JAHWEH: …"), niet een citaat daarbinnen
            tellers['over_span_begint_met_inleiding'] += 1
            continue
        na = plat[colon + 1:].strip()
        if len(na) < MIN_NA or len(na.split()) < 3:
            tellers['over_te_kort'] += 1
            continue
        if not BEGIN_CITAAT.match(na):
            # een opsomming of indirecte rede ("…, zeggende: dat zij …")
            tellers['over_geen_hoofdletter'] += 1
            continue
        bruikbaar.append((colon, vstart, soort, clausule, na))
    if not bruikbaar:
        return None
    colon, vstart, soort, clausule, na = bruikbaar[-1]
    if VERTELLER_HERVAT.search(na):
        tellers['over_verteller_hervat'] += 1
        tellers.setdefault('_overgeslagen', []).append((ref, 'verteller hervat', na[:90]))
        return None
    m = KORT_ANTWOORD.match(na)
    if m and len(m.group(2)) > 20:
        tellers['over_kort_antwoord'] += 1
        tellers.setdefault('_overgeslagen', []).append((ref, 'kort antwoord', na[:90]))
        return None
    return colon, vstart, soort, clausule, na


# --------------------------------------------------------------------------
# Handmatig nagelopen verzen
# --------------------------------------------------------------------------
# Door de eigenaar aangewezen verzen waar de omhullende span om het hele vers
# stond (inclusief de inleiding van de verteller en/of het verhalende vervolg)
# of waar de markering helemaal ontbrak. Stuk voor stuk tegen de 1637- en
# 1888-tekst gelegd.
#
# Vorm: (boek, hoofdstuk, vers, zoekpatroon, vervanging, klaar-patroon).
# Het zoekpatroon is een reguliere expressie op `text2026_html`; matcht die
# niet, maar het klaar-patroon wél, dan is de correctie al doorgevoerd en
# gebeurt er niets. Bewust met patronen in plaats van letterlijke tekst: aan
# de vertaling zelf wordt in parallel gewerkt ("de kinderen van Israël" werd
# bijvoorbeeld "de Israëlieten"), en daar mag deze correctie niet op stuklopen.
HANDMATIG = [
    # de span slokte het verhalende vervolg op; alleen "Ga heen." is gesproken
    ('exodus', 2, 8,
     r'^(En de dochter van Farao zei tot haar: )<span class="direct-speech"><i>(Ga heen\.) (.*)</i></span>$',
     r'\1<span class="direct-speech"><i>\2</i></span> \3',
     r'<i>Ga heen\.</i></span> En de jonge maagd'),
    # de span begon bij de verteller en liep door tot in het verhalende slot
    ('exodus', 3, 6,
     r'^<span class="god-speaks"><i>(Hij zei verder: )(.*?)( En Mozes verborg .*)</i></span>$',
     r'\1<span class="god-speaks"><i>\2</i></span>\3',
     r'^Hij zei verder: <span class="god-speaks">'),
    ('exodus', 3, 7,
     r'^<span class="god-speaks"><i>(En JAHWEH zei: )(.*)</i></span>$',
     r'\1<span class="god-speaks"><i>\2</i></span>',
     r'^En JAHWEH zei: <span class="god-speaks">'),
    # bovendien een citaat in een citaat: de boodschap die Mozes moet doorgeven
    # eindigt bij "gezonden;", daarna spreekt God weer over Zijn eigen Naam
    ('exodus', 3, 15,
     r'^<span class="god-speaks"><i>(Toen zei God verder tot Mozes: )(Zo zult u tot .*? zeggen: )(.*?gezonden;)( dat is Mijn Naam .*)</i></span>$',
     r'\1<span class="god-speaks"><i>\2<span class="direct-speech"><i>\3</i></span>\4</i></span>',
     r'^Toen zei God verder tot Mozes: <span class="god-speaks">'),
    # vervolg van de Godsspraak uit vers 4, maar zonder enige markering
    ('exodus', 4, 5,
     r'^(Opdat zij geloven, dat u verschenen is JAHWEH[^<]*)$',
     r'<span class="god-speaks"><i>\1</i></span>',
     r'^<span class="god-speaks"><i>Opdat zij geloven'),
    ('exodus', 4, 7,
     r'^<span class="god-speaks"><i>(En Hij zei: )(Steek uw hand opnieuw in uw boezem\.)( En hij stak .*)</i></span>$',
     r'\1<span class="god-speaks"><i>\2</i></span>\3',
     r'^En Hij zei: <span class="god-speaks">'),
    ('exodus', 4, 26,
     r'^<span class="direct-speech"><i>(En Hij liet van hem af\. Toen zei zij: )(Bloedbruidegom!)( vanwege de besnijdenis\.)</i></span>$',
     r'\1<span class="direct-speech"><i>\2</i></span>\3',
     r'^En Hij liet van hem af\. Toen zei zij: <span'),
    # geen directe rede in dit vers: de hele span kan weg
    ('exodus', 4, 29,
     r'^<span class="direct-speech"><i>(Toen ging Mozes en Aäron,[^<]*)</i></span>$',
     r'\1',
     r'^Toen ging Mozes en Aäron,'),
    ('exodus', 4, 30,
     r'^<span class="direct-speech"><i>(En Aäron sprak al de woorden,[^<]*)</i></span>$',
     r'\1',
     r'^En Aäron sprak al de woorden,'),
    # hier ontbrak de markering van de directe rede helemaal
    ('exodus', 5, 13,
     r'^(En de aandrijvers drongen aan, zeggende: )(Voltooit uw werken[^<]*)$',
     r'\1<span class="direct-speech"><i>\2</i></span>',
     r'zeggende: <span class="direct-speech"><i>Voltooit'),
    # het ingebedde citaat van de aandrijvers is maar één zin; daarna spreken
    # de ambtlieden Farao weer aan ("uwe knechten worden geslagen", 1637)
    ('exodus', 5, 16,
     r'(zij zeggen tot ons: )(Maakt de bakstenen;)( en ziet,)',
     r'\1<span class="direct-speech"><i>\2</i></span>\3',
     r'<i>Maakt de bakstenen;</i></span> en ziet,'),
    # Godsspraak zonder enige markering (elders Exodus 6:1)
    ('exodus', 5, 24,
     r'^(Toen zei JAHWEH tot Mozes: )(Nu zult u zien[^<]*)$',
     r'\1<span class="god-speaks"><i>\2</i></span>',
     r'^Toen zei JAHWEH tot Mozes: <span class="god-speaks">'),
]


def handmatig_index():
    idx = defaultdict(dict)
    for boek, hfst, vers, zoek, verv, klaar in HANDMATIG:
        idx[(boek, hfst)][vers] = (re.compile(zoek, re.S), verv, re.compile(klaar))
    return idx


# --------------------------------------------------------------------------
# Kern
# --------------------------------------------------------------------------
def verwerk_vers(html, tellers, ref):
    """Geef de nieuwe html terug plus een lijst beschrijvingen, of (html, [])."""
    spans = buitenste_spans(html)
    if spans is None or html.count('<i>') != html.count('</i>'):
        tellers['vers_onbalans'] += 1
        tellers.setdefault('_onbalans', []).append(ref)
        return html, []

    invoegingen, verslag = [], []
    for klasse, cs, ce in spans:
        binnen = html[cs:ce]
        if '<span' in binnen:
            tellers['span_al_genest'] += 1
            continue
        plat, kaart = ontleed(binnen)
        keuze = kies_inleiding(plat, tellers, ref)
        if not keuze:
            continue
        colon, vstart, soort, clausule, na = keuze

        # eerste zichtbare teken ná de dubbele punt = begin van het citaat
        start = colon + 1
        while start < len(plat) and plat[start].isspace():
            start += 1
        eind = len(plat)
        while eind > start and plat[eind - 1].isspace():
            eind -= 1
        if eind <= start:
            continue
        nieuwe_klasse = 'god-speaks' if god_spreekt(clausule) else 'direct-speech'
        invoegingen.append((cs + kaart[start][0], f'<span class="{nieuwe_klasse}"><i>'))
        invoegingen.append((cs + kaart[eind - 1][1], '</i></span>'))
        verslag.append({
            'ref': ref, 'buiten': klasse, 'binnen': nieuwe_klasse, 'soort': soort,
            'inleiding': clausule.strip()[-60:], 'citaat': plat[start:eind][:110],
        })

    if not invoegingen:
        return html, []
    for pos, tekst in sorted(invoegingen, key=lambda x: -x[0]):
        html = html[:pos] + tekst + html[pos:]
    return html, verslag


def tel_genest(html):
    diepte = nest = 0
    for m in re.finditer(r'<span\b[^>]*>|</span>', html):
        if m.group(0).startswith('</'):
            diepte -= 1
        else:
            diepte += 1
            if diepte >= 2:
                nest = 1
    return nest


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--toepassen', action='store_true', help='schrijf de wijzigingen weg')
    ap.add_argument('--boek', help='beperk tot één boek-id, bv. exodus')
    ap.add_argument('--details', action='store_true', help='toon elke wijziging')
    ap.add_argument('--overgeslagen', action='store_true', help='toon de bewust overgeslagen gevallen')
    args = ap.parse_args()

    books = json.load(open(os.path.join(DATA, 'books.json'), encoding='utf-8'))['books']
    hand = handmatig_index()
    tellers = Counter()
    verslag, per_boek, hand_gedaan, hand_mislukt = [], Counter(), [], []
    genest_voor = genest_na = 0

    for b in books:
        bid = b['id']
        if args.boek and bid != args.boek:
            continue
        for ch in b.get('chaptersIncluded', []):
            fp = os.path.join(DATA, bid, f'{ch}.json')
            if not os.path.exists(fp):
                continue
            with open(fp, encoding='utf-8', newline='') as fh:
                ruw_orig = fh.read()
            # regeleinde van het bestand zelf overnemen; de werkmap staat
            # gemengd op CRLF en LF en we willen geen ruis in de diff
            regeleinde = '\r\n' if '\r\n' in ruw_orig else '\n'
            ruw = ruw_orig.replace('\r\n', '\n')
            m = re.search(r'\n( +)"', ruw)                 # inspringing uit het bestand zelf
            inspring = len(m.group(1)) if m else 2
            eindregel = ruw.endswith('\n')
            doc = json.loads(ruw)
            gewijzigd = False
            for v in doc.get('verses', []):
                if not isinstance(v, dict):
                    continue
                html = v.get('text2026_html')
                if not html:
                    continue
                ref = f'{bid} {ch}:{v.get("number")}'
                tellers['verzen'] += 1
                genest_voor += tel_genest(html)

                regel = hand.get((bid, ch), {}).get(v.get('number'))
                if regel:
                    zoek, verv, klaar = regel
                    if zoek.search(html):
                        html = zoek.sub(verv, html)
                        gewijzigd = True
                        hand_gedaan.append(ref)
                    elif not klaar.search(html):
                        hand_mislukt.append(ref)

                nieuw_html, deel = verwerk_vers(html, tellers, ref)
                if deel:
                    verslag.extend(deel)
                    per_boek[bid] += 1
                    tellers['gemarkeerd'] += len(deel)
                    html = nieuw_html
                if html != v['text2026_html']:
                    # veiligheidsnet: de zichtbare tekst en de kanttekening-
                    # markers moeten letterlijk hetzelfde blijven
                    if (strip_tags(html) != strip_tags(v['text2026_html'])
                            or html.count('<sup') != v['text2026_html'].count('<sup')):
                        print(f'FOUT tekst of nootmarker gewijzigd bij {ref}', file=sys.stderr)
                        sys.exit(1)
                    plat = v.get('text2026')
                    if plat is not None and _wit(ontleed(html)[0]) != _wit(plat):
                        tellers['waarschuwing_plat_wijkt_af'] += 1
                        tellers.setdefault('_plat_afwijkend', []).append(ref)
                    if not balans(html):
                        print(f'FOUT onbalans na bewerking bij {ref}', file=sys.stderr)
                        sys.exit(1)
                    v['text2026_html'] = html
                    gewijzigd = True
                genest_na += tel_genest(html)

            if gewijzigd and args.toepassen:
                uit = json.dumps(doc, ensure_ascii=False, indent=inspring)
                if eindregel:
                    uit += '\n'
                with open(fp, 'w', encoding='utf-8', newline='') as fh:
                    fh.write(uit.replace('\n', regeleinde))

    # ---------------------------------------------------------------- verslag
    print(f'verzen bekeken            : {tellers["verzen"]}')
    print(f'verzen met nesting vóór   : {genest_voor}')
    print(f'verzen met nesting ná     : {genest_na}')
    print(f'nieuw gemarkeerd          : {tellers["gemarkeerd"]} in {len(per_boek)} boeken')
    print(f'handmatige correcties     : {len(hand_gedaan)}'
          + (f'  (niet toegepast: {hand_mislukt})' if hand_mislukt else ''))
    print(f'spans die al genest waren  : {tellers["span_al_genest"]}')
    print(f'verzen met bestaande onbalans (overgeslagen): {tellers["vers_onbalans"]}')
    print('bewust overgeslagen:')
    for sleutel, label in [
        ('over_span_begint_met_inleiding', 'span begint met de inleiding (eerste niveau)'),
        ('over_zelfcitaat', 'spreker kondigt eigen woorden aan ("Ik zeg u:")'),
        ('over_te_kort', 'te weinig tekst na de dubbele punt'),
        ('over_geen_hoofdletter', 'geen hoofdletter na de dubbele punt (opsomming/indirect)'),
        ('over_verteller_hervat', 'verteller pakt de draad weer op'),
        ('over_kort_antwoord', 'kort antwoord gevolgd door veel meer tekst'),
    ]:
        print(f'  {tellers[sleutel]:5d}  {label}')
    print('per boek:', ', '.join(f'{k} {v}' for k, v in per_boek.most_common()))
    if args.details:
        for r in verslag:
            print(f'  {r["ref"]:24s} [{r["buiten"]}>{r["binnen"]}] '
                  f'…{r["inleiding"]}: {r["citaat"]}')
    if args.overgeslagen:
        for ref, reden, tekst in tellers.get('_overgeslagen', []):
            print(f'  OVERGESLAGEN {ref:22s} ({reden}) {tekst}')
    if not args.toepassen:
        print('\n(proefdraai — niets weggeschreven; gebruik --toepassen)')


if __name__ == '__main__':
    main()
