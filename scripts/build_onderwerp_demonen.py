#!/usr/bin/env python3
"""Bouw stagingdata voor het onderwerp 'Demonen en duivelen'.

De builder leest alle primaire ``text2026``-verzen. Woordherkenning levert
alleen kandidaten; expliciete uitsluitingen, contextpassages en een aparte
reviewlijst voorkomen dat woorden als ``geest``, ``satan`` of ``bezeten``
zonder context als demonische entiteit worden gepubliceerd.
"""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT_MANIFEST = DATA / "onderwerp-demonen-manifest.json"
OUT_MENTIONS = DATA / "onderwerp-demonen-vermeldingen.json"
OUT_REVIEW = DATA / "onderwerp-demonen-review.json"
TAGS_PATH = DATA / "tags.json"

CATEGORIES = (
    "satan-duivel",
    "demon-onreine-geest",
    "bezetenheid",
    "uitdrijving",
    "verzoeking-misleiding",
    "demonische-eredienst-afgoderij",
    "gevallen-machten",
    "visioen-symboliek",
    "twijfelgeval",
)


def ref_range(book: str, chapter: int, start: int, end: int) -> list[str]:
    return [f"{book} {chapter}:{verse}" for verse in range(start, end + 1)]


# Contextverzen horen bij dezelfde episode, ook als niet ieder vers de entiteit
# opnieuw noemt. Ze zijn expliciet opgenomen na lezing van de hele passage.
PASSAGES = [
    (ref_range("mattheus", 4, 1, 11), ("satan-duivel", "verzoeking-misleiding"), "zeker", ()),
    (ref_range("mattheus", 8, 28, 34), ("demon-onreine-geest", "bezetenheid", "uitdrijving"), "zeker", ()),
    (ref_range("mattheus", 9, 32, 34), ("demon-onreine-geest", "bezetenheid", "uitdrijving"), "zeker", ()),
    (ref_range("mattheus", 12, 22, 30), ("demon-onreine-geest", "bezetenheid", "uitdrijving"), "zeker", ()),
    (ref_range("mattheus", 12, 43, 45), ("demon-onreine-geest", "bezetenheid"), "zeker", ()),
    (ref_range("mattheus", 15, 21, 28), ("demon-onreine-geest", "bezetenheid", "uitdrijving"), "zeker", ()),
    (ref_range("mattheus", 17, 14, 21), ("demon-onreine-geest", "bezetenheid", "uitdrijving"), "zeker", ()),
    (ref_range("markus", 1, 12, 13), ("satan-duivel", "verzoeking-misleiding"), "zeker", ()),
    (ref_range("markus", 1, 21, 28), ("demon-onreine-geest", "bezetenheid", "uitdrijving"), "zeker", ()),
    (ref_range("markus", 3, 20, 30), ("satan-duivel", "demon-onreine-geest", "uitdrijving"), "zeker", ()),
    (ref_range("markus", 5, 1, 20), ("demon-onreine-geest", "bezetenheid", "uitdrijving"), "zeker", ()),
    (ref_range("markus", 7, 24, 30), ("demon-onreine-geest", "bezetenheid", "uitdrijving"), "zeker", ()),
    (ref_range("markus", 9, 14, 29), ("demon-onreine-geest", "bezetenheid", "uitdrijving"), "zeker", ()),
    (ref_range("lukas", 4, 1, 13), ("satan-duivel", "verzoeking-misleiding"), "zeker", ()),
    (ref_range("lukas", 4, 31, 37), ("demon-onreine-geest", "bezetenheid", "uitdrijving"), "zeker", ()),
    (ref_range("lukas", 8, 26, 39), ("demon-onreine-geest", "bezetenheid", "uitdrijving"), "zeker", ()),
    (ref_range("lukas", 9, 37, 43), ("demon-onreine-geest", "bezetenheid", "uitdrijving"), "zeker", ()),
    (ref_range("lukas", 11, 14, 26), ("demon-onreine-geest", "bezetenheid", "uitdrijving"), "zeker", ()),
    (ref_range("handelingen", 16, 16, 18), ("demon-onreine-geest", "bezetenheid", "uitdrijving"), "zeker", ()),
    (ref_range("handelingen", 19, 11, 20), ("demon-onreine-geest", "bezetenheid", "uitdrijving"), "zeker", ()),
    (ref_range("tobit", 3, 7, 8), ("demon-onreine-geest", "bezetenheid"), "zeker", ()),
    (ref_range("tobit", 6, 8, 20), ("demon-onreine-geest", "bezetenheid", "uitdrijving"), "zeker", ()),
    (ref_range("tobit", 8, 1, 3), ("demon-onreine-geest", "uitdrijving"), "zeker", ("engelen",)),
    (ref_range("openbaring", 9, 1, 11), ("gevallen-machten", "visioen-symboliek"), "waarschijnlijk", ("engelen",)),
    (ref_range("openbaring", 12, 3, 17), ("satan-duivel", "gevallen-machten", "visioen-symboliek"), "zeker", ("engelen",)),
    (ref_range("henoch", 6, 1, 8), ("gevallen-machten", "verzoeking-misleiding"), "zeker", ("engelen",)),
    (ref_range("henoch", 7, 1, 6), ("gevallen-machten",), "zeker", ("engelen",)),
    (ref_range("henoch", 8, 1, 3), ("gevallen-machten", "verzoeking-misleiding"), "zeker", ("engelen",)),
    (ref_range("henoch", 9, 6, 8), ("gevallen-machten", "verzoeking-misleiding"), "zeker", ("engelen",)),
    (ref_range("henoch", 10, 4, 15), ("gevallen-machten",), "zeker", ("engelen",)),
    (ref_range("henoch", 12, 4, 6), ("gevallen-machten",), "zeker", ("engelen",)),
    (ref_range("henoch", 13, 1, 7), ("gevallen-machten",), "zeker", ("engelen",)),
    (ref_range("henoch", 14, 1, 7), ("gevallen-machten",), "zeker", ("engelen",)),
    (ref_range("henoch", 15, 1, 11), ("gevallen-machten", "demon-onreine-geest"), "zeker", ("engelen",)),
    (ref_range("henoch", 16, 1, 4), ("gevallen-machten", "verzoeking-misleiding"), "zeker", ("engelen",)),
    (ref_range("henoch", 67, 6, 13), ("gevallen-machten",), "zeker", ("engelen",)),
    (["henoch 68:2"], ("gevallen-machten",), "zeker", ("engelen",)),
    (ref_range("henoch", 69, 1, 12), ("gevallen-machten", "verzoeking-misleiding"), "zeker", ("engelen",)),
    (["henoch 84:4"], ("gevallen-machten",), "zeker", ("engelen",)),
    (ref_range("jubileeen", 10, 1, 14), ("demon-onreine-geest", "verzoeking-misleiding"), "zeker", ()),
    ([f"jubileeen 11:{verse}" for verse in (5, 6, 7, 8, 9, 11, 12, 13)], ("satan-duivel", "demon-onreine-geest", "verzoeking-misleiding"), "zeker", ("engelen",)),
    (ref_range("jubileeen", 48, 1, 18), ("satan-duivel", "verzoeking-misleiding"), "zeker", ("engelen",)),
    (ref_range("1meqabyan", 18, 3, 7), ("gevallen-machten", "satan-duivel"), "zeker", ("engelen",)),
    (["1meqabyan 19:10"], ("gevallen-machten", "verzoeking-misleiding"), "zeker", ("engelen",)),
    (ref_range("2meqabyan", 20, 9, 11), ("gevallen-machten", "demon-onreine-geest"), "zeker", ("engelen",)),
    (ref_range("3meqabyan", 4, 1, 9), ("gevallen-machten", "demon-onreine-geest"), "zeker", ("engelen",)),
    (ref_range("3meqabyan", 6, 4, 9), ("satan-duivel", "demon-onreine-geest"), "zeker", ("engelen",)),
]


