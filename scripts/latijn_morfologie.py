#!/usr/bin/env python3
"""Latijnse vormleer — paradigma-generator voor de verrijking van het woordenboek.

Dit is de *motor*: hij weet hoe Latijnse naamwoorden verbogen en werkwoorden
vervoegd worden. De woordenschat zelf (welke stamwoorden er zijn en wat ze
betekenen) staat in `scripts/latijn_stamwoorden.py`.

Waarom een generator en geen kant-en-klare vormenlijst? De 3961 vermeldingen in
`data/lexicon-latijn.json` zijn geen lemma's maar *tekstvormen*: `filius`,
`filii`, `filiorum` en `filios` staan er alle vier apart in. Door per stamwoord
het volledige paradigma te genereren kunnen we die vormen aan hun stamwoord
knopen én zeggen welke naamval/persoon het is.

Alle grammaticale feiten hier zijn standaard schoolgrammatica en dus vrij van
auteursrecht; de betekenissen komen uit Lewis & Short (1879, publiek domein).
"""

# ---------------------------------------------------------------------------
# Etiketten (Nederlands, leesbaar voor een niet-classicus)
# ---------------------------------------------------------------------------

NAAMVAL = {'nom': 'nominatief', 'gen': 'genitief', 'dat': 'datief',
           'acc': 'accusatief', 'abl': 'ablatief', 'voc': 'vocatief'}
GETAL = {'ev': 'enkelvoud', 'mv': 'meervoud'}
GESLACHT = {'m': 'mannelijk', 'v': 'vrouwelijk', 'o': 'onzijdig'}

TIJD = {
    'praes': 'tegenwoordige tijd',
    'imperf': 'verleden tijd (imperfectum)',
    'fut': 'toekomende tijd',
    'perf': 'perfectum (voltooid of verleden tijd)',
    'plqp': 'plusquamperfectum (voltooid verleden tijd)',
    'futex': 'voltooid toekomende tijd',
}
PERSOON = {1: '1e pers.', 2: '2e pers.', 3: '3e pers.'}


def _naamval_label(paren):
    """['gen ev', 'nom mv', 'voc mv'] -> 'genitief ev., of nominatief/vocatief mv.'"""
    per_getal = {}
    volgorde = []
    for nv, getal in paren:
        if getal not in per_getal:
            per_getal[getal] = []
            volgorde.append(getal)
        if nv not in per_getal[getal]:
            per_getal[getal].append(nv)
    delen = []
    for getal in volgorde:
        nvn = '/'.join(NAAMVAL[n] for n in per_getal[getal])
        delen.append(nvn + ' ' + ('ev.' if getal == 'ev' else 'mv.'))
    return ', of '.join(delen)


# ---------------------------------------------------------------------------
# Zelfstandige naamwoorden
# ---------------------------------------------------------------------------
# Per klasse: (naamval, getal) -> uitgang achter de stam. 'nom ev' met waarde
# None betekent: neem de opgegeven nominatief letterlijk over (3e klasse).

_ZN = {
    # 1e klasse (a-stammen): terra, terrae
    '1': {('nom', 'ev'): 'a', ('gen', 'ev'): 'ae', ('dat', 'ev'): 'ae',
          ('acc', 'ev'): 'am', ('abl', 'ev'): 'a', ('voc', 'ev'): 'a',
          ('nom', 'mv'): 'ae', ('gen', 'mv'): 'arum', ('dat', 'mv'): 'is',
          ('acc', 'mv'): 'as', ('abl', 'mv'): 'is', ('voc', 'mv'): 'ae'},
    # 2e klasse mannelijk/vrouwelijk: dominus, domini
    '2': {('nom', 'ev'): 'us', ('gen', 'ev'): 'i', ('dat', 'ev'): 'o',
          ('acc', 'ev'): 'um', ('abl', 'ev'): 'o', ('voc', 'ev'): 'e',
          ('nom', 'mv'): 'i', ('gen', 'mv'): 'orum', ('dat', 'mv'): 'is',
          ('acc', 'mv'): 'os', ('abl', 'mv'): 'is', ('voc', 'mv'): 'i'},
    # 2e klasse onzijdig: verbum, verbi
    '2o': {('nom', 'ev'): 'um', ('gen', 'ev'): 'i', ('dat', 'ev'): 'o',
           ('acc', 'ev'): 'um', ('abl', 'ev'): 'o', ('voc', 'ev'): 'um',
           ('nom', 'mv'): 'a', ('gen', 'mv'): 'orum', ('dat', 'mv'): 'is',
           ('acc', 'mv'): 'a', ('abl', 'mv'): 'is', ('voc', 'mv'): 'a'},
    # 3e klasse medeklinkerstam: rex, regis
    '3': {('nom', 'ev'): None, ('gen', 'ev'): 'is', ('dat', 'ev'): 'i',
          ('acc', 'ev'): 'em', ('abl', 'ev'): 'e', ('voc', 'ev'): None,
          ('nom', 'mv'): 'es', ('gen', 'mv'): 'um', ('dat', 'mv'): 'ibus',
          ('acc', 'mv'): 'es', ('abl', 'mv'): 'ibus', ('voc', 'mv'): 'es'},
    # 3e klasse i-stam: civitas, civitatis (gen. mv. -ium)
    '3i': {('nom', 'ev'): None, ('gen', 'ev'): 'is', ('dat', 'ev'): 'i',
           ('acc', 'ev'): 'em', ('abl', 'ev'): 'e', ('voc', 'ev'): None,
           ('nom', 'mv'): 'es', ('gen', 'mv'): 'ium', ('dat', 'mv'): 'ibus',
           ('acc', 'mv'): 'es', ('abl', 'mv'): 'ibus', ('voc', 'mv'): 'es'},
    # 3e klasse onzijdig medeklinkerstam: nomen, nominis
    '3o': {('nom', 'ev'): None, ('gen', 'ev'): 'is', ('dat', 'ev'): 'i',
           ('acc', 'ev'): None, ('abl', 'ev'): 'e', ('voc', 'ev'): None,
           ('nom', 'mv'): 'a', ('gen', 'mv'): 'um', ('dat', 'mv'): 'ibus',
           ('acc', 'mv'): 'a', ('abl', 'mv'): 'ibus', ('voc', 'mv'): 'a'},
    # 3e klasse onzijdig i-stam: mare, maris (abl. ev. -i, mv. -ia/-ium)
    '3oi': {('nom', 'ev'): None, ('gen', 'ev'): 'is', ('dat', 'ev'): 'i',
            ('acc', 'ev'): None, ('abl', 'ev'): 'i', ('voc', 'ev'): None,
            ('nom', 'mv'): 'ia', ('gen', 'mv'): 'ium', ('dat', 'mv'): 'ibus',
            ('acc', 'mv'): 'ia', ('abl', 'mv'): 'ibus', ('voc', 'mv'): 'ia'},
    # 4e klasse: fructus, fructus
    '4': {('nom', 'ev'): 'us', ('gen', 'ev'): 'us', ('dat', 'ev'): 'ui',
          ('acc', 'ev'): 'um', ('abl', 'ev'): 'u', ('voc', 'ev'): 'us',
          ('nom', 'mv'): 'us', ('gen', 'mv'): 'uum', ('dat', 'mv'): 'ibus',
          ('acc', 'mv'): 'us', ('abl', 'mv'): 'ibus', ('voc', 'mv'): 'us'},
    # 4e klasse onzijdig: cornu, cornus
    '4o': {('nom', 'ev'): 'u', ('gen', 'ev'): 'us', ('dat', 'ev'): 'u',
           ('acc', 'ev'): 'u', ('abl', 'ev'): 'u', ('voc', 'ev'): 'u',
           ('nom', 'mv'): 'ua', ('gen', 'mv'): 'uum', ('dat', 'mv'): 'ibus',
           ('acc', 'mv'): 'ua', ('abl', 'mv'): 'ibus', ('voc', 'mv'): 'ua'},
    # 5e klasse: dies, diei
    '5': {('nom', 'ev'): 'es', ('gen', 'ev'): 'ei', ('dat', 'ev'): 'ei',
          ('acc', 'ev'): 'em', ('abl', 'ev'): 'e', ('voc', 'ev'): 'es',
          ('nom', 'mv'): 'es', ('gen', 'mv'): 'erum', ('dat', 'mv'): 'ebus',
          ('acc', 'mv'): 'es', ('abl', 'mv'): 'ebus', ('voc', 'mv'): 'es'},
}


