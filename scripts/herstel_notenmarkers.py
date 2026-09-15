#!/usr/bin/env python3
"""Zet verdwenen notenmarkeringen terug in text2026_html.

Waarom dit nodig is. Bij het aanbrengen van citaatopmaak (god-speaks,
direct-speech) is text2026_html in duizenden verzen opnieuw opgebouwd, en
daarbij vielen de <sup class="note-marker">-elementen weg. De kanttekening
bestaat nog, maar in de lezende tekst staat geen nummertje meer om op te
klikken. De citaatscripts zagen het niet: hun controle stript eerst alle
<sup>'s en vergelijkt dan de kale tekst.

Wat dit script doet. Voor elk nummertje dat in text2026_html ontbreekt maar in
textSV1888_html (of anders text1637_html) wel staat, zoekt het het woord
waarachter het nummertje in die laag staat, lijnt de woorden van die laag uit
tegen text2026_html en zet het nummertje achter het overeenkomende woord.

Het plaatst alleen als de uitlijning zeker is:
  - het ankerwoord ligt in een gelijk blok van minstens twee woorden (of het is
    in beide verzen het eerste woord), en de relatieve plaats in het vers is
    ongeveer gelijk; of
  - het nummertje staat in de bron voor het eerste woord van het vers.
Al het andere gaat naar de werklijst en blijft ongemoeid: een nummertje op de
verkeerde plek is erger dan geen nummertje. Dat geldt ook voor de noten
waarvan het nummertje in geen enkele laag staat; daar is vaak de nummering
zelf stuk (1 Korinthiers 14:30 heeft in 1637 de nummers 1-4, de noten heten
101-104), en koppelen op volgorde is niet betrouwbaar.

Na elke plaatsing wordt getoetst dat de kale tekst gelijk is gebleven en dat
het nummertje er precies een keer staat. Het bestand wordt chirurgisch
bijgewerkt: alleen de betrokken JSON-strings veranderen, de rest blijft byte
voor byte, en na afloop wordt per vers nagelezen dat precies de bedoelde html
is weggeschreven.

Gebruik:
    python scripts/herstel_notenmarkers.py              droogtest, alleen tellen
    python scripts/herstel_notenmarkers.py --schrijf    doorvoeren + werklijst
    python scripts/herstel_notenmarkers.py --boek genesis
"""
import argparse
import difflib
import json
import os
import re
import sys
from collections import Counter

WORTEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WERKLIJST = os.path.join("data", "notenmarkers-werklijst.json")

SUP = re.compile(r'<sup class="note-marker" data-note="([^"]*)">.*?</sup>', re.S)
TAG = re.compile(r'<sup class="note-marker"[^>]*>.*?</sup>|<[^>]+>', re.S)
BRONLAGEN = ("textSV1888_html", "text1637_html")


def markers(html):
    return SUP.findall(html or "")


def kaal(html):
    """De leesbare tekst zonder markeringen en opmaak."""
    zonder = SUP.sub("", html or "")
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", zonder)).strip()


def woorden(html):
    """Woorden van een html-regel met hun plaats in de html.

    Opmaak telt niet als woordgrens (1637 zet <i> midden in een woord) en
    notenmarkeringen worden overgeslagen. Per woord: de genormaliseerde vorm,
    de html-positie direct na de laatste letter, en die na het laatste teken
    (dus na aansluitende leestekens)."""
    html = html or ""
    tekens = []
    vorige = 0
    for m in TAG.finditer(html):
        tekens.extend((html[k], k) for k in range(vorige, m.start()))
        vorige = m.end()
    tekens.extend((html[k], k) for k in range(vorige, len(html)))

    uit = []
    run = []
    for teken, pos in tekens + [(" ", len(html))]:
        if teken.isspace():
            if run:
                tekst = "".join(t for t, _ in run)
                vorm = re.sub(r"[^\w]", "", tekst.lower())
                if vorm:
                    na_letter = max(p for t, p in run if re.match(r"\w", t)) + 1
                    uit.append({"vorm": vorm, "na_letter": na_letter, "na_alles": run[-1][1] + 1})
                run = []
        else:
            run.append((teken, pos))
    return uit


def ankers(html):
    """Per nummertje in een bronlaag: de index van het woord ervoor (-1 is het
    versbegin), of het direct na een letter staat, en de groep nummertjes die
    zonder tussenliggende tekst op dezelfde plek staan."""
    html = html or ""
    ws = woorden(html)
    uit = {}
    groepen = []
    laatste_eind = None
    for m in SUP.finditer(html):
        index = sum(1 for w in ws if w["na_alles"] <= m.start()) - 1
        voor = re.sub(r"(?:<sup[^>]*>.*?</sup>|<[^>]+>)+$", "", html[:m.start()], flags=re.S)
        na_letter = bool(voor) and bool(re.match(r"\w", voor[-1]))
        if laatste_eind is not None and html[laatste_eind:m.start()].strip() == "":
            groepen[-1].append(m.group(1))
        else:
            groepen.append([m.group(1)])
        uit[m.group(1)] = {"index": index, "na_letter": na_letter, "groep": groepen[-1]}
        laatste_eind = m.end()
    return uit, [w["vorm"] for w in ws]


