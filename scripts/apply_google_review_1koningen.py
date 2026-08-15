#!/usr/bin/env python3
"""Verwerk uitsluitend eenduidige Google-opmerkingen voor 1 Koningen."""

from __future__ import annotations

import sys
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from sweep_principe import kaal, lees, nieuwe_diff, schrijf  # noqa: E402
from synchroniseer_opmaak import bijtrekken  # noqa: E402


CORRECTIES = {
    (1, 9): [("noodde", "nodigde")],
    (1, 10): [("noodde hij niet", "nodigde hij niet uit")],
    (1, 49): [("ieder zijns weegs", "ieder zijn eigen weg")],
    (3, 9): [("Uw zwaar volk", "Uw machtig volk")],
    (3, 20): [("haar doden zoon", "haar dode zoon")],
    (3, 26): [("haar binnenste ontstak over haar zoon", "haar moederhart brandde van medelijden om haar zoon")],
    (4, 23): [("uitgenomen", "uitgezonderd")],
    (5, 4): [("bejegening van kwaad", "bedreiging")],
    (5, 10): [("cederenhout", "cederhout")],
    (5, 13): [
        (
            "deed een uitschot opkomen uit geheel Isra\u00ebl; en het uitschot was dertig duizend man",
            "legde heel Isra\u00ebl een herendienst op; de herendienst bestond uit dertig duizend man",
        )
    ],
    (5, 14): [("Adoniram was over dit uitschot", "Adoniram had de leiding over deze herendienst")],
    (6, 4): [("vensteren", "vensters")],
    (6, 5): [("zijkameren", "zijkamers")],
    (6, 11): [("gebeurde het woord", "kwam het woord")],
    (6, 21): [("overtoog", "overtrok")],
    (7, 17): [("nettenwerk", "vlechtwerk")],
    (7, 20): [("appelen", "appels")],
    (7, 23): [("gegotene", "gegoten")],
    (7, 28): [("werk der stelling", "werk van het onderstel")],
    (7, 30): [("stelling", "onderstel"), ("schouders", "steunen")],
    (7, 32): [("aan de stelling", "aan het onderstel")],
    (7, 34): [
        ("ener stelling", "van een onderstel"),
        ("uit de stelling", "uit het onderstel"),
        ("schouders", "steunen"),
    ],
    (7, 35): [
        ("ener stelling", "van een onderstel"),
        ("der stelling", "van het onderstel"),
    ],
    (7, 37): [("stellingen", "onderstellen")],
    (7, 38): [("op elke stelling", "op elk onderstel"), ("stellingen", "onderstellen")],
    (7, 39): [("stellingen", "onderstellen")],
    (7, 43): [("stellingen", "onderstellen")],
    (7, 45): [("schoffelen", "scheppen")],
    (7, 47): [("zeer grote menigte", "zeer grote hoeveelheid")],
    (7, 50): [("gaffelen", "messen"), ("herren", "scharnieren")],
    (8, 5): [("hele vergadering", "hele gemeenschap")],
    (8, 19): [("uit uw lendenen", "uit uw lichaam")],
    (9, 15): [
        (
            "Dit is nu de oorzaak van het uitschot, dat de koning Salomo deed opkomen, om",
            "Dit is de reden waarom koning Salomo herendienst oplegde: om",
        )
    ],
    (9, 21): [
        ("heeft Salomo gebracht op slaafsen uitschot", "heeft Salomo tot slavenarbeid verplicht")
    ],
    (10, 15): [("kramers", "marskramers"), ("geweldigen", "landvoogden")],
    (10, 16): [
        ("rondassen", "grote schilden"),
        ("elke rondas", "elk groot schild"),
        ("gouds", "goud"),
    ],
    (10, 17): [("gouds", "goud")],
    (10, 18): [("Nog", "Ook"), ("overtoog", "overtrok")],
    (10, 20): [("in geen koninkrijken", "in geen enkel koninkrijk")],
    (11, 1): [("vreemde vrouwen", "buitenlandse vrouwen")],
    (11, 7): [
        ("de gruwel van de Moabieten", "de afschuwelijke afgod van de Moabieten"),
        ("de gruwel van de kinderen Ammons", "de afschuwelijke afgod van de kinderen Ammons"),
    ],
    (12, 21): [("uitgelezenen", "beste manschappen")],
    (12, 22): [("woord van God gebeurde", "woord van God kwam")],
    (12, 32): [("van gelijken deed hij", "zo deed hij")],
    (13, 12): [("getogen", "gegaan")],
    (13, 20): [("woord van JAHWEH gebeurde", "woord van JAHWEH kwam")],
    (13, 22): [("uw vaderen graf", "het graf van uw vader")],
    (13, 30): [
        ("maakten over hem een weeklage", "bedreven rouw over hem"),
        ("mijn broer", "mijn broeder"),
    ],
    (14, 5): [("aangaande haar zoon", "inzake haar zoon")],
    (14, 19): [("hoe hij gekrijgd", "hoe hij gevochten")],
    (15, 12): [("zijn vaders gemaakt hadden", "zijn vader gemaakt had")],
    (15, 27): [("maakte een verbintenis tegen hem", "smeedde een samenzwering tegen hem")],
    (16, 1): [("Toen gebeurde het woord van JAHWEH", "Toen kwam het woord van JAHWEH")],
    (16, 9): [("maakte een verbintenis tegen hem", "smeedde een samenzwering tegen hem")],
    (16, 26): [("verwekkende JAHWEH", "en verwekte JAHWEH")],
    (17, 1): [("inwoneren van Gilead", "inwoners van Gilead")],
    (17, 2): [("Daarna gebeurde het woord van JAHWEH", "Daarna kwam het woord van JAHWEH")],
    (17, 8): [("Toen gebeurde het woord van JAHWEH", "Toen kwam het woord van JAHWEH")],
    (17, 12): [("hand vol meels", "hand vol meel")],
    (18, 30): [("heelde het altaar", "herstelde het altaar")],
    (19, 2): [("morgen ongeveer deze tijd", "morgen om deze tijd")],
    (19, 18): [("alle knieën", "knieën")],
    (20, 32): [("mijn broer", "mijn broeder")],
    (20, 43): [("gemelijk en boos", "somber gestemd en boos")],
    (21, 4): [("gemelijk en boos", "geïrriteerd en boos")],
    (21, 10): [("God en de koning gezegend", "God en de koning vaarwel gezegd")],
    (21, 13): [("God en de koning gezegend", "God en de koning vaarwel gezegd")],
    (22, 25): [("u te versteken", "u te verbergen")],
    (22, 30): [("mij versteld heb", "mij vermomd heb"), ("verstelde zich", "vermomde zich")],
}


