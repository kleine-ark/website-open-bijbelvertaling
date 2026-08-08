#!/usr/bin/env python3
"""Controleert de wijzigingsprincipes op onderlinge tegenstrijdigheden.

Achtergrond: een principe hoort éénmalig te werken vanuit de 1888-tekst als
basis. Wat een principe oplevert mag niet het bronwoord van een ander principe
zijn, want dan hangt de uitkomst af van de volgorde waarin sweeps draaien.
Zie het kopje "Wijzigingsprincipes" in CLAUDE.md.

De eerste vier controles kijken alleen naar de principes zelf. De laatste twee
leggen de principes naast de tekst en zoeken naar half werk:

  5) half toegepast — het principe pakte één verbuiging en liet de rest staan.
     Zo bleef "drenken" achter toen "drenkte" was vervangen, en "vlade" toen
     "vladen" was gedaan. Binnen één vers kan dat twee woorden voor dezelfde
     handeling opleveren.
  6) bereik niet nagekomen — een principe met een bereik dat daarbinnen niet
     overal is toegepast, of juist daarbuiten.

Die twee melden alleen; ze wijzigen niets. Dat is met opzet: homoniemen en
betekenisverschillen leveren terechte resterende gevallen op. "Drenken" hoort
te blijven staan waar de regen de aarde drenkt, en "vellen" waar bomen geveld
worden. Een script kan dat verschil niet zien, een lezer wel.

Draaien vanuit de repo-root:  python scripts/audit_principes.py
                              python scripts/audit_principes.py --snel
Geeft exitcode 1 als er iets gevonden is, zodat het in een controle past.
"""
import json
import os
import re
import sys
import glob
import collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAD = os.path.join(ROOT, "data", "wijzigingsprincipes.json")

# Woorden die in een bronwoord staan maar niets zeggen over de woordfamilie.
STOPWOORDEN = {
    "de", "het", "een", "der", "des", "den", "die", "dat", "deze", "dezen",
    "en", "of", "in", "op", "tot", "van", "voor", "met", "te", "ten", "ter",
    "zijn", "haar", "hun", "uw", "mijn", "hij", "zij", "gij", "u", "ik", "wij",
    "is", "was", "waren", "zal", "zult", "zullen", "niet", "ook", "als", "dan",
    "overig", "overige", "alle", "al", "men", "er", "aan", "bij", "naar", "uit",
}

# Achtervoegsels die we van een woord afhalen om bij de stam te komen. Van lang
# naar kort, want "geboorten" moet eerst "ten" verliezen en niet meteen "n".
UITGANGEN = ("tten", "nden", "den", "ten", "sen", "nen", "eren", "ende",
             "de", "te", "en", "er", "st", "s", "e", "t", "n")

MIN_STAM = 5


def norm(s):
    return re.sub(r"\s+", " ", (s or "").strip().lower())


def stam(woord):
    """Ruwe stam: haal er één Nederlandse uitgang af, als er genoeg overblijft."""
    w = woord.lower()
    for u in UITGANGEN:
        if w.endswith(u) and len(w) - len(u) >= MIN_STAM:
            return w[: -len(u)]
    return w


def kernwoord(zin):
    """Het langste inhoudswoord uit een bronwoord; daar hangt de familie aan."""
    woorden = [w for w in re.findall(r"[a-zà-ÿ]+", (zin or "").lower())
               if w not in STOPWOORDEN and len(w) >= MIN_STAM]
    return max(woorden, key=len) if woorden else None


def kaal(s):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", s or ""))


def woorden(s):
    return re.findall(r"[a-zà-ÿ]+", (s or "").lower())