def zelfstandig(nom, stam, klasse, alleen=None):
    """Verbuig een zelfstandig naamwoord. Geeft {vorm: [(naamval, getal), ...]}.

    `alleen` = 'ev' of 'mv' voor woorden die maar in één getal voorkomen
    (bv. `tenebrae`, duisternis — alleen meervoud).
    """
    tabel = _ZN[klasse]
    uit = {}
    # 2e klasse op -er/-ir (ager, liber, vir): de nominatief en vocatief zijn
    # gelijk aan het kopwoord, niet aan stam + -us/-e.
    afwijkend = klasse == '2' and nom and not nom.endswith('us')
    for (nv, getal), einde in tabel.items():
        if alleen and getal != alleen:
            continue
        if afwijkend and getal == 'ev' and nv in ('nom', 'voc'):
            vorm = nom
        else:
            vorm = nom if einde is None else stam + einde
        uit.setdefault(vorm, []).append((nv, getal))
    # De vocatief valt bijna altijd samen met de nominatief; hem dan ook noemen
    # maakt de vormanalyse alleen langer. Alleen een eigen vocatiefvorm (Domine)
    # blijft staan.
    for vorm, paren in uit.items():
        nommers = {g for n, g in paren if n == 'nom'}
        uit[vorm] = [(n, g) for n, g in paren if not (n == 'voc' and g in nommers)]
    return uit


# ---------------------------------------------------------------------------
# Bijvoeglijke naamwoorden
# ---------------------------------------------------------------------------

def _bnw_12(stam):
    """bonus, bona, bonum — 1e/2e klasse, drie geslachten.

    De vocatief blijft weg: bij bijvoeglijke naamwoorden en deelwoorden komt hij
    in 4 Ezra niet voor en hij maakt de vormanalyse alleen onleesbaar.
    """
    uit = {}
    for geslacht, klasse in (('m', '2'), ('v', '1'), ('o', '2o')):
        for vorm, paren in zelfstandig(None, stam, klasse).items():
            for nv, getal in paren:
                if nv == 'voc':
                    continue
                uit.setdefault(vorm, []).append((nv, getal, geslacht))
    return {v: p for v, p in uit.items() if p}


# 3e klasse bijvoeglijk naamwoord (omnis/omne, fortis/forte, felix/felicis).
_BNW3 = {
    ('nom', 'ev', 'mv_'): 'is', ('nom', 'ev', 'o'): 'e',
    ('gen', 'ev', '*'): 'is', ('dat', 'ev', '*'): 'i',
    ('acc', 'ev', 'mv_'): 'em', ('acc', 'ev', 'o'): 'e',
    ('abl', 'ev', '*'): 'i',
    ('nom', 'mv', 'mv_'): 'es', ('nom', 'mv', 'o'): 'ia',
    ('gen', 'mv', '*'): 'ium', ('dat', 'mv', '*'): 'ibus',
    ('acc', 'mv', 'mv_'): 'es', ('acc', 'mv', 'o'): 'ia',
    ('abl', 'mv', '*'): 'ibus',
}


