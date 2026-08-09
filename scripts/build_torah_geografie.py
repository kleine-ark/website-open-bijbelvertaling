#!/usr/bin/env python3
"""Bouw geografische versmetadata voor de vijf boeken van de Torah.

De catalogus hieronder is bewust expliciet en door een agent vers voor vers
beoordeeld. De tekstmatcher is alleen het reproduceerbare uitvoermechanisme;
twijfelachtige homoniemen worden uitsluitend via expliciete verslijsten
toegelaten of in de reviewqueue gezet.
"""

from __future__ import annotations

import json
import re
import unicodedata
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
BOOKS = ("genesis", "exodus", "leviticus", "numeri", "deuteronomium")


def slug(value: str) -> str:
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def entity(name: str, kind: str, *aliases: str, only: tuple[str, ...] = ()) -> dict:
    return {
        "id": f"geo-{slug(name)}",
        "naam": name,
        "type": kind,
        "aliases": list(dict.fromkeys((name, *aliases))),
        "alleenVerzen": set(only),
    }


# Types volgen de indeling van de geografische wiki. Eenzelfde zichtbare naam
# kan in de brontekst meer dan één betekenis hebben; zulke gevallen staan in
# AMBIGUOUS en worden niet blind gepubliceerd.
CATALOG = [
    entity("Egypte", "land-streek", "Egypteland"),
    entity("Kanaän", "land-streek"), entity("Gosen", "land-streek"),
    entity("Midian", "land-streek", only=("exodus 2:15", "exodus 2:16", "exodus 3:1", "exodus 4:19", "exodus 18:1", "numeri 22:4", "numeri 22:7", "numeri 25:15", "numeri 25:18", "numeri 31:2", "numeri 31:3", "numeri 31:7", "numeri 31:8", "numeri 31:9")),
    entity("Palestina", "land-streek"), entity("Edom", "land-streek"),
    entity("Moab", "land-streek"), entity("Basan", "land-streek", "Bazan"),
    entity("Gilead", "land-streek"), entity("Argob", "land-streek"),
    entity("Assur", "land-streek"), entity("Syrië", "land-streek", "SyriÃ«"),
    entity("Chittim", "land-streek", "Chitteers"),
    entity("Kafthor", "land-streek"), entity("Mesopotamië", "land-streek", "MesopotamiÃ«"),
    entity("Seïr", "land-streek", "SeÃ¯r"), entity("Zuiden", "land-streek"),

    entity("Jordaan", "rivier-water"), entity("Schelfzee", "rivier-water"),
    entity("Zoutzee", "rivier-water"), entity("Arnon", "rivier-water"),
    entity("Jabbok", "rivier-water"), entity("Zered", "rivier-water"),
    entity("Cinnereth", "rivier-water"), entity("Frath", "rivier-water"),

    entity("Horeb", "berg"), entity("Hor", "berg"), entity("Abarim", "berg"),
    entity("Pisga", "berg"), entity("Peor", "berg"), entity("Nebo", "plaats"),
    entity("Hermon", "berg", "Sirjon", "Senir", "Sion"),
    entity("Ebal", "berg"), entity("Gerizim", "berg"), entity("Libanon", "berg"),

    entity("woestijn Sin", "woestijn", "Sin"),
    entity("Sinaï", "plaats", "SinaÃ¯"),
    entity("woestijn Paran", "woestijn", "Paran"),
    entity("woestijn Zin", "woestijn", "Zin"),
    entity("woestijn Sur", "woestijn", "Sur"),
    entity("woestijn Kedemot", "woestijn", "Kedemot"),

    entity("Rameses", "stad-dorp", "Raamses"), entity("Pitom", "stad-dorp", "Pithom"),
    entity("Migdol", "stad-dorp"), entity("Hesbon", "stad-dorp", "Hezbon"),
    entity("Sodom", "stad-dorp"), entity("Gomorra", "stad-dorp"),
    entity("Adama", "stad-dorp"), entity("Zeboïm", "stad-dorp", "Zeboim"),
    entity("Zoar", "stad-dorp"),
    entity("Jahza", "stad-dorp", "Jahaz"), entity("Edreï", "stad-dorp", "Edre", "EdreÃ¯"),
    entity("Jericho", "stad-dorp"), entity("Pethor", "stad-dorp"),
    entity("Kirjath-huzzoth", "stad-dorp"), entity("Beth-jesimoth", "stad-dorp"),
    entity("Ataroth", "stad-dorp"), entity("Dibon", "stad-dorp"),
    entity("Jaëzer", "stad-dorp", "JaÃ«zer"), entity("Nimra", "stad-dorp"),
    entity("Eleale", "stad-dorp"), entity("Schebam", "stad-dorp", "Sibma"),
    entity("Behon", "stad-dorp", "Beon"), entity("Aroër", "stad-dorp", "AroÃ«r"),
    entity("Atroth-Sofan", "stad-dorp"), entity("Jogbeha", "stad-dorp"),
    entity("Beth-Nimra", "stad-dorp"), entity("Beth-Haran", "stad-dorp"),
    entity("Baäl-Meon", "stad-dorp", "BaÃ«l-Meon"), entity("Nobah", "stad-dorp"),
    entity("Kenath", "stad-dorp"), entity("Dibon-gad", "stad-dorp"),
    entity("Almon-diblathaim", "stad-dorp"), entity("Hazar-enan", "stad-dorp"),
    entity("Hazar-addar", "stad-dorp"), entity("Ribla", "stad-dorp"),
    entity("Ain", "stad-dorp", only=("numeri 34:11",)), entity("Sefam", "stad-dorp"),
    entity("Zedad", "stad-dorp"), entity("Zifron", "stad-dorp"),
    entity("Astharoth", "stad-dorp", "Asteroth"), entity("Salcha", "stad-dorp"),
    entity("Rabba", "stad-dorp"), entity("Beth-Peor", "stad-dorp", "Beth-peor"),
    entity("Bezer", "stad-dorp"), entity("Ramoth", "stad-dorp"),
    entity("Golan", "stad-dorp"), entity("Gilgal", "stad-dorp"),
    entity("Gaza", "stad-dorp"), entity("Hazerim", "stad-dorp"),
    entity("Rechob", "stad-dorp"), entity("Hamath", "stad-dorp"),
    entity("Zoan", "stad-dorp"), entity("Hebron", "stad-dorp"),
    entity("Eskol", "plaats"),
    entity("Horma", "stad-dorp"), entity("Harad", "stad-dorp"),
    entity("Ar", "stad-dorp", only=("numeri 21:15", "numeri 21:28", "numeri 21:29", "deuteronomium 2:9", "deuteronomium 2:18", "deuteronomium 2:29")),
    entity("Nofat", "stad-dorp"), entity("Medeba", "stad-dorp"),
    entity("Thirza", "stad-dorp", "Tirza"),
    entity("Kirjathaim", "stad-dorp"), entity("Elath", "stad-dorp"),
    entity("Dan", "stad-dorp", only=("genesis 14:14", "deuteronomium 34:1")),
    entity("Laban", "route-legerplaats", only=("deuteronomium 1:1",)),
    entity("More", "plaats", only=("genesis 12:6", "deuteronomium 11:30")),

    entity("Sukkoth", "route-legerplaats"), entity("Etham", "route-legerplaats"),
    entity("Pi-hachiroth", "route-legerplaats"), entity("Baäl-Zefon", "route-legerplaats", "BaÃ«l-Zefon"),
    entity("Mara", "route-legerplaats"), entity("Elim", "route-legerplaats"),
    entity("Rafidim", "route-legerplaats"), entity("Massa", "route-legerplaats"),
    entity("Meriba", "route-legerplaats"), entity("Kibroth Thaava", "route-legerplaats", "Kibroth-thaava"),
    entity("Hazeroth", "route-legerplaats"), entity("Kades", "route-legerplaats", "Kades-barnea"),
    entity("Oboth", "route-legerplaats"), entity("Waheb", "route-legerplaats"),
    entity("Beer", "route-legerplaats", only=("numeri 21:16",)),
    entity("Mattana", "route-legerplaats"), entity("Nahaliel", "route-legerplaats"),
    entity("Bamoth", "route-legerplaats", "hoogten van Baäl", "hoogten van BaÃ«l"),
    entity("Sittim", "route-legerplaats", "Abel-sittim", only=("numeri 25:1", "numeri 33:49")),
    entity("Dofka", "route-legerplaats"), entity("Aluz", "route-legerplaats"),
    entity("Rithma", "route-legerplaats"), entity("Rimmon-perez", "route-legerplaats"),
    entity("Libna", "route-legerplaats"), entity("Rissa", "route-legerplaats"),
    entity("Kehelatha", "route-legerplaats"), entity("Safer", "route-legerplaats"),
    entity("Harada", "route-legerplaats"), entity("Makheloth", "route-legerplaats"),
    entity("Tachath", "route-legerplaats"), entity("Tharah", "route-legerplaats"),
    entity("Mithka", "route-legerplaats"), entity("Hasmona", "route-legerplaats"),
    entity("Moseroth", "route-legerplaats", "Mosera"), entity("Bene-jaakan", "route-legerplaats", "Bene-Jaäkan", "Bene-JaÃ¤kan"),
    entity("Hor-gidgad", "route-legerplaats"), entity("Jotbatha", "route-legerplaats", "Jotbath"),
    entity("Abrona", "route-legerplaats"), entity("Ezeon-geber", "route-legerplaats"),
    entity("Zalmona", "route-legerplaats"), entity("Funon", "route-legerplaats"),
    entity("Akrabbim", "route-legerplaats"), entity("Azmon", "route-legerplaats"),
    entity("Havvoth-Jaïr", "land-streek", "Havvoth-JaÃ¯r"),
    entity("veld Zofim", "plaats", "Zofim"), entity("Asdoth-Pisga", "plaats", "Asdoth-pisga"),
    entity("Suf", "route-legerplaats", only=("deuteronomium 1:1",)),
    entity("Tofel", "route-legerplaats"), entity("Dizahab", "route-legerplaats"),
    entity("Beëroth Bene-Jaäkan", "route-legerplaats", "BeÃ«roth Bene-JaÃ¤kan"),
    entity("Thab-era", "route-legerplaats", "Thabera"), entity("Gudgod", "route-legerplaats"),
    entity("gebied van Nafthali", "land-streek", "hele Nafthali", only=("deuteronomium 34:2",)),
    entity("gebied van Efraïm", "land-streek", "land van Efraïm", "land van EfraÃ¯m", only=("deuteronomium 34:2",)),
    entity("gebied van Manasse", "land-streek", "land van Manasse", only=("deuteronomium 34:2",)),
    entity("gebied van Juda", "land-streek", "land van Juda", only=("deuteronomium 34:2",)),
]

