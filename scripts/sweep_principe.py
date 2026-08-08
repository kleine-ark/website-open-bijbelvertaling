#!/usr/bin/env python3
"""Past één principe corpusbreed toe, volgens de eerstelijnsregel.

De kern: of een vers in aanmerking komt wordt bepaald door **textSV1888**, niet
door text2026. Anders kan een sweep zijn eigen uitvoer opnieuw als invoer zien,
of de uitvoer van een ánder principe aanpakken. Dat is eerder misgegaan —
'leger' in de huidige tekst is op veel plaatsen juist het resultaat van
V321 (legermacht) en O2 (heir), en die mogen door een leger-sweep niet geraakt
worden. Zie het kopje "Wijzigingsprincipes" in CLAUDE.md.

Gebruik:
    python scripts/sweep_principe.py --id V1193 \
        --sv "\\bjaren oud\\b" --zoek "\\bjaren oud\\b" --vervang "jaar oud" --droog

    --sv        patroon dat in textSV1888 moet voorkomen (de eerstelijnstoets)
    --zoek      patroon dat in text2026 vervangen wordt (default: gelijk aan --sv)
    --vervang   vervanging; backreferences als \\1 mogen
    --boeken    kommalijst om te beperken, bijv. numeri,leviticus
    --sla-over  kommalijst boek:hoofdstuk:vers die overgeslagen worden
    --droog     toon wat er zou veranderen, schrijf niets

Zonder --droog worden text2026 én text2026_html bijgewerkt en wordt de
phraseDiff opnieuw opgebouwd, waarbij het nieuwe woordpaar aan --id wordt
gekoppeld en bestaande koppelingen bewaard blijven.
"""
import argparse
import difflib
import glob
import json
import os
import re
import sys

WORTEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def kaal(s):
    """Versie zonder opmaak en zonder nootmarkeringen, voor de woorddiff."""
    s = re.sub(r"<sup[^>]*>.*?</sup>", "", s or "")
    s = re.sub(r"<[^>]+>", "", s)
    return re.sub(r"\s+", " ", s).strip()


def sleutel(paar):
    return (re.sub(r"^[^\w]+|[^\w]+$", "", paar[0]),
            re.sub(r"^[^\w]+|[^\w]+$", "", paar[1]))


def lees(pad):
    """JSON plus de opmaak van het origineel: de repo mengt inspringing van 1
    en 2 spaties en niet elk bestand heeft dezelfde regeleindes."""
    ruw = open(pad, encoding="utf-8", newline="").read()
    m = re.search(r'\n( +)"', ruw)
    return json.loads(ruw), {
        "indent": len(m.group(1)) if m else 2,
        "newline": "\r\n" if "\r\n" in ruw else "\n",
        "eindregel": ruw.endswith("\n"),
    }


def schrijf(pad, data, vorm):
    tekst = json.dumps(data, ensure_ascii=False, indent=vorm["indent"])
    if vorm["eindregel"]:
        tekst += "\n"
    if vorm["newline"] != "\n":
        tekst = tekst.replace("\n", vorm["newline"])
    open(pad, "w", encoding="utf-8", newline="").write(tekst)


def nieuwe_diff(sv, ov, oude_diff, pid, merk=""):
    """Woorddiff SV1888 tegen 2026; bestaande principe-koppelingen behouden.

    Let op het onderscheid tussen "dit paar stond er al, zonder principe" en
    "dit paar is nieuw". Een woordpaar dat al bestond met principe null moet
    null blijven — het hoort niet bij deze sweep. Alleen paren die door deze
    wijziging ontstaan krijgen het nieuwe id. Dat verschil sneuvelt zodra je
    `principe or pid` schrijft, en dan plakt de sweep zijn id op wijzigingen
    van iemand anders.
    """
    kaart = {sleutel((e["old"], e["new"])): e.get("principe") for e in oude_diff}
    a, b = sv.split(), ov.split()
    uit = []
    gezien = set()
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b).get_opcodes():
        if tag == "equal":
            continue
        oud, nieuw = " ".join(a[i1:i2]), " ".join(b[j1:j2])
        if not (oud or nieuw):
            continue
        s = sleutel((oud, nieuw))
        gezien.add(s)
        principe = kaart[s] if s in kaart else pid
        uit.append({"old": oud, "new": nieuw, "principe": principe})
    # Een paar dat verdwijnt is meestal opgegaan in een groter blok; dan kan een
    # koppeling stilletjes verloren gaan. Melden, niet oplossen.
    for s, p in kaart.items():
        if s not in gezien and p:
            print(f"  !! {merk}: koppeling {p} bij {s} is vervallen door hergroepering")
    return uit


