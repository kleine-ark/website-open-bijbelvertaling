#!/usr/bin/env python3
"""Werklijst van grondwoorden in kanttekeningen die niet klikbaar worden.

js/noot-grondwoorden.js maakt een Hebreeuws of Grieks woord in een
kanttekening klikbaar als dezelfde vorm in de grondtekst van het vers staat,
met een eenduidig Strongsnummer. Dit script telt met dezelfde regels en zet de
rest op data/grondwoorden-noten-werklijst.json:

  - deels_in_vers     de noot geeft een andere vorm van een woord dat wel in het
                      vers staat (bijvoorbeeld het lemma raqa bij raqia)
  - dubbelzinnig      de vorm staat in het vers bij verschillende nummers
  - niet_in_vers      het woord komt in de grondtekst van dit vers niet voor

Die gevallen vragen een beslissing per noot en horen bij het herzien van de
kanttekeningen, niet bij een automatische koppeling.

De normalisatie moet gelijk blijven aan normaliseer() in js/noot-grondwoorden.js.

Gebruik:
    python scripts/grondwoorden_in_noten.py              alleen tellen
    python scripts/grondwoorden_in_noten.py --schrijf    werklijst opslaan
"""
import argparse
import json
import os
import re
import sys
import unicodedata
from collections import Counter

WORTEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

HEBREEUWS = re.compile(r"[א-תװ-ײ][֑-ׇא-תװ-״]*")
GRIEKS = re.compile(r"[Ͱ-Ͽἀ-῿][̀-ͯͰ-Ͽἀ-῿]*")
NUMMERS = re.compile(r"(?:OVL|OVG)\d+|[HG]\d+[A-Za-z]?")


def normaliseer(woord):
    s = unicodedata.normalize("NFD", woord or "")
    s = re.sub(r"[֑-ׇ̀-ͯ]", "", s)
    s = re.sub(r"[/־\sʹ͵;·]", "", s)
    return s.lower().replace("ς", "σ")


def nummer_van(strongs):
    nummers = [n for n in NUMMERS.findall(strongs or "")
               if not (n.startswith("H") and n[1:].isdigit() and int(n[1:]) >= 9000)]
    uniek = list(dict.fromkeys(nummers))
    return uniek[0] if len(uniek) == 1 else None


def index_van(vers):
    index, dubbel = {}, set()
    for woord in vers.get("grondtekst") or []:
        if not isinstance(woord, dict) or not woord.get("woord"):
            continue
        vorm, nummer = normaliseer(woord["woord"]), nummer_van(woord.get("strongs"))
        if not vorm or not nummer:
            continue
        if vorm in index and index[vorm] != nummer:
            dubbel.add(vorm)
        else:
            index[vorm] = nummer
    return {v: n for v, n in index.items() if v not in dubbel}, dubbel


def main(argv=None):
    ap = argparse.ArgumentParser(description="Werklijst van niet-klikbare grondwoorden in kanttekeningen.")
    ap.add_argument("--schrijf", action="store_true")
    ap.add_argument("--wortel", default=WORTEL)
    args = ap.parse_args(argv)

    data = os.path.join(args.wortel, "data")
    teller, items = Counter(), []
    for boek in sorted(os.listdir(data)):
        map_ = os.path.join(data, boek)
        if not os.path.isdir(map_):
            continue
        for bestand in sorted(os.listdir(map_), key=lambda x: (len(x), x)):
            if not re.fullmatch(r"\d+\.json", bestand):
                continue
            try:
                hoofdstuk = json.load(open(os.path.join(map_, bestand), encoding="utf-8"))
            except ValueError:
                continue
            if not isinstance(hoofdstuk, dict) or not isinstance(hoofdstuk.get("verses"), list):
                continue
            for vers in hoofdstuk["verses"]:
                noten = vers.get("marginNotes") or []
                if not noten:
                    continue
                index, dubbel = index_van(vers)
                for noot in noten:
                    tekst = noot.get("text2026") or ""
                    for woord in HEBREEUWS.findall(tekst) + GRIEKS.findall(tekst):
                        vorm = normaliseer(woord)
                        if not vorm:
                            continue
                        teller["grondwoorden"] += 1
                        if vorm in index:
                            teller["klikbaar"] += 1
                            continue
                        if vorm in dubbel:
                            reden, kandidaten = "dubbelzinnig", []
                        else:
                            kandidaten = sorted({n for v, n in index.items() if len(v) > 2 and (vorm in v or v in vorm)})
                            reden = "deels_in_vers" if kandidaten else "niet_in_vers"
                        teller[reden] += 1
                        items.append({"boek": boek, "hoofdstuk": int(bestand[:-5]), "vers": vers.get("number"),
                                      "marker": str(noot.get("marker")), "woord": woord, "reden": reden,
                                      "kandidaten": kandidaten})

    print(dict(teller))
    if args.schrijf:
        pad = os.path.join(args.wortel, "data", "grondwoorden-noten-werklijst.json")
        inhoud = {
            "uitleg": "Hebreeuwse en Griekse woorden in kanttekeningen die niet automatisch klikbaar "
                      "worden, omdat ze niet eenduidig in de grondtekst van hun vers staan. Gemaakt door "
                      "scripts/grondwoorden_in_noten.py; de koppeling zelf gebeurt in js/noot-grondwoorden.js.",
            "telling": dict(teller),
            "items": items,
        }
        with open(pad, "wb") as fh:
            fh.write((json.dumps(inhoud, ensure_ascii=False, indent=1) + "\n").encode("utf-8"))
        print("werklijst:", pad)
    return 0


if __name__ == "__main__":
    sys.exit(main())
