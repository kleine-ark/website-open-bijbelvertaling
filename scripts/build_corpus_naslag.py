#!/usr/bin/env python3
"""Bouw corpusbrede wiki-naslagdata uit de zichtbare Open Vertaling."""

from __future__ import annotations

from dataclasses import dataclass
import html
import json
from pathlib import Path
import re
from typing import Any

try:
    from scripts.enrich_naslag_materialen import enrich
except ModuleNotFoundError:  # rechtstreeks uitgevoerd: scripts/ staat op sys.path
    from enrich_naslag_materialen import enrich


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
CATALOG_PATH = DATA / "naslag-catalogus.json"
OUTPUTS = {
    "materialen": "naslag-materialen.json",
    "dieren": "naslag-dieren.json",
    "bomen-planten": "naslag-bomen-planten.json",
    "personen": "naslag-personen.json",
    "muziekinstrumenten": "naslag-muziekinstrumenten.json",
}
LETTER = r"0-9A-Za-zÀ-ÖØ-öø-ÿ"

NATURE_EXTRA_ITEMS = {
    "dieren": [
        ("dieren-algemeen", "Dieren", ["dier", "dieren"], "Algemene vermeldingen van dieren zonder nadere soortaanduiding."),
        ("beesten", "Beesten", ["beest", "beesten"], "Algemene vermeldingen van beesten zonder nadere soortaanduiding."),
        ("gedierte", "Gedierte", ["gedierte", "wild gedierte", "kruipend gedierte"], "Diergroepen die de vertaling als gedierte aanduidt."),
        ("vogels", "Vogels", ["vogel", "vogels", "gevogelte"], "Vogels waarvan de tekst geen afzonderlijke soort noemt."),
        ("veulen", "Veulen", ["veulen", "veulens"], "Jonge paarden en ezels die als veulen worden aangeduid."),
        ("ooi", "Ooi", ["ooi", "ooien", "ooilam"], "Vrouwelijke schapen en het ooilam."),
        ("kid", "Geitenbokje", ["kid", "kidderen", "geitenbokje", "geitenbokjes"], "Jonge geiten die de tekst afzonderlijk noemt."),
        ("havik", "Havik", ["havik", "haviken"], "De roofvogel die in de spijswetten wordt genoemd."),
        ("sperwer", "Sperwer", ["sperwer", "sperwers"], "Een roofvogel uit de spijswetten en het boek Job."),
        ("koekoek", "Koekoek", ["koekoek", "koekoeken"], "Een vogel uit de lijsten van onreine vogels."),
        ("roerdomp", "Roerdomp", ["roerdomp", "roerdompen"], "Een vogel van woeste en verlaten plaatsen."),
        ("kauw", "Kauw", ["kauw", "kauwen"], "Een vogel uit de lijsten van onreine vogels."),
        ("visarend", "Visarend", ["visarend", "visarenden"], "Een roofvogel uit de spijswetten."),
        ("zeearend", "Zeearend", ["zeearend", "zeearenden"], "Een roofvogel uit de spijswetten."),
        ("steenuil", "Steenuil", ["steenuil", "steenuilen"], "Een uilensoort die in de vertaling afzonderlijk wordt genoemd."),
        ("ransuil", "Ransuil", ["ransuil", "ransuilen"], "Een uilensoort die in de vertaling afzonderlijk wordt genoemd."),
        ("hyena", "Hyena", ["hyena", "hyena's"], "Een roofdier dat in Henoch wordt genoemd."),
        ("hagedis", "Hagedis", ["hagedis", "hagedissen"], "Een kruipend dier uit de spijswetten."),
        ("vlo", "Vlo", ["vlo", "vlooien"], "Het kleine dier waarmee David zichzelf tegenover Saul vergelijkt."),
        ("luis", "Luis", ["luis", "luizen"], "Het plaagdier uit de Egyptische plagen."),
        ("made", "Made", ["made", "maden"], "Larven die met ontbinding en vergankelijkheid verbonden worden."),
        ("draak", "Draak", ["draak", "draken"], "Het Bijbelse dierlemma draak, letterlijk of beeldend gebruikt."),
        ("basilisk", "Basilisk", ["basilisk", "basiliskus", "basilisken"], "Het traditionele Bijbelse lemma voor een gevaarlijke slang."),
        ("buffel", "Buffel", ["buffel", "buffelen"], "Een rundachtig dier dat afzonderlijk wordt genoemd."),
        ("steenbok", "Steenbok", ["steenbok", "steenbokken"], "Een wild hoefdier van de bergen."),
        ("gems", "Gems", ["gems", "gemzen"], "Een wild hoefdier uit de spijswetten."),
        ("das", "Das", ["das", "dassen"], "Een dier uit de spijswetten; de historische soortidentificatie vraagt voorzichtigheid."),
        ("hengst", "Hengst", ["hengst", "hengsten"], "Een mannelijk paard dat de tekst afzonderlijk noemt."),
        ("kudde", "Kudde", ["kudde", "kudden"], "Een groep gehouden dieren waarvan niet altijd één soort wordt genoemd."),
    ],
    "bomen-planten": [
        ("boom-algemeen", "Boom", ["boom", "bomen", "geboomte"], "Bomen waarvan de tekst geen afzonderlijke soort noemt."),
        ("struik-algemeen", "Struik", ["struik", "struiken"], "Struiken waarvan de tekst geen afzonderlijke soort noemt."),
        ("gewas", "Gewas", ["gewas", "gewassen", "veldgewas", "veldgewassen"], "Gewassen en veldgewassen zonder nadere soortaanduiding."),
        ("vrucht-algemeen", "Vrucht", ["vrucht", "vruchten", "veldvrucht", "veldvruchten"], "Botanische vruchten waarvan de tekst geen afzonderlijke soort noemt."),
        ("tak-en-wortel", "Tak en wortel", ["tak", "takken", "wortel", "wortels", "wortelen"], "Botanische takken en wortels, letterlijk of als beeld gebruikt."),
        ("papyrus", "Papyrus", ["papyrus"], "De plant die als schrijfmateriaal wordt gebruikt."),
        ("terebint", "Terebint", ["terebint", "terebinten", "terebintnoten"], "Een boom die in Jubileeën wordt genoemd."),
        ("almuggimboom", "Almuggimboom", ["almuggimhout"], "Het kostbare hout waarvan de precieze boomsoort onzeker is."),
        ("graan-en-koren", "Graan en koren", ["graan", "koren"], "Graan en koren als gewas en voedsel."),
        ("korenaar", "Korenaar", ["aar", "aren", "korenaar", "korenaren"], "De aar waarin het graan groeit."),
        ("stro-en-kaf", "Stro en kaf", ["stro", "kaf"], "De stengel en het omhulsel die na de graanoogst overblijven."),
        ("wikke", "Wikke", ["wikke", "wikken"], "Een akkergewas dat Jesaja naast komijn noemt."),
        ("doornstruik", "Doornstruik", ["doornstruik", "doornstruiken"], "Een doornige struik die de tekst afzonderlijk noemt."),
        ("blad-algemeen", "Blad", ["blad", "bladeren"], "Bladeren van bomen en planten, letterlijk of beeldend gebruikt."),
        ("bloem-algemeen", "Bloem", ["bloem", "bloemen"], "Bloemen van planten, letterlijk of beeldend gebruikt."),
    ],
}