def lees_corpus():
    """Alle verzen plus een woordindex.

    De index is nodig voor de snelheid: zonder index moet elk van de ruim
    duizend principes langs alle verzen, en dat loopt in de miljoenen
    zoekacties. Met een gesorteerde woordenlijst is een stam opzoeken een
    kwestie van bisect.

    In de index staan alleen woorden die in datzelfde vers óók in de
    1888-tekst voorkomen. Dat is de eerstelijnsregel: wat een ánder principe
    heeft opgeleverd telt niet mee als achtergebleven bronwoord.
    """
    verzen = []
    index = collections.defaultdict(list)
    for pad in sorted(glob.glob(os.path.join(ROOT, "data", "*", "*.json"))):
        boek = os.path.basename(os.path.dirname(pad))
        try:
            d = json.load(open(pad, encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(d, dict) or "verses" not in d:
            continue
        hs = d.get("number")
        rij = d["verses"]
        rij = rij if isinstance(rij, list) else list(rij.values())
        for v in rij:
            if not isinstance(v, dict) or "text2026" not in v:
                continue
            sv, ov = kaal(v.get("textSV1888")), kaal(v.get("text2026"))
            i = len(verzen)
            verzen.append((boek, hs, v.get("number"), sv, ov))
            sv_w = set(woorden(sv))
            for w in set(woorden(ov)) & sv_w:
                index[w].append(i)
    return verzen, index, sorted(index)


def half_toegepast(principes, verzen, index, vocab, toon=30):
    """5) Staat er nog een andere verbuiging van een vervangen bronwoord?

    Twee soorten principes moeten hier buiten blijven, anders verdrinkt de
    melding in ruis:

    * Een verbuigingswijziging, waarbij het bronwoord en de uitkomst dezelfde
      stam delen — "jaren oud" wordt "jaar oud", "priesteren" wordt
      "priesters". Dat andere vormen van datzelfde woord blijven staan is
      juist de bedoeling.
    * Een principe met een bereik. Dat is met opzet tot een paar plaatsen
      beperkt; dat het woord elders blijft staan is geen fout maar de afspraak.
      Controle 6 kijkt of dat bereik wél is nagekomen.

    Wat overblijft is de echte vraag: dit woord is als verouderd afgevoerd —
    waarom staat een andere vorm ervan er dan nog?
    """
    import bisect

    bevindingen = []
    gezien = {}
    for p in principes:
        if p.get("bereik"):
            continue
        kern = kernwoord(p.get("oud"))
        if not kern:
            continue
        st = stam(kern)
        if len(st) < MIN_STAM:
            continue
        # deelt de uitkomst de stam? dan is het een verbuiging, geen vervanging
        if any(w.startswith(st) or st.startswith(stam(w))
               for w in woorden(p.get("nieuw"))):
            continue
        gezien.setdefault(st, []).append(p["id"])

    for st, ids in gezien.items():
        i = bisect.bisect_left(vocab, st)
        rest = collections.Counter()
        plek = collections.defaultdict(list)
        while i < len(vocab) and vocab[i].startswith(st):
            w = vocab[i]
            rest[w] = len(index[w])
            for j in index[w][:3]:
                b, hs, vs, _, _ = verzen[j]
                plek[w].append(f"{b} {hs}:{vs}")
            i += 1
        if rest:
            bevindingen.append((sum(rest.values()), st, ids, rest, plek))

    # Klein eerst: één of twee achterblijvers is het klassieke gemiste-verbuiging
    # patroon (vlade naast vladen). Grote aantallen zijn meestal een homoniem.
    bevindingen.sort(key=lambda b: b[0])
    print(f"\nhalf toegepast — bronwoord staat nog in een andere verbuiging: "
          f"{len(bevindingen)} woordfamilies (kleinste eerst)")
    for totaal, st, ids, rest, plek in bevindingen[:toon]:
        vormen = ", ".join(f"{w} ({c}x)" for w, c in rest.most_common(4))
        eerste = rest.most_common(1)[0][0]
        print(f"  {','.join(ids[:3]):16} '{st}-' {totaal}x: {vormen}")
        print(f"                   bijv. {', '.join(plek[eerste])}")
    if len(bevindingen) > toon:
        print(f"  ... en nog {len(bevindingen) - toon} woordfamilies met meer "
              f"vindplaatsen; die zijn vaker een homoniem dan half werk")
    return bevindingen


def bereik_nagelopen(principes, verzen):
    """6) Principes met een bereik: binnen niet gedaan, of buiten wél gedaan."""
    per_vers = {(b, hs, vs): (sv, ov) for b, hs, vs, sv, ov in verzen}
    meldingen = []

    for p in principes:
        ber = p.get("bereik")
        if not ber:
            continue
        kern_oud = kernwoord(p.get("oud"))
        kern_nieuw = kernwoord(p.get("nieuw"))
        if not kern_oud:
            continue
        pat_oud = re.compile(r"\b" + re.escape(stam(kern_oud)) + r"[a-zà-ÿ]*\b", re.I)
        pat_nieuw = (re.compile(r"\b" + re.escape(stam(kern_nieuw)) + r"[a-zà-ÿ]*\b", re.I)
                     if kern_nieuw else None)

        binnen, boeken = set(), set()
        for boek, plaatsen in (ber or {}).items():
            boeken.add(boek.lower())
            # Een boek zonder hoofdstukken (null of een lege lijst) betekent
            # "het hele boek". Wie dat als een leeg bereik leest, meldt elke
            # toepassing in dat boek als "buiten bereik" — precies andersom.
            if not plaatsen:
                binnen.update(k for k in per_vers if k[0] == boek.lower())
                continue
            for x in plaatsen:
                if isinstance(x, int):
                    binnen.update(k for k in per_vers if k[0] == boek.lower() and k[1] == x)
                else:
                    hs, _, vs = str(x).partition(":")
                    if vs:
                        binnen.add((boek.lower(), int(hs), int(vs)))
                    else:
                        binnen.update(k for k in per_vers
                                      if k[0] == boek.lower() and k[1] == int(hs))

        # 6a) binnen het bereik staat het bronwoord er nog
        for k in sorted(binnen):
            if k not in per_vers:
                continue
            sv, ov = per_vers[k]
            if pat_oud.search(ov) and pat_oud.search(sv):
                meldingen.append((p["id"], "binnen bereik niet toegepast",
                                  f"{k[0]} {k[1]}:{k[2]}", ov[:80]))

        # 6b) buiten het bereik staat de uitkomst er wél, terwijl 1888 het
        #     bronwoord had — dan is het principe verder gegaan dan afgesproken
        if pat_nieuw:
            for k, (sv, ov) in per_vers.items():
                if k[0] not in boeken or k in binnen:
                    continue
                if pat_nieuw.search(ov) and pat_oud.search(sv):
                    meldingen.append((p["id"], "buiten bereik wél toegepast",
                                      f"{k[0]} {k[1]}:{k[2]}", ov[:80]))

    print(f"\nbereik niet nagekomen: {len(meldingen)}")
    for pid, wat, waar, tekst in meldingen[:20]:
        print(f"  {pid} — {wat} — {waar}")
        print(f"       {tekst}")
    if len(meldingen) > 20:
        print(f"  ... en nog {len(meldingen) - 20}")
    return meldingen


def main():
    snel = "--snel" in sys.argv
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

    # 5 en 6 leggen de principes naast de tekst. Dat kost een paar seconden
    # inlezen, dus met --snel blijft alleen de controle op de principes over.
    if not snel:
        verzen, index, vocab = lees_corpus()
        print(f"\ntekst ingelezen: {len(verzen)} verzen, {len(vocab)} woorden")
        half_toegepast(principes, verzen, index, vocab)
        problemen += len(bereik_nagelopen(principes, verzen))
        print("\nDe woordfamilies hierboven zijn meldingen, geen fouten: homoniemen")
        print("en betekenisverschillen horen erbij. Loop ze na, tel ze niet.")

    print(f"\n{'GEEN PROBLEMEN' if problemen == 0 else str(problemen) + ' PUNT(EN) OM NA TE LOPEN'}")
    return 1 if problemen else 0


if __name__ == "__main__":
    sys.exit(main())
