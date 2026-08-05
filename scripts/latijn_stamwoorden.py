#!/usr/bin/env python3
"""Latijnse stamwoorden bij 4 Ezra — de woordenschat achter de verrijking.

Elk stamwoord staat hier één keer, met woordsoort, stamvormen en genummerde
betekenissen. `scripts/latijn_morfologie.py` bouwt daar de volledige paradigma's
van, zodat elke tekstvorm in `data/lexicon-latijn.json` (`filii`, `filiorum`,
`filios`, …) aan zijn stamwoord geknoopt kan worden.

Bronnen — alles publiek domein:
* Lewis & Short, *A Latin Dictionary* (1879) — woordsoort, stamvormen en de
  volgorde van de betekenissen; de deelverzameling die 4 Ezra raakt staat in
  `data/lexicon-lewis-short-4ezra.json`.
* Standaard Latijnse schoolgrammatica voor de verbuigings- en
  vervoegingstabellen (feiten, niet auteursrechtelijk beschermd).
* De Latijnse tekst van 4 Ezra zelf (`data/4ezra/*.json`, veld `grondtekst`)
  voor de opmerkingen over het gebruik ter plaatse.

Betekenissen zijn gescheiden met ` | `, van grondbetekenis naar afgeleide.
`toel=` is een korte toelichting (afwijkend Vulgaat-gebruik, bijzonderheid in
4 Ezra); `verw=` zijn verwante woorden.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import latijn_morfologie as M       # noqa: E402

STAMWOORDEN = {}     # kopwoord -> dict met woordsoort, stamvormen, betekenissen, vormen


def _voeg(kop, ws, stamvormen, bet, vormen, toel=None, verw=None, prio=0):
    if kop in STAMWOORDEN:
        raise ValueError('dubbel stamwoord: ' + kop)
    STAMWOORDEN[kop] = {
        'kop': kop, 'woordsoort': ws, 'stamvormen': stamvormen,
        'betekenissen': [b.strip() for b in bet.split('|') if b.strip()],
        'vormen': vormen, 'toelichting': toel, 'verwant': verw or [],
        'prio': prio,      # hoger wint bij vormen die bij meer stamwoorden passen
    }


_WS_ZN = {'m': 'zelfstandig naamwoord (mannelijk)', 'v': 'zelfstandig naamwoord (vrouwelijk)',
          'o': 'zelfstandig naamwoord (onzijdig)', 'mv': 'zelfstandig naamwoord (m./v.)'}


def N(kop, bet, i=False, toel=None, verw=None, alleen=None, prio=0, extra=None):
    """Zelfstandig naamwoord: N('filius, filii, m.', 'zoon | nakomeling').

    De verbuigingsklasse volgt uit nominatief + genitief; `i=True` markeert een
    i-stam van de 3e klasse (genitief meervoud op -ium).
    """
    delen = [d.strip() for d in kop.split(',')]
    nom, gen = delen[0], delen[1]
    gsl = delen[2].rstrip('.') if len(delen) > 2 else 'm'
    if gen.endswith('arum'):           # meervoudswoord: tenebrae, tenebrarum
        kl, stam, alleen = '1', gen[:-4], 'mv'
    elif gen.endswith('orum'):
        kl, stam, alleen = ('2o' if gsl == 'o' else '2'), gen[:-4], 'mv'
    elif gen.endswith('ae'):
        kl, stam = '1', gen[:-2]
    elif gen.endswith('us') and not nom.endswith('er'):
        kl, stam = ('4o' if gsl == 'o' else '4'), gen[:-2]
    elif nom.endswith('es') and gen.endswith('ei'):
        kl, stam = '5', gen[:-2]
    elif gen.endswith('is'):
        stam = gen[:-2]
        kl = ('3oi' if i else '3o') if gsl == 'o' else ('3i' if i else '3')
    elif gen.endswith('i'):
        kl, stam = ('2o' if gsl == 'o' else '2'), gen[:-1]
    else:
        raise ValueError('onbekende verbuiging: ' + kop)
    ruw = M.zelfstandig(nom, stam, kl, alleen=alleen)
    vormen = {v: M.naamwoord_label(p) for v, p in ruw.items()}
    vormen.update(extra or {})
    _voeg(nom, _WS_ZN.get(gsl, _WS_ZN['m']), nom + ', ' + gen + ', ' + gsl + '.',
          bet, vormen, toel, verw, prio)


def A(kop, bet, toel=None, verw=None, comp=None, sup=None, bijw=None, prio=0, extra=None):
    """Bijvoeglijk naamwoord 1e/2e klasse: A('bonus, bona, bonum', '…')."""
    delen = [d.strip() for d in kop.split(',')]
    stam = delen[1][:-1]           # vrouwelijke vorm min de -a geeft altijd de stam
    ruw = M.bijvoeglijk(stam, '12', comp_stam=comp, sup_stam=sup, bijw=bijw)
    vormen = {v: M.naamwoord_label(p, met_geslacht=True) for v, p in ruw.items()}
    if delen[0] != stam + 'us':     # type niger/nigra of noster/nostra
        vormen[delen[0]] = 'nominatief/vocatief ev. mannelijk'
    vormen.update(extra or {})
    _voeg(delen[0], 'bijvoeglijk naamwoord', kop, bet, vormen, toel, verw, prio)


def A3(kop, bet, een=False, toel=None, verw=None, comp=None, sup=None, bijw=None, prio=0,
       extra=None):
    """Bijvoeglijk naamwoord 3e klasse: A3('omnis, omne', …) of, met één uitgang,
    A3('felix, felicis', …, een=True)."""
    delen = [d.strip() for d in kop.split(',')]
    if een:
        stam, nom_mv, nom_o = delen[1][:-2], delen[0], delen[0]
    else:
        stam, nom_mv, nom_o = delen[0][:-2], delen[0], delen[1]
    ruw = M.bijvoeglijk(stam, '3', nom_mv=nom_mv, nom_o=nom_o,
                        comp_stam=comp, sup_stam=sup, bijw=bijw)
    vormen = {v: M.naamwoord_label(p, met_geslacht=True) for v, p in ruw.items()}
    vormen.update(extra or {})
    _voeg(delen[0], 'bijvoeglijk naamwoord', kop, bet, vormen, toel, verw, prio)


def V(kop, bet, k='1', toel=None, verw=None, prio=0, extra=None, naam=None):
    """Werkwoord: V('facio, facere, feci, factum', '…', k='3io').

    `k` is de vervoeging: '1', '2', '3', '3io', '4', met een d erachter voor
    deponentia ('1d', '3d', …).
    """
    delen = [d.strip() for d in kop.split(',')]
    dep = k.endswith('d')
    basis = k[:-1] if dep else k
    inf = delen[1]
    if dep:
        af = {'1': 3, '2': 3, '3': 1, '3io': 1, '4': 3}[basis]
        wortel = inf[:-af]
        perf_stam = None
        sup_stam = delen[2].split()[0][:-2] if len(delen) > 2 else None
    else:
        wortel = inf[:-3]
        perf_stam = delen[2][:-1] if len(delen) > 2 and delen[2] else None
        sup_stam = delen[3][:-2] if len(delen) > 3 and delen[3] else None
    ruw = M.werkwoord(wortel, basis, perf_stam, sup_stam, deponens=dep)
    vormen = {v: M.vorm_omschrijving(ana) for v, ana in ruw.items()}
    vormen.update(extra or {})
    _voeg(naam or delen[0], 'werkwoord' + (' (deponens)' if dep else ''), kop, bet,
          vormen, toel, verw, prio)


def I(kop, ws, bet, extra=None, toel=None, verw=None, prio=0):
    """Onverbuigbaar woord (voorzetsel, voegwoord, bijwoord, tussenwerpsel)."""
    vormen = {kop: ws}
    for v in (extra or []):
        vormen[v] = ws
    _voeg(kop, ws, kop, bet, vormen, toel, verw, prio)


def X(kop, ws, stamvormen, bet, vormen, toel=None, verw=None, prio=0):
    """Vrije vorm: expliciete vormtabel {vorm: omschrijving}. Voor voornaamwoorden
    en al te onregelmatige woorden."""
    _voeg(kop, ws, stamvormen, bet, vormen, toel, verw, prio)


def W(kop, ws, stamvormen, bet, paradigma, toel=None, verw=None, prio=0):
    """Werkwoord met een kant-en-klaar paradigma uit latijn_morfologie."""
    vormen = {v: M.vorm_omschrijving(ana) for v, ana in paradigma.items()}
    _voeg(kop, ws, stamvormen, bet, vormen, toel, verw, prio)


# ===========================================================================
# 1. Voornaamwoorden
# ===========================================================================

def _vnw(rijen):
    """rijen = [(vorm, omschrijving), …]; gelijke vormen worden samengevoegd."""
    uit = {}
    for vorm, oms in rijen:
        if vorm in uit:
            if oms not in uit[vorm]:
                uit[vorm] += ', of ' + oms
        else:
            uit[vorm] = oms
    return uit


X('qui', 'betrekkelijk voornaamwoord', 'qui, quae, quod',
  'die, dat, wie, wat | (na een punt, aan het begin van een zin) en hij, en dat '
  '| (met aanvoegende wijs) zodat hij, opdat hij',
  _vnw([('qui', 'nominatief ev. mannelijk, of nominatief mv. mannelijk'),
        ('quae', 'nominatief ev. vrouwelijk, of nominatief/accusatief mv. onzijdig, '
                 'of nominatief mv. vrouwelijk'),
        ('quod', 'nominatief/accusatief ev. onzijdig'),
        ('cuius', 'genitief ev. (alle geslachten)'), ('cui', 'datief ev. (alle geslachten)'),
        ('quem', 'accusatief ev. mannelijk'), ('quam', 'accusatief ev. vrouwelijk'),
        ('quo', 'ablatief ev. mannelijk/onzijdig'), ('qua', 'ablatief ev. vrouwelijk'),
        ('quorum', 'genitief mv. mannelijk/onzijdig'), ('quarum', 'genitief mv. vrouwelijk'),
        ('quibus', 'datief/ablatief mv.'), ('quos', 'accusatief mv. mannelijk'),
        ('quas', 'accusatief mv. vrouwelijk'), ('quis', 'datief/ablatief mv. (nevenvorm van quibus)')]),
  toel='In 4 Ezra begint een nieuwe zin vaak met een betrekkelijke aansluiting '
       '("Et respondi et dixi… qui…"); daar is `qui` het best als "en hij" te vertalen.')

X('quis', 'vragend/onbepaald voornaamwoord', 'quis, quid',
  'wie? wat? | (na si, nisi, ne, num) iemand, iets',
  _vnw([('quis', 'nominatief ev. mannelijk/vrouwelijk'), ('quid', 'nominatief/accusatief ev. onzijdig'),
        ('cuius', 'genitief ev.'), ('cui', 'datief ev.'), ('quem', 'accusatief ev. mannelijk'),
        ('quo', 'ablatief ev. mannelijk/onzijdig'), ('qua', 'ablatief ev. vrouwelijk')]),
  toel='`quid` staat in 4 Ezra ook los als "waarom?".', prio=-1)

X('hic', 'aanwijzend voornaamwoord', 'hic, haec, hoc',
  'deze, dit (dicht bij de spreker) | de hier bedoelde, de zojuist genoemde | '
  'de tegenwoordige (bv. hoc saeculum, deze wereld)',
  _vnw([('hic', 'nominatief ev. mannelijk'), ('haec', 'nominatief ev. vrouwelijk, '
                                                      'of nominatief/accusatief mv. onzijdig'),
        ('hoc', 'nominatief/accusatief ev. onzijdig, of ablatief ev. mannelijk/onzijdig'),
        ('huius', 'genitief ev.'), ('huic', 'datief ev.'), ('hunc', 'accusatief ev. mannelijk'),
        ('hanc', 'accusatief ev. vrouwelijk'), ('hac', 'ablatief ev. vrouwelijk'),
        ('hi', 'nominatief mv. mannelijk'), ('hii', 'nominatief mv. mannelijk (late spelling)'),
        ('hae', 'nominatief mv. vrouwelijk'), ('horum', 'genitief mv. mannelijk/onzijdig'),
        ('harum', 'genitief mv. vrouwelijk'), ('his', 'datief/ablatief mv.'),
        ('hos', 'accusatief mv. mannelijk'), ('has', 'accusatief mv. vrouwelijk')]),
  toel='"hoc saeculum" tegenover "futurum saeculum" is in 4 Ezra een vaste tegenstelling: '
       'deze wereld tegenover de komende.')

X('ille', 'aanwijzend voornaamwoord', 'ille, illa, illud',
  'die, dat (daarginds) | hij, zij, het (als persoonlijk voornaamwoord) | de bekende, de befaamde',
  _vnw([('ille', 'nominatief ev. mannelijk'), ('illa', 'nominatief/ablatief ev. vrouwelijk, '
                                                       'of nominatief/accusatief mv. onzijdig'),
        ('illud', 'nominatief/accusatief ev. onzijdig'), ('illius', 'genitief ev.'),
        ('illi', 'datief ev., of nominatief mv. mannelijk'),
        ('illum', 'accusatief ev. mannelijk'), ('illam', 'accusatief ev. vrouwelijk'),
        ('illo', 'ablatief ev. mannelijk/onzijdig'), ('illae', 'nominatief mv. vrouwelijk'),
        ('illorum', 'genitief mv. mannelijk/onzijdig'), ('illarum', 'genitief mv. vrouwelijk'),
        ('illis', 'datief/ablatief mv.'), ('illos', 'accusatief mv. mannelijk'),
        ('illas', 'accusatief mv. vrouwelijk')]),
  toel='In het late Latijn van 4 Ezra verzwakt `ille` tot een gewoon persoonlijk '
       'voornaamwoord — precies de weg waarlangs het Romaanse lidwoord (il, el, le) ontstond.')

X('iste', 'aanwijzend voornaamwoord', 'iste, ista, istud',
  'die van jou, die daar | die, deze (zonder bijklank, laat-Latijn)',
  _vnw([('iste', 'nominatief ev. mannelijk'), ('ista', 'nominatief/ablatief ev. vrouwelijk, '
                                                       'of nominatief/accusatief mv. onzijdig'),
        ('istud', 'nominatief/accusatief ev. onzijdig'), ('istius', 'genitief ev.'),
        ('isti', 'datief ev., of nominatief mv. mannelijk'), ('istum', 'accusatief ev. mannelijk'),
        ('istam', 'accusatief ev. vrouwelijk'), ('isto', 'ablatief ev. mannelijk/onzijdig'),
        ('istae', 'nominatief mv. vrouwelijk'), ('istorum', 'genitief mv. mannelijk/onzijdig'),
        ('istis', 'datief/ablatief mv.'), ('istos', 'accusatief mv. mannelijk'),
        ('istas', 'accusatief mv. vrouwelijk')]))

X('is', 'aanwijzend/persoonlijk voornaamwoord', 'is, ea, id',
  'hij, zij, het | die, dat | zo iemand, zodanig (vooruitwijzend naar qui of ut)',
  _vnw([('is', 'nominatief ev. mannelijk'), ('ea', 'nominatief/ablatief ev. vrouwelijk, '
                                                   'of nominatief/accusatief mv. onzijdig'),
        ('id', 'nominatief/accusatief ev. onzijdig'), ('eius', 'genitief ev.'),
        ('ei', 'datief ev., of nominatief mv. mannelijk'), ('eum', 'accusatief ev. mannelijk'),
        ('eam', 'accusatief ev. vrouwelijk'), ('eo', 'ablatief ev. mannelijk/onzijdig'),
        ('eae', 'nominatief mv. vrouwelijk'), ('eorum', 'genitief mv. mannelijk/onzijdig'),
        ('earum', 'genitief mv. vrouwelijk'), ('eis', 'datief/ablatief mv.'),
        ('iis', 'datief/ablatief mv. (nevenvorm)'), ('eos', 'accusatief mv. mannelijk'),
        ('eas', 'accusatief mv. vrouwelijk')]))

X('ipse', 'nadrukkelijk voornaamwoord', 'ipse, ipsa, ipsum',
  'zelf, in eigen persoon | juist die, nu juist | (versterkend bij een ander voornaamwoord) zelfs',
  _vnw([('ipse', 'nominatief ev. mannelijk'), ('ipsa', 'nominatief/ablatief ev. vrouwelijk, '
                                                       'of nominatief/accusatief mv. onzijdig'),
        ('ipsum', 'nominatief/accusatief ev. onzijdig, of accusatief ev. mannelijk'),
        ('ipsud', 'nominatief/accusatief ev. onzijdig (late nevenvorm van ipsum)'),
        ('ipsius', 'genitief ev.'), ('ipsi', 'datief ev., of nominatief mv. mannelijk'),
        ('ipsam', 'accusatief ev. vrouwelijk'), ('ipso', 'ablatief ev. mannelijk/onzijdig'),
        ('ipsae', 'nominatief mv. vrouwelijk'), ('ipsorum', 'genitief mv. mannelijk/onzijdig'),
        ('ipsarum', 'genitief mv. vrouwelijk'), ('ipsis', 'datief/ablatief mv.'),
        ('ipsos', 'accusatief mv. mannelijk'), ('ipsas', 'accusatief mv. vrouwelijk')]))

X('idem', 'aanwijzend voornaamwoord', 'idem, eadem, idem', 'dezelfde, hetzelfde | eveneens',
  _vnw([('idem', 'nominatief ev. mannelijk, of nominatief/accusatief ev. onzijdig'),
        ('eadem', 'nominatief/ablatief ev. vrouwelijk, of nominatief/accusatief mv. onzijdig'),
        ('eiusdem', 'genitief ev.'), ('eidem', 'datief ev.'), ('eundem', 'accusatief ev. mannelijk'),
        ('eandem', 'accusatief ev. vrouwelijk'), ('eodem', 'ablatief ev. mannelijk/onzijdig'),
        ('eorundem', 'genitief mv. mannelijk/onzijdig'), ('isdem', 'datief/ablatief mv.'),
        ('eisdem', 'datief/ablatief mv.')]))

X('ego', 'persoonlijk voornaamwoord', 'ego, mei, mihi, me', 'ik | (meervoud nos) wij',
  _vnw([('ego', 'nominatief ev. — ik'), ('mei', 'genitief ev. — van mij'),
        ('mihi', 'datief ev. — aan mij, voor mij'), ('michi', 'datief ev. (middeleeuwse spelling)'),
        ('me', 'accusatief/ablatief ev. — mij'), ('mecum', 'met mij (me + cum)'),
        ('nos', 'nominatief/accusatief mv. — wij, ons'), ('nostri', 'genitief mv. — van ons'),
        ('nostrum', 'genitief mv. — van ons (deelgenitief)'),
        ('nobis', 'datief/ablatief mv. — aan ons, door ons'),
        ('nobiscum', 'met ons'), ('nobismet', 'datief/ablatief mv. met versterkend -met — aan onszelf')]),
  prio=-1,
  toel='In 4 Ezra spreekt Ezra zelf; het nadrukkelijke `ego` markeert steeds de wisseling '
       'tussen de ziener en de engel.')

X('tu', 'persoonlijk voornaamwoord', 'tu, tui, tibi, te', 'gij, jij | (meervoud vos) gij allen',
  _vnw([('tu', 'nominatief ev. — gij'), ('tui', 'genitief ev. — van u'),
        ('tibi', 'datief ev. — aan u'), ('tibimet', 'datief ev. met versterkend -met — aan uzelf'),
        ('te', 'accusatief/ablatief ev. — u'), ('temet', 'accusatief ev. met versterkend -met — uzelf'),
        ('tecum', 'met u'), ('vos', 'nominatief/accusatief mv. — gij allen, u'),
        ('vestri', 'genitief mv. — van u'), ('vestrum', 'genitief mv. — van u (deelgenitief)'),
        ('vobis', 'datief/ablatief mv. — aan u'), ('vobiscum', 'met u')]), prio=-1)

X('sui', 'wederkerend voornaamwoord', 'sui, sibi, se', 'zich, zichzelf | hem-, haar-, henzelf',
  _vnw([('sui', 'genitief — van zich'), ('sibi', 'datief — aan zich'),
        ('sibimet', 'datief met versterkend -met — aan zichzelf'),
        ('se', 'accusatief/ablatief — zich'), ('sese', 'accusatief (verdubbeld) — zichzelf'),
        ('semet', 'accusatief met versterkend -met — zichzelf'), ('secum', 'met zich')]))

A('meus, mea, meum', 'mijn | van mij', comp=False, sup=False,
  toel='De vocatief mannelijk is onregelmatig: `mi` (mijn zoon = fili mi).')
A('tuus, tua, tuum', 'uw, jouw | van u', comp=False, sup=False)
A('suus, sua, suum', 'zijn, haar, hun (terugwijzend naar het onderwerp) | eigen',
  comp=False, sup=False, prio=-1)
A('noster, nostra, nostrum', 'ons, onze | van ons', comp=False, sup=False)
A('vester, vestra, vestrum', 'uw, van u allen', comp=False, sup=False)

X('quidam', 'onbepaald voornaamwoord', 'quidam, quaedam, quoddam',
  'een zekere, iemand | sommige, enkele (in het meervoud)',
  _vnw([('quidam', 'nominatief ev. mannelijk'), ('quaedam', 'nominatief ev. vrouwelijk, '
                                                            'of nominatief/accusatief mv. onzijdig'),
        ('quoddam', 'nominatief/accusatief ev. onzijdig'), ('quendam', 'accusatief ev. mannelijk'),
        ('quandam', 'accusatief ev. vrouwelijk'), ('quorumdam', 'genitief mv. mannelijk/onzijdig'),
        ('quibusdam', 'datief/ablatief mv.'), ('quosdam', 'accusatief mv. mannelijk'),
        ('quasdam', 'accusatief mv. vrouwelijk')]))

X('quisquam', 'onbepaald voornaamwoord', 'quisquam, quicquam',
  'iemand (in ontkennende en vragende zinnen) | ook maar iemand',
  _vnw([('quisquam', 'nominatief ev.'), ('quicquam', 'nominatief/accusatief ev. onzijdig'),
        ('quidquam', 'nominatief/accusatief ev. onzijdig'), ('cuiquam', 'datief ev.'),
        ('quemquam', 'accusatief ev. mannelijk')]))

X('quisque', 'onbepaald voornaamwoord', 'quisque, quaeque, quodque',
  'ieder afzonderlijk, elk',
  _vnw([('quisque', 'nominatief ev. mannelijk'), ('quique', 'nominatief mv. mannelijk'),
        ('quaeque', 'nominatief ev. vrouwelijk'), ('cuique', 'datief ev.'),
        ('unusquisque', 'nominatief ev. mannelijk — ieder afzonderlijk'),
        ('unaquaque', 'ablatief ev. vrouwelijk — bij elke afzonderlijke')]))

X('aliquis', 'onbepaald voornaamwoord', 'aliquis, aliqua, aliquid',
  'iemand, iets | een of andere, enige',
  _vnw([('aliquis', 'nominatief ev. mannelijk'), ('aliqui', 'nominatief ev. mannelijk (bijvoeglijk)'),
        ('aliqua', 'nominatief ev. vrouwelijk, of nominatief/accusatief mv. onzijdig'),
        ('aliquae', 'nominatief mv. vrouwelijk'), ('aliquid', 'nominatief/accusatief ev. onzijdig'),
        ('aliquod', 'nominatief/accusatief ev. onzijdig (bijvoeglijk)'),
        ('alicuius', 'genitief ev.'), ('alicui', 'datief ev.'),
        ('aliquem', 'accusatief ev. mannelijk'), ('aliquam', 'accusatief ev. vrouwelijk')]))

X('alius', 'onbepaald voornaamwoord', 'alius, alia, aliud', 'een ander | de een … de ander',
  _vnw([('alius', 'nominatief ev. mannelijk'), ('alia', 'nominatief/ablatief ev. vrouwelijk, '
                                                        'of nominatief/accusatief mv. onzijdig'),
        ('aliud', 'nominatief/accusatief ev. onzijdig'), ('alii', 'datief ev., of nominatief mv. mannelijk'),
        ('alium', 'accusatief ev. mannelijk'), ('aliam', 'accusatief ev. vrouwelijk'),
        ('alio', 'ablatief ev. mannelijk/onzijdig'), ('alias', 'accusatief mv. vrouwelijk'),
        ('aliorum', 'genitief mv. mannelijk/onzijdig'), ('aliis', 'datief/ablatief mv.'),
        ('alios', 'accusatief mv. mannelijk'), ('alis', 'datief/ablatief mv. (late nevenvorm)')]))

X('alter', 'onbepaald voornaamwoord', 'alter, altera, alterum',
  'de ander (van twee) | de tweede',
  _vnw([('alter', 'nominatief ev. mannelijk'), ('altera', 'nominatief/ablatief ev. vrouwelijk'),
        ('alterum', 'nominatief/accusatief ev. onzijdig, of accusatief ev. mannelijk'),
        ('alterius', 'genitief ev.'), ('alteri', 'datief ev.'),
        ('alterutro', 'ablatief ev. — de een tegenover de ander, wederzijds')]))

X('uterque', 'onbepaald voornaamwoord', 'uterque, utraque, utrumque', 'ieder van beiden, beide',
  _vnw([('uterque', 'nominatief ev. mannelijk'), ('utraque', 'nominatief/ablatief ev. vrouwelijk'),
        ('utrique', 'datief ev., of nominatief mv. mannelijk'),
        ('utrumque', 'accusatief ev. mannelijk/onzijdig')]))

X('nemo', 'onbepaald voornaamwoord', 'nemo, neminis', 'niemand',
  _vnw([('nemo', 'nominatief ev.'), ('nemini', 'datief ev.'), ('neminem', 'accusatief ev.')]))

X('nihil', 'onbepaald voornaamwoord', 'nihil (nil)', 'niets | (bijwoordelijk) in het geheel niet',
  _vnw([('nihil', 'onverbuigbaar — niets'), ('nihilum', 'accusatief ev. — het niets'),
        ('nil', 'onverbuigbaar (samengetrokken vorm) — niets')]))


# ===========================================================================
# 2. Voorzetsels, voegwoorden en bijwoorden
# ===========================================================================

I('a', 'voorzetsel (met ablatief)', 'van, vandaan | door (bij een lijdende vorm) | sinds',
  extra=['ab', 'abs'],
  toel='`a` staat voor een medeklinker, `ab` voor een klinker; `abs` alleen nog in vaste '
       'verbindingen. In de Vulgaat markeert `a`/`ab` bijna altijd de handelende persoon.')
I('ad', 'voorzetsel (met accusatief)',
  'naar, tot | bij, aan | tegen (van spreken: ad me, tot mij) | met het oog op, voor')
I('adhuc', 'bijwoord', 'tot nu toe, nog steeds | bovendien, nog daarbij')
I('adversus', 'voorzetsel (met accusatief)', 'tegenover, tegen | jegens', extra=['adversum'],
  verw=['adversarius'])
I('ante', 'voorzetsel (met accusatief) en bijwoord', 'voor (in tijd of plaats) | vooraan, eerder',
  verw=['antequam'])
I('antequam', 'voegwoord', 'voordat, eer', verw=['ante', 'priusquam'])
I('apud', 'voorzetsel (met accusatief)', 'bij, in de nabijheid van | ten huize van | in de ogen van')
I('at', 'voegwoord', 'maar, echter (met nadruk)')
I('attamen', 'voegwoord', 'maar toch, en toch', verw=['tamen'])
I('aut', 'voegwoord', 'of | (aut … aut) of … of')
I('autem', 'voegwoord (achter het eerste woord van de zin)',
  'echter, maar | nu, en (overgang naar het volgende)',
  toel='In 4 Ezra vaak nauwelijks tegenstellend: eerder een vertellend "en toen".')
I('bene', 'bijwoord', 'goed, wel | terecht', verw=['bonus'], prio=1)
I('certe', 'bijwoord', 'zeker, stellig | in elk geval', verw=['certus'], prio=1)
I('circa', 'voorzetsel (met accusatief) en bijwoord', 'rondom, om … heen | omstreeks, ongeveer',
  extra=['circum'])
I('contra', 'voorzetsel (met accusatief) en bijwoord', 'tegen, tegenover | daarentegen')
I('coram', 'voorzetsel (met ablatief)', 'in het bijzijn van, ten overstaan van')
I('cotidie', 'bijwoord', 'dagelijks, elke dag', verw=['dies'])
I('cum', 'voorzetsel (met ablatief) en voegwoord',
  'met, samen met | (als voegwoord) toen, wanneer | omdat | hoewel',
  toel='Vorm en betekenis vallen samen: het voorzetsel `cum` (met) en het voegwoord `cum` '
       '(toen/omdat) zijn in de tekst alleen uit de zinsbouw te onderscheiden.')
I('de', 'voorzetsel (met ablatief)',
  'van … af, vanaf | over, aangaande | uit (materiaal, herkomst) | volgens')
I('deorsum', 'bijwoord', 'naar beneden, omlaag', verw=['sursum'])
I('donec', 'voegwoord', 'totdat | zolang als')
I('dum', 'voegwoord', 'terwijl, zolang als | totdat | mits')
I('ecce', 'tussenwerpsel', 'zie! kijk! | daar is …',
  toel='Vaste opening van een visioen in 4 Ezra: "et ecce" — en zie daar.')
I('enim', 'voegwoord (achter het eerste woord van de zin)', 'want, immers | namelijk')
I('ergo', 'voegwoord', 'dus, daarom | welnu')
I('et', 'voegwoord en bijwoord', 'en | ook, zelfs | (et … et) zowel … als',
  toel='Het verhaal van 4 Ezra rijgt zinnen aaneen met `et`, naar Hebreeuws model '
       '(het "en" van de waw-consecutief).')
I('etiam', 'bijwoord en voegwoord', 'ook, eveneens | zelfs | ja zeker')
I('ex', 'voorzetsel (met ablatief)',
  'uit, vanuit | van … af | uit (materiaal) | ten gevolge van | overeenkomstig', extra=['e'],
  toel='`ex` voor een klinker, `e` voor een medeklinker; 4 Ezra gebruikt vrijwel altijd `ex`.')
I('forte', 'bijwoord', 'toevallig, bij toeval | misschien', verw=['fortassis'], prio=1)
I('fortassis', 'bijwoord', 'misschien, wellicht', verw=['forte'])
I('frequenter', 'bijwoord', 'vaak, herhaaldelijk | in groten getale')
I('frustra', 'bijwoord', 'tevergeefs, zonder resultaat | zonder reden')
I('hodie', 'bijwoord', 'vandaag, heden | tegenwoordig', verw=['dies'])
I('huc', 'bijwoord', 'hierheen, naar deze plaats', verw=['hic'])
I('iam', 'bijwoord', 'reeds, al | nu | (met een ontkenning) niet meer')
I('ibi', 'bijwoord', 'daar, op die plaats | toen, daarop')
I('ideo', 'bijwoord', 'daarom, om die reden', extra=['ideoque'], verw=['is'])
I('illic', 'bijwoord', 'daarginds, op die plaats', verw=['ille'])
I('in', 'voorzetsel (met ablatief of accusatief)',
  'in, op (met ablatief: waar?) | naar, tot in (met accusatief: waarheen?) | tegen | '
  'gedurende, voor (in aeternum: voor eeuwig)')
I('inde', 'bijwoord', 'vandaar, van daaruit | daarna, vervolgens')
I('inter', 'voorzetsel (met accusatief)', 'tussen, onder | gedurende', verw=['invicem'])
I('interdie', 'bijwoord', 'overdag, bij daglicht', verw=['dies'])
I('intra', 'voorzetsel (met accusatief)', 'binnen, binnen in | binnen (een tijdsduur)')
I('introrsus', 'bijwoord', 'naar binnen, binnenwaarts')
I('invicem', 'bijwoord', 'om beurten, wederzijds | elkaar, onder elkaar')
I('ita', 'bijwoord', 'zo, op die manier | zozeer | (ita ut) zodat')
I('item', 'bijwoord', 'evenzo, insgelijks | eveneens')
I('iterum', 'bijwoord', 'opnieuw, nog eens | van de andere kant', extra=['iterato'],
  toel='`iterato` is een late nevenvorm met dezelfde betekenis: nogmaals.')
I('iuxta', 'voorzetsel (met accusatief) en bijwoord', 'naast, dichtbij | volgens, overeenkomstig')
I('magis', 'bijwoord', 'meer, in hogere mate | eerder, liever', verw=['maior'])
I('modo', 'bijwoord', 'slechts, alleen maar | zojuist, pas | (modo … modo) nu eens … dan weer',
  prio=1, verw=['modus'])
I('nam', 'voegwoord', 'want, immers')
I('ne', 'voegwoord en ontkennend partikel',
  'opdat niet, dat niet | (bij een gebod) niet | of (in een afhankelijke vraag)')
I('nec', 'voegwoord', 'en niet, ook niet | (nec … nec) noch … noch', extra=['neque'],
  verw=['non'])
I('necdum', 'bijwoord', 'en nog niet, nog altijd niet', verw=['nondum'])
I('nempe', 'bijwoord', 'namelijk, welnu | natuurlijk, ongetwijfeld')
I('nisi', 'voegwoord', 'tenzij, als niet | behalve, dan alleen', verw=['si', 'non'])
I('noctu', 'bijwoord', 'bij nacht, in de nacht', verw=['nox'])
I('non', 'ontkennend bijwoord', 'niet | geen')
I('nondum', 'bijwoord', 'nog niet', verw=['non', 'necdum'])
I('nonne', 'vraagpartikel', 'toch zeker wel? niet waar? (verwacht het antwoord "ja")',
  verw=['non', 'numquid'])
I('numquam', 'bijwoord', 'nooit, nimmer', verw=['umquam'])
I('numquid', 'vraagpartikel', 'soms? toch niet? (verwacht het antwoord "nee")',
  toel='In de vraaggesprekken van 4 Ezra opent `numquid` telkens een vraag waarop de engel '
       'ontkennend antwoordt.', verw=['nonne'])
I('nunc', 'bijwoord', 'nu, thans | welnu (overgang in een betoog)')
I('nusquam', 'bijwoord', 'nergens | in geen enkel opzicht')
I('o', 'tussenwerpsel', 'o! ach! (bij een aanspreking of uitroep)')
I('olim', 'bijwoord', 'eertijds, vroeger | eens, ooit (ook van de toekomst)')
I('palam', 'bijwoord', 'openlijk, in het openbaar')
I('paene', 'bijwoord', 'bijna, haast')
I('paulatim', 'bijwoord', 'geleidelijk, beetje bij beetje', verw=['paululum'])
I('paululum', 'bijwoord', 'een weinig, een korte tijd', verw=['paulatim'])
I('penes', 'voorzetsel (met accusatief)', 'in de macht van, bij')
I('per', 'voorzetsel (met accusatief)',
  'door, doorheen | gedurende | door middel van, door toedoen van | bij (in een eed)')
I('post', 'voorzetsel (met accusatief) en bijwoord', 'na, achter | daarna', extra=['postea'])
I('prae', 'voorzetsel (met ablatief)', 'voor, voor … uit | wegens, vanwege')
I('praeter', 'voorzetsel (met accusatief)', 'behalve, met uitzondering van | langs, voorbij')
I('prius', 'bijwoord', 'eerder, vroeger | eerst', prio=1, verw=['prior', 'priusquam'])
I('priusquam', 'voegwoord', 'voordat, eer', verw=['prius', 'antequam'])
I('pro', 'voorzetsel (met ablatief)',
  'voor, ten behoeve van | in plaats van | in verhouding tot, overeenkomstig')
I('propter', 'voorzetsel (met accusatief)', 'wegens, vanwege | vlak bij',
  extra=['propterea'])
I('quam', 'bijwoord en voegwoord', 'hoe (in een uitroep) | dan (na een vergrotende trap) | '
  '(quam met de overtreffende trap) zo … mogelijk', prio=1)
I('quamdiu', 'voegwoord', 'zolang als, hoelang')
I('quando', 'bijwoord en voegwoord', 'wanneer? | toen, wanneer | aangezien')
I('quapropter', 'bijwoord', 'daarom, om welke reden')
I('quare', 'bijwoord', 'waarom? | daarom, en daarom')
I('quasi', 'voegwoord en bijwoord', 'alsof, als het ware | ongeveer, zowat', verw=['sicut'])
I('quemadmodum', 'voegwoord', 'op welke wijze, zoals | evenals', verw=['quomodo'])
I('quidem', 'bijwoord', 'weliswaar, althans | zeker, inderdaad')
I('quoadusque', 'voegwoord', 'totdat, zolang tot', verw=['donec'])
I('quomodo', 'bijwoord en voegwoord', 'hoe? op welke manier? | zoals', verw=['quemadmodum'])
I('quoniam', 'voegwoord', 'omdat, aangezien | dat (na werkwoorden van zeggen)',
  toel='In de Vulgaat leidt `quoniam` heel vaak een lijdend voorwerpszin in — daar is het '
       'gewoon "dat", niet "omdat".', verw=['quia'])
I('quia', 'voegwoord', 'omdat, want | dat (na werkwoorden van zeggen en menen)',
  verw=['quoniam'])
I('quoque', 'bijwoord', 'ook, eveneens')
I('quotquot', 'onbepaald bijwoord', 'hoevelen ook, allen die')
I('recte', 'bijwoord', 'op de juiste wijze, terecht | rechtuit', verw=['rectus'], prio=1)
I('secrete', 'bijwoord', 'in het geheim, apart', verw=['secretum'], prio=1)
I('secundum', 'voorzetsel (met accusatief)', 'volgens, overeenkomstig | langs | onmiddellijk na',
  prio=1, verw=['secundus'])
I('sed', 'voegwoord', 'maar, echter | (na een ontkenning) maar wel')
I('semper', 'bijwoord', 'altijd, steeds')
I('si', 'voegwoord', 'als, indien | of (in een afhankelijke vraag)')
I('sic', 'bijwoord', 'zo, op deze wijze | (sic … quomodo) zoals … zo')
I('sicut', 'voegwoord', 'zoals, gelijk | alsof', verw=['quasi', 'sic'])
I('similiter', 'bijwoord', 'evenzo, op dezelfde wijze', verw=['similis'], prio=1)
I('simul', 'bijwoord', 'tegelijk, samen | zodra')
I('sine', 'voorzetsel (met ablatief)', 'zonder')
I('singillatim', 'bijwoord', 'stuk voor stuk, afzonderlijk', verw=['singuli'])
I('solummodo', 'bijwoord', 'alleen maar, uitsluitend', verw=['solus'])
I('statim', 'bijwoord', 'onmiddellijk, terstond')
I('sub', 'voorzetsel (met ablatief of accusatief)', 'onder | aan de voet van | tegen (van tijd)')
I('subito', 'bijwoord', 'plotseling, opeens', prio=1)
I('super', 'voorzetsel (met accusatief of ablatief) en bijwoord',
  'boven, over | op | meer dan | betreffende, over',
  toel='In de Vulgaat verdringt `super` het klassieke `de` en `in`: "super hoc" = hierover.')
I('supra', 'voorzetsel (met accusatief) en bijwoord', 'boven, boven op | eerder, hierboven')
I('sursum', 'bijwoord', 'omhoog, naar boven', verw=['deorsum'])
I('tam', 'bijwoord', 'zo, zozeer | (tam … quam) even … als')
I('tamen', 'voegwoord', 'toch, niettemin', verw=['attamen'])
I('tamquam', 'voegwoord', 'als, zoals | alsof', verw=['quasi'])
I('tot', 'onverbuigbaar telwoord', 'zoveel, zo talrijk', verw=['totidem'])
I('totidem', 'onverbuigbaar telwoord', 'evenveel, even talrijk', verw=['tot'])
I('trans', 'voorzetsel (met accusatief)', 'over, aan de overzijde van | dwars door')
I('tunc', 'bijwoord', 'toen, op dat ogenblik | dan (van de toekomst)')
I('ubi', 'bijwoord en voegwoord', 'waar? | waar, op de plaats waar | zodra',
  extra=['ubicumque'])
I('umquam', 'bijwoord', 'ooit, te eniger tijd', verw=['numquam'])
I('unde', 'bijwoord', 'vanwaar? | waarvandaan, uit welke oorzaak')
I('usque', 'bijwoord', 'tot toe, onafgebroken | (usque ad) helemaal tot aan',
  extra=['usquequo'],
  toel='`usquequo` is in de Vulgaat een vaste vraag: "hoelang nog?"')
I('ut', 'voegwoord', 'opdat, zodat | dat | zoals | (met de aantonende wijs) toen, zodra',
  toel='Het talrijkste voegwoord van 4 Ezra; met de aanvoegende wijs is het "opdat/zodat", '
       'met de aantonende wijs "zoals" of "zodra".')
I('utique', 'bijwoord', 'in elk geval, stellig | zeker, natuurlijk')
I('valde', 'bijwoord', 'zeer, in hoge mate | hevig')
I('vel', 'voegwoord', 'of | (vel … vel) hetzij … hetzij | zelfs, zelfs maar')
I('vere', 'bijwoord', 'werkelijk, waarlijk | naar waarheid', verw=['verus'], prio=1)
I('vero', 'bijwoord', 'werkelijk, echt | maar, echter (zwak tegenstellend)', prio=1,
  verw=['verus'])
I('vix', 'bijwoord', 'nauwelijks, met moeite | pas net')
I('diligenter', 'bijwoord', 'zorgvuldig, nauwgezet | ijverig', verw=['diligentia'])
I('constanter', 'bijwoord', 'standvastig, onwrikbaar')
I('perseveranter', 'bijwoord', 'volhardend, onafgebroken', verw=['perseverantia'])
I('fortiter', 'bijwoord', 'dapper, krachtig | met kracht', verw=['fortis'], prio=1)
I('impie', 'bijwoord', 'goddeloos, zonder ontzag', verw=['impius'], prio=1)
I('iniuste', 'bijwoord', 'onrechtvaardig, ten onrechte', verw=['iniustus'], prio=1)
I('inreligiose', 'bijwoord', 'zonder eerbied, goddeloos',
  toel='Klassiek geschreven als *irreligiose*; de handschriften van 4 Ezra laten de '
       'assimilatie van in- en r- vaak achterwege.')
I('splendide', 'bijwoord', 'schitterend, luisterrijk', verw=['splendor'], prio=1)
I('velociter', 'bijwoord', 'snel, spoedig', verw=['velocitas'], prio=1)
I('celerius', 'bijwoord', 'sneller, tamelijk snel (vergrotende trap van celeriter)',
  verw=['celeritas'], prio=1)
I('facilius', 'bijwoord', 'gemakkelijker (vergrotende trap van facile)', verw=['facilis'], prio=1)
I('velocius', 'bijwoord', 'sneller (vergrotende trap van velociter)', verw=['velocitas'], prio=1)
I('melius', 'bijwoord', 'beter (vergrotende trap van bene)', prio=1, verw=['bonus'])
I('amplius', 'bijwoord', 'meer, verder | langer, voortaan nog', prio=1)
I('plus', 'bijwoord en onbepaald telwoord', 'meer | meer dan', prio=1, verw=['multus'])


# ===========================================================================
# 3. Telwoorden
# ===========================================================================

X('unus', 'telwoord', 'unus, una, unum', 'één | een enkele, één en dezelfde | alleen',
  _vnw([('unus', 'nominatief ev. mannelijk'), ('una', 'nominatief/ablatief ev. vrouwelijk'),
        ('unum', 'nominatief/accusatief ev. onzijdig, of accusatief ev. mannelijk'),
        ('unius', 'genitief ev. (alle geslachten)'), ('uni', 'datief ev. (alle geslachten)'),
        ('unam', 'accusatief ev. vrouwelijk'), ('uno', 'ablatief ev. mannelijk/onzijdig'),
        ('unis', 'datief/ablatief mv.')]), verw=['unicus', 'unusquisque'])
X('duo', 'telwoord', 'duo, duae, duo', 'twee | beide',
  _vnw([('duo', 'nominatief/accusatief mv. mannelijk/onzijdig'), ('duae', 'nominatief mv. vrouwelijk'),
        ('duorum', 'genitief mv. mannelijk/onzijdig'), ('duarum', 'genitief mv. vrouwelijk'),
        ('duobus', 'datief/ablatief mv. mannelijk/onzijdig'), ('duabus', 'datief/ablatief mv. vrouwelijk'),
        ('duos', 'accusatief mv. mannelijk'), ('duas', 'accusatief mv. vrouwelijk')]))
X('tres', 'telwoord', 'tres, tria', 'drie',
  _vnw([('tres', 'nominatief/accusatief mv. mannelijk/vrouwelijk'),
        ('tria', 'nominatief/accusatief mv. onzijdig'), ('trium', 'genitief mv.'),
        ('tribus', 'datief/ablatief mv.')]), prio=-1)
I('quattuor', 'onverbuigbaar telwoord', 'vier')
I('quinque', 'onverbuigbaar telwoord', 'vijf')
I('sex', 'onverbuigbaar telwoord', 'zes')
I('septem', 'onverbuigbaar telwoord', 'zeven',
  toel='Het getal zeven ordent 4 Ezra: zeven visioenen, zeven dagen vasten, zeven wegen.')
I('octo', 'onverbuigbaar telwoord', 'acht')
I('novem', 'onverbuigbaar telwoord', 'negen')
I('decem', 'onverbuigbaar telwoord', 'tien')
I('duodecim', 'onverbuigbaar telwoord', 'twaalf', verw=['duo', 'decem'])
I('triginta', 'onverbuigbaar telwoord', 'dertig',
  toel='"anno tricesimo" — in het dertigste jaar; de openingsdatering van 4 Ezra.')
I('quadraginta', 'onverbuigbaar telwoord', 'veertig')
I('septuaginta', 'onverbuigbaar telwoord', 'zeventig')
I('centum', 'onverbuigbaar telwoord', 'honderd')
I('mille', 'telwoord', 'duizend | (meervoud milia) duizendtallen', extra=['milia', 'milibus'])
A('nongentus, nongenta, nongentum', 'negenhonderd', comp=False, sup=False,
  extra={'nongenti': 'nominatief mv. mannelijk — negenhonderd'})
A('quadringentus, quadringenta, quadringentum', 'vierhonderd', comp=False, sup=False,
  extra={'quadringenti': 'nominatief mv. mannelijk — vierhonderd'})
A('primus, prima, primum', 'eerste | voornaamste, belangrijkste | het begin (primum, als bijwoord: eerst)',
  comp=False, sup=False, verw=['prior', 'primogenitus'])
A('secundus, secunda, secundum', 'tweede | volgend | gunstig (van wind of stroom)',
  comp=False, sup=False, prio=-1)
A('tertius, tertia, tertium', 'derde', comp=False, sup=False)
A('quartus, quarta, quartum', 'vierde', comp=False, sup=False)
A('quintus, quinta, quintum', 'vijfde', comp=False, sup=False)
A('sextus, sexta, sextum', 'zesde', comp=False, sup=False)
A('septimus, septima, septimum', 'zevende', comp=False, sup=False,
  toel='De zevende dag en het zevende tijdperk zijn in 4 Ezra het rustpunt van de geschiedenis.')
A('octavus, octava, octavum', 'achtste', comp=False, sup=False)
A('nonus, nona, nonum', 'negende', comp=False, sup=False)
A('decimus, decima, decimum', 'tiende | (decima, als zelfstandig naamwoord) het tiende deel, de tiende',
  comp=False, sup=False)
A('tricesimus, tricesima, tricesimum', 'dertigste', comp=False, sup=False)
A('singulus, singula, singulum', 'elk afzonderlijk, één voor één | telkens één',
  comp=False, sup=False, verw=['singillatim'])


# ===========================================================================
# 4. Onregelmatige werkwoorden
# ===========================================================================

W('sum', 'werkwoord (onregelmatig)', 'sum, esse, fui',
  'zijn, bestaan | er zijn, aanwezig zijn | (met datief) toebehoren aan | '
  '(als koppelwerkwoord) zijn, worden genoemd', M.sum_paradigma(),
  toel='De vormen met f- (fui, fuit, fuerunt, fuisset) horen bij hetzelfde werkwoord als '
       'die met s-/e- (sum, est, erat, esse); het perfectum heeft een andere stam.')
W('possum', 'werkwoord (onregelmatig)', 'possum, posse, potui',
  'kunnen, in staat zijn | vermogen, macht hebben', M.possum_paradigma(),
  verw=['potens', 'potestas'])
W('eo', 'werkwoord (onregelmatig)', 'eo, ire, ii (ivi), itum',
  'gaan | komen | (van tijd) verstrijken', M.eo_paradigma(), prio=-1,
  toel='Van dit werkwoord komen in 4 Ezra vooral de samenstellingen: exire (uitgaan), '
       'transire (voorbijgaan), perire (vergaan), introire (binnengaan).')
W('exeo', 'werkwoord (onregelmatig)', 'exeo, exire, exii (exivi), exitum',
  'uitgaan, naar buiten gaan | voortkomen, ontspringen | aflopen, ten einde lopen',
  M.eo_paradigma('ex'), verw=['eo', 'exitus'])
W('transeo', 'werkwoord (onregelmatig)', 'transeo, transire, transii (transivi), transitum',
  'oversteken, overgaan | voorbijgaan, verstrijken | overtreden',
  M.eo_paradigma('trans'), verw=['eo', 'pertranseo'])
W('pertranseo', 'werkwoord (onregelmatig)',
  'pertranseo, pertransire, pertransii (pertransivi), pertransitum',
  'geheel doortrekken, doorkruisen | voorbijgaan, voorbijtrekken',
  M.eo_paradigma('pertrans'),
  toel='In 4 Ezra het woord voor het wegtrekken van de tijden: "pertransiit saeculum".',
  verw=['transeo'])
W('pereo', 'werkwoord (onregelmatig)', 'pereo, perire, perii, peritum',
  'vergaan, te gronde gaan | omkomen, verloren gaan', M.eo_paradigma('per'),
  verw=['perditio', 'perdo'])
W('intereo', 'werkwoord (onregelmatig)', 'intereo, interire, interii, interitum',
  'te gronde gaan, omkomen | ophouden te bestaan', M.eo_paradigma('inter'),
  verw=['interitus', 'pereo'])
W('introeo', 'werkwoord (onregelmatig)', 'introeo, introire, introii, introitum',
  'binnengaan, naar binnen gaan', M.eo_paradigma('intro'), verw=['introitus'])
W('abeo', 'werkwoord (onregelmatig)', 'abeo, abire, abii, abitum',
  'weggaan, vertrekken | overgaan in, veranderen in', M.eo_paradigma('ab'))
W('subeo', 'werkwoord (onregelmatig)', 'subeo, subire, subii, subitum',
  'naderen, opkomen | ondergaan, op zich nemen', M.eo_paradigma('sub'))
W('fero', 'werkwoord (onregelmatig)', 'fero, ferre, tuli, latum',
  'dragen, torsen | brengen, aandragen | verdragen, doorstaan | melden, vertellen',
  M.fero_paradigma(), verw=['adfero', 'offero'])
W('volo', 'werkwoord (onregelmatig)', 'volo, velle, volui',
  'willen | wensen, verlangen | bedoelen', M.volo_paradigma('volo'), verw=['voluntas', 'nolo'])
W('nolo', 'werkwoord (onregelmatig)', 'nolo, nolle, nolui',
  'niet willen, weigeren | (noli, nolite met een infinitief) doe niet, laat na',
  M.volo_paradigma('nolo'),
  toel='`noli`/`nolite` + infinitief is in de Vulgaat de gewone manier om een verbod uit te '
       'drukken: "nolite timere" — vreest niet.', verw=['volo'])
W('fio', 'werkwoord (onregelmatig)', 'fio, fieri, factus sum',
  'worden | gebeuren, geschieden | gemaakt worden (dient als lijdende vorm van facio)',
  M.fio_paradigma(), verw=['facio'])
W('adsum', 'werkwoord (onregelmatig)', 'adsum, adesse, adfui',
  'aanwezig zijn, erbij zijn | bijstaan, te hulp komen', M.sum_paradigma('ad'),
  toel='Klassiek meestal geschreven als *assum, adesse*; de Vulgaat houdt de onversmolten '
       'spelling ad- aan.', verw=['sum'])


# ===========================================================================
# 5. Zelfstandige naamwoorden
# ===========================================================================

# --- 1e verbuiging -------------------------------------------------------
N('terra, terrae, v.', 'aarde, aardbodem | land, gebied | grond, bodem',
  toel='In 4 Ezra staat `terra` steeds tegenover de hemel: het toneel van de vergankelijke wereld.')
N('aqua, aquae, v.', 'water | (meervoud) wateren, watermassa | regen')
N('via, viae, v.', 'weg, straat | reis, tocht | manier, levenswandel',
  toel='"viae Altissimi" — de wegen van de Allerhoogste; in 4 Ezra het beeld voor Gods '
       'ondoorgrondelijke bestuur.')
N('vita, vitae, v.', 'leven | levenswijze | levenskracht', verw=['vivo'])
N('gloria, gloriae, v.', 'roem, eer | heerlijkheid, luister | pracht')
N('gratia, gratiae, v.', 'gunst, welwillendheid | genade | dank | bevalligheid',
  toel='"gratias agere" is de vaste uitdrukking voor "dank brengen".')
N('iustitia, iustitiae, v.', 'gerechtigheid, rechtvaardigheid | rechtvaardige daad',
  verw=['iustus', 'iudex'])
N('iniustitia, iniustitiae, v.', 'onrechtvaardigheid, onrecht | onrechtvaardige daad',
  verw=['iustitia'])
N('misericordia, misericordiae, v.', 'medelijden, erbarmen | barmhartigheid, ontferming',
  verw=['misericors', 'misereor'])
N('sapientia, sapientiae, v.', 'wijsheid, inzicht | kennis', verw=['sapiens', 'sapio'])
N('superbia, superbiae, v.', 'hoogmoed, trots | overmoed', verw=['superbus'])
N('ira, irae, v.', 'toorn, gramschap | wraak', verw=['iracundia'])
N('iracundia, iracundiae, v.', 'opvliegendheid, toorn', verw=['ira'])
N('hora, horae, v.', 'uur | tijdstip, ogenblik')
N('causa, causae, v.', 'oorzaak, reden | rechtszaak, geding | (met genitief) omwille van')
N('silva, silvae, v.', 'woud, bos | struikgewas',
  toel='Het woud dat met de zee twist (4 Ezra 4) is een gelijkenis over de grenzen die God '
       'aan elk schepsel stelde.')
N('stella, stellae, v.', 'ster | gesternte', verw=['sidus'])
N('luna, lunae, v.', 'maan | maanlicht')
N('turba, turbae, v.', 'menigte, schare | oploop, gewoel', verw=['turbatio'])
N('anima, animae, v.', 'ziel | leven, levensadem | geest van een gestorvene',
  toel='In 4 Ezra is `anima` het deel van de mens dat na de dood in de voorraadkamers wacht.',
  verw=['animus', 'spiritus'])
N('creatura, creaturae, v.', 'schepsel | schepping, het geschapene', verw=['creo', 'creatio'])
N('flamma, flammae, v.', 'vlam | vuurgloed', verw=['ignis'])
N('gehenna, gehennae, v.', 'Gehenna, de plaats van het vuur | hel',
  toel='Grieks-Hebreeuws leenwoord (Ge-Hinnom, het dal bij Jeruzalem); in de Vulgaat de '
       'vaste naam voor de plaats van straf.')
N('harena, harenae, v.', 'zand | zandvlakte, strand')
N('herba, herbae, v.', 'kruid, plant | gras')
N('mensa, mensae, v.', 'tafel | maaltijd | wisseltafel')
N('mensura, mensurae, v.', 'maat, afmeting | maatstaf | de toegemeten hoeveelheid',
  verw=['mensuro'])
N('memoria, memoriae, v.', 'geheugen, herinnering | gedachtenis | vermelding', verw=['memoro'])
N('natura, naturae, v.', 'natuur, aard | aangeboren gesteldheid', verw=['nascor'])
N('oliva, olivae, v.', 'olijf | olijfboom')
N('pluvia, pluviae, v.', 'regen | regenbui', verw=['aqua'])
N('porta, portae, v.', 'poort, stadspoort | ingang, toegang')
N('pugna, pugnae, v.', 'gevecht, strijd | veldslag', verw=['bellum'])
N('ruina, ruinae, v.', 'instorting, val | ondergang, verderf | puinhoop')
N('sagitta, sagittae, v.', 'pijl | schicht', verw=['sagittarius'])
N('semita, semitae, v.', 'pad, voetpad | smalle weg',
  toel='De "smalle paden" van 4 Ezra 7 zijn het beeld voor de moeizame weg naar het leven.',
  verw=['via'])
N('sponsa, sponsae, v.', 'bruid, verloofde', verw=['sponsus', 'sponsio'])
N('tenebrae, tenebrarum, v.', 'duisternis, donker | blindheid | verborgenheid', alleen='mv',
  toel='Alleen in het meervoud gebruikt, ook waar het Nederlands een enkelvoud heeft.',
  verw=['lux'])
N('tuba, tubae, v.', 'trompet, bazuin | bazuingeschal')
N('tunica, tunicae, v.', 'onderkleed, tuniek | omhulsel, vlies')
N('umbra, umbrae, v.', 'schaduw | schim, schijn',
  toel='4 Ezra noemt de tijd van nu "een schaduw" tegenover de blijvende toekomst.')
N('uva, uvae, v.', 'druif | druiventros', verw=['botrus', 'racemus'])
N('vindemia, vindemiae, v.', 'wijnoogst, druivenpluk | de geoogste druiven',
  verw=['vinea', 'vinum'])
N('vinea, vineae, v.', 'wijngaard | wijnstok', verw=['vinum'])
N('ancilla, ancillae, v.', 'dienstmaagd, slavin', verw=['famula', 'servus'])
N('aquila, aquilae, v.', 'arend, adelaar | (militair) veldteken',
  toel='De adelaar van het vijfde visioen (4 Ezra 11-12) is het Romeinse rijk; de adelaar was '
       'het veldteken van de Romeinse legioenen.')
N('area, areae, v.', 'open plek, plein | dorsvloer')
N('arca, arcae, v.', 'kist, kast | ark (van Noach, of het verbond)')
N('bestia, bestiae, v.', 'dier, beest | wild dier', verw=['animal'])
N('camera, camerae, v.', 'kamer, vertrek | gewelf')
N('columba, columbae, v.', 'duif')
N('coma, comae, v.', 'haar, hoofdhaar | loof van een boom')
N('corona, coronae, v.', 'krans, kroon | erekrans',
  toel='De kroon voor wie de strijd volbracht heeft — in 4 Ezra 2 het loon van de standvastigen.')
N('cura, curae, v.', 'zorg, bezorgdheid | verzorging | inspanning')
N('disciplina, disciplinae, v.', 'onderricht, lering | tucht, orde | leefregel')
N('famula, famulae, v.', 'dienares, dienstmaagd', verw=['ancilla'])
N('fornicaria, fornicariae, v.', 'hoer, ontuchtige vrouw', verw=['fornicatio'])
N('gallina, gallinae, v.', 'hen, kip')
N('gutta, guttae, v.', 'druppel')
N('laetitia, laetitiae, v.', 'vreugde, blijdschap | feestvreugde', verw=['tristitia'])
N('lucerna, lucernae, v.', 'lamp, olielamp | licht', verw=['lumen'])
N('maestitia, maestitiae, v.', 'droefheid, neerslachtigheid', verw=['tristitia'])
N('mamilla, mamillae, v.', 'borst | tepel')
N('pausa, pausae, v.', 'rust, onderbreking | einde', verw=['requies'])
N('persona, personae, v.', 'masker, rol | persoon, iemand | aanzien')
N('petra, petrae, v.', 'rots, steenrots | rotsblok', verw=['lapis'])
N('pinna, pinnae, v.', 'veer, vleugel | vin | tinne, transje',
  toel='De vleugels van de adelaar in visioen vijf; elke `pinna` staat voor een koning.')
N('plaga, plagae, v.', 'slag, houw | plaag, ramp | streek, gewest')
N('provincia, provinciae, v.', 'provincie, wingewest | ambtsgebied')
N('rapina, rapinae, v.', 'roof, plundering | buit', verw=['rapio'])
N('romphea, rompheae, v.', 'zwaard, groot slagzwaard',
  toel='Grieks leenwoord (rhomphaia); in de Vulgaat het zwaard van het oordeel.',
  verw=['gladius'])
N('rosa, rosae, v.', 'roos | rozenstruik')
N('saliva, salivae, v.', 'speeksel | sap, vocht')
N('scintilla, scintillae, v.', 'vonk, sprankje',
  toel='"een vonkje uit de vuurhaard" — het beeld voor het kleine overblijfsel dat behouden blijft.')
N('spica, spicae, v.', 'aar, korenaar')
N('spina, spinae, v.', 'doorn, stekel | doornstruik')
N('statera, staterae, v.', 'weegschaal, balans',
  toel='"in statera" — op de weegschaal; het beeld voor het afwegen van de tijden in 4 Ezra 4.')
N('stipula, stipulae, v.', 'stoppel, halm | stro')
N('tristitia, tristitiae, v.', 'droefheid, verdriet | somberheid', verw=['tristis', 'laetitia'])
N('vena, venae, v.', 'ader | bloedvat | ader in de aarde')
N('vidua, viduae, v.', 'weduwe',
  toel='De rouwende vrouw van het vierde visioen is de weduwe Sion.', verw=['viduitas'])
N('lucusta, lucustae, v.', 'sprinkhaan')
N('fovea, foveae, v.', 'kuil, valkuil | groeve')
N('framea, frameae, v.', 'speer, werpspies | zwaard', verw=['gladius', 'romphea'])
N('gleba, glebae, v.', 'aardkluit, kluit aarde | grond')
N('procella, procellae, v.', 'storm, stormvlaag | onweer', verw=['tempestas'])
N('fistula, fistulae, v.', 'pijp, buis | herdersfluit')
N('agricola, agricolae, m.', 'landbouwer, boer | landman', verw=['ager'])
N('alae, alarum, v.', 'vleugels | (afzonderlijk: ala, alae) vleugel, arm van een leger',
  alleen='mv', verw=['pinna'])
N('ala, alae, v.', 'vleugel | oksel | zijvleugel van een leger', prio=-1, verw=['pinna'])
N('inconstantia, inconstantiae, v.', 'onbestendigheid, wisselvalligheid', verw=['constanter'])
N('incontinentia, incontinentiae, v.', 'onbeheerstheid, gebrek aan zelfbeheersing')
N('concupiscentia, concupiscentiae, v.', 'begeerte, hartstocht', verw=['concupisco'])
N('perseverantia, perseverantiae, v.', 'volharding, standvastigheid', verw=['perseveranter'])
N('diligentia, diligentiae, v.', 'zorgvuldigheid, nauwgezetheid | ijver', verw=['diligenter'])
N('substantia, substantiae, v.', 'bestaan, wezen | bezit, vermogen | grondstof')
N('contentio, contentionis, v.', 'inspanning | strijd, twist', verw=['contendo'])
N('pudicitia, pudicitiae, v.', 'kuisheid, eerbaarheid')
N('penuria, penuriae, v.', 'gebrek, schaarste')
N('copia, copiae, v.', 'overvloed, voorraad | gelegenheid | (meervoud) troepen',
  verw=['copiosus'])

# --- 2e verbuiging, mannelijk -------------------------------------------
N('deus, dei, m.', 'God | god, godheid',
  toel='De onregelmatige meervoudsvormen zijn dii/di (nominatief) en diis/dis (datief en '
       'ablatief); 4 Ezra gebruikt `diis` voor de afgoden van de volken.',
  extra={'dii': 'nominatief mv. — goden', 'di': 'nominatief mv. — goden',
         'diis': 'datief/ablatief mv. — aan/door de goden',
         'dis': 'datief/ablatief mv. — aan/door de goden'})
N('dominus, domini, m.', 'heer, meester | eigenaar | de Heere (God)',
  toel='In de Vulgaat vertaalt `Dominus` de Godsnaam JHWH; de vocatief `Domine` is de aanroep '
       '"Heere!".')
N('populus, populi, m.', 'volk | menigte, schare | de gemeenschap',
  toel='"populus meus" — mijn volk; in 4 Ezra 1-2 spreekt God zo over Israël.')
N('filius, filii, m.', 'zoon | kind, nakomeling | lid van een groep, aanhanger',
  toel='"filii hominum" (mensenkinderen) en "filii Israhel" zijn hebraïsmen: het gaat om de '
       'leden van een groep, niet om afstamming.', verw=['filia', 'pater'])
N('servus, servi, m.', 'slaaf, knecht | dienaar', verw=['servio', 'ancilla'])
N('angelus, angeli, m.', 'engel | bode, gezant',
  toel='Grieks leenwoord (angelos, bode). De engel Uriël is in 4 Ezra de gesprekspartner van Ezra.',
  verw=['archangelus'])
N('archangelus, archangeli, m.', 'aartsengel, hoofd van de engelen', verw=['angelus'])
N('annus, anni, m.', 'jaar | jaargetijde, seizoen', verw=['anniculus'])
N('campus, campi, m.', 'vlakte, veld | akker | slagveld')
N('modus, modi, m.', 'maat | wijze, manier | grens, perk')
N('mundus, mundi, m.', 'wereld, heelal | mensheid | sieraad, opschik',
  verw=['saeculum', 'orbis'])
N('numerus, numeri, m.', 'getal, aantal | rij, gelid | maat',
  toel='"numerus" is in 4 Ezra bijna een technische term: het vastgestelde aantal rechtvaardigen '
       'dat vol moet worden.', verw=['numero'])
N('oculus, oculi, m.', 'oog | blik | knop van een plant')
N('amicus, amici, m.', 'vriend | bondgenoot', verw=['inimicus'])
N('inimicus, inimici, m.', 'vijand, tegenstander', verw=['amicus'])
N('ager, agri, m.', 'akker, veld | landgoed | gebied', verw=['agricola', 'agrestis'])
N('liber, libri, m.', 'boek, geschrift | boekrol | bast van een boom (grondbetekenis)',
  toel='De oorspronkelijke betekenis is "bast": de binnenbast van de boom was het eerste '
       'schrijfmateriaal. In 4 Ezra 14 gaat het om de vierentwintig openbare en zeventig '
       'verborgen boeken.', verw=['littera', 'scribo'])
N('puer, pueri, m.', 'jongen, knaap | kind | knecht, dienaar')
N('vir, viri, m.', 'man | echtgenoot | held',
  toel='Anders dan `homo` (mens) benoemt `vir` uitdrukkelijk het mannelijke.', verw=['homo', 'mulier'])
N('hymnus, hymni, m.', 'lofzang, hymne')
N('murus, muri, m.', 'muur, stadsmuur | wal')
N('thesaurus, thesauri, m.', 'schat | schatkamer, voorraad',
  toel='In 4 Ezra de hemelse "schatkamers" waarin de goede werken bewaard worden.',
  verw=['promptuarium'])
N('thronus, throni, m.', 'troon, zetel', verw=['sedes'])
N('ventus, venti, m.', 'wind | luchtstroom', verw=['flatus', 'spiritus'])
N('rivus, rivi, m.', 'beek, stroompje | waterloop', verw=['flumen'])
N('botrus, botri, m.', 'druiventros', verw=['racemus', 'uva'])
N('racemus, racemi, m.', 'tros, druiventros | het achtergebleven trosje bij de nalezing',
  verw=['botrus', 'uva'])
N('acinus, acini, m.', 'bes, druifje | pit',
  toel='"één druifje uit een tros" — het beeld voor het kleine overblijfsel van Israël.')
N('gladius, gladii, m.', 'zwaard | het zwaard als beeld van oorlog en oordeel',
  verw=['framea', 'romphea'])
N('lupus, lupi, m.', 'wolf')
N('sonus, soni, m.', 'geluid, klank | gerucht', verw=['vox'])
N('paradisus, paradisi, m.', 'park, lusthof | paradijs',
  toel='Perzisch leenwoord via het Grieks; in 4 Ezra de plaats van rust die voor de '
       'rechtvaardigen bereid is.')
N('saccus, sacci, m.', 'zak | rouwgewaad van grof haar')
N('rubus, rubi, m.', 'braamstruik, doornbos',
  toel='De brandende braamstruik waarin God zich aan Mozes bekendmaakte (4 Ezra 14:3).')
N('dolus, doli, m.', 'list, bedrog | valstrik')
N('nimbus, nimbi, m.', 'regenwolk, stortbui | wolk', verw=['nubes'])
N('adversarius, adversarii, m.', 'tegenstander, vijand', verw=['adversus', 'inimicus'])
N('accusator, accusatoris, m.', 'aanklager, beschuldiger', verw=['accuso'])
N('amator, amatoris, m.', 'liefhebber, minnaar', verw=['amo'])
N('subsessor, subsessoris, m.', 'belager, hinderlaaglegger')
N('cultor, cultoris, m.', 'bewerker, landbouwer | vereerder', verw=['colo'])
N('apostata, apostatae, m.', 'afvallige', toel='Grieks leenwoord; in 4 Ezra 1:8 het verwijt aan het volk.')
N('advena, advenae, m.', 'vreemdeling, nieuwkomer', verw=['advenio', 'alienigena'])
N('alienigena, alienigenae, m.', 'vreemdeling, iemand van een ander volk', verw=['advena'])
N('carmonius, carmonii, m.', 'Karmoniër (bewoner van een land in het adelaarsvisioen)')
N('megestanus, megestani, m.', 'grote, machthebber',
  toel='Grieks leenwoord (megistanes, de groten van het rijk); zeldzaam buiten de Vulgaat.')

# --- 2e verbuiging, onzijdig --------------------------------------------
N('verbum, verbi, o.', 'woord | uitspraak, gezegde | zaak, aangelegenheid',
  toel='"verbum Domini" — het woord van de Heere; de vaste formule waarmee een profetie begint.',
  verw=['sermo', 'vox'])
N('saeculum, saeculi, o.', 'mensenleeftijd, generatie | eeuw, tijdperk | wereld | eeuwigheid',
  toel='De sleutelterm van 4 Ezra: "hoc saeculum" (deze wereld, deze tijd) tegenover '
       '"futurum saeculum" (de komende wereld). "in saecula saeculorum" = tot in eeuwigheid.',
  verw=['mundus', 'aeternus'])
N('regnum, regni, o.', 'koningschap, heerschappij | koninkrijk, rijk', verw=['rex', 'regno'])
N('signum, signi, o.', 'teken, merkteken | veldteken | wonderteken, voorteken',
  toel='"signa" zijn in 4 Ezra de voortekenen van het einde.', verw=['signaculum'])
N('bellum, belli, o.', 'oorlog, strijd | veldslag', verw=['pugna', 'bellicosus'])
N('templum, templi, o.', 'tempel, heiligdom | gewijde ruimte')
N('iudicium, iudicii, o.', 'rechtspraak, oordeel | vonnis | gerechtshof',
  toel='"dies iudicii" — de dag van het oordeel, het scharnierpunt van 4 Ezra 7.',
  verw=['iudex', 'iudico'])
N('principium, principii, o.', 'begin, aanvang | oorsprong | grondslag', verw=['initium'])
N('initium, initii, o.', 'begin, aanvang | oorsprong', verw=['principium', 'finis'])
N('consilium, consilii, o.', 'beraad, overleg | raadsbesluit, plan | raad, advies')
N('mysterium, mysterii, o.', 'geheim, geheimenis | verborgen raadsbesluit',
  toel='Grieks leenwoord; in 4 Ezra wat God alleen aan de ziener onthult.')
N('periculum, periculi, o.', 'gevaar, risico | beproeving')
N('praeceptum, praecepti, o.', 'voorschrift, gebod | onderricht', verw=['praecipio', 'mandatum'])
N('praemium, praemii, o.', 'beloning, loon | prijs', verw=['merces'])
N('promptuarium, promptuarii, o.', 'voorraadkamer, bergplaats',
  toel='De "promptuaria animarum" van 4 Ezra 4 en 7: de kamers waarin de zielen van de '
       'gestorvenen wachten tot het oordeel.', verw=['thesaurus'])
N('sepulchrum, sepulchri, o.', 'graf, grafmonument')
N('silentium, silentii, o.', 'stilte, zwijgen | rust', verw=['sileo'])
N('spatium, spatii, o.', 'ruimte, afstand | tijdsruimte, tijdsbestek')
N('tabernaculum, tabernaculi, o.', 'tent | woning, verblijf | tabernakel')
N('testamentum, testamenti, o.', 'testament, uiterste wil | verbond',
  toel='In de Vulgaat de vertaling van het Hebreeuwse *berit*: het verbond tussen God en zijn volk.')
N('vestigium, vestigii, o.', 'voetspoor, voetstap | spoor, teken')
N('vinum, vini, o.', 'wijn | wijnstok, wijnoogst', verw=['vinea', 'vindemia'])
N('lignum, ligni, o.', 'hout | boom | balk, stuk hout', verw=['arbor'])
N('membrum, membri, o.', 'lichaamsdeel, lid | onderdeel', verw=['corpus'])
N('exterminium, exterminii, o.', 'verdelging, ondergang', verw=['extermino'])
N('folium, folii, o.', 'blad | loof')
N('fundamentum, fundamenti, o.', 'grondslag, fundament | grondvesten', verw=['fundo'])
N('firmamentum, firmamenti, o.', 'steun, stut | uitspansel, hemelgewelf',
  toel='In Genesis 1 en in 4 Ezra 6 het gewelf dat de wateren scheidt.')
N('gaudium, gaudii, o.', 'vreugde, blijdschap | genot', verw=['gaudeo', 'laetitia'])
N('imperium, imperii, o.', 'bevel, gezag | heerschappij | rijk', verw=['impero'])
N('inproperium, inproperii, o.', 'smaad, verwijt | schimp',
  toel='Klassiek *improperium*; laat-Latijns woord dat vooral in de Vulgaat voorkomt.',
  verw=['obprobrium'])
N('obprobrium, obprobrii, o.', 'schande, smaad | schimpscheut',
  toel='Klassiek geschreven als *opprobrium*.', verw=['inproperium'])
N('scabillum, scabilli, o.', 'voetbankje, voetenbank')
N('signaculum, signaculi, o.', 'zegel, zegelmerk | teken', verw=['signum'])
N('spiramentum, spiramenti, o.', 'ademtocht, ademhaling | luchtgat', verw=['spiritus'])
N('candelabrum, candelabri, o.', 'kandelaar, lampenstandaard')
N('convivium, convivii, o.', 'gastmaal, feestmaal')
N('cruciamentum, cruciamenti, o.', 'foltering, kwelling', verw=['crucio', 'cruciatus'])
N('delictum, delicti, o.', 'misstap, vergrijp | zonde', verw=['peccatum', 'delinquo'])
N('desertum, deserti, o.', 'woestijn, wildernis | onbewoond land', verw=['desero'])
N('diluvium, diluvii, o.', 'overstroming | zondvloed')
N('epulum, epuli, o.', 'feestmaal, gastmaal', verw=['convivium'])
N('figmentum, figmenti, o.', 'maaksel, vormsel | verzinsel', verw=['fingo', 'plasma'])
N('frumentum, frumenti, o.', 'koren, graan', verw=['granum', 'semen'])
N('granum, grani, o.', 'korrel, graankorrel | zaadkorrel', verw=['semen'])
N('idolum, idoli, o.', 'beeld, afbeelding | afgodsbeeld, afgod')
N('iumentum, iumenti, o.', 'lastdier, trekdier | vee', verw=['pecus'])
N('latibulum, latibuli, o.', 'schuilplaats, hol', verw=['lateo'])
N('lilium, lilii, o.', 'lelie')
N('monumentum, monumenti, o.', 'gedenkteken | grafmonument | herinnering', verw=['memoria'])
N('odoramentum, odoramenti, o.', 'reukwerk, welriekende specerij', verw=['odor'])
N('pinnaculum, pinnaculi, o.', 'vleugeltje | tinne, spits', verw=['pinna'])
N('portentum, portenti, o.', 'wonderteken, voorteken | gedrocht', verw=['prodigium', 'signum'])
N('prodigium, prodigii, o.', 'wonderteken, voorteken | wangedrocht', verw=['portentum'])
N('psalterium, psalterii, o.', 'harp, snarenspel | psalmboek')
N('somnium, somnii, o.', 'droom | droombeeld', verw=['somnio'])
N('territorium, territorii, o.', 'gebied, grondgebied', verw=['terra'])
N('unguentum, unguenti, o.', 'zalf, balsem | reukwerk')
N('vestimentum, vestimenti, o.', 'kledingstuk, gewaad', verw=['vestis', 'tunica'])
N('bonum, boni, o.', 'het goede | goed, bezit | voordeel', prio=-1, verw=['bonus'])
N('malum, mali, o.', 'het kwaad | onheil, ramp | misdaad', prio=-1, verw=['malus'])
N('beneficium, beneficii, o.', 'weldaad, gunst | dienst', verw=['bonus'])
N('facinus, facinoris, o.', 'daad | wandaad, misdaad', verw=['facio'])
N('adiutorium, adiutorii, o.', 'hulp, bijstand', verw=['adiuvo'])
N('vestibulum, vestibuli, o.', 'voorhof, ingang')
N('cogitamentum, cogitamenti, o.', 'gedachte, overleg',
  toel='Laat-Latijnse nevenvorm van *cogitatio*; buiten de Vulgaat zeldzaam.', verw=['cogito'])
N('legitimum, legitimi, o.', 'wettelijke bepaling, voorschrift', verw=['lex'])
N('sabbatum, sabbati, o.', 'sabbat, rustdag')
N('conloquium, conloquii, o.', 'gesprek, onderhoud', verw=['loquor'])

# --- 3e verbuiging, mannelijk en vrouwelijk ------------------------------
N('rex, regis, m.', 'koning | heerser, vorst', verw=['regnum', 'regno'])
N('lex, legis, v.', 'wet | wetsvoorschrift | de Wet van Mozes',
  toel='In 4 Ezra draait alles om de Wet: zij is gegeven, verbrand en opnieuw geschreven (14:21-22).',
  verw=['legitimum'])
N('pax, pacis, v.', 'vrede | rust, verzoening | verdrag')
N('vox, vocis, v.', 'stem | geluid, klank | woord, uitspraak', verw=['verbum'])
N('lux, lucis, v.', 'licht | daglicht | glans', verw=['lumen', 'tenebrae'])
N('nox, noctis, v.', 'nacht | duisternis', i=True, verw=['dies', 'noctu'])
N('pars, partis, v.', 'deel, gedeelte | kant, zijde | partij, rol', i=True)
N('mors, mortis, v.', 'dood | sterven | ondergang', i=True, verw=['morior', 'vita'])
N('gens, gentis, v.', 'volk, stam | geslacht | (meervoud) de heidenvolken', i=True,
  toel='In de Vulgaat zijn "gentes" bijna altijd de niet-joodse volken, de heidenen.',
  verw=['natio', 'populus'])
N('mens, mentis, v.', 'geest, verstand | gezindheid | gedachte', i=True, verw=['cor', 'sensus'])
N('fons, fontis, m.', 'bron, wel | oorsprong', i=True)
N('mons, montis, m.', 'berg | gebergte', i=True)
N('dens, dentis, m.', 'tand | punt, tand van een werktuig', i=True)
N('civitas, civitatis, v.', 'burgerschap | staat, gemeenschap | stad',
  toel='De "civitas" die Ezra in een visioen ziet is het hemelse Sion.', verw=['civis'])
N('veritas, veritatis, v.', 'waarheid | werkelijkheid | oprechtheid', verw=['verus'])
N('iniquitas, iniquitatis, v.', 'onbillijkheid | onrecht, ongerechtigheid | wandaad',
  verw=['iniustitia', 'iniquus'])
N('impietas, impietatis, v.', 'gebrek aan ontzag, goddeloosheid | misdaad', verw=['impius'])
N('aeternitas, aeternitatis, v.', 'eeuwigheid | onvergankelijkheid', verw=['aeternus'])
N('caritas, caritatis, v.', 'duurte, hoge prijs | liefde, genegenheid',
  toel='In de Vulgaat het woord voor de zelfgevende liefde (Grieks agapè).')
N('claritas, claritatis, v.', 'helderheid, glans | roem, luister', verw=['clarus', 'splendor'])
N('humilitas, humilitatis, v.', 'laagte, geringheid | nederigheid | vernedering',
  verw=['humilis'])
N('infirmitas, infirmitatis, v.', 'zwakte, gebrek aan kracht | ziekte', verw=['infirmus'])
N('libertas, libertatis, v.', 'vrijheid | vrijmoedigheid', verw=['liber'])
N('multitudo, multitudinis, v.', 'menigte, grote hoeveelheid | volksmassa', verw=['multus'])
N('similitudo, similitudinis, v.', 'gelijkenis, overeenkomst | beeld, evenbeeld | vergelijking',
  toel='De gelijkenissen waarmee de engel Ezra antwoordt heten in de tekst `similitudines`.',
  verw=['similis'])
N('magnitudo, magnitudinis, v.', 'grootte, omvang | verhevenheid', verw=['magnus'])
N('altitudo, altitudinis, v.', 'hoogte | diepte | verhevenheid', verw=['altus'])
N('latitudo, latitudinis, v.', 'breedte, uitgestrektheid', verw=['latus'])
N('pulchritudo, pulchritudinis, v.', 'schoonheid, bevalligheid')
N('fortitudo, fortitudinis, v.', 'sterkte, kracht | dapperheid', verw=['fortis'])
N('consuetudo, consuetudinis, v.', 'gewoonte, gebruik | omgang')
N('longanimitas, longanimitatis, v.', 'lankmoedigheid, geduld',
  toel='Letterlijk "langgeestigheid"; de Vulgaat vormde het woord om het Griekse makrothumia '
       'weer te geven. In 4 Ezra 7 een eigenschap van God.')
N('necessitas, necessitatis, v.', 'noodzaak, dwang | nood, benauwdheid')
N('paupertas, paupertatis, v.', 'armoede, gebrek', verw=['pauper'])
N('potestas, potestatis, v.', 'macht, vermogen | gezag, bevoegdheid | machthebber',
  verw=['possum', 'potens'])
N('satietas, satietatis, v.', 'verzadiging | overdaad, walging', verw=['saturitas'])
N('saturitas, saturitatis, v.', 'verzadiging, overvloed', verw=['satietas'])
N('senectus, senectutis, v.', 'ouderdom, hoge leeftijd', verw=['senesco', 'iuventus'])
N('servitus, servitutis, v.', 'slavernij, dienstbaarheid', verw=['servus', 'servio'])
N('iuventus, iuventutis, v.', 'jeugd, jonge jaren | de jongeren', verw=['iuvenis', 'senectus'])
N('virtus, virtutis, v.', 'mannelijkheid, dapperheid | kracht, vermogen | deugd | (meervoud) '
  'machten, wonderdaden', verw=['vir', 'fortitudo'])
N('velocitas, velocitatis, v.', 'snelheid, vlugheid', verw=['velociter'])
N('vanitas, vanitatis, v.', 'leegheid, ijdelheid | zinloosheid', verw=['vanus'])
N('vilitas, vilitatis, v.', 'geringe waarde, goedkoopte | verachtelijkheid')
N('honestas, honestatis, v.', 'eerbaarheid, achtenswaardigheid | eer', verw=['honor'])
N('tarditas, tarditatis, v.', 'traagheid, langzaamheid', verw=['tardo'])
N('nativitas, nativitatis, v.', 'geboorte | afkomst', verw=['nascor'])
N('bonitas, bonitatis, v.', 'goedheid, deugdelijkheid | welwillendheid', verw=['bonus'])
N('homo, hominis, m.', 'mens | man, iemand | de mensheid',
  toel='"filius hominis" (mensenzoon) en "filii hominum" (mensenkinderen) zijn in 4 Ezra vaste '
       'uitdrukkingen voor "de mens".', verw=['vir'])
N('nomen, nominis, o.', 'naam | benaming | roem, reputatie', verw=['nomino'])
N('corpus, corporis, o.', 'lichaam | lijk | geheel, verzameling', verw=['membrum', 'anima'])
N('tempus, temporis, o.', 'tijd, tijdstip | gelegenheid | tijdsgewricht',
  toel='"tempora" in het meervoud zijn de vastgestelde tijdperken van de wereldgeschiedenis.',
  verw=['saeculum', 'hora'])
N('opus, operis, o.', 'werk, arbeid | daad | bouwwerk',
  toel='De "opera" waarnaar de mens geoordeeld wordt zijn zijn daden, niet zijn werkzaamheden.',
  verw=['operor', 'factum'])
N('pectus, pectoris, o.', 'borst | hart, gemoed', verw=['cor'])
N('pondus, ponderis, o.', 'gewicht | last | belang', verw=['statera'])
N('semen, seminis, o.', 'zaad | zaaigoed | nageslacht, kroost',
  toel='"semen malum" — het boze zaad dat in Adams hart geplant werd (4 Ezra 4:30); een '
       'sleutelbeeld van het boek.', verw=['semino', 'granum'])
N('flumen, fluminis, o.', 'rivier, stroom | stroming', verw=['rivus', 'aqua'])
N('lumen, luminis, o.', 'licht | lamp | oog', verw=['lux', 'lucerna'])
N('caput, capitis, o.', 'hoofd | kop | hoofdzaak, begin | leider',
  toel='De koppen van de adelaar in visioen vijf staan voor keizers.')
N('cor, cordis, o.', 'hart | gemoed, geest | moed',
  toel='"cor malignum" — het boosaardige hart dat de mens van Adam erfde (4 Ezra 3:20-22).',
  verw=['mens', 'pectus'])
N('lac, lactis, o.', 'melk')
N('mel, mellis, o.', 'honing')
N('os, oris, o.', 'mond | gelaat, gezicht | opening', verw=['facies', 'vultus'])
N('vas, vasis, o.', 'vat, gereedschap | (meervoud vasa) huisraad, gerei',
  extra={'vaso': 'ablatief ev. (naar de onzijdige nevenvorm vasum)',
         'vasa': 'nominatief/accusatief mv.', 'vasorum': 'genitief mv.',
         'vasis': 'datief/ablatief mv.'},
  toel='In het meervoud gaat het woord over op de 2e verbuiging: vasa, vasorum, vasis.')
N('iter, itineris, o.', 'weg, tocht | reis | doortocht', verw=['via'])
N('genus, generis, o.', 'geboorte, afkomst | geslacht, familie | soort, aard',
  verw=['gens', 'generatio'])
N('sidus, sideris, o.', 'gesternte, sterrenbeeld | ster', verw=['stella'])
N('stercus, stercoris, o.', 'mest, drek | vuil')
N('vulnus, vulneris, o.', 'wond | slag, verlies')
N('sanguis, sanguinis, m.', 'bloed | bloedverwantschap | bloedvergieten')
N('pastor, pastoris, m.', 'herder | hoeder', verw=['grex'])
N('peccator, peccatoris, m.', 'zondaar', verw=['peccatum', 'pecco'])
N('creator, creatoris, m.', 'schepper, voortbrenger', verw=['creo', 'creatura'])
N('salvator, salvatoris, m.', 'redder, heiland', verw=['salvo', 'salus'])
N('dominator, dominatoris, m.', 'heerser, gebieder', verw=['dominus', 'dominor'])
N('aemulator, aemulatoris, m.', 'naijverig persoon | ijveraar',
  toel='"Deus aemulator" vertaalt het Hebreeuwse "naijverige God" — God die geen andere goden duldt.')
N('iudex, iudicis, m.', 'rechter | beoordelaar', verw=['iudicium', 'iudico'])
N('dux, ducis, m.', 'leider, aanvoerder | veldheer | gids', verw=['duco', 'ducatus'])
N('lapis, lapidis, m.', 'steen | edelsteen | grenssteen', verw=['petra'])
N('leo, leonis, m.', 'leeuw',
  toel='De leeuw die de adelaar aanklaagt (4 Ezra 11:37) is de Messias uit Juda.')
N('draco, draconis, m.', 'draak, slang | zeemonster')
N('radix, radicis, v.', 'wortel | oorsprong, grondslag')
N('matrix, matricis, v.', 'moederschoot, baarmoeder | oorsprong', verw=['mater'])
N('mulier, mulieris, v.', 'vrouw | echtgenote', verw=['vir', 'vidua'])
N('mater, matris, v.', 'moeder | moederstad', verw=['pater', 'matrix'])
N('pater, patris, m.', 'vader | (meervoud) voorvaderen, voorouders', verw=['mater', 'filius'])
N('frater, fratris, m.', 'broer | geloofsgenoot, medemens')
N('sermo, sermonis, m.', 'gesprek, taal | rede, toespraak | woord', verw=['verbum'])
N('oratio, orationis, v.', 'rede, toespraak | gebed', verw=['oro'])
N('creatio, creationis, v.', 'schepping, het scheppen', verw=['creo', 'creatura'])
N('generatio, generationis, v.', 'verwekking, voortbrenging | geslacht, generatie',
  verw=['genus', 'genero'])
N('interpretatio, interpretationis, v.', 'uitleg, verklaring | vertaling', verw=['interpretor'])
N('corruptio, corruptionis, v.', 'bederf, verval | vergankelijkheid | zedelijk verderf',
  toel='4 Ezra zet `corruptio` (vergankelijkheid) telkens tegenover `incorruptio` — de '
       'onvergankelijkheid van de komende wereld.', verw=['corrumpo', 'incorruptio'])
N('perditio, perditionis, v.', 'ondergang, verderf | verlies', verw=['perdo', 'pereo'])
N('tribulatio, tribulationis, v.', 'verdrukking, benauwdheid | beproeving', verw=['tribulo'])
N('visio, visionis, v.', 'het zien, gezicht | visioen, verschijning', verw=['video', 'visus'])
N('turbatio, turbationis, v.', 'verwarring, beroering | opschudding', verw=['turbo', 'turba'])
N('castigatio, castigationis, v.', 'terechtwijzing, kastijding', verw=['castigo'])
N('consummatio, consummationis, v.', 'voltooiing, voleinding | einde',
  toel='"consummatio saeculi" — de voleinding van de wereld.', verw=['consummo'])
N('contritio, contritionis, v.', 'verbrijzeling, vermorzeling | verslagenheid', verw=['contero'])
N('deprecatio, deprecationis, v.', 'smeekbede, voorbede', verw=['deprecor'])
N('desertio, desertionis, v.', 'verlating, het in de steek laten', verw=['desero'])
N('dispositio, dispositionis, v.', 'ordening, beschikking | inrichting, plan',
  verw=['dispono'])
N('divisio, divisionis, v.', 'verdeling, scheiding', verw=['divido'])
N('resurrectio, resurrectionis, v.', 'opstanding, verrijzenis', verw=['resurgo', 'exsurrectio'])
N('exsurrectio, exsurrectionis, v.', 'het opstaan, opstanding', verw=['resurrectio'])
N('sessio, sessionis, v.', 'het zitten, zitting | zetel', verw=['sedeo'])
N('salvatio, salvationis, v.', 'redding, behoud', verw=['salvator', 'salus'])
N('sanctificatio, sanctificationis, v.', 'heiliging | heiligdom', verw=['sanctus'])
N('servatio, servationis, v.', 'bewaring, behoud', verw=['servo'])
N('plantatio, plantationis, v.', 'beplanting, aanplant | het planten', verw=['planto'])
N('plasmatio, plasmationis, v.', 'vorming, boetsering | maaksel', verw=['plasma'])
N('portio, portionis, v.', 'deel, aandeel | portie', verw=['pars'])
N('probatio, probationis, v.', 'beproeving, toetsing | bewijs', verw=['probo'])
N('redditio, redditionis, v.', 'teruggave, vergelding', verw=['reddo'])
N('receptio, receptionis, v.', 'ontvangst, opname', verw=['recipio'])
N('requietio, requietionis, v.', 'rust, verpozing', verw=['requies'])
N('iussio, iussionis, v.', 'bevel, opdracht', verw=['iubeo'])
N('indignatio, indignationis, v.', 'verontwaardiging, toorn', verw=['indignor'])
N('intermissio, intermissionis, v.', 'onderbreking, tussenpoos',
  toel='"sine intermissione" — zonder ophouden.', verw=['intermitto'])
N('commotio, commotionis, v.', 'beweging, beroering | opschudding', verw=['commoveo'])
N('conmigratio, conmigrationis, v.', 'verhuizing, wegvoering | ballingschap',
  toel='Klassiek *commigratio*; hier de wegvoering naar Babylon.')
N('conculcatio, conculcationis, v.', 'vertrapping, vertreding', verw=['conculco'])
N('circumventio, circumventionis, v.', 'omsingeling | bedrog, misleiding')
N('conventio, conventionis, v.', 'samenkomst | overeenkomst, afspraak')
N('adinventio, adinventionis, v.', 'uitvinding, vondst | list, streek',
  toel='In de Vulgaat meestal ongunstig: de eigen bedenksels van de mens tegenover Gods wet.')
N('occisio, occisionis, v.', 'het doden, slachting', verw=['occido'])
N('oblatio, oblationis, v.', 'aanbieding | offergave, offer', verw=['offero'])
N('percussio, percussionis, v.', 'slag, het slaan', verw=['percutio'])
N('violatio, violationis, v.', 'schending, ontheiliging', verw=['violo'])
N('spretio, spretionis, v.', 'versmading, minachting', verw=['sperno'])
N('sponsio, sponsionis, v.', 'plechtige belofte, verbintenis', verw=['sponsa'])
N('distinctio, distinctionis, v.', 'onderscheid, scheiding | indeling')
N('devoratio, devorationis, v.', 'het verslinden, verslinding', verw=['devoro'])
N('direptio, direptionis, v.', 'plundering, roof', verw=['diripio', 'rapina'])
N('directio, directionis, v.', 'het rechtmaken, richting | rechtheid', verw=['dirigo'])
N('desolatio, desolationis, v.', 'verwoesting, verlatenheid')
N('defatigatio, defatigationis, v.', 'uitputting, vermoeidheid', verw=['fatigo'])
N('destructio, destructionis, v.', 'afbraak, verwoesting', verw=['destruo'])
N('constabilitio, constabilitionis, v.', 'bevestiging, vaste grondslag',
  toel='Laat-Latijns woord, vrijwel alleen in 4 Ezra; het tegendeel is `inconstabilitio`.')
N('inconstabilitio, inconstabilitionis, v.', 'onvastheid, wankelheid',
  verw=['constabilitio'])
N('exteritio, exteritionis, v.', 'uitwrijving, het uitwrijven van korenaren',
  verw=['extero'])
N('procreatio, procreationis, v.', 'voortbrenging, verwekking', verw=['procreo'])
N('interpretatum, interpretati, o.', 'uitlegging, verklaard woord', verw=['interpretor'])
N('fames, famis, v.', 'honger | hongersnood', i=True)
N('nubes, nubis, v.', 'wolk | zwerm, menigte', i=True, verw=['nimbus'],
  extra={'nubs': 'nominatief ev. (late nevenvorm van nubes)'})
N('sedes, sedis, v.', 'zetel, zitplaats | woonplaats, verblijf', i=True, verw=['thronus'])
N('civis, civis, m.', 'burger, stadsgenoot', i=True, verw=['civitas'])
N('finis, finis, m.', 'grens, einde | doel | (meervoud) gebied', i=True,
  toel='"finis saeculi" — het einde van de wereld; in 4 Ezra het brandpunt van elke vraag.',
  verw=['initium', 'finio'])
N('ignis, ignis, m.', 'vuur | brand | vuurgloed', i=True, verw=['flamma'])
N('navis, navis, v.', 'schip, vaartuig', i=True)
N('orbis, orbis, m.', 'kring, cirkel | schijf | (orbis terrarum) de aardbol, de wereld',
  i=True, verw=['mundus'])
N('panis, panis, m.', 'brood | voedsel', i=True)
N('piscis, piscis, m.', 'vis', i=True)
N('sitis, sitis, v.', 'dorst | droogte', i=True,
  extra={'siti': 'ablatief ev. — door dorst'})
N('collis, collis, m.', 'heuvel', i=True, verw=['mons'])
N('vestis, vestis, v.', 'kleed, gewaad | kleding', i=True, verw=['vestimentum'])
N('grando, grandinis, v.', 'hagel, hagelbui')
N('uredo, uredinis, v.', 'brand, korenbrand | schroeiing')
N('virgo, virginis, v.', 'meisje, jonge vrouw | maagd')
N('arbor, arboris, v.', 'boom | mast', verw=['lignum'])
N('labor, laboris, m.', 'inspanning, arbeid | moeite, last', verw=['laboro'])
N('dolor, doloris, m.', 'pijn, smart | verdriet | verontwaardiging', verw=['doleo'])
N('timor, timoris, m.', 'vrees, angst | ontzag', verw=['timeo'])
N('odor, odoris, m.', 'geur, reuk | walm', verw=['odoramentum'])
N('honor, honoris, m.', 'eer, aanzien | ereambt | eerbewijs', verw=['honestas'])
N('tremor, tremoris, m.', 'beving, siddering | aardbeving', verw=['tremo'])
N('vapor, vaporis, m.', 'damp, wasem | hitte')
N('ardor, ardoris, m.', 'gloed, brand | hartstocht', verw=['ardeo'])
N('color, coloris, m.', 'kleur | schijn, voorwendsel')
N('splendor, splendoris, m.', 'glans, schittering | luister', verw=['splendide'])
N('pulvis, pulveris, m.', 'stof, stuifzand | as')
N('cinis, cineris, m.', 'as | as van de doden', verw=['pulvis'])
N('mos, moris, m.', 'gewoonte, gebruik | (meervoud) zeden, karakter')
N('flos, floris, m.', 'bloem, bloesem | bloei', verw=['floreo'])
N('custos, custodis, m.', 'bewaker, wachter | hoeder', verw=['custodio'])
N('sacerdos, sacerdotis, m.', 'priester | offeraar')
N('heres, heredis, m.', 'erfgenaam', verw=['hereditas'])
N('merces, mercedis, v.', 'loon, beloning | huur | prijs', verw=['praemium'])
N('carbo, carbonis, m.', 'kool, houtskool | gloeiende kool')
N('coturnix, coturnicis, v.', 'kwartel')
N('fornax, fornacis, v.', 'oven, smeltoven',
  toel='"fornax terrae" — de aarde als smeltoven, beeld van de beproeving in 4 Ezra 6.')
N('calix, calicis, m.', 'beker, drinkschaal | kelk')
N('grex, gregis, m.', 'kudde | schare, groep', verw=['pastor'])
N('vertex, verticis, m.', 'draaikolk | kruin, top | hoogste punt')
N('unguis, unguis, m.', 'nagel | klauw', i=True)
N('aer, aeris, m.', 'lucht, dampkring | luchtruim',
  toel='Grieks leenwoord; de accusatief is `aerem` of `aera`.')
N('venter, ventris, m.', 'buik | moederschoot | binnenste', i=True, verw=['matrix'])
N('turris, turris, v.', 'toren | burcht', i=True)
N('imago, imaginis, v.', 'beeld, afbeelding | evenbeeld | verschijning', verw=['similitudo'])
N('origo, originis, v.', 'oorsprong, begin | afkomst')
N('ratio, rationis, v.', 'berekening | reden, verstand | wijze, methode')
N('regio, regionis, v.', 'streek, gebied | richting | landstreek', verw=['terra', 'provincia'])
N('legio, legionis, v.', 'legioen, legerafdeling')
N('plebs, plebis, v.', 'volk, gewone bevolking | menigte', verw=['populus'])
N('stirps, stirpis, v.', 'stam, wortel | geslacht, afstamming', i=True)
N('robur, roboris, o.', 'eikenhout | kracht, sterkte')
N('agmen, agminis, o.', 'stoet, drom | legerschaar')
N('crimen, criminis, o.', 'beschuldiging | misdaad, schuld')
N('culmen, culminis, o.', 'top, hoogtepunt | nok')
N('examen, examinis, o.', 'zwerm | onderzoek, weging')
N('fulmen, fulminis, o.', 'bliksem, bliksemschicht')
N('germen, germinis, o.', 'spruit, kiem | loot', verw=['germino'])
N('stramen, straminis, o.', 'stro, strooisel', verw=['stipula'])
N('litus, litoris, o.', 'kust, oever, strand')
N('onus, oneris, o.', 'last, vracht | zware plicht')
N('scelus, sceleris, o.', 'misdaad, wandaad | goddeloosheid')
N('vulgus, vulgi, o.', 'volksmenigte, het gewone volk', verw=['populus'])

# --- 4e verbuiging ------------------------------------------------------
N('fructus, fructus, m.', 'vrucht, opbrengst | genot, voordeel',
  toel='"fructus legis" — de vrucht van de wet; in 4 Ezra het beeld voor wat het volk had '
       'moeten voortbrengen.', verw=['fructifico'])
N('spiritus, spiritus, m.', 'adem, ademtocht | wind | geest, ziel | de Geest',
  verw=['anima', 'flatus'])
N('manus, manus, v.', 'hand | macht, geweld | schare, troep')
N('domus, domus, v.', 'huis, woning | huisgezin, geslacht',
  toel='Verbuigt gemengd: naast de vormen van de 4e verbuiging komen ook `domo` en `domum` '
       'van de 2e voor.', extra={'domo': 'ablatief ev. — uit het huis',
                                 'domos': 'accusatief mv. — de huizen'})
N('fluctus, fluctus, m.', 'golf, branding | onstuimigheid', verw=['mare', 'aqua'])
N('sensus, sensus, m.', 'waarneming, gevoel | verstand, inzicht | betekenis', verw=['mens'])
N('exercitus, exercitus, m.', 'leger, krijgsmacht | oefening')
N('aspectus, aspectus, m.', 'aanblik, gezicht | verschijning', verw=['aspicio'])
N('exitus, exitus, m.', 'uitgang, uittocht | afloop, einde | dood', verw=['exeo'])
N('introitus, introitus, m.', 'ingang, toegang | intocht', verw=['introeo'])
N('transitus, transitus, m.', 'doortocht, overgang | het voorbijgaan', verw=['transeo'])
N('interitus, interitus, m.', 'ondergang, vernietiging | dood', verw=['intereo'])
N('impetus, impetus, m.', 'aanval, aandrang | vaart, kracht')
N('motus, motus, m.', 'beweging | opschudding, oproer | aandoening', verw=['moveo'])
N('gemitus, gemitus, m.', 'gezucht, gekreun | geweeklaag', verw=['gemo'])
N('gressus, gressus, m.', 'schrede, gang | het gaan')
N('gustus, gustus, m.', 'het proeven, smaak | voorproefje', verw=['gusto'])
N('luctus, luctus, m.', 'rouw, droefheid | rouwbetoon', verw=['lugeo'])
N('planctus, planctus, m.', 'weeklacht, rouwmisbaar', verw=['plango'])
N('visus, visus, m.', 'het zien, gezichtsvermogen | aanblik, verschijning', verw=['video'])
N('vultus, vultus, m.', 'gelaat, gelaatsuitdrukking | blik', verw=['facies'])
N('lacus, lacus, m.', 'meer, waterbekken | put, kuil')
N('casus, casus, m.', 'val | toeval, lot | ongeluk', verw=['cado'])
N('actus, actus, m.', 'handeling, daad | het drijven', prio=1, verw=['ago'])
N('auditus, auditus, m.', 'het horen, gehoor | bericht, gerucht', prio=1, verw=['audio'])
N('excessus, excessus, m.', 'het heengaan, vertrek | dood | geestvervoering',
  toel='"in excessu mentis" — in geestvervoering; de toestand waarin Ezra de visioenen ontvangt.',
  verw=['excedo'])
N('principatus, principatus, m.', 'eerste plaats, heerschappij | overheid',
  verw=['princeps', 'imperium'])
N('potentatus, potentatus, m.', 'macht, heerschappij', verw=['potestas'])
N('ducatus, ducatus, m.', 'leiding, aanvoering | veldheerschap', verw=['dux'])
N('cruciatus, cruciatus, m.', 'foltering, marteling | pijn', verw=['crucio'])
N('sibilatus, sibilatus, m.', 'gesis, gefluit')
N('aestus, aestus, m.', 'hitte, gloed | branding, deining')
N('flatus, flatus, m.', 'het blazen, ademtocht | windvlaag', verw=['spiritus'])
N('fetus, fetus, m.', 'het baren, worp | vrucht, jong')
N('partus, partus, m.', 'het baren, geboorte | vrucht, kind', prio=-1, verw=['pario'])
N('status, status, m.', 'stand, houding | toestand, staat', verw=['sto'])
N('tumultus, tumultus, m.', 'rumoer, oproer | verwarring')
N('sinus, sinus, m.', 'kromming, plooi | boezem, schoot | baai')
N('victus, victus, m.', 'levensonderhoud, voedsel | levenswijze', verw=['vivo'])
N('conspectus, conspectus, m.', 'aanblik, gezicht | tegenwoordigheid',
  toel='"in conspectu Domini" — voor het aangezicht van de Heere.', verw=['conspicio'])
N('gelu, gelus, o.', 'vorst, ijzige kou | ijs')
N('cornu, cornus, o.', 'hoorn | punt, uiteinde | vleugel van een leger')
N('portus, portus, m.', 'haven | toevluchtsoord')
N('census, census, m.', 'schatting, vermogen | volkstelling')
N('senatus, senatus, m.', 'raad van oudsten, senaat')

# --- 5e verbuiging ------------------------------------------------------
N('dies, diei, m.', 'dag | daglicht | tijdstip, termijn',
  toel='In de Vulgaat vaak vrouwelijk wanneer het om een bepaalde dag of termijn gaat: '
       '"dies iudicii", de dag van het oordeel.', verw=['nox', 'tempus'])
N('res, rei, v.', 'zaak, ding | omstandigheid | bezit, vermogen')
N('facies, faciei, v.', 'gedaante, uiterlijk | gelaat, aangezicht | oppervlak',
  toel='"a facie" — van voor het aangezicht van, dus: vanwege. Een hebraïsme in de Vulgaat.',
  verw=['vultus', 'os'])
N('species, speciei, v.', 'aanblik, uiterlijk | schoonheid | soort, gedaante')
N('fides, fidei, v.', 'trouw, betrouwbaarheid | vertrouwen, geloof | belofte',
  verw=['fidelis'])
N('spes, spei, v.', 'hoop, verwachting')
N('requies, requiei, v.', 'rust, verpozing | de eeuwige rust',
  toel='Verbuigt gemengd: naast de 5e verbuiging komen ook de 3e-verbuigingsvormen '
       '`requietis`, `requietem` voor. In 4 Ezra de rust die de zielen na de dood wacht.',
  extra={'requiem': 'accusatief ev. — de rust', 'requietis': 'genitief ev. — van de rust',
         'requiete': 'ablatief ev. — in rust'}, verw=['requietio', 'pausa'])


# ===========================================================================
# 6. Bijvoeglijke naamwoorden
# ===========================================================================

# --- 1e/2e klasse --------------------------------------------------------
A('bonus, bona, bonum', 'goed, deugdelijk | rechtschapen | gunstig, voordelig',
  comp=False, sup=False,
  toel='De trappen zijn onregelmatig: melior (beter), optimus (best).', verw=['malus'])
A('malus, mala, malum', 'slecht, kwaad | boosaardig | ongelukkig, rampzalig',
  comp=False, sup=False,
  toel='De trappen zijn onregelmatig: peior (slechter), pessimus (slechtst).', verw=['bonus'])
A('magnus, magna, magnum', 'groot, omvangrijk | machtig, aanzienlijk | hevig',
  comp=False, sup=False,
  toel='De trappen zijn onregelmatig: maior (groter), maximus (grootst).', verw=['parvus'])
A('multus, multa, multum', 'veel, talrijk | uitgebreid', comp=False, sup=False,
  toel='De vergrotende trap is `plures, plura` (meer), de overtreffende `plurimus` (zeer veel).',
  verw=['plus'])
A('parvus, parva, parvum', 'klein, gering | jong | onbeduidend', comp=False, sup=False,
  verw=['parvulus', 'magnus'])
A('parvulus, parvula, parvulum', 'heel klein | (als zelfstandig naamwoord) kind, kleintje',
  comp=False, sup=False, verw=['parvus'])
A('altus, alta, altum', 'hoog | diep | verheven', verw=['altitudo', 'altissimus'])
A('altissimus, altissima, altissimum',
  'de Allerhoogste (God) | zeer hoog, zeer diep (overtreffende trap van altus)',
  comp=False, sup=False,
  toel='In 4 Ezra is `Altissimus` de gewone aanduiding van God — vaker nog dan Dominus of Deus.',
  verw=['altus', 'excelsus'])
A('sanctus, sancta, sanctum', 'gewijd, heilig | onschendbaar | eerbiedwaardig',
  verw=['sanctifico'])
A('iustus, iusta, iustum', 'rechtvaardig, billijk | rechtmatig | (als zelfstandig naamwoord) '
  'de rechtvaardige', verw=['iustitia', 'iniustus'])
A('iniustus, iniusta, iniustum', 'onrechtvaardig, onbillijk', verw=['iustus', 'iniquus'])
A('iniquus, iniqua, iniquum', 'ongelijk, oneffen | onbillijk, onrechtvaardig | vijandig',
  verw=['iniquitas'])
A('impius, impia, impium', 'zonder ontzag, goddeloos | misdadig', verw=['impietas', 'pius'])
A('pius, pia, pium', 'plichtsgetrouw, vroom | liefdevol', verw=['impius'])
A('vanus, vana, vanum', 'leeg, ijdel | zonder inhoud, nutteloos | bedrieglijk', verw=['vanitas'])
A('verus, vera, verum', 'waar, echt | oprecht | rechtmatig', verw=['veritas'])
A('plenus, plena, plenum', 'vol, gevuld | volledig | verzadigd', verw=['plenitudo', 'vacuus'])
A('vacuus, vacua, vacuum', 'leeg, onbezet | vrij van | vergeefs', verw=['plenus'])
A('aeternus, aeterna, aeternum', 'eeuwig, zonder einde | onvergankelijk',
  toel='"in aeternum" — voor eeuwig, tot in eeuwigheid.', verw=['aeternitas', 'sempiternus'])
A('sempiternus, sempiterna, sempiternum', 'eeuwigdurend, altijddurend',
  verw=['aeternus', 'semper'])
A('mortuus, mortua, mortuum', 'gestorven, dood | (als zelfstandig naamwoord) de dode',
  comp=False, sup=False, verw=['morior', 'mors', 'vivus'])
A('vivus, viva, vivum', 'levend, in leven | levendig, vers', comp=False, sup=False,
  verw=['vivo', 'mortuus'])
A('beatus, beata, beatum', 'gelukkig, gezegend | zalig | rijk', verw=['beatifico'])
A('caecus, caeca, caecum', 'blind | duister, verborgen')
A('certus, certa, certum', 'vaststaand, zeker | betrouwbaar | bepaald')
A('dignus, digna, dignum', 'waardig, passend | verdienend', verw=['indignus'])
A('indignus, indigna, indignum', 'onwaardig, onverdiend | schandelijk', verw=['dignus'])
A('humanus, humana, humanum', 'menselijk, van de mens | beschaafd, menslievend', verw=['homo'])
A('humidus, humida, humidum', 'vochtig, nat')
A('idoneus, idonea, idoneum', 'geschikt, bekwaam | passend', comp=False, sup=False)
A('infructuosus, infructuosa, infructuosum', 'onvruchtbaar, zonder vrucht', verw=['fructus'])
A('innoxius, innoxia, innoxium', 'onschadelijk | onschuldig', comp=False, sup=False)
A('invalidus, invalida, invalidum', 'zwak, krachteloos | ziekelijk', verw=['validus'])
A('validus, valida, validum', 'sterk, krachtig | gezond | invloedrijk',
  bijw='validissime', verw=['invalidus', 'valde'])
A('laboriosus, laboriosa, laboriosum', 'moeizaam, zwaar | werkzaam, noest', verw=['labor'])
A('modicus, modica, modicum', 'matig, gering | klein, bescheiden', verw=['modus'])
A('molestus, molesta, molestum', 'lastig, hinderlijk | bezwaarlijk')
A('notus, nota, notum', 'bekend, vertrouwd | beroemd', verw=['nosco'])
A('piceus, picea, picea', 'pikzwart, van pek', comp=False, sup=False)
A('proximus, proxima, proximum', 'zeer nabij, naast | eerstvolgend | (als zelfstandig '
  'naamwoord) de naaste', comp=False, sup=False, verw=['prope', 'proximo'])
A('rectus, recta, rectum', 'recht, rechtlijnig | juist, rechtschapen', verw=['dirigo'])
A('solus, sola, solum', 'alleen, enig | eenzaam | uitsluitend', comp=False, sup=False,
  verw=['solummodo'])
A('spatiosus, spatiosa, spatiosum', 'ruim, uitgestrekt | langdurig', verw=['spatium'])
A('stultus, stulta, stultum', 'dwaas, onverstandig | dom', verw=['insipiens'])
A('tantus, tanta, tantum', 'zo groot, zoveel | zo belangrijk', comp=False, sup=False,
  verw=['quantus', 'tot'])
A('quantus, quanta, quantum', 'hoe groot? hoeveel? | zo groot als', comp=False, sup=False,
  verw=['tantus'])
A('totus, tota, totum', 'geheel, heel | volledig', comp=False, sup=False)
A('varius, varia, varium', 'veelkleurig, bont | verschillend, afwisselend')
A('copiosus, copiosa, copiosum', 'overvloedig, rijk voorzien | talrijk', verw=['copia'])
A('angustus, angusta, angustum', 'nauw, smal | benauwd, beperkt',
  toel='De "nauwe ingangen" van 4 Ezra 7:6-9 zijn het beeld voor de weg naar het leven.',
  verw=['angustia'])
A('apertus, aperta, apertum', 'open, onbedekt | duidelijk, openlijk', verw=['aperio'])
A('aridus, arida, aridum', 'droog, dor | schraal')
A('carus, cara, carum', 'dierbaar, geliefd | kostbaar, duur')
A('celsus, celsa, celsum', 'hoog, verheven | trots', verw=['excelsus'])
A('coruscus, corusca, coruscum', 'flikkerend, bliksemend | glanzend', comp=False, sup=False,
  verw=['corusco'])
A('excelsus, excelsa, excelsum', 'hoog verheven, verheven | de hoogte', verw=['celsus', 'altus'])
A('horridus, horrida, horridum', 'ruw, ruig | huiveringwekkend', verw=['horreo'])
A('inmensus, inmensa, inmensum', 'onmetelijk, grenzeloos',
  toel='Klassiek geschreven als *immensus*.', verw=['mensura'])
A('inmaturus, inmatura, inmaturum', 'onrijp, ontijdig | voortijdig',
  toel='Klassiek *immaturus*.')
A('supernus, superna, supernum', 'bovenste, hemels | van boven', verw=['super'])
A('sinister, sinistra, sinistrum', 'links | ongunstig, onheilspellend', verw=['dexter'])
A('dexter, dextra, dextrum', 'rechts | gunstig | (dextera, als zelfstandig naamwoord) '
  'de rechterhand', verw=['sinister'],
  extra={'dextera': 'nominatief/ablatief ev. vrouwelijk (volle vorm) — de rechterhand',
         'dexteram': 'accusatief ev. vrouwelijk (volle vorm)'})
A('secretus, secreta, secretum', 'afgezonderd, verborgen | geheim', verw=['secretum'])
A('subitus, subita, subitum', 'plotseling, onverwacht')
A('perpetuus, perpetua, perpetuum', 'onafgebroken, blijvend | eeuwigdurend')
A('praeteritus, praeterita, praeteritum', 'voorbij, verstreken | vroeger',
  comp=False, sup=False, prio=1, verw=['praetereo'])
A('futurus, futura, futurum', 'toekomstig, aanstaande | (als zelfstandig naamwoord) '
  'de toekomst', comp=False, sup=False, prio=-1,
  toel='Eigenlijk het toekomend deelwoord van `sum`; in 4 Ezra vast onderdeel van '
       '"futurum saeculum", de komende wereld.', verw=['sum'])
A('pessimus, pessima, pessimum', 'zeer slecht, allerslechtst (overtreffende trap van malus)',
  comp=False, sup=False, prio=-1, verw=['malus'])
A('plurimus, plurima, plurimum', 'zeer veel, de meeste (overtreffende trap van multus)',
  comp=False, sup=False, prio=-1, verw=['multus'])
A('maximus, maxima, maximum', 'zeer groot, de grootste (overtreffende trap van magnus)',
  comp=False, sup=False, prio=-1, verw=['magnus'])
A('novissimus, novissima, novissimum', 'de laatste, de uiterste | het einde',
  comp=False, sup=False,
  toel='In de Vulgaat het gewone woord voor "laatste": "novissimi dies", de laatste dagen.',
  verw=['novus'])
A('novus, nova, novum', 'nieuw, pas ontstaan | ongewoon', comp=False, verw=['novissimus'])
A('purus, pura, purum', 'zuiver, rein | onvermengd')
A('sacer, sacra, sacrum', 'gewijd, heilig | vervloekt', verw=['sanctus'])
A('serenus, serena, serenum', 'helder, onbewolkt | opgewekt')
A('siccus, sicca, siccum', 'droog, dor', verw=['sicco'])
A('salsus, salsa, salsum', 'zout, gezouten | scherp')
A('miser, misera, miserum', 'ellendig, rampzalig | beklagenswaardig', verw=['misericordia'])
A('paucus, pauca, paucum', 'weinig, gering in aantal', comp=False, sup=False,
  verw=['multus'])
A('electus, electa, electum', 'uitverkoren, uitgelezen | (als zelfstandig naamwoord) '
  'de uitverkorene', comp=False, sup=False, prio=-1, verw=['eligo'])
A3('inmortalis, inmortale', 'onsterfelijk, onvergankelijk', verw=['mortalis'])
A3('agrestis, agreste', 'op het land levend, wild | boers', verw=['ager'])
A('opacus, opaca, opacum', 'schaduwrijk, donker')
A('candidus, candida, candidum', 'stralend wit, blinkend | oprecht')
A('splendidus, splendida, splendidum', 'schitterend, glanzend | luisterrijk',
  verw=['splendor'])
A('honorificus, honorifica, honorificum', 'eervol, eerbewijzend', verw=['honor'])
A('pomifer, pomifera, pomiferum', 'vruchtdragend', comp=False, sup=False)
A('bellicosus, bellicosa, bellicosum', 'oorlogszuchtig, strijdbaar', verw=['bellum'])
A('curiosus, curiosa, curiosum', 'nieuwsgierig, weetgierig | zorgvuldig')
A('timoratus, timorata, timoratum', 'godvrezend, eerbiedig',
  toel='Laat-Latijnse vorming bij `timor`: wie ontzag heeft voor God.', verw=['timor'])
A3('carnalis, carnale', 'vleselijk, lichamelijk', verw=['caro'])
A('impiger, impigra, impigrum', 'onvermoeibaar, ijverig')
A('mancus, manca, mancum', 'verminkt, gebrekkig | onvolledig')
A('claudus, clauda, claudum', 'kreupel, mank')
A3('pinguis, pingue', 'vet, vruchtbaar | log')
A3('sterilis, sterile', 'onvruchtbaar, kinderloos | schraal')
A('gravidus, gravida, gravidum', 'zwaar beladen | zwanger', verw=['praegnans'])

# --- 3e klasse -----------------------------------------------------------
A3('omnis, omne', 'al, geheel | ieder, elk | (meervoud) allen, alle dingen',
   comp=False, sup=False,
   toel='"omnia" (alle dingen) is in 4 Ezra vaak een zelfstandig gebruikt onzijdig meervoud.')
A3('similis, simile', 'gelijk, gelijkend | soortgelijk', verw=['similitudo'])
A3('fortis, forte', 'sterk, krachtig | dapper, standvastig', verw=['fortitudo'])
A3('gravis, grave', 'zwaar | drukkend, lastig | ernstig, gewichtig')
A3('brevis, breve', 'kort, klein | kortstondig')
A3('dulcis, dulce', 'zoet | aangenaam, lieflijk')
A3('facilis, facile', 'gemakkelijk, moeiteloos | inschikkelijk', bijw='facile',
   verw=['facio', 'facilius'])
A3('fidelis, fidele', 'trouw, betrouwbaar | gelovig', verw=['fides'])
A3('humilis, humile', 'laag, nederig | gering, onaanzienlijk', verw=['humilitas'])
A3('levis, leve', 'licht (van gewicht) | onbeduidend | wispelturig')
A3('terribilis, terribile', 'schrikwekkend, verschrikkelijk', verw=['terreo'])
A3('horribilis, horribile', 'huiveringwekkend, afschuwelijk', verw=['horreo'])
A3('corruptibilis, corruptibile', 'vergankelijk, aan bederf onderhevig',
   verw=['corruptio', 'incorruptio'])
A3('possibilis, possibile', 'mogelijk, uitvoerbaar', verw=['possum'])
A3('mirabilis, mirabile', 'wonderbaarlijk, verbazingwekkend', verw=['miror'])
A3('miserabilis, miserabile', 'beklagenswaardig, jammerlijk', verw=['miser'])
A3('mortalis, mortale', 'sterfelijk, vergankelijk | (als zelfstandig naamwoord) sterveling',
   verw=['mors', 'inmortalis'])
A3('multiformis, multiforme', 'veelvormig, veelsoortig', verw=['multus'])
A3('innumerabilis, innumerabile', 'ontelbaar, onnoemelijk veel', verw=['numerus'])
A3('inaestimabilis, inaestimabile', 'onschatbaar, niet te waarderen', verw=['aestimo'])
A3('investigabilis, investigabile', 'ondoorgrondelijk, niet na te speuren',
   toel='In de Vulgaat ontkennend bedoeld: wat niet uit te vorsen is.', verw=['investigo'])
A3('inconprehensibilis, inconprehensibile', 'onbegrijpelijk, onvatbaar',
   toel='Klassiek *incomprehensibilis*.', verw=['conprehendo'])
A3('inimitabilis, inimitabile', 'onnavolgbaar, weergaloos')
A3('indeficiens, indeficientis', 'onuitputtelijk, niet ophoudend', een=True,
   verw=['deficio'])
A3('hilaris, hilare', 'vrolijk, opgewekt')
A3('tristis, triste', 'droevig, bedroefd | somber, streng', verw=['tristitia'])
A3('talis, tale', 'zodanig, van dien aard | zulk een', comp=False, sup=False, verw=['qualis'])
A3('qualis, quale', 'hoedanig? van welke aard? | zoals', comp=False, sup=False, verw=['talis'])
A3('omnipotens, omnipotentis', 'almachtig, alvermogend', een=True, verw=['potens', 'possum'])
A3('potens, potentis', 'machtig, invloedrijk | in staat tot', een=True,
   verw=['possum', 'potestas'])
A3('praesens, praesentis', 'aanwezig, tegenwoordig | van dit ogenblik', een=True,
   toel='"praesens saeculum" — de tegenwoordige wereld, tegenover de komende.', verw=['adsum'])
A3('sapiens, sapientis', 'wijs, verstandig | (als zelfstandig naamwoord) een wijze', een=True,
   verw=['sapientia', 'sapio'])
A3('insipiens, insipientis', 'onverstandig, dwaas', een=True, verw=['sapiens', 'stultus'])
A3('misericors, misericordis', 'barmhartig, medelijdend', een=True, verw=['misericordia'])
A3('pauper, pauperis', 'arm, behoeftig', een=True, verw=['paupertas'],
   extra={'paupera': 'nominatief/ablatief ev. vrouwelijk (late nevenvorm naar de 1e klasse)'})
A('incredulus, incredula, incredulum', 'ongelovig, wantrouwend', verw=['incredulitas'])
A('ingratus, ingrata, ingratum', 'ondankbaar | onaangenaam')
A3('vetus, veteris', 'oud, uit vroeger tijd | vroeger', een=True, comp=False, sup=False)
A3('supplex, supplicis', 'smekend, ootmoedig', een=True)
A3('capax, capacis', 'ruim, veel bevattend | in staat tot', een=True, verw=['capio'])
A3('velox, velocis', 'snel, vlug', een=True, verw=['velocitas'])
A3('consors, consortis', 'deelgenoot, deelhebbend aan', een=True)
A3('superstes, superstitis', 'overlevend, in leven gebleven', een=True)
A('nudus, nuda, nudum', 'naakt, onbedekt | beroofd van')

# --- Vergrotende trappen die zelfstandig voorkomen -----------------------
X('maior', 'bijvoeglijk naamwoord (vergrotende trap)', 'maior, maius',
  'groter | ouder | belangrijker',
  {'maior': 'nominatief ev. mannelijk/vrouwelijk', 'maius': 'nominatief/accusatief ev. onzijdig',
   'maioris': 'genitief ev.', 'maiori': 'datief ev.', 'maiorem': 'accusatief ev. mannelijk/vrouwelijk',
   'maiore': 'ablatief ev.', 'maiores': 'nominatief/accusatief mv. mannelijk/vrouwelijk',
   'maiora': 'nominatief/accusatief mv. onzijdig', 'maiorum': 'genitief mv.',
   'maioribus': 'datief/ablatief mv.'}, verw=['magnus', 'magis'])
X('melior', 'bijvoeglijk naamwoord (vergrotende trap)', 'melior, melius', 'beter | voortreffelijker',
  {'melior': 'nominatief ev. mannelijk/vrouwelijk', 'melioris': 'genitief ev.',
   'meliori': 'datief ev.', 'meliorem': 'accusatief ev. mannelijk/vrouwelijk',
   'meliore': 'ablatief ev.', 'meliores': 'nominatief/accusatief mv. mannelijk/vrouwelijk',
   'meliora': 'nominatief/accusatief mv. onzijdig', 'meliorum': 'genitief mv.',
   'melioribus': 'datief/ablatief mv.'}, verw=['bonus'])
X('peior', 'bijvoeglijk naamwoord (vergrotende trap)', 'peior, peius', 'slechter, erger',
  {'peior': 'nominatief ev. mannelijk/vrouwelijk', 'peius': 'nominatief/accusatief ev. onzijdig',
   'peiorem': 'accusatief ev. mannelijk/vrouwelijk', 'peiores': 'nominatief/accusatief mv.',
   'peiora': 'nominatief/accusatief mv. onzijdig'}, verw=['malus'])
X('minor', 'bijvoeglijk naamwoord (vergrotende trap)', 'minor, minus',
  'kleiner, geringer | jonger',
  {'minor': 'nominatief ev. mannelijk/vrouwelijk', 'minoris': 'genitief ev.',
   'minorem': 'accusatief ev. mannelijk/vrouwelijk', 'minores': 'nominatief/accusatief mv.',
   'minora': 'nominatief/accusatief mv. onzijdig', 'minoribus': 'datief/ablatief mv.',
   'minimo': 'datief/ablatief ev. (overtreffende trap: het minste)'}, verw=['parvus'])
X('prior', 'bijvoeglijk naamwoord (vergrotende trap)', 'prior, prius',
  'de eerste van twee, vroegere | voorafgaande',
  {'prior': 'nominatief ev. mannelijk/vrouwelijk', 'prioris': 'genitief ev.',
   'priori': 'datief ev.', 'priorem': 'accusatief ev. mannelijk/vrouwelijk',
   'priore': 'ablatief ev.', 'priores': 'nominatief/accusatief mv. mannelijk/vrouwelijk',
   'priora': 'nominatief/accusatief mv. onzijdig', 'priorum': 'genitief mv.',
   'prioribus': 'datief/ablatief mv.'}, verw=['primus', 'prius'])
X('plures', 'bijvoeglijk naamwoord (vergrotende trap)', 'plures, plura',
  'meer, meerdere | verscheidene',
  {'plures': 'nominatief/accusatief mv. mannelijk/vrouwelijk',
   'plura': 'nominatief/accusatief mv. onzijdig', 'plurium': 'genitief mv.',
   'pluribus': 'datief/ablatief mv.'}, verw=['multus', 'plus'])
X('eminentior', 'bijvoeglijk naamwoord (vergrotende trap)', 'eminentior, eminentius',
  'hoger uitstekend, meer verheven',
  {'eminentior': 'nominatief ev. mannelijk/vrouwelijk',
   'eminentiorem': 'accusatief ev. mannelijk/vrouwelijk'}, verw=['emineo'])
X('timoratior', 'bijvoeglijk naamwoord (vergrotende trap)', 'timoratior, timoratius',
  'godvrezender, eerbiediger', {'timoratior': 'nominatief ev. mannelijk/vrouwelijk'},
  verw=['timoratus'])
X('ulterior', 'bijvoeglijk naamwoord (vergrotende trap)', 'ulterior, ulterius',
  'verder gelegen, verdergaand',
  {'ulterior': 'nominatief ev. mannelijk/vrouwelijk',
   'ulteriorem': 'accusatief ev. mannelijk/vrouwelijk'})
X('deterior', 'bijvoeglijk naamwoord (vergrotende trap)', 'deterior, deterius',
  'minder goed, slechter',
  {'deterior': 'nominatief ev. mannelijk/vrouwelijk',
   'deteriora': 'nominatief/accusatief mv. onzijdig'})


# ===========================================================================
# 7. Werkwoorden — 1e vervoeging (-are)
# ===========================================================================

V('do, dare, dedi, datum', 'geven, schenken | overhandigen | toestaan, verlenen',
  verw=['reddo', 'trado'])
V('sto, stare, steti', 'staan | stilstaan, standhouden | (met in) blijven bij')
V('amo, amare, amavi, amatum', 'liefhebben, beminnen | graag doen', verw=['amator'])
V('ambulo, ambulare, ambulavi, ambulatum', 'wandelen, gaan | zich gedragen, leven',
  toel='In de Vulgaat vaak overdrachtelijk: "in via Domini ambulare" — leven naar Gods weg.')
V('adpropinquo, adpropinquare, adpropinquavi, adpropinquatum', 'naderen, dichtbij komen',
  toel='Klassiek *appropinquare*.', verw=['adpropio', 'prope'])
V('adpropio, adpropiare, adpropiavi, adpropiatum', 'naderen, dichtbij komen',
  toel='Laat-Latijnse nevenvorm van adpropinquare.', verw=['adpropinquo'])
V('adsimilo, adsimilare, adsimilavi, adsimilatum', 'gelijkmaken, vergelijken | nabootsen',
  toel='Klassiek *assimilare*.', verw=['similis', 'similo'])
V('similo, similare, similavi, similatum', 'gelijken op, nabootsen', prio=-1,
  verw=['similis'])
V('aedifico, aedificare, aedificavi, aedificatum', 'bouwen, opbouwen | stichten',
  verw=['aedificium'])
V('aestimo, aestimare, aestimavi, aestimatum', 'schatten, waarderen | menen, oordelen')
V('adnuntio, adnuntiare, adnuntiavi, adnuntiatum', 'aankondigen, verkondigen | melden',
  toel='Klassiek *annuntiare*.', verw=['renuntio'])
V('renuntio, renuntiare, renuntiavi, renuntiatum', 'berichten, melden | opzeggen',
  verw=['adnuntio'])
V('accuso, accusare, accusavi, accusatum', 'aanklagen, beschuldigen', verw=['accusator'])
V('beatifico, beatificare, beatificavi, beatificatum', 'zalig prijzen, gelukkig maken',
  verw=['beatus'])
V('cogito, cogitare, cogitavi, cogitatum', 'denken, overwegen | van plan zijn',
  verw=['cogitatio', 'cogitamentum'])
V('clamo, clamare, clamavi, clamatum', 'roepen, schreeuwen | luid verkondigen',
  verw=['proclamo'])
V('proclamo, proclamare, proclamavi, proclamatum', 'uitroepen, luid verkondigen',
  verw=['clamo'])
V('commendo, commendare, commendavi, commendatum', 'toevertrouwen | aanbevelen')
V('confirmo, confirmare, confirmavi, confirmatum', 'versterken, bevestigen | bemoedigen',
  verw=['firmamentum'])
V('conforto, confortare, confortavi, confortatum', 'sterken, bemoedigen',
  toel='Laat-Latijns woord, in de Vulgaat gewoon voor "sterk maken".', verw=['fortis'])
V('congrego, congregare, congregavi, congregatum', 'samenbrengen, verzamelen',
  verw=['grex', 'colligo'])
V('conservo, conservare, conservavi, conservatum', 'bewaren, behouden | in stand houden',
  verw=['servo'])
V('considero, considerare, consideravi, consideratum', 'beschouwen, overwegen | nauwkeurig bezien')
V('conturbo, conturbare, conturbavi, conturbatum', 'in verwarring brengen, verontrusten',
  verw=['turbo', 'turbatio'])
V('turbo, turbare, turbavi, turbatum', 'in beroering brengen, verwarren', verw=['turba'])
V('contristo, contristare, contristavi, contristatum', 'bedroeven, droevig maken',
  verw=['tristis', 'tristor'])
V('creo, creare, creavi, creatum', 'scheppen, voortbrengen | benoemen, aanstellen',
  prio=-1, verw=['creator', 'creatura'])
V('crucio, cruciare, cruciavi, cruciatum', 'folteren, kwellen', verw=['cruciatus'])
V('curo, curare, curavi, curatum', 'zorgen voor, verzorgen | genezen', verw=['cura'])
V('demonstro, demonstrare, demonstravi, demonstratum', 'aanwijzen, tonen | aantonen',
  verw=['monstro', 'ostendo'])
V('monstro, monstrare, monstravi, monstratum', 'tonen, wijzen', verw=['demonstro'])
V('desidero, desiderare, desideravi, desideratum', 'verlangen naar, wensen | missen')
V('devasto, devastare, devastavi, devastatum', 'verwoesten, plunderen', verw=['vasto'])
V('vasto, vastare, vastavi, vastatum', 'verwoesten, leegmaken', verw=['devasto'])
V('devoro, devorare, devoravi, devoratum', 'verslinden, opslokken', verw=['devoratio'])
V('dono, donare, donavi, donatum', 'schenken, geven | kwijtschelden', verw=['do'])
V('educo, educare, educavi, educatum', 'opvoeden, grootbrengen | voeden',
  toel='Niet te verwarren met `educo, educere` (3e vervoeging): uitleiden. De perfectumvormen '
       'verschillen: educavi tegenover eduxi.', verw=['nutrio'])
V('enarro, enarrare, enarravi, enarratum', 'uitvoerig vertellen, uiteenzetten')
V('exorno, exornare, exornavi, exornatum', 'versieren, uitrusten', verw=['orno'])
V('orno, ornare, ornavi, ornatum', 'uitrusten, versieren', verw=['exorno'])
V('exulto, exultare, exultavi, exultatum', 'opspringen, juichen | jubelen',
  toel='In de handschriften ook geschreven als *exsulto*.')
V('festino, festinare, festinavi, festinatum', 'zich haasten, spoeden | bespoedigen')
V('glorifico, glorificare, glorificavi, glorificatum', 'verheerlijken, eren', verw=['gloria'])
V('gusto, gustare, gustavi, gustatum', 'proeven | genieten van', verw=['gustus'])
V('habito, habitare, habitavi, habitatum', 'wonen, verblijven | bewonen',
  verw=['inhabito', 'habitatio'])
V('inhabito, inhabitare, inhabitavi, inhabitatum', 'bewonen, wonen in', verw=['habito'])
V('honorifico, honorificare, honorificavi, honorificatum', 'eren, verheerlijken', verw=['honor'])
V('humilio, humiliare, humiliavi, humiliatum', 'vernederen, verlagen', verw=['humilis'])
V('impero, imperare, imperavi, imperatum', 'bevelen, gebieden | heersen over',
  verw=['imperium'])
V('inchoo, inchoare, inchoavi, inchoatum', 'beginnen, aanvangen', verw=['incipio'])
V('inflammo, inflammare, inflammavi, inflammatum', 'in brand steken, ontvlammen',
  verw=['flamma'])
V('interrogo, interrogare, interrogavi, interrogatum', 'vragen, ondervragen',
  toel='Het werkwoord dat het gesprek tussen Ezra en de engel draagt: telkens vraagt Ezra en '
       'antwoordt de engel.', verw=['rogo', 'respondeo'])
V('inrito, inritare, inritavi, inritatum', 'prikkelen, tergen | vertoornen',
  toel='Klassiek *irritare*.')
V('iucundo, iucundare, iucundavi, iucundatum', 'verblijden, verheugen | zich verheugen',
  verw=['iucunditas', 'gaudeo'])
V('iudico, iudicare, iudicavi, iudicatum', 'oordelen, rechtspreken | menen',
  verw=['iudex', 'iudicium'])
V('iustifico, iustificare, iustificavi, iustificatum', 'rechtvaardigen, rechtvaardig verklaren',
  verw=['iustus', 'iustitia'])
V('laboro, laborare, laboravi, laboratum', 'zich inspannen, zwoegen | lijden', verw=['labor'])
V('lanio, laniare, laniavi, laniatum', 'verscheuren, uiteenrukken')
V('laudo, laudare, laudavi, laudatum', 'prijzen, loven', verw=['conlaudo'])
V('conlaudo, conlaudare, conlaudavi, conlaudatum', 'luid prijzen, samen loven',
  toel='Klassiek *collaudare*.', verw=['laudo'])
V('levo, levare, levavi, levatum', 'oplichten, opheffen | verlichten', verw=['relevo'])
V('relevo, relevare, relevavi, relevatum', 'oplichten | verlichten, opbeuren', verw=['levo'])
V('libero, liberare, liberavi, liberatum', 'bevrijden, verlossen', verw=['libertas'])
V('maculo, maculare, maculavi, maculatum', 'bevlekken, bezoedelen')
V('mando, mandare, mandavi, mandatum', 'opdragen, bevelen | toevertrouwen',
  verw=['mandatum', 'praecipio'])
V('manduco, manducare, manducavi, manducatum', 'kauwen, eten',
  toel='In de Vulgaat het gewone woord voor "eten", waar het klassieke Latijn `edere` gebruikt.',
  verw=['comedo'])
V('memoro, memorare, memoravi, memoratum', 'vermelden, in herinnering brengen',
  verw=['memoria'])
V('mensuro, mensurare, mensuravi, mensuratum', 'meten, afmeten', verw=['mensura', 'metior'])
V('mortifico, mortificare, mortificavi, mortificatum', 'doden, ter dood brengen',
  verw=['mors', 'vivifico'])
V('multiplico, multiplicare, multiplicavi, multiplicatum', 'vermenigvuldigen, vermeerderen',
  verw=['multus'])
V('murmuro, murmurare, murmuravi, murmuratum', 'morren, mopperen | ruisen')
V('muto, mutare, mutavi, mutatum', 'veranderen, verwisselen', verw=['commuto'])
V('commuto, commutare, commutavi, commutatum', 'veranderen, omruilen', verw=['muto'])
V('nomino, nominare, nominavi, nominatum', 'noemen, bij name aanduiden', prio=-1,
  verw=['nomen'])
V('numero, numerare, numeravi, numeratum', 'tellen, opsommen', verw=['numerus'])
V('observo, observare, observavi, observatum', 'waarnemen, gadeslaan | in acht nemen')
V('occulto, occultare, occultavi, occultatum', 'verbergen, verheimelijken',
  verw=['abscondo'])
V('oro, orare, oravi, oratum', 'spreken, pleiten | bidden, smeken', verw=['oratio', 'deprecor'])
V('paro, parare, paravi, paratum', 'gereedmaken, bereiden | verschaffen', verw=['praeparo'])
V('praeparo, praeparare, praeparavi, praeparatum', 'voorbereiden, gereedmaken',
  toel='In 4 Ezra het woord voor wat God van tevoren bereid heeft: de wereld, het oordeel, '
       'het paradijs.', verw=['paro'])
V('pecco, peccare, peccavi, peccatum', 'een misstap doen, zondigen',
  verw=['peccatum', 'peccator'])
V('planto, plantare, plantavi, plantatum', 'planten, beplanten', verw=['plantatio'])
V('ploro, plorare, ploravi, ploratum', 'wenen, jammeren', verw=['fleo', 'lugeo'])
V('plasmo, plasmare, plasmavi, plasmatum', 'boetseren, vormen',
  toel='Grieks leenwoord; in de Vulgaat het woord voor Gods vormen van de mens uit klei.',
  verw=['plasma', 'figmentum'])
V('pondero, ponderare, ponderavi, ponderatum', 'wegen, afwegen | overwegen',
  verw=['pondus', 'statera'])
V('porto, portare, portavi, portatum', 'dragen, vervoeren', verw=['fero'])
V('probo, probare, probavi, probatum', 'beproeven, toetsen | goedkeuren, bewijzen',
  verw=['probatio'])
V('procreo, procreare, procreavi, procreatum', 'voortbrengen, verwekken', verw=['creo'])
V('proximo, proximare, proximavi, proximatum', 'naderen, dichtbij komen',
  verw=['proximus', 'adpropinquo'])
V('puto, putare, putavi, putatum', 'menen, denken | achten, houden voor')
V('refrigero, refrigerare, refrigeravi, refrigeratum', 'afkoelen, verkwikken | verlichten')
V('regno, regnare, regnavi, regnatum', 'als vorst heersen, regeren | heerschappij voeren',
  verw=['rex', 'regnum'])
V('reservo, reservare, reservavi, reservatum', 'bewaren, achterhouden', verw=['servo'])
V('revoco, revocare, revocavi, revocatum', 'terugroepen | herroepen', verw=['voco'])
V('rogo, rogare, rogavi, rogatum', 'vragen, verzoeken | smeken', verw=['interrogo'])
V('salvo, salvare, salvavi, salvatum', 'redden, behouden',
  toel='Laat-Latijns, gevormd bij `salvus`; in de Vulgaat het gewone woord voor "verlossen".',
  verw=['salvus', 'salvator'])
V('sanctifico, sanctificare, sanctificavi, sanctificatum', 'heiligen, wijden',
  verw=['sanctus'])
V('scrutino, scrutinare, scrutinavi, scrutinatum', 'doorzoeken, navorsen',
  toel='Laat-Latijnse nevenvorm van `scrutor`, vooral in 4 Ezra.', verw=['scruto'])
V('scruto, scrutare, scrutavi, scrutatum', 'doorzoeken, onderzoeken', verw=['scrutino'])
V('semino, seminare, seminavi, seminatum', 'zaaien, uitzaaien', verw=['semen', 'sero'])
V('servo, servare, servavi, servatum', 'bewaren, behouden | in acht nemen',
  verw=['conservo', 'servatio'])
V('signo, signare, signavi, signatum', 'merken, verzegelen | aanduiden', prio=-1,
  verw=['signum', 'supersigno'])
V('significo, significare, significavi, significatum', 'betekenen, aanduiden | te kennen geven',
  verw=['signum'])
V('spero, sperare, speravi, speratum', 'hopen, verwachten | vertrouwen op', verw=['spes'])
V('suscito, suscitare, suscitavi, suscitatum', 'opwekken, doen opstaan | aansporen',
  verw=['surgo', 'excito'])
V('excito, excitare, excitavi, excitatum', 'opwekken, aansporen | doen opstaan',
  verw=['suscito'])
V('tardo, tardare, tardavi, tardatum', 'vertragen, ophouden | talmen', verw=['tarditas'])
V('tribulo, tribulare, tribulavi, tribulatum', 'verdrukken, kwellen',
  toel='Laat-Latijns, van `tribulum` (dorsslede): eigenlijk "dorsen", dus platdrukken.',
  verw=['tribulatio'])
V('triumpho, triumphare, triumphavi, triumphatum', 'zegevieren, triomferen')
V('vaco, vacare, vacavi, vacatum', 'leeg zijn, vrij zijn | zich wijden aan', verw=['vacuus'])
V('vigilo, vigilare, vigilavi, vigilatum', 'waken, wakker zijn | waakzaam zijn')
V('vindico, vindicare, vindicavi, vindicatum', 'opeisen | wreken, straffen')
V('violo, violare, violavi, violatum', 'schenden, ontheiligen', verw=['violatio'])
V('visito, visitare, visitavi, visitatum', 'bezoeken | bezoeking brengen over', verw=['video'])
V('vivifico, vivificare, vivificavi, vivificatum', 'levend maken, doen herleven',
  verw=['vivo', 'mortifico'])
V('voco, vocare, vocavi, vocatum', 'roepen, aanroepen | noemen | uitnodigen', prio=-1,
  verw=['vox', 'invoco', 'convoco'])
V('invoco, invocare, invocavi, invocatum', 'aanroepen, inroepen', verw=['voco'])
V('convoco, convocare, convocavi, convocatum', 'bijeenroepen, samenroepen', verw=['voco'])
V('zelo, zelare, zelavi, zelatum', 'ijveren, naijverig zijn | benijden',
  toel='Grieks leenwoord; in de Vulgaat gaat het om Gods naijver voor zijn volk.',
  verw=['aemulator'])
V('volo, volare, volavi, volatum', 'vliegen | snellen', prio=-1, naam='volo (vliegen)',
  toel='Niet te verwarren met het onregelmatige `volo, velle` (willen): dat heeft geen '
       'vormen op -a-.', verw=['volo'])
V('exalto, exaltare, exaltavi, exaltatum', 'verhogen, verheffen', verw=['altus'])
V('superexalto, superexaltare, superexaltavi, superexaltatum', 'zeer verhogen',
  verw=['exalto'])
V('nuntio, nuntiare, nuntiavi, nuntiatum', 'berichten, melden', verw=['adnuntio'])
V('ieiuno, ieiunare, ieiunavi, ieiunatum', 'vasten',
  toel='De zeven dagen vasten waarmee Ezra zich telkens op een nieuw visioen voorbereidt.')
V('conculco, conculcare, conculcavi, conculcatum', 'vertrappen, met voeten treden',
  verw=['conculcatio'])
V('calco, calcare, calcavi, calcatum', 'betreden, treden op', verw=['conculco'])
V('exagito, exagitare, exagitavi, exagitatum', 'opjagen, verontrusten')
V('festo, festare, festavi, festatum', 'feestvieren', verw=['festus'])
V('numeror, numerari, numeratus sum', 'geteld worden', k='1d', prio=-2, verw=['numero'])
V('conservor, conservari, conservatus sum', 'bewaard worden', k='1d', prio=-2,
  verw=['conservo'])


# ===========================================================================
# 8. Werkwoorden — 2e vervoeging (-ere met lange e)
# ===========================================================================

V('habeo, habere, habui, habitum',
  'hebben, bezitten | vasthouden | beschouwen als | (met adverbium) zich bevinden', k='2')
V('video, videre, vidi, visum', 'zien, waarnemen | begrijpen, inzien | '
  '(lijdende vorm videor) schijnen, lijken', k='2', verw=['visio', 'visus'])
V('doceo, docere, docui, doctum', 'onderwijzen, leren | aantonen', k='2', verw=['disciplina'])
V('timeo, timere, timui', 'vrezen, bang zijn | ontzag hebben voor', k='2',
  verw=['timor', 'timoratus'])
V('teneo, tenere, tenui, tentum', 'vasthouden, houden | bezitten | in bedwang houden', k='2',
  verw=['retineo', 'sustineo'])
V('retineo, retinere, retinui, retentum', 'vasthouden, tegenhouden | bewaren', k='2',
  verw=['teneo'])
V('sustineo, sustinere, sustinui, sustentum', 'omhooghouden, dragen | verdragen, volhouden | '
  'verwachten', k='2', verw=['teneo'])
V('moveo, movere, movi, motum', 'bewegen, in beweging brengen | ontroeren', k='2',
  verw=['commoveo', 'motus'])
V('commoveo, commovere, commovi, commotum', 'hevig bewegen, doen schudden | ontroeren',
  k='2', verw=['moveo', 'commotio'])
V('iubeo, iubere, iussi, iussum', 'bevelen, gelasten', k='2', verw=['iussio'])
V('maneo, manere, mansi, mansum', 'blijven, verblijven | standhouden | afwachten', k='2',
  verw=['permaneo', 'remaneo'])
V('permaneo, permanere, permansi, permansum', 'volharden, blijven voortbestaan', k='2',
  verw=['maneo'])
V('remaneo, remanere, remansi, remansum', 'achterblijven, overblijven', k='2', verw=['maneo'])
V('respondeo, respondere, respondi, responsum', 'antwoorden | beantwoorden aan', k='2',
  toel='"respondi et dixi" — het vaste ritme waarmee de gesprekken in 4 Ezra vorderen.',
  verw=['interrogo'])
V('sedeo, sedere, sedi, sessum', 'zitten | zetelen | gelegerd zijn', k='2',
  verw=['sedes', 'sessio'])
V('possideo, possidere, possedi, possessum', 'bezitten, in bezit hebben', k='2',
  verw=['possessio'])
V('ardeo, ardere, arsi, arsum', 'branden, in vuur staan | gloeien', k='2', verw=['ardor'])
V('debeo, debere, debui, debitum', 'verschuldigd zijn | moeten, behoren', k='2')
V('deleo, delere, delevi, deletum', 'uitwissen, vernietigen', k='2')
V('doleo, dolere, dolui', 'pijn hebben, treuren | betreuren', k='2', verw=['dolor'])
V('gaudeo, gaudere', 'zich verheugen, blij zijn', k='2', verw=['gaudium', 'iucundo'])
V('horreo, horrere, horrui', 'huiveren, sidderen | terugschrikken voor', k='2',
  verw=['horribilis', 'horridus'])
V('iaceo, iacere, iacui', 'liggen, neerliggen | terneer liggen', k='2')
V('luceo, lucere, luxi', 'lichten, schijnen', k='2', verw=['lux', 'lumen'])
V('lugeo, lugere, luxi, luctum', 'rouwen, treuren | betreuren', k='2',
  verw=['luctus', 'ploro'])
V('noceo, nocere, nocui', 'schaden, kwaad doen', k='2', verw=['innoxius'])
V('pareo, parere, parui', 'zichtbaar zijn, verschijnen | gehoorzamen', k='2', prio=-1,
  toel='Niet te verwarren met `pario, parere` (baren): dat heeft het perfectum peperi.',
  verw=['appareo'])
V('placeo, placere, placui, placitum', 'behagen, bevallen', k='2')
V('praebeo, praebere, praebui, praebitum', 'aanbieden, verschaffen | tonen', k='2')
V('sileo, silere, silui', 'zwijgen, stil zijn', k='2', verw=['silentium', 'taceo'])
V('taceo, tacere, tacui, tacitum', 'zwijgen, stilzwijgen', k='2', verw=['sileo'])
V('terreo, terrere, terrui, territum', 'verschrikken, afschrikken', k='2',
  verw=['terribilis', 'exterreo'])
V('exterreo, exterrere, exterrui, exterritum', 'hevig verschrikken, doen ontstellen', k='2',
  verw=['terreo'])
V('exerceo, exercere, exercui, exercitum', 'oefenen, bezighouden | uitoefenen', k='2',
  verw=['exercitus'])
V('misceo, miscere, miscui, mixtum', 'mengen, vermengen | in verwarring brengen', k='2')
V('torqueo, torquere, torsi, tortum', 'draaien, wringen | folteren', k='2')
V('fleo, flere, flevi, fletum', 'wenen, huilen | bewenen', k='2', verw=['ploro', 'lugeo'])
V('impleo, implere, implevi, impletum', 'vullen, vervullen | voltooien', k='2',
  toel='In de handschriften ook *inpleo*.', verw=['conpleo', 'suppleo'])
V('conpleo, conplere, conplevi, conpletum', 'vullen, voltooien | vervullen', k='2',
  toel='Klassiek *compleo*.', verw=['impleo'])
V('suppleo, supplere, supplevi, suppletum', 'aanvullen, volmaken', k='2', verw=['impleo'])
V('cohaereo, cohaerere, cohaesi, cohaesum', 'samenhangen, vastzitten aan', k='2')
V('pateo, patere, patui', 'openstaan | zich uitstrekken | duidelijk zijn', k='2',
  verw=['apertus'])
V('appareo, apparere, apparui, apparitum', 'verschijnen, zichtbaar worden | blijken', k='2',
  verw=['pareo', 'conpareo'])
V('conpareo, conparere, conparui', 'te voorschijn komen, zichtbaar zijn', k='2',
  toel='Klassiek *compareo*.', verw=['appareo'])
V('caveo, cavere, cavi, cautum', 'oppassen, zich hoeden', k='2')
V('adzelor, adzelari, adzelatus sum', 'naijverig worden, ijveren', k='1d',
  toel='Zeldzame laat-Latijnse vorming bij het Griekse zèlos; buiten 4 Ezra nauwelijks bekend.',
  verw=['zelo'])


# ===========================================================================
# 9. Werkwoorden — 3e vervoeging (-ere met korte e)
# ===========================================================================

V('dico, dicere, dixi, dictum', 'zeggen, spreken | noemen | bepalen', k='3',
  toel='"et dixi" opent in 4 Ezra vrijwel elke beurt van Ezra; de gebiedende wijs enkelvoud '
       'is onregelmatig kort: `dic`.', verw=['loquor', 'verbum'],
  extra={'dic': 'gebiedende wijs ev. (onregelmatig verkort)'})
V('praedico, praedicere, praedixi, praedictum', 'vooraf zeggen, voorspellen', k='3',
  toel='Niet te verwarren met `praedico, praedicare` (1e vervoeging): verkondigen, prediken.',
  verw=['dico'])
V('praedico, praedicare, praedicavi, praedicatum', 'verkondigen, prediken | roemen',
  naam='praedico (verkondigen)', prio=-1, verw=['praedico'])
V('facio, facere, feci, factum', 'maken, vervaardigen | doen, verrichten | veroorzaken',
  k='3io', toel='"factum est" — "het geschiedde"; de vaste vertelformule van de Vulgaat. De '
                'gebiedende wijs enkelvoud is onregelmatig kort: `fac`. De lijdende vorm wordt '
                'door `fio` geleverd.',
  extra={'fac': 'gebiedende wijs ev. (onregelmatig verkort)'}, verw=['fio', 'factum'])
V('ago, agere, egi, actum', 'in beweging brengen, drijven | doen, handelen | behandelen',
  k='3', toel='"gratias agere" — dank brengen; "agere de" — spreken over.', verw=['actus'])
V('duco, ducere, duxi, ductum', 'leiden, voeren | menen, achten', k='3',
  extra={'duc': 'gebiedende wijs ev. (onregelmatig verkort)'}, verw=['dux', 'educo'])
V('educo, educere, eduxi, eductum', 'uitleiden, naar buiten voeren', k='3',
  naam='educo (uitleiden)', prio=-1,
  toel='Te onderscheiden van `educo, educare` (opvoeden): het perfectum is hier `eduxi`.',
  verw=['duco'])
V('induco, inducere, induxi, inductum', 'binnenleiden, aanvoeren | doen ontstaan', k='3',
  verw=['duco'])
V('mitto, mittere, misi, missum', 'zenden, sturen | loslaten, werpen', k='3',
  verw=['emitto', 'inmitto', 'dimitto'])
V('emitto, emittere, emisi, emissum', 'uitzenden, laten uitgaan', k='3', verw=['mitto'])
V('inmitto, inmittere, inmisi, inmissum', 'inzenden, laten binnengaan | loslaten op', k='3',
  toel='Klassiek *immitto*.', verw=['mitto'])
V('dimitto, dimittere, dimisi, dimissum', 'wegzenden, loslaten | vergeven', k='3',
  verw=['mitto'])
V('accipio, accipere, accepi, acceptum', 'aannemen, ontvangen | vernemen | opvatten',
  k='3io', verw=['capio', 'recipio'])
V('capio, capere, cepi, captum', 'nemen, grijpen | bevatten | innemen', k='3io',
  verw=['capax', 'accipio'])
V('recipio, recipere, recepi, receptum', 'terugnemen, ontvangen | opnemen', k='3io',
  verw=['accipio', 'receptio'])
V('suscipio, suscipere, suscepi, susceptum', 'opnemen, op zich nemen | ontvangen', k='3io',
  verw=['accipio'])
V('excipio, excipere, excepi, exceptum', 'opvangen, ontvangen | uitzonderen', k='3io',
  verw=['accipio'])
V('percipio, percipere, percepi, perceptum', 'in ontvangst nemen, verkrijgen | begrijpen',
  k='3io', verw=['accipio'])
V('incipio, incipere', 'beginnen, aanvangen', k='3io',
  toel='Het perfectum wordt geleverd door het gebrekkige `coepi`.', verw=['coepi', 'inchoo'])
V('interficio, interficere, interfeci, interfectum', 'doden, ombrengen', k='3io',
  verw=['occido', 'facio'])
V('perficio, perficere, perfeci, perfectum', 'voltooien, volbrengen', k='3io', verw=['facio'])
V('efficio, efficere, effeci, effectum', 'bewerken, tot stand brengen', k='3io', verw=['facio'])
V('deficio, deficere, defeci, defectum', 'ontbreken, tekortschieten | bezwijken, afvallen',
  k='3io', verw=['facio', 'indeficiens'])
V('sufficio, sufficere, suffeci, suffectum', 'toereikend zijn, volstaan | verschaffen',
  k='3io', verw=['facio'])
V('proicio, proicere, proieci, proiectum', 'wegwerpen, neerwerpen | verstoten', k='3io',
  verw=['iacio', 'reicio'])
V('reicio, reicere, reieci, reiectum', 'terugwerpen | verwerpen, afwijzen', k='3io',
  verw=['proicio'])
V('eicio, eicere, eieci, eiectum', 'uitwerpen, verdrijven', k='3io', verw=['proicio'])
V('adicio, adicere, adieci, adiectum', 'toevoegen, erbij doen | bovendien doen', k='3io',
  toel='Klassiek ook *adjicio*.', verw=['proicio'])
V('respicio, respicere, respexi, respectum', 'omzien naar, achteromkijken | letten op',
  k='3io', verw=['aspicio', 'conspicio'])
V('aspicio, aspicere, aspexi, aspectum', 'aanzien, aanschouwen | letten op', k='3io',
  verw=['aspectus', 'respicio'])
V('conspicio, conspicere, conspexi, conspectum', 'in het oog krijgen, aanschouwen', k='3io',
  verw=['conspectus', 'aspicio'])
V('rapio, rapere, rapui, raptum', 'wegrukken, roven | meesleuren', k='3io',
  verw=['rapina', 'diripio'])
V('diripio, diripere, diripui, direptum', 'uiteenrukken, plunderen', k='3io',
  verw=['rapio', 'direptio'])
V('sapio, sapere, sapivi', 'smaken | verstandig zijn, begrijpen', k='3io',
  verw=['sapiens', 'sapientia'])
V('pario, parere, peperi, partum', 'baren, voortbrengen | verwerven', k='3io',
  naam='pario (baren)',
  toel='De onbepaalde wijs `parere` valt samen met die van `pareo` (gehoorzamen); het '
       'perfectum `peperi` onderscheidt de twee.', verw=['partus', 'pareo'])
V('cado, cadere, cecidi, casum', 'vallen, neervallen | omkomen | uitvallen, aflopen', k='3',
  verw=['casus', 'concido'])
V('concido, concidere, concidi', 'ineenstorten, neervallen', k='3', verw=['cado'])
V('cognosco, cognoscere, cognovi, cognitum', 'leren kennen, vernemen | erkennen', k='3',
  verw=['nosco', 'intellego'])
V('nosco, noscere, novi, notum', 'leren kennen, kennen', k='3', verw=['cognosco', 'notus'])
V('colo, colere, colui, cultum', 'bebouwen, verzorgen | bewonen | vereren', k='3',
  verw=['cultor', 'cultura'])
V('credo, credere, credidi, creditum', 'geloven, vertrouwen | toevertrouwen', k='3',
  verw=['fides', 'incredulus'])
V('discredo, discredere, discredidi', 'niet geloven, wantrouwen', k='3',
  toel='Laat-Latijnse vorming; klassiek zou men `non credere` zeggen.', verw=['credo'])
V('cresco, crescere, crevi, cretum', 'groeien, toenemen | ontstaan', k='3',
  verw=['incresco', 'germino'])
V('incresco, increscere, increvi', 'aangroeien, toenemen', k='3', verw=['cresco'])
V('curro, currere, cucurri, cursum', 'lopen, snellen | stromen', k='3', verw=['decurro'])
V('decurro, decurrere, decucurri, decursum', 'naar beneden lopen, afstromen', k='3',
  verw=['curro'])
V('defendo, defendere, defendi, defensum', 'afweren | verdedigen, beschermen', k='3')
V('derelinquo, derelinquere, dereliqui, derelictum', 'in de steek laten, verlaten | '
  'achterlaten', k='3',
  toel='"quare dereliquisti me?" — de klacht die in 4 Ezra telkens terugkeert.',
  verw=['relinquo', 'desero'])
V('relinquo, relinquere, reliqui, relictum', 'achterlaten, overlaten | verlaten', k='3',
  verw=['derelinquo'])
V('desero, deserere, deserui, desertum', 'in de steek laten, verlaten', k='3',
  verw=['desertum', 'desertio'])
V('dirigo, dirigere, direxi, directum', 'richten, sturen | rechtmaken', k='3',
  verw=['rego', 'directio'])
V('divido, dividere, divisi, divisum', 'verdelen, scheiden', k='3', verw=['divisio'])
V('effundo, effundere, effudi, effusum', 'uitgieten, uitstorten | verspillen', k='3',
  verw=['fundo'])
V('fundo, fundere, fudi, fusum', 'gieten, storten | verspreiden', k='3', verw=['effundo'])
V('eligo, eligere, elegi, electum', 'uitkiezen, verkiezen', k='3',
  toel='De "electi" zijn in 4 Ezra de uitverkorenen voor wie de wereld gemaakt is.',
  verw=['lego', 'electus'])
V('lego, legere, legi, lectum', 'verzamelen, lezen | voorlezen', k='3',
  verw=['colligo', 'eligo'])
V('colligo, colligere, collegi, collectum', 'bijeenbrengen, verzamelen | opnemen', k='3',
  verw=['lego', 'congrego'])
V('diligo, diligere, dilexi, dilectum', 'hoogachten, liefhebben', k='3', verw=['amo'])
V('neglego, neglegere, neglexi, neglectum', 'verwaarlozen, veronachtzamen', k='3',
  verw=['lego'])
V('intellego, intellegere, intellexi, intellectum', 'begrijpen, inzien | merken', k='3',
  toel='In de handschriften ook *intelligo*. In 4 Ezra het woord voor het inzicht dat Ezra '
       'juist niet heeft.', verw=['intellectus', 'cognosco'])
V('excludo, excludere, exclusi, exclusum', 'buitensluiten, uitsluiten', k='3',
  verw=['claudo'])
V('claudo, claudere, clausi, clausum', 'sluiten, afsluiten | insluiten', k='3',
  verw=['concludo', 'recludo'])
V('concludo, concludere, conclusi, conclusum', 'insluiten, opsluiten | besluiten', k='3',
  verw=['claudo'])
V('recludo, recludere, reclusi, reclusum', 'ontsluiten, openen', k='3', verw=['claudo'])
V('includo, includere, inclusi, inclusum', 'insluiten, opsluiten', k='3', verw=['claudo'])
V('exquiro, exquirere, exquisivi, exquisitum', 'uitvorsen, navorsen | opzoeken', k='3',
  verw=['quaero', 'inquiro'])
V('inquiro, inquirere, inquisivi, inquisitum', 'onderzoeken, navragen', k='3', verw=['quaero'])
V('requiro, requirere, requisivi, requisitum', 'zoeken, opeisen | missen', k='3',
  verw=['quaero'])
V('quaero, quaerere, quaesivi, quaesitum', 'zoeken | vragen, navorsen | trachten', k='3',
  verw=['exquiro', 'inquiro'])
V('extinguo, extinguere, extinxi, extinctum', 'uitdoven, blussen | vernietigen', k='3',
  toel='In de handschriften ook *exstinguo*.', verw=['ignis'])
V('gero, gerere, gessi, gestum', 'dragen | voeren, uitvoeren | zich gedragen', k='3')
V('occido, occidere, occidi, occisum', 'neerslaan, doden', k='3', verw=['occisio'])
V('ostendo, ostendere, ostendi, ostensum', 'tonen, laten zien | verklaren', k='3',
  toel='Het werkwoord waarmee de engel Ezra zijn visioenen "toont".',
  verw=['demonstro', 'tendo'])
V('tendo, tendere, tetendi, tentum', 'spannen, uitstrekken | streven', k='3',
  verw=['extendo', 'ostendo'])
V('extendo, extendere, extendi, extensum', 'uitstrekken, uitspreiden', k='3', verw=['tendo'])
V('perdo, perdere, perdidi, perditum', 'te gronde richten, verderven | verliezen', k='3',
  verw=['perditio', 'pereo'])
V('reddo, reddere, reddidi, redditum', 'teruggeven | vergelden | maken tot', k='3',
  verw=['do', 'redditio'])
V('trado, tradere, tradidi, traditum', 'overgeven, overleveren | overdragen, meedelen',
  k='3', verw=['do'])
V('addo, addere, addidi, additum', 'toevoegen, erbij doen', k='3', verw=['do'])
V('pono, ponere, posui, positum', 'plaatsen, leggen | stellen, vaststellen', k='3',
  verw=['depono', 'dispono', 'inpono'])
V('depono, deponere, deposui, depositum', 'neerleggen, afleggen | in bewaring geven', k='3',
  verw=['pono'])
V('dispono, disponere, disposui, dispositum', 'ordenen, inrichten | beschikken', k='3',
  toel='In 4 Ezra Gods beschikken over de tijden: "disposuit tempora".',
  verw=['pono', 'dispositio'])
V('inpono, inponere, inposui, inpositum', 'opleggen, erop zetten', k='3',
  toel='Klassiek *impono*.', verw=['pono'])
V('praepono, praeponere, praeposui, praepositum', 'vooropstellen, aan het hoofd stellen',
  k='3', verw=['pono'])
V('propono, proponere, proposui, propositum', 'voorstellen, voorleggen | voornemen', k='3',
  verw=['pono'])
V('repono, reponere, reposui, repositum', 'terugleggen, wegleggen | bewaren', k='3',
  verw=['pono'])
V('superpono, superponere, superposui, superpositum', 'erbovenop plaatsen', k='3',
  verw=['pono'])
V('rego, regere, rexi, rectum', 'besturen, leiden | recht houden', k='3', prio=-1,
  verw=['rex', 'dirigo'])
V('scribo, scribere, scripsi, scriptum', 'schrijven, opschrijven | voorschrijven', k='3',
  toel='4 Ezra 14 vertelt hoe de verbrande boeken opnieuw geschreven worden.',
  verw=['liber', 'scriptura'])
V('sculpo, sculpere, sculpsi, sculptum', 'uithouwen, beitelen', k='3')
V('sero, serere, sevi, satum', 'zaaien, planten', k='3', naam='sero (zaaien)',
  verw=['semen', 'semino'])
V('sperno, spernere, sprevi, spretum', 'versmaden, verwerpen | minachten', k='3',
  toel='"spreverunt legem meam" — zij versmaadden mijn wet; een refrein in 4 Ezra 1.',
  verw=['spretio'])
V('sumo, sumere, sumpsi, sumptum', 'nemen, opnemen | zich toe-eigenen', k='3',
  verw=['resumo', 'consumo'])
V('resumo, resumere, resumpsi, resumptum', 'weer opnemen, hervatten', k='3', verw=['sumo'])
V('consumo, consumere, consumpsi, consumptum', 'verbruiken, verteren | vernietigen', k='3',
  verw=['sumo'])
V('consummo, consummare, consummavi, consummatum', 'voltooien, voleindigen',
  verw=['consummatio'])
V('surgo, surgere, surrexi, surrectum', 'opstaan, oprijzen', k='3',
  verw=['exsurgo', 'resurgo'])
V('exsurgo, exsurgere, exsurrexi, exsurrectum', 'opstaan, zich verheffen', k='3',
  verw=['surgo', 'exsurrectio'])
V('resurgo, resurgere, resurrexi, resurrectum', 'weer opstaan, verrijzen', k='3',
  verw=['surgo', 'resurrectio'])
V('tego, tegere, texi, tectum', 'bedekken, beschermen | verbergen', k='3',
  verw=['obtego', 'protego'])
V('protego, protegere, protexi, protectum', 'beschermen, beschutten', k='3', verw=['tego'])
V('obtego, obtegere, obtexi, obtectum', 'bedekken, verbergen', k='3', verw=['tego'])
V('vinco, vincere, vici, victum', 'overwinnen, verslaan', k='3', verw=['victoria'])
V('vivo, vivere, vixi, victum', 'leven, in leven zijn', k='3', verw=['vita', 'vivus'])
V('descendo, descendere, descendi, descensum', 'afdalen, neerkomen', k='3',
  verw=['ascendo'])
V('ascendo, ascendere, ascendi, ascensum', 'opstijgen, beklimmen', k='3', verw=['descendo'])
V('accedo, accedere, accessi, accessum', 'naderen, toetreden | erbij komen', k='3',
  verw=['cedo', 'discedo'])
V('excedo, excedere, excessi, excessum', 'heengaan, wijken | overtreffen', k='3',
  verw=['excessus'])
V('procedo, procedere, processi, processum', 'voortgaan, voortkomen | vorderen', k='3',
  verw=['cedo'])
V('recedo, recedere, recessi, recessum', 'terugwijken, weggaan', k='3', verw=['cedo'])
V('discedo, discedere, discessi, discessum', 'uiteengaan, heengaan', k='3', verw=['cedo'])
V('fluo, fluere, fluxi, fluxum', 'vloeien, stromen', k='3', verw=['flumen', 'fluctus'])
V('destruo, destruere, destruxi, destructum', 'afbreken, verwoesten', k='3',
  verw=['instruo', 'destructio'])
V('instruo, instruere, instruxi, instructum', 'opbouwen, inrichten | onderrichten', k='3',
  verw=['destruo'])
V('constituo, constituere, constitui, constitutum', 'opstellen, vaststellen | aanstellen',
  k='3', verw=['statuo'])
V('statuo, statuere, statui, statutum', 'plaatsen, opstellen | vaststellen, besluiten',
  k='3', verw=['sto', 'constituo'])
V('instituo, instituere, institui, institutum', 'instellen, inrichten | onderwijzen', k='3',
  verw=['statuo'])
V('quiesco, quiescere, quievi, quietum', 'rusten, tot rust komen | ophouden', k='3',
  toel='In 4 Ezra de rust van de zielen die in de voorraadkamers wachten.',
  verw=['requies', 'requiesco'])
V('adquiro, adquirere, adquisivi, adquisitum', 'verwerven, verkrijgen', k='3',
  toel='Klassiek *acquiro*.', verw=['quaero'])
V('fingo, fingere, finxi, fictum', 'boetseren, vormen | verzinnen', k='3',
  verw=['figmentum', 'plasmo'])
V('praecingo, praecingere, praecinxi, praecinctum', 'omgorden, omringen', k='3')
V('dispergo, dispergere, dispersi, dispersum', 'verstrooien, uiteendrijven', k='3',
  toel='Het woord voor de verstrooiing van Israël onder de volken.')
V('contero, conterere, contrivi, contritum', 'vermalen, verbrijzelen | uitputten', k='3',
  verw=['contritio', 'extero'])
V('extero, exterere, extrivi, extritum', 'uitwrijven, uitdorsen | vermorzelen', k='3',
  verw=['contero', 'exteritio'])
V('emo, emere, emi, emptum', 'kopen, verwerven', k='3')
V('bibo, bibere, bibi', 'drinken', k='3', verw=['potus'])
V('comedo, comedere, comedi, comestum', 'opeten, verteren', k='3', verw=['manduco'])
V('vendo, vendere, vendidi, venditum', 'verkopen', k='3', verw=['emo'])
V('tollo, tollere, sustuli, sublatum', 'opheffen, opnemen | wegnemen', k='3', verw=['fero'])
V('conprehendo, conprehendere, conprehendi, conprehensum', 'samenvatten, grijpen | begrijpen',
  k='3', toel='Klassiek *comprehendo*.', verw=['adprehendo'])
V('adprehendo, adprehendere, adprehendi, adprehensum', 'aangrijpen, vastpakken', k='3',
  toel='Klassiek *apprehendo*.', verw=['conprehendo'])
V('contingo, contingere, contigi, contactum', 'aanraken | te beurt vallen, gebeuren', k='3',
  verw=['tango'])
V('convert, convertere, converti, conversum', 'omkeren, veranderen | zich bekeren', k='3',
  naam='converto', verw=['verto'])
V('everto, evertere, everti, eversum', 'omverwerpen, verwoesten', k='3', verw=['verto'])
V('subverto, subvertere, subverti, subversum', 'omverwerpen, ondersteboven keren', k='3',
  verw=['verto'])
V('averto, avertere, averti, aversum', 'afwenden, wegkeren', k='3', verw=['verto'])
V('verto, vertere, verti, versum', 'keren, wenden | veranderen', k='3', verw=['converto'])
V('dissolvo, dissolvere, dissolvi, dissolutum', 'losmaken, ontbinden | vernietigen', k='3',
  verw=['solvo', 'absolvo'])
V('absolvo, absolvere, absolvi, absolutum', 'losmaken, vrijspreken | voltooien', k='3',
  verw=['solvo', 'absolutio'])
V('solvo, solvere, solvi, solutum', 'losmaken, ontbinden | betalen', k='3',
  verw=['dissolvo'])
V('constringo, constringere, constrinxi, constrictum', 'samenbinden, in bedwang houden',
  k='3')
V('satago, satagere', 'zich inspannen, druk in de weer zijn', k='3', verw=['ago'])
V('subduco, subducere, subduxi, subductum', 'wegtrekken, onttrekken', k='3', verw=['duco'])
V('succendo, succendere, succendi, succensum', 'aansteken, in brand zetten', k='3',
  verw=['accendo'])
V('accendo, accendere, accendi, accensum', 'aansteken, ontsteken', k='3', verw=['succendo'])
V('incendo, incendere, incendi, incensum', 'in brand steken, ontsteken', k='3',
  verw=['accendo', 'incendium'])
V('abscondo, abscondere, abscondi, absconditum', 'verbergen, wegstoppen', k='3',
  toel='In 4 Ezra ook van de verborgen boeken en de verborgen wereld die komt.',
  verw=['occulto'])
V('confundo, confundere, confudi, confusum', 'dooreenmengen | verwarren, beschamen', k='3',
  verw=['fundo', 'confusio'])
V('agnosco, agnoscere, agnovi, agnitum', 'herkennen, erkennen', k='3', verw=['cognosco'])
V('serpo, serpere, serpsi', 'kruipen, voortkruipen', k='3', verw=['reptilis'])


# ===========================================================================
# 10. Werkwoorden — 4e vervoeging (-ire)
# ===========================================================================

V('audio, audire, audivi, auditum', 'horen, luisteren | vernemen | gehoorzamen', k='4',
  verw=['auditus', 'exaudio'])
V('exaudio, exaudire, exaudivi, exauditum', 'aanhoren, verhoren', k='4', verw=['audio'])
V('obaudio, obaudire, obaudivi, obauditum', 'gehoorzamen, luisteren naar', k='4',
  toel='Laat-Latijnse nevenvorm van *oboedio*; de Vulgaat gebruikt beide.', verw=['audio'])
V('venio, venire, veni, ventum', 'komen, aankomen | ontstaan', k='4',
  verw=['advenio', 'invenio', 'convenio'])
V('advenio, advenire, adveni, adventum', 'aankomen, naderbij komen', k='4', verw=['venio'])
V('invenio, invenire, inveni, inventum', 'vinden, aantreffen | ontdekken', k='4',
  verw=['venio'])
V('convenio, convenire, conveni, conventum', 'samenkomen, bijeenkomen | overeenkomen',
  k='4', verw=['venio', 'conventio'])
V('pervenio, pervenire, perveni, perventum', 'aankomen, bereiken', k='4', verw=['venio'])
V('scio, scire, scivi, scitum', 'weten, kennen | verstaan', k='4', verw=['nescio', 'scientia'])
V('nescio, nescire, nescivi, nescitum', 'niet weten, onbekend zijn met', k='4', verw=['scio'])
V('sentio, sentire, sensi, sensum', 'waarnemen, voelen | menen, oordelen', k='4',
  verw=['sensus', 'consentio'])
V('consentio, consentire, consensi, consensum', 'instemmen, het eens zijn', k='4',
  verw=['sentio'])
V('aperio, aperire, aperui, apertum', 'openen, ontsluiten | onthullen', k='4',
  verw=['adaperio', 'apertus'])
V('adaperio, adaperire, adaperui, adapertum', 'wijd openen, ontsluiten', k='4',
  verw=['aperio'])
V('custodio, custodire, custodivi, custoditum', 'bewaken, behoeden | onderhouden (van geboden)',
  k='4', verw=['custos', 'servo'])
V('dormio, dormire, dormivi, dormitum', 'slapen | ontslapen, sterven', k='4',
  toel='"qui dormierunt" — zij die ontslapen zijn; in 4 Ezra de gestorvenen die op de '
       'opstanding wachten.')
V('erudio, erudire, erudivi, eruditum', 'onderrichten, opvoeden', k='4', verw=['doceo'])
V('finio, finire, finivi, finitum', 'begrenzen, beëindigen | ophouden', k='4', verw=['finis'])
V('inpedio, inpedire, inpedivi, inpeditum', 'belemmeren, verhinderen', k='4',
  toel='Klassiek *impedio*.')
V('munio, munire, munivi, munitum', 'versterken, ommuren | beveiligen', k='4')
V('nutrio, nutrire, nutrivi, nutritum', 'voeden, grootbrengen', k='4',
  verw=['enutrio', 'nutrix'])
V('enutrio, enutrire, enutrivi, enutritum', 'opvoeden, grootbrengen', k='4', verw=['nutrio'])
V('punio, punire, punivi, punitum', 'straffen, bestraffen', k='4')
V('servio, servire, servivi, servitum', 'dienen, dienstbaar zijn', k='4',
  verw=['servus', 'servitus', 'deservio'])
V('deservio, deservire, deservivi, deservitum', 'ijverig dienen, toegewijd zijn', k='4',
  verw=['servio'])
V('vestio, vestire, vestivi, vestitum', 'kleden, bekleden', k='4', verw=['vestis'])
V('sitio, sitire, sitivi', 'dorst hebben, dorsten naar', k='4', verw=['sitis'])
V('esurio, esurire, esurivi', 'honger hebben, hongeren', k='4', verw=['fames'])


# ===========================================================================
# 11. Deponentia en gebrekkige werkwoorden
# ===========================================================================

V('loquor, loqui, locutus sum', 'spreken, zeggen | uitspreken', k='3d',
  toel='Deponens: het heeft passieve vormen maar een actieve betekenis.',
  verw=['dico', 'sermo'])
V('sequor, sequi, secutus sum', 'volgen, achternagaan | gehoorzamen', k='3d',
  verw=['consequor', 'persequor'])
V('consequor, consequi, consecutus sum', 'achterhalen, bereiken | verkrijgen', k='3d',
  verw=['sequor'])
V('persequor, persequi, persecutus sum', 'nazetten, vervolgen | volhouden', k='3d',
  verw=['sequor'])
V('nascor, nasci, natus sum', 'geboren worden, ontstaan | opkomen', k='3d',
  verw=['nativitas', 'natura'])
V('morior, mori, mortuus sum', 'sterven, omkomen', k='3iod', verw=['mors', 'mortuus'])
V('patior, pati, passus sum', 'lijden, verduren | toelaten', k='3iod')
V('ingredior, ingredi, ingressus sum', 'binnengaan, betreden | beginnen', k='3iod',
  verw=['transgredior'])
V('transgredior, transgredi, transgressus sum', 'overschrijden, oversteken | overtreden',
  k='3iod', verw=['ingredior'])
V('proficiscor, proficisci, profectus sum', 'vertrekken, op weg gaan | voortkomen uit',
  k='3d')
V('utor, uti, usus sum', 'gebruiken, zich bedienen van', k='3d')
V('obliviscor, oblivisci, oblitus sum', 'vergeten', k='3d', verw=['oblivio'])
V('amplector, amplecti, amplexus sum', 'omarmen, omvatten | koesteren', k='3d')
V('orior, oriri, ortus sum', 'opkomen, ontstaan | geboren worden', k='4d', verw=['oriens'])
V('metior, metiri, metitus sum', 'meten, afmeten | beoordelen', k='4d',
  toel='Het klassieke voltooid deelwoord is `mensus`; 4 Ezra heeft de late vorm `metitus`.',
  verw=['mensura', 'mensuro'])
V('misereor, misereri, misertus sum', 'medelijden hebben, zich erbarmen', k='2d',
  verw=['misericordia', 'misericors'])
V('tueor, tueri, tuitus sum', 'aanschouwen | beschermen, bewaken', k='2d', verw=['tutor'])
V('tutor, tutari, tutatus sum', 'beschermen, beveiligen', k='1d', verw=['tueor', 'tutela'])
V('consolor, consolari, consolatus sum', 'troosten, bemoedigen', k='1d',
  toel='Het vierde visioen begint met Ezra die een rouwende vrouw wil troosten.',
  verw=['consolatio'])
V('deprecor, deprecari, deprecatus sum', 'smeken, afsmeken | afbidden', k='1d',
  verw=['deprecatio', 'oro'])
V('interpretor, interpretari, interpretatus sum', 'uitleggen, verklaren | vertalen', k='1d',
  verw=['interpretatio'])
V('testor, testari, testatus sum', 'getuigen, betuigen | tot getuige nemen', k='1d',
  verw=['testis', 'testificor'])
V('testificor, testificari, testificatus sum', 'getuigenis afleggen, betuigen', k='1d',
  verw=['testor'])
V('peregrinor, peregrinari, peregrinatus sum', 'in den vreemde verblijven, rondtrekken',
  k='1d', verw=['peregrinatio'])
V('dominor, dominari, dominatus sum', 'heersen, de baas zijn', k='1d',
  verw=['dominus', 'dominator'])
V('fornicor, fornicari, fornicatus sum', 'hoererij bedrijven, ontucht plegen', k='1d',
  toel='In de profetische taal het beeld voor afgoderij: ontrouw aan het verbond.',
  verw=['fornicatio'])
V('conversor, conversari, conversatus sum', 'verkeren, omgaan met | leven', k='1d',
  verw=['converto'])
V('tristor, tristari, tristatus sum', 'bedroefd zijn, treuren', k='1d',
  verw=['tristis', 'contristo'])
V('miror, mirari, miratus sum', 'zich verwonderen, bewonderen', k='1d', verw=['mirabilis'])
V('negotior, negotiari, negotiatus sum', 'handel drijven, zaken doen', k='1d')
V('mercor, mercari, mercatus sum', 'kopen, handel drijven', k='1d', verw=['merces'])
V('imitor, imitari, imitatus sum', 'nabootsen, navolgen', k='1d', verw=['inimitabilis'])
V('abutor, abuti, abusus sum', 'misbruiken, verkwisten', k='3d', verw=['utor'])
V('confiteor, confiteri, confessus sum', 'bekennen, belijden | prijzen', k='2d')
V('confido, confidere, confisus sum', 'vertrouwen, zich verlaten op', k='3',
  extra={'confide': 'gebiedende wijs ev. — heb vertrouwen',
         'confiderunt': '3e pers. mv., perfectum — zij vertrouwden',
         'confisus': 'voltooid deelwoord — vertrouwd hebbend'}, verw=['fides', 'credo'])
V('audeo, audere', 'durven, wagen', k='2',
  toel='Half-deponens: het perfectum luidt `ausus sum`.')

X('coepi', 'werkwoord (gebrekkig)', 'coepi, coepisse, coeptum',
  'ik ben begonnen, ik begon | aanvangen',
  {'coepi': '1e pers. ev., perfectum — ik begon', 'coepisti': '2e pers. ev., perfectum',
   'coepit': '3e pers. ev., perfectum — hij begon',
   'coepimus': '1e pers. mv., perfectum', 'coepistis': '2e pers. mv., perfectum',
   'coeperunt': '3e pers. mv., perfectum — zij begonnen',
   'coeperam': '1e pers. ev., plusquamperfectum', 'coeperat': '3e pers. ev., plusquamperfectum',
   'coeperint': '3e pers. mv., voltooid toekomende tijd of perfectum aanvoegende wijs',
   'coepissem': '1e pers. ev., plusquamperfectum aanvoegende wijs',
   'coepisset': '3e pers. ev., plusquamperfectum aanvoegende wijs',
   'coepissent': '3e pers. mv., plusquamperfectum aanvoegende wijs',
   'coepisse': 'voltooide onbepaalde wijs — begonnen te zijn',
   'coeptum': 'voltooid deelwoord onzijdig — begonnen'},
  toel='Alleen in het perfectumsysteem in gebruik; de tegenwoordige tijd wordt door '
       '`incipio` geleverd.', verw=['incipio'])
X('odi', 'werkwoord (gebrekkig)', 'odi, odisse',
  'ik haat, ik verafschuw | vijandig gezind zijn',
  {'odi': '1e pers. ev. — ik haat (perfectum met tegenwoordige betekenis)',
   'odisti': '2e pers. ev. — gij haat', 'odit': '3e pers. ev. — hij haat',
   'oderunt': '3e pers. mv. — zij haten', 'oderant': '3e pers. mv., verleden tijd — zij haatten',
   'odisse': 'onbepaalde wijs — te haten',
   'odiens': 'tegenwoordig deelwoord (late vorming) — hatend'},
  toel='Een perfectum met de betekenis van een tegenwoordige tijd: "odi" betekent "ik haat", '
       'niet "ik haatte".', verw=['odibilis'])
X('oportet', 'onpersoonlijk werkwoord', 'oportet, oportere, oportuit',
  'het behoort, het moet | het is nodig',
  {'oportet': '3e pers. ev., tegenwoordige tijd — het behoort',
   'oportebat': '3e pers. ev., verleden tijd — het behoorde',
   'oportuit': '3e pers. ev., perfectum — het heeft behoord',
   'oporteat': '3e pers. ev., aanvoegende wijs', 'oportere': 'onbepaalde wijs'},
  toel='Alleen in de derde persoon enkelvoud; het onderwerp is een hele zin.',
  verw=['debeo', 'decet'])
X('decet', 'onpersoonlijk werkwoord', 'decet, decere, decuit',
  'het past, het betaamt',
  {'decet': '3e pers. ev., tegenwoordige tijd — het betaamt',
   'decebat': '3e pers. ev., verleden tijd', 'decuit': '3e pers. ev., perfectum'},
  verw=['oportet'])
X('restat', 'onpersoonlijk werkwoord', 'restat, restare, restitit',
  'het blijft over, het rest | er blijft nog te doen',
  {'restat': '3e pers. ev., tegenwoordige tijd — het rest',
   'restabat': '3e pers. ev., verleden tijd', 'restant': '3e pers. mv. — zij blijven over'},
  verw=['remaneo'])


# ===========================================================================
# 12. Aanvullingen — wat de tekst van 4 Ezra verder nog vraagt
# ===========================================================================

N('caelum, caeli, o.', 'hemel, hemelgewelf | lucht | het hemelse',
  toel='In de Vulgaat is het meervoud mannelijk (caeli, caelorum, caelos) naar het Hebreeuwse '
       '*sjamajim*, dat altijd meervoud is.',
  extra={'caeli': 'genitief ev., of nominatief mv. (mannelijk meervoud caeli)',
         'caelos': 'accusatief mv. — de hemelen'}, verw=['terra', 'firmamentum'])
N('locus, loci, m.', 'plaats, plek | gelegenheid | positie, rang',
  toel='Het meervoud is meestal onzijdig: loca, locorum.',
  extra={'loca': 'nominatief/accusatief mv. (onzijdige nevenvorm loca)',
         'lociis': 'datief/ablatief mv. (schrijfvariant van locis)'})
N('mare, maris, o.', 'zee | het zeewater', i=True, verw=['aqua', 'fluctus'])
N('animal, animalis, o.', 'levend wezen, dier', i=True, verw=['bestia', 'anima'])
N('altare, altaris, o.', 'altaar, offertafel', i=True)
N('caro, carnis, v.', 'vlees | lichaam | de mens in zijn vergankelijkheid', i=True,
  toel='"caro et sanguis" — vlees en bloed; het beeld voor de sterfelijke mens.',
  verw=['corpus', 'carnalis'])
N('aurum, auri, o.', 'goud | gouden voorwerp')
N('auris, auris, v.', 'oor | gehoor', i=True, verw=['audio'])
N('lingua, linguae, v.', 'tong | taal, spraak')
N('sol, solis, m.', 'zon | zonlicht', verw=['luna', 'stella'])
N('pes, pedis, m.', 'voet | tred')
N('ovis, ovis, v.', 'schaap', i=True, verw=['grex', 'pastor'])
N('equus, equi, m.', 'paard, ros')
N('castra, castrorum, o.', 'legerkamp, legerplaats',
  toel='Alleen in het meervoud; het enkelvoud castrum betekent "vesting".')
N('esca, escae, v.', 'voedsel, spijs | aas')
N('femur, femoris, o.', 'dij, heup')
N('fumus, fumi, m.', 'rook, damp')
N('nutrix, nutricis, v.', 'voedster, min', verw=['nutrio'])
N('potus, potus, m.', 'drank, het drinken', verw=['bibo'])
N('ren, renis, m.', 'nier | (meervoud renes) nieren, lendenen, het binnenste', i=True,
  toel='In de Bijbelse taal de zetel van de diepste gedachten, naast het hart.')
N('securis, securis, v.', 'bijl, strijdbijl', i=True)
N('sors, sortis, v.', 'lot, aandeel | orakel', i=True)
N('terminus, termini, m.', 'grens, grenspaal | einde', verw=['finis'])
N('testis, testis, m.', 'getuige', i=True, verw=['testor', 'testimonium'])
N('testimonium, testimonii, o.', 'getuigenis, bewijs', verw=['testis'])
N('thalamus, thalami, m.', 'slaapvertrek, bruidsvertrek')
N('tormentum, tormenti, o.', 'folterwerktuig | marteling, kwelling', verw=['torqueo'])
N('uxor, uxoris, v.', 'echtgenote, vrouw', verw=['mulier', 'maritus'])
N('maritus, mariti, m.', 'echtgenoot, man', verw=['uxor'])
N('columna, columnae, v.', 'zuil, pilaar')
N('camelus, cameli, m.', 'kameel')
N('cera, cerae, v.', 'was | wastafeltje om op te schrijven')
N('brachium, brachii, o.', 'arm, onderarm | tak')
N('cacumen, cacuminis, o.', 'top, spits | uiterste punt')
N('calcaneum, calcanei, o.', 'hiel',
  toel='Ezra vraagt of Jakobs hand aan Esaus hiel het einde van het tijdperk aanwijst (4 Ezra 6:8-10).')
N('canticum, cantici, o.', 'lied, gezang', verw=['hymnus', 'cano'])
N('carta, cartae, v.', 'schrijfblad, papyrusblad | geschrift', verw=['liber'])
N('cubile, cubilis, o.', 'slaapplaats, leger | hol', i=True)
N('dimidium, dimidii, o.', 'de helft', verw=['pars'])
N('faenum, faeni, o.', 'hooi, gras',
  toel='In de handschriften ook *fenum*.')
N('filia, filiae, v.', 'dochter', prio=-1, verw=['filius'])
N('infans, infantis, m.', 'kind, zuigeling | wie nog niet spreken kan', i=True)
N('infernus, inferni, m.', 'onderwereld, dodenrijk | hel',
  toel='In 4 Ezra de plaats waar de zielen bewaard worden, niet zonder meer de hel.',
  verw=['gehenna'])
N('iuvenis, iuvenis, m.', 'jongeman, jongeling', i=True, verw=['iuventus', 'senex'])
N('senex, senis, m.', 'oude man, grijsaard', verw=['senectus', 'iuvenis'])
N('labium, labii, o.', 'lip | rand')
N('mensis, mensis, m.', 'maand', i=True, verw=['luna'])
N('miraculum, miraculi, o.', 'wonder, wonderteken', verw=['miror', 'mirabilis'])
N('momentum, momenti, o.', 'ogenblik | beweging, uitslag van de weegschaal')
N('natio, nationis, v.', 'volk, volksstam | geboorte', verw=['gens', 'nascor'])
N('pecus, pecoris, o.', 'vee, kudde', verw=['iumentum'])
N('platea, plateae, v.', 'straat, plein')
N('pratum, prati, o.', 'weide, grasland')
N('princeps, principis, m.', 'eerste, voornaamste | vorst, aanvoerder',
  verw=['principatus', 'primus'])
N('pupillus, pupilli, m.', 'weeskind, pupil', verw=['orphanus', 'vidua'])
N('orphanus, orphani, m.', 'wees, ouderloos kind',
  toel='In de handschriften ook *orfanus*; Grieks leenwoord.', verw=['pupillus'])
N('quercus, quercus, v.', 'eik, eikenboom')
N('salus, salutis, v.', 'welzijn, heil | redding, behoud', verw=['salvo', 'salvus'])
N('scientia, scientiae, v.', 'kennis, wetenschap | inzicht', verw=['scio'])
N('statura, staturae, v.', 'gestalte, lichaamslengte', verw=['sto'])
N('stillicidium, stillicidii, o.', 'druppelval, druppelend water', verw=['gutta'])
N('tempestas, tempestatis, v.', 'weersgesteldheid | storm, onweer | tijdstip',
  verw=['procella'])
N('tribus, tribus, v.', 'stam, volksstam | afdeling van het volk', prio=1,
  toel='Verwar de vormen niet met die van `tres` (drie): `tribus` is ook de datief en '
       'ablatief meervoud daarvan.', verw=['gens'])
N('tutela, tutelae, v.', 'bescherming, hoede', verw=['tutor'])
N('viduitas, viduitatis, v.', 'weduwstaat, weduwschap', verw=['vidua'])
N('voluntas, voluntatis, v.', 'wil, wens | welwillendheid', verw=['volo'])
N('vis, vis, v.', 'kracht, geweld | invloed | (meervoud vires) krachten',
  extra={'vis': 'nominatief ev. — kracht', 'vim': 'accusatief ev. — geweld',
         'vi': 'ablatief ev. — met geweld', 'vires': 'nominatief/accusatief mv. — krachten',
         'viribus': 'datief/ablatief mv. — met krachten'},
  toel='Sterk gebrekkig: de genitief en datief enkelvoud ontbreken in de praktijk.')
N('abyssus, abyssi, v.', 'afgrond, diepte | oervloed',
  toel='Grieks leenwoord (abussos, bodemloos); in de Vulgaat de oervloed en de diepte van de zee.')
N('angustia, angustiae, v.', 'nauwte, engte | benauwdheid, nood', verw=['angustus'])
N('abundantia, abundantiae, v.', 'overvloed, rijkdom', verw=['abundo'])
N('cogitatio, cogitationis, v.', 'het denken, gedachte | overweging, plan', verw=['cogito'])
N('habitatio, habitationis, v.', 'het wonen, woonplaats | woning', verw=['habito'])
N('separatio, separationis, v.', 'scheiding, afzondering', verw=['separo'])
N('malignitas, malignitatis, v.', 'boosaardigheid, kwaadwilligheid', verw=['malignus'])
A('malignus, maligna, malignum', 'boosaardig, kwaadwillig | schraal, karig',
  toel='"cor malignum" — het boze hart dat Adam meekreeg en doorgaf (4 Ezra 3:20).',
  verw=['malus', 'malignitas'])
N('hereditas, hereditatis, v.', 'erfenis, erfdeel | erfrecht', verw=['heres', 'heredito'])
N('operatio, operationis, v.', 'werking, werkzaamheid | goed werk', verw=['opus', 'operor'])
N('opera, operae, v.', 'moeite, inspanning | werk, dienst', prio=-1, verw=['opus'])
N('captivitas, captivitatis, v.', 'gevangenschap, ballingschap | de weggevoerden',
  verw=['captivus'])
A('captivus, captiva, captivum', 'gevangen, krijgsgevangen | (als zelfstandig naamwoord) '
  'gevangene', verw=['captivitas'])
N('contumelia, contumeliae, v.', 'smaad, belediging | mishandeling', verw=['obprobrium'])
A('contrarius, contraria, contrarium', 'tegenovergesteld, vijandig | ongunstig',
  verw=['contra'])
N('circumcisio, circumcisionis, v.', 'besnijdenis')
N('circuitus, circuitus, m.', 'omtrek, kringloop | omweg', verw=['circa'])
N('corruptela, corruptelae, v.', 'bederf, verleiding | verderf', verw=['corrumpo'])
N('incorruptio, incorruptionis, v.', 'onvergankelijkheid, onbederfelijkheid',
  toel='De eigenschap van de komende wereld, tegenover de `corruptio` van deze.',
  verw=['corruptio'])
N('incredulitas, incredulitatis, v.', 'ongeloof, wantrouwen', verw=['incredulus'])
N('inmortalitas, inmortalitatis, v.', 'onsterfelijkheid',
  toel='Klassiek *immortalitas*.', verw=['inmortalis'])
N('paenitentia, paenitentiae, v.', 'berouw, boete | verandering van gezindheid',
  toel='In 4 Ezra 7 de vraag of er na de dood nog gelegenheid tot berouw is.')
N('prophetia, prophetiae, v.', 'profetie, godsspraak', verw=['propheta'])
N('propheta, prophetae, m.', 'profeet, godsspreker',
  toel='Grieks leenwoord; verbuigt volgens de 1e klasse maar is mannelijk.',
  verw=['prophetia'])
N('pressura, pressurae, v.', 'druk, verdrukking | benauwdheid', verw=['tribulatio'])
N('precatio, precationis, v.', 'gebed, smeekbede', verw=['deprecatio'])
N('possessio, possessionis, v.', 'bezit, eigendom | het bezitten', verw=['possideo'])
N('celeritas, celeritatis, v.', 'snelheid, spoed', verw=['celerius'])
N('cognatio, cognationis, v.', 'verwantschap | familie, geslacht', verw=['genus'])
N('constitutio, constitutionis, v.', 'inrichting, instelling | verordening',
  verw=['constituo'])
N('confusio, confusionis, v.', 'verwarring | schaamte, schande', verw=['confundo'])
N('conceptum, concepti, o.', 'wat ontvangen is, vrucht van de schoot', verw=['concipio'])
N('aedificium, aedificii, o.', 'gebouw, bouwwerk', verw=['aedifico'])
N('agger, aggeris, m.', 'dam, wal | opgeworpen hoop')
N('acumen, acuminis, o.', 'scherpte, punt | scherpzinnigheid', verw=['acutus'])
A('acutus, acuta, acutum', 'scherp, spits | scherpzinnig', verw=['acumen'])
N('annona, annonae, v.', 'jaaropbrengst, graanvoorraad | levensmiddelenprijs', verw=['annus'])
A('anniculus, annicula, anniculum', 'eenjarig, van één jaar oud', comp=False, sup=False,
  verw=['annus'])
N('antiquitas, antiquitatis, v.', 'oudheid, hoge ouderdom', verw=['antiquus'])
A('antiquus, antiqua, antiquum', 'oud, uit vroeger tijd | eerbiedwaardig', verw=['vetus'])
N('exultatio, exultationis, v.', 'gejubel, uitbundige vreugde', verw=['exulto'])
N('iucunditas, iucunditatis, v.', 'aangenaamheid, vreugde', verw=['iucundo'])
N('medietas, medietatis, v.', 'het midden, de helft', verw=['medius'])
A('medius, media, medium', 'middelste, in het midden | halverwege', comp=False, sup=False,
  verw=['medietas'])
N('militia, militiae, v.', 'krijgsdienst, oorlogvoering | legermacht')
N('oblivio, oblivionis, v.', 'vergetelheid, het vergeten', verw=['obliviscor'])
N('plenitudo, plenitudinis, v.', 'volheid, volledigheid', verw=['plenus'])
N('transmigratio, transmigrationis, v.', 'volksverhuizing, wegvoering | ballingschap',
  verw=['transmigro'])
N('terraemotus, terraemotus, m.', 'aardbeving',
  toel='Als één woord geschreven uit `terrae motus`, "beweging van de aarde".',
  verw=['terra', 'motus'])
N('tonitruum, tonitrui, o.', 'donder, donderslag', verw=['tono'])
N('homicidium, homicidii, o.', 'moord, doodslag', verw=['homo'])
N('blasphemia, blasphemiae, v.', 'godslastering, smaadrede',
  toel='Grieks leenwoord.', verw=['blasphemo'])
N('neomenia, neomeniae, v.', 'nieuwe maan, nieuwemaansfeest',
  toel='Grieks leenwoord (neomènia); een van de feesten die het volk veronachtzaamde.')
N('ebdomas, ebdomadis, v.', 'week, zevental dagen',
  toel='Grieks leenwoord (hebdomas); klassiek gespeld *hebdomas*.', verw=['septem'])
N('christus, christi, m.', 'de Gezalfde, Christus',
  toel='Grieks leenwoord (christos, gezalfde), de vertaling van het Hebreeuwse "messias".')
X('leviathan', 'eigennaam', 'Leviathan (onverbuigbaar)', 'Leviathan, het zeemonster',
  {'leviathan': 'onverbuigbaar — Leviathan',
   'leviathae': 'genitief/datief (verlatijnste vorm)'},
  toel='Hebreeuwse naam; in 4 Ezra 6:49-52 het zeemonster naast Behemoth, geschapen op de '
       'vijfde dag.')
N('mastix, mastigis, v.', 'gesel, zweep',
  toel='Grieks leenwoord (mastix); daarvan ook het werkwoord `mastigo`, geselen.')
A3('spiritalis, spiritale', 'geestelijk, van de geest', verw=['spiritus'])
A3('volatilis, volatile', 'vliegend, gevleugeld | (als zelfstandig naamwoord) vogel',
  verw=['volo (vliegen)'])
A3('reptilis, reptile', 'kruipend | (als zelfstandig naamwoord) kruipend dier',
  verw=['serpo'])
A('salvus, salva, salvum', 'behouden, ongedeerd | gezond', verw=['salus', 'salvo'])
A3('praegnans, praegnantis', 'zwanger, drachtig | vol', een=True, comp=False, sup=False,
   verw=['gravidus'])
A('proprius, propria, proprium', 'eigen, aan zichzelf toebehorend | kenmerkend')
A3('odibilis, odibile', 'hatelijk, verafschuwd', verw=['odi'])
A3('debilis, debile', 'zwak, verzwakt | verminkt')
A3('mendax, mendacis', 'leugenachtig, bedrieglijk', een=True, verw=['mendacium'])
N('mendacium, mendacii, o.', 'leugen, onwaarheid', verw=['mendax'])
A('festus, festa, festum', 'feestelijk, feest- | (als zelfstandig naamwoord) feestdag')
A('mansuetus, mansueta, mansuetum', 'zachtmoedig, tam | mild')
A('residuus, residua, residuum', 'overblijvend, resterend | (als zelfstandig naamwoord) '
  'het overschot', verw=['remaneo'])
A3('caelestis, caeleste', 'hemels, van de hemel', verw=['caelum'])
A('terrenus, terrena, terrenum', 'aards, van aarde gemaakt', verw=['terra'])
A('campester, campestris, campestre', 'van de vlakte, veld-', verw=['campus'])
A('unicus, unica, unicum', 'enig, enkel | weergaloos', verw=['unus'])
A('unigenitus, unigenita, unigenitum', 'eniggeboren, enig kind', comp=False, sup=False,
  verw=['unus'])
A('primogenitus, primogenita, primogenitum', 'eerstgeboren | (als zelfstandig naamwoord) '
  'eerstgeborene', verw=['primus'])
A('elatus, elata, elatum', 'verheven, hooghartig | opgeheven', comp=False, sup=False)
A('citatus, citata, citatum', 'snel, gehaast | opgeroepen')
A('minutus, minuta, minutum', 'klein, gering | fijngemaakt')
A('meridianus, meridiana, meridianum', 'van de middag, zuidelijk')
A3('orientalis, orientale', 'oostelijk, van het oosten', verw=['oriens'])
N('oriens, orientis, m.', 'de opgaande zon, het oosten', verw=['orior', 'occidens'])
N('occidens, occidentis, m.', 'de ondergaande zon, het westen', verw=['oriens'])
N('septentrio, septentrionis, m.', 'het noorden, noordenwind')
N('boreas, boreae, m.', 'noordenwind, het noorden',
  toel='Grieks leenwoord; als windnaam ook de aanduiding van de windstreek.')
N('eurus, euri, m.', 'oostenwind, zuidoostenwind',
  toel='Grieks leenwoord; in 4 Ezra een van de vier windstreken.')
A3('sequens, sequentis', 'volgend, daaropvolgend', een=True, comp=False, sup=False,
   verw=['sequor'])
A('permissus, permissa, permissum', 'toegestaan, geoorloofd', comp=False, sup=False)

V('supero, superare, superavi, superatum', 'overtreffen, te boven gaan | overwinnen | '
  'overblijven, over zijn', verw=['super'])
V('superabundo, superabundare, superabundavi, superabundatum', 'overvloedig aanwezig zijn',
  verw=['abundo'])
V('abundo, abundare, abundavi, abundatum', 'overvloeien, in overvloed hebben',
  verw=['abundantia'])
V('supersigno, supersignare, supersignavi, supersignatum', 'verzegelen, met een teken merken',
  verw=['signo'])
V('superelevo, superelevare, superelevavi, superelevatum', 'zich hoog verheffen, opzwellen',
  verw=['elevo'])
V('elevo, elevare, elevavi, elevatum', 'opheffen, verheffen', verw=['levo'])
V('superfloresco, superflorescere', 'bovenmatig bloeien, in bloei uitbotten', k='3',
  verw=['floreo'])
V('floreo, florere, florui', 'bloeien, in bloei staan', k='2', verw=['flos'])
V('supervalesco, supervalescere', 'sterk worden, de overhand krijgen', k='3',
  toel='Laat-Latijnse vorming; 4 Ezra houdt van dit soort samenstellingen met super-.')
V('superinvalesco, superinvalescere', 'de overhand krijgen, sterker worden', k='3',
  verw=['supervalesco'])
V('convalesco, convalescere, convalui', 'sterk worden, aansterken', k='3')
V('corrumpo, corrumpere, corrupi, corruptum', 'bederven, vernietigen | verleiden, omkopen',
  k='3', verw=['corruptio', 'corruptela'])
V('contradico, contradicere, contradixi, contradictum', 'tegenspreken, weerspreken', k='3',
  verw=['dico'])
V('expavesco, expavescere, expavi', 'hevig schrikken, sidderen', k='3',
  verw=['paveo', 'expaveo'])
V('expaveo, expavere, expavi', 'hevig vrezen, terugdeinzen', k='2', verw=['expavesco'])
V('paveo, pavere, pavi', 'beven van angst, vrezen', k='2', verw=['pavor'])
N('pavor, pavoris, m.', 'schrik, angst | beving', verw=['paveo'])
V('captivo, captivare, captivavi, captivatum', 'gevangennemen, wegvoeren',
  verw=['captivus'])
V('circumfero, circumferre, circumtuli, circumlatum', 'ronddragen, rondvoeren', k='3',
  extra={'circumferebantur': '3e pers. mv., verleden tijd, lijdende vorm — zij werden rondgedragen'},
  verw=['fero'])
V('circumteneo, circumtinere, circumtinui', 'rondom vasthouden, omsluiten', k='2',
  extra={'circumtenent': '3e pers. mv., tegenwoordige tijd — zij omsluiten'}, verw=['teneo'])
V('praecipio, praecipere, praecepi, praeceptum', 'vooraf nemen | voorschrijven, bevelen',
  k='3io', verw=['praeceptum', 'mando'])
V('praecedo, praecedere, praecessi, praecessum', 'voorafgaan, vooruitgaan', k='3',
  verw=['cedo'])
V('intermitto, intermittere, intermisi, intermissum', 'onderbreken, nalaten', k='3',
  verw=['mitto', 'intermissio'])
V('interpreto, interpretare, interpretavi, interpretatum', 'uitleggen, verklaren',
  naam='interpreto (actieve nevenvorm)', prio=-1,
  toel='Laat-Latijnse actieve nevenvorm naast het deponens `interpretor`.',
  verw=['interpretor'])
V('fructifico, fructificare, fructificavi, fructificatum', 'vrucht dragen, vruchtbaar zijn',
  verw=['fructus'])
V('fructifero, fructiferare, fructiferavi, fructiferatum', 'vrucht voortbrengen',
  toel='Zeldzame laat-Latijnse nevenvorm van fructificare.', verw=['fructifico'])
V('revertor, reverti, reversus sum', 'terugkeren, omkeren', k='3d', verw=['verto'])
V('genero, generare, generavi, generatum', 'voortbrengen, verwekken',
  verw=['genus', 'generatio'])
V('separo, separare, separavi, separatum', 'scheiden, afzonderen', verw=['separatio'])
V('segrego, segregare, segregavi, segregatum', 'afzonderen, uitzonderen', verw=['separo'])
V('tremo, tremere, tremui', 'beven, sidderen', k='3', verw=['tremor', 'tremesco'])
V('tremesco, tremescere', 'beginnen te beven, sidderen', k='3', verw=['tremo'])
V('trepido, trepidare, trepidavi, trepidatum', 'angstig heen en weer lopen, beven')
V('heredito, hereditare, hereditavi, hereditatum', 'erven, in bezit nemen',
  toel='Laat-Latijns, gevormd bij `hereditas`.', verw=['hereditas'])
V('revelo, revelare, revelavi, revelatum', 'ontsluieren, openbaren',
  toel='Letterlijk "de sluier wegnemen"; het woord waaruit "openbaring" (revelatio) komt.',
  verw=['velum'])
V('operor, operari, operatus sum', 'werken, werkzaam zijn | verrichten', k='1d',
  verw=['opus', 'operatio'])
V('extermino, exterminare, exterminavi, exterminatum', 'verdrijven, verdelgen',
  verw=['exterminium'])
V('praesto, praestare, praestiti, praestitum', 'vooraan staan, uitmunten | verschaffen, '
  'bewijzen', verw=['sto'])
V('comminor, comminari, comminatus sum', 'dreigen, bedreigen', k='1d')
V('committo, committere, commisi, commissum', 'samenbrengen | toevertrouwen | bedrijven',
  k='3', verw=['mitto'])
V('reprobo, reprobare, reprobavi, reprobatum', 'afkeuren, verwerpen', verw=['probo'])
V('repromitto, repromittere, repromisi, repromissum', 'plechtig beloven, toezeggen', k='3',
  verw=['promitto'])
V('promitto, promittere, promisi, promissum', 'beloven, toezeggen', k='3', verw=['mitto'])
V('praetereo, praeterire, praeterii, praeteritum', 'voorbijgaan, verstrijken | overslaan',
  k='4', extra={'praeteriit': '3e pers. ev., perfectum — het ging voorbij',
                'praeterivit': '3e pers. ev., perfectum (volle vorm)',
                'praeterientis': 'tegenwoordig deelwoord, genitief ev. — van het voorbijgaande'},
  verw=['transeo'])
V('domino, dominare, dominavi, dominatum', 'heersen, gebieden',
  naam='domino (actieve nevenvorm)', prio=-1,
  toel='Laat-Latijnse actieve nevenvorm naast het deponens `dominor`.', verw=['dominor'])
V('transmigro, transmigrare, transmigravi, transmigratum', 'verhuizen, wegtrekken | in '
  'ballingschap gaan', verw=['transmigratio'])
V('transfero, transferre, transtuli, translatum', 'overbrengen, verplaatsen | vertalen',
  k='3', extra={'transtulit': '3e pers. ev., perfectum — hij bracht over',
                'transtulerunt': '3e pers. mv., perfectum — zij brachten over',
                'transferam': '1e pers. ev., toekomende tijd — ik zal overbrengen',
                'translati': 'voltooid deelwoord, nominatief mv. mannelijk — overgebracht'},
  verw=['fero'])
V('offero, offerre, obtuli, oblatum', 'aanbieden, opdragen | offeren', k='3',
  extra={'offerre': 'onbepaalde wijs — aan te bieden',
         'offerebantur': '3e pers. mv., verleden tijd, lijdende vorm — zij werden geofferd',
         'obtulit': '3e pers. ev., perfectum — hij offerde',
         'obtuleritis': '2e pers. mv., voltooid toekomende tijd — als gij geofferd zult hebben',
         'oblata': 'voltooid deelwoord, vrouwelijk/onzijdig mv. — geofferd'},
  verw=['fero', 'oblatio'])
V('adfero, adferre, adtuli, adlatum', 'aanbrengen, aandragen | berichten', k='3',
  extra={'adferet': '3e pers. ev., toekomende tijd — hij zal aanbrengen'}, verw=['fero'])
V('confero, conferre, contuli, conlatum', 'samenbrengen, vergelijken | bijdragen', k='3',
  extra={'contuli': '1e pers. ev., perfectum — ik bracht samen'}, verw=['fero'])
V('aufero, auferre, abstuli, ablatum', 'wegnemen, wegdragen | ontnemen', k='3',
  extra={'abstulit': '3e pers. ev., perfectum — hij nam weg',
         'abstulisti': '2e pers. ev., perfectum — gij hebt weggenomen'}, verw=['fero'])
V('circueo, circuire, circuii, circuitum', 'rondgaan, omcirkelen', k='4',
  extra={'circuibunt': '3e pers. mv., toekomende tijd — zij zullen rondgaan'},
  verw=['circuitus', 'eo'])
V('adduco, adducere, adduxi, adductum', 'aanvoeren, brengen | bewegen tot', k='3',
  verw=['duco'])
V('traduco, traducere, traduxi, traductum', 'overbrengen, overzetten', k='3', verw=['duco'])
V('produco, producere, produxi, productum', 'voortbrengen, tevoorschijn brengen', k='3',
  verw=['duco'])
V('deduco, deducere, deduxi, deductum', 'wegleiden, afvoeren', k='3', verw=['duco'])
V('admitto, admittere, admisi, admissum', 'toelaten, binnenlaten | begaan', k='3',
  verw=['mitto'])
V('adtendo, adtendere, adtendi, adtentum', 'de aandacht richten op, letten op', k='3',
  toel='Klassiek *attendo*.', verw=['tendo'])
V('intendo, intendere, intendi, intentum', 'spannen, richten | zich toeleggen op', k='3',
  verw=['tendo'])
V('adpono, adponere, adposui, adpositum', 'erbij plaatsen, toevoegen', k='3',
  toel='Klassiek *appono*.', verw=['pono'])
V('antepono, anteponere, anteposui, antepositum', 'vooropstellen, verkiezen boven', k='3',
  verw=['pono'])
V('subiicio, subicere, subieci, subiectum', 'onderwerpen, eronder plaatsen', k='3io',
  naam='subicio', verw=['proicio'])
V('alieno, alienare, alienavi, alienatum', 'vervreemden, afstaan', verw=['alienus'])
A('alienus, aliena, alienum', 'van een ander, vreemd | ongunstig', verw=['alienigena'])
V('alligo, alligare, alligavi, alligatum', 'vastbinden, boeien',
  toel='In de handschriften ook *adligo*.', verw=['ligo'])
V('adlido, adlidere, adlisi, adlisum', 'ergens tegenaan slaan, verpletteren', k='3',
  toel='Klassiek *allido*; ook geschreven als *conlido/collido*.')
V('arefacio, arefacere, arefeci, arefactum', 'doen verdorren, uitdrogen', k='3io',
  verw=['aridus', 'facio'])
V('arguo, arguere, argui, argutum', 'aantonen | beschuldigen, terechtwijzen', k='3')
V('castigo, castigare, castigavi, castigatum', 'terechtwijzen, kastijden',
  verw=['castigatio'])
V('cano, canere, cecini, cantum', 'zingen | (van instrumenten) klinken, blazen', k='3',
  verw=['canticum'])
V('cesso, cessare, cessavi, cessatum', 'ophouden, rusten | talmen')
V('cibo, cibare, cibavi, cibatum', 'voeden, te eten geven', verw=['esca'])
V('coinquino, coinquinare, coinquinavi, coinquinatum', 'bezoedelen, verontreinigen',
  verw=['contamino'])
V('contamino, contaminare, contaminavi, contaminatum', 'bezoedelen, ontheiligen',
  verw=['coinquino'])
V('concipio, concipere, concepi, conceptum', 'opnemen, bevatten | ontvangen (zwanger worden)',
  k='3io', verw=['capio', 'conceptum'])
V('concupisco, concupiscere, concupivi, concupitum', 'hevig begeren, verlangen naar', k='3',
  verw=['concupiscentia'])
V('condemno, condemnare, condemnavi, condemnatum', 'veroordelen, schuldig verklaren',
  verw=['iudico'])
V('consisto, consistere, constiti', 'zich opstellen, standhouden | bestaan', k='3',
  verw=['sto'])
V('consto, constare, constiti', 'vaststaan, bestaan | overeenstemmen', verw=['sto'])
V('conticesco, conticescere, conticui', 'verstommen, zwijgen', k='3', verw=['taceo'])
V('corripio, corripere, corripui, correptum', 'aangrijpen | berispen, terechtwijzen',
  k='3io', verw=['rapio'])
V('corusco, coruscare, coruscavi, coruscatum', 'flikkeren, bliksemen', verw=['coruscus'])
V('cupio, cupere, cupivi, cupitum', 'begeren, verlangen', k='3io', verw=['concupisco'])
V('debello, debellare, debellavi, debellatum', 'de oorlog uitvechten, onderwerpen',
  verw=['bellum'])
V('declino, declinare, declinavi, declinatum', 'afbuigen, afwijken | ontwijken')
V('defleo, deflere, deflevi, defletum', 'bewenen, beklagen', k='2', verw=['fleo'])
V('demolior, demoliri, demolitus sum', 'afbreken, verwoesten', k='4d', verw=['destruo'])
V('deputo, deputare, deputavi, deputatum', 'toewijzen, bestemmen | achten')
V('derideo, deridere, derisi, derisum', 'uitlachen, bespotten', k='2', verw=['inrideo'])
V('inrideo, inridere, inrisi, inrisum', 'bespotten, uitlachen', k='2',
  toel='Klassiek *irrideo*.', verw=['derideo'])
V('desino, desinere, desii, desitum', 'ophouden, eindigen', k='3', verw=['finio'])
V('detineo, detinere, detinui, detentum', 'vasthouden, ophouden', k='2', verw=['teneo'])
V('devinco, devincere, devici, devictum', 'volledig overwinnen', k='3', verw=['vinco'])
V('dissipo, dissipare, dissipavi, dissipatum', 'verstrooien, uiteendrijven',
  verw=['dispergo'])
V('effugio, effugere, effugi', 'ontvluchten, ontkomen aan', k='3io', verw=['fugio'])
V('fugio, fugere, fugi, fugitum', 'vluchten, ontvluchten | mijden', k='3io',
  verw=['fuga', 'effugio'])
N('fuga, fugae, v.', 'vlucht, het vluchten', verw=['fugio'])
V('egeo, egere, egui', 'gebrek hebben, behoeven', k='2', verw=['paupertas'])
V('erigo, erigere, erexi, erectum', 'oprichten, opheffen | bemoedigen', k='3', verw=['rego'])
V('eripio, eripere, eripui, ereptum', 'ontrukken, bevrijden', k='3io', verw=['rapio'])
V('eructo, eructare, eructavi, eructatum', 'oprispen, uitstoten | uitspreken')
V('evigilo, evigilare, evigilavi, evigilatum', 'wakker worden, ontwaken', verw=['vigilo'])
V('excutio, excutere, excussi, excussum', 'uitschudden, afschudden | onderzoeken', k='3io')
V('exhibeo, exhibere, exhibui, exhibitum', 'tonen, verschaffen | bewijzen', k='2',
  verw=['habeo'])
V('existimo, existimare, existimavi, existimatum', 'menen, oordelen', verw=['aestimo'])
V('expando, expandere, expandi, expansum', 'uitspreiden, openspreiden', k='3')
V('expecto, expectare, expectavi, expectatum', 'verwachten, afwachten',
  toel='In de handschriften ook *exspecto*.')
V('expugno, expugnare, expugnavi, expugnatum', 'bestormen, veroveren', verw=['pugna'])
V('exuo, exuere, exui, exutum', 'uittrekken, ontdoen van', k='3')
V('fatigo, fatigare, fatigavi, fatigatum', 'vermoeien, afmatten', verw=['defatigatio'])
V('fastidio, fastidire, fastidivi, fastiditum', 'walgen van, versmaden', k='4')
V('fulgeo, fulgere, fulsi', 'schitteren, bliksemen', k='2', verw=['splendor'])
V('fundo, fundare, fundavi, fundatum', 'grondvesten, stichten',
  naam='fundo (grondvesten)', prio=-1, verw=['fundamentum'])
V('gemo, gemere, gemui, gemitum', 'zuchten, kreunen', k='3', verw=['gemitus'])
V('germino, germinare, germinavi, germinatum', 'uitspruiten, ontkiemen', verw=['germen'])
V('guberno, gubernare, gubernavi, gubernatum', 'sturen, besturen')
V('ignoro, ignorare, ignoravi, ignoratum', 'niet weten, onbekend zijn met', verw=['nescio'])
V('incido, incidere, incidi, incasum', 'vallen in, overkomen | voorvallen', k='3',
  verw=['cado'])
V('inclino, inclinare, inclinavi, inclinatum', 'buigen, neigen', verw=['declino'])
V('inebrio, inebriare, inebriavi, inebriatum', 'dronken maken, doordrenken')
V('infirmo, infirmare, infirmavi, infirmatum', 'verzwakken, ontkrachten', verw=['infirmitas'])
V('infulcio, infulcire, infulsi, infultum', 'inproppen, inprenten', k='4')
V('insuflo, insuflare, insuflavi, insuflatum', 'inblazen, aanblazen',
  toel='Klassiek *insufflo*; het woord voor Gods inblazen van de levensadem.')
V('inveterasco, inveterascere, inveteravi', 'verouderen, ingeworteld raken', k='3',
  verw=['vetus'])
V('inluminо, inluminare, inluminavi, inluminatum', 'verlichten, doen oplichten',
  naam='inlumino', toel='Klassiek *illumino*.', verw=['lumen'])
V('liquesco, liquescere, licui', 'smelten, vloeibaar worden', k='3')
V('magnifico, magnificare, magnificavi, magnificatum', 'grootmaken, verheerlijken',
  verw=['magnus'])
V('manifesto, manifestare, manifestavi, manifestatum', 'openbaren, duidelijk maken',
  verw=['revelo'])
V('mastigo, mastigare, mastigavi, mastigatum', 'geselen, met de zweep slaan',
  verw=['mastix'])
V('meto, metere, messui, messum', 'maaien, oogsten', k='3', verw=['messis'])
N('messis, messis, v.', 'oogst, maaitijd', i=True, verw=['meto'])
V('metuo, metuere, metui', 'vrezen, bang zijn voor', k='3', verw=['timeo'])
V('minuo, minuere, minui, minutum', 'verkleinen, verminderen', k='3', verw=['minor'])
V('moror, morari, moratus sum', 'talmen, verwijlen | ophouden', k='1d')
V('mugio, mugire, mugivi, mugitum', 'loeien, bulderen', k='4')
V('nubo, nubere, nupsi, nuptum', 'trouwen (van de vrouw), huwen', k='3', prio=-1)
V('occurro, occurrere, occurri, occursum', 'tegemoet lopen, ontmoeten', k='3', verw=['curro'])
V('omitto, omittere, omisi, omissum', 'nalaten, achterwege laten', k='3', verw=['mitto'])
V('opto, optare, optavi, optatum', 'wensen, verlangen')
V('parco, parcere, peperci, parsum', 'sparen, ontzien | zich onthouden van', k='3')
V('percontinuo, percontinuare, percontinuavi, percontinuatum', 'aaneengesloten voortzetten')
V('percutio, percutere, percussi, percussum', 'doorstoten, treffen | slaan', k='3io',
  verw=['percussio'])
V('pergo, pergere, perrexi, perrectum', 'voortgaan, verdergaan', k='3', verw=['rego'])
V('periclitor, periclitari, periclitatus sum', 'in gevaar verkeren, gevaar lopen', k='1d',
  verw=['periculum'])
V('permitto, permittere, permisi, permissum', 'toestaan, overlaten', k='3', verw=['mitto'])
V('persuadeo, persuadere, persuasi, persuasum', 'overtuigen, overreden', k='2')
V('pervideo, pervidere, pervidi, pervisum', 'geheel overzien, doorzien', k='2', verw=['video'])
V('porrigo, porrigere, porrexi, porrectum', 'uitstrekken, aanreiken', k='3', verw=['rego'])
V('poto, potare, potavi, potatum', 'drinken, laten drinken', prio=-1, verw=['potus'])
V('praepondero, praeponderare, praeponderavi, praeponderatum', 'zwaarder wegen, overwegen',
  verw=['pondero'])
V('prodeo, prodire, prodii, proditum', 'te voorschijn komen, uitgaan', k='4', verw=['eo'])
V('profano, profanare, profanavi, profanatum', 'ontwijden, ontheiligen', verw=['sanctifico'])
V('prohibeo, prohibere, prohibui, prohibitum', 'verhinderen, weerhouden', k='2',
  verw=['habeo'])
V('prolongo, prolongare, prolongavi, prolongatum', 'verlengen, uitstellen')
V('provideo, providere, providi, provisum', 'vooruitzien, zorgen voor', k='2', verw=['video'])
V('radico, radicare, radicavi, radicatum', 'wortel schieten, wortelen', prio=-1,
  verw=['radix'])
V('recapitulo, recapitulare, recapitulavi, recapitulatum', 'samenvatten, hervatten',
  toel='Laat-Latijnse vorming bij `caput`: onder één hoofd samenbrengen.', verw=['caput'])
V('recumbo, recumbere, recubui', 'aanliggen, gaan liggen', k='3')
V('recutio, recutere, recussi, recussum', 'terugslaan, doen terugdeinzen', k='3io')
V('relucesco, relucescere', 'weer gaan lichten, opnieuw oplichten', k='3', verw=['luceo'])
V('renovo, renovare, renovavi, renovatum', 'vernieuwen, herstellen', verw=['novus'])
V('repleo, replere, replevi, repletum', 'weer vullen, geheel vullen', k='2', verw=['impleo'])
V('repudio, repudiare, repudiavi, repudiatum', 'verstoten, verwerpen')
V('resigno, resignare, resignavi, resignatum', 'ontzegelen, openen', verw=['signo'])
V('respuo, respuere, respui', 'uitspuwen, verwerpen', k='3')
V('resuscito, resuscitare, resuscitavi, resuscitatum', 'weer opwekken, doen herleven',
  verw=['suscito'])
V('revivesco, reviviscere, revixi', 'weer levend worden, herleven', k='3',
  naam='revivesco', verw=['vivo'])
V('sacrifico, sacrificare, sacrificavi, sacrificatum', 'offeren, een offer brengen',
  verw=['sacer'])
V('senesco, senescere, senui', 'oud worden, verouderen', k='3', verw=['senectus', 'senex'])
V('sicco, siccare, siccavi, siccatum', 'drogen, droogleggen', verw=['siccus'])
V('sono, sonare, sonui, sonitum', 'klinken, weerklinken', verw=['sonus'])
V('spiro, spirare, spiravi, spiratum', 'ademen, blazen', verw=['spiritus'])
V('splendeo, splendere, splendui', 'schitteren, glanzen', k='2', verw=['splendor'])
V('spolio, spoliare, spoliavi, spoliatum', 'beroven, plunderen', verw=['rapina'])
V('stillo, stillare, stillavi, stillatum', 'druppelen, laten druppelen', verw=['gutta'])
V('suspendo, suspendere, suspendi, suspensum', 'ophangen, in de lucht houden', k='3')
V('suspiro, suspirare, suspiravi, suspiratum', 'zuchten, verzuchten', verw=['spiro'])
V('tabesco, tabescere, tabui', 'wegkwijnen, verteren', k='3')
V('thesaurizo, thesaurizare, thesaurizavi, thesaurizatum', 'schatten verzamelen, opslaan',
  toel='Grieks leenwoord; in 4 Ezra 7 het verzamelen van schatten van goede werken.',
  verw=['thesaurus'])
V('tono, tonare, tonui', 'donderen, dreunen', verw=['tonitruum'])
V('traicio, traicere, traieci, traiectum', 'overzetten, doorsteken', k='3io')
V('ululo, ululare, ululavi, ululatum', 'huilen, weeklagen')
V('ventilo, ventilare, ventilavi, ventilatum', 'wannen, in de wind schudden', verw=['ventus'])
V('verbero, verberare, verberavi, verberatum', 'slaan, geselen')
V('vindemio, vindemiare, vindemiavi, vindemiatum', 'de wijnoogst binnenhalen',
  verw=['vindemia'])
V('plango, plangere, planxi, planctum', 'slaan (op de borst), weeklagen', k='3',
  verw=['planctus'])
V('propitior, propitiari, propitiatus sum', 'gunstig gestemd worden, zich verzoenen', k='1d')
V('anxior, anxiari, anxiatus sum', 'angstig zijn, benauwd zijn', k='1d')
V('amaricor, amaricari, amaricatus sum', 'verbitterd worden, bitter zijn', k='1d',
  verw=['amarus'])
A('amarus, amara, amarum', 'bitter | bitter van smaak, verbitterd', verw=['amaricor'])
V('aporior, aporiari, aporiatus sum', 'in verlegenheid zijn, radeloos zijn', k='1d',
  toel='Grieks leenwoord (aporein, geen uitweg weten); zeldzaam buiten de Vulgaat.')
V('scirto, scirtare, scirtavi, scirtatum', 'huppelen, van vreugde opspringen',
  toel='Grieks leenwoord (skirtan); komt vrijwel alleen in 4 Ezra voor.')
V('baiulo, baiulare, baiulavi, baiulatum', 'dragen, torsen', verw=['porto'])
V('haesito, haesitare, haesitavi, haesitatum', 'aarzelen, weifelen')
V('adsumo, adsumere, adsumpsi, adsumptum', 'opnemen, tot zich nemen', k='3',
  toel='Klassiek *assumo*.', verw=['sumo'])
V('advento, adventare, adventavi, adventatum', 'naderen, aankomen', verw=['advenio'])
V('advoco, advocare, advocavi, advocatum', 'erbij roepen, ontbieden', verw=['voco'])
V('abnego, abnegare, abnegavi, abnegatum', 'ontkennen, verloochenen', verw=['nego'])
V('nego, negare, negavi, negatum', 'ontkennen, weigeren', verw=['abnego'])
V('abalieno, abalienare, abalienavi, abalienatum', 'vervreemden, wegnemen', verw=['alieno'])
V('blasphemo, blasphemare, blasphemavi, blasphematum', 'lasteren, godslasterlijk spreken',
  verw=['blasphemia'])
V('conburo, conburere, conbussi, conbustum', 'verbranden, in de as leggen', k='3',
  toel='Klassiek *comburo*.', verw=['ardeo'])
V('conspiro, conspirare, conspiravi, conspiratum', 'samenzweren, samenspannen',
  verw=['spiro'])
V('conmoror, conmorari, conmoratus sum', 'verblijven, vertoeven', k='1d', verw=['moror'])
V('conplector, conplecti, conplexus sum', 'omvatten, omhelzen', k='3d',
  toel='Klassiek *complector*.', verw=['amplector'])
V('conquiro, conquirere, conquisivi, conquisitum', 'opsporen, bijeenzoeken', k='3',
  verw=['quaero'])
V('convolo, convolare, convolavi, convolatum', 'samenvliegen, toesnellen',
  verw=['volo (vliegen)'])
V('corono, coronare, coronavi, coronatum', 'kronen, bekransen', verw=['corona'])
V('deficio, deficere, defeci, defectum', 'ontbreken', naam='deficio (nevenvorm)', prio=-3)
V('dissolvo, dissolvere, dissolvi, dissolutum', 'ontbinden', naam='dissolvo (nevenvorm)',
  prio=-3)
V('exubero, exuberare, exuberavi, exuberatum', 'overvloeien, welig groeien')
V('expergefacio, expergefacere, expergefeci, expergefactum', 'wakker maken, doen ontwaken',
  k='3io', verw=['vigilo'])
V('extollo, extollere', 'omhoogheffen, verheffen', k='3', verw=['tollo'])
V('impetro, impetrare, impetravi, impetratum', 'verkrijgen, gedaan krijgen',
  toel='In de handschriften ook *inpetro*.')
V('inproperо, inproperare, inproperavi, inproperatum', 'verwijten, smaden',
  naam='inpropero', verw=['inproperium'])
V('minoro, minorare, minoravi, minoratum', 'verkleinen, verminderen', verw=['minuo'])
V('nutrio, nutrire, nutrivi, nutritum', 'voeden', naam='nutrio (nevenvorm)', prio=-3)
V('perrogo, perrogare, perrogavi, perrogatum', 'doorvragen, uitvragen', verw=['rogo'])
V('propero, properare, properavi, properatum', 'zich haasten, spoeden', verw=['festino'])
V('subremaneo, subremanere, subremansi', 'nog enigszins overblijven', k='2',
  toel='Laat-Latijnse samenstelling; in 4 Ezra van wat er na het oordeel overblijft.',
  verw=['remaneo'])
V('subsequor, subsequi, subsecutus sum', 'onmiddellijk volgen, achternagaan', k='3d',
  verw=['sequor'])
V('subduco, subducere, subduxi, subductum', 'wegtrekken', naam='subduco (nevenvorm)',
  prio=-3)
V('treicio, treicere, treieci, treiectum', 'doorsteken, doorboren', k='3io',
  toel='Nevenvorm van *traicio* in de handschriften van 4 Ezra.', verw=['traicio'])
V('vado, vadere', 'gaan, voortschrijden', k='3',
  extra={'vade': 'gebiedende wijs ev. — ga!', 'vadens': 'tegenwoordig deelwoord — gaande'},
  toel='"vade" is in 4 Ezra 1 het bevel waarmee God Ezra naar zijn volk stuurt.',
  verw=['eo'])
I('vae', 'tussenwerpsel', 'wee! | ach! (uitroep van klacht of dreiging)')
I('adextera', 'bijwoordelijke uitdrukking', 'aan de rechterhand, ter rechterzijde',
  toel='In de handschriften aaneengeschreven uit `ad dextera(m)`.')
I('exagro', 'bijwoordelijke uitdrukking', 'van het veld, uit het land',
  toel='Aaneengeschreven uit `ex agro`.')
I('invio', 'bijwoordelijke uitdrukking', 'op de weg, onderweg',
  toel='Aaneengeschreven uit `in via`.')

# --- laatste aanvullingen op de woordenschat -----------------------------
I('ac', 'voegwoord', 'en, en ook | (na woorden van gelijkheid) als, dan',
  toel='Nevenvorm van `atque`; staat voor een medeklinker.', verw=['et'])
I('adeo', 'bijwoord', 'zozeer, in die mate | zelfs', prio=1)
I('false', 'bijwoord', 'ten onrechte, bedrieglijk', verw=['falsus'])
I('absconse', 'bijwoord', 'in het verborgen, heimelijk', verw=['abscondo'])
I('peromnes', 'bijwoordelijke uitdrukking', 'door allen heen, overal',
  toel='Aaneengeschreven uit `per omnes`.')

N('absolutio, absolutionis, v.', 'voltooiing, afronding | vrijspraak', verw=['absolvo'])
N('adnuntium, adnuntii, o.', 'aankondiging, boodschap', verw=['adnuntio'])
N('destrictio, destrictionis, v.', 'afsnijding, strenge scheiding | gestrengheid')
N('successio, successionis, v.', 'opeenvolging, opvolging')
N('peregrinatio, peregrinationis, v.', 'verblijf in den vreemde, omzwerving',
  verw=['peregrinor'])
N('miseria, miseriae, v.', 'ellende, rampspoed', verw=['miser'])
N('maeror, maeroris, m.', 'droefheid, smart', verw=['maestitia'])
N('nitor, nitoris, m.', 'glans, schittering', verw=['splendor'])
N('ordo, ordinis, m.', 'rij, orde | rangschikking, regel')
N('pestis, pestis, v.', 'pest, besmettelijke ziekte | verderf', i=True)
N('punctum, puncti, o.', 'punt, stip | ogenblik',
  toel='"in puncto" — in een ondeelbaar ogenblik; 4 Ezra gebruikt het voor de plotselinge '
       'omslag van de tijden.')
N('profundum, profundi, o.', 'diepte, afgrond | het diepe van de zee', verw=['abyssus'])
N('incendium, incendii, o.', 'brand, vuurgloed', verw=['incendo'])
N('decor, decoris, m.', 'sieraad, bevalligheid | luister', verw=['decorus'])
A('decorus, decora, decorum', 'sierlijk, passend | luisterrijk', verw=['decor'])
N('sagittarius, sagittarii, m.', 'boogschutter', verw=['sagitta'])
N('sponsus, sponsi, m.', 'bruidegom, verloofde', verw=['sponsa'])
N('viduus, vidui, m.', 'weduwnaar | (bijvoeglijk) beroofd, verlaten', verw=['vidua'])
N('liberi, liberorum, m.', 'kinderen (van vrije ouders)',
  toel='Alleen in het meervoud; niet te verwarren met `liber` (boek) of `liber` (vrij).',
  verw=['filius'])
N('parens, parentis, m.', 'ouder, vader of moeder | voorvader', i=True,
  verw=['pater', 'mater'])
N('palma, palmae, v.', 'handpalm, hand | palmtak, zegepalm')
N('manna, mannae, v.', 'manna, hemels brood',
  toel='Hebreeuws leenwoord; in de Vulgaat meestal onverbuigbaar onzijdig, maar 4 Ezra heeft '
       'de accusatief `mannam`.')
N('buxus, buxi, v.', 'buksboom, palmhout')
N('tinctura, tincturae, v.', 'verf, kleurstof | het verven')
N('suffrago, suffraginis, v.', 'kniebuiging, hielgewricht')
N('susceptorium, susceptorii, o.', 'opvangplaats, bergplaats', verw=['suscipio'])
N('salutare, salutaris, o.', 'heil, redding', i=True, verw=['salus'])
N('coadulescentia, coadulescentiae, v.', 'het samen opgroeien, meegroeien',
  toel='Zeldzame laat-Latijnse vorming; in 4 Ezra 4:11 van wat met de mens meegroeit.')
N('extritio, extritionis, v.', 'vermorzeling, vernietiging', verw=['extero'])
N('lapsus, lapsus, m.', 'val, uitglijden | misstap', verw=['labor (glijden)'])
N('unctus, uncti, m.', 'gezalfde, de gezalfde',
  toel='Voltooid deelwoord van `unguo` (zalven), zelfstandig gebruikt; de Latijnse tegenhanger '
       'van "messias" en "christus".', verw=['christus'])

A('crastinus, crastina, crastinum', 'van morgen, morgig', comp=False, sup=False)
A('falsus, falsa, falsum', 'onwaar, bedrieglijk | vals', bijw='false', verw=['fallo'])
A('irritus, irrita, irritum', 'ongeldig, krachteloos | vergeefs')
A('inconpositus, inconposita, inconpositum', 'ongeordend, wanordelijk',
  toel='Klassiek *incompositus*; in 4 Ezra van de aarde vóór de scheppingsordening.')
A('indisciplinatus, indisciplinata, indisciplinatum', 'ongetuchtigd, tuchteloos',
  verw=['disciplina'])
A('infirmus, infirma, infirmum', 'zwak, krachteloos | ziek', verw=['infirmitas'])
A('innocuus, innocua, innocuum', 'onschadelijk, onschuldig', verw=['innoxius'])
A('insanus, insana, insanum', 'krankzinnig, razend', verw=['insanio'])
A('menstruatus, menstruata, menstruatum', 'onrein, in de maandelijkse onreinheid',
  comp=False, sup=False, verw=['mensis'])
A('obscurus, obscura, obscurum', 'donker, duister | onduidelijk')
A('pacificus, pacifica, pacificum', 'vreedzaam, vredestichtend', verw=['pax'])
A('pusillus, pusilla, pusillum', 'heel klein, gering', comp=False, sup=False,
  verw=['parvus'])
A('vicinus, vicina, vicinum', 'naburig, dichtbij | (als zelfstandig naamwoord) buur')
A3('exilis, exile', 'dun, schraal | gering, onbeduidend')
A3('fictilis, fictile', 'van aarde gebakken | (als zelfstandig naamwoord) aarden vat',
   verw=['fingo'])
A3('subalaris, subalare', 'onder de vleugel gelegen | (als zelfstandig naamwoord) '
   'ondervleugel', verw=['ala'])
A3('praeceps, praecipitis', 'hals over kop, steil | overijld', een=True)
X('superior', 'bijvoeglijk naamwoord (vergrotende trap)', 'superior, superius',
  'hoger gelegen, bovenste | vroeger, eerder',
  {'superior': 'nominatief ev. mannelijk/vrouwelijk', 'superius': 'nominatief/accusatief ev. onzijdig',
   'superiorem': 'accusatief ev. mannelijk/vrouwelijk',
   'superiores': 'nominatief/accusatief mv. mannelijk/vrouwelijk',
   'superiora': 'nominatief/accusatief mv. onzijdig',
   'superioribus': 'datief/ablatief mv.'}, verw=['super', 'supra'])
X('quisquis', 'onbepaald betrekkelijk voornaamwoord', 'quisquis, quicquid',
  'wie ook maar, al wie | wat ook maar, al wat',
  {'quisquis': 'nominatief ev. mannelijk', 'quicquid': 'nominatief/accusatief ev. onzijdig',
   'quidquid': 'nominatief/accusatief ev. onzijdig (volle spelling)'}, verw=['quisquam'])
X('chaos', 'zelfstandig naamwoord (onzijdig)', 'chaos, chai',
  'chaos, de ongeordende oertoestand | gapende diepte',
  {'chaos': 'nominatief/accusatief ev.', 'chaus': 'nominatief ev. (spelling in de handschriften)',
   'chao': 'ablatief ev.'},
  toel='Grieks leenwoord; in 4 Ezra 6:39 de toestand vóór de scheppingsordening.',
  verw=['abyssus'])

V('adsto, adstare, adstiti', 'erbij staan, naast iemand staan',
  toel='Klassiek *asto*.', verw=['sto'])
V('adimpleo, adimplere, adimplevi, adimpletum', 'geheel vervullen, volmaken', k='2',
  verw=['impleo'])
V('apparesco, apparescere', 'te voorschijn komen, zichtbaar worden', k='3',
  toel='Laat-Latijnse inchoatieve vorm naast `appareo`.', verw=['appareo'])
V('conparesco, conparescere', 'te voorschijn komen, verschijnen', k='3',
  toel='Klassiek *comparesco*.', verw=['conpareo'])
V('ardesco, ardescere, arsi', 'ontbranden, gaan gloeien', k='3', verw=['ardeo'])
V('aporio, aporiare, aporiavi, aporiatum', 'in verlegenheid brengen, radeloos maken',
  naam='aporio (actieve nevenvorm)', prio=-1, verw=['aporior'])
V('commoneo, commonere, commonui, commonitum', 'herinneren, vermanen', k='2', verw=['moneo'])
V('moneo, monere, monui, monitum', 'herinneren, vermanen | waarschuwen', k='2',
  verw=['commoneo'])
V('confringo, confringere, confregi, confractum', 'stukbreken, verbrijzelen', k='3',
  verw=['contero'])
V('conlido, conlidere, conlisi, conlisum', 'tegen elkaar slaan, botsen', k='3',
  toel='Klassiek *collido*.', verw=['adlido'])
V('contemno, contemnere, contempsi, contemptum', 'minachten, versmaden', k='3',
  verw=['sperno', 'contemptus'])
N('contemptus, contemptus, m.', 'minachting, geringschatting', verw=['contemno'])
V('delinquo, delinquere, deliqui, delictum', 'tekortschieten, zich misdragen | zondigen',
  k='3', verw=['delictum', 'pecco'])
V('demolio, demolire, demolivi, demolitum', 'afbreken, slechten',
  naam='demolio (actieve nevenvorm)', k='4', prio=-1, verw=['demolior'])
V('discindo, discindere, discidi, discissum', 'openscheuren, vaneenscheuren', k='3')
V('discumbo, discumbere, discubui', 'aanliggen, gaan liggen (aan tafel)', k='3',
  verw=['recumbo'])
V('disperdo, disperdere, disperdidi, disperditum', 'geheel verdelgen, te gronde richten',
  k='3', verw=['perdo'])
V('expono, exponere, exposui, expositum', 'uiteenzetten, uitleggen | blootstellen', k='3',
  verw=['pono'])
V('existo, existere, extiti', 'te voorschijn treden, ontstaan | bestaan', k='3',
  toel='In de handschriften ook *exsisto*.')
V('fallo, fallere, fefelli, falsum', 'bedriegen, misleiden | ontgaan', k='3',
  verw=['falsus'])
V('fluctuo, fluctuare, fluctuavi, fluctuatum', 'golven, deinen | wankelen',
  verw=['fluctus'])
V('fulcio, fulcire, fulsi, fultum', 'stutten, ondersteunen', k='4')
V('gigno, gignere, genui, genitum', 'voortbrengen, baren | verwekken', k='3',
  verw=['genus', 'genero'])
V('glorior, gloriari, gloriatus sum', 'roemen, zich beroemen', k='1d', verw=['gloria'])
V('gravo, gravare, gravavi, gravatum', 'zwaar maken, bezwaren', verw=['gravis'])
V('indignor, indignari, indignatus sum', 'verontwaardigd zijn, zich ergeren', k='1d',
  verw=['indignatio'])
V('infero, inferre, intuli, inlatum', 'aanbrengen, toebrengen | binnendragen', k='3',
  extra={'inlata': 'voltooid deelwoord, vrouwelijk/onzijdig mv. — aangebracht',
         'inferre': 'onbepaalde wijs — toe te brengen'}, verw=['fero'])
V('profero, proferre, protuli, prolatum', 'te voorschijn brengen, voortbrengen | uiten',
  k='3', extra={'proferri': 'onbepaalde wijs, lijdende vorm — voortgebracht te worden'},
  verw=['fero'])
V('inobaudio, inobaudire, inobaudivi, inobauditum', 'ongehoorzaam zijn, niet luisteren',
  k='4', toel='Laat-Latijnse ontkennende vorming naast `obaudio`.', verw=['obaudio'])
V('oboedio, oboedire, oboedivi, oboeditum', 'gehoorzamen, luisteren naar', k='4',
  verw=['obaudio'])
V('insanio, insanire, insanivi', 'razend zijn, waanzinnig zijn', k='4', verw=['insanus'])
V('investigo, investigare, investigavi, investigatum', 'naspeuren, uitvorsen',
  verw=['investigabilis'])
V('labor, labi, lapsus sum', 'glijden, vallen | een misstap doen', k='3d',
  naam='labor (glijden)',
  toel='Niet te verwarren met het zelfstandig naamwoord `labor` (arbeid).', verw=['lapsus'])
V('ministro, ministrare, ministravi, ministratum', 'dienen, bedienen | verschaffen',
  verw=['servio'])
V('peto, petere, petivi, petitum', 'streven naar, zoeken | vragen, verzoeken | aanvallen',
  k='3', verw=['rogo', 'quaero'])
V('persevero, perseverare, perseveravi, perseveratum', 'volharden, volhouden',
  verw=['perseverantia'])
V('praesum, praeesse, praefui', 'aan het hoofd staan, leiden', k='1',
  extra={'praees': '2e pers. ev., tegenwoordige tijd — gij staat aan het hoofd',
         'praeest': '3e pers. ev., tegenwoordige tijd', 'praesunt': '3e pers. mv.',
         'praeesse': 'onbepaalde wijs', 'praeerat': '3e pers. ev., verleden tijd'},
  verw=['sum'])
V('pugno, pugnare, pugnavi, pugnatum', 'strijden, vechten', verw=['pugna'])
V('somnio, somniare, somniavi, somniatum', 'dromen', verw=['somnium'])
V('unguo, unguere, unxi, unctum', 'zalven, insmeren', k='3', verw=['unguentum', 'unctus'])
V('percontinuo, percontinuare, percontinuavi, percontinuatum', 'aaneengesloten voortzetten',
  naam='percontinuo (nevenvorm)', prio=-3,
  extra={'percontinuit': '3e pers. ev., perfectum — hij hield onafgebroken vast'})


# ===========================================================================
# 13. Eigennamen
# ===========================================================================

def PN(kop, bet, vormen, toel=None, verw=None):
    """Eigennaam. `vormen` is een lijst (alle vormen onverbuigbaar) of een dict."""
    if isinstance(vormen, (list, tuple)):
        vormen = {v: 'onverbuigbare naam' for v in vormen}
    _voeg(kop, 'eigennaam', kop, bet, vormen, toel, verw, 0)


PN('Ezra', 'Ezra, de schrijver en ziener van dit boek',
   {'ezra': 'nominatief', 'ezras': 'nominatief (Griekse vorm)',
    'ezrae': 'genitief/datief — van of aan Ezra', 'ezram': 'accusatief'},
   toel='In 4 Ezra draagt de ziener ook de naam Salathiel (3:1).')
PN('Salathihel', 'Salathiël, de tweede naam van de ziener', ['salathihel'],
   toel='4 Ezra 3:1: "ego Salathihel qui et Ezras" — ik, Salathiël, die ook Ezra heet.')
PN('Urihel', 'Uriël, de engel die Ezra onderwijst', ['urihel'],
   toel='De gesprekspartner van Ezra in de eerste visioenen (4:1).')
PN('Hieremihel', 'Jeremiël, de aartsengel', ['hieremihel'],
   toel='De engel die in 4 Ezra 4:36 de zielen antwoord geeft.')
PN('Hierusalem', 'Jeruzalem', ['hierusalem'],
   toel='Onverbuigbare Hebreeuwse naam; in 4 Ezra staat het verwoeste Jeruzalem tegenover de '
        'stad die God zal tonen.')
PN('Sion', 'Sion, de tempelberg en de stad', ['sion'],
   toel='De rouwende vrouw van het vierde visioen blijkt Sion zelf te zijn.')
PN('Babylon', 'Babylon, de stad van de ballingschap',
   {'babylon': 'nominatief', 'babylonis': 'genitief', 'babylone': 'ablatief',
    'babylonem': 'accusatief', 'babylonia': 'Babylonië, het land'},
   toel='4 Ezra speelt zogenaamd in Babylon, dertig jaar na de verwoesting; achter Babylon '
        'gaat het Rome van na het jaar 70 schuil.')
PN('Aegyptus', 'Egypte',
   {'aegyptus': 'nominatief ev.', 'aegypti': 'genitief ev. — van Egypte',
    'aegypto': 'datief/ablatief ev.', 'aegyptum': 'accusatief ev.',
    'aegypte': 'vocatief ev. — o Egypte',
    'aegyptiis': 'datief/ablatief mv. — aan de Egyptenaren',
    'agyptiis': 'datief/ablatief mv. (spelling in de handschriften)'})
PN('Adam', 'Adam, de eerste mens',
   {'adam': 'onverbuigbaar', 'adae': 'genitief/datief — van of aan Adam'},
   toel='In 4 Ezra de bron van het "boze hart" dat heel het nageslacht meedraagt (3:21).')
PN('Abraham', 'Abraham, de aartsvader', ['abraham'])
PN('Isaac', 'Izak, de zoon van Abraham', ['isaac'])
PN('Iacob', 'Jakob, de stamvader van Israël', ['iacob'])
PN('Esau', 'Ezau, de broer van Jakob', ['esau'],
   toel='4 Ezra 6:8-10 gebruikt Jakob en Ezau als beeld voor de twee wereldtijdperken.')
PN('Israhel', 'Israël, het volk en de aartsvader', ['israhel'],
   toel='In de handschriften ook *Israel*.')
PN('Iuda', 'Juda, de stam en het rijk', ['iuda'])
PN('Levi', 'Levi, de priesterstam',
   {'levi': 'onverbuigbaar — Levi', 'levitae': 'nominatief mv. — de levieten'})
PN('Moyses', 'Mozes',
   {'moyses': 'nominatief', 'moysi': 'genitief/datief — van of aan Mozes',
    'moysen': 'accusatief (Griekse vorm)'},
   toel='4 Ezra 14 vergelijkt Ezra uitdrukkelijk met Mozes bij de braamstruik.')
PN('Aaron', 'Aäron, de eerste hogepriester', ['aaron'])
PN('David', 'David, de koning', ['david'])
PN('Salomon', 'Salomo, de zoon van David', ['salomon'])
PN('Noe', 'Noach, de man van de ark', ['noe'])
PN('Enoch', 'Henoch, die met God wandelde', ['enoch'])
PN('Danihel', 'Daniël, de profeet',
   {'danihel': 'nominatief', 'danihelo': 'datief/ablatief — aan Daniël'})
PN('Iesus', 'Jezus', ['iesus'])
PN('Esaias', 'Jesaja, de profeet',
   {'esaias': 'nominatief', 'esaiam': 'accusatief', 'esaiae': 'genitief/datief'})
PN('Hieremias', 'Jeremia, de profeet',
   {'hieremias': 'nominatief', 'hieremiam': 'accusatief', 'hieremiae': 'genitief/datief'})
PN('Osee', 'Hosea, de profeet', ['osee'])
PN('Amos', 'Amos, de profeet', ['amos'])
PN('Michaeas', 'Micha, de profeet', {'michae': 'genitief/datief — van Micha'})
PN('Iohel', 'Joël, de profeet', {'iohelis': 'genitief — van Joël'})
PN('Abdias', 'Obadja, de profeet', {'abdiae': 'genitief/datief — van Obadja'})
PN('Ionas', 'Jona, de profeet', {'ionae': 'genitief/datief — van Jona'})
PN('Naum', 'Nahum, de profeet', ['naum'])
PN('Abacuc', 'Habakuk, de profeet', ['abacuc'])
PN('Sofonias', 'Sefanja, de profeet', {'sofoniae': 'genitief/datief — van Sefanja'})
PN('Aggeus', 'Haggai, de profeet', {'aggei': 'genitief — van Haggai'})
PN('Zacharias', 'Zacharia, de profeet', {'zacchariae': 'genitief/datief — van Zacharia'})
PN('Malachias', 'Maleachi, de profeet', {'malachiae': 'genitief/datief — van Maleachi'})
PN('Iosias', 'Josia, de koning', {'iosiae': 'genitief/datief — van Josia'})
PN('Ozias', 'Uzzia, in de stamboom van Ezra', {'oziae': 'genitief/datief'})
PN('Sarei', 'Sarei, de vader van Ezra in de geslachtslijst', ['sarei'],
   toel='Een van de negentien namen in de stamboom waarmee 4 Ezra opent (1:1-3).')
PN('Azarei', 'Azarei, in de geslachtslijst van Ezra', ['azarei'])
PN('Helchias', 'Helkia, in de geslachtslijst van Ezra',
   {'helchiae': 'genitief/datief'})
PN('Salame', 'Salame (Sallum), in de geslachtslijst van Ezra', ['salame'])
PN('Sadoch', 'Sadok, in de geslachtslijst van Ezra', ['sadoch'])
PN('Acitob', 'Achitob, in de geslachtslijst van Ezra', ['acitob'])
PN('Achias', 'Achia, in de geslachtslijst van Ezra', {'achiae': 'genitief/datief'})
PN('Finees', 'Pinehas, in de geslachtslijst van Ezra', ['finees'])
PN('Heli', 'Eli, in de geslachtslijst van Ezra', ['heli'])
PN('Ameria', 'Ameria, in de geslachtslijst van Ezra', {'ameriae': 'genitief/datief'})
PN('Aziei', 'Aziei, in de geslachtslijst van Ezra', ['aziei'])
PN('Marimoth', 'Marimoth, in de geslachtslijst van Ezra', ['marimoth'])
PN('Arna', 'Arna, in de geslachtslijst van Ezra', ['arna'])
PN('Borith', 'Borith, in de geslachtslijst van Ezra', ['borith'])
PN('Abissei', 'Abissei, in de geslachtslijst van Ezra', ['abissei'])
PN('Eleazar', 'Eleazar, in de geslachtslijst van Ezra', ['eleazar'])
PN('Asihel', 'Asiël, een van de vijf schrijvers', ['asihel'],
   toel='In 4 Ezra 14:24 krijgt Ezra vijf snelle schrijvers mee: Sarea, Dabria, Selemia, '
        'Ethan en Asiël.')
PN('Sarea', 'Sarea, een van de vijf schrijvers', {'saream': 'accusatief'})
PN('Dabria', 'Dabria, een van de vijf schrijvers', {'dabriam': 'accusatief'})
PN('Selemias', 'Selemia, een van de vijf schrijvers', {'selemiam': 'accusatief'})
PN('Ethanus', 'Ethan, een van de vijf schrijvers', {'ethanum': 'accusatief'})
PN('Phalthihel', 'Phaltiël, de leider van het volk', ['phalthiheldux'],
   toel='In de handschriften aaneengeschreven met `dux` (leider): 4 Ezra 5:16.')
PN('Salmanassar', 'Salmanassar, de koning van Assyrië', ['salmanassar'],
   toel='De koning die de tien stammen wegvoerde (4 Ezra 13:40).')
PN('Artaxerses', 'Artaxerxes, de Perzische koning', {'artaxersis': 'genitief'})
PN('Pharao', 'Farao, de koning van Egypte', {'pharaonem': 'accusatief'})
PN('Assur', 'Assur, Assyrië', ['assur'])
PN('Assyrii', 'de Assyriërs', {'assyriorum': 'genitief mv. — van de Assyriërs'})
PN('Medi', 'de Meden', {'medorum': 'genitief mv. — van de Meden'})
PN('Persae', 'de Perzen', {'persarum': 'genitief mv. — van de Perzen'})
PN('Arabes', 'de Arabieren', {'arabum': 'genitief mv. — van de Arabieren'})
PN('Chananei', 'de Kanaänieten', {'chananeos': 'accusatief mv.'})
PN('Ferezei', 'de Ferezieten', {'ferezeos': 'accusatief mv.'})
PN('Philisthei', 'de Filistijnen', {'philistheos': 'accusatief mv.',
                                    'philistheosa': 'accusatief mv. (aaneengeschreven met a)'})
PN('Sodoma', 'Sodom', {'sodomae': 'genitief/datief — van Sodom',
                       'sodomitum': 'genitief mv. — van de Sodomieten'})
PN('Gomorra', 'Gomorra', {'gomorrae': 'genitief/datief — van Gomorra'})
PN('Tyrus', 'Tyrus, de havenstad', {'tyri': 'genitief — van Tyrus'})
PN('Sidon', 'Sidon, de havenstad', {'sidonis': 'genitief — van Sidon'})
PN('Asia', 'Asia, de Romeinse provincie', ['asia'])
PN('Syria', 'Syrië', ['syria'])
PN('Libanus', 'de Libanon', {'libanus': 'nominatief', 'libano': 'datief/ablatief'})
PN('Horeb', 'Horeb, de berg van de openbaring', ['horeb'])
PN('Sina', 'Sinaï, de berg van de wet', ['sina'])
PN('Eufrates', 'de Eufraat', {'eufraten': 'accusatief (Griekse vorm)'})
PN('Arzar', 'Arzareth, het land van de tien stammen', ['arzar'],
   toel='4 Ezra 13:45: het verre land waarheen de tien stammen trokken; de naam betekent in '
        'het Hebreeuws "ander land".')