def plaats(doel_html, nummer, anker, bron_vormen):
    """Geeft (nieuwe_html, None) of (None, reden)."""
    doel = woorden(doel_html)
    if anker["index"] < 0:
        pos = 0
    else:
        vormen = [w["vorm"] for w in doel]
        sm = difflib.SequenceMatcher(None, bron_vormen, vormen, autojunk=False)
        j = None
        for a, b, grootte in sm.get_matching_blocks():
            # Een blok van een woord is te zwak ("en", "de" komen overal voor),
            # behalve het eerste woord van beide verzen: "In den beginne" en
            # "In het begin" delen alleen "In", en dat is wel zeker.
            eerste_woord = a == b == anker["index"] == 0
            if (grootte >= 2 or eerste_woord) and a <= anker["index"] < a + grootte:
                j = b + (anker["index"] - a)
                break
        if j is None:
            return None, "benaderd"
        if abs(anker["index"] / max(1, len(bron_vormen)) - j / max(1, len(vormen))) > 0.35:
            return None, "plaats_wijkt_af"
        pos = doel[j]["na_letter"] if anker["na_letter"] else doel[j]["na_alles"]

    # Staan er op die plek al nummertjes uit dezelfde groep die eerder horen, dan erachter.
    groep = anker["groep"]
    while True:
        m = SUP.match(doel_html, pos)
        if not m or m.group(1) not in groep or groep.index(m.group(1)) > groep.index(nummer):
            break
        pos = m.end()
    sup = f'<sup class="note-marker" data-note="{nummer}">{nummer}</sup>'
    # Aan het versbegin volgt in text2026_html een spatie op het nummertje,
    # behalve als er meteen een citaat-span of een ander nummertje begint.
    volgende = doel_html[pos:pos + 1]
    tussen = " " if anker["index"] < 0 and volgende and not volgende.isspace() and volgende != "<" else ""
    return doel_html[:pos] + sup + tussen + doel_html[pos:], None


def ontbrekende_markers(vers):
    """De nummers van kanttekeningen die geen nummertje in text2026_html hebben."""
    noten = [str(n.get("marker")) for n in vers.get("marginNotes") or []]
    if not noten or not vers.get("text2026_html"):
        return []
    aanwezig = set(markers(vers.get("text2026_html")))
    return [n for n in noten if n not in aanwezig]


def herstel_vers(vers):
    """Geeft (nieuwe_html, geplaatste_nummers, werklijst_items)."""
    html = vers.get("text2026_html") or ""
    ontbrekend = ontbrekende_markers(vers)
    geplaatst, lijst = [], []
    if not ontbrekend:
        return html, geplaatst, lijst
    bronnen = [(laag, *ankers(vers.get(laag))) for laag in BRONLAGEN]
    for nummer in ontbrekend:
        bron = next(((laag, a, v) for laag, a, v in bronnen if nummer in a), None)
        if bron is None:
            lijst.append({"marker": nummer, "reden": "geen_nummertje_in_bron",
                          "nummers1637": markers(vers.get("text1637_html"))})
            continue
        laag, ank, vormen = bron
        nieuw, reden = plaats(html, nummer, ank[nummer], vormen)
        if nieuw is None:
            i = ank[nummer]["index"]
            lijst.append({"marker": nummer, "reden": reden, "bronlaag": laag,
                          "ankerwoorden": " ".join(vormen[max(0, i - 2):i + 1])})
            continue
        if kaal(nieuw) != kaal(html) or markers(nieuw).count(nummer) != 1:
            lijst.append({"marker": nummer, "reden": "controle_faalt", "bronlaag": laag})
            continue
        html = nieuw
        geplaatst.append(nummer)
    return html, geplaatst, lijst


def hoofdstukken(wortel, boek=None):
    data = os.path.join(wortel, "data")
    for b in sorted(os.listdir(data)):
        if boek and b != boek:
            continue
        map_ = os.path.join(data, b)
        if not os.path.isdir(map_):
            continue
        for f in sorted(os.listdir(map_), key=lambda x: (len(x), x)):
            if re.fullmatch(r"\d+\.json", f):
                yield b, int(f[:-5]), os.path.join(map_, f)


def lees(pad):
    with open(pad, "rb") as fh:
        ruw = fh.read().decode("utf-8")
    try:
        data = json.loads(ruw)
    except ValueError:
        return ruw, None
    if not isinstance(data, dict) or not isinstance(data.get("verses"), list):
        return ruw, None
    return ruw, data


