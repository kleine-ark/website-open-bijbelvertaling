#!/usr/bin/env python3
"""Export a public, identity-free release snapshot from the authoritative API."""
import argparse
import json
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]


def export_status(root=ROOT, api="http://127.0.0.1:8787"):
    catalog = json.loads((root / "data/review-catalog.json").read_text(encoding="utf-8"))
    url = api.rstrip("/") + "/api/collaboration/verified-chapters?" + urlencode({
        "catalogRevision": catalog["catalogRevision"],
    })
    request = Request(url, headers={"Cache-Control": "no-store"})
    with urlopen(request, timeout=60) as response:
        snapshot = json.load(response)
    known = {item["id"] for item in catalog["subjects"] if item["type"] == "text-chapter"}
    if not isinstance(snapshot, dict) or any(
        not isinstance(chapters, list) or len(set(chapters)) != len(chapters)
        or any(type(chapter) is not int or f"{book}/{chapter}" not in known for chapter in chapters)
        for book, chapters in snapshot.items()
    ):
        raise ValueError("ongeldige verificatiestatus van de API")
    output = root / "data/verified-chapters.json"
    temporary = output.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(output)
    return snapshot


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api", default="http://127.0.0.1:8787")
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    snapshot = export_status(args.root, args.api)
    print(f"Verificatiesnapshot: {sum(map(len, snapshot.values()))} hoofdstukken")


if __name__ == "__main__":
    main()