UNCERTAIN_NATURE = {
    "wilde-os": ("onzeker", "Het Bijbelse dierlemma is zeker; de moderne soortidentificatie is omstreden."),
    "nijlpaard": ("waarschijnlijk", "Behemoth wordt vaak met het nijlpaard verbonden, maar de identificatie is niet zeker."),
    "krokodil": ("waarschijnlijk", "Leviathan wordt soms met de krokodil verbonden; niet iedere vermelding laat die identificatie toe."),
    "walvis": ("onzeker", "De grondtekst duidt een groot zeedier aan en niet noodzakelijk een moderne walvissoort."),
    "egel": ("onzeker", "De historische dieridentificatie van dit Bijbelse lemma is onzeker."),
    "schildpad": ("onzeker", "De historische dieridentificatie van dit Bijbelse lemma is onzeker."),
    "populier-hazelaar-en-kastanje": ("waarschijnlijk", "De traditionele boomnamen zijn behouden; de precieze botanische identificatie is niet overal zeker."),
    "dudaim": ("onzeker", "Het Bijbelse lemma dudaïm is behouden; de precieze plantensoort is onzeker."),
    "cipres": ("waarschijnlijk", "De traditionele boomnaam is behouden; de precieze naaldboomsoort is niet zeker."),
    "jeneverboom": ("waarschijnlijk", "De traditionele naam is behouden; de precieze woestijnstruik is niet zeker."),
    "balsemplant": ("waarschijnlijk", "De tekst noemt balsem; niet elke vermelding maakt de producerende plant herkenbaar."),
    "draak": ("onzeker", "Het traditionele lemma is behouden; de passages doelen niet noodzakelijk op één moderne diersoort."),
    "basilisk": ("onzeker", "Het traditionele lemma is behouden; de precieze slangensoort is onzeker."),
    "das": ("onzeker", "Het traditionele lemma is behouden; de historische soortidentificatie is onzeker."),
    "almuggimboom": ("onzeker", "Het hout wordt genoemd, maar de producerende boomsoort is onzeker."),
}


