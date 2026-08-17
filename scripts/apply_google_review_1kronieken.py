#!/usr/bin/env python3
"""Verwerk de menselijke tekst- en citaatreview van 1 Kronieken."""
from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from apply_citations_2koningen import markeer, zonder_spraak
from sweep_principe import kaal, lees, nieuwe_diff, schrijf
from synchroniseer_opmaak import bijtrekken


CORRECTIES = {
    (1, 43): [("eer er een koning", "voordat er een koning")],
    (4, 23): [("wonende bij", "wonend bij")],
    (4, 38): [("zijnde vorsten", "waren vorsten")],
    (9, 22): [("uitgelezen waren", "uitgekozen waren")],
    (12, 17): [("tegelijk over u zijn", "één met u zijn")],
    (12, 30): [("kloeke helden", "strijdbare helden"), ("vaderen", "vaders")],
    (13, 2): [("overige broers", "overige broeders")],
    (14, 10): [("Toen vraagde David", "Toen vroeg David")],
    (15, 13): [("een scheur gedaan", "een straf gegeven")],
    (16, 3): [("een bol broods", "een rond brood")],
    (16, 22): [("Tas Mijn", "Raak Mijn")],
    (18, 8): [("zeer veel kopers", "zeer veel koper")],
    (20, 1): [("ten tijde van de wederkomst van het jaar", "ten tijde van het aanbreken van het nieuwe jaar")],
    (20, 2): [("zeer veel roofs", "zeer veel roof")],
    (21, 8): [("zottelijk", "dwaas")],
    (21, 20): [("verstaken zich", "verborgen zich")],
    (21, 28): [("Ter zelfder tijd", "In die tijd")],
    (28, 11): [("een voorbeeld", "een ontwerp")],
    (28, 12): [("En een voorbeeld", "En een ontwerp")],
    (29, 28): [("goeden ouderdom", "goede ouderdom")],
}

GLOBALE_PRINCIPEPAREN = {
    ("kloeke helden", "strijdbare helden"),
    ("vaderen", "vaders"),
    ("zottelijk", "dwaas"),
    ("verstaken zich", "verborgen zich"),
    ("ter zelfder tijd", "in die tijd"),
    ("ten tijde van de wederkomst van het jaar", "ten tijde van het aanbreken van het nieuwe jaar"),
}


# "heel" markeert de volledige zichtbare verstekst. Vertelling blijft bewust
# buiten de bereiken, ook wanneer een oud citaat over meerdere verzen doorliep.
CITATEN = {
    (10, 5): [],
    (11, 1): [("mens", "Zie, wij zijn", "uw vlees.")],
    (11, 2): [("mens", "Zelfs ook", "tot u gezegd:"), ("god", "U zult Mijn", "Mijn volk Israël.")],
    (11, 5): [("mens", "U zult hier", "niet inkomen.")],
    (11, 17): [("mens", "Wie zal mij", "de poort is?")],
    (11, 19): [("mens", "Dat late mijn God", "zij dat gebracht.")],
    (12, 17): [("mens", "Als u ten vrede", "en straffe het!")],
    (12, 18): [("mens", "Wij zijn uw", "uw God helpt u.")],
    (13, 4): [],
    (13, 12): [("mens", "Hoe zal ik", "tot mij brengen?")],
    (14, 10): [("mens", "Zal ik optrekken", "in mijn hand geven?"), ("god", "Trek op", "in uw hand geven.")],
    (14, 11): [("mens", "God heeft mijn", "van de wateren;")],
    (14, 12): [], (14, 13): [],
    (15, 2): [("mens", "Niemand mag", "de eeuwigheid.")],
    **{(15, nummer): [] for nummer in range(3, 12)},
    (15, 12): [("mens", "U bent familiehoofden", "bereid heb.")],
    (15, 13): "heel",
    **{(15, nummer): [] for nummer in range(14, 25)},
    **{(16, nummer): "heel" for nummer in range(8, 36)},
    (16, 36): [("mens", "Geloofd zij JAHWEH", "tot eeuwigheid!"), ("mens", "Amen!", "Amen!")],
    (17, 1): [("mens", "Zie, ik woon", "onder gordijnen.")],
    (17, 3): [],
    (19, 2): [("mens", "Ik zal goedertierenheid", "aan mij gedaan.")],
    (19, 12): "heel",
    (21, 4): [], (21, 5): [], (21, 6): [], (21, 7): [], (21, 14): [],
    (21, 15): [("god", "Het is genoeg", "uw hand af.")],
    (21, 16): [], (21, 18): [], (21, 19): [], (21, 20): [], (21, 26): [],
    (21, 27): [], (21, 28): [], (21, 29): [], (21, 30): [],
    (22, 1): [("mens", "Hier zal", "Israël zijn.")],
    (22, 2): [], (22, 3): [], (22, 4): [],
    (22, 5): [("mens", "Mijn zoon Salomo", "voorraad bereiden.")],
    (22, 6): [],
    (22, 7): [("mens", "Mijn zoon", "een huis te bouwen;")],
    (22, 8): [("god", "U hebt bloed", "vergoten hebt.")],
    (22, 9): "heel", (22, 10): "heel",
    **{(22, nummer): "heel" for nummer in range(11, 17)},
    (22, 17): [], (22, 18): "heel", (22, 19): "heel",
    (23, 25): [("mens", "JAHWEH, de God", "tot in eeuwigheid.")],
    (29, 1): [("mens", "God heeft mijn", "God, JAHWEH.")],
    (29, 2): "heel", (29, 3): "heel", (29, 4): "heel", (29, 5): "heel",
    (29, 20): [("mens", "Loof nu", "uw God!")],
}


