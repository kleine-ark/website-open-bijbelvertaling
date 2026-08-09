"""Bouw de canonieke naslag en tagging voor Volken & Naties.

De gepubliceerde lijst bevat alleen passages uit de 66 canonieke boeken.
Treffers buiten die canon worden uitsluitend in de reviewqueue vastgelegd.
"""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"


AMMON_PASSAGES = [
    "genesis 19:30-38",
    "numeri 21:21-32",
    "deuteronomium 2:16-23",
    "deuteronomium 2:26-37",
    "deuteronomium 3:11-17",
    "deuteronomium 23:3-6",
    "jozua 12:1-2",
    "jozua 13:8-12",
    "jozua 13:24-28",
    "richteren 3:12-14",
    "richteren 10:6-18",
    "richteren 11:1-40",
    "richteren 12:1-7",
    "1samuel 11:1-15",
    "1samuel 12:12-15",
    "1samuel 14:47-48",
    "2samuel 8:9-14",
    "2samuel 10:1-19",
    "2samuel 11:1-27",
    "2samuel 12:1-15",
    "2samuel 12:26-31",
    "2samuel 17:24-29",
    "2samuel 23:37",
    "1koningen 11:1-8",
    "1koningen 11:29-39",
    "1koningen 14:21",
    "1koningen 14:31",
    "2koningen 23:10-14",
    "2koningen 24:1-4",
    "1kronieken 11:39",
    "1kronieken 18:9-13",
    "1kronieken 19:1-19",
    "1kronieken 20:1-3",
    "2kronieken 12:13",
    "2kronieken 20:1-30",
    "2kronieken 24:26",
    "2kronieken 26:6-8",
    "2kronieken 27:1-6",
    "ezra 9:1-4",
    "nehemia 2:10-20",
    "nehemia 4:1-9",
    "nehemia 13:1-3",
    "nehemia 13:23-31",
    "psalmen 83:2-9",
    "jesaja 11:10-16",
    "jeremia 9:23-26",
    "jeremia 25:15-29",
    "jeremia 27:1-11",
    "jeremia 40:7-16",
    "jeremia 41:1-18",
    "jeremia 49:1-6",
    "ezechiel 21:18-32",
    "ezechiel 25:1-7",
    "ezechiel 25:8-11",
    "daniel 11:40-45",
    "amos 1:13-15",
    "zefanja 2:8-11",
]


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=1) + "\n",
        encoding="utf-8",
    )


def expand(reference: str) -> list[str]:
    match = re.fullmatch(r"(\S+) (\d+):(\d+)(?:-(\d+))?", reference)
    if not match:
        raise ValueError(f"Ongeldige verwijzing: {reference}")
    book, chapter, first, last = match.groups()
    return [
        f"{book} {chapter}:{verse}"
        for verse in range(int(first), int(last or first) + 1)
    ]


def literal_hits(book: dict) -> list[dict]:
    result = []
    for chapter in book["chaptersIncluded"]:
        chapter_file = DATA / book["id"] / f"{chapter}.json"
        if not chapter_file.exists():
            continue
        for verse in read_json(chapter_file).get("verses", []):
            text = verse.get("text2026_html") or verse.get("text2026") or ""
            text = re.sub(r"<[^>]+>", " ", text)
            if re.search(r"(?i)\b(?:ben[- ]?ammi|ammon\w*|ammons)\b", text):
                result.append({
                    "ref": f'{book["id"]} {chapter}:{verse["number"]}',
                    "boek": book["nameDutch"],
                    "testament": book["testament"],
                    "tekst": text,
                })
    return result


