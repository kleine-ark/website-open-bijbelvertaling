#!/usr/bin/env python3
"""Bouw het corpusbrede onderwerp Engelen zonder de Bijbeltekst te wijzigen."""

from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
import re
from typing import Any, Iterable

try:
    from scripts.build_corpus_naslag import load_books, load_corpus
except ModuleNotFoundError:  # Direct uitgevoerd als `python scripts/...`.
    from build_corpus_naslag import load_books, load_corpus


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

HUMAN_MESSENGERS = {
    "markus 1:2": "Johannes de Doper is hier de menselijke bode uit de profetie.",
    "mattheus 11:10": "Johannes de Doper is hier de menselijke bode uit de profetie.",
    "lukas 7:27": "Johannes de Doper is hier de menselijke bode uit de profetie.",
    "maleachi 2:7": "De priester wordt hier als bode van JAHWEH aangeduid.",
    "4ezra 1:40": "Maleachi wordt hier als menselijke profeet met het woord engel aangeduid.",
}

CHURCH_ANGELS = {
    "openbaring 1:20", "openbaring 2:1", "openbaring 2:8",
    "openbaring 2:12", "openbaring 2:18", "openbaring 3:1",
    "openbaring 3:7", "openbaring 3:14",
}

# Deze verschijningen worden gepubliceerd omdat de tekst zelf een Engel noemt,
# maar zonder een theologische identiteit aan die Engel toe te kennen.
THEOPHANY_REFS = {
    "genesis 16:7", "genesis 16:9", "genesis 16:10", "genesis 16:11",
    "genesis 22:11", "genesis 22:15", "genesis 48:16",
    "exodus 3:2", "exodus 14:19", "exodus 23:20", "exodus 23:23",
    "exodus 32:34", "exodus 33:2", "psalmen 34:8", "psalmen 35:5",
    "psalmen 35:6", "jesaja 63:9", "hosea 12:5", "maleachi 3:1",
} | {f"richteren 13:{verse}" for verse in (3, 6, 9, 13, 15, 16, 17, 18, 20, 21, 22)}

FALSE_DEMON_REFERENCES = {
    "markus 8:33": "Petrus wordt aangesproken als satan; de identiteit is contextueel en niet letterlijk vastgelegd.",
    "johannes 6:70": "Judas wordt beeldend een duivel genoemd.",
    "johannes 7:20": "De menigte uit een beschuldiging die de tekst niet bevestigt.",
    "johannes 8:48": "De tegenstanders uiten een beschuldiging die de tekst niet bevestigt.",
    "johannes 8:49": "Jezus ontkent de voorafgaande beschuldiging.",
    "johannes 8:52": "De tegenstanders herhalen een beschuldiging die de tekst niet bevestigt.",
    "johannes 10:20": "Een deel van de menigte uit een beschuldiging.",
    "johannes 10:21": "De voorafgaande beschuldiging wordt weersproken.",
    "mattheus 16:23": "Petrus wordt aangesproken als satan; de identiteit is contextueel en niet letterlijk vastgelegd.",
    "handelingen 13:10": "Kind van de duivel is hier een karakterisering van een mens.",
}

SPIRITUAL_POWER_REFS = {
    "romeinen 8:38", "efeziers 1:21", "efeziers 3:10", "efeziers 6:12",
    "kolossenzen 1:16", "kolossenzen 2:10", "kolossenzen 2:15",
    "1petrus 3:22",
}

FALLEN_ANGEL_REFS = {
    "2petrus 2:4", "judas 1:6",
    "1meqabyan 18:3", "1meqabyan 18:5", "1meqabyan 18:7",
    "1meqabyan 19:4", "1meqabyan 19:10",
}

HEAVENLY_HOST_REFS = {
    "1koningen 22:19", "2kronieken 18:18", "psalmen 103:21",
    "psalmen 148:2", "lukas 2:13",
}