def herstel_hoofdstuk(ruw, data):
    """Geeft (nieuw_ruw, geplaatst_per_vers, werklijst_items_per_vers)."""
    verzen = data["verses"]
    totaal = Counter(v.get("text2026_html") or "" for v in verzen)
    vervangen = Counter()
    gezien = Counter()
    nieuw_ruw = ruw
    verwacht = []
    geplaatst_per_vers, lijst_per_vers = {}, {}
    for vers in verzen:
        html_oud = vers.get("text2026_html") or ""
        k = gezien[html_oud]
        gezien[html_oud] += 1
        html_nieuw, geplaatst, lijst = herstel_vers(vers)
        if geplaatst:
            sleutel = '"text2026_html": ' + json.dumps(html_oud, ensure_ascii=False)
            treffers = [m.start() for m in re.finditer(re.escape(sleutel), nieuw_ruw)]
            # Staat dezelfde html in meer verzen (1 Koningen 19:10 en 19:14), dan
            # hoort bij dit vers de k-de, geteld over wat nog niet vervangen is.
            if len(treffers) == totaal[html_oud] - vervangen[html_oud]:
                i = treffers[k - vervangen[html_oud]]
                nieuw_ruw = (nieuw_ruw[:i] + '"text2026_html": '
                             + json.dumps(html_nieuw, ensure_ascii=False) + nieuw_ruw[i + len(sleutel):])
                vervangen[html_oud] += 1
                geplaatst_per_vers[vers["number"]] = geplaatst
            else:
                lijst = lijst + [{"marker": n, "reden": "schrijfvorm"} for n in geplaatst]
                html_nieuw = html_oud
        else:
            html_nieuw = html_oud
        if lijst:
            lijst_per_vers[vers["number"]] = lijst
        verwacht.append(html_nieuw)
    if nieuw_ruw != ruw:
        controle = json.loads(nieuw_ruw)
        if [v.get("text2026_html") or "" for v in controle["verses"]] != verwacht:
            raise AssertionError("de weggeschreven html wijkt af van wat bedoeld was")
        if [kaal(v.get("text2026_html")) for v in controle["verses"]] != [kaal(v.get("text2026_html")) for v in verzen]:
            raise AssertionError("de leesbare tekst is veranderd")
    return nieuw_ruw, geplaatst_per_vers, lijst_per_vers


def main(argv=None):
    ap = argparse.ArgumentParser(description="Verdwenen notenmarkeringen terugzetten.")
    ap.add_argument("--schrijf", action="store_true", help="wijzigingen en werklijst opslaan")
    ap.add_argument("--boek", help="beperk tot een boek (werklijst wordt dan niet geschreven)")
    ap.add_argument("--wortel", default=WORTEL)
    args = ap.parse_args(argv)

    geplaatst_totaal = verzen = bestanden = 0
    redenen = Counter()
    werklijst = []
    for boek, hs, pad in hoofdstukken(args.wortel, args.boek):
        ruw, data = lees(pad)
        if data is None:
            continue
        try:
            nieuw_ruw, geplaatst, lijsten = herstel_hoofdstuk(ruw, data)
        except AssertionError as fout:
            raise AssertionError(f"{pad}: {fout}") from None
        for nummer, items in lijsten.items():
            for item in items:
                redenen[item["reden"]] += 1
                werklijst.append({"boek": boek, "hoofdstuk": hs, "vers": nummer, **item})
        geplaatst_totaal += sum(len(g) for g in geplaatst.values())
        verzen += len(geplaatst)
        if nieuw_ruw != ruw:
            bestanden += 1
            if args.schrijf:
                with open(pad, "wb") as fh:
                    fh.write(nieuw_ruw.encode("utf-8"))

    print(f"geplaatst: {geplaatst_totaal} nummertjes in {verzen} verzen, {bestanden} bestanden")
    print(f"naar de werklijst: {sum(redenen.values())} {dict(redenen)}")
    if args.schrijf and not args.boek:
        pad = os.path.join(args.wortel, WERKLIJST)
        inhoud = {
            "uitleg": "Kanttekeningen waarvan het nummertje in text2026_html ontbreekt en dat niet "
                      "zeker automatisch terug te zetten was. Gemaakt door "
                      "scripts/herstel_notenmarkers.py. tests/test_notenmarkers.py faalt zodra er "
                      "een nummertje ontbreekt dat hier niet op staat.",
            "aantal": len(werklijst),
            "items": werklijst,
        }
        with open(pad, "wb") as fh:
            fh.write((json.dumps(inhoud, ensure_ascii=False, indent=1) + "\n").encode("utf-8"))
        print(f"werklijst: {pad}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