@dataclass(frozen=True)
class VerseRef:
    book_id: str
    book_name: str
    testament: str
    chapter: int
    verse: int
    text: str

    @property
    def ref(self) -> str:
        return f"{self.book_id} {self.chapter}:{self.verse}"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def normalize_visible_text(markup: str) -> str:
    """Projecteer site-HTML op zichtbare tekst zonder kanttekeningnummers."""
    text = re.sub(r"<sup\b[^>]*>.*?</sup>", "", markup or "", flags=re.I | re.S)
    text = re.sub(r"<[^>]+>", "", text)
    return re.sub(r"\s+", " ", html.unescape(text)).strip()


def load_books(root: Path = ROOT) -> list[dict[str, Any]]:
    return read_json(root / "data" / "books.json")["books"]


def load_corpus(root: Path = ROOT, include_ethiopic: bool = False) -> list[VerseRef]:
    """Lees alle echte versteksten in de vaste boek-, hoofdstuk- en versvolgorde."""
    corpus: list[VerseRef] = []
    for book in load_books(root):
        if book.get("ethiopic") and not include_ethiopic:
            continue
        for chapter in book.get("chaptersIncluded", []):
            path = root / "data" / book["id"] / f"{chapter}.json"
            if not path.exists():
                continue
            data = read_json(path)
            for verse in data.get("verses", []):
                if not isinstance(verse, dict):
                    continue
                raw = verse.get("text2026_html") or verse.get("text2026") or ""
                text = normalize_visible_text(raw)
                if not text:
                    continue
                corpus.append(
                    VerseRef(
                        book_id=book["id"],
                        book_name=book["nameDutch"],
                        testament=book.get("testament", ""),
                        chapter=int(chapter),
                        verse=int(verse["number"]),
                        text=text,
                    )
                )
    return corpus


def _nature_definitions(definition: dict[str, Any], category: str) -> list[dict[str, Any]]:
    items = [dict(item) for item in definition.get("items", [])]
    existing = {item["id"] for item in items}
    for item_id, name, forms, description in NATURE_EXTRA_ITEMS[category]:
        if item_id not in existing:
            items.append({"id": item_id, "naam": name, "zoekvormen": forms, "beschrijving": description})
    return items


def _nature_pattern(forms: list[str]) -> re.Pattern[str] | None:
    cleaned = sorted({form.strip() for form in forms if form and form.strip()}, key=lambda value: (-len(value), value.casefold()))
    if not cleaned:
        return None
    alternatives = "|".join(re.escape(form).replace(r"\ ", r"\s+") for form in cleaned)
    return re.compile(rf"(?<![{LETTER}])(?P<form>{alternatives})(?![{LETTER}])", re.I)


def _nature_context_allowed(item_id: str, text: str, matched: str) -> tuple[bool, str | None]:
    lowered = text.casefold()
    if item_id == "rammen" and matched.casefold() == "ram":
        if matched == "Ram" and re.search(r"\b(?:verwekte|kinderen van|geboren|geslacht)\b", lowered):
            return False, "Ram is hier een persoonsnaam."
    return True, None


def _mention_usage(item_id: str, text: str, start: int, end: int) -> tuple[str, str]:
    before = text[max(0, start - 24):start].casefold()
    context = text[max(0, start - 45):min(len(text), end + 45)].casefold()
    if re.search(r"\b(?:als|zoals|gelijk)\s+(?:een|de|het|aan)?\s*$", before):
        return "vergelijkend", "zeker"
    if item_id == "zaad" and not re.search(r"\b(?:zaai|gezaaid|akker|aarde|land|plant|vrucht|graan|koren|kruid|boom|oogst)\w*\b", context):
        return "beeldend-symbolisch", "waarschijnlijk"
    if re.search(r"\b(?:gelijkenis|beeld|teken|gezicht|droom|figuurlijk|geestelijk)\b", context):
        return "beeldend-symbolisch", "waarschijnlijk"
    return "letterlijk", "waarschijnlijk"


