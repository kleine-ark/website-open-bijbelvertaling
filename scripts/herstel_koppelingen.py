#!/usr/bin/env python3
"""Haalt samengeklonterde woorddiff-blokken weer uit elkaar.

Staan twee wijzigingen naast elkaar, dan voegt difflib.SequenceMatcher ze samen
tot een blok, omdat er geen gelijk woord tussen staat om op te splitsen. Dat
blok draagt daarna nog maar een principe-id, en het werk van het andere
principe verdwijnt stilletjes uit de herkomst:

    voor  ('der', 'van de', N2) en ('landschappen', 'gewesten', V1535)
    na    ('der landschappen', 'van de gewesten', V1535)

`sweep_principe.py` meldt dit met "koppeling ... is vervallen door
hergroepering", maar lost het niet op. Dit script wel.

Werkwijze: de vorige versie van het bestand komt uit git, want daarin staan de
koppelingen nog goed. Voor elk paar dat verdwenen is wordt geprobeerd het van
de voorkant of de achterkant van het nieuwe blok af te pellen. Lukt dat niet,
dan wordt het gemeld en niet geraden -- een half afgepeld blok is erger dan een
blok dat de melding houdt.

Gebruik:
    python scripts/herstel_koppelingen.py --proef
    python scripts/herstel_koppelingen.py
"""
import argparse
import json
import os
import re
import subprocess
import sys

WORTEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(WORTEL, "scripts"))
from sweep_principe import lees, schrijf, sleutel  # noqa: E402


def uit_git(pad, revisie="HEAD"):
    """De inhoud van een bestand zoals het in git staat, of None."""
    rel = os.path.relpath(pad, WORTEL).replace(os.sep, "/")
    r = subprocess.run(["git", "show", f"{revisie}:{rel}"],
                       cwd=WORTEL, capture_output=True)
    if r.returncode:
        return None
    try:
        return json.loads(r.stdout.decode("utf-8"))
    except Exception:
        return None


def peel(blok, paar):
    """Splitst een blok in twee, als het paar er aan de voor- of achterkant af kan.

    Geeft een lijst van (oud, nieuw, principe) terug, of None.
    """
    oud, nieuw, pid = blok["old"], blok["new"], blok.get("principe")
    o, n, p = paar
    if not o or not n:
        return None
    if oud.startswith(o + " ") and nieuw.startswith(n + " "):
        return [(o, n, p), (oud[len(o) + 1:], nieuw[len(n) + 1:], pid)]
    if oud.endswith(" " + o) and nieuw.endswith(" " + n):
        return [(oud[:-len(o) - 1], nieuw[:-len(n) - 1], pid), (o, n, p)]
    return None


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--proef", action="store_true")
    p.add_argument("--revisie", default="HEAD", help="waarmee vergelijken")
    a = p.parse_args()

    r = subprocess.run(["git", "diff", "--name-only", a.revisie, "--", "data"],
                       cwd=WORTEL, capture_output=True, text=True)
    paden = [os.path.join(WORTEL, x) for x in r.stdout.split("\n")
             if re.fullmatch(r"data/[a-z0-9]+/\d+\.json", x.strip())]

    hersteld = niet_gelukt = 0
    for pad in paden:
        oud_data = uit_git(pad, a.revisie)
        if not isinstance(oud_data, dict) or "verses" not in oud_data:
            continue
        try:
            d, vorm = lees(pad)
        except Exception:
            continue
        was = {v.get("number"): v for v in oud_data["verses"] if isinstance(v, dict)}
        gewijzigd = False
        for v in d["verses"]:
            if not isinstance(v, dict):
                continue
            oud_v = was.get(v.get("number"))
            if not oud_v:
                continue
            nu = v.get("phraseDiff") or []
            toen = oud_v.get("phraseDiff") or []
            heeft = {sleutel((e["old"], e["new"])) for e in nu}
            # koppelingen die bestonden en nu weg zijn
            kwijt = [(e["old"], e["new"], e.get("principe")) for e in toen
                     if e.get("principe") and sleutel((e["old"], e["new"])) not in heeft]
            if not kwijt:
                continue
            merk = f"{os.path.basename(os.path.dirname(pad))} " \
                   f"{d.get('number')}:{v.get('number')}"
            for paar in kwijt:
                gelukt = False
                for i, blok in enumerate(nu):
                    delen = peel(blok, paar)
                    if not delen:
                        continue
                    nu[i:i + 1] = [{"old": o, "new": n, "principe": pr} for o, n, pr in delen]
                    print(f"{merk}: {paar[2]} weer los uit "
                          f"{blok['old'][:50]!r} -> {blok['new'][:50]!r}")
                    hersteld += 1
                    gelukt = True
                    gewijzigd = True
                    break
                if not gelukt:
                    print(f"!! {merk}: {paar[2]} bij {paar[0][:40]!r} niet af te pellen")
                    niet_gelukt += 1
            v["phraseDiff"] = nu
        if gewijzigd and not a.proef:
            schrijf(pad, d, vorm)

    print()
    print(f"{'ZOU HERSTELLEN' if a.proef else 'HERSTELD'}: {hersteld} koppelingen")
    if niet_gelukt:
        print(f"met de hand na te lopen: {niet_gelukt}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