AMBIGUOUS = {
    "genesis 10:2": "Volkennamen en geografische namen lopen in de volkenlijst samen; afzonderlijke identiteit controleren.",
    "genesis 10:7": "Havila, Seba en Dedan kunnen hier zowel personen als latere gebieden aanduiden.",
    "genesis 36:20": "Seïr is in dit vers een persoon, niet het gelijknamige gebied.",
    "numeri 21:1": "Atharim kan een plaatsnaam of een routeaanduiding zijn.",
    "numeri 32:3": "Behon is een onzekere spelling/identificatie van Baäl-Meon.",
    "deuteronomium 3:9": "Sion is hier een naamvariant van de Hermon, niet Jeruzalem/Sion elders.",
    "deuteronomium 34:1": "Dan is hier een plaats; elders in de Torah meestal persoon of stam.",
}

EXCLUDED = {
    ("exodus 6:18", "geo-hebron"),  # Hebron is hier een persoon.
}

GENESIS_LEGACY_TYPES = {
    "stad-dorp": set("""Abel-mizraim Accad Adama Adullam Ai Asteroth-karnaim Avith Babel Bela Bered Ber-seba Beth-el Bethlehem Bozra Calne Chezib Damascus Dan Dinhaba Dothan Efrath En-mispat Erech Gaza Gerar Gomorra Haran Hazezon-thamar Hebron Hoba Kalach Kiriath-arba Kirjath-arba Lasa Luz Mahanaim Masreka Migdal-eder Mizpa Nineve On Pahu Pniël Rehoboth Resen Salem Schave-kiriathaim Sichem Sidon Sodom Sukkoth Timna Zeboim Zoar Zoboim""".split()) | {"Ur van de Chaldeeën"},
    "land-streek": set("""Amalekieten Amoriet Amorieten Emieten Fereziet Ferezieten Filistijnen Girgaziet Hethiet Horieten Jebusiet Kadmoniet Kanaäniet Kanaänieten Keniet Keniziet Midian Refaieten Zuzieten Assur Cusch Edom Egypte Egypteland Elam Kanaän Moab Eden Ellasar Gilead Gosen Ham Havila Kades Machpela Mamre Mescha Mesopotamië Moria Nod Paddan Paddan-aram Paran Rameses Schave Seïr Siddim Sinear Sur zuiderland""".split()),
    "berg": {"Ararat", "Sefar"},
    "rivier-water": {"Esek", "Lachai-roi", "Seba", "Sitna", "Zoutzee", "Frath", "Gihon", "Hiddekel", "Jabbok", "Jordaan", "Pison"},
}


