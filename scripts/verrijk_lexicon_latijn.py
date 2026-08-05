#!/usr/bin/env python3
"""Verrijk data/lexicon-latijn.json met woordsoort, stamvormen en betekenissen.

De 3961 vermeldingen in het Latijnse woordenboek zijn *tekstvormen* uit 4 Ezra,
geen lemma's: `filius`, `filii`, `filiorum` en `filios` staan er alle vier apart
in, elk met één kale gloss ("zoon", "van de zonen", …). Dit script knoopt elke
vorm aan zijn stamwoord en zet daar het woordenboekartikel bij:

    woordsoort    zelfstandig naamwoord (mannelijk)
    stamvormen    filius, filii, m.
    betekenissen  ["zoon", "kind, nakomeling", "lid van een groep, aanhanger"]
    vormanalyse   genitief ev., of nominatief/vocatief mv.
    stamwoord     filius

De woordenschat staat in `scripts/latijn_stamwoorden.py`, de vormleer in
`scripts/latijn_morfologie.py`. Alle bronnen zijn publiek domein: Lewis & Short
(1879) — in de repo als `data/lexicon-lewis-short-4ezra.json` — en standaard
Latijnse schoolgrammatica.

Wat het script *niet* doet: raden. Past een vorm bij geen enkel stamwoord, of
bij meer stamwoorden zonder dat de bestaande gloss uitsluitsel geeft, dan blijft
de vermelding onaangeroerd en krijgt hij alleen `"verrijkt": false`.

Gebruik:
    python scripts/verrijk_lexicon_latijn.py             # schrijf de verrijking weg
    python scripts/verrijk_lexicon_latijn.py --rapport   # alleen tellen, niets schrijven
    python scripts/verrijk_lexicon_latijn.py --open N    # toon de N grootste gaten
"""
import json
import os
import re
import sys
import unicodedata
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import latijn_stamwoorden as SW            # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'data')
LEXICON = os.path.join(DATA, 'lexicon-latijn.json')
LEWIS_SHORT = os.path.join(DATA, 'lexicon-lewis-short-4ezra.json')

# Velden die dit script beheert; ze worden bij elke draai opnieuw gezet, zodat
# het script herhaalbaar is en een verwijderd stamwoord ook echt verdwijnt.
EIGEN_VELDEN = ('woordsoort', 'stamvormen', 'betekenissen', 'vormanalyse',
                'stamwoord', 'toelichting', 'verwant', 'homoniem', 'bron', 'verrijkt')

# Spellingvarianten: de handschriften van 4 Ezra laten voorvoegsels vaak
# onversmolten (inmortalis naast immortalis, conpletus naast completus). Dit is
# alleen een zoeksleutel — de getoonde spelling verandert er niet door.
_ASSIMILATIE = [
    (re.compile(r'^ad([plsfgctrn])'), r'a\1\1'),
    (re.compile(r'^adq'), 'acq'),
    (re.compile(r'^inm'), 'imm'), (re.compile(r'^inp'), 'imp'),
    (re.compile(r'^inb'), 'imb'), (re.compile(r'^inr'), 'irr'),
    (re.compile(r'^inl'), 'ill'),
    (re.compile(r'^conp'), 'comp'), (re.compile(r'^conb'), 'comb'),
    (re.compile(r'^conm'), 'comm'), (re.compile(r'^conl'), 'coll'),
    (re.compile(r'^conr'), 'corr'),
    (re.compile(r'^obp'), 'opp'), (re.compile(r'^obf'), 'off'),
    (re.compile(r'^obc'), 'occ'), (re.compile(r'^subp'), 'supp'),
]


def sleutel(woord):
    """Zoeksleutel: kleine letters, zonder diakritische tekens, met versmolten
    voorvoegsels — zodat `inmortalem` en `immortalem` bij elkaar komen."""
    w = unicodedata.normalize('NFD', woord or '')
    w = ''.join(c for c in w if unicodedata.category(c) != 'Mn').lower()
    w = re.sub(r'[^a-z]', '', w)
    for patroon, vervang in _ASSIMILATIE:
        nieuw = patroon.sub(vervang, w)
        if nieuw != w:
            return nieuw
    return w


# Woordjes die niets zeggen als je twee kandidaten op hun gloss vergelijkt.
_STOP = set('de het een en of van in op te met aan voor door als dat die dit er '
            'is zijn was wordt worden niet naar bij uit om ook nog al dan wel '
            'ik gij hij zij wij mij hem haar hen u uw mijn zijn hun ons je jij '
            'men iets iemand zich naamwoord'.split())


def gloss_woorden(tekst):
    return {w for w in re.split(r'[^a-zA-Zàâäéèêëïîôöùûüç]+', (tekst or '').lower())
            if len(w) > 1 and w not in _STOP}


