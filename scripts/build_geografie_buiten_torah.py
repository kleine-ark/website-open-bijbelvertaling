"""Bouw een afgeschermde plaatsinventaris voor alle boeken buiten de Torah.

De uitvoer staat bewust onder ``data/geografie-staging/buiten-torah``. Het
script wijzigt de bestaande kaartindex en GeoJSON niet. Voor de 61 overige
boeken van de protestantse canon gebruikt het de versontdubbeling en
identificaties uit de openbare OpenBible.info-geodataset (CC BY 4.0). De
overige boeken krijgen een afzonderlijke kandidaat-inventaris; daarin wordt
niets stilzwijgend als zekere identificatie gepubliceerd.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import math
import re
import unicodedata
import urllib.request
from collections import Counter, defaultdict
from functools import lru_cache
from pathlib import Path

from geografie_versificatie import source_osis


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUTPUT = DATA / "geografie-staging" / "buiten-torah"
SOURCE_URL = (
    "https://raw.githubusercontent.com/openbibleinfo/"
    "Bible-Geocoding-Data/master/data/ancient.jsonl"
)
SOURCE_PAGE = "https://github.com/openbibleinfo/Bible-Geocoding-Data"
TORAH = {"genesis", "exodus", "leviticus", "numeri", "deuteronomium"}

OSIS_TO_BOOK = {
    "Josh": "jozua", "Judg": "richteren", "Ruth": "ruth",
    "1Sam": "1samuel", "2Sam": "2samuel", "1Kgs": "1koningen",
    "2Kgs": "2koningen", "1Chr": "1kronieken", "2Chr": "2kronieken",
    "Ezra": "ezra", "Neh": "nehemia", "Esth": "esther", "Job": "job",
    "Ps": "psalmen", "Prov": "spreuken", "Eccl": "prediker",
    "Song": "hooglied", "Isa": "jesaja", "Jer": "jeremia",
    "Lam": "klaagliederen", "Ezek": "ezechiel", "Dan": "daniel",
    "Hos": "hosea", "Joel": "joel", "Amos": "amos", "Obad": "obadja",
    "Jonah": "jona", "Mic": "micha", "Nah": "nahum", "Hab": "habakuk",
    "Zeph": "zefanja", "Hag": "haggai", "Zech": "zacharia",
    "Mal": "maleachi", "Matt": "mattheus", "Mark": "markus",
    "Luke": "lukas", "John": "johannes", "Acts": "handelingen",
    "Rom": "romeinen", "1Cor": "1korinthiers", "2Cor": "2korinthiers",
    "Gal": "galaten", "Eph": "efeziers", "Phil": "filippenzen",
    "Col": "kolossenzen", "1Thess": "1tessalonicensen",
    "2Thess": "2tessalonicensen", "1Tim": "1timotheus",
    "2Tim": "2timotheus", "Titus": "titus", "Phlm": "filemon",
    "Heb": "hebreeen", "Jas": "jakobus", "1Pet": "1petrus",
    "2Pet": "2petrus", "1John": "1johannes", "2John": "2johannes",
    "3John": "3johannes", "Jude": "judas", "Rev": "openbaring",
}

TYPE_MAP = {
    "settlement": "stad-dorp", "city": "stad-dorp", "village": "stad-dorp",
    "mountain": "berg", "mountain range": "berg", "hill": "berg",
    "river": "rivier-water", "stream": "rivier-water",
    "body of water": "rivier-water", "sea": "rivier-water",
    "lake": "rivier-water", "spring": "rivier-water",
    "desert": "woestijn", "wilderness": "woestijn", "island": "eiland",
    "valley": "dal-vlakte", "plain": "dal-vlakte", "region": "land-streek",
    "country": "land-streek", "territory": "land-streek",
}

# Deze korte of semantisch ambigue vormen worden nooit blind gemarkeerd.
AMBIGUOUS = {
    "dan", "job", "ram", "sela", "on", "no", "ar", "chebar", "eden",
    "israel", "juda", "egypte", "assur", "babel", "moab", "edom",
}


def slug(value: str) -> str:
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def bible_books() -> list[str]:
    books = []
    for directory in DATA.iterdir():
        if not directory.is_dir() or directory.name in {"geografie-staging", "vertalingen"}:
            continue
        chapters = [p for p in directory.glob("*.json") if p.stem.isdigit()]
        if chapters:
            books.append(directory.name)
    return sorted(books)


def verses_for_book(book: str) -> dict[str, str]:
    result = {}
    chapters = sorted(
        (p for p in (DATA / book).glob("*.json") if p.stem.isdigit()),
        key=lambda p: int(p.stem),
    )
    for path in chapters:
        chapter = int(path.stem)
        for verse in read_json(path)["verses"]:
            result[f"{chapter}:{verse['number']}"] = verse["text2026"]
    return result


def parse_osis(value: str):
    match = re.fullmatch(r"([^.]+)\.(\d+)\.(\d+)(?:-.*)?", value)
    if not match or match.group(1) not in OSIS_TO_BOOK:
        return None
    return OSIS_TO_BOOK[match.group(1)], f"{int(match.group(2))}:{int(match.group(3))}"


def source_rows(source: Path):
    with source.open(encoding="utf-8") as handle:
        for line in handle:
            yield json.loads(line)


def choose_resolution(row: dict):
    candidates = {}
    special_options = []
    for identification in row.get("identifications", []):
        scores = identification.get("score", {})
        time_score = max(0, min(1000, scores.get("time_total", 0)))
        for resolution in identification.get("resolutions", []):
            # Volg ook tussenstappen: de bron definieert modern_associations
            # als time_total * best_time_score / 1000, niet vote_average.
            score = time_score * max(0, min(1000, resolution.get("best_time_score", 1000))) / 1000
            if resolution.get("special"):
                special_options.append((score, resolution.get("special"), identification.get("description", "")))
                continue
            lonlat = resolution.get("lonlat")
            if not lonlat:
                continue
            try:
                lon, lat = (float(part) for part in lonlat.split(","))
            except (TypeError, ValueError):
                continue
            if not (math.isfinite(lon) and math.isfinite(lat) and -180 <= lon <= 180 and -90 <= lat <= 90):
                continue
            key = (resolution.get("modern_basis_id"), lon, lat)
            if key not in candidates or candidates[key][0] < score:
                candidates[key] = (score, lon, lat, identification, resolution)
    if not candidates:
        return None
    candidates = list(candidates.values())
    candidates.sort(key=lambda item: item[0], reverse=True)
    score, lon, lat, identification, resolution = candidates[0]
    special_options.sort(key=lambda item: item[0], reverse=True)
    preferred_special = special_options[0] if special_options and special_options[0][0] >= score else None
    # Een voorkeurslezing 'persoon/geen plaats' met sterke bronweging wordt
    # niet als stad gepubliceerd. De bronrij blijft in de review-inventaris.
    if score <= 0 or (preferred_special and preferred_special[1] == "not_a_place" and preferred_special[0] >= 500):
        return None
    tied = sum(1 for item in candidates if item[0] == score) > 1
    # Publicatielabels zijn conservatieve categorieën, geen kanspercentages.
    confidence = "onzeker" if tied or preferred_special or score < 500 else "waarschijnlijk"
    if not tied and not preferred_special and score >= 900 and identification.get("score", {}).get("vote_total", 0) >= 500:
        confidence = "zeker"
    description = resolution.get("description", identification.get("description", ""))
    modern_name = re.search(r"<modern\b[^>]*>(.*?)</modern>", description)
    return {
        "lat": lat,
        "lon": lon,
        "zekerheid": confidence,
        "bron": {
            "dataset": "OpenBible.info Bible Geocoding Data",
            "url": f"https://www.openbible.info/geo/ancient/{row['id']}/{row.get('url_slug', slug(row['friendly_id']))}",
            "datasetUrl": SOURCE_PAGE,
            "ancientId": row["id"],
            "identificationId": identification.get("id"),
            "modernId": resolution.get("modern_basis_id"),
            "moderneNaam": (plain_description(modern_name.group(1)) if modern_name else
                            row.get("modern_associations", {}).get(resolution.get("modern_basis_id"), {}).get("name", "")),
            "onderbouwing": plain_description(description),
            "score": score,
            "scoreType": "time_total × best_time_score / 1000",
            "scores": identification.get("score", {}),
            "puntType": " / ".join(str(resolution[key]) for key in ("lonlat_type", "ancient_geometry") if resolution.get(key)),
            "voorkeursInterpretatie": plain_description(preferred_special[2]) if preferred_special else "",
            "alternatieven": [
                {"modernId": item[4].get("modern_basis_id"), "lon": item[1], "lat": item[2],
                 "score": item[0], "onderbouwing": plain_description(item[4].get("description", ""))}
                for item in candidates[1:]
            ],
        },
        "betwist": bool(preferred_special) or tied or len(candidates) > 1,
    }


def plain_description(value: str) -> str:
    return html.unescape(re.sub(r"<[^>]*>", "", value)).strip()


def entity_type(row: dict) -> str:
    values = list(row.get("types", []))
    for identification in row.get("identifications", []):
        values.extend(identification.get("types", []))
    for value in values:
        if value in TYPE_MAP:
            return TYPE_MAP[value]
    return "plaats"


def possible_labels(row: dict) -> list[str]:
    # Per bronidentiteit gecontroleerde SV-vormen. Globale Engelse varianten
    # zoals Ashan -> Ain mogen niet het andere woord in hetzelfde vers stelen.
    verified = {
        "ab5175f": ["Asan", "Ashan"],
        "ac24f5f": ["Gibeä", "Gibea", "Gibeah"],
        "ae981db": ["Seïr", "Seir"],
    }
    if row.get("id") in verified:
        return verified[row["id"]]
    labels = [row.get("friendly_id", "")]
    labels.extend(name for name, entity_id in legacy_crosswalk().items() if entity_id == stable_id(row))
    labels.extend(row.get("translation_name_counts", {}).keys())
    labels.extend(item.get("name", "") for item in row.get("names", []))
    return sorted({label.strip() for label in labels if label.strip()}, key=lambda label: (-len(label), label.casefold()))


def exact_label(text: str, labels: list[str]):
    for label in labels:
        match = re.search(rf"(?<!\w){re.escape(label)}(?!\w)", text, flags=re.IGNORECASE)
        if match:
            return text[match.start():match.end()]
    return None


def stable_id(row: dict) -> str:
    # De bron-ID maakt homoniemen stabiel en ondubbelzinnig.
    return f"geo-{slug(row['friendly_id'])}-{row['id'][1:]}"


@lru_cache(maxsize=1)
def legacy_crosswalk() -> dict:
    return read_json(DATA / "geografie-staging" / "legacy-crosswalk.json")


def review_colliding_mentions(mentions: list[dict]) -> None:
    owners = defaultdict(set)
    for mention in mentions:
        if mention.get("label"):
            owners[mention["label"].casefold()].add(mention["entityId"])
    for mention in mentions:
        if mention.get("label") and len(owners[mention["label"].casefold()]) > 1:
            mention["status"] = "needs-human-review"


def build(source: Path):
    books = [book for book in bible_books() if book not in TORAH]
    text = {book: verses_for_book(book) for book in books}
    entities = {}
    per_book = {book: defaultdict(list) for book in books}
    review = {book: [] for book in books}
    alias_hits = defaultdict(lambda: defaultdict(list))
    unlocated = []

    # Eerst de bron-gedisambigueerde 66-boekencorpus verwerken.
    for row in source_rows(source):
        resolution = choose_resolution(row)
        if not resolution:
            unlocated.append({"entityId": stable_id(row), "naam": row["friendly_id"],
                              "bron": f"https://www.openbible.info/geo/ancient/{row['id']}/{row.get('url_slug', slug(row['friendly_id']))}",
                              "reden": "Geen publiceerbaar punt; onbekende locatie, onvoldoende bronweging of voorkeurslezing geen plaats.",
                              "status": "needs-human-review", "humanReviewed": False})
            continue
        entity_id = stable_id(row)
        labels = possible_labels(row)
        entity = {
            "id": entity_id,
            "slug": entity_id[4:],
            "naam": row["friendly_id"],
            "type": entity_type(row),
            "punt": {"lat": resolution["lat"], "lon": resolution["lon"]},
            "zekerheid": resolution["zekerheid"],
            "coordinatenBron": resolution["bron"],
            "synoniemenInTekst": [],
            "status": "agent-reviewed",
            "humanReviewed": False,
        }
        used = False
        for verse in row.get("verses", []):
            parsed = parse_osis(source_osis(verse))
            if not parsed:
                continue
            book, key = parsed
            if book in TORAH or book not in text or key not in text[book]:
                continue
            used = True
            label = exact_label(text[book][key], labels)
            status = "agent-reviewed" if label and slug(label) not in AMBIGUOUS else "needs-human-review"
            mention = {
                "entityId": entity_id,
                "ref": f"{book} {key}",
                "href": f"index.html#{book}/{key.replace(':', '/')}",
                "label": label,
                "status": status,
                "bronVerskoppeling": "OpenBible.info verse disambiguation",
                "bronOsis": verse.get("osis", ""),
                "lokaleOsis": source_osis(verse),
            }
            per_book[book][key].append(mention)
            if status == "agent-reviewed":
                alias_hits[entity_id][label].append(f"{book} {key}")
            else:
                review[book].append({
                    "type": "label-of-homoniem",
                    "entityId": entity_id,
                    "ref": f"{book} {key}",
                    "tekst": text[book][key],
                    "reden": "Geen eenduidige Nederlandse plaatsvorm gevonden of de vorm is contextueel ambigu.",
                    "status": "needs-human-review",
                })
        if used:
            if resolution["betwist"]:
                entity["status"] = "needs-human-review"
            entities[entity_id] = entity

    # Een overeenkomstige tekstvorm bewijst bij meerdere bronentiteiten geen
    # identiteit. Neem zulke Engelse vertaalvarianten niet als NL-aliassen over.
    alias_hits.clear()
    for book, verses in per_book.items():
        for key, mentions in verses.items():
            previously_reviewed = {item["entityId"] for item in mentions if item["status"] == "agent-reviewed"}
            review_colliding_mentions(mentions)
            for item in mentions:
                if item["status"] == "agent-reviewed":
                    alias_hits[item["entityId"]][item["label"]].append(item["ref"])
                elif item["entityId"] in previously_reviewed:
                    review[book].append({"type": "labelbotsing-in-vers", "entityId": item["entityId"],
                                         "ref": item["ref"], "tekst": text[book][key],
                                         "reden": "Dezelfde tekstvorm wordt aan meerdere bronentiteiten gekoppeld.",
                                         "status": "needs-human-review"})

    for entity_id, labels in alias_hits.items():
        folded = {}
        for label, refs in labels.items():
            key = label.casefold()
            if key not in folded:
                folded[key] = {"vorm": label, "vindplaatsen": []}
            folded[key]["vindplaatsen"].extend(refs)
        entities[entity_id]["synoniemenInTekst"] = sorted(
            (
                {"vorm": item["vorm"], "vindplaatsen": sorted(set(item["vindplaatsen"]))}
                for item in folded.values()
            ),
            key=lambda item: item["vorm"].casefold(),
        )

    # Niet-protestantse boeken: alleen expliciete naamtreffers als kandidaten.
    # Dit vermijdt dat persoonsnamen en gelijknamige plaatsen automatisch tags worden.
    canonical_books = set(OSIS_TO_BOOK.values()) | TORAH
    aliases = []
    for entity in entities.values():
        for alias in entity["synoniemenInTekst"]:
            form = alias["vorm"]
            if len(form) >= 4 and form.casefold() not in AMBIGUOUS:
                aliases.append((form, entity["id"]))
    aliases.sort(key=lambda item: len(item[0]), reverse=True)
    for book in books:
        if book in canonical_books:
            continue
        for key, verse_text in text[book].items():
            seen = set()
            for form, entity_id in aliases:
                if entity_id in seen:
                    continue
                match = re.search(rf"(?<!\w){re.escape(form)}(?!\w)", verse_text, re.IGNORECASE)
                if not match:
                    continue
                seen.add(entity_id)
                review[book].append({
                    "type": "niet-canonieke-naamtreffer",
                    "entityId": entity_id,
                    "ref": f"{book} {key}",
                    "label": verse_text[match.start():match.end()],
                    "tekst": verse_text,
                    "reden": "Naamtreffer buiten de 66-boekenbron; identiteit en geografische betekenis vereisen menselijke controle.",
                    "status": "needs-human-review",
                })

    OUTPUT.mkdir(parents=True, exist_ok=True)
    (OUTPUT / "niet-gepubliceerde-punten.json").write_text(
        json.dumps({"status": "needs-human-review", "humanReviewed": False, "plaatsen": unlocated},
                   ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (OUTPUT / "boeken").mkdir(exist_ok=True)
    counts = Counter()
    total_verses = 0
    total_mentions = 0
    for book in books:
        total_verses += len(text[book])
        mentions = {key: value for key, value in sorted(per_book[book].items())}
        total_mentions += sum(len(value) for value in mentions.values())
        counts.update(m["status"] for values in mentions.values() for m in values)
        payload = {
            "schemaVersion": 1,
            "boek": book,
            "scope": "buiten-torah",
            "status": "agent-reviewed",
            "humanReviewed": False,
            "dekking": {
                "verzenBeoordeeld": len(text[book]),
                "verzenMetBronvermelding": len(mentions),
                "vermeldingen": sum(len(value) for value in mentions.values()),
                "reviewQueue": len(review[book]),
            },
            "mentions": mentions,
            "reviewQueue": review[book],
        }
        (OUTPUT / "boeken" / f"{book}.json").write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )

    entity_payload = {
        "schemaVersion": 1,
        "scope": "buiten-torah",
        "status": "agent-reviewed",
        "humanReviewed": False,
        "bron": {"naam": "OpenBible.info Bible Geocoding Data", "url": SOURCE_PAGE, "licentie": "CC BY 4.0"},
        "entities": sorted(entities.values(), key=lambda item: item["id"]),
    }
    (OUTPUT / "entities.json").write_text(
        json.dumps(entity_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    alias_owners = defaultdict(set)
    for entity in entities.values():
        for alias in entity["synoniemenInTekst"]:
            alias_owners[alias["vorm"].casefold()].add(entity["id"])
    collisions = [
        {
            "vorm": form,
            "entityIds": sorted(owners),
            "reden": "Dezelfde tekstvorm hoort bij meer dan één geografische entiteit; contextueel beoordelen.",
            "status": "needs-human-review",
        }
        for form, owners in sorted(alias_owners.items())
        if len(owners) > 1
    ]
    (OUTPUT / "alias-botsingen.json").write_text(
        json.dumps(
            {"schemaVersion": 1, "status": "needs-human-review", "botsingen": collisions},
            ensure_ascii=False,
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )
    category_counts = Counter(entity["type"] for entity in entities.values())
    confidence_counts = Counter(entity["zekerheid"] for entity in entities.values())
    manifest = {
        "schemaVersion": 1,
        "scope": "alle-88-boeken-buiten-torah",
        "status": "agent-reviewed",
        "humanReviewed": False,
        "publicatieStatus": "staging-niet-samenvoegen-zonder-afstemming",
        "bronSha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "nietGeplaatsteBronentiteiten": len(unlocated),
        "boeken": books,
        "aantallen": {
            "boeken": len(books), "verzenBeoordeeld": total_verses,
            "entiteiten": len(entities), "vermeldingen": total_mentions,
            "agentReviewedVermeldingen": counts["agent-reviewed"],
            "teBeoordelenVermeldingen": counts["needs-human-review"],
            "reviewQueueTotaal": sum(len(items) for items in review.values()),
            "aliasBotsingen": len(collisions),
            "perCategorie": dict(sorted(category_counts.items())),
            "perZekerheid": dict(sorted(confidence_counts.items())),
        },
    }
    (OUTPUT / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return manifest


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, help="lokale ancient.jsonl; anders downloaden naar TEMP")
    args = parser.parse_args()
    source = args.source
    if source is None:
        source = Path.home() / ".cache" / "open-vertaling" / "openbible-ancient.jsonl"
        source.parent.mkdir(parents=True, exist_ok=True)
        if not source.exists():
            urllib.request.urlretrieve(SOURCE_URL, source)
    manifest = build(source)
    print(json.dumps(manifest["aantallen"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