def _build_nature_category(
    definition: dict[str, Any], books: list[dict[str, Any]], corpus: list[VerseRef],
    category: str, reviewqueue: list[dict[str, Any]],
) -> dict[str, Any]:
    data = _base_dataset(definition["titel"], definition.get("intro", ""), books, include_ethiopic=True)
    data.update({
        "reviewStatus": "agent-reviewed", "humanReviewed": False,
        "methodiek": "expliciete lemmacatalogus, vers-voor-vers toegepast op alle 88 boeken",
    })
    positions = {verse.ref: index for index, verse in enumerate(corpus)}
    per_book = {
        book["id"]: {"boek": book["id"], "gescand": True, "dieren": 0, "bomen-planten": 0}
        for book in books if book.get("chaptersIncluded")
    }
    definitions = _nature_definitions(definition, category)
    forms_to_ids: dict[str, set[str]] = {}
    for source in definitions:
        for form in source.get("zoekvormen", []):
            forms_to_ids.setdefault(form.casefold(), set()).add(source["id"])
    for form, ids in sorted(forms_to_ids.items()):
        if len(ids) > 1:
            reviewqueue.append({"categorie": category, "type": "aliasbotsing", "tekstvorm": form, "itemIds": sorted(ids), "reviewStatus": "needs-human-review"})

    for source in definitions:
        pattern = _nature_pattern(source.get("zoekvormen", []))
        excluded = set(source.get("uitsluiten", []))
        mentions_by_ref: dict[str, dict[str, Any]] = {}
        found_forms: set[str] = set()
        if pattern:
            for verse in corpus:
                if source.get("boeken") and verse.book_id not in source["boeken"]:
                    continue
                if verse.ref in excluded:
                    continue
                accepted = []
                for match in pattern.finditer(verse.text):
                    form = match.group("form")
                    allowed, reason = _nature_context_allowed(source["id"], verse.text, form)
                    if allowed:
                        accepted.append(match)
                    else:
                        reviewqueue.append({"categorie": category, "type": "contextueel-homoniem", "itemId": source["id"], "ref": verse.ref, "tekstvorm": form, "notitie": reason, "reviewStatus": "needs-human-review"})
                if not accepted:
                    continue
                classifications = [_mention_usage(source["id"], verse.text, match.start("form"), match.end("form")) for match in accepted]
                usages = {value[0] for value in classifications}
                usage = "vergelijkend" if "vergelijkend" in usages else ("beeldend-symbolisch" if "beeldend-symbolisch" in usages else "letterlijk")
                certainty = "zeker" if all(value[1] == "zeker" for value in classifications) else "waarschijnlijk"
                exact_forms = sorted({match.group("form") for match in accepted}, key=str.casefold)
                found_forms.update(exact_forms)
                mentions_by_ref[verse.ref] = {
                    "ref": verse.ref, "tekstvorm": exact_forms[0], "tekstvormen": exact_forms,
                    "gebruik": usage, "classificatieZekerheid": certainty,
                    "reviewStatus": "agent-reviewed", "humanReviewed": False,
                }
        for ref in source.get("expliciet", []):
            if ref in positions and ref not in mentions_by_ref:
                mentions_by_ref[ref] = {
                    "ref": ref, "tekstvorm": source["naam"], "tekstvormen": [source["naam"]],
                    "gebruik": "letterlijk", "classificatieZekerheid": "waarschijnlijk",
                    "reviewStatus": "agent-reviewed", "humanReviewed": False,
                }

        mentions = sorted(mentions_by_ref.values(), key=lambda mention: positions[mention["ref"]])
        if not mentions:
            continue
        certainty, note = UNCERTAIN_NATURE.get(source["id"], ("zeker", None))
        item = {
            "id": source["id"], "naam": source["naam"], "beschrijving": source["beschrijving"],
            "verzen": [mention["ref"] for mention in mentions], "vermeldingen": mentions,
            "tekstvormen": sorted(found_forms, key=str.casefold), "zekerheid": certainty,
            "reviewStatus": "agent-reviewed", "humanReviewed": False,
        }
        if category == "dieren":
            item["afbeelding"] = f"images/wiki/dieren/{source['id']}.webp"
        if note:
            item["reviewnotitie"] = note
            reviewqueue.append({"categorie": category, "type": "historische-soortidentificatie", "itemId": source["id"], "notitie": note, "reviewStatus": "needs-human-review"})
        for key in ("gebruik", "onderscheiding"):
            if source.get(key):
                item[key] = source[key]
        data["items"].append(item)
        for mention in mentions:
            per_book[mention["ref"].split(" ", 1)[0]][category] += 1

    data["dekking"] = {"boekenGescand": len(per_book), "verzenGescand": len(corpus), "perBoek": list(per_book.values())}
    return data


