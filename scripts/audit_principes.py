#!/usr/bin/env python3
"""Controleert de wijzigingsprincipes op onderlinge tegenstrijdigheden.

Achtergrond: een principe hoort éénmalig te werken vanuit de 1888-tekst als
basis. Wat een principe oplevert mag niet het bronwoord van een ander principe
zijn, want dan hangt de uitkomst af van de volgorde waarin sweeps draaien.
Zie het kopje "Wijzigingsprincipes" in CLAUDE.md.

Draaien vanuit de repo-root:  python scripts/audit_principes.py
Geeft exitcode 1 als er iets gevonden is, zodat het in een controle past.
"""
import json
import os
import re
import sys
import collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAD = os.path.join(ROOT, "data", "wijzigingsprincipes.json")


def norm(s):
    return re.sub(r"\s+", " ", (s or "").strip().lower())


def main():
    principes = json.load(open(PAD, encoding="utf-8"))["principes"]
    print(f"principes: {len(principes)}\n")
    problemen = 0

    # 1) Regelrechte omkering: A -> B en B -> A. Die draaien elkaar eeuwig terug.
    paren = collections.defaultdict(list)
    for p in principes:
        paren[(norm(p.get("oud")), norm(p.get("nieuw")))].append(p["id"])
    omkeringen = []
    for (oud, nieuw), ids in paren.items():
        if oud and nieuw and (nieuw, oud) in paren:
            andere = paren[(nieuw, oud)]
            if ids[0] < andere[0]:
                omkeringen.append((ids, oud, andere, nieuw))
    print(f"omkeringen (A->B naast B->A): {len(omkeringen)}")
    for a, oud, b, nieuw in omkeringen:
        print(f"  {','.join(a)}: '{oud}' -> '{nieuw}'  TEGENOVER  {','.join(b)}: '{nieuw}' -> '{oud}'")
    problemen += len(omkeringen)

    # 2) Hetzelfde bronwoord met verschillende uitkomsten.
    per_oud = collections.defaultdict(list)
    for p in principes:
        if norm(p.get("oud")):
            per_oud[norm(p["oud"])].append((p["id"], norm(p.get("nieuw"))))
    botsend = {k: v for k, v in per_oud.items() if len({n for _, n in v}) > 1}
    # '(context-afhankelijk)' is een bewuste markering, geen botsing
    botsend = {k: v for k, v in botsend.items()
               if not any("context" in n for _, n in v)}
    print(f"\nzelfde bronwoord, verschillende uitkomst: {len(botsend)}")
    for k, v in sorted(botsend.items()):
        print("  '" + k + "' -> " + " | ".join(f"{i}:'{n}'" for i, n in v))
    problemen += len(botsend)

    # 3) Ketens: de uitkomst van het ene principe is het bronwoord van het andere.
    per_nieuw = collections.defaultdict(list)
    for p in principes:
        if norm(p.get("nieuw")):
            per_nieuw[norm(p["nieuw"])].append(p["id"])
    ketens = []
    for p in principes:
        oud = norm(p.get("oud"))
        if oud and oud in per_nieuw:
            for eerder in per_nieuw[oud]:
                if eerder != p["id"]:
                    ketens.append((eerder, oud, p["id"], norm(p.get("nieuw"))))
    print(f"\nketens (uitkomst van X is bronwoord van Y): {len(ketens)}")
    for a, midden, b, eind in ketens:
        print(f"  {a} levert '{midden}' op; {b} maakt daar '{eind}' van")
    problemen += len(ketens)

    # 4) Dubbele nummers.
    tel = collections.Counter(p["id"] for p in principes)
    dubbel = sorted(k for k, v in tel.items() if v > 1)
    print(f"\ndubbele id's: {len(dubbel)}" + ("  " + ", ".join(dubbel) if dubbel else ""))
    problemen += len(dubbel)

    print(f"\n{'GEEN PROBLEMEN' if problemen == 0 else str(problemen) + ' PUNT(EN) OM NA TE LOPEN'}")
    return 1 if problemen else 0


if __name__ == "__main__":
    sys.exit(main())