def _bnw_3(stam, nom_mv=None, nom_o=None):
    """3e klasse. `nom_mv` = nominatief m./v. als die afwijkt (felix, ingens)."""
    uit = {}
    for (nv, getal, gsl), einde in _BNW3.items():
        gsln = ('m', 'v') if gsl == 'mv_' else ('o',) if gsl == 'o' else ('m', 'v', 'o')
        vorm = stam + einde
        if nv == 'nom' and getal == 'ev':
            if gsl == 'mv_' and nom_mv:
                vorm = nom_mv
            if gsl == 'o' and nom_o:
                vorm = nom_o
        if nv == 'acc' and getal == 'ev' and gsl == 'o' and nom_o:
            vorm = nom_o
        for g in gsln:
            uit.setdefault(vorm, []).append((nv, getal, g))
    # vocatief valt in de 3e klasse samen met de nominatief
    return uit


def _bnw_comp(stam):
    """Vergrotende trap: melior, melius / maior, maius (3e klasse medeklinker)."""
    uit = {}
    tab = {
        ('nom', 'ev', 'mv_'): 'ior', ('nom', 'ev', 'o'): 'ius',
        ('gen', 'ev', '*'): 'ioris', ('dat', 'ev', '*'): 'iori',
        ('acc', 'ev', 'mv_'): 'iorem', ('acc', 'ev', 'o'): 'ius',
        ('abl', 'ev', '*'): 'iore',
        ('nom', 'mv', 'mv_'): 'iores', ('nom', 'mv', 'o'): 'iora',
        ('gen', 'mv', '*'): 'iorum', ('dat', 'mv', '*'): 'ioribus',
        ('acc', 'mv', 'mv_'): 'iores', ('acc', 'mv', 'o'): 'iora',
        ('abl', 'mv', '*'): 'ioribus',
    }
    for (nv, getal, gsl), einde in tab.items():
        gsln = ('m', 'v') if gsl == 'mv_' else ('o',) if gsl == 'o' else ('m', 'v', 'o')
        for g in gsln:
            uit.setdefault(stam + einde, []).append((nv, getal, g))
    return uit


def bijvoeglijk(stam, soort='12', nom_mv=None, nom_o=None,
                comp_stam=None, sup_stam=None, bijw=None):
    """Volledig paradigma van een bijvoeglijk naamwoord, met trappen van
    vergelijking. Geeft {vorm: [(naamval, getal, geslacht, trap), ...]}, waarbij
    trap 'pos' | 'comp' | 'sup' | 'bijw' is."""
    uit = {}

    def voeg(deel, trap):
        for vorm, paren in deel.items():
            for nv, getal, gsl in paren:
                uit.setdefault(vorm, []).append((nv, getal, gsl, trap))

    voeg(_bnw_12(stam) if soort == '12' else _bnw_3(stam, nom_mv, nom_o), 'pos')
    if comp_stam is not False:
        voeg(_bnw_comp(comp_stam if comp_stam else stam), 'comp')
    if sup_stam is not False:
        voeg(_bnw_12((sup_stam if sup_stam else stam) + 'issim'), 'sup')
    if bijw:
        for b in ([bijw] if isinstance(bijw, str) else bijw):
            uit.setdefault(b, []).append((None, None, None, 'bijw'))
    return uit


# ---------------------------------------------------------------------------
# Werkwoorden
# ---------------------------------------------------------------------------
# Per vervoeging: sleutel -> zes uitgangen (1e-3e pers. ev., 1e-3e pers. mv.)
# achter de *wortel* (infinitief min -are/-ere/-ire).

