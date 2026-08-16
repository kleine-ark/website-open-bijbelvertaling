"""Bouw de canonieke naslag en tagging voor Volken & Naties."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

# De eerste pagina, Ammon, bevat bewust bredere tekstpassages voor context.
# De drie volgende pagina's gebruiken alle letterlijke canonieke treffers.
AMMON_PASSAGES = [
    "genesis 19:30-38", "numeri 21:21-32", "deuteronomium 2:16-23", "deuteronomium 2:26-37", "deuteronomium 3:11-17", "deuteronomium 23:3-6", "jozua 12:1-2", "jozua 13:8-12", "jozua 13:24-28", "richteren 3:12-14", "richteren 10:6-18", "richteren 11:1-40", "richteren 12:1-7", "1samuel 11:1-15", "1samuel 12:12-15", "1samuel 14:47-48", "2samuel 8:9-14", "2samuel 10:1-19", "2samuel 11:1-27", "2samuel 12:1-15", "2samuel 12:26-31", "2samuel 17:24-29", "2samuel 23:37", "1koningen 11:1-8", "1koningen 11:29-39", "1koningen 14:21", "1koningen 14:31", "2koningen 23:10-14", "2koningen 24:1-4", "1kronieken 11:39", "1kronieken 18:9-13", "1kronieken 19:1-19", "1kronieken 20:1-3", "2kronieken 12:13", "2kronieken 20:1-30", "2kronieken 24:26", "2kronieken 26:6-8", "2kronieken 27:1-6", "ezra 9:1-4", "nehemia 2:10-20", "nehemia 4:1-9", "nehemia 13:1-3", "nehemia 13:23-31", "psalmen 83:2-9", "jesaja 11:10-16", "jeremia 9:23-26", "jeremia 25:15-29", "jeremia 27:1-11", "jeremia 40:7-16", "jeremia 41:1-18", "jeremia 49:1-6", "ezechiel 21:18-32", "ezechiel 25:1-7", "ezechiel 25:8-11", "daniel 11:40-45", "amos 1:13-15", "zefanja 2:8-11",
]

CANON_ORDER = "genesis exodus leviticus numeri deuteronomium jozua richteren ruth 1samuel 2samuel 1koningen 2koningen 1kronieken 2kronieken ezra nehemia esther job psalmen spreuken prediker hooglied jesaja jeremia klaagliederen ezechiel daniel hosea joel amos obadja jona micha nahum habakuk zefanja haggai zacharia maleachi mattheus markus lukas johannes handelingen romeinen 1korinthiers 2korinthiers galaten efeziers filippenzen kolossenzen 1tessalonicensen 2tessalonicensen 1timotheus 2timotheus titus filemon hebreeen jakobus 1petrus 2petrus 1johannes 2johannes 3johannes judas openbaring".split()
BOOK_ORDER = {book: index for index, book in enumerate(CANON_ORDER)}


def kaart(plaats, modern, coord, gebied, zekerheid, toelichting, label):
    return {"plaats": plaats, "moderneNaam": modern, "coordinaten": coord, "gebied": gebied,
            "zekerheid": zekerheid, "toelichting": toelichting,
            "bron": "data/geografie.geojson",
            "bronLabel": "Geografische aanduidingen in Gods Woord",
            "link": f"kaart.html?plaats={plaats}", "label": label}


NATIONS = [
    {"id": "ammon", "naam": "Ammon", "pattern": r"(?i)\b(?:ben[- ]?ammi|ammon\w*|ammons)\b", "passages": AMMON_PASSAGES,
     "onderscheiding": "Het volk Ammon; te onderscheiden van Ben-Ammi, de stamvader.",
     "beschrijving": "De Ammonieten stamden volgens Genesis af van Ben-Ammi, de jongste zoon van Lot. Hun historische kerngebied lag ten oosten van de Jordaan, rond hun hoofdstad Rabba. In Gods Woord komen zij voor als verwant buurvolk van Israël, als tegenstander en soms als deel van Israëls samenleving.",
     "naamvormen": ["Ammon", "kinderen van Ammon", "kinderen Ammons", "Ammonieten", "Ammoniet", "Ammonietische"],
     "stamvader": {"naam": "Ben-Ammi", "betekenis": "zoon van mijn volk", "relatie": "zoon van Lot en stamvader van de Ammonieten", "ref": "genesis 19:38"},
     "kaart": kaart("Rabba", "Amman, Jordanië", [35.6094, 31.9539], "historisch kerngebied ten oosten van de Jordaan", "benadering", "Rabba is zeker geïdentificeerd; de omvang van het historische gebied is bij benadering.", "AMMON")},
    {"id": "edom", "naam": "Edom", "pattern": r"(?i)\b(?:edom\w*|idume\w*)\b",
     "onderscheiding": "Edom wordt ook met Ezau verbonden; de pagina volgt het volk en het land, niet iedere persoon met deze naam.",
     "beschrijving": "De Edomieten worden in Genesis verbonden met Ezau, die ook Edom genoemd werd. Hun land lag vooral ten zuiden en zuidoosten van de Dode Zee, in het bergland van Seïr. De Bijbel vertelt over verwantschap met Israël, grensconflicten, koningen en profetieën over Edom.",
     "naamvormen": ["Edom", "Edomieten", "Edomiet", "Idumea"],
     "stamvader": {"naam": "Ezau", "betekenis": "behaard", "relatie": "zoon van Izak en Rebekka; ook Edom genoemd en stamvader van de Edomieten", "ref": "genesis 25:30"},
     "kaart": kaart("Edom", "zuid-Jordanië", [35.6, 30.5], "het bergland van Seïr, ten zuiden van de Dode Zee", "benadering", "Het kaartpunt geeft het historische kerngebied weer, niet een scherpe landsgrens.", "EDOM")},
    {"id": "midian", "naam": "Midian", "pattern": r"(?i)\b(?:midian\w*)\b",
     "onderscheiding": "Midian is zowel de naam van Abrahams zoon als van de Midianieten en hun woongebied.",
     "beschrijving": "De Midianieten stammen volgens Genesis af van Midian, een zoon van Abraham en Ketura. De Bijbelse verhalen plaatsen Midian in de woestijngebieden ten oosten en zuiden van Kanaän, maar de begrenzing van hun gebied wisselt en is niet precies vast te leggen. Mozes verbleef er vóór de uittocht; later worden de Midianieten vooral genoemd in Numeri en Richteren.",
     "naamvormen": ["Midian", "Midianieten", "Midianiet", "Midianitisch"],
     "stamvader": {"naam": "Midian", "betekenis": "twist", "relatie": "zoon van Abraham en Ketura en stamvader van de Midianieten", "ref": "genesis 25:2"},
     "kaart": kaart("Midian", "noordwest-Arabië / oostelijke Sinaï", [35.0, 28.25], "woestijngebieden rond de Golf van Akaba", "onzeker", "De Bijbelse teksten noemen Midian als uitgestrekt woongebied; een centraal kaartpunt is daarom slechts een oriëntatie.", "MIDIAN")},
    {"id": "moab", "naam": "Moab", "pattern": r"(?i)\b(?:moab\w*)\b",
     "onderscheiding": "Moab is de naam van de stamvader, het volk en het land; de pagina brengt die bij elkaar.",
     "beschrijving": "De Moabieten stammen volgens Genesis af van Moab, de zoon van Lot en zijn oudste dochter. Hun land lag op de hoogvlakte ten oosten van de Dode Zee. Moab is in Gods Woord nauw verweven met Israëls tocht door de woestijn, het verhaal van Ruth, de koningen en de profetieën.",
     "naamvormen": ["Moab", "Moabieten", "Moabiet", "Moabietische"],
     "stamvader": {"naam": "Moab", "betekenis": "uit de vader", "relatie": "zoon van Lot en stamvader van de Moabieten", "ref": "genesis 19:37"},
     "kaart": kaart("Moab", "west-Jordanië", [35.7, 31.4], "de hoogvlakte ten oosten van de Dode Zee", "benadering", "Het kaartpunt geeft de Moabitische hoogvlakte in grote lijnen weer.", "MOAB")},
]

MIDIAN_FEATURE = {"type": "Feature", "geometry": {"type": "Point", "coordinates": [35.0, 28.25]}, "properties": {"id": "midian", "naam": "Midian", "type": "streek", "moderneNaam": "noordwest-Arabië / oostelijke Sinaï", "landModern": "Jordanië / Saoedi-Arabië", "zekerheid": "onzeker", "verwijzingen": ["genesis 25:2", "exodus 2:15", "richteren 6:1"], "toelichting": "Woestijngebied van de Midianieten. De precieze ligging en omvang zijn onzeker; het punt is een oriëntatie."}}


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def expand(reference):
    match = re.fullmatch(r"(\S+) (\d+):(\d+)(?:-(\d+))?", reference)
    if not match:
        raise ValueError(f"Ongeldige verwijzing: {reference}")
    book, chapter, first, last = match.groups()
    return [f"{book} {chapter}:{verse}" for verse in range(int(first), int(last or first) + 1)]


def reference_key(reference):
    book, cv = reference.split(" ", 1)
    chapter, verse = cv.split(":", 1)
    return BOOK_ORDER.get(book, len(BOOK_ORDER)), int(chapter), int(verse)


def literal_hits(book, pattern):
    hits, regex = [], re.compile(pattern)
    for chapter in book["chaptersIncluded"]:
        path = DATA / book["id"] / f"{chapter}.json"
        if not path.exists():
            continue
        for verse in read_json(path).get("verses", []):
            text = verse.get("text2026_html") or verse.get("text2026") or ""
            if regex.search(re.sub(r"<[^>]+>", " ", text)):
                hits.append(f'{book["id"]} {chapter}:{verse["number"]}')
    return hits


def literal_references(books, pattern):
    refs = [ref for book in books if book["testament"] in {"OT", "NT"} for ref in literal_hits(book, pattern)]
    return sorted(set(refs), key=reference_key)


def ensure_midian_geography():
    path = DATA / "geografie.geojson"
    data = read_json(path)
    data["features"] = [f for f in data["features"] if f.get("properties", {}).get("naam") != "Midian"] + [MIDIAN_FEATURE]
    data.setdefault("metadata", {})["aantal"] = len(data["features"])
    write_json(path, data)


def build():
    books = read_json(DATA / "books.json")["books"]
    items, reports = [], []
    for nation in NATIONS:
        refs = nation.get("passages") or literal_references(books, nation["pattern"])
        item = {key: value for key, value in nation.items() if key not in {"pattern", "passages"}}
        item.update({"soort": "volk", "verzen": refs})
        literal = literal_references(books, nation["pattern"])
        covered = {ref for passage in refs for ref in expand(passage)}
        missing = sorted(set(literal) - covered, key=reference_key)
        if missing:
            raise RuntimeError(f'Onbedekte canonieke {nation["naam"]}-treffers: ' + ", ".join(missing))
        items.append(item)
        reports.append({"id": nation["id"], "naam": nation["naam"], "gepubliceerdePassages": len(refs), "gepubliceerdeVerzen": len(covered), "letterlijkeTreffers": len(literal), "reviewStatus": "agent-reviewed", "humanReviewed": False})
    return {"titel": "Volken & Naties", "intro": "Volken en naties in Gods Woord, met hun oorsprong, naamvormen, woongebied en alle relevante canonieke teksten.", "bron": "Gods Woord", "canon": "66 boeken", "boeknamen": {book["id"]: book["nameDutch"] for book in books}, "items": items}, {"onderwerp": "Volken & Naties", "publicatiebeleid": "Alleen passages uit de 66 canonieke boeken worden gepubliceerd.", "canoniekeBoekenGescand": sum(book["testament"] in {"OT", "NT"} for book in books), "items": reports, "reviewStatus": "agent-reviewed", "humanReviewed": False}


def update_tags(catalogue):
    path = DATA / "tags.json"
    data = read_json(path)
    tags = [tag for tag in data["tags"] if not tag.get("id", "").startswith("volk-")]
    nation_tags = []
    for nation in catalogue["items"]:
        refs = sorted({ref for passage in nation["verzen"] for ref in expand(passage)}, key=reference_key)
        nation_tags.append({"id": f'volk-{nation["id"]}', "naam": nation["naam"], "beschrijving": f'Teksten over {nation["naam"]}, de naamvormen en het verbonden volk.', "kleur": "#9a7421", "categorie": "Volken & Naties", "verzen": [{"ref": ref, "rang": 1, "categorieen": ["volken-naties", nation["id"]], "zekerheid": "zeker", "reviewStatus": "agent-reviewed", "humanReviewed": False} for ref in refs]})
    # Houd de bestaande rubriek bij haar oude anker en laat werk van andere
    # processen in tags.json in dezelfde volgorde staan.
    anchor = next((index for index, tag in enumerate(tags) if tag.get("id") == "reuzen"), len(tags))
    data["tags"] = tags[:anchor] + nation_tags + tags[anchor:]
    write_json(path, data)


if __name__ == "__main__":
    ensure_midian_geography()
    catalogue, review = build()
    write_json(DATA / "naslag-volken-naties.json", catalogue)
    write_json(DATA / "volken-naties-review.json", review)
    update_tags(catalogue)
    print("Volken & Naties: " + ", ".join(f'{item["naam"]} ({len(item["verzen"])} passages)' for item in catalogue["items"]))