def _overlap(a, b):
    """Aantal woorden dat de twee verzamelingen delen, op de eerste vier letters
    vergeleken — zo telt 'koningen' in de gloss ook mee bij 'koning' in het
    woordenboekartikel."""
    ka = {w[:4] for w in a}
    kb = {w[:4] for w in b}
    return len(ka & kb)


# Aanwijzingen uit de bestaande gloss: gaat het om een werkwoordsvorm of om een
# naamwoord? "ik zag" wijst op een werkwoord, "zonen (dat./abl.)" op een naamwoord.
_HINT_WW = re.compile(r'^(ik|gij|je|jij|hij|wij|men)\b'
                      r'|\b(zal|zult|zullen|zou|zouden|wordt|worden|werd|werden|moge)\b')
_HINT_NW = re.compile(r'\((?:gen|dat|abl|acc|nom|voc|mv|ev|m|v|o|vr|f)\.'
                      r'|^(?:van de|van het|van een|der|des|aan de|aan het)\b')


def bouw_index():
    """vorm-sleutel -> [(kopwoord, vormomschrijving), …]"""
    index = defaultdict(list)
    for kop, sw in SW.STAMWOORDEN.items():
        for vorm, oms in sw['vormen'].items():
            index[sleutel(vorm)].append((kop, oms))
    return index


def lewis_short_koppen():
    """Kopwoorden uit Lewis & Short, op zoeksleutel (zonder telcijfer)."""
    with open(LEWIS_SHORT, encoding='utf-8') as fh:
        data = json.load(fh)
    koppen = {}
    for it in data.get('woorden', []):
        k = sleutel(re.sub(r'[0-9]+$', '', it.get('woord', '')))
        if k and k not in koppen:
            koppen[k] = it.get('woord')
    return koppen


def kies(kandidaten, gloss, vorm=''):
    """Meer stamwoorden claimen dezelfde vorm. Kies er één op grond van de
    bestaande Nederlandse gloss; lukt dat niet overtuigend, kies dan niets."""
    koppen = sorted({k for k, _ in kandidaten})
    if len(koppen) == 1:
        return koppen[0], []
    # 1. expliciete voorrang (bv. het voegwoord `quam` boven de accusatief van qui)
    hoogste = max(SW.STAMWOORDEN[k]['prio'] for k in koppen)
    top = [k for k in koppen if SW.STAMWOORDEN[k]['prio'] == hoogste]
    if len(top) == 1:
        return top[0], [k for k in koppen if k != top[0]]
    # 2. wijst de gloss op een werkwoordsvorm of juist op een naamwoord?
    gl = (gloss or '').lower()
    if _HINT_NW.search(gl):
        smal = [k for k in top if not SW.STAMWOORDEN[k]['woordsoort'].startswith('werkwoord')]
    elif _HINT_WW.search(gl):
        smal = [k for k in top if SW.STAMWOORDEN[k]['woordsoort'].startswith('werkwoord')]
    else:
        smal = top
    if smal:
        top = smal
    if len(top) == 1:
        return top[0], [k for k in koppen if k != top[0]]
    # 3. overlap tussen de bestaande gloss en de betekenissen van het stamwoord,
    #    plus een voorkeur voor het stamwoord waarvan dit de grondvorm is
    #    (`creatura` als zelfstandig naamwoord gaat voor het toekomend deelwoord
    #    van `creare`).
    doel = gloss_woorden(gloss)
    scores = {}
    for k in top:
        eigen = set()
        for b in SW.STAMWOORDEN[k]['betekenissen']:
            eigen |= gloss_woorden(b)
        score = 2 * _overlap(doel, eigen)
        if vorm and sleutel(k) == vorm:
            score += 1        # de tekstvorm is het kopwoord zelf
        omschrijvingen = [o for k2, o in kandidaten if k2 == k]
        if omschrijvingen and all('deelwoord' in o for o in omschrijvingen):
            score -= 1        # een deelwoordlezing is minder waarschijnlijk
        scores[k] = score
    beste = max(scores.values())
    winnaars = [k for k in top if scores[k] == beste]
    if beste > 0 and len(winnaars) == 1:
        return winnaars[0], [k for k in koppen if k != winnaars[0]]
    return None, koppen