# Ondubbelzinnige of door de directe context vastgelegde tekstbenamingen.
RULES = [
    (re.compile(r"\bsatans?\b", re.I), "satan-duivel", "Satan"),
    (re.compile(r"\bduivel(?:en|s)?\b", re.I), "satan-duivel", "duivel"),
    (re.compile(r"\bdemon(?:en|ische)?\b", re.I), "demon-onreine-geest", "demon"),
    (re.compile(r"\bonreine? geest(?:en)?\b", re.I), "demon-onreine-geest", "onreine geest"),
    (re.compile(r"\bboze? geest(?:en)?\b", re.I), "demon-onreine-geest", "boze geest"),
    (re.compile(r"\b(?:stomme(?: en dove)?|dove) geest\b", re.I), "demon-onreine-geest", "stomme of dove geest"),
    (re.compile(r"\basmode[uü]s\b", re.I), "demon-onreine-geest", "Asmodeüs"),
    (re.compile(r"\bbe[eë]lzeb[uo]l\b", re.I), "satan-duivel", "Beëlzebul"),
    (re.compile(r"\blegio(?:en)?\b", re.I), "demon-onreine-geest", "Legio"),
    (re.compile(r"\bverzoeker\b", re.I), "verzoeking-misleiding", "verzoeker"),
    (re.compile(r"\bwaarzeggende geest\b|\bgeest der waarzegging\b", re.I), "demon-onreine-geest", "waarzeggende geest"),
    (re.compile(r"\bverleidende geesten\b", re.I), "verzoeking-misleiding", "verleidende geesten"),
    (re.compile(r"\boverste van deze wereld\b", re.I), "satan-duivel", "overste van deze wereld"),
    (re.compile(r"\bgod van deze eeuw\b", re.I), "satan-duivel", "god van deze eeuw"),
    (re.compile(r"\boverste van de macht van de lucht\b", re.I), "gevallen-machten", "overste van de macht van de lucht"),
    (re.compile(r"\bgeestelijke boosheden\b", re.I), "gevallen-machten", "geestelijke boosheden"),
    (re.compile(r"\bengel van de satan\b", re.I), "gevallen-machten", "engel van de satan"),
    (re.compile(r"\bazazel\b", re.I), "gevallen-machten", "Azazel"),
    (re.compile(r"\bmastema\b", re.I), "satan-duivel", "Mastema"),
    (re.compile(r"\bbeliar\b", re.I), "satan-duivel", "Beliar"),
    (re.compile(r"\babaddon\b", re.I), "gevallen-machten", "Abaddon"),
    (re.compile(r"\bapollyon\b", re.I), "gevallen-machten", "Apollyon"),
    (re.compile(r"\boude slang\b", re.I), "satan-duivel", "oude slang"),
    (re.compile(r"\bgrote draak\b", re.I), "satan-duivel", "grote draak"),
]