def read_verses(book: str):
    for path in sorted((DATA / book).glob("*.json"), key=lambda p: int(p.stem)):
        chapter = json.loads(path.read_text(encoding="utf-8"))
        for verse in chapter["verses"]:
            yield chapter["number"], verse


def word_match(text: str, alias: str) -> bool:
    return bool(re.search(r"(?<![\w-])" + re.escape(alias) + r"(?![\w-])", text, re.IGNORECASE))


def contextual_type(item: dict, text: str) -> str:
    """Verfijn namen die zowel een berg als een ruimere plaats kunnen zijn."""
    if item["naam"] == "Sinaï":
        if re.search(r"\b(?:berg|gebergte)\s+(?:van\s+)?Sina", text, re.IGNORECASE):
            return "berg"
        if re.search(r"\bwoestijn\s+Sina", text, re.IGNORECASE):
            return "woestijn"
    if item["naam"] == "Nebo":
        return "berg" if re.search(r"\bberg\s+Nebo\b", text, re.IGNORECASE) else "stad-dorp"
    if item["naam"] == "Abarim" and re.search(r"\bheuvelen\s+van\s+Abarim\b", text, re.IGNORECASE):
        return "route-legerplaats"
    return item["type"]


def normalize_legacy_type(value: str) -> str:
    if value in {"plaats", "land-streek", "berg", "rivier-water", "woestijn", "stad-dorp", "route-legerplaats"}:
        return value
    return {
        "stad": "stad-dorp", "land": "land-streek", "streek": "land-streek",
        "rivier": "rivier-water", "zee": "rivier-water", "berg": "berg",
        "woestijn": "woestijn", "volk-gebied": "land-streek",
    }.get(value, "plaats")