_WW = {
    '1': {
        'praes': ['o', 'as', 'at', 'amus', 'atis', 'ant'],
        'imperf': ['abam', 'abas', 'abat', 'abamus', 'abatis', 'abant'],
        'fut': ['abo', 'abis', 'abit', 'abimus', 'abitis', 'abunt'],
        'praes_c': ['em', 'es', 'et', 'emus', 'etis', 'ent'],
        'imperf_c': ['arem', 'ares', 'aret', 'aremus', 'aretis', 'arent'],
        'praes_p': ['or', 'aris', 'atur', 'amur', 'amini', 'antur'],
        'imperf_p': ['abar', 'abaris', 'abatur', 'abamur', 'abamini', 'abantur'],
        'fut_p': ['abor', 'aberis', 'abitur', 'abimur', 'abimini', 'abuntur'],
        'praes_cp': ['er', 'eris', 'etur', 'emur', 'emini', 'entur'],
        'imperf_cp': ['arer', 'areris', 'aretur', 'aremur', 'aremini', 'arentur'],
        'imp': ['a', 'ate'], 'inf': 'are', 'inf_p': 'ari',
        'ptc': 'ans', 'ptc_stam': 'ant', 'gerund': 'and',
    },
    '2': {
        'praes': ['eo', 'es', 'et', 'emus', 'etis', 'ent'],
        'imperf': ['ebam', 'ebas', 'ebat', 'ebamus', 'ebatis', 'ebant'],
        'fut': ['ebo', 'ebis', 'ebit', 'ebimus', 'ebitis', 'ebunt'],
        'praes_c': ['eam', 'eas', 'eat', 'eamus', 'eatis', 'eant'],
        'imperf_c': ['erem', 'eres', 'eret', 'eremus', 'eretis', 'erent'],
        'praes_p': ['eor', 'eris', 'etur', 'emur', 'emini', 'entur'],
        'imperf_p': ['ebar', 'ebaris', 'ebatur', 'ebamur', 'ebamini', 'ebantur'],
        'fut_p': ['ebor', 'eberis', 'ebitur', 'ebimur', 'ebimini', 'ebuntur'],
        'praes_cp': ['ear', 'earis', 'eatur', 'eamur', 'eamini', 'eantur'],
        'imperf_cp': ['erer', 'ereris', 'eretur', 'eremur', 'eremini', 'erentur'],
        'imp': ['e', 'ete'], 'inf': 'ere', 'inf_p': 'eri',
        'ptc': 'ens', 'ptc_stam': 'ent', 'gerund': 'end',
    },
    '3': {
        'praes': ['o', 'is', 'it', 'imus', 'itis', 'unt'],
        'imperf': ['ebam', 'ebas', 'ebat', 'ebamus', 'ebatis', 'ebant'],
        'fut': ['am', 'es', 'et', 'emus', 'etis', 'ent'],
        'praes_c': ['am', 'as', 'at', 'amus', 'atis', 'ant'],
        'imperf_c': ['erem', 'eres', 'eret', 'eremus', 'eretis', 'erent'],
        'praes_p': ['or', 'eris', 'itur', 'imur', 'imini', 'untur'],
        'imperf_p': ['ebar', 'ebaris', 'ebatur', 'ebamur', 'ebamini', 'ebantur'],
        'fut_p': ['ar', 'eris', 'etur', 'emur', 'emini', 'entur'],
        'praes_cp': ['ar', 'aris', 'atur', 'amur', 'amini', 'antur'],
        'imperf_cp': ['erer', 'ereris', 'eretur', 'eremur', 'eremini', 'erentur'],
        'imp': ['e', 'ite'], 'inf': 'ere', 'inf_p': 'i',
        'ptc': 'ens', 'ptc_stam': 'ent', 'gerund': 'end',
    },
    '3io': {
        'praes': ['io', 'is', 'it', 'imus', 'itis', 'iunt'],
        'imperf': ['iebam', 'iebas', 'iebat', 'iebamus', 'iebatis', 'iebant'],
        'fut': ['iam', 'ies', 'iet', 'iemus', 'ietis', 'ient'],
        'praes_c': ['iam', 'ias', 'iat', 'iamus', 'iatis', 'iant'],
        'imperf_c': ['erem', 'eres', 'eret', 'eremus', 'eretis', 'erent'],
        'praes_p': ['ior', 'eris', 'itur', 'imur', 'imini', 'iuntur'],
        'imperf_p': ['iebar', 'iebaris', 'iebatur', 'iebamur', 'iebamini', 'iebantur'],
        'fut_p': ['iar', 'ieris', 'ietur', 'iemur', 'iemini', 'ientur'],
        'praes_cp': ['iar', 'iaris', 'iatur', 'iamur', 'iamini', 'iantur'],
        'imperf_cp': ['erer', 'ereris', 'eretur', 'eremur', 'eremini', 'erentur'],
        'imp': ['e', 'ite'], 'inf': 'ere', 'inf_p': 'i',
        'ptc': 'iens', 'ptc_stam': 'ient', 'gerund': 'iend',
    },
    '4': {
        'praes': ['io', 'is', 'it', 'imus', 'itis', 'iunt'],
        'imperf': ['iebam', 'iebas', 'iebat', 'iebamus', 'iebatis', 'iebant'],
        'fut': ['iam', 'ies', 'iet', 'iemus', 'ietis', 'ient'],
        'praes_c': ['iam', 'ias', 'iat', 'iamus', 'iatis', 'iant'],
        'imperf_c': ['irem', 'ires', 'iret', 'iremus', 'iretis', 'irent'],
        'praes_p': ['ior', 'iris', 'itur', 'imur', 'imini', 'iuntur'],
        'imperf_p': ['iebar', 'iebaris', 'iebatur', 'iebamur', 'iebamini', 'iebantur'],
        'fut_p': ['iar', 'ieris', 'ietur', 'iemur', 'iemini', 'ientur'],
        'praes_cp': ['iar', 'iaris', 'iatur', 'iamur', 'iamini', 'iantur'],
        'imperf_cp': ['irer', 'ireris', 'iretur', 'iremur', 'iremini', 'irentur'],
        'imp': ['i', 'ite'], 'inf': 'ire', 'inf_p': 'iri',
        'ptc': 'iens', 'ptc_stam': 'ient', 'gerund': 'iend',
    },
}

# Perfectum-systeem: uniform voor alle vervoegingen, achter de perfectumstam.
_PERF = {
    'perf': ['i', 'isti', 'it', 'imus', 'istis', 'erunt'],
    'plqp': ['eram', 'eras', 'erat', 'eramus', 'eratis', 'erant'],
    'futex': ['ero', 'eris', 'erit', 'erimus', 'eritis', 'erint'],
    'perf_c': ['erim', 'eris', 'erit', 'erimus', 'eritis', 'erint'],
    'plqp_c': ['issem', 'isses', 'isset', 'issemus', 'issetis', 'issent'],
}

# Werkwoordsvorm-etiketten. De persoonsvormen krijgen er persoon/getal bij.
_WW_LABEL = {
    'praes': ('praes', 'ind', 'act'), 'imperf': ('imperf', 'ind', 'act'),
    'fut': ('fut', 'ind', 'act'), 'praes_c': ('praes', 'conj', 'act'),
    'imperf_c': ('imperf', 'conj', 'act'), 'praes_p': ('praes', 'ind', 'pass'),
    'imperf_p': ('imperf', 'ind', 'pass'), 'fut_p': ('fut', 'ind', 'pass'),
    'praes_cp': ('praes', 'conj', 'pass'), 'imperf_cp': ('imperf', 'conj', 'pass'),
    'perf': ('perf', 'ind', 'act'), 'plqp': ('plqp', 'ind', 'act'),
    'futex': ('futex', 'ind', 'act'), 'perf_c': ('perf', 'conj', 'act'),
    'plqp_c': ('plqp', 'conj', 'act'),
}