# Verzen waarin het hemelwezen uit de omliggende context blijkt, maar waarin
# niet ieder afzonderlijk vers opnieuw het woord engel gebruikt.
IMPLICIT_GROUPS: dict[str, tuple[str, str, str]] = {
    **{f"jesaja 6:{v}": ("serafim", "visioen-symboliek", "zeker") for v in range(1, 8)},
    **{f"ezechiel 1:{v}": ("cherubim", "visioen-symboliek", "waarschijnlijk") for v in range(4, 26)},
    **{f"ezechiel 3:{v}": ("cherubim", "visioen-symboliek", "waarschijnlijk") for v in range(12, 15)},
    **{f"ezechiel 10:{v}": ("cherubim", "visioen-symboliek", "zeker") for v in range(1, 23)},
    "ezechiel 11:22": ("cherubim", "visioen-symboliek", "zeker"),
    **{f"daniel 8:{v}": ("genoemde-engel", "visioen-symboliek", "waarschijnlijk") for v in range(15, 27)},
    **{f"daniel 9:{v}": ("genoemde-engel", "visioen-symboliek", "waarschijnlijk") for v in range(20, 24)},
    **{f"daniel 10:{v}": ("genoemde-engel", "visioen-symboliek", "waarschijnlijk") for v in range(5, 22)},
    **{f"daniel 12:{v}": ("hemelwezen-overig", "visioen-symboliek", "waarschijnlijk") for v in (1, 5, 6, 7)},
    **{f"lukas 24:{v}": ("engel", "verschijning-handeling", "waarschijnlijk") for v in range(4, 8)},
    **{f"handelingen 1:{v}": ("engel", "verschijning-handeling", "waarschijnlijk") for v in (10, 11)},
    **{f"openbaring 4:{v}": ("hemelwezen-overig", "visioen-symboliek", "zeker") for v in (6, 7, 8, 9)},
    **{f"openbaring 5:{v}": ("hemelwezen-overig", "visioen-symboliek", "zeker") for v in (6, 8, 11, 14)},
    **{f"openbaring 6:{v}": ("hemelwezen-overig", "visioen-symboliek", "zeker") for v in (1, 3, 5, 6, 7)},
    **{f"openbaring 7:{v}": ("hemelwezen-overig", "visioen-symboliek", "zeker") for v in (11,)},
    **{f"openbaring 14:{v}": ("hemelwezen-overig", "visioen-symboliek", "zeker") for v in (3,)},
    **{f"openbaring 15:{v}": ("hemelwezen-overig", "visioen-symboliek", "zeker") for v in (7,)},
    **{f"openbaring 19:{v}": ("hemelwezen-overig", "visioen-symboliek", "zeker") for v in (4,)},
}

UNCERTAIN_BEINGS = {
    "genesis 6:2": "De identiteit van de zonen van God is omstreden.",
    "genesis 6:4": "De identiteit van de zonen van God is omstreden.",
    "jozua 5:13": "De man met het uitgetrokken zwaard kan niet zonder interpretatie als engel worden vastgelegd.",
    "jozua 5:14": "De vorst van het leger van JAHWEH wordt niet expliciet engel genoemd.",
    "jozua 5:15": "De identiteit van de spreker wordt niet expliciet als engel vastgelegd.",
    "job 1:6": "De zonen van God worden vaak hemelwezens genoemd; de tekst gebruikt hier niet het woord engelen.",
    "job 2:1": "De zonen van God worden vaak hemelwezens genoemd; de tekst gebruikt hier niet het woord engelen.",
    "job 38:7": "De zonen van God worden vaak hemelwezens genoemd; de tekst gebruikt hier niet het woord engelen.",
    "psalmen 82:1": "De identiteit van de vergadering van goden is exegetisch omstreden.",
    "psalmen 82:6": "De identiteit van de aangesproken goden/zonen van de Allerhoogste is omstreden.",
    "handelingen 1:10": "De twee mannen in witte kleding worden niet in dit vers expliciet engelen genoemd.",
    "handelingen 1:11": "De twee mannen in witte kleding worden niet in dit vers expliciet engelen genoemd.",
}