def verzen(d):
    v = d.get("verses")
    if isinstance(v, list):
        return [x for x in v if isinstance(x, dict)]
    if isinstance(v, dict):
        return [x for x in v.values() if isinstance(x, dict)]
    return []


def main():
    p = argparse.ArgumentParser(description="Pas één principe corpusbreed toe.")
    p.add_argument("--id", required=True, help="principe-id, bijv. V1193")
    p.add_argument("--sv", required=True, help="patroon dat in textSV1888 moet staan")
    p.add_argument("--zoek", help="patroon in text2026 (default: gelijk aan --sv)")
    p.add_argument("--vervang", required=True)
    p.add_argument("--boeken", help="kommalijst, bijv. numeri,leviticus")
    p.add_argument("--sla-over", default="", help="kommalijst boek:hoofdstuk:vers")
    p.add_argument("--droog", action="store_true")
    a = p.parse_args()

    sv_pat = re.compile(a.sv)
    zoek_pat = re.compile(a.zoek or a.sv)
    boeken = set(x.strip().lower() for x in a.boeken.split(",")) if a.boeken else None
    overslaan = set(x.strip().lower() for x in a.sla_over.split(",") if x.strip())

    geraakt = 0
    overgeslagen_regel = 0
    niet_in_sv = 0
    bestanden = 0

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

        for v in verzen(d):
            ov = v.get("text2026") or ""
            if not zoek_pat.search(ov):
                continue
            merk = f"{boek}:{hs}:{v.get('number')}"
            if merk.lower() in overslaan:
                overgeslagen_regel += 1
                print(f"  overgeslagen op verzoek  {merk}")
                continue
            # eerstelijnstoets: staat het bronwoord überhaupt in de 1888-tekst?
            if not sv_pat.search(v.get("textSV1888") or ""):
                niet_in_sv += 1
                print(f"  GEEN SV-bron, niet aangeraakt  {merk}: {kaal(ov)[:90]}")
                continue

            nieuw_ov = zoek_pat.sub(a.vervang, ov)
            nieuw_html = zoek_pat.sub(a.vervang, v.get("text2026_html") or "")
            if nieuw_ov == ov:
                continue
            print(f"{merk}\n   was: {kaal(ov)[:150]}\n   nu : {kaal(nieuw_ov)[:150]}")
            geraakt += 1
            if not a.droog:
                v["text2026"] = nieuw_ov
                v["text2026_html"] = nieuw_html
                v["phraseDiff"] = nieuwe_diff(
                    kaal(v.get("textSV1888", "")), kaal(nieuw_ov),
                    v.get("phraseDiff", []), a.id, merk)
                gewijzigd = True

        if gewijzigd:
            schrijf(pad, d, vorm)
            bestanden += 1

    print()
    print(f"{'ZOU WIJZIGEN' if a.droog else 'GEWIJZIGD'}: {geraakt} verzen"
          f"{'' if a.droog else f' in {bestanden} bestanden'}")
    if niet_in_sv:
        print(f"overgeslagen omdat het bronwoord niet in SV1888 staat: {niet_in_sv}")
    if overgeslagen_regel:
        print(f"overgeslagen op verzoek: {overgeslagen_regel}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