# Een aantal nieuwe woordvervangingen ligt naast een oudere wijziging. De
# standaardwoorddiff voegt zulke blokken soms samen; deze expliciete koppelingen
# bewaren dan de herkomst van de eerdere wijziging.
TE_BEHOUDEN_KOPPELINGEN = [
    (10, 16, "sikkelen", "sikkels", "V941"),
    (10, 18, "denzelven", "die", "N4"),
    (10, 18, "elpenbenen", "ivoren", "V913"),
    (16, 9, "der wagenen", "van de wagens", "N2"),
    (16, 26, "den HEERE, den", "JAHWEH, de", "N1"),
    (19, 2, "omtrent dezen", "om deze", "N4"),
    (20, 43, "toog henen", "trok heen", "V67"),
    (22, 30, "Alzo", "Zo", "V42"),
]

CORPUS_KOPPELINGEN = [
    ("1koningen", 21, 17, "Doch", "Maar", "V1"),
    ("1kronieken", 22, 8, "Doch", "Maar", "V1"),
    ("2kronieken", 11, 2, "Doch", "Maar", "V1"),
    ("ezechiel", 13, 1, "des HEEREN", "het", "N3"),
    ("ezechiel", 15, 1, "des HEEREN", "het", "N3"),
    ("ezechiel", 17, 1, "des HEEREN", "het", "N3"),
    ("ezechiel", 21, 1, "des HEEREN", "het", "N3"),
    ("ezechiel", 25, 1, "des HEEREN", "het", "N3"),
    ("ezechiel", 33, 1, "des HEEREN", "het", "N3"),
    ("ezechiel", 34, 1, "des HEEREN", "het", "N3"),
    ("jeremia", 1, 13, "des HEEREN", "het", "N3"),
    ("jeremia", 2, 1, "des HEEREN", "het", "N3"),
    ("jeremia", 16, 1, "des HEEREN", "het", "N3"),
    ("jeremia", 28, 12, "Doch des HEEREN", "Maar het", "N3"),
    ("jeremia", 33, 19, "des HEEREN", "het", "N3"),
    ("zacharia", 6, 9, "des HEEREN", "het", "N3"),
]


