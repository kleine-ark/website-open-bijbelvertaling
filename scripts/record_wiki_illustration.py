#!/usr/bin/env python3
"""Optimize one generated image and record resumable wiki illustration progress."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image, ImageOps


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("category")
    parser.add_argument("item_id")
    parser.add_argument("source", type=Path)
    parser.add_argument("--status", choices=("generated", "validated", "integrated"), default="validated")
    args = parser.parse_args()

    manifest_path = ROOT / "images/wiki/manifests" / f"{args.category}.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    row = next((entry for entry in manifest["items"] if entry["id"] == args.item_id), None)
    if row is None:
        raise SystemExit(f"Onbekend item: {args.category}/{args.item_id}")

    destination = ROOT / row["doelpad"]
    destination.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(args.source) as image:
        image = ImageOps.fit(image.convert("RGB"), (640, 640), method=Image.Resampling.LANCZOS)
        image.save(destination, "WEBP", quality=84, method=6)

    row["status"] = args.status
    row["foutreden"] = None
    row["bronGeneratie"] = str(args.source)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(destination)


if __name__ == "__main__":
    main()