POSSESSION = re.compile(r"\b(?:bezetene|bezetenen|van de duivel bezeten|demonen? had)\b", re.I)
EXORCISM = re.compile(r"\b(?:uitwerp\w*|uitgevaren|uitging|ga uit)\b", re.I)
IDOLATRY = re.compile(r"\b(?:offer\w*|aanbid\w*|tafel|drinkbeker|gemeenschap)\b", re.I)
VISION = re.compile(r"\b(?:visioen|draak|oude slang|afgrond|teken gezien)\b", re.I)

# Deze woordvormen beschrijven in hun vers een mens, landbezit, beroep of echt
# dier/afgodsbeeld. Ze mogen nooit door de letterlijke matcher gepubliceerd worden.
EXCLUDED_REFS = {
    "2samuel 19:22",       # satan = menselijke tegenstander
    "deuteronomium 30:5", "nehemia 9:22", "nehemia 9:25",
    "jesaja 63:18", "jeremia 16:19", "jeremia 32:23",  # erfelijk bezeten
    "mattheus 26:53",     # legioenen engelen, geen demonen
    "belenddedraak 1:22", # een vereerde draak; de tekst legt geen demonische identiteit
    "2makkabeeen 5:9",    # Demoniërs = inwoners van een plaats
}

# Alleen 2 Korintiërs 6 gebruikt Belial als persoonlijke boze macht. Elders is
# het in deze vertaling een benaming voor menselijke nietswaardigheid.
BELIAL_REF = "2korinthiers 6:15"