def pas_tekst_aan(vers, vervangingen, referentie):
    """Pas exacte vervangingen toe en behoud de zichtbare HTML-opmaak."""
    nieuw = vers["text2026"]
    # Normaliseer een eventuele herhaalde prefix uit een oudere,
    # niet-idempotente uitvoering van kramers -> marskramers.
    nieuw = re.sub(r"\b(?:mars)+kramers\b", "marskramers", nieuw)
    for oud, vervang in vervangingen:
        if vervang in nieuw:
            continue
        if oud not in nieuw:
            raise ValueError(f"{referentie}: niet gevonden: {oud!r}")
        nieuw = nieuw.replace(oud, vervang)

    if nieuw == vers["text2026"]:
        return False
    html = bijtrekken(vers["text2026_html"], nieuw)
    if html is None or kaal(html) != kaal(nieuw):
        raise ValueError(f"{referentie}: HTML kon niet veilig worden bijgewerkt")
    vers["text2026"] = nieuw
    vers["text2026_html"] = html
    vers["phraseDiff"] = nieuwe_diff(
        kaal(vers["textSV1888"]),
        kaal(nieuw),
        vers.get("phraseDiff", []),
        None,
        referentie.lower(),
    )
    return True


def voeg_dubbelhartigheid_toe(data):
    """Voeg de eerste expliciete verwijzing voor het onderwerp toe."""
    tags = data.setdefault("tags", [])
    tag = next((item for item in tags if item.get("id") == "dubbelhartigheid"), None)
    if tag is None:
        tag = {
            "id": "dubbelhartigheid",
            "naam": "Dubbelhartigheid",
            "beschrijving": "Een verdeelde toewijding aan JAHWEH en andere wegen.",
            "kleur": "#8b5e3c",
            "verzen": [],
        }
        tags.append(tag)
    refs = {item.get("ref") for item in tag["verzen"]}
    if "1koningen 3:3" not in refs:
        tag["verzen"].append({"ref": "1koningen 3:3", "rang": 1})
    return tag


def voeg_zaaien_en_oogsten_toe(data):
    """Koppel Salomo's gebed over rechtvaardig vergelding aan het onderwerp."""
    tag = next(
        (item for item in data.get("tags", []) if item.get("id") == "zaaien-en-oogsten"),
        None,
    )
    if tag is None:
        raise ValueError("Onderwerp 'zaaien-en-oogsten' ontbreekt in data/tags.json")
    if "1koningen 8:32" not in {item.get("ref") for item in tag["verzen"]}:
        tag["verzen"].append({"ref": "1koningen 8:32", "rang": 1})
    return tag


def voeg_reviewtags_toe(data):
    """Leg de inhoudelijke koppelingen uit de 1 Koningen-review vast."""
    definities = {
        "straf-in-dit-leven": {
            "naam": "Gods straf in dit leven",
            "beschrijving": "Teksten waarin Gods oordeel al tijdens het aardse leven zichtbaar wordt.",
            "kleur": "#9a594f",
            "refs": [
                "genesis 3:17", "numeri 16:32", "jozua 7:25", "1samuel 5:6",
                "1koningen 11:14", "2koningen 17:18", "handelingen 5:5",
                "handelingen 12:23", "1korinthiers 11:30", "openbaring 2:22",
            ],
        },
        "verloren-bijbelse-bronnen": {
            "naam": "Niet-bewaarde geschriften die de Bijbel noemt",
            "beschrijving": "Geschriften waarnaar de Bijbel verwijst, maar waarvan geen zelfstandige tekst is overgeleverd.",
            "kleur": "#6d7890",
            "refs": [
                "numeri 21:14", "jozua 10:13", "1koningen 11:41", "1kronieken 29:29",
                "2kronieken 9:29", "2kronieken 12:15", "2kronieken 20:34",
                "2kronieken 24:27", "2kronieken 26:22", "2kronieken 33:19",
            ],
        },
        "boze-geesten": {
            "naam": "Boze geesten",
            "beschrijving": "Teksten over boze en misleidende geesten en hun werking.",
            "kleur": "#66526f",
            "refs": [
                "richteren 9:23", "1samuel 16:14", "1samuel 18:10", "1samuel 19:9",
                "1koningen 22:19", "1koningen 22:20", "1koningen 22:21",
                "1koningen 22:22", "1koningen 22:23", "1koningen 22:24",
                "mattheus 8:16", "markus 5:2", "lukas 8:2", "handelingen 16:16",
                "efeziers 6:12",
            ],
        },
    }
    tags = data.setdefault("tags", [])
    for ident, definitie in definities.items():
        tag = next((item for item in tags if item.get("id") == ident), None)
        if tag is None:
            tag = {
                "id": ident,
                "naam": definitie["naam"],
                "beschrijving": definitie["beschrijving"],
                "kleur": definitie["kleur"],
                "verzen": [],
            }
            tags.append(tag)
        bestaand = {item.get("ref") for item in tag["verzen"]}
        for ref in definitie["refs"]:
            if ref not in bestaand:
                tag["verzen"].append({"ref": ref, "rang": 2})

    vals = next(item for item in tags if item.get("id") == "valse-profetie")
    bestaand = {item.get("ref") for item in vals["verzen"]}
    for nummer in range(2, 13):
        ref = f"1koningen 22:{nummer}"
        if ref not in bestaand:
            vals["verzen"].append({"ref": ref, "rang": 2})