def genesis_legacy_type(label: str, value: str) -> str:
    for kind, labels in GENESIS_LEGACY_TYPES.items():
        if label in labels:
            return kind
    return normalize_legacy_type(value)


def build_book(book: str, legacy: dict | None = None) -> dict:
    names: dict[str, dict] = {}
    verses: dict[str, list[str]] = {}
    mentions: dict[str, list[dict]] = {}
    verse_count = 0

    for chapter, verse in read_verses(book):
        verse_count += 1
        ref = f"{book} {chapter}:{verse['number']}"
        key = f"{chapter}:{verse['number']}"
        text = verse.get("text2026", "")
        seen = set()
        for item in CATALOG:
            if (ref, item["id"]) in EXCLUDED:
                continue
            if item["alleenVerzen"] and ref not in item["alleenVerzen"]:
                continue
            found = [alias for alias in item["aliases"] if word_match(text, alias)]
            if not found:
                continue
            label = max(found, key=len)
            kind = contextual_type(item, text)
            signature = (item["id"], label.casefold())
            if signature in seen:
                continue
            seen.add(signature)
            names[label] = {
                "id": item["id"], "naam": item["naam"], "type": kind,
                "status": "agent-reviewed",
            }
            verses.setdefault(key, []).append(label)
            mentions.setdefault(key, []).append({
                "id": item["id"], "label": label, "type": kind,
                "ref": ref, "href": f"index.html#{book}/{chapter}/{verse['number']}",
                "status": "agent-reviewed",
            })

    # Genesis had al een handmatig samengestelde conceptinventaris. Neem die
    # zonder verlies over, maar geef ieder item nu een stabiele id en expliciete
    # agentstatus. De oorspronkelijke Bijbelbestanden worden niet gewijzigd.
    if legacy:
        for key, labels in legacy.get("verzen", {}).items():
            chapter, verse_number = key.split(":", 1)
            ref = f"{book} {chapter}:{verse_number}"
            for label in labels:
                if any(m["label"] == label for m in mentions.get(key, [])):
                    continue
                old_meta = legacy.get("namen", {}).get(label, {})
                kind = genesis_legacy_type(label, old_meta.get("type", "plaats"))
                entity_id = old_meta.get("id") or f"geo-{slug(label)}"
                names[label] = {
                    "id": entity_id, "naam": old_meta.get("naam", label),
                    "type": kind, "status": "agent-reviewed",
                }
                verses.setdefault(key, []).append(label)
                mentions.setdefault(key, []).append({
                    "id": entity_id, "label": label, "type": kind, "ref": ref,
                    "href": f"index.html#{book}/{chapter}/{verse_number}",
                    "status": "agent-reviewed",
                })

    queue = [
        {"ref": ref, "reden": reason, "status": "needs-human-review"}
        for ref, reason in AMBIGUOUS.items() if ref.startswith(book + " ")
    ]
    return {
        "boek": book,
        "status": "agent-reviewed",
        "reviewStatus": "ai-geidentificeerd-agent-reviewed",
        "humanReviewed": False,
        "provenance": {
            "methode": "vers-voor-vers agentbeoordeling met expliciete plaatscatalogus",
            "scope": "uitsluitend Bijbeltekst; kanttekeningen niet meegetagd",
        },
        "dekking": {"verzenBeoordeeld": verse_count, "verzenMetTags": len(verses)},
        "namen": dict(sorted(names.items(), key=lambda pair: pair[0].casefold())),
        "verzen": verses,
        "mentions": mentions,
        "reviewQueue": queue,
    }


def main() -> None:
    genesis_path = DATA / "genesis-geo.json"
    legacy_genesis = json.loads(genesis_path.read_text(encoding="utf-8"))
    all_books = {}
    totals = Counter()
    for book in BOOKS:
        result = build_book(book, legacy_genesis if book == "genesis" else None)
        out = DATA / f"{book}-geo.json"
        out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        all_books[book] = {
            "bestand": out.name,
            "status": result["status"],
            "dekking": result["dekking"],
            "reviewQueue": len(result["reviewQueue"]),
        }
        for verse_mentions in result["mentions"].values():
            totals.update(m["type"] for m in verse_mentions)

    manifest = {
        "id": "geografie-torah",
        "status": "agent-reviewed",
        "humanReviewed": False,
        "boeken": all_books,
        "categorieen": dict(sorted(totals.items())),
    }
    (DATA / "geografie-torah.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
