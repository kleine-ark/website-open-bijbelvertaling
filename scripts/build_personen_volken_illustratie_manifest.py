#!/usr/bin/env python3
"""Bouw het hervatbare productiemanifest voor personen en volkenillustraties."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "images" / "wiki" / "personen-volken-manifest.json"

POSES = (
    "standing calmly with both hands relaxed",
    "standing in a restrained three-quarter pose",
    "seated quietly on a low ancient stone",
    "walking slowly with one foot slightly forward",
    "standing with one open hand in a modest conversational gesture",
    "standing calmly with hands loosely folded",
)
MANTLES = ("muted olive", "warm sand", "faded ochre", "restrained navy-gray", "soft umber", "pale flax")
BACKDROPS = (
    "a faint dry Judean ridge",
    "a sparse ancient Near Eastern courtyard wall",
    "a low desert path and distant ridge",
    "a suggestion of an ancient tent edge",
    "two weathered limestone blocks",
    "a sparse cultivated field edge",
)


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def stable_variant(item_id: str, values: tuple[str, ...], offset: int = 0) -> str:
    digest = hashlib.sha256(item_id.encode("utf-8")).digest()
    return values[(digest[offset % len(digest)] + offset) % len(values)]


def person_prompt(item: dict) -> str:
    item_id = item["id"]
    gender = "woman" if item.get("geslacht") == "v" else "man"
    age = "adult"
    description = item.get("beschrijving", "").strip()
    if any(word in description.lower() for word in ("kind", "zoon van", "dochter van")):
        age = "young adult"
    if any(word in description.lower() for word in ("oud", "aartsvader", "stamvader")):
        age = "elderly"
    pose = stable_variant(item_id, POSES)
    mantle = stable_variant(item_id, MANTLES, 1)
    backdrop = stable_variant(item_id, BACKDROPS, 2)
    reference = item.get("verzen", [""])[0]
    return (
        "Use case: historical-scene\n"
        "Asset type: square wiki catalogue tile illustration\n"
        f"Primary request: a respectful, historically plausible individual portrait representing the biblical person {item['naam']}; "
        f"catalogue context: {description or 'a person named in the biblical genealogies'}; first reference: {reference}\n"
        f"Scene/backdrop: minimal pale ancient Near Eastern ground with {backdrop}, dissolving into a plain warm aged parchment field\n"
        f"Subject: exactly one {age} ancient Semitic {gender}, {pose}, in simple period-appropriate handwoven robes with a {mantle} mantle; "
        "natural face and anatomy; do not attempt a modern celebrity likeness\n"
        "Style/medium: highly refined historical pencil drawing with fine navy-gray graphite contours and very subtle transparent watercolor washes, "
        "matching a restrained nineteenth-century museum plate and the existing Open Vertaling biblical instrument illustrations\n"
        "Composition/framing: square, one centered full or three-quarter figure only, clear silhouette, generous clean margins\n"
        "Lighting/mood: gentle warm side light, dignified, quiet and reverent\n"
        "Color palette: parchment cream, sand, muted antique gold, faded olive, warm brown and deep navy-gray; low saturation\n"
        "Materials/textures: handwoven wool and linen, simple ancient leather sandals, delicate parchment grain\n"
        "Constraints: no text, no letters, no numbers, no artist signature, no mark in any corner, no frame, no border, no watermark, "
        "no halo, no glowing aura, no modern objects, no other people, no dramatic action, no photorealism, no fantasy costume, "
        "no European medieval clothing, no crown or weapon unless the catalogue context explicitly requires it"
    )


def ammon_prompt(item: dict) -> str:
    return (
        "Use case: historical-scene\n"
        "Asset type: square wiki catalogue tile illustration\n"
        "Primary request: a historically plausible visual emblem of the ancient Ammonite people, descendants of Ben-Ammi, centered on their Iron Age homeland around Rabba east of the Jordan\n"
        "Scene/backdrop: sparse highland terrain around ancient Rabba with a restrained stone settlement silhouette dissolving into warm aged parchment\n"
        "Subject: one dignified ancient Ammonite family group of three seen from a respectful distance, in historically plausible Iron Age Levantine wool and linen garments; one simple water jar and a low boundary stone as quiet cultural details\n"
        "Style/medium: highly refined historical pencil drawing with fine navy-gray graphite contours and very subtle transparent watercolor washes, matching the restrained hand-drawn museum-plate quality of the existing Open Vertaling biblical instrument illustrations\n"
        "Composition/framing: square, compact group centered, landscape kept minimal, generous clear margins\n"
        "Lighting/mood: calm warm morning light, documentary and reverent rather than heroic\n"
        "Color palette: parchment cream, sand, muted antique gold, faded olive, earth brown and deep navy-gray; low saturation\n"
        "Materials/textures: handwoven wool and linen, weathered limestone, dry highland earth\n"
        "Constraints: no text, no letters, no numbers, no map labels, no modern Amman skyline, no modern objects, no frame, no border, no watermark, no crown, no idol, no battle, no weapons, no dramatic action, no fantasy costume, no photorealism"
    )


def existing_status(previous: dict[str, dict], item_id: str, target: Path) -> tuple[str, str | None]:
    old = previous.get(item_id, {})
    status = old.get("status", "pending")
    error = old.get("foutreden")
    if target.exists() and status in {"generated", "validated", "integrated"}:
        return status, error
    return "pending", error


def main() -> None:
    previous_items: dict[str, dict] = {}
    if MANIFEST.exists():
        previous = read_json(MANIFEST)
        previous_items = {entry["item_id"]: entry for entry in previous.get("items", [])}

    entries = []
    persons = read_json(ROOT / "data" / "naslag-personen.json")["items"]
    for person in persons:
        target = ROOT / "images" / "wiki" / "personen" / f"{person['id']}.webp"
        status, error = existing_status(previous_items, f"personen:{person['id']}", target)
        if person["id"] == "mozes" and (ROOT / "images" / "wiki" / "proefserie" / "mozes.webp").exists():
            status = "pending" if not target.exists() else status
        entries.append({
            "categorie": "personen",
            "item_id": f"personen:{person['id']}",
            "bron_id": person["id"],
            "naam": person["naam"],
            "doelpad": target.relative_to(ROOT).as_posix(),
            "status": status,
            "prompt": person_prompt(person),
            "foutreden": error,
        })

    nations = read_json(ROOT / "data" / "naslag-volken-naties.json")["items"]
    for nation in nations:
        target = ROOT / "images" / "wiki" / "volken-naties" / f"{nation['id']}.webp"
        status, error = existing_status(previous_items, f"volken-naties:{nation['id']}", target)
        entries.append({
            "categorie": "volken-naties",
            "item_id": f"volken-naties:{nation['id']}",
            "bron_id": nation["id"],
            "naam": nation["naam"],
            "doelpad": target.relative_to(ROOT).as_posix(),
            "status": status,
            "prompt": ammon_prompt(nation),
            "foutreden": error,
        })

    payload = {
        "versie": 1,
        "stijl": "historische potloodtekening met subtiele aquarel op warm perkament",
        "statussen": ["pending", "generated", "validated", "integrated"],
        "totaal": len(entries),
        "items": entries,
    }
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Manifest: {MANIFEST} ({len(entries)} items)")


if __name__ == "__main__":
    main()
