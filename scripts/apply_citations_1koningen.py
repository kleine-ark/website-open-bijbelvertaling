#!/usr/bin/env python3
"""Herstel de citaatopmaak van de nagekeken verzen in 1 Koningen.

De bereikdefinities gebruiken de zichtbare tekst. Bestaande nootmarkeringen
blijven daardoor behouden en alleen de spraakmarkering wordt opnieuw gezet.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from citaatopmaak import kaal
from sweep_principe import lees, schrijf


ROOT = Path(__file__).resolve().parents[1]
OPEN = re.compile(r'<span class="(?:god-speaks|direct-speech|angel-speaks|devil-speaks)"><i>')


RANGES = {
    (11, 2): [("god", "U zult tot hen niet ingaan", "zij zouden zeker uw hart achter hun goden neigen;")],
    (11, 13): [("god", "Maar Ik zal", "dat Ik gekozen heb.")],
    (12, 10): [("mens", "Zo zult u zeggen", "dan het middel van mijn vader.")],
    (12, 16): [("mens", "Wat deel hebben wij", "Voorzie nu uw huis, o David!")],
    (12, 18): [],
    (12, 24): [("god", "U zult niet optrekken", "want deze zaak is van Mij gebeurd.")],
    (12, 27): [("mens", "Zo dit volk", "de koning van Juda, terugkeren.")],
    (13, 2): [
        ("mens", "Altaar, altaar, zo zegt JAHWEH:", "Altaar, altaar, zo zegt JAHWEH:"),
        ("god", "Zie, een zoon", "men zal mensenbeenderen op u verbranden."),
    ],
    (13, 3): [("mens", "Dit is dat wonderteken", "afgestort worden.")],
    (13, 6): [("mens", "Aanbid toch", "dat mijn hand weer tot mij kome!")],
    (13, 9): [("god", "U zult geen brood eten", "die u gegaan bent.")],
    (13, 14): [
        ("mens", "Bent u de man van God", "uit Juda gekomen bent?"),
        ("mens", "Ik ben het.", "Ik ben het."),
    ],
    (13, 17): [("god", "U zult daar noch brood eten", "waarlangs u gegaan bent.")],
    (14, 6): [("mens", "Kom in, u huisvrouw", "met een harde boodschap.")],
    (14, 12): [("god", "U dan maak u op", "zo zal het kind sterven.")],
    (14, 13): [("god", "En geheel Israël", "gevonden is.")],
    (14, 14): [("god", "Maar JAHWEH", "wat zal het ook nu zijn?")],
    (14, 15): [("god", "JAHWEH zal ook Israël", "JAHWEH tot toorn verwekkende.")],
    (14, 16): [("god", "En Hij zal Israël", "Israël heeft doen zondigen.")],
    (16, 2): [("god", "Daarom, dat Ik", "door hun zonden;")],
    (16, 16): [("mens", "Zimri heeft een verbintenis gemaakt", "heeft ook de koning verslagen;")],
    (18, 1): [("god", "Ga heen, vertoon u", "op de aardbodem.")],
    (18, 21): [("mens", "Hoe lang hinkt u", "volgt hem na!")],
    (18, 40): [("mens", "Grijp de profeten", "dat niemand van hen ontkome.")],
    (18, 43): [
        ("mens", "Ga nu op", "zie uit naar de zee."),
        ("mens", "Er is niets.", "Er is niets."),
        ("mens", "Ga weer heen, zevenmaal.", "Ga weer heen, zevenmaal."),
    ],
    (18, 44): [
        ("mens", "Zie, een kleine wolk", "gaat op van de zee."),
        ("mens", "Ga op, zeg tot Achab", "dat u de regen niet ophoude."),
    ],
    (19, 11): [("god", "Ga uit, en sta", "voor het aangezicht van JAHWEH.")],
    (20, 22): [("mens", "Ga heen, sterk u", "tegen u optrekken.")],
    (20, 28): [("god", "Omdat de Syriërs", "dat Ik JAHWEH ben.")],
    (20, 37): [("mens", "Sla mij toch.", "Sla mij toch.")],
    (20, 40): [("mens", "Zo is uw oordeel", "u hebt zelf het geveld.")],
    (21, 2): [("mens", "Geef mij uw wijngaard", "de waarde daarvan geven.")],
    (21, 20): [
        ("mens", "Hebt u mij gevonden", "o, mijn vijand?"),
        ("mens", "Ik heb u gevonden", "in de ogen van JAHWEH."),
    ],
    (22, 3): [("mens", "Weet u, dat Ramoth", "van de koning van Syrië.")],
    (22, 15): [
        ("mens", "Micha, zullen wij", "of zullen wij het nalaten?"),
        ("mens", "Trek op", "in de hand van de koning geven."),
    ],
    (22, 20): [("god", "Wie zal Achab", "te Ramoth in Gilead?")],
    (22, 22): [
        ("god", "Waarmee?", "Waarmee?"),
        ("mens", "Ik zal uitgaan", "van al zijn profeten."),
        ("god", "U zult overreden", "ga uit en doe zo."),
    ],
}


def zonder_spraak(html: str) -> str:
    aantal = len(OPEN.findall(html))
    html = OPEN.sub("", html)
    for _ in range(aantal):
        html = html.replace("</i></span>", "", 1)
    return html


def zichtbare_indexen(html: str):
    """Geef zichtbare tekst plus de bijbehorende posities in de HTML."""
    tekst, posities = [], []
    i = 0
    while i < len(html):
        if html.startswith("<sup", i):
            einde = html.find("</sup>", i)
            if einde < 0:
                raise ValueError("onafgesloten sup-markering")
            i = einde + len("</sup>")
        elif html[i] == "<":
            einde = html.find(">", i)
            if einde < 0:
                raise ValueError("onafgesloten HTML-markering")
            i = einde + 1
        else:
            tekst.append(html[i])
            posities.append(i)
            i += 1
    return "".join(tekst), posities


def markeer(html: str, bereiken):
    basis = zonder_spraak(html)
    zichtbaar, posities = zichtbare_indexen(basis)
    invoegingen = []
    zoek_vanaf = 0
    for spreker, begin, einde in bereiken:
        start = zichtbaar.find(begin, zoek_vanaf)
        if start < 0:
            raise ValueError(f"begin niet gevonden: {begin!r}")
        stop_begin = zichtbaar.find(einde, start)
        if stop_begin < 0:
            raise ValueError(f"einde niet gevonden: {einde!r}")
        stop = stop_begin + len(einde)
        klasse = "god-speaks" if spreker == "god" else "direct-speech"
        invoegingen.append((posities[start], posities[stop - 1] + 1, klasse))
        zoek_vanaf = stop

    resultaat = basis
    for start, stop, klasse in sorted(invoegingen, reverse=True):
        resultaat = (
            resultaat[:stop] + "</i></span>" + resultaat[stop:]
        )
        resultaat = (
            resultaat[:start] + f'<span class="{klasse}"><i>' + resultaat[start:]
        )
    return resultaat


def main():
    per_hoofdstuk = {}
    for (hoofdstuk, vers), bereiken in RANGES.items():
        per_hoofdstuk.setdefault(hoofdstuk, {})[vers] = bereiken

    geraakt = 0
    for hoofdstuk, opdrachten in per_hoofdstuk.items():
        pad = ROOT / "data" / "1koningen" / f"{hoofdstuk}.json"
        data, vorm = lees(str(pad))
        for vers in data["verses"]:
            if vers["number"] not in opdrachten:
                continue
            oud = vers["text2026_html"]
            nieuw = markeer(oud, opdrachten[vers["number"]])
            if kaal(oud) != kaal(nieuw):
                raise AssertionError(f"1 Koningen {hoofdstuk}:{vers['number']}: tekst gewijzigd")
            if nieuw != oud:
                vers["text2026_html"] = nieuw
                geraakt += 1
        schrijf(str(pad), data, vorm)
    print(f"Citaatopmaak in {geraakt} verzen van 1 Koningen hersteld.")


if __name__ == "__main__":
    main()