ANGEL_RE = re.compile(r"(?<![0-9A-Za-zÀ-ÿ])engel(?:en|s)?(?![0-9A-Za-zÀ-ÿ])", re.I)
CHERUB_RE = re.compile(r"(?<![0-9A-Za-zÀ-ÿ])cherub(?:s|im)?(?![0-9A-Za-zÀ-ÿ])", re.I)
SERAPH_RE = re.compile(r"(?<![0-9A-Za-zÀ-ÿ])seraf(?:s|im)?(?![0-9A-Za-zÀ-ÿ])", re.I)
ARCHANGEL_RE = re.compile(r"(?<![0-9A-Za-zÀ-ÿ])(?:aartsengel|archangel)(?:en)?(?![0-9A-Za-zÀ-ÿ])", re.I)
DEMON_RE = re.compile(
    r"(?<![0-9A-Za-zÀ-ÿ])(?:demon(?:en)?|duivel(?:s)?|satan|"
    r"onreine geest(?:en)?|boze geest(?:en)?|boze geesten|engelen der duisternis)"
    r"(?![0-9A-Za-zÀ-ÿ])", re.I,
)
WATCHER_RE = re.compile(r"(?<![0-9A-Za-zÀ-ÿ])wakers?(?![0-9A-Za-zÀ-ÿ])", re.I)


def _review(ref: str, kind: str, note: str) -> dict[str, Any]:
    return {
        "ref": ref,
        "type": kind,
        "notitie": note,
        "reviewStatus": "agent-reviewed-needs-human-review",
        "humanReviewed": False,
    }


def _display_type(book_id: str, text: str, subcategory: str) -> str:
    lowered = text.casefold()
    if book_id in {"zacharia", "ezechiel", "daniel", "openbaring", "henoch", "4ezra"}:
        return "visioen-symboliek"
    if any(word in lowered for word in ("visioen", "gezicht", "droom", "ik zag", "ik hoorde")):
        return "visioen-symboliek"
    if subcategory in {"geestelijke-machten"} or any(
        word in lowered for word in ("weet u niet", "zijn engelen", "de engelen zijn", "tot de engelen")
    ):
        return "onderwijs"
    return "verschijning-handeling"


def _named_angel(text: str, ref: str) -> bool:
    lowered = text.casefold()
    book = ref.split(" ", 1)[0]
    if "gabriël" in lowered or "gabriel" in lowered:
        return book != "tobit" or ref not in {"tobit 1:16", "tobit 4:21"}
    if "rafaël" in lowered or "rafael" in lowered:
        return book in {"tobit", "henoch", "1meqabyan"} and not ref.startswith("tobit 1:")
    if "uriël" in lowered or "uriel" in lowered:
        return book in {"4ezra", "henoch"}
    if "michaël" in lowered or "michael" in lowered:
        return book in {"daniel", "judas", "openbaring", "henoch", "1meqabyan", "3meqabyan"}
    return any(name in lowered for name in ("fanuël", "fanuel", "suryan", "uryan", "remiël", "remiel", "sarqaël")) and book == "henoch"


def _make_mention(ref: str, subcategory: str, display: str, certainty: str, rank: int = 2) -> dict[str, Any]:
    return {
        "ref": ref,
        "rang": rank,
        "subcategorie": subcategory,
        "weergave": display,
        "zekerheid": certainty,
        "reviewStatus": "agent-reviewed",
        "humanReviewed": False,
    }