def _search_pattern(forms: list[str]) -> re.Pattern[str] | None:
    cleaned = [form.strip() for form in forms if form and form.strip()]
    if not cleaned:
        return None
    alternatives = []
    for form in sorted(set(cleaned), key=lambda value: (-len(value), value.casefold())):
        alternatives.append(re.escape(form).replace(r"\ ", r"\s+"))
    return re.compile(
        rf"(?:^|[^{LETTER}])(?:{'|'.join(alternatives)})(?=$|[^{LETTER}])",
        flags=re.I,
    )


def find_refs(corpus: list[VerseRef], item: dict[str, Any]) -> list[str]:
    """Vind, corrigeer en canoniek sorteer alle verwijzingen voor één item."""
    positions = {verse.ref: index for index, verse in enumerate(corpus)}
    pattern = _search_pattern(item.get("zoekvormen", []))
    found = {
        verse.ref
        for verse in corpus
        if pattern is not None
        and (not item.get("boeken") or verse.book_id in item["boeken"])
        and pattern.search(verse.text)
    }
    for ref in item.get("expliciet", []):
        if ref not in positions:
            raise ValueError(f"Ongeldige expliciete naslagverwijzing: {ref}")
        found.add(ref)
    for ref in item.get("uitsluiten", []):
        if ref not in positions:
            raise ValueError(f"Ongeldige uitgesloten naslagverwijzing: {ref}")
        found.discard(ref)
    return sorted(found, key=positions.__getitem__)


def _build_category(
    definition: dict[str, Any],
    books: list[dict[str, Any]],
    corpus: list[VerseRef],
    empty: list[dict[str, str]],
    category: str,
) -> dict[str, Any]:
    data = _base_dataset(definition["titel"], definition.get("intro", ""), books)
    seen: set[str] = set()
    for source in definition.get("items", []):
        item_id = source.get("id", "")
        if not item_id or item_id in seen:
            raise ValueError(f"Ontbrekend of dubbel item-id in {category}: {item_id!r}")
        seen.add(item_id)
        refs = find_refs(corpus, source)
        if not refs:
            empty.append({"categorie": category, "id": item_id})
            continue
        item = {
            "id": item_id,
            "naam": source["naam"],
            "beschrijving": source["beschrijving"],
            "verzen": refs,
        }
        for key in ("gebruik", "onderscheiding"):
            if source.get(key):
                item[key] = source[key]
        data["items"].append(item)
    return data