# Expliciete gevallen machten zonder een term uit RULES.
CURATED = {
    "efeziers 2:2": (("gevallen-machten",), "waarschijnlijk", ()),
    "efeziers 6:12": (("gevallen-machten",), "zeker", ()),
    "kolossenzen 2:15": (("gevallen-machten",), "waarschijnlijk", ()),
    "2petrus 2:4": (("gevallen-machten",), "zeker", ("engelen",)),
    "judas 1:6": (("gevallen-machten",), "zeker", ("engelen",)),
    "1meqabyan 18:5": (("gevallen-machten", "satan-duivel"), "zeker", ("engelen",)),
    "2meqabyan 20:11": (("gevallen-machten", "demon-onreine-geest"), "zeker", ("engelen",)),
    "openbaring 12:9": (("satan-duivel", "gevallen-machten", "visioen-symboliek"), "zeker", ("engelen",)),
    "openbaring 16:13": (("demon-onreine-geest", "visioen-symboliek"), "zeker", ()),
    "openbaring 16:14": (("demon-onreine-geest", "visioen-symboliek"), "zeker", ()),
}


def review_range(book: str, chapter: int, start: int, end: int, reason: str) -> list[tuple[str, str]]:
    return [(ref, reason) for ref in ref_range(book, chapter, start, end)]


# Geen van deze identificaties wordt door de builder als feit vastgesteld.
REVIEW_ITEMS = [
    *review_range("genesis", 3, 1, 15, "De slang wordt hier niet in de directe tekst Satan of de duivel genoemd."),
    *review_range("genesis", 6, 1, 4, "De identiteit van de zonen van God en de Nephilim is omstreden."),
    *review_range("leviticus", 16, 8, 10, "De weggaande bok mag niet zonder taalkundige beoordeling met een demonische Azazel worden vereenzelvigd."),
    ("leviticus 16:26", "De weggaande bok mag niet zonder taalkundige beoordeling met een demonische Azazel worden vereenzelvigd."),
    ("richteren 9:23", "Een door God gezonden boze geest kan vijandschap of een geestelijke macht aanduiden."),
    *review_range("1samuel", 16, 14, 16, "De boze geest van God vereist theologische en taalkundige beoordeling."),
    ("1samuel 16:23", "De boze geest van God vereist theologische en taalkundige beoordeling."),
    ("1samuel 18:10", "De boze geest van God vereist theologische en taalkundige beoordeling."),
    ("1samuel 19:9", "De boze geest van JAHWEH vereist theologische en taalkundige beoordeling."),
    *review_range("1koningen", 22, 19, 23, "De leugengeest in de hemelse raad wordt niet expliciet een demon genoemd."),
    ("psalmen 109:6", "Satan kan hier ook 'tegenstander' of 'aanklager' betekenen."),
    ("jesaja 13:21", "De vertaalde term demonen staat in een poëtische ruïnebeschrijving en vereist lexicale beoordeling."),
    *review_range("jesaja", 14, 12, 15, "De passage spreekt direct tot de koning van Babel; identificatie met Satan is omstreden."),
    ("jesaja 34:14", "De vertaalde term duivel staat tussen woestijndieren en vereist lexicale beoordeling."),
    *review_range("ezechiel", 28, 12, 17, "De passage spreekt direct tot de koning van Tyrus; een achterliggende gevallen engel is omstreden."),
    *review_range("daniel", 10, 13, 21, "De vorsten van Perzië en Griekenland lijken geestelijke machten, maar hun precieze identiteit is niet benoemd."),
    *review_range("1petrus", 3, 19, 20, "De identiteit van de geesten in de gevangenis is exegetisch omstreden."),
    *review_range("1johannes", 4, 1, 6, "Geest kan hier leer, houding, menselijke geest of geestelijke macht aanduiden."),
]


