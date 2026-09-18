#!/usr/bin/env python3
"""Pas expliciet onderbouwde geografische tekstbesluiten reproduceerbaar toe."""

from __future__ import annotations

import hashlib
import json
import math
import re
from collections import Counter
from functools import lru_cache
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
REVIEW_DIR = ROOT / "data" / "geografie-staging" / "reviews"


@lru_cache(maxsize=None)
def chapter_texts(book: str, chapter: int) -> dict[int, str]:
    path = ROOT / "data" / book / f"{chapter}.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    return {v["number"]: v["text2026"] for v in payload["verses"]}


def split_ref(ref: str) -> tuple[str, int, int]:
    match = re.fullmatch(r"([a-z0-9]+) ([1-9]\d*):([1-9]\d*)", ref or "")
    if not match:
        raise ValueError(f"Ongeldige reviewverwijzing: {ref}")
    return match[1], int(match[2]), int(match[3])


def verse_text(ref: str) -> str:
    book, chapter, verse = split_ref(ref)
    try:
        return chapter_texts(book, chapter)[verse]
    except (OSError, KeyError) as exc:
        raise ValueError(f"Reviewvers ontbreekt: {ref}") from exc


def source_url(value: str) -> bool:
    parsed = urlparse(value or "")
    return parsed.scheme == "https" and bool(parsed.netloc)


def new_feature(entity: dict) -> dict:
    point = entity.get("punt", {})
    coords = [point.get("lon"), point.get("lat")]
    if (any(isinstance(n, bool) or not isinstance(n, (int, float)) or not math.isfinite(n) for n in coords)
            or not (-180 <= coords[0] <= 180 and -90 <= coords[1] <= 90)):
        raise ValueError(f"Ongeldig reviewpunt: {entity.get('id')}")
    source = entity.get("coordinatenBron", {})
    if not source_url(source.get("url")) or not source.get("onderbouwing"):
        raise ValueError(f"Controleerbare coördinatenbron ontbreekt: {entity.get('id')}")
    if entity.get("humanReviewed") is not False or not entity.get("naam"):
        raise ValueError("Een aanvullende entiteit moet als agentcontrole herkenbaar zijn.")
    return {
        "type": "Feature", "geometry": {"type": "Point", "coordinates": coords},
        "properties": {
            "id": entity["id"], "naam": entity["naam"], "type": entity.get("type", "plaats"),
            "zekerheid": entity.get("zekerheid", "onzeker"),
            "koppelingStatus": "agent-reviewed", "humanReviewed": False, "aliases": [],
            "refs": [], "bron": source, "moderneNaam": source.get("moderneNaam", ""),
        },
    }