def verrijk(woorden, index, ls_koppen):
    telling = Counter()
    onbekend = []
    for item in woorden:
        for veld in EIGEN_VELDEN:
            item.pop(veld, None)
        lemma = item.get('lemma', '')
        k = sleutel(lemma)
        kandidaten = index.get(k)
        if not kandidaten:
            item['verrijkt'] = False
            telling['geen_stamwoord'] += 1
            onbekend.append(lemma)
            continue
        kop, anderen = kies(kandidaten, item.get('betekenis', ''), k)
        if kop is None:
            item['verrijkt'] = False
            telling['dubbelzinnig'] += 1
            continue
        sw = SW.STAMWOORDEN[kop]
        omschrijvingen = [o for k2, o in kandidaten if k2 == kop]
        item['woordsoort'] = sw['woordsoort']
        item['stamvormen'] = sw['stamvormen']
        item['betekenissen'] = sw['betekenissen']
        analyse = ' of '.join(dict.fromkeys(omschrijvingen))
        if analyse and analyse != sw['woordsoort']:
            item['vormanalyse'] = analyse
        if sleutel(kop) != k:
            item['stamwoord'] = kop
        if sw['toelichting']:
            item['toelichting'] = sw['toelichting']
        if sw['verwant']:
            item['verwant'] = sw['verwant']
        if anderen:
            item['homoniem'] = anderen
        ls = ls_koppen.get(sleutel(kop))
        item['bron'] = ('Lewis & Short (1879)' if ls
                        else 'Latijnse schoolgrammatica en de context in 4 Ezra')
        telling['verrijkt'] += 1
        if ls:
            telling['met_lewis_short'] += 1
    return telling, onbekend


def sorteer(item):
    """Zet de velden in een vaste, leesbare volgorde (bestaande velden eerst)."""
    volgorde = ['lemma', 'vormen', 'betekenis', 'woordsoort', 'stamvormen',
                'betekenissen', 'vormanalyse', 'stamwoord', 'toelichting',
                'verwant', 'homoniem', 'bron', 'verrijkt', 'verwijzingen', 'ovl']
    uit = {}
    for veld in volgorde:
        if veld in item:
            uit[veld] = item[veld]
    for veld in item:                      # veiligheidsnet voor onbekende velden
        if veld not in uit:
            uit[veld] = item[veld]
    return uit


def schrijf(pad, data, ruw):
    """Schrijf terug in dezelfde opmaak als het origineel. Staat het bestand op
    één regel (zoals nu), dan blijft dat zo — anders wordt de diff onleesbaar."""
    m = re.search(r'\n( +)"', ruw)
    inspring = len(m.group(1)) if m else None
    tekst = json.dumps(data, ensure_ascii=False, indent=inspring)
    with open(pad, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(tekst)
        if ruw.endswith('\n'):
            fh.write('\n')


def main():
    args = sys.argv[1:]
    alleen_rapport = '--rapport' in args
    toon_open = 0
    if '--open' in args:
        toon_open = int(args[args.index('--open') + 1])

    with open(LEXICON, encoding='utf-8') as fh:
        ruw = fh.read()
    data = json.loads(ruw)
    woorden = data['woorden']

    index = bouw_index()
    ls_koppen = lewis_short_koppen()
    telling, onbekend = verrijk(woorden, index, ls_koppen)

    totaal = len(woorden)
    print('stamwoorden in de woordenschat : %d' % len(SW.STAMWOORDEN))
    print('gegenereerde vormen            : %d' % len(index))
    print('vermeldingen totaal            : %d' % totaal)
    print('  verrijkt                     : %d  (%.1f%%)'
          % (telling['verrijkt'], 100.0 * telling['verrijkt'] / totaal))
    print('    waarvan met Lewis & Short  : %d' % telling['met_lewis_short'])
    print('  geen stamwoord gevonden      : %d' % telling['geen_stamwoord'])
    print('  vorm te dubbelzinnig         : %d' % telling['dubbelzinnig'])

    if toon_open:
        clusters = defaultdict(list)
        for w in onbekend:
            clusters[w[:5]].append(w)
        top = sorted(clusters.items(), key=lambda kv: -len(kv[1]))[:toon_open]
        print('\nGrootste gaten (op de eerste vier letters):')
        for stam, lijst in top:
            print('  %-7s %2d  %s' % (stam, len(lijst), ' '.join(sorted(lijst))))

    if alleen_rapport:
        return
    # Kopgegevens vóór de woordenlijst houden, anders staat de metadata
    # achter 3961 items in het bestand.
    nieuw = {}
    for veld in ('taal', 'bron'):
        if veld in data:
            nieuw[veld] = data[veld]
    nieuw['verrijking'] = {
        'verrijkt': telling['verrijkt'],
        'nogNiet': totaal - telling['verrijkt'],
        'bronnen': 'Lewis & Short, A Latin Dictionary (1879), publiek domein; '
                   'standaard Latijnse vormleer; de Latijnse tekst van 4 Ezra zelf. '
                   'Gegenereerd met scripts/verrijk_lexicon_latijn.py.',
    }
    for veld in data:
        if veld not in nieuw and veld != 'woorden':
            nieuw[veld] = data[veld]
    nieuw['woorden'] = [sorteer(w) for w in woorden]
    schrijf(LEXICON, nieuw, ruw)
    print('\ngeschreven: %s' % os.path.relpath(LEXICON, ROOT))


if __name__ == '__main__':
    main()