def load_corpus() -> tuple[list[dict], dict[str, dict], dict[str, int]]:
    books = json.loads((DATA / "books.json").read_text(encoding="utf-8"))["books"]
    verses: dict[str, dict] = {}
    counts: dict[str, int] = {}
    for book in books:
        book_count = 0
        for chapter in book["chaptersIncluded"]:
            path = DATA / book["id"] / f"{chapter}.json"
            if not path.exists():
                raise FileNotFoundError(f"Ontbrekend hoofdstukbestand: {path}")
            data = json.loads(path.read_text(encoding="utf-8-sig"))
            for verse in data.get("verses", []):
                ref = f"{book['id']} {chapter}:{verse['number']}"
                verses[ref] = {
                    "boek": book["id"],
                    "hoofdstuk": chapter,
                    "vers": verse["number"],
                    "tekst": verse.get("text2026", ""),
                }
                book_count += 1
        counts[book["id"]] = book_count
    return books, verses, counts


def add_hit(hits: dict[str, dict], ref: str, categories, certainty="zeker", overlap=(), names=()):
    item = hits.setdefault(ref, {
        "categorieen": set(), "zekerheid": certainty,
        "overlapTopics": set(), "benamingenInTekst": set(),
    })
    item["categorieen"].update(categories)
    item["overlapTopics"].update(overlap)
    item["benamingenInTekst"].update(names)
    rank = {"zeker": 2, "waarschijnlijk": 1, "onzeker": 0}
    if rank[certainty] < rank[item["zekerheid"]]:
        item["zekerheid"] = certainty


def direct_hits(verses: dict[str, dict]) -> dict[str, dict]:
    hits: dict[str, dict] = {}
    for ref, verse in verses.items():
        if ref in EXCLUDED_REFS:
            continue
        text = verse["tekst"]
        found = []
        for pattern, category, canonical in RULES:
            if pattern.search(text):
                found.append((category, canonical))
        if ref == BELIAL_REF:
            found.append(("satan-duivel", "Belial"))
        if not found:
            continue
        categories = {category for category, _ in found}
        names = {name for _, name in found}
        if POSSESSION.search(text):
            categories.add("bezetenheid")
        if EXORCISM.search(text) and categories & {"demon-onreine-geest", "bezetenheid"}:
            categories.add("uitdrijving")
        if IDOLATRY.search(text) and categories & {"demon-onreine-geest", "satan-duivel"}:
            categories.add("demonische-eredienst-afgoderij")
        if VISION.search(text):
            categories.add("visioen-symboliek")
        named_fallen_power = names & {"Azazel", "Mastema", "Abaddon", "Apollyon"}
        overlap = ("engelen",) if (
            (re.search(r"\bengelen?\b", text, re.I) and categories & {"gevallen-machten", "satan-duivel"})
            or named_fallen_power
        ) else ()
        add_hit(hits, ref, categories, overlap=overlap, names=names)
    return hits