def _syncope(wortel, perf_stam, einde):
    """Samengetrokken perfectumvormen: amavisti -> amasti, amaverunt -> amarunt.

    Bij een perfectum op -avi/-evi/-ivi valt de -v- weg voor de uitgangen die
    met -is- of -er- beginnen. De Vulgaat gebruikt deze korte vormen voortdurend
    (`creasti`, `audisti`, `peccastis`), dus zonder deze regel blijft een flink
    deel van de tekstvormen onherkend. De regel geldt alleen als de -v- bij de
    uitgang hoort en niet bij de stam zelf: `paveo/pavi` hoort er dus niet bij,
    anders zou `paverit` ten onrechte `parit` opleveren.
    """
    if perf_stam not in (wortel + 'av', wortel + 'ev', wortel + 'iv'):
        return []
    if not (einde.startswith('is') or einde.startswith('er')):
        return []
    kort = [perf_stam[:-1] + einde[1:]]
    if perf_stam.endswith('iv'):
        # Bij -ivi-perfecta valt vaak alleen de -v- weg: audiverunt -> audierunt.
        kort.append(perf_stam[:-1] + einde)
    return kort


def werkwoord(wortel, vervoeging, perf_stam=None, sup_stam=None, deponens=False):
    """Vervoeg een werkwoord volledig. Geeft {vorm: [analyse-tuple, ...]}.

    De analyse-tuple is ('pv', persoon, getal, tijd, wijs, genus) voor
    persoonsvormen, ('inf', genus) voor infinitieven, ('imp', getal) voor de
    gebiedende wijs, ('ptc', soort, naamval, getal, geslacht) voor deelwoorden,
    ('gerundivum'|'gerundium'|'supinum', ...) voor de rest.
    """
    tab = _WW[vervoeging]
    uit = {}

    def voeg(vorm, analyse):
        uit.setdefault(vorm, []).append(analyse)

    # --- persoonsvormen uit het presens-systeem
    for sleutel, (tijd, wijs, genus) in _WW_LABEL.items():
        if sleutel in _PERF:
            continue
        # Bij een deponens bestaan alleen de passieve vormen — met actieve betekenis.
        actief = genus == 'act'
        if deponens and actief:
            continue
        for i, einde in enumerate(tab[sleutel]):
            voeg(wortel + einde, ('pv', i % 3 + 1, 'ev' if i < 3 else 'mv',
                                  tijd, wijs, 'act' if deponens else genus))

    # --- perfectumstam (actief); deponentia vormen hun perfectum met het PPP
    if perf_stam and not deponens:
        for sleutel, uitgangen in _PERF.items():
            tijd, wijs, genus = _WW_LABEL[sleutel]
            for i, einde in enumerate(uitgangen):
                voeg(perf_stam + einde, ('pv', i % 3 + 1, 'ev' if i < 3 else 'mv',
                                         tijd, wijs, genus))
                for kort in _syncope(wortel, perf_stam, einde):
                    voeg(kort, ('pv', i % 3 + 1, 'ev' if i < 3 else 'mv',
                                tijd, wijs, genus))
        voeg(perf_stam + 'isse', ('inf', 'perf_act'))
        for kort in _syncope(wortel, perf_stam, 'isse'):
            voeg(kort, ('inf', 'perf_act'))

    # --- gebiedende wijs, infinitief, deelwoorden
    if deponens:
        voeg(wortel + tab['inf_p'], ('inf', 'praes_act'))
        # gebiedende wijs van een deponens = de passieve vormen: conare/conamini
        voeg(wortel + tab['praes_p'][1][:-3] + 're', ('imp', 'ev'))
        voeg(wortel + tab['praes_p'][4], ('imp', 'mv'))
    else:
        voeg(wortel + tab['imp'][0], ('imp', 'ev'))
        voeg(wortel + tab['imp'][1], ('imp', 'mv'))
        voeg(wortel + tab['inf'], ('inf', 'praes_act'))
        if sup_stam:
            voeg(wortel + tab['inf_p'], ('inf', 'praes_pass'))

    # tegenwoordig deelwoord (ook bij deponentia)
    for vorm, paren in _bnw_3(wortel + tab['ptc_stam'], nom_mv=wortel + tab['ptc'],
                              nom_o=wortel + tab['ptc']).items():
        for nv, getal, gsl in paren:
            voeg(vorm, ('ptc', 'praes', nv, getal, gsl))
    # ablatief ev. van een deelwoord is meestal -e, niet -i
    voeg(wortel + tab['ptc_stam'] + 'e', ('ptc', 'praes', 'abl', 'ev', None))

    # gerundivum en gerundium
    for vorm, paren in _bnw_12(wortel + tab['gerund']).items():
        for nv, getal, gsl in paren:
            voeg(vorm, ('gerundivum', nv, getal, gsl))
    for einde, nv in (('i', 'gen'), ('o', 'dat/abl'), ('um', 'acc')):
        voeg(wortel + tab['gerund'] + einde, ('gerundium', nv))

    # voltooid deelwoord (PPP), toekomend deelwoord, supinum
    if sup_stam:
        for vorm, paren in _bnw_12(sup_stam).items():
            for nv, getal, gsl in paren:
                voeg(vorm, ('ptc', 'perf', nv, getal, gsl))
        for vorm, paren in _bnw_12(sup_stam + 'ur').items():
            for nv, getal, gsl in paren:
                voeg(vorm, ('ptc', 'fut', nv, getal, gsl))
        voeg(sup_stam + 'um', ('supinum', None))
        voeg(sup_stam + 'u', ('supinum', None))
    return uit


def vorm_omschrijving(analyses):
    """Bundel alle lezingen van één werkwoordsvorm tot één leesbare zin.

    Deelwoorden worden per soort samengevoegd, zodat `parati` niet vier losse
    regels oplevert maar één: "voltooid deelwoord, genitief ev., of
    nominatief mv. mannelijk".
    """
    deelwoorden = {}
    volgorde = []
    overig = []
    for a in analyses:
        if a[0] == 'ptc' and a[2] is not None:
            if a[1] not in deelwoorden:
                deelwoorden[a[1]] = []
                volgorde.append(a[1])
            deelwoorden[a[1]].append((a[2], a[3], a[4]))
        else:
            lab = werkwoord_label(a)
            if lab and lab not in overig:
                overig.append(lab)
    delen = []
    for soort in volgorde:
        naam = {'praes': 'tegenwoordig deelwoord', 'perf': 'voltooid deelwoord',
                'fut': 'toekomend deelwoord'}[soort]
        delen.append(naam + ', ' + naamwoord_label(deelwoorden[soort], met_geslacht=True))
    return ' of '.join(delen + overig)


