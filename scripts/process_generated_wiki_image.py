#!/usr/bin/env python3
"""Optimaliseer een gegenereerde wiki-illustratie naar de vaste 640px-WebP."""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("target", type=Path)
    args = parser.parse_args()

    args.target.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(args.source) as source:
        image = source.convert("RGB").resize((640, 640), Image.Resampling.LANCZOS)
        image.save(args.target, "WEBP", quality=86, method=6)

    with Image.open(args.target) as result:
        if result.format != "WEBP" or result.size != (640, 640):
            raise RuntimeError(f"Ongeldige uitvoer: {args.target} {result.format} {result.size}")

    print(args.target.as_posix())


if __name__ == "__main__":
    main()