def pas_2kronieken_8_8_aan():
    """Houd de parallel bij Salomo's herendienst in 2 Kronieken gelijk."""
    pad = ROOT / "data" / "2kronieken" / "8.json"
    data, vorm = lees(str(pad))
    vers = next(item for item in data["verses"] if item["number"] == 8)
    gewijzigd = pas_tekst_aan(
        vers,
        [("bracht Salomo op uitschot", "verplichtte Salomo tot slavenarbeid")],
        "2 Kronieken 8:8",
    )
    if gewijzigd:
        schrijf(str(pad), data, vorm)
    return gewijzigd


def behoud_aangrenzende_koppelingen():
    """Zet herkomstlabels terug die door een samengevoegde woorddiff vervielen."""
    per_hoofdstuk = {}
    for hoofdstuk, nummer, oud, nieuw, principe in TE_BEHOUDEN_KOPPELINGEN:
        per_hoofdstuk.setdefault(hoofdstuk, []).append((nummer, oud, nieuw, principe))

    toegevoegd = 0
    for hoofdstuk, koppelingen in per_hoofdstuk.items():
        pad = ROOT / "data" / "1koningen" / f"{hoofdstuk}.json"
        data, vorm = lees(str(pad))
        verzen = {item["number"]: item for item in data["verses"]}
        gewijzigd = False
        for nummer, oud, nieuw, principe in koppelingen:
            diffs = verzen[nummer].setdefault("phraseDiff", [])
            if principe in {item.get("principe") for item in diffs}:
                continue
            diffs.append({"old": oud, "new": nieuw, "principe": principe})
            toegevoegd += 1
            gewijzigd = True
        if gewijzigd:
            schrijf(str(pad), data, vorm)
    return toegevoegd


def behoud_corpuskoppelingen():
    """Herstel oudere labels die door de bredere profetische formule groepeerden."""
    toegevoegd = 0
    for boek, hoofdstuk, nummer, oud, nieuw, principe in CORPUS_KOPPELINGEN:
        pad = ROOT / "data" / boek / f"{hoofdstuk}.json"
        data, vorm = lees(str(pad))
        vers = next(item for item in data["verses"] if item["number"] == nummer)
        diffs = vers.setdefault("phraseDiff", [])
        if principe not in {item.get("principe") for item in diffs}:
            diffs.append({"old": oud, "new": nieuw, "principe": principe})
            schrijf(str(pad), data, vorm)
            toegevoegd += 1
    return toegevoegd


def main():
    per_hoofdstuk = {}
    for (hoofdstuk, nummer), vervangingen in CORRECTIES.items():
        per_hoofdstuk.setdefault(hoofdstuk, []).append((nummer, vervangingen))

    geraakt = 0
    for hoofdstuk, verscorrecties in per_hoofdstuk.items():
        pad = ROOT / "data" / "1koningen" / f"{hoofdstuk}.json"
        data, vorm = lees(str(pad))
        verzen = {item["number"]: item for item in data["verses"]}
        gewijzigd = False
        for nummer, vervangingen in verscorrecties:
            if pas_tekst_aan(verzen[nummer], vervangingen, f"1 Koningen {hoofdstuk}:{nummer}"):
                geraakt += 1
                gewijzigd = True
        if gewijzigd:
            schrijf(str(pad), data, vorm)
    if pas_2kronieken_8_8_aan():
        geraakt += 1

    tag_pad = ROOT / "data" / "tags.json"
    tags, vorm = lees(str(tag_pad))
    voeg_dubbelhartigheid_toe(tags)
    voeg_zaaien_en_oogsten_toe(tags)
    voeg_reviewtags_toe(tags)
    schrijf(str(tag_pad), tags, vorm)
    gekoppeld = behoud_aangrenzende_koppelingen()
    gekoppeld += behoud_corpuskoppelingen()
    print(f"{geraakt} verzen in 1 Koningen bijgewerkt; {gekoppeld} koppelingen behouden.")


if __name__ == "__main__":
    main()