def werkwoord_label(analyse):
    """Analyse-tuple -> Nederlandse omschrijving."""
    soort = analyse[0]
    if soort == 'pv':
        _, pers, getal, tijd, wijs, genus = analyse
        s = PERSOON[pers] + ' ' + ('ev.' if getal == 'ev' else 'mv.') + ', ' + TIJD[tijd]
        if wijs == 'conj':
            s += ', aanvoegende wijs'
        if genus == 'pass':
            s += ', lijdende vorm'
        return s
    if soort == 'inf':
        return {'praes_act': 'onbepaalde wijs (infinitief)',
                'praes_pass': 'onbepaalde wijs, lijdende vorm',
                'perf_act': 'voltooide onbepaalde wijs'}[analyse[1]]
    if soort == 'imp':
        return 'gebiedende wijs ' + ('ev.' if analyse[1] == 'ev' else 'mv.')
    if soort == 'ptc':
        naam = {'praes': 'tegenwoordig deelwoord', 'perf': 'voltooid deelwoord',
                'fut': 'toekomend deelwoord'}[analyse[1]]
        if analyse[2] is None:
            return naam
        staart = _naamval_label([(analyse[2], analyse[3])])
        if analyse[4]:
            staart += ' ' + GESLACHT[analyse[4]]
        return naam + ', ' + staart
    if soort == 'gerundivum':
        return 'gerundivum (het te ...-en), ' + _naamval_label([(analyse[1], analyse[2])])
    if soort == 'gerundium':
        return 'gerundium (het ...-en), ' + analyse[1]
    if soort == 'supinum':
        return 'supinum'
    return ''


# ---------------------------------------------------------------------------
# Onregelmatige werkwoorden — expliciete vormtabellen
# ---------------------------------------------------------------------------
# `sum` en `eo` (en hun samenstellingen) zijn in 4 Ezra veruit de vaakst
# voorkomende werkwoorden; ze laten zich niet uit een wortel afleiden.

def _rij(uit, vormen, tijd, wijs, genus='act'):
    for i, vorm in enumerate(vormen):
        if not vorm:
            continue
        for v in vorm.split('|'):
            uit.setdefault(v, []).append(
                ('pv', i % 3 + 1, 'ev' if i < 3 else 'mv', tijd, wijs, genus))


def sum_paradigma(pre=''):
    """`sum, esse, fui` — met optioneel voorvoegsel (ad-, ab-, pro-, inter-).
    Het voorvoegsel wordt voor elke vorm geplakt; `possum` is te onregelmatig
    en staat daarom apart."""
    u = {}
    _rij(u, ['sum', 'es', 'est', 'sumus', 'estis', 'sunt'], 'praes', 'ind')
    _rij(u, ['eram', 'eras', 'erat', 'eramus', 'eratis', 'erant'], 'imperf', 'ind')
    _rij(u, ['ero', 'eris', 'erit', 'erimus', 'eritis', 'erunt'], 'fut', 'ind')
    _rij(u, ['sim', 'sis', 'sit', 'simus', 'sitis', 'sint'], 'praes', 'conj')
    _rij(u, ['essem', 'esses', 'esset', 'essemus', 'essetis', 'essent'], 'imperf', 'conj')
    _rij(u, ['fui', 'fuisti', 'fuit', 'fuimus', 'fuistis', 'fuerunt'], 'perf', 'ind')
    _rij(u, ['fueram', 'fueras', 'fuerat', 'fueramus', 'fueratis', 'fuerant'], 'plqp', 'ind')
    _rij(u, ['fuero', 'fueris', 'fuerit', 'fuerimus', 'fueritis', 'fuerint'], 'futex', 'ind')
    _rij(u, ['fuerim', 'fueris', 'fuerit', 'fuerimus', 'fueritis', 'fuerint'], 'perf', 'conj')
    _rij(u, ['fuissem', 'fuisses', 'fuisset', 'fuissemus', 'fuissetis', 'fuissent'], 'plqp', 'conj')
    u.setdefault('esse', []).append(('inf', 'praes_act'))
    u.setdefault('fuisse', []).append(('inf', 'perf_act'))
    u.setdefault('es', []).append(('imp', 'ev'))
    u.setdefault('este', []).append(('imp', 'mv'))
    u.setdefault('esto', []).append(('imp', 'ev'))
    u.setdefault('estote', []).append(('imp', 'mv'))
    for vorm, paren in _bnw_12('futur').items():
        for nv, getal, gsl in paren:
            u.setdefault(vorm, []).append(('ptc', 'fut', nv, getal, gsl))
    if not pre:
        return u
    return {pre + k: v for k, v in u.items()}


