#!/usr/bin/env python3
"""Herstelt scheve citaat-markup in text2026_html.

Twee fouten, allebei van voor het Bijbelbrede markeren van geneste citaten,
en allebei reden waarom 135 verzen daar zijn overgeslagen:

1. Verkeerde sluitvolgorde met een dubbele sluittag, vooral Genesis 1-20:
       <span class="god-speaks"><i>…tekst</span></i></span>
   Er hoort te staan: <i>…tekst</i></span>

2. Een zwevende cursief vóór de span, vooral Johannes:
       <sup …></sup><i><span class="god-speaks"><i>…
   Die eerste <i> opent zonder te sluiten.

Browsers repareren dit stil, dus je ziet er niets van. Scripts lopen er wel
op stuk.

De zichtbare tekst en alle kanttekening-markers moeten exact gelijk blijven;
het script weigert een vers te schrijven zodra dat niet zo is.

Draaien vanuit de repo-root:  python scripts/herstel_citaat_markup.py [--doen]
"""
import json
import os
import re
import sys
import collections

DOEN = "--doen" in sys.argv
DATA = "data"


def zichtbaar(h):
    """Alleen de leesbare tekst, zonder enige opmaak."""
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", h)).strip()


def markers(h):
    """De kanttekening-verwijzingen, in volgorde."""
    return re.findall(r'data-note="([^"]+)"', h)


def scheef(h):
    return (len(re.findall(r"<span\b", h)) != len(re.findall(r"</span>", h))
            or len(re.findall(r"<i>", h)) != len(re.findall(r"</i>", h)))


def herstel(h):
    """Geeft de herstelde html terug, of None als er niets te doen valt."""
    origineel = h

    # Fout 1: </span></i></span> -> </i></span>, ook bij meer dan een dubbele.
    while re.search(r"</span>\s*</i>\s*</span>", h):
        h = re.sub(r"</span>(\s*</i>\s*</span>)", r"\1", h, count=1)

    # Fout 2: een <i> die direct voor een <span> opent en nergens sluit.
    if len(re.findall(r"<i>", h)) > len(re.findall(r"</i>", h)):
        h2 = re.sub(r"<i>(\s*<span\b)", r"\1", h, count=1)
        if len(re.findall(r"<i>", h2)) == len(re.findall(r"</i>", h2)):
            h = h2

    return h if h != origineel else None


def main():
    hersteld = 0
    resteert = []
    geweigerd = []
    per_boek = collections.Counter()

    for boek in sorted(os.listdir(DATA)):
        bd = os.path.join(DATA, boek)
        if not os.path.isdir(bd):
            continue
        for f in sorted(os.listdir(bd)):
            if not re.match(r"^\d+\.json$", f):
                continue
            pad = os.path.join(bd, f)
            ruw = open(pad, encoding="utf-8").read()
            try:
                doc = json.loads(ruw)
            except Exception:
                continue
            m_ins = re.search(r'\n( +)"', ruw)
            ins = len(m_ins.group(1)) if m_ins else 1
            gewijzigd = False

            for v in doc.get("verses") or []:
                h = v.get("text2026_html") or ""
                if not h or not scheef(h):
                    continue
                nieuw = herstel(h)
                ref = f"{boek} {f[:-5]}:{v['number']}"
                if nieuw is None:
                    resteert.append(ref)
                    continue
                # Niets mag aan de tekst of de markers veranderen.
                if zichtbaar(nieuw) != zichtbaar(h) or markers(nieuw) != markers(h):
                    geweigerd.append(ref)
                    continue
                if scheef(nieuw):
                    resteert.append(ref)
                    continue
                v["text2026_html"] = nieuw
                gewijzigd = True
                hersteld += 1
                per_boek[boek] += 1

            if gewijzigd and DOEN:
                json.dump(doc, open(pad, "w", encoding="utf-8"),
                          ensure_ascii=False, indent=ins)

    print("PROEFDRAAI" if not DOEN else "TOEGEPAST")
    print(f"\nhersteld : {hersteld} verzen")
    for b, n in per_boek.most_common():
        print(f"   {b}: {n}")
    print(f"\nnog scheef na herstel : {len(resteert)}")
    for r in resteert[:10]:
        print("   ", r)
    print(f"geweigerd (tekst of marker zou veranderen) : {len(geweigerd)}")
    for r in geweigerd[:10]:
        print("   ", r)
    return 0


if __name__ == "__main__":
    sys.exit(main())
