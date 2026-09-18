#!/usr/bin/env python3
"""Bouw één archeologische onderzoeksinventaris voor alle gepubliceerde plaatsen."""

from __future__ import annotations

import argparse
import copy
from collections import Counter
from datetime import date
import json
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
STATUSES = ("nog-te-onderzoeken", "archeologische-bron", "alleen-identificatie",
            "regionale-context", "geen-passende-bron-gevonden")
SOURCE_TYPES = {"opgravingsrapport", "erfgoeddossier", "onderzoeksartikel", "sitebeheerder"}


def nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def validate(dossier):
    place = dossier["plaatsId"]
    status = dossier.get("onderzoeksstatus")
    if status not in STATUSES[1:]:
        raise ValueError(f"Ongeldige onderzoeksstatus: {place}")
    if dossier.get("humanReviewed") is not False:
        raise ValueError(f"humanReviewed moet false blijven voor deze onderzoeksinventaris: {place}")
    for field in ("siteNaam", "samenvatting", "koppelingAanPlaats"):
        if not nonempty(dossier.get(field)):
            raise ValueError(f"Ontbrekend onderzoeksveld {field}: {place}")
    try:
        date.fromisoformat(dossier.get("gecontroleerdOp", ""))
    except (ValueError, TypeError) as exc:
        raise ValueError(f"Ongeldige onderzoeksdatum: {place}") from exc
    for field in ("perioden", "beperkingen"):
        if not isinstance(dossier.get(field), list) or any(not nonempty(s) for s in dossier[field]):
            raise ValueError(f"Ongeldig onderzoeksveld {field}: {place}")
    sources = dossier.get("bronnen")
    if not isinstance(sources, list):
        raise ValueError(f"Ongeldige bronnen: {place}")
    source_ids = set()
    for source in sources:
        if not all(nonempty(source.get(k)) for k in ("id", "titel", "organisatie", "url")):
            raise ValueError(f"Onvolledige bron: {place}")
        url = urlparse(source["url"])
        if url.scheme != "https" or not url.netloc or source.get("type") not in SOURCE_TYPES:
            raise ValueError(f"Ongeldige bron: {place}")
        if source["id"] in source_ids:
            raise ValueError(f"Dubbel bron-ID: {place}")
        source_ids.add(source["id"])
    findings = dossier.get("bevindingen")
    if not isinstance(findings, list) or (status != "geen-passende-bron-gevonden" and not findings):
        raise ValueError(f"Onderzoeksbevindingen ontbreken: {place}")
    if status != "geen-passende-bron-gevonden" and not sources:
        raise ValueError(f"Onderzoeksbronnen ontbreken: {place}")
    for finding in findings:
        ids = finding.get("bronIds", [])
        if not nonempty(finding.get("tekst")) or not isinstance(ids, list) or not ids or not set(ids) <= source_ids:
            raise ValueError(f"Een bevinding vereist bestaande bronverwijzingen: {place}")


def build_index(runtime: dict, documents: list[dict]) -> dict:
    entries = {}
    for feature in runtime["features"]:
        props = feature["properties"]
        place = props["id"]
        if place in entries:
            raise ValueError(f"Dubbele plaats in runtime: {place}")
        entries[place] = {
            "plaatsId": place, "onderzoeksstatus": "nog-te-onderzoeken", "humanReviewed": False,
        }
    seen = set()
    for document in documents:
        if document.get("schemaVersion") != 1 or not isinstance(document.get("dossiers"), list):
            raise ValueError("Ongeldig archeologisch brondocument.")
        for dossier in document["dossiers"]:
            place = dossier.get("plaatsId")
            if place not in entries:
                raise ValueError(f"Onbekende plaats: {place}")
            if place in seen:
                raise ValueError(f"Dubbel dossier: {place}")
            validate(dossier)
            seen.add(place)
            entries[place] = copy.deepcopy(dossier)
    counts = Counter({status: 0 for status in STATUSES})
    counts.update(item["onderzoeksstatus"] for item in entries.values())
    return {
        "schemaVersion": 1,
        "metadata": {
            "totaal": len(entries), "onderzocht": len(seen),
            "metArcheologischeBron": counts["archeologische-bron"],
            "perStatus": dict(counts), "humanReviewed": False,
            "toelichting": "Een inventarisrecord is geen afgerond onderzoek. Plaatsidentiteit en archeologische bewijsvoering zijn afzonderlijke beoordelingen.",
        },
        "dossiers": dict(sorted(entries.items())),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime", type=Path, default=DATA / "geografie-runtime.geojson")
    parser.add_argument("--data-dir", type=Path, default=DATA)
    parser.add_argument("--output", type=Path, default=DATA / "geografie-archeologie.json")
    args = parser.parse_args()
    runtime = json.loads(args.runtime.read_text(encoding="utf-8"))
    documents = [json.loads(p.read_text(encoding="utf-8"))
                 for p in sorted(args.data_dir.glob("geografie-archeologie-*.json"))]
    output = build_index(runtime, documents)
    args.output.write_text(json.dumps(output, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    print(json.dumps(output["metadata"], ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()