def apply_reviews(features: dict, directory: Path = REVIEW_DIR, text_loader=verse_text) -> dict:
    """Valideer alle bestanden voordat beslissingen de runtime-index wijzigen."""
    documents = [(p, json.loads(p.read_text(encoding="utf-8")))
                 for p in sorted(directory.glob("*.json"))]
    additions, decisions = {}, {}
    stats = Counter({"confirmed": 0, "rejected": 0, "needs-human-review": 0, "stale": 0,
                     "duplicates": 0, "unresolvedCandidates": 0})
    for path, doc in documents:
        if doc.get("schemaVersion") != 1 or doc.get("humanReviewed") is not False or not doc.get("scope"):
            raise ValueError(f"Ongeldig reviewdocument: {path.name}")
        stats["unresolvedCandidates"] += len(doc.get("unresolvedCandidates", []))
        for entity in doc.get("entities", []):
            entity_id = entity.get("id")
            if not entity_id or entity_id in features or entity_id in additions:
                raise ValueError(f"Dubbele/ontbrekende reviewentiteit: {entity_id}")
            additions[entity_id] = new_feature(entity)

    for path, doc in documents:
        for decision in doc.get("decisions", []):
            entity_id, ref = decision.get("entityId"), decision.get("ref")
            if not isinstance(entity_id, str) or not entity_id.strip():
                raise ValueError("Een reviewbesluit vereist een niet-leeg entiteit-ID.")
            split_ref(ref)
            status = decision.get("decision")
            if status not in {"confirmed", "rejected", "needs-human-review"}:
                raise ValueError(f"Ongeldig reviewbesluit: {ref}")
            if entity_id not in features and entity_id not in additions and status != "rejected":
                raise ValueError(f"Onbekende entiteit: {entity_id}")
            fingerprint = decision.get("textSha256", "")
            if not re.fullmatch(r"[0-9a-f]{64}", fingerprint):
                raise ValueError(f"textSha256 ontbreekt/is ongeldig: {ref}")
            if not decision.get("reason"):
                raise ValueError(f"Onderbouwing ontbreekt: {ref}")
            sources = decision.get("sources", [])
            if any(not source.get("title") or not source_url(source.get("url")) for source in sources):
                raise ValueError(f"Ongeldige reviewbron: {ref}")
            kind = decision.get("mentionType", "explicit")
            if kind not in {"explicit", "origin", "contextual"}:
                raise ValueError(f"Ongeldig vermeldingstype: {ref}")
            text = text_loader(ref)
            stale = hashlib.sha256(text.encode("utf-8")).hexdigest() != fingerprint
            label = decision.get("label")
            if not stale and label and not re.search(r"(?<!\w)" + re.escape(label) + r"(?!\w)", text, re.I):
                raise ValueError(f"Label ontbreekt als volledige tekstvorm: {ref}: {label}")
            if not stale and status == "confirmed" and not label and kind != "contextual":
                raise ValueError(f"Label ontbreekt bij expliciete bevestiging: {ref}")
            key = (entity_id, ref)
            signature = (status, label, fingerprint, kind)
            if key in decisions:
                previous = decisions[key]
                if previous["signature"] != signature:
                    raise ValueError(f"Tegenstrijdige reviewbesluiten: {entity_id} / {ref}")
                previous["files"].append(path.name)
                previous["evidence"].append({"reason": decision["reason"], "sources": sources})
                stats["duplicates"] += 1
                continue
            decisions[key] = {
                "signature": signature, "decision": decision, "stale": stale,
                "files": [path.name], "scope": doc["scope"],
                "evidence": [{"reason": decision["reason"], "sources": sources}],
            }

    labels = {}
    for (entity_id, ref), entry in decisions.items():
        status, label, _, _ = entry["signature"]
        if entry["stale"] or status != "confirmed" or not label:
            continue
        key = (ref, label.casefold())
        labels.setdefault(key, set()).add(entity_id)
    for (ref, label), owners in labels.items():
        occurrences = len(re.findall(r"(?<!\w)" + re.escape(label) + r"(?!\w)", text_loader(ref), re.I))
        if len(owners) > occurrences:
            raise ValueError(f"Meerdere entiteiten voor één tekstvermelding: {ref}: {label}")

    features.update(additions)
    settled = set()
    for (entity_id, ref), entry in decisions.items():
        decision = entry["decision"]
        status, label, fingerprint, kind = entry["signature"]
        feature = features.get(entity_id)
        props = feature["properties"] if feature else None
        existing = next((r for r in props["refs"] if r["ref"] == ref), None) if props else None
        if entry["stale"]:
            stats["stale"] += 1
            if existing:
                existing["status"] = "needs-human-review"
                existing.pop("label", None)
                existing["review"] = {"stale": True, "files": entry["files"],
                                      "textSha256": fingerprint, "reason": "Versinhoud gewijzigd; opnieuw controleren."}
            continue
        stats[status] += 1
        if status != "needs-human-review":
            settled.add((entity_id, ref))
        if status == "rejected":
            if existing:
                props["refs"].remove(existing)
            continue
        book, chapter, verse = split_ref(ref)
        if not existing:
            existing = {"boek": book, "hoofdstuk": chapter, "vers": verse, "ref": ref,
                        "href": f"index.html#{book}/{chapter}/{verse}"}
            props["refs"].append(existing)
        existing["status"] = "agent-reviewed" if status == "confirmed" else "needs-human-review"
        existing["mentionType"] = kind
        existing["review"] = {
            "files": entry["files"], "textSha256": fingerprint, "decision": status,
            "reason": decision["reason"], "sources": decision.get("sources", []),
        }
        if len(entry["evidence"]) > 1:
            existing["review"]["evidence"] = entry["evidence"]
        existing.pop("label", None)
        if label:
            existing["label"] = label
            if status == "confirmed" and kind == "explicit" and label not in props["aliases"]:
                props["aliases"].append(label)
    return {"metadata": {"files": len(documents), "decisions": len(decisions), **dict(stats)},
            "settled": settled}
