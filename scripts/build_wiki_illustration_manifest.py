#!/usr/bin/env python3
"""Build resumable manifests for generated wiki catalogue illustrations."""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CATEGORIES = {
    "materialen": {
        "data": "data/naslag-materialen.json",
        "folder": "images/wiki/materialen",
        "kind": "historically plausible biblical material or object",
        "medium": "archaeological still-life",
    },
    "bomen-planten": {
        "data": "data/naslag-bomen-planten.json",
        "folder": "images/wiki/bomen-planten",
        "kind": "botanically plausible biblical plant",
        "medium": "botanical-historical specimen plate",
    },
    "dieren": {
        "data": "data/naslag-dieren.json",
        "folder": "images/wiki/dieren",
        "kind": "anatomically plausible biblical animal",
        "medium": "natural-history specimen plate",
    },
    "liederen": {
        "data": "data/naslag-liederen.json",
        "folder": "images/wiki/liederen",
        "kind": "quiet historically plausible biblical song scene",
        "medium": "historical narrative plate",
    },
    "gebeden": {
        "data": "data/naslag-gebeden.json",
        "folder": "images/wiki/gebeden",
        "kind": "quiet historically plausible biblical prayer scene",
        "medium": "historical narrative plate",
    },
    "personen": {
        "data": "data/naslag-personen.json",
        "folder": "images/wiki/personen",
        "kind": "respectful historically plausible biblical person",
        "medium": "historical portrait plate",
    },
    "volken-naties": {
        "data": "data/naslag-volken-naties.json",
        "folder": "images/wiki/volken-naties",
        "kind": "respectful historically plausible ancient people or nation",
        "medium": "historical ethnographic plate",
    },
}
PILOTS = {
    ("materialen", "goud"): "images/wiki/proefserie/goud.webp",
    ("bomen-planten", "olijfboom"): "images/wiki/proefserie/olijfboom.webp",
    ("dieren", "duif-en-tortelduif"): "images/wiki/proefserie/duif-en-tortelduif.webp",
    ("liederen", "lied-bij-de-schelfzee"): "images/wiki/proefserie/lied-bij-de-schelfzee.webp",
    ("gebeden", "jezus-in-gethsemane"): "images/wiki/proefserie/jezus-in-gethsemane.webp",
    ("personen", "mozes"): "images/wiki/proefserie/mozes.webp",
}


def excerpt(item: dict) -> str:
    text = item.get("beschrijving") or item.get("toelichting") or ""
    text = re.sub(r"\s+", " ", text).strip()
    return text[:420]


def prompt(category: str, item: dict) -> str:
    cfg = CATEGORIES[category]
    name = item.get("naam") or item.get("titel") or item["id"]
    context = excerpt(item)
    return (
        "Use case: historical-scene\n"
        "Asset type: square wiki catalogue tile illustration\n"
        f"Primary request: portray {name} as a {cfg['kind']}, clearly recognizable at thumbnail size\n"
        f"Biblical context for subject selection: {context}\n"
        "Scene/backdrop: sparse historically fitting ground or setting dissolving naturally into plain warm aged parchment with delicate fibers and subtle patina\n"
        f"Style/medium: highly refined {cfg['medium']} in fine navy-gray pencil contours with restrained transparent watercolor washes, exactly matching the supplied approved Open Vertaling reference illustration\n"
        "Composition/framing: square, one clear central subject or one restrained coherent group, full silhouette visible, generous clean margins, no panorama or busy background\n"
        "Lighting/mood: gentle warm side light, quiet, dignified and reverent\n"
        "Color palette: parchment cream, sand, muted antique gold, faded olive, warm brown and deep navy-gray; low saturation\n"
        "Constraints: subject and period details must be plausible; no text, letters, numbers, captions, labels, artist signature, corner mark, frame, border, watermark, modern objects, halo, dramatic rays, fantasy ornament, crowded action, cartoon style or photorealism"
    )


def load_items(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return data["items"] if isinstance(data, dict) else data


def main() -> None:
    manifest_dir = ROOT / "images/wiki/manifests"
    manifest_dir.mkdir(parents=True, exist_ok=True)
    for category, cfg in CATEGORIES.items():
        items = load_items(ROOT / cfg["data"])
        old_path = manifest_dir / f"{category}.json"
        old = {}
        if old_path.exists():
            old = {row["id"]: row for row in json.loads(old_path.read_text(encoding="utf-8"))["items"]}
        rows = []
        for item in items:
            item_id = item["id"]
            target = f"{cfg['folder']}/{item_id}.webp"
            pilot = PILOTS.get((category, item_id))
            row = {
                "id": item_id,
                "naam": item.get("naam") or item.get("titel") or item_id,
                "doelpad": target,
                "status": "pending",
                "prompt": prompt(category, item),
                "foutreden": None,
                "bronPilot": pilot,
            }
            if item_id in old:
                row.update({key: old[item_id].get(key, row[key]) for key in ("status", "foutreden")})
            if pilot and (ROOT / pilot).exists() and row["status"] == "pending":
                row["status"] = "generated"
            rows.append(row)
        payload = {
            "categorie": category,
            "bronbestand": cfg["data"],
            "doelmap": cfg["folder"],
            "formaat": {"type": "WebP", "breedte": 640, "hoogte": 640},
            "statussen": ["pending", "generated", "validated", "integrated"],
            "items": rows,
        }
        old_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