def build() -> tuple[dict, dict]:
    books = read_json(DATA / "books.json")["books"]
    canonical_ids = {
        book["id"] for book in books if book["testament"] in {"OT", "NT"}
    }
    covered = {ref for passage in AMMON_PASSAGES for ref in expand(passage)}
    missing = [
        hit["ref"]
        for book in books
        if book["testament"] in {"OT", "NT"}
        for hit in literal_hits(book)
        if hit["ref"] not in covered
    ]
    if missing:
        raise RuntimeError("Onbedekte canonieke Ammon-treffers: " + ", ".join(missing))
    if any(passage.split()[0] not in canonical_ids for passage in AMMON_PASSAGES):
        raise RuntimeError("Niet-canoniek boek in de gepubliceerde Ammon-lijst")

    catalogue = {
        "titel": "Volken & Naties",
        "intro": "Volken en naties in Gods Woord, met hun oorsprong, naamvormen, woongebied en alle relevante canonieke teksten.",
        "bron": "Gods Woord",
        "canon": "66 boeken",
        "boeknamen": {book["id"]: book["nameDutch"] for book in books},
        "items": [{
            "id": "ammon",
            "naam": "Ammon",
            "soort": "volk",
            "onderscheiding": "Het volk Ammon; te onderscheiden van Ben-Ammi, de stamvader.",
            "beschrijving": "De Ammonieten stamden volgens Genesis af van Ben-Ammi, de jongste zoon van Lot. Hun historische kerngebied lag ten oosten van de Jordaan, rond hun hoofdstad Rabba. In Gods Woord komen zij voor als verwant buurvolk van Israël, als tegenstander en soms als deel van Israëls samenleving.",
            "naamvormen": [
                "Ammon",
                "kinderen van Ammon",
                "kinderen Ammons",
                "Ammonieten",
                "Ammoniet",
                "Ammonietische",
            ],
            "stamvader": {
                "naam": "Ben-Ammi",
                "betekenis": "zoon van mijn volk",
                "relatie": "zoon van Lot en stamvader van de Ammonieten",
                "ref": "genesis 19:38",
            },
            "kaart": {
                "plaats": "Rabba",
                "moderneNaam": "Amman, Jordanië",
                "coordinaten": [35.6094, 31.9539],
                "gebied": "historisch kerngebied ten oosten van de Jordaan",
                "zekerheid": "benadering",
                "toelichting": "De plaats van Rabba is zeker; de getoonde historische gebiedsgrenzen zijn bij benadering.",
                "bron": "data/geografie.geojson",
                "link": "kaart.html?plaats=Rabba",
            },
            "verzen": AMMON_PASSAGES,
        }],
    }

    noncanonical = [
        hit
        for book in books
        if book["testament"] not in {"OT", "NT"}
        for hit in literal_hits(book)
    ]
    review = {
        "onderwerp": "Volken & Naties — Ammon",
        "publicatiebeleid": "Niet-canonieke treffers worden niet gepubliceerd in de hoofdtekstlijst.",
        "canoniekeBoekenGescand": len(canonical_ids),
        "gepubliceerdePassages": len(AMMON_PASSAGES),
        "gepubliceerdeVerzen": len(covered),
        "nietCanoniekeTreffers": noncanonical,
        "reviewStatus": "agent-reviewed",
        "humanReviewed": False,
    }
    return catalogue, review


def update_tags(catalogue: dict) -> None:
    tags_path = DATA / "tags.json"
    data = read_json(tags_path)
    ammon = catalogue["items"][0]
    references = sorted(
        {ref for passage in ammon["verzen"] for ref in expand(passage)},
        key=lambda ref: (ammon["verzen"].index(next(p for p in ammon["verzen"] if ref in expand(p))), int(ref.rsplit(":", 1)[1])),
    )
    tag = {
        "id": "volk-ammon",
        "naam": "Ammon",
        "beschrijving": "Teksten over het volk Ammon, de Ammonieten en hun stamvader Ben-Ammi.",
        "kleur": "#9a7421",
        "categorie": "Volken & Naties",
        "verzen": [
            {
                "ref": ref,
                "rang": 1,
                "categorieen": ["volken-naties", "ammon"],
                "zekerheid": "zeker",
                "reviewStatus": "agent-reviewed",
                "humanReviewed": False,
            }
            for ref in references
        ],
    }
    data["tags"] = [entry for entry in data["tags"] if entry.get("id") != tag["id"]]
    data["tags"].append(tag)
    write_json(tags_path, data)


if __name__ == "__main__":
    catalogue, review = build()
    write_json(DATA / "naslag-volken-naties.json", catalogue)
    write_json(DATA / "volken-naties-review.json", review)
    update_tags(catalogue)
    print(
        f'Ammon: {review["gepubliceerdePassages"]} passages, '
        f'{review["gepubliceerdeVerzen"]} canonieke verzen; '
        f'{len(review["nietCanoniekeTreffers"])} niet-canonieke treffers in review.'
    )
