#!/usr/bin/env python3
"""Bouw de compacte, canonieke runtime-index voor kaart en geografielijst.

De generator voegt de bestaande buiten-Torah-staging, de reeds beoordeelde
Torah-inventaris en de handmatig samengestelde kaartlaag samen. Bronentiteiten
houden hun stabiele id; gelijknamige plaatsen worden daardoor niet samengevoegd.
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
                add_ref(
                    feature,
                    runtime_ref(mention["ref"], mention["status"], mention.get("label")),
                )


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
            parsed = parse_torah_osis(verse.get("osis", ""))
            if parsed and parsed[1] in texts[parsed[0]]:
                uses.append(parsed)
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
        for book, key in uses:
            source_refs += 1
            label = staging_builder.exact_label(texts[book][key], labels)
            # De bron identificeert het vers; de lokale inventaris bevestigt dat
            # het vers geografische metadata bevat. Alleen een teruggevonden
            # Nederlandse vorm krijgt de sterkere agent-reviewed status.
            status = "agent-reviewed" if label and (book, key) in explicit else "needs-human-review"
            if (book, key) in explicit:
                matched_explicit_refs += 1
            ref = f"{book} {key}"
            add_ref(feature, runtime_ref(ref, status, label))
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
        for value in [props["naam"], *props.get("aliases", [])]:
            if fold(value):
                owners[fold(value)].add(entity_id)
    ref_owners: dict[str, set[str]] = defaultdict(set)
    for entity_id, feature in features.items():
        for ref in feature["properties"].get("refs", []):
            ref_owners[ref["ref"]].add(entity_id)

    enriched = 0
    appended = 0
    for old in legacy:
        props = old.get("properties", {})
        ids = owners.get(fold(props.get("naam", "")), set())
        if len(ids) != 1:
            overlap = Counter()
            for ref in props.get("verwijzingen", []):
                overlap.update(ref_owners.get(ref, set()))
            if overlap:
                best_score = max(overlap.values())
                best = {entity_id for entity_id, score in overlap.items() if score == best_score}
                if len(best) == 1:
                    ids = best
        if len(ids) == 1:
            target = features[next(iter(ids))]["properties"]
            for key in ("moderneNaam", "landModern", "toelichting"):
                if props.get(key) and not target.get(key):
                    target[key] = props[key]
            enriched += 1
            continue

        # Handmatig gepubliceerde punten zonder eenduidige crosswalk blijven
        # beschikbaar, maar worden nooit met een homoniem samengevoegd.
        coords = old.get("geometry", {}).get("coordinates")
        if not coords or len(coords) != 2:
            continue
        legacy_id = "geo-legacy-" + staging_builder.slug(props.get("naam", "plaats"))
        suffix = 2
        while legacy_id in features:
            legacy_id = f"{legacy_id}-{suffix}"
            suffix += 1
        refs = []
        for ref in props.get("verwijzingen", []):
            if parse_ref(ref):
                refs.append(runtime_ref(ref, "agent-reviewed"))
        old["properties"] = {
            **props,
            "id": legacy_id,
            "koppelingStatus": "agent-reviewed",
            "humanReviewed": False,
            "aliases": [],
            "refs": refs,
            "bron": {
                "dataset": "Open Vertaling bestaande kaartgegevens",
                "url": "https://openvertaling.nl/geografie.html",
                "onderbouwing": "Bestaand handmatig samengesteld kaartpunt; de tekstverwijzingen zijn in de runtime-index opgenomen.",
            },
        }
        features[legacy_id] = old
        appended += 1
    return {"verrijkt": enriched, "losBehouden": appended}


def build(source: Path, output: Path = OUTPUT) -> dict:
    features: dict[str, dict] = {}
    add_outside_inventory(features)
    torah_counts = add_torah_inventory(features, source)
    legacy_counts = enrich_from_legacy(features)

    published = []
    excluded = Counter()
    for path in (STAGING / "boeken").glob("*.json"):
        for item in read_json(path).get("reviewQueue", []):
            if item.get("type") == "niet-canonieke-naamtreffer":
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