def _merge_mention(existing: dict[str, Any], incoming: dict[str, Any]) -> dict[str, Any]:
    priority = {
        "genoemde-engel": 8, "engel-van-jahweh": 7, "aartsengel": 6,
        "serafim": 5, "cherubim": 4, "wachters": 3,
        "gevallen-demonisch": 2, "geestelijke-machten": 1,
        "hemelse-heerscharen": 1, "engel": 0,
        "hemelwezen-overig": 0,
    }
    if priority.get(incoming["subcategorie"], 0) > priority.get(existing["subcategorie"], 0):
        existing["subcategorie"] = incoming["subcategorie"]
    if incoming["zekerheid"] == "onzeker" or existing["zekerheid"] == "onzeker":
        existing["zekerheid"] = "onzeker"
    elif incoming["zekerheid"] == "waarschijnlijk" or existing["zekerheid"] == "waarschijnlijk":
        existing["zekerheid"] = "waarschijnlijk"
    existing["rang"] = min(existing["rang"], incoming["rang"])
    return existing


def _json_dump(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def build_engelen(root: Path = ROOT, write: bool = True) -> dict[str, Any]:
    books = [book for book in load_books(root) if book.get("chaptersIncluded")]
    corpus = load_corpus(root, include_ethiopic=True)
    position = {verse.ref: index for index, verse in enumerate(corpus)}
    verse_by_ref = {verse.ref: verse for verse in corpus}
    mentions: dict[str, dict[str, Any]] = {}
    reviewqueue: list[dict[str, Any]] = []

    def add(ref: str, subcategory: str, display: str | None = None, certainty: str = "zeker", rank: int = 2) -> None:
        verse = verse_by_ref.get(ref)
        if not verse:
            raise ValueError(f"Onbekende Bijbelverwijzing: {ref}")
        mention = _make_mention(
            ref, subcategory, display or _display_type(verse.book_id, verse.text, subcategory), certainty, rank
        )
        mentions[ref] = _merge_mention(mentions[ref], mention) if ref in mentions else mention

    for verse in corpus:
        ref, text = verse.ref, verse.text
        if ref in HUMAN_MESSENGERS:
            if ANGEL_RE.search(text):
                reviewqueue.append(_review(ref, "mogelijke-menselijke-bode", HUMAN_MESSENGERS[ref]))
            continue

        if CHERUB_RE.search(text):
            add(ref, "cherubim")
        if SERAPH_RE.search(text):
            add(ref, "serafim")
        if ARCHANGEL_RE.search(text):
            add(ref, "aartsengel", certainty="zeker")
        if WATCHER_RE.search(text) and verse.book_id in {"henoch", "jubileeen"}:
            add(ref, "wachters", certainty="zeker")
        if _named_angel(text, ref):
            add(ref, "genoemde-engel", certainty="zeker", rank=1)

        if ref in FALSE_DEMON_REFERENCES:
            if DEMON_RE.search(text):
                reviewqueue.append(_review(ref, "contextueel-niet-letterlijk", FALSE_DEMON_REFERENCES[ref]))
        elif DEMON_RE.search(text):
            add(ref, "gevallen-demonisch", certainty="waarschijnlijk")

        if ANGEL_RE.search(text):
            has_theophany_title = any(title in text for title in (
                "Engel van JAHWEH", "Engel van God", "Engel van de Heere", "Engel van het verbond"
            ))
            if ref in THEOPHANY_REFS or has_theophany_title:
                add(ref, "engel-van-jahweh", certainty="waarschijnlijk", rank=1)
                reviewqueue.append(_review(
                    ref, "theofanie-vraagstuk",
                    "De tekst noemt de Engel; deze tag legt geen identiteit met God of Christus vast.",
                ))
            elif ref in CHURCH_ANGELS:
                add(ref, "engel", "twijfelgeval", "onzeker")
                reviewqueue.append(_review(
                    ref, "mogelijke-menselijke-bode",
                    "De engel van de gemeente kan als hemels wezen of als menselijke vertegenwoordiger worden uitgelegd.",
                ))
            else:
                add(ref, "engel")

        if ref in FALLEN_ANGEL_REFS:
            add(ref, "gevallen-demonisch", certainty="zeker")

    for ref in sorted(SPIRITUAL_POWER_REFS, key=position.__getitem__):
        add(ref, "geestelijke-machten", "onderwijs", "waarschijnlijk")
    for ref in sorted(HEAVENLY_HOST_REFS, key=position.__getitem__):
        add(ref, "hemelse-heerscharen")
    for ref, (subcategory, display, certainty) in IMPLICIT_GROUPS.items():
        add(ref, subcategory, display, certainty)
    for ref, note in UNCERTAIN_BEINGS.items():
        reviewqueue.append(_review(ref, "onzeker-hemelwezen", note))

    # De onzekere witte mannen worden zichtbaar aangeboden, maar expliciet als
    # waarschijnlijk en met hun menselijke-reviewvraag ernaast.
    for ref in ("handelingen 1:10", "handelingen 1:11"):
        add(ref, "engel", "twijfelgeval", "waarschijnlijk")

    ordered = [mentions[ref] for ref in sorted(mentions, key=position.__getitem__)]
    reviewqueue = sorted(
        {((item.get("ref") or ""), item["type"]): item for item in reviewqueue}.values(),
        key=lambda item: (position.get(item.get("ref", ""), 10**9), item["type"]),
    )

    tag = {
        "id": "engelen",
        "naam": "Engelen",
        "beschrijving": "Alle teksten over engelen en andere hemelwezens, met onderscheid tussen verschijningen, onderwijs, visioenen en gevallen hemelwezens.",
        "kleur": "#6f86a3",
        "aliassen": [
            "engel van JAHWEH", "engel van God", "engel van de Heere",
            "cherub", "cherubim", "seraf", "serafim", "aartsengel",
            "wachters", "hemelse heerscharen", "Gabriël", "Michaël",
            "Rafaël", "Uriël",
        ],
        "reviewStatus": "agent-reviewed",
        "humanReviewed": False,
        "verzen": ordered,
    }

    subcategories = Counter(item["subcategorie"] for item in ordered)
    per_book = []
    for book in books:
        refs = [item for item in ordered if item["ref"].startswith(book["id"] + " ")]
        per_book.append({
            "boek": book["id"],
            "naam": book["nameDutch"],
            "gescand": True,
            "verzenGetagd": len(refs),
            "subcategorieen": dict(sorted(Counter(item["subcategorie"] for item in refs).items())),
            "twijfelgevallen": sum(1 for item in reviewqueue if (item.get("ref") or "").startswith(book["id"] + " ")),
        })
    report = {
        "onderwerp": "engelen",
        "boekenGescand": len(books),
        "verzenGescand": len(corpus),
        "verzenGetagd": len(ordered),
        "boekenMetTreffers": sum(1 for book in per_book if book["verzenGetagd"]),
        "subcategorieen": dict(sorted(subcategories.items())),
        "twijfelgevallen": len(reviewqueue),
        "reviewStatus": "agent-reviewed",
        "humanReviewed": False,
        "perBoek": per_book,
    }
    result = {"tag": tag, "reviewqueue": reviewqueue, "report": report}

    if write:
        data_dir = root / "data"
        _json_dump(data_dir / "onderwerp-engelen.json", {"tag": tag})
        _json_dump(data_dir / "onderwerp-engelen-reviewqueue.json", {"reviewqueue": reviewqueue})
        _json_dump(data_dir / "onderwerp-engelen-dekking.json", report)
        tags_path = data_dir / "tags.json"
        tags_doc = json.loads(tags_path.read_text(encoding="utf-8"))
        current = tags_doc.get("tags", [])
        replacement = []
        inserted = False
        for existing in current:
            if existing.get("id") == "engelen":
                replacement.append(tag)
                inserted = True
            else:
                replacement.append(existing)
        if not inserted:
            replacement.append(tag)
        tags_doc["tags"] = replacement
        _json_dump(tags_path, tags_doc)

    return result


if __name__ == "__main__":
    built = build_engelen()
    print(json.dumps(built["report"], ensure_ascii=False, indent=2))
