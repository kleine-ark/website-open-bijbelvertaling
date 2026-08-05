#!/usr/bin/env python3
"""Gereedschap om de citaatopmaak van een hoofdstuk recht te zetten.

De conventie, zoals die in Genesis is aangehouden:

  - De aankondiging blijft búiten de span:  En hij zei: <span…>de woorden</span>
  - god-speaks    voor God, de HEERE, JAHWEH
  - direct-speech voor een mens
  - Een citaat binnen een citaat is een span binnen een span; de CSS geeft die
    het gele accent. Welke klasse de binnenste krijgt maakt voor de weergave
    niet uit — de nesting bepaalt het accent.
  - Een vers dat een rede voortzet zonder eigen aankondiging krijgt één span
    over het hele vers.

Wat er misging voordat dit bestond: hele verzen vertelling zaten in een
spraak-span, redes van mensen stonden als Godsspraak gemarkeerd, en op andere
plaatsen ontbrak de opmaak juist. Dat is niet met zoeken-en-vervangen te
verhelpen, want of iets vertelling of rede is volgt uit de zin, niet uit een
patroon. Vandaar dit gereedschap: het neemt de losse beslissingen aan, en
bewaakt alleen dat het resultaat welgevormd is en dat er geen tekst zoekraakt.

Gebruik vanuit een ander script:

    from citaatopmaak import Hoofdstuk
    h = Hoofdstuk("exodus", 8)
    h.vertelling(6, 7, 12)              # span eraf, het is vertelling
    h.rede(11, "mens")                  # heel het vers is rede
    h.na(8, "en zei:", "mens")          # aankondiging buiten, rest erin
    h.bewaar()
"""
import json
import os
import re

WORTEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KLASSE = {"god": "god-speaks", "mens": "direct-speech"}
SPAN = re.compile(r'<span class="(?:god-speaks|direct-speech|angel-speaks|devil-speaks)"><i>(.*?)</i></span>', re.S)


def kaal(html):
    """Alleen de leesbare tekst — om te toetsen dat er niets zoekraakt."""
    zonder = re.sub(r'<sup[^>]*>.*?</sup>', '', html)
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', zonder)).strip()


class Hoofdstuk:
    def __init__(self, boek, nummer):
        self.pad = os.path.join(WORTEL, "data", boek, f"{nummer}.json")
        ruw = open(self.pad, encoding="utf-8").read()
        m = re.search(r'\n( +)"', ruw)
        self.inspring = len(m.group(1)) if m else 2
        self.data = json.loads(ruw)
        self.vers = {v["number"]: v for v in self.data["verses"]}
        self.voor = {n: kaal(v["text2026_html"]) for n, v in self.vers.items()}
        self.gewijzigd = []

    # -- bouwstenen ---------------------------------------------------------

    def _zet(self, n, html):
        if self.vers[n]["text2026_html"] != html:
            self.vers[n]["text2026_html"] = html
            self.gewijzigd.append(n)

    def _ontdaan(self, n):
        """Het vers zonder de buitenste spraak-span, inhoud ongemoeid."""
        h = self.vers[n]["text2026_html"]
        m = re.fullmatch(r'<span class="[a-z-]+"><i>(.*)</i></span>', h, re.S)
        return m.group(1) if m else h

    # -- beslissingen -------------------------------------------------------

    def vertelling(self, *nummers):
        """Deze verzen zijn vertelling: geen spraak-span omheen."""
        for n in nummers:
            self._zet(n, self._ontdaan(n))

    def rede(self, n, spreker):
        """Heel het vers is rede — een vers dat de vorige voortzet."""
        self._zet(n, f'<span class="{KLASSE[spreker]}"><i>{self._ontdaan(n)}</i></span>')

    def na(self, n, aankondiging, spreker, tot=None):
        """Alles ná de aankondiging is rede; de aankondiging blijft erbuiten.

        `tot` begrenst de rede als het vers daarna weer vertelling wordt."""
        h = self._ontdaan(n)
        i = h.find(aankondiging)
        if i < 0:
            raise ValueError(f'{self.pad} vers {n}: "{aankondiging}" niet gevonden')
        kop = h[:i + len(aankondiging)]
        rest = h[i + len(aankondiging):].lstrip()
        staart = ""
        if tot is not None:
            j = rest.find(tot)
            if j < 0:
                raise ValueError(f'{self.pad} vers {n}: einde "{tot}" niet gevonden')
            staart = rest[j + len(tot):].lstrip()
            # Geen spatie vóór leesteken: het citaat eindigt lang niet altijd op
            # een zinseinde, en dan hoort de komma of puntkomma erachter direct
            # tegen de span aan.
            staart = ("" if staart[:1] in ",;:.!?" else " ") + staart
            rest = rest[:j + len(tot)]
        self._zet(n, f'{kop} <span class="{KLASSE[spreker]}"><i>{rest}</i></span>{staart}')

    def nest(self, n, aankondiging, spreker, tot=None):
        """Een citaat bínnen een lopende rede, zonder die rede af te breken.

        Aäron vertelt Mozes wat het volk zei; die aangehaalde woorden krijgen
        een span binnen de zijne. De CSS geeft de binnenste het gele accent."""
        h = self.vers[n]["text2026_html"]
        i = h.find(aankondiging)
        if i < 0:
            raise ValueError(f'{self.pad} vers {n}: "{aankondiging}" niet gevonden')
        start = i + len(aankondiging)
        rest = h[start:]
        einde = len(rest)
        if tot is not None:
            j = rest.find(tot)
            if j < 0:
                raise ValueError(f'{self.pad} vers {n}: einde "{tot}" niet gevonden')
            einde = j + len(tot)
        else:
            # tot het einde van de omhullende rede
            k = rest.rfind('</i></span>')
            if k >= 0:
                einde = k
        binnen = rest[:einde].strip()
        self._zet(n, f'{h[:start]} <span class="{KLASSE[spreker]}"><i>{binnen}</i></span>{rest[einde:]}')

    def klasse(self, spreker, *nummers):
        """Alleen de klasse van de buitenste span wisselen."""
        for n in nummers:
            h = self.vers[n]["text2026_html"]
            self._zet(n, re.sub(r'^<span class="[a-z-]+">', f'<span class="{KLASSE[spreker]}">', h))

    # -- afsluiten ----------------------------------------------------------

    def bewaar(self):
        for n, v in self.vers.items():
            if kaal(v["text2026_html"]) != self.voor[n]:
                raise AssertionError(f"vers {n}: de tekst is veranderd, alleen opmaak mocht wijzigen\n"
                                     f"  was: {self.voor[n][:110]}\n"
                                     f"  nu : {kaal(v['text2026_html'])[:110]}")
            h = v["text2026_html"]
            if h.count('<span') != h.count('</span>') or h.count('<i>') != h.count('</i>'):
                raise AssertionError(f"vers {n}: ongebalanceerde opmaak")
        open(self.pad, "w", encoding="utf-8", newline="").write(
            json.dumps(self.data, ensure_ascii=False, indent=self.inspring) + "\n")
        return sorted(set(self.gewijzigd))