def norm(tekst: str) -> str:
    return re.sub(r"\s+", " ", tekst.strip().lower())


def registreer_principes():
    pad = ROOT / "data" / "wijzigingsprincipes.json"
    data = json.loads(pad.read_text(encoding="utf-8"))
    data["principes"] = [item for item in data["principes"] if not item.get("id", "").startswith("MR-1KR-")]
    ids = {}
    nummer = 1
    for (hoofdstuk, vers), paren in sorted(CORRECTIES.items()):
        for oud, nieuw in paren:
            principe_id = f"MR-1KR-{nummer:03d}"
            nummer += 1
            ids[(norm(oud), norm(nieuw))] = principe_id
            principe = {
                "id": principe_id,
                "categorie": "Menselijke review",
                "oud": oud,
                "nieuw": nieuw,
                "toelichting": "Contextueel beoordeeld tijdens de menselijke review van 1 Kronieken.",
                "regex": rf"\b{re.escape(oud)}\b" if (norm(oud), norm(nieuw)) in GLOBALE_PRINCIPEPAREN else "",
                "voorbeeld": f"1 Kronieken {hoofdstuk}:{vers}",
                "bron": "menselijke-review",
            }
            if (norm(oud), norm(nieuw)) not in GLOBALE_PRINCIPEPAREN:
                principe["bereik"] = {"1kronieken": [f"{hoofdstuk}:{vers}"]}
            data["principes"].append(principe)
    pad.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return ids


def verwerk_tekstcorrecties(ids):
    per_hoofdstuk = defaultdict(list)
    for (hoofdstuk, vers), paren in CORRECTIES.items():
        per_hoofdstuk[hoofdstuk].append((vers, paren))
    for hoofdstuk, opdrachten in per_hoofdstuk.items():
        pad = ROOT / "data" / "1kronieken" / f"{hoofdstuk}.json"
        data, vorm = lees(str(pad))
        per_vers = {item["number"]: item for item in data["verses"]}
        for vers, paren in opdrachten:
            item = per_vers[vers]
            origineel = item["text2026"]
            tekst = origineel
            for oud, nieuw in paren:
                patroon = re.compile(rf"(?<!\w){re.escape(oud)}(?!\w)")
                if patroon.search(tekst):
                    tekst = patroon.sub(nieuw, tekst)
                elif not re.search(rf"(?<!\w){re.escape(nieuw)}(?!\w)", tekst):
                    raise ValueError(f"1 Kronieken {hoofdstuk}:{vers}: {oud!r} niet gevonden")
            if tekst != origineel:
                item["text2026"] = tekst
                html = bijtrekken(item["text2026_html"], tekst)
                if html is None or kaal(html) != kaal(tekst):
                    raise ValueError(f"HTML kon niet worden bijgewerkt: 1 Kronieken {hoofdstuk}:{vers}")
                item["text2026_html"] = html
                item["phraseDiff"] = nieuwe_diff(
                    kaal(item["textSV1888"]), kaal(tekst), item.get("phraseDiff", []),
                    None, f"1kronieken {hoofdstuk}:{vers}",
                )
            for oud, nieuw in paren:
                principe_id = ids[(norm(oud), norm(nieuw))]
                verschillen = item.setdefault("phraseDiff", [])
                if not any(diff.get("principe") == principe_id for diff in verschillen):
                    verschil = next((
                        diff for diff in verschillen
                        if norm(nieuw) in norm(diff.get("new", "")) and not diff.get("principe")
                    ), None)
                    if verschil is None:
                        verschil = {"old": oud, "new": nieuw}
                        verschillen.append(verschil)
                    verschil["principe"] = principe_id
        schrijf(str(pad), data, vorm)


def verwerk_citaten():
    per_hoofdstuk = defaultdict(dict)
    for (hoofdstuk, vers), bereiken in CITATEN.items():
        per_hoofdstuk[hoofdstuk][vers] = bereiken
    for hoofdstuk, opdrachten in per_hoofdstuk.items():
        pad = ROOT / "data" / "1kronieken" / f"{hoofdstuk}.json"
        data, vorm = lees(str(pad))
        for item in data["verses"]:
            if item["number"] not in opdrachten:
                continue
            bereiken = opdrachten[item["number"]]
            if bereiken == "heel":
                bereiken = [("mens", item["text2026"], item["text2026"])]
                if hoofdstuk == 22 and item["number"] in (9, 10):
                    bereiken = [("god", item["text2026"], item["text2026"])]
            oud = item["text2026_html"]
            basis = zonder_spraak(oud)
            nieuw = markeer(basis, bereiken) if bereiken else basis
            if kaal(oud) != kaal(nieuw):
                raise ValueError(f"Citaat wijzigde tekst: 1 Kronieken {hoofdstuk}:{item['number']}")
            item["text2026_html"] = nieuw
        schrijf(str(pad), data, vorm)


def verwerk_reuzenverwijzing():
    pad = ROOT / "data" / "begrippenlijst-1kronieken.json"
    data = json.loads(pad.read_text(encoding="utf-8"))
    item = next(item for item in data if item.get("woord") == "reuzen")
    item["ref"] = "1 Kron 20:4-8"
    pad.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    ids = registreer_principes()
    verwerk_tekstcorrecties(ids)
    verwerk_citaten()
    verwerk_reuzenverwijzing()


if __name__ == "__main__":
    main()
