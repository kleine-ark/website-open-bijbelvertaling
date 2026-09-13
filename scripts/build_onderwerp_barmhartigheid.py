#!/usr/bin/env python3
"""Bouw het onderwerp Barmhartigheid uit de vermeldingen in de Bijbeltekst.

Aanleiding: een lezer vroeg bij Ezechiel 34:4 — waar de herders het zwakke niet
sterken en het zieke niet helen — om een onderwerp barmhartigheid.

Het woord zelf staat daar niet. Daarom staan er naast de letterlijke treffers
enkele kernpassages die met de hand zijn toegevoegd; elk vers draagt zelf welke
van de twee het is, zodat de herkomst na te gaan blijft.

Goedertierenheid en genadig zijn bewust NIET meegenomen. Die woorden vertalen
andere begrippen (chesed en chanan), komen samen ruim driehonderd keer voor en
zouden het onderwerp overspoelen; ze verdienen een eigen ingang. Erbarmelijk
blijft ook buiten beeld: dat betekent jammerlijk, niet barmhartig.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
from typing import Any

try:
    from scripts.build_corpus_naslag import load_books, load_corpus
except ModuleNotFoundError:  # rechtstreeks uitgevoerd vanuit scripts/
    from build_corpus_naslag import load_books, load_corpus


ROOT = Path(__file__).resolve().parents[1]

# erbarmelijk valt af: dat is jammerlijk, niet barmhartig.
WOORD = re.compile(
    r"(?<![0-9A-Za-zÀ-ÖØ-öø-ÿ-])"
    r"(barmhartig\w*|ontferm\w*|erbarmen|erbarme|erbarmt|erbarmde|"
    r"medelijden|mededogen|meedogen\w*)"
    r"(?![0-9A-Za-zÀ-ÖØ-öø-ÿ-])",
    re.I,
)
UITGESLOTEN = re.compile(r"erbarmelijk", re.I)

# Kernpassages zonder het woord zelf. De eerste twee zijn de aanleiding.
MET_DE_HAND = [
    "ezechiel 34:4",
    "ezechiel 34:16",
    "jesaja 58:7",
    "mattheus 25:35",
    "mattheus 25:36",
    "mattheus 25:40",
    "jakobus 1:27",
]

TOP_TIEN = [
    "exodus 34:6",
    "ezechiel 34:4",
    "psalmen 103:13",
    "spreuken 14:31",
    "jesaja 49:15",
    "klaagliederen 3:22",
    "mattheus 5:7",
    "lukas 6:36",
    "lukas 10:33",
    "efeziers 2:4",
]


def _json_dump(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def build_barmhartigheid(root: Path = ROOT, *, write: bool = True) -> dict[str, Any]:
    books = load_books(root)
    corpus = load_corpus(root, include_ethiopic=True)

    letterlijk = []
    alle_refs = set()
    for vers in corpus:
        alle_refs.add(vers.ref)
        schoon = UITGESLOTEN.sub(" ", vers.text)
        if WOORD.search(schoon):
            letterlijk.append(vers.ref)

    ontbrekend = [ref for ref in MET_DE_HAND if ref not in alle_refs]
    if ontbrekend:
        raise ValueError(f"Onbekende verwijzing: {', '.join(ontbrekend)}")
    dubbel = [ref for ref in MET_DE_HAND if ref in set(letterlijk)]
    if dubbel:
        raise ValueError(
            "Deze staan al in de letterlijke treffers en horen niet met de hand "
            f"toegevoegd te worden: {', '.join(dubbel)}"
        )

    volgorde = {ref: i for i, ref in enumerate(v.ref for v in corpus)}
    refs = sorted(set(letterlijk) | set(MET_DE_HAND), key=lambda r: volgorde[r])

    mist_top = [ref for ref in TOP_TIEN if ref not in set(refs)]
    if mist_top:
        raise ValueError(f"Top 10 staat niet in de selectie: {', '.join(mist_top)}")

    tag = {
        "id": "barmhartigheid",
        "naam": "Barmhartigheid en ontferming",
        "beschrijving": "Teksten over barmhartigheid, ontferming en medelijden: "
                        "God die Zich ontfermt, en de mens die ontferming bewijst aan "
                        "wie zwak, ziek, arm of gebroken is.",
        "kleur": "#8a5a3b",
        "selectiemethode": "letterlijke-vermeldingen-plus-benoemde-kernpassages",
        "topTien": TOP_TIEN,
        "reviewStatus": "automatisch-geïdentificeerd",
        "humanReviewed": False,
        "verzen": [
            {
                "ref": ref,
                "rang": 1 if ref in TOP_TIEN else 2,
                "selectie": "met-de-hand" if ref in MET_DE_HAND else "letterlijk",
                "reviewStatus": "automatisch-geïdentificeerd",
                "humanReviewed": False,
            }
            for ref in refs
        ],
    }

    per_book = [
        {
            "boek": book["id"],
            "naam": book["nameDutch"],
            "gescand": True,
            "verzenGetagd": sum(ref.startswith(book["id"] + " ") for ref in refs),
        }
        for book in books
    ]
    report = {
        "onderwerp": "barmhartigheid",
        "selectiemethode": tag["selectiemethode"],
        "boekenGescand": len(books),
        "verzenGescand": len(corpus),
        "verzenGetagd": len(refs),
        "verzenMetDeHand": len(MET_DE_HAND),
        "boekenMetTreffers": sum(book["verzenGetagd"] > 0 for book in per_book),
        "topTien": TOP_TIEN,
        "reviewStatus": tag["reviewStatus"],
        "humanReviewed": False,
        "perBoek": per_book,
    }
    result = {"tag": tag, "report": report}

    if write:
        data = root / "data"
        _json_dump(data / "onderwerp-barmhartigheid-dekking.json", report)
        tags_path = data / "tags.json"
        tags_doc = json.loads(tags_path.read_text(encoding="utf-8"))
        tags = tags_doc.get("tags", [])
        tags_doc["tags"] = [item for item in tags if item.get("id") != "barmhartigheid"] + [tag]
        _json_dump(tags_path, tags_doc)

    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="scan zonder bestanden te wijzigen")
    args = parser.parse_args()
    built = build_barmhartigheid(write=not args.check)
    verslag = dict(built["report"])
    verslag["perBoek"] = [b for b in verslag["perBoek"] if b["verzenGetagd"]]
    print(json.dumps(verslag, ensure_ascii=False, indent=2)[:2000])
