#!/usr/bin/env python3
"""Controleert js/selectie.js tegen de OSV-data in ../data/.

Meldt elke passage waarvan het boek of hoofdstuk niet bestaat of waarvan het
versbereik buiten het hoofdstuk valt. Exit-code 1 bij fouten.
"""
import json
import sys
from pathlib import Path

WERKMAP = Path(__file__).resolve().parent.parent
DATA = WERKMAP.parent / "data"


def lees_selectie(pad: Path):
    """Haalt de JSON-array uit js/selectie.js (tussen eerste [ en laatste ])."""
    tekst = pad.read_text(encoding="utf-8")
    start = tekst.index("[")
    einde = tekst.rindex("]")
    return json.loads(tekst[start:einde + 1])


def controleer(selectie, boeken):
    fouten = []
    for i, p in enumerate(selectie):
        plek = f"regel {i + 1} ({p.get('boek')} {p.get('hoofdstuk')})"
        boek, hoofdstuk = p.get("boek"), p.get("hoofdstuk")
        if boek not in boeken:
            fouten.append(f"{plek}: onbekend boek '{boek}'")
            continue
        bestand = DATA / boek / f"{hoofdstuk}.json"
        if not bestand.exists():
            fouten.append(f"{plek}: hoofdstuk bestaat niet ({bestand})")
            continue
        aantal = len(json.loads(bestand.read_text(encoding="utf-8"))["verses"])
        bereik = p.get("verzen")
        if bereik:
            eerste, laatste = bereik
            if eerste < 1 or eerste > aantal:
                fouten.append(f"{plek}: eerste vers {eerste} buiten 1-{aantal}")
            if laatste > aantal:
                fouten.append(f"{plek}: laatste vers {laatste} > {aantal} verzen")
            if laatste < eerste:
                fouten.append(f"{plek}: versbereik loopt achteruit")
    return fouten


def main():
    pad = WERKMAP / "js" / "selectie.js"
    if not pad.exists():
        print(f"js/selectie.js niet gevonden ({pad})")
        return 1
    selectie = lees_selectie(pad)
    boeken = {b["id"] for b in json.loads((DATA / "books.json").read_text(encoding="utf-8"))["books"]}
    fouten = controleer(selectie, boeken)
    if fouten:
        print(f"{len(fouten)} fout(en) in {len(selectie)} passages:")
        print("\n".join(f"  - {f}" for f in fouten))
        return 1
    print(f"{len(selectie)} passages: alle boeken en hoofdstukken gevonden, versbereiken binnen bereik")
    return 0


if __name__ == "__main__":
    sys.exit(main())