def _build_instruments(
    definition: dict[str, Any],
    books: list[dict[str, Any]],
    corpus: list[VerseRef],
    empty: list[dict[str, str]],
    reviewqueue: list[dict[str, Any]],
) -> dict[str, Any]:
    """Bouw de instrumentenindex uit alle corpusdelen met reviewmetadata."""
    data = _base_dataset(
        definition["titel"], definition.get("intro", ""), books,
        include_ethiopic=True,
    )
    data.update({
        "reviewStatus": "agent-reviewed",
        "humanReviewed": False,
        "methodiek": "expliciete instrumentcatalogus met naamvarianten en contextuele uitsluitingen, toegepast op alle 88 boeken",
    })
    verse_by_ref = {verse.ref: verse for verse in corpus}

    for source in definition.get("items", []):
        refs = find_refs(corpus, source)
        if not refs:
            empty.append({"categorie": "muziekinstrumenten", "id": source["id"]})
            continue
        canonical = [ref for ref in refs if verse_by_ref[ref].testament in {"OT", "NT"}]
        apocryphal = [ref for ref in refs if verse_by_ref[ref].testament == "AP"]
        ethiopic = [ref for ref in refs if verse_by_ref[ref].testament == "ET"]
        item = {
            "id": source["id"],
            "naam": source["naam"],
            "afbeelding": f"images/wiki/muziekinstrumenten/{source['id']}.webp",
            "beschrijving": source["beschrijving"],
            "verzen": canonical + apocryphal + ethiopic,
            "canoniekeVerzen": canonical,
            "apocriefeVerzen": apocryphal,
            "ethiopischeVerzen": ethiopic,
            "tekstvormen": source.get("zoekvormen", []),
            "zekerheid": source.get("zekerheid", "zeker"),
            "reviewStatus": "agent-reviewed",
            "humanReviewed": False,
        }
        if source.get("gebruik"):
            item["gebruik"] = source["gebruik"]
        if source.get("reviewnotitie"):
            item["reviewnotitie"] = source["reviewnotitie"]
            reviewqueue.append({
                "type": "historische-instrumentidentificatie",
                "itemId": source["id"],
                "verzen": source.get("reviewrefs", refs),
                "notitie": source["reviewnotitie"],
                "reviewStatus": "needs-human-review",
            })
        data["items"].append(item)

    for candidate in definition.get("reviewgevallen", []):
        refs = find_refs(corpus, candidate)
        reviewqueue.append({
            "type": "onzekere-muziekterm",
            "term": candidate["term"],
            "verzen": refs,
            "notitie": candidate["reden"],
            "reviewStatus": "needs-human-review",
        })

    data["dekking"] = {
        "boekenGescand": len({verse.book_id for verse in corpus}),
        "verzenGescand": len(corpus),
    }
    return data


def _base_dataset(
    title: str, intro: str, books: list[dict[str, Any]],
    include_ethiopic: bool = False,
) -> dict[str, Any]:
    return {
        "titel": title,
        "bron": "de hele Bijbel",
        "corpusbreed": True,
        "intro": intro,
        "boeknamen": {
            book["id"]: book["nameDutch"]
            for book in books
            if book.get("chaptersIncluded") and (include_ethiopic or not book.get("ethiopic"))
        },
        "items": [],
    }


def _build_people(
    definition: dict[str, Any],
    root: Path,
    books: list[dict[str, Any]],
    corpus: list[VerseRef],
    empty: list[dict[str, str]],
) -> dict[str, Any]:
    """Bouw personen zonder gelijknamige mensen met elkaar te vermengen."""
    data = _base_dataset(definition["titel"], definition.get("intro", ""), books)
    positions = {verse.ref: index for index, verse in enumerate(corpus)}
    supplements = {
        item["id"]: item for item in definition.get("aanvullingen", [])
    }
    seen: set[str] = set()
    family_tree = read_json(root / "data" / "stamboom.json")["personen"]

    for person_id, person in family_tree.items():
        if person.get("soort") == "volk":
            continue
        if person_id in seen:
            raise ValueError(f"Dubbel persoon-id in stamboom: {person_id}")
        seen.add(person_id)
        refs: set[str] = set()
        for verse in person.get("verzen", []):
            ref = f"{verse['boek']} {verse['hoofdstuk']}:{verse['vers']}"
            if ref in positions:
                refs.add(ref)

        supplement = supplements.get(person_id, {})
        if supplement:
            refs.update(find_refs(corpus, supplement))
        ordered_refs = sorted(refs, key=positions.__getitem__)
        if not ordered_refs:
            empty.append({"categorie": "personen", "id": person_id})
            continue

        description = supplement.get("beschrijving") or person.get("opmerking")
        if not description:
            first = ordered_refs[0]
            description = f"{person['naam']} wordt voor het eerst genoemd in {first}."
        item = {
            "id": person_id,
            "naam": person["naam"],
            "beschrijving": description,
            "verzen": ordered_refs,
        }
        if person.get("geslacht"):
            item["geslacht"] = person["geslacht"]
        if supplement.get("gebruik"):
            item["gebruik"] = supplement["gebruik"]
        data["items"].append(item)

    for source in definition.get("extra", []):
        person_id = source.get("id", "")
        if not person_id or person_id in seen:
            raise ValueError(f"Ontbrekend of dubbel persoon-id: {person_id!r}")
        seen.add(person_id)
        refs = find_refs(corpus, source)
        if not refs:
            empty.append({"categorie": "personen", "id": person_id})
            continue
        item = {
            "id": person_id,
            "naam": source["naam"],
            "beschrijving": source["beschrijving"],
            "verzen": refs,
        }
        for key in ("gebruik", "onderscheiding"):
            if source.get(key):
                item[key] = source[key]
        data["items"].append(item)

    people_by_name: dict[str, list[dict[str, Any]]] = {}
    for item in data["items"]:
        people_by_name.setdefault(item["naam"].casefold(), []).append(item)
    for same_name in people_by_name.values():
        if len(same_name) < 2:
            continue
        for item in same_name:
            book_id, verse = item["verzen"][0].split(" ", 1)
            book_name = data["boeknamen"].get(book_id, book_id.capitalize())
            item.setdefault(
                "onderscheiding", f"Eerste vermelding: {book_name} {verse}"
            )

    data["items"].sort(key=lambda item: positions[item["verzen"][0]])
    return data


