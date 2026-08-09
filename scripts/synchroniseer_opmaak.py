#!/usr/bin/env python3
"""Trekt text2026_html bij waar die is achtergebleven op text2026.

Waarom dit nodig is: een sweep vervangt een woord in beide velden met hetzelfde
patroon. Staat er een nootmarkering middenin het zinsdeel — "ten<sup>21</sup>
zondoffer" — dan grijpt de regex wel op de platte tekst en niet op de opmaak.
De sweep meldt niets, maar vanaf dat moment leest de leestekst iets anders dan
wat de bezoeker op het scherm ziet. De opmaak is wat de site toont, dus dat is
de ernstige kant.

De platte tekst is hier leidend: die is bijgewerkt, de opmaak niet.

Werkwijze: de woorden in de opmaak worden opgezocht mét hun plaats in de
tekenreeks, waarbij alles binnen een tag en binnen een <sup>-blok wordt
overgeslagen. Daarna een woorddiff tegen text2026, en de wijzigingen worden van
achter naar voren in de opmaak aangebracht, zodat de posities blijven kloppen.
Tags, spans en nootmarkeringen blijven staan waar ze stonden.

Verzen waarvan het enige verschil een typografisch aanhalingsteken is
(&ldquo; en &rdquo;) blijven met rust: die staan bewust alleen in de opmaak.

Gebruik:
    python scripts/synchroniseer_opmaak.py --droog
    python scripts/synchroniseer_opmaak.py
"""
import argparse
import difflib
import glob
import json
import os
import re
import sys

WORTEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(WORTEL, "scripts"))
from sweep_principe import lees, schrijf, kaal  # noqa: E402

# Losse tag, of een heel <sup>...</sup>-blok in één keer: de inhoud van een
# nootmarkering is geen leestekst en mag niet als woord meetellen.
NIET_TEKST = re.compile(r"<sup[^>]*>.*?</sup>|<[^>]+>", re.S)

# Overal in het woord, niet alleen aan de rand: het sluitteken staat vaak vóór
# de leesteken-staart, zoals in plaats&rdquo;; — dus niet aan het eind.
ALLEEN_AANHALING = re.compile(r"&ldquo;|&rdquo;")


def woorden_met_plaats(html):
    """Woorden buiten tags en nootmarkeringen, met hun plaats in de opmaak.

    Niet met een woordpatroon op de ruwe opmaak: "ten<sup>21</sup> zondoffer"
    levert dan het token "ten<sup" op, dat over een tag heen valt en wegvalt.
    Daarom eerst de platte tekst opbouwen mét voor elk teken de plaats waar het
    in de opmaak stond, en daarna pas in woorden knippen.
    """
    plat, terug = [], []
    i, n = 0, len(html)
    while i < n:
        m = NIET_TEKST.match(html, i)
        if m:
            i = m.end()
            continue
        plat.append(html[i])
        terug.append(i)
        i += 1

    uit = []
    for m in re.finditer(r"\S+", "".join(plat)):
        uit.append((m.group(0), terug[m.start()], terug[m.end() - 1] + 1))
    return uit


def alleen_aanhalingsverschil(a, b):
    """Verschillen a en b alleen in typografische aanhalingstekens?"""
    return ALLEEN_AANHALING.sub("", a) == ALLEEN_AANHALING.sub("", b)


def bijtrekken(html, tekst):
    """Geeft de bijgewerkte opmaak terug, of None als er niets te doen valt."""
    plaatsen = woorden_met_plaats(html)
    uit_html = [w for w, _, _ in plaatsen]
    uit_tekst = tekst.split()
    if uit_html == uit_tekst:
        return None

    opdrachten = []
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, uit_html, uit_tekst).get_opcodes():
        if tag == "equal":
            continue
        oud = " ".join(uit_html[i1:i2])
        nieuw = " ".join(uit_tekst[j1:j2])
        if alleen_aanhalingsverschil(oud, nieuw):
            continue
        if i1 < i2:
            start, eind = plaatsen[i1][1], plaatsen[i2 - 1][2]
        else:
            # invoeging: achter het vorige woord, of vooraan
            start = eind = plaatsen[i1 - 1][2] if i1 else 0
            nieuw = " " + nieuw
        opdrachten.append((start, eind, nieuw))

    if not opdrachten:
        return None
    for start, eind, nieuw in sorted(opdrachten, reverse=True):
        html = html[:start] + nieuw + html[eind:]
    return re.sub(r"  +", " ", html)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--droog", action="store_true")
    p.add_argument("--boeken", help="kommalijst")
    a = p.parse_args()
    boeken = set(x.strip().lower() for x in a.boeken.split(",")) if a.boeken else None

    geraakt = 0
    mislukt = []
    overgeslagen = 0
    for pad in sorted(glob.glob(os.path.join(WORTEL, "data", "*", "*.json"))):
        boek = os.path.basename(os.path.dirname(pad))
        if boeken and boek not in boeken:
            continue
        try:
            d, vorm = lees(pad)
        except Exception:
            continue
        if not isinstance(d, dict) or "verses" not in d:
            continue
        hs = d.get("number")
        gewijzigd = False
        rij = d["verses"]
        rij = rij if isinstance(rij, list) else list(rij.values())
        for v in rij:
            if not isinstance(v, dict) or not v.get("text2026_html"):
                continue
            tekst, html = kaal(v["text2026"]), kaal(v["text2026_html"])
            if tekst == html:
                continue
            merk = f"{boek} {hs}:{v.get('number')}"
            nieuw = bijtrekken(v["text2026_html"], v["text2026"])
            if nieuw is None:
                overgeslagen += 1
                continue
            if kaal(nieuw) != kaal(v["text2026"]):
                mislukt.append(merk)
                continue
            if nieuw.count("<span") != nieuw.count("</span>") or \
               nieuw.count("<i>") != nieuw.count("</i>"):
                mislukt.append(merk + " (ongebalanceerd)")
                continue
            print(f"{merk}\n   {nieuw[:130]}")
            geraakt += 1
            if not a.droog:
                v["text2026_html"] = nieuw
                gewijzigd = True
        if gewijzigd:
            schrijf(pad, d, vorm)

    print()
    print(f"{'ZOU BIJTREKKEN' if a.droog else 'BIJGETROKKEN'}: {geraakt} verzen")
    if overgeslagen:
        print(f"met rust gelaten (alleen aanhalingstekens): {overgeslagen}")
    if mislukt:
        print(f"NIET GELUKT, met de hand na te lopen: {len(mislukt)}")
        for m in mislukt:
            print(f"  {m}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
