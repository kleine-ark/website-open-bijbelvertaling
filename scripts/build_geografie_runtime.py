#!/usr/bin/env python3
"""Bouw de compacte, canonieke runtime-index voor kaart en geografielijst.

De generator voegt de buiten-Torah-staging en Torah-bronvermeldingen samen.
Gecontroleerde namen uit de oude kaartlaag worden als aliassen toegevoegd;
onopgeloste oude punten blijven in de review-inventaris. Bronentiteiten houden
hun stabiele id; gelijknamige plaatsen worden niet op alleen hun naam verenigd.
Alle output blijft expliciet ``humanReviewed: false`` zolang dat voor de bron zo
is. Waarschijnlijke en onzekere punten worden wel gepubliceerd, met hun label.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
STAGING = DATA / "geografie-staging" / "buiten-torah"
OUTPUT = DATA / "geografie-runtime.geojson"
SOURCE_CACHE = Path.home() / ".cache" / "open-vertaling" / "openbible-ancient.jsonl"
TORAH_OSIS = {
    "Gen": "genesis",
    "Exod": "exodus",
    "Lev": "leviticus",
    "Num": "numeri",
    "Deut": "deuteronomium",
}

# Hergebruik exact dezelfde bronresolutie en stabiele ids als de stagingbouw.
sys.path.insert(0, str(Path(__file__).parent))
import build_geografie_buiten_torah as staging_builder  # noqa: E402
from geografie_reviewbesluiten import apply_reviews  # noqa: E402


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def fold(value: str) -> str:
    value = unicodedata.normalize("NFKD", value or "")
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9]+", "", value.casefold())


def parse_ref(ref: str) -> tuple[str, int, int] | None:
    match = re.fullmatch(r"([^ ]+) (\d+):(\d+)", ref)
    if not match:
        return None
    return match.group(1), int(match.group(2)), int(match.group(3))


def runtime_ref(ref: str, status: str, label: str | None = None) -> dict:
    parsed = parse_ref(ref)
    if not parsed:
        raise ValueError(f"Ongeldige verwijzing: {ref}")
    book, chapter, verse = parsed
    item = {
        "boek": book,
        "hoofdstuk": chapter,
        "vers": verse,
        "ref": ref,
        "href": f"index.html#{book}/{chapter}/{verse}",
        "status": status,
    }
    if label:
        item["label"] = label
    return item


def empty_feature(entity: dict) -> dict:
    point = entity["punt"]
    return {
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [point["lon"], point["lat"]]},
        "properties": {
            "id": entity["id"],
            "naam": entity["naam"],
            "type": entity.get("type", "plaats"),
            "zekerheid": entity.get("zekerheid", "onzeker"),
            "koppelingStatus": entity.get("status", "needs-human-review"),
            "humanReviewed": bool(entity.get("humanReviewed", False)),
            "aliases": sorted(
                {alias["vorm"] for alias in entity.get("synoniemenInTekst", []) if alias.get("vorm")},
                key=str.casefold,
            ),
            "refs": [],
            "bron": entity.get("coordinatenBron", {}),
            "moderneNaam": entity.get("coordinatenBron", {}).get("moderneNaam", ""),
        },
    }


def add_ref(feature: dict, item: dict) -> None:
    refs = feature["properties"]["refs"]
    signature = (item["boek"], item["hoofdstuk"], item["vers"])
    existing = next(
        (ref for ref in refs if (ref["boek"], ref["hoofdstuk"], ref["vers"]) == signature),
        None,
    )
    if existing:
        # Een agent-beoordeelde koppeling is sterker dan een wachtrijstatus.
        if item["status"] == "agent-reviewed":
            existing.update(item)
        return
    refs.append(item)


def add_outside_inventory(features: dict[str, dict]) -> None:
    entities = read_json(STAGING / "entities.json")["entities"]
    for entity in entities:
        features[entity["id"]] = empty_feature(entity)

    for path in sorted((STAGING / "boeken").glob("*.json")):
        book = read_json(path)
        for mentions in book.get("mentions", {}).values():
            for mention in mentions:
                feature = features.get(mention["entityId"])
                if not feature:
                    continue
                ref = runtime_ref(mention["ref"], mention["status"], mention.get("label"))
                if mention.get("bronOsis"):
                    ref["bronOsis"] = mention["bronOsis"]
                add_ref(feature, ref)


def parse_torah_osis(value: str) -> tuple[str, str] | None:
    match = re.fullmatch(r"([^.]+)\.(\d+)\.(\d+)(?:-.*)?", value)
    if not match or match.group(1) not in TORAH_OSIS:
        return None
    return TORAH_OSIS[match.group(1)], f"{int(match.group(2))}:{int(match.group(3))}"


def torah_inventory() -> tuple[dict[tuple[str, str], list[dict]], dict[str, dict[str, str]]]:
    mentions = {}
    texts = {}
    for book in TORAH_OSIS.values():
        payload = read_json(DATA / f"{book}-geo.json")
        mentions.update({(book, key): values for key, values in payload.get("mentions", {}).items()})
        texts[book] = staging_builder.verses_for_book(book)
    return mentions, texts


def add_torah_inventory(features: dict[str, dict], source: Path) -> dict:
    explicit, texts = torah_inventory()
    source_refs = 0
    matched_explicit_refs = 0
    for row in staging_builder.source_rows(source):
        resolution = staging_builder.choose_resolution(row)
        if not resolution:
            continue
        uses = []
        for verse in row.get("verses", []):
            parsed = parse_torah_osis(staging_builder.source_osis(verse))
            if parsed and parsed[1] in texts[parsed[0]]:
                uses.append((*parsed, verse.get("osis", "")))
        if not uses:
            continue

        entity_id = staging_builder.stable_id(row)
        if entity_id not in features:
            features[entity_id] = empty_feature({
                "id": entity_id,
                "naam": row["friendly_id"],
                "type": staging_builder.entity_type(row),
                "punt": {"lat": resolution["lat"], "lon": resolution["lon"]},
                "zekerheid": resolution["zekerheid"],
                "coordinatenBron": resolution["bron"],
                "synoniemenInTekst": [],
                "status": "needs-human-review" if resolution["betwist"] else "agent-reviewed",
                "humanReviewed": False,
            })
        feature = features[entity_id]
        labels = staging_builder.possible_labels(row)
        for book, key, source_ref in uses:
            source_refs += 1
            label = staging_builder.exact_label(texts[book][key], labels)
            # Niet alleen hetzelfde vers, maar dezelfde Nederlandse labelvorm
            # moet in de lokale inventaris staan. Ambigue namen blijven review.
            same_label = label and any(fold(item.get("label", "")) == fold(label) for item in explicit.get((book, key), []))
            status = "agent-reviewed" if same_label and staging_builder.slug(label) not in staging_builder.AMBIGUOUS else "needs-human-review"
            if (book, key) in explicit:
                matched_explicit_refs += 1
            ref = f"{book} {key}"
            reference = runtime_ref(ref, status, label)
            reference["bronOsis"] = source_ref
            add_ref(feature, reference)
            if label and label not in feature["properties"]["aliases"]:
                feature["properties"]["aliases"].append(label)

    return {
        "bronvermeldingen": source_refs,
        "bronvermeldingenMetLokaleInventaris": matched_explicit_refs,
        "lokaleInventarisVermeldingen": sum(len(items) for items in explicit.values()),
    }


def enrich_from_legacy(features: dict[str, dict]) -> dict:
    legacy = read_json(DATA / "geografie.geojson").get("features", [])
    owners: dict[str, set[str]] = defaultdict(set)
    for entity_id, feature in features.items():
        props = feature["properties"]
        for value in [props["naam"], re.sub(r" \d+$", "", props["naam"]), *props.get("aliases", [])]:
            if fold(value):
                owners[fold(value)].add(entity_id)
    # Gecontroleerde Nederlandse namen voor dezelfde bronidentiteit. Andere
    # homoniemen mogen alleen via naam EN gedeelde verwijzing worden verbonden.
    crosswalk = {fold(name): entity_id for name, entity_id in staging_builder.legacy_crosswalk().items()}
    enriched = 0
    pending = []
    for old in legacy:
        props = old.get("properties", {})
        name = fold(props.get("naam", ""))
        ids = {crosswalk[name]} if name in crosswalk else owners.get(name, set())
        old_refs = set(props.get("verwijzingen", []))
        ids = {entity_id for entity_id in ids if entity_id in features and
               old_refs.intersection(ref["ref"] for ref in features[entity_id]["properties"].get("refs", []))}
        if len(ids) == 1:
            target = features[next(iter(ids))]["properties"]
            if props.get("naam") not in target["aliases"]:
                target["aliases"].append(props["naam"])
            old_id = "geo-legacy-" + staging_builder.slug(props.get("naam", "plaats"))
            if old_id not in target.setdefault("legacyIds", []):
                target["legacyIds"].append(old_id)
            # De moderne naam/omschrijving hoort bij de gekozen bronresolutie,
            # niet bij een oude (mogelijk concurrerende) coördinaat.
            enriched += 1
            continue

        # Oude punten zonder controleerbare identiteit zijn geen extra plaatsen.
        # Bewaar ze volledig in de bronlaag en expliciet in de review-inventaris.
        pending.append({"naam": props.get("naam"), "verwijzingen": sorted(old_refs),
                        "reden": "Geen eenduidige bronidentiteit; controleer naam, homoniem en coördinaat.",
                        "status": "needs-human-review"})
    return {"verrijkt": enriched, "losBehouden": 0, "teControleren": pending}


def apply_location_preferences(features: dict[str, dict]) -> None:
    """Gebruik redactioneel gekozen bronkandidaten zonder hun zekerheid te verhogen."""
    path = DATA / "geografie-locatievoorkeuren.json"
    if not path.exists():
        return
    document = read_json(path)
    if document.get("schemaVersion") != 1:
        raise ValueError("Onbekend schema voor locatievoorkeuren")
    for preference in document["voorkeuren"]:
        for place_id in preference["plaatsIds"]:
            feature = features[place_id]
            props = feature["properties"]
            source = props["bron"]
            # Een reeds toegepast voorkeurspunt blijft bij herhaald toepassen gelijk.
            if source.get("kaartVoorkeur", {}).get("modernId") == preference["modernId"]:
                continue
            candidates = source.get("alternatieven", [])
            candidate = next((item for item in candidates if item.get("modernId") == preference["modernId"]), None)
            if not candidate:
                raise ValueError(f"Locatievoorkeur is geen bestaande bronkandidaat: {place_id}")
            original = {
                "modernId": source.get("modernId"),
                "lon": feature["geometry"]["coordinates"][0],
                "lat": feature["geometry"]["coordinates"][1],
                "score": source.get("score"),
                "onderbouwing": source.get("onderbouwing"),
            }
            source["alternatieven"] = [original] + [item for item in candidates if item is not candidate]
            source["kaartVoorkeur"] = {
                "modernId": preference["modernId"], "url": preference["bronUrl"],
                "titel": preference["bronTitel"], "oorspronkelijkeModernId": original["modernId"],
            }
            source["voorkeursInterpretatie"] = preference["toelichting"]
            # Bron-id, bronweging en oorspronkelijke bronvoorkeur blijven intact.
            source["onderbouwing"] = (source.get("onderbouwing") or "") + ". Dit is de oorspronkelijke bronvoorkeur; het weergegeven kaartpunt volgt de locatievoorkeur hierboven."
            feature["geometry"]["coordinates"] = [candidate["lon"], candidate["lat"]]
            props["moderneNaam"] = "Jabal al-Lawz" if props["type"] == "berg" else "Omgeving van Jabal al-Lawz"
            props["landModern"] = preference["landModern"]
            props["zekerheid"] = "onzeker"
            props["toelichting"] = preference["toelichting"]


def build(source: Path, output: Path = OUTPUT) -> dict:
    features: dict[str, dict] = {}
    add_outside_inventory(features)
    torah_counts = add_torah_inventory(features, source)
    reviewed = apply_reviews(features)
    legacy_counts = enrich_from_legacy(features)
    apply_location_preferences(features)
    legacy_review = legacy_counts.pop("teControleren")
    legacy_counts["teControleren"] = len(legacy_review)
    (STAGING / "legacy-review.json").write_text(
        json.dumps({"humanReviewed": False, "plaatsen": legacy_review}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    published = []
    excluded = Counter()
    for path in (STAGING / "boeken").glob("*.json"):
        for item in read_json(path).get("reviewQueue", []):
            if item.get("type") == "niet-canonieke-naamtreffer":
                if (item.get("entityId"), item.get("ref")) not in reviewed["settled"]:
                    excluded["apocrief-of-ethiopisch-naamskandidaat-zonder-bevestigde-puntkoppeling"] += 1
    for feature in features.values():
        geometry = feature.get("geometry", {})
        coords = geometry.get("coordinates")
        if geometry.get("type") != "Point" or not coords or len(coords) != 2:
            excluded["geen-valide-puntcoordinaat"] += 1
            continue
        lon, lat = coords
        if not (-180 <= lon <= 180 and -90 <= lat <= 90):
            excluded["coordinaat-buiten-bereik"] += 1
            continue
        props = feature["properties"]
        props["aliases"] = sorted(set(props.get("aliases", [])), key=str.casefold)
        props["refs"] = sorted(
            props.get("refs", []),
            key=lambda r: (r["boek"], r["hoofdstuk"], r["vers"]),
        )
        props["verwijzingen"] = [ref["ref"] for ref in props["refs"]]
        if not props["refs"]:
            excluded["geen-bijbelverwijzing"] += 1
            continue
        published.append(feature)

    published.sort(key=lambda f: (f["properties"]["naam"].casefold(), f["properties"]["id"]))
    refs = [ref for feature in published for ref in feature["properties"]["refs"]]
    books = Counter(ref["boek"] for ref in refs)
    confidence = Counter(f["properties"].get("zekerheid", "onzeker") for f in published)
    statuses = Counter(ref["status"] for ref in refs)
    metadata = {
        "schemaVersion": 2,
        "titel": "Canonieke geografische runtime-index",
        "status": "agent-reviewed",
        "humanReviewed": False,
        "punten": len(published),
        "verwijzingen": len(refs),
        "uniekeVerzen": len({(r["boek"], r["hoofdstuk"], r["vers"]) for r in refs}),
        "boekenMetPunten": len(books),
        "perBoek": dict(sorted(books.items())),
        "perZekerheid": dict(sorted(confidence.items())),
        "perKoppelingStatus": dict(sorted(statuses.items())),
        "torah": torah_counts,
        "legacy": legacy_counts,
        "inhoudelijkeControle": reviewed["metadata"],
        "bronSha256": read_json(STAGING / "manifest.json").get("bronSha256"),
        "nietGeplaatsteBronentiteiten": read_json(STAGING / "manifest.json").get("nietGeplaatsteBronentiteiten", 0),
        "uitgesloten": dict(sorted(excluded.items())),
        "toelichting": "Onzekere punten zijn zichtbaar als zodanig; humanReviewed blijft false voor agentinventarisatie.",
    }
    output.write_text(
        json.dumps({"type": "FeatureCollection", "metadata": metadata, "features": published}, ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    return metadata


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=SOURCE_CACHE)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    if not args.source.exists():
        args.source.parent.mkdir(parents=True, exist_ok=True)
        staging_builder.urllib.request.urlretrieve(staging_builder.SOURCE_URL, args.source)
    print(json.dumps(build(args.source, args.output), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