def build_all(root: Path = ROOT, write: bool = True) -> dict[str, dict[str, Any]]:
    """Bouw alle vijf gegevenssets; `write=False` is puur en testbaar."""
    catalog = read_json(root / "data" / "naslag-catalogus.json")
    books = load_books(root)
    corpus = load_corpus(root)
    built: dict[str, dict[str, Any]] = {}
    empty: list[dict[str, str]] = []
    reviewqueue: list[dict[str, Any]] = []
    instrument_reviewqueue: list[dict[str, Any]] = []
    nature_corpus = load_corpus(root, include_ethiopic=True)
    for category, definition in catalog["categorieen"].items():
        if category in ("dieren", "bomen-planten"):
            built[category] = _build_nature_category(
                definition, books, nature_corpus, category, reviewqueue
            )
        elif category == "muziekinstrumenten":
            built[category] = _build_instruments(
                definition, books, nature_corpus, empty, instrument_reviewqueue
            )
        else:
            built[category] = _build_category(
                definition, books, corpus, empty, category
            )
    built["personen"] = _build_people(
        catalog["personen"], root, books, corpus, empty
    )
    built["materialen"] = enrich(built["materialen"])

    report = {
        "boekenGescand": len({verse.book_id for verse in corpus}),
        "verzenGescand": len(corpus),
        "itemsZonderVindplaats": empty,
        "onbekendeKandidaten": [],
    }
    nature_report = {
        "boekenGescand": len(books),
        "verzenGescand": len(nature_corpus),
        "reviewStatus": "agent-reviewed",
        "humanReviewed": False,
        "totalen": {
            category: {
                "items": len(built[category]["items"]),
                "vermeldingen": sum(len(item["vermeldingen"]) for item in built[category]["items"]),
            }
            for category in ("dieren", "bomen-planten")
        },
        "perBoek": [
            {
                "boek": book["id"],
                "dieren": next(row["dieren"] for row in built["dieren"]["dekking"]["perBoek"] if row["boek"] == book["id"]),
                "bomen-planten": next(row["bomen-planten"] for row in built["bomen-planten"]["dekking"]["perBoek"] if row["boek"] == book["id"]),
            }
            for book in books
        ],
        "reviewqueue": reviewqueue,
    }
    instrument_report = {
        "boekenGescand": built["muziekinstrumenten"]["dekking"]["boekenGescand"],
        "verzenGescand": built["muziekinstrumenten"]["dekking"]["verzenGescand"],
        "items": len(built["muziekinstrumenten"]["items"]),
        "vermeldingen": sum(
            len(item["verzen"])
            for item in built["muziekinstrumenten"]["items"]
        ),
        "reviewStatus": "agent-reviewed",
        "humanReviewed": False,
        "reviewqueue": instrument_reviewqueue,
    }

    if write:
        for category, filename in OUTPUTS.items():
            target = root / "data" / filename
            target.write_text(
                json.dumps(built[category], ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
        (root / "data" / "naslag-controle.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        (root / "data" / "naslag-natuur-controle.json").write_text(
            json.dumps(nature_report, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        (root / "data" / "naslag-muziekinstrumenten-controle.json").write_text(
            json.dumps(instrument_report, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    return built


def main() -> int:
    corpus = load_corpus(ROOT, include_ethiopic=True)
    built = build_all(ROOT, write=True)
    counts = ", ".join(f"{name}: {len(data['items'])}" for name, data in built.items())
    print(f"Corpusnaslag gebouwd uit 88 boeken en {len(corpus)} verzen ({counts})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
