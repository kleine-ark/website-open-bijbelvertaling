#!/usr/bin/env python3
"""Gedeeld gereedschap voor het verwerken van lezersmeldingen.

Een melding leidt vaak tot een kleine woordvervanging in één vers. Die moet op
drie plaatsen kloppen: in de leestekst, in de opmaak die de site toont, en in
de woorddiff tegen 1888, waar elk gewijzigd woordpaar een principe draagt.
Dit bestand houdt die drie bij elkaar. Citaatopmaak gaat via citaatopmaak.py.

    from review_hulp import pas_tekst_aan, schrijf_reviewlijst
"""

from __future__ import annotations

import json
from pathlib import Path

from sweep_principe import kaal, lees, nieuwe_diff, schrijf
from synchroniseer_opmaak import bijtrekken

ROOT = Path(__file__).resolve().parents[1]

STATUSSEN = ("verwerkt", "afgedekt", "gepland", "open", "vervallen")


def herkoppel(oude_diff, diff):
    """Hang een principe dat door hergroepering losraakte aan het nieuwe blok.

    Een woordpaar dat in een groter blok opgaat verliest zijn principe-id: de
    sleutel bestaat niet meer. Het blok dat het oude paar bevat is dezelfde
    wijziging, alleen ruimer opgeschreven, en erft dus dat id. Hetzelfde geldt
    voor een blok met precies dezelfde woorden uit 1888 waarvan alleen de
    uitkomst veranderde.
    """
    bezet = {(e["old"], e["new"]) for e in diff}
    for oud_paar in oude_diff:
        principe = oud_paar.get("principe")
        if not principe or (oud_paar["old"], oud_paar["new"]) in bezet:
            continue
        for blok in diff:
            if blok.get("principe") is not None:
                continue
            if (oud_paar["old"] == blok["old"] and oud_paar["old"]) or (
                    oud_paar["old"] in blok["old"] and oud_paar["new"] in blok["new"]):
                blok["principe"] = principe
                break
    return diff


def kern(oud, nieuw):
    """Het deel van de nieuwe tekst dat werkelijk verschilt van de oude."""
    a, b = oud.split(), nieuw.split()
    while a and b and a[0] == b[0]:
        a, b = a[1:], b[1:]
    while a and b and a[-1] == b[-1]:
        a, b = a[:-1], b[:-1]
    return " ".join(b)


def koppel(oude_diff, diff, correcties):
    """Geef de blokken die door deze correcties ontstaan hun principe."""
    oud = {(e["old"], e["new"]) for e in oude_diff}
    for blok in diff:
        if blok.get("principe") or (blok["old"], blok["new"]) in oud:
            continue
        woorden = blok["new"].strip(" ,.;:!?")
        for oud_tekst, nieuw_tekst, principe in correcties:
            if woorden and woorden in kern(oud_tekst, nieuw_tekst):
                blok["principe"] = principe
                break
    return diff


def pas_tekst_aan(vers, correcties, referentie):
    """Pas exacte vervangingen (oud, nieuw, principe) toe op één vers.

    Leestekst, opmaak en woorddiff worden samen bijgewerkt. Staat de nieuwe
    tekst er al, dan gebeurt er niets; dat maakt een herhaalde run veilig.
    """
    nieuw = vers["text2026"]
    for oud, vervang, _ in correcties:
        # Eerst kijken of het oude er nog staat: "verleidde" zit ook in
        # "verleiddet", dus alleen op het nieuwe letten zou ten onrechte
        # overslaan. Is het oude een deel van het nieuwe, dan is het al gedaan.
        if oud in nieuw and not (oud in vervang and vervang in nieuw):
            nieuw = nieuw.replace(oud, vervang)
        elif vervang not in nieuw:
            raise ValueError("%s: niet gevonden: %r" % (referentie, oud))
    if nieuw == vers["text2026"]:
        return False
    html = bijtrekken(vers["text2026_html"], nieuw)
    if html is None or kaal(html) != kaal(nieuw):
        raise ValueError("%s: HTML kon niet veilig worden bijgewerkt" % referentie)
    vers["text2026"] = nieuw
    vers["text2026_html"] = html
    # De Ethiopische boeken hebben geen tekst uit 1888; daar is geen woorddiff om
    # bij te werken, en een diff tegen een lege tekst zou één groot blok zijn.
    if (vers.get("textSV1888") or "").strip():
        oude_diff = vers.get("phraseDiff", [])
        diff = nieuwe_diff(kaal(vers["textSV1888"]), kaal(nieuw), oude_diff, None,
                           referentie.lower())
        vers["phraseDiff"] = koppel(oude_diff, herkoppel(oude_diff, diff), correcties)
    return True


def verwerk_correcties(boek, naam, correcties):
    """{(hoofdstuk, vers): [(oud, nieuw, principe)]} voor één boek."""
    per_hoofdstuk = {}
    for (hoofdstuk, nummer), paren in correcties.items():
        per_hoofdstuk.setdefault(hoofdstuk, []).append((nummer, paren))
    geraakt = 0
    for hoofdstuk, opdrachten in sorted(per_hoofdstuk.items()):
        pad = ROOT / "data" / boek / ("%d.json" % hoofdstuk)
        data, vorm = lees(str(pad))
        verzen = {item["number"]: item for item in data["verses"]}
        gewijzigd = False
        for nummer, paren in sorted(opdrachten):
            if pas_tekst_aan(verzen[nummer], paren, "%s %d:%d" % (naam, hoofdstuk, nummer)):
                geraakt += 1
                gewijzigd = True
        if gewijzigd:
            schrijf(str(pad), data, vorm)
    return geraakt


def registreer_principes(prefix, nieuwe, bijgewerkt=None, gebruikt=()):
    """Vervang de principes met dit id-voorvoegsel door `nieuwe`.

    `bijgewerkt` past velden van bestaande principes aan; `gebruikt` is de
    lijst ids waarnaar correcties verwijzen, en die moeten allemaal bestaan.
    """
    pad = ROOT / "data" / "wijzigingsprincipes.json"
    data, vorm = lees(str(pad))
    principes = [p for p in data["principes"] if not p["id"].startswith(prefix)]
    principes.extend(nieuwe)
    per_id = {p["id"]: p for p in principes}
    if len(per_id) != len(principes):
        raise ValueError("dubbel principe-id")
    for pid, velden in (bijgewerkt or {}).items():
        per_id[pid].update(velden)
    ontbreekt = sorted(set(gebruikt) - set(per_id))
    if ontbreekt:
        raise ValueError("principes bestaan niet: %s" % ", ".join(ontbreekt))
    data["principes"] = principes
    schrijf(str(pad), data, vorm)


def schrijf_reviewlijst(boek, naam, besluiten, bron="Google-opmerkingen, opgehaald 2026-09-14"):
    """Schrijf per melding het besluit weg: (ref, suggestie, categorie, status, resultaat)."""
    items = []
    for ref, suggestie, categorie, status, resultaat in besluiten:
        if status not in STATUSSEN:
            raise ValueError("%s %s: onbekende status %r" % (naam, ref, status))
        items.append({"ref": "%s %s" % (naam, ref), "suggestie": suggestie,
                      "categorie": categorie, "status": status, "resultaat": resultaat})
    pad = ROOT / "data" / ("google-opmerkingen-%s-reviewqueue.json" % boek)
    pad.write_text(json.dumps({"source": bron, "book": naam, "items": items},
                              ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return len(items)
