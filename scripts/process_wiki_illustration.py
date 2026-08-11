#!/usr/bin/env python3
"""Verwerk één gegenereerde wiki-illustratie en werk het manifest atomisch bij."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "images" / "wiki" / "personen-volken-manifest.json"


def write_json_atomic(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
        temp = Path(handle.name)
    os.replace(temp, path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("item_id")
    parser.add_argument("source", type=Path)
    parser.add_argument("--status", choices=("generated", "validated", "integrated"), default="generated")
    parser.add_argument("--error")
    args = parser.parse_args()

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    entry = next((item for item in manifest["items"] if item["item_id"] == args.item_id), None)
    if entry is None:
        raise SystemExit(f"Onbekend manifest-item: {args.item_id}")

    if args.error:
        entry["status"] = "pending"
        entry["foutreden"] = args.error
        write_json_atomic(MANIFEST, manifest)
        return

    destination = ROOT / entry["doelpad"]
    destination.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(args.source) as image:
        image = image.convert("RGB")
        if image.size != (640, 640):
            image = image.resize((640, 640), Image.Resampling.LANCZOS)
        image.save(destination, "WEBP", quality=84, method=6)

    entry["status"] = args.status
    entry["foutreden"] = None
    write_json_atomic(MANIFEST, manifest)
    print(f"{args.item_id}: {args.status} -> {destination.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