def build() -> None:
    books, verses, verse_counts = load_corpus()
    if len(books) != 88:
        raise ValueError(f"Verwacht 88 boeken, vond {len(books)}")

    hits = direct_hits(verses)
    for refs, categories, certainty, overlap in PASSAGES:
        for ref in refs:
            if ref not in verses:
                raise ValueError(f"Contextverwijzing bestaat niet: {ref}")
            add_hit(hits, ref, categories, certainty, overlap)
    for ref, (categories, certainty, overlap) in CURATED.items():
        if ref not in verses:
            raise ValueError(f"Handmatige verwijzing bestaat niet: {ref}")
        add_hit(hits, ref, categories, certainty, overlap)

    # Betwiste passages blijven uitsluitend in de reviewqueue. Als een woordregel
    # ze ook vond, wordt die publicatiekandidaat bewust verwijderd.
    review_by_ref = dict(REVIEW_ITEMS)
    for ref in review_by_ref:
        if ref not in verses:
            raise ValueError(f"Reviewverwijzing bestaat niet: {ref}")
        hits.pop(ref, None)

    mentions = []
    for ref, meta in hits.items():
        verse = verses[ref]
        mentions.append({
            "ref": ref,
            "href": f"index.html#{verse['boek']}/{verse['hoofdstuk']}/{verse['vers']}",
            "boek": verse["boek"],
            "hoofdstuk": verse["hoofdstuk"],
            "vers": verse["vers"],
            "categorieen": sorted(meta["categorieen"]),
            "zekerheid": meta["zekerheid"],
            "benamingenInTekst": sorted(meta["benamingenInTekst"], key=str.casefold),
            "overlapTopics": sorted(meta["overlapTopics"]),
            "status": "agent-reviewed",
            "humanReviewed": False,
        })

    order = {book["id"]: number for number, book in enumerate(books)}
    mentions.sort(key=lambda item: (order[item["boek"]], item["hoofdstuk"], item["vers"]))

    review_queue = []
    for ref, reason in REVIEW_ITEMS:
        verse = verses[ref]
        review_queue.append({
            "ref": ref,
            "href": f"index.html#{verse['boek']}/{verse['hoofdstuk']}/{verse['vers']}",
            "boek": verse["boek"],
            "reden": reason,
            "categorie": "twijfelgeval",
            "zekerheid": "onzeker",
            "status": "needs-human-review",
            "humanReviewed": False,
        })

    categories = Counter()
    certainty = Counter()
    tagged_per_book = Counter()
    for item in mentions:
        categories.update(item["categorieen"])
        certainty[item["zekerheid"]] += 1
        tagged_per_book[item["boek"]] += 1
    categories["twijfelgeval"] = len(review_queue)

    manifest = {
        "onderwerpId": "demonen-en-duivelen",
        "naam": "Demonen en duivelen",
        "beschrijving": "Bijbelteksten over Satan, de duivel, demonen, onreine en boze geesten, demonische machten, bezetenheid en uitdrijving.",
        "status": "agent-reviewed",
        "humanReviewed": False,
        "publicatieStatus": "staging-niet-samenvoegen-zonder-afstemming",
        "boekenBeoordeeld": len(books),
        "verzenBeoordeeld": sum(verse_counts.values()),
        "aantalGetagdeVerzen": len(mentions),
        "aantalReviewgevallen": len(review_queue),
        "aantallenPerCategorie": {category: categories[category] for category in CATEGORIES},
        "aantallenPerZekerheid": {level: certainty[level] for level in ("zeker", "waarschijnlijk", "onzeker")},
        "dekkingPerBoek": [
            {
                "boek": book["id"],
                "verzenBeoordeeld": verse_counts[book["id"]],
                "getagdeVerzen": tagged_per_book[book["id"]],
                "status": "agent-reviewed",
                "humanReviewed": False,
            }
            for book in books
        ],
    }

    payloads = {
        OUT_MANIFEST: manifest,
        OUT_MENTIONS: {
            "onderwerpId": "demonen-en-duivelen",
            "status": "agent-reviewed",
            "humanReviewed": False,
            "mentions": mentions,
        },
        OUT_REVIEW: {
            "onderwerpId": "demonen-en-duivelen",
            "status": "needs-human-review",
            "humanReviewed": False,
            "reviewQueue": review_queue,
        },
    }
    for path, payload in payloads.items():
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    topic_tag = {
        "id": "demonen-en-duivelen",
        "naam": "Demonen en duivelen",
        "beschrijving": "Alle teksten over Satan, de duivel, demonen, onreine en boze geesten, demonische machten, bezetenheid en uitdrijving.",
        "kleur": "#70465d",
        "aliassen": [
            "Satan", "duivel", "demon", "onreine geest", "boze geest",
            "Beëlzebul", "Legio", "Asmodeüs", "Azazel", "Mastema",
            "Beliar", "oude slang", "grote draak", "Abaddon", "Apollyon",
        ],
        "reviewStatus": "agent-reviewed",
        "humanReviewed": False,
        "verzen": [
            {
                "ref": item["ref"],
                "rang": 1 if "satan-duivel" in item["categorieen"] else 2,
                "categorieen": item["categorieen"],
                "zekerheid": item["zekerheid"],
                "overlapTopics": item["overlapTopics"],
                "reviewStatus": item["status"],
                "humanReviewed": False,
            }
            for item in mentions
        ],
    }
    tags_data = json.loads(TAGS_PATH.read_text(encoding="utf-8"))
    tags_data["tags"] = [
        tag for tag in tags_data.get("tags", [])
        if tag.get("id") != topic_tag["id"]
    ] + [topic_tag]
    TAGS_PATH.write_text(
        json.dumps(tags_data, ensure_ascii=False, indent=1) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    build()