def possum_paradigma():
    u = {}
    _rij(u, ['possum', 'potes', 'potest', 'possumus', 'potestis', 'possunt'], 'praes', 'ind')
    _rij(u, ['poteram', 'poteras', 'poterat', 'poteramus', 'poteratis', 'poterant'], 'imperf', 'ind')
    _rij(u, ['potero', 'poteris', 'poterit', 'poterimus', 'poteritis', 'poterunt'], 'fut', 'ind')
    _rij(u, ['possim', 'possis', 'possit', 'possimus', 'possitis', 'possint'], 'praes', 'conj')
    _rij(u, ['possem', 'posses', 'posset', 'possemus', 'possetis', 'possent'], 'imperf', 'conj')
    _rij(u, ['potui', 'potuisti', 'potuit', 'potuimus', 'potuistis', 'potuerunt'], 'perf', 'ind')
    _rij(u, ['potueram', 'potueras', 'potuerat', 'potueramus', 'potueratis', 'potuerant'], 'plqp', 'ind')
    _rij(u, ['potuero', 'potueris', 'potuerit', 'potuerimus', 'potueritis', 'potuerint'], 'futex', 'ind')
    _rij(u, ['potuerim', 'potueris', 'potuerit', 'potuerimus', 'potueritis', 'potuerint'], 'perf', 'conj')
    _rij(u, ['potuissem', 'potuisses', 'potuisset', 'potuissemus', 'potuissetis', 'potuissent'], 'plqp', 'conj')
    u.setdefault('posse', []).append(('inf', 'praes_act'))
    u.setdefault('potuisse', []).append(('inf', 'perf_act'))
    for vorm, paren in _bnw_3('potent', nom_mv='potens', nom_o='potens').items():
        for nv, getal, gsl in paren:
            u.setdefault(vorm, []).append(('ptc', 'praes', nv, getal, gsl))
    return u


def eo_paradigma(pre=''):
    """`eo, ire, ii/ivi, itum` — gaan; ook voor exeo, transeo, pereo enz."""
    u = {}
    _rij(u, ['eo', 'is', 'it', 'imus', 'itis', 'eunt'], 'praes', 'ind')
    _rij(u, ['ibam', 'ibas', 'ibat', 'ibamus', 'ibatis', 'ibant'], 'imperf', 'ind')
    # Late nevenvorm naar de 4e vervoeging: `exiebat` naast `exibat`.
    _rij(u, ['iebam', 'iebas', 'iebat', 'iebamus', 'iebatis', 'iebant'], 'imperf', 'ind')
    _rij(u, ['ibo', 'ibis', 'ibit', 'ibimus', 'ibitis', 'ibunt'], 'fut', 'ind')
    # Laat-Latijnse toekomende tijd naar het model van de 4e vervoeging; 4 Ezra
    # heeft naast `transibunt` ook `transient`, naast `exibit` ook `exiet`.
    _rij(u, ['iam', 'ies', 'iet', 'iemus', 'ietis', 'ient'], 'fut', 'ind')
    _rij(u, ['eam', 'eas', 'eat', 'eamus', 'eatis', 'eant'], 'praes', 'conj')
    _rij(u, ['irem', 'ires', 'iret', 'iremus', 'iretis', 'irent'], 'imperf', 'conj')
    _rij(u, ['ii|ivi', 'isti|ivisti|iisti', 'iit|ivit', 'iimus|ivimus',
             'istis|ivistis', 'ierunt|iverunt'], 'perf', 'ind')
    _rij(u, ['ieram|iveram', 'ieras', 'ierat|iverat', 'ieramus', 'ieratis', 'ierant'], 'plqp', 'ind')
    _rij(u, ['iero', 'ieris', 'ierit', 'ierimus', 'ieritis', 'ierint'], 'futex', 'ind')
    _rij(u, ['ierim', 'ieris', 'ierit', 'ierimus', 'ieritis', 'ierint'], 'perf', 'conj')
    _rij(u, ['issem|ivissem', 'isses', 'isset|ivisset', 'issemus', 'issetis', 'issent'], 'plqp', 'conj')
    u.setdefault('ire', []).append(('inf', 'praes_act'))
    u.setdefault('isse', []).append(('inf', 'perf_act'))
    u.setdefault('i', []).append(('imp', 'ev'))
    u.setdefault('ite', []).append(('imp', 'mv'))
    for vorm, paren in _bnw_3('eunt', nom_mv='iens', nom_o='iens').items():
        for nv, getal, gsl in paren:
            u.setdefault(vorm, []).append(('ptc', 'praes', nv, getal, gsl))
    for vorm, paren in _bnw_12('itur').items():
        for nv, getal, gsl in paren:
            u.setdefault(vorm, []).append(('ptc', 'fut', nv, getal, gsl))
    if not pre:
        return u
    return {pre + k: v for k, v in u.items()}


def fero_paradigma(pre=''):
    """`fero, ferre, tuli, latum` — dragen, brengen."""
    u = {}
    _rij(u, ['fero', 'fers', 'fert', 'ferimus', 'fertis', 'ferunt'], 'praes', 'ind')
    _rij(u, ['ferebam', 'ferebas', 'ferebat', 'ferebamus', 'ferebatis', 'ferebant'], 'imperf', 'ind')
    _rij(u, ['feram', 'feres', 'feret', 'feremus', 'feretis', 'ferent'], 'fut', 'ind')
    _rij(u, ['feram', 'feras', 'ferat', 'feramus', 'feratis', 'ferant'], 'praes', 'conj')
    _rij(u, ['ferrem', 'ferres', 'ferret', 'ferremus', 'ferretis', 'ferrent'], 'imperf', 'conj')
    _rij(u, ['feror', 'ferris', 'fertur', 'ferimur', 'ferimini', 'feruntur'], 'praes', 'ind', 'pass')
    _rij(u, ['ferebar', 'ferebaris', 'ferebatur', 'ferebamur', 'ferebamini', 'ferebantur'],
         'imperf', 'ind', 'pass')
    _rij(u, ['tuli', 'tulisti', 'tulit', 'tulimus', 'tulistis', 'tulerunt'], 'perf', 'ind')
    _rij(u, ['tuleram', 'tuleras', 'tulerat', 'tuleramus', 'tuleratis', 'tulerant'], 'plqp', 'ind')
    _rij(u, ['tulero', 'tuleris', 'tulerit', 'tulerimus', 'tuleritis', 'tulerint'], 'futex', 'ind')
    _rij(u, ['tulerim', 'tuleris', 'tulerit', 'tulerimus', 'tuleritis', 'tulerint'], 'perf', 'conj')
    _rij(u, ['tulissem', 'tulisses', 'tulisset', 'tulissemus', 'tulissetis', 'tulissent'],
         'plqp', 'conj')
    u.setdefault('ferre', []).append(('inf', 'praes_act'))
    u.setdefault('ferri', []).append(('inf', 'praes_pass'))
    u.setdefault('fer', []).append(('imp', 'ev'))
    u.setdefault('ferte', []).append(('imp', 'mv'))
    for vorm, paren in _bnw_3('ferent', nom_mv='ferens', nom_o='ferens').items():
        for nv, getal, gsl in paren:
            u.setdefault(vorm, []).append(('ptc', 'praes', nv, getal, gsl))
    for vorm, paren in _bnw_12('lat').items():
        for nv, getal, gsl in paren:
            u.setdefault(vorm, []).append(('ptc', 'perf', nv, getal, gsl))
    if not pre:
        return u
    return {pre + k: v for k, v in u.items()}


def volo_paradigma(soort='volo'):
    """`volo/nolo, velle/nolle, volui/nolui` — willen / niet willen."""
    u = {}
    if soort == 'volo':
        _rij(u, ['volo', 'vis', 'vult', 'volumus', 'vultis', 'volunt'], 'praes', 'ind')
        _rij(u, ['volebam', 'volebas', 'volebat', 'volebamus', 'volebatis', 'volebant'],
             'imperf', 'ind')
        _rij(u, ['volam', 'voles', 'volet', 'volemus', 'voletis', 'volent'], 'fut', 'ind')
        _rij(u, ['velim', 'velis', 'velit', 'velimus', 'velitis', 'velint'], 'praes', 'conj')
        _rij(u, ['vellem', 'velles', 'vellet', 'vellemus', 'velletis', 'vellent'], 'imperf', 'conj')
        stam, inf = 'volu', 'velle'
        ptc, ptcs = 'volens', 'volent'
    else:
        _rij(u, ['nolo', 'non vis', 'non vult', 'nolumus', 'non vultis', 'nolunt'], 'praes', 'ind')
        _rij(u, ['nolebam', 'nolebas', 'nolebat', 'nolebamus', 'nolebatis', 'nolebant'],
             'imperf', 'ind')
        _rij(u, ['nolam', 'noles', 'nolet', 'nolemus', 'noletis', 'nolent'], 'fut', 'ind')
        _rij(u, ['nolim', 'nolis', 'nolit', 'nolimus', 'nolitis', 'nolint'], 'praes', 'conj')
        _rij(u, ['nollem', 'nolles', 'nollet', 'nollemus', 'nolletis', 'nollent'], 'imperf', 'conj')
        u.setdefault('noli', []).append(('imp', 'ev'))
        u.setdefault('nolite', []).append(('imp', 'mv'))
        stam, inf = 'nolu', 'nolle'
        ptc, ptcs = 'nolens', 'nolent'
    for sleutel, uitgangen in _PERF.items():
        tijd, wijs, genus = _WW_LABEL[sleutel]
        _rij(u, [stam + e for e in uitgangen], tijd, wijs)
    u.setdefault(inf, []).append(('inf', 'praes_act'))
    u.setdefault(stam + 'isse', []).append(('inf', 'perf_act'))
    for vorm, paren in _bnw_3(ptcs, nom_mv=ptc, nom_o=ptc).items():
        for nv, getal, gsl in paren:
            u.setdefault(vorm, []).append(('ptc', 'praes', nv, getal, gsl))
    return u


def fio_paradigma():
    """`fio, fieri, factus sum` — worden, gebeuren (lijdende vorm van facio)."""
    u = {}
    _rij(u, ['fio', 'fis', 'fit', 'fimus', 'fitis', 'fiunt'], 'praes', 'ind')
    _rij(u, ['fiebam', 'fiebas', 'fiebat', 'fiebamus', 'fiebatis', 'fiebant'], 'imperf', 'ind')
    _rij(u, ['fiam', 'fies', 'fiet', 'fiemus', 'fietis', 'fient'], 'fut', 'ind')
    _rij(u, ['fiam', 'fias', 'fiat', 'fiamus', 'fiatis', 'fiant'], 'praes', 'conj')
    _rij(u, ['fierem', 'fieres', 'fieret', 'fieremus', 'fieretis', 'fierent'], 'imperf', 'conj')
    u.setdefault('fieri', []).append(('inf', 'praes_act'))
    u.setdefault('fi', []).append(('imp', 'ev'))
    u.setdefault('fite', []).append(('imp', 'mv'))
    return u


# ---------------------------------------------------------------------------
# Hulp: samenvoegen van analyses tot één leesbare zin
# ---------------------------------------------------------------------------

def naamwoord_label(paren, met_geslacht=False):
    """[(nv, getal[, geslacht[, trap]])] -> leesbare Nederlandse omschrijving."""
    trappen = {}
    volgorde = []
    for p in paren:
        trap = p[3] if len(p) > 3 else 'pos'
        if trap not in trappen:
            trappen[trap] = []
            volgorde.append(trap)
        trappen[trap].append(p)
    stukken = []
    for trap in volgorde:
        groep = trappen[trap]
        if trap == 'bijw':
            stukken.append('bijwoord')
            continue
        if met_geslacht:
            per_gsl = {}
            gvolg = []
            for p in groep:
                g = p[2] if len(p) > 2 else None
                if g not in per_gsl:
                    per_gsl[g] = []
                    gvolg.append(g)
                per_gsl[g].append((p[0], p[1]))
            delen = []
            for g in gvolg:
                d = _naamval_label(per_gsl[g])
                if g:
                    d += ' ' + GESLACHT[g]
                delen.append(d)
            s = ', of '.join(delen)
        else:
            s = _naamval_label([(p[0], p[1]) for p in groep])
        if trap == 'comp':
            s = 'vergrotende trap, ' + s
        elif trap == 'sup':
            s = 'overtreffende trap, ' + s
        stukken.append(s)
    return ', of '.join(stukken)
