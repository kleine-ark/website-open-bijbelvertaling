#!/usr/bin/env python3
"""Bouw het agent-beoordeelde register voor Personen en stambomen.

De generator verandert geen Bijbeltekst. Bestaande gecureerde persoonsdata blijft
leidend; aanvullende lexiconitems zijn alleen een kandidaatbron. Alleen unieke,
letterlijk aangetroffen naamvormen worden automatisch gekoppeld. Botsingen,
onzekere categorieën en mogelijke kernferentie gaan naar de reviewqueue.
"""

from __future__ import annotations

from collections import defaultdict
import html
import json
from pathlib import Path
import re
import unicodedata
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
LETTER = "0-9A-Za-zÀ-ÖØ-öø-ÿ"
SCHEMA_VERSION = 1

# Namen die in de zichtbare vertaling ook een gewoon woord, plaats, stam of boek
# kunnen zijn. Nieuwe treffers worden daarom nooit zonder context toegewezen.
CONTEXT_SENSITIVE_FORMS = {
    "dan", "er", "ram", "job", "sela", "elisa", "israel", "edom", "moab",
    "hebron", "gad", "juda", "benjamin", "ephraim", "efraim", "simeon",
    "levi", "assur", "kanaan", "tarsis", "ofir", "sidon", "aram",
}


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def normalize_text(markup: str) -> str:
    text = re.sub(r"<sup\b[^>]*>.*?</sup>", "", markup or "", flags=re.I | re.S)
    text = re.sub(r"<[^>]+>", "", text)
    return re.sub(r"\s+", " ", html.unescape(text)).strip()


def stable_slug(value: str) -> str:
    value = unicodedata.normalize("NFD", value.casefold())
    value = "".join(char for char in value if unicodedata.category(char) != "Mn")
    return re.sub(r"[^a-z0-9]+", "-", value).strip("-") or "persoon"


def normalized_form(value: str) -> str:
    return stable_slug(value).replace("-", " ")


def load_corpus(root: Path) -> tuple[list[dict[str, Any]], dict[str, list[dict[str, Any]]]]:
    books = read_json(root / "data" / "books.json")["books"]
    corpus: dict[str, list[dict[str, Any]]] = {}
    for book in books:
        verses: list[dict[str, Any]] = []
        for chapter in book.get("chaptersIncluded", []):
            path = root / "data" / book["id"] / f"{chapter}.json"
            if not path.exists():
                continue
            data = read_json(path)
            for verse in data.get("verses", []):
                raw = verse.get("text2026_html") or verse.get("text2026") or ""
                text = normalize_text(raw)
                if text:
                    verses.append(
                        {
                            "ref": f"{book['id']} {chapter}:{int(verse['number'])}",
                            "text": text,
                        }
                    )
        corpus[book["id"]] = verses
    return books, corpus


def _whole_form(text: str, form: str) -> bool:
    return bool(
        re.search(
            rf"(?:^|[^{LETTER}]){re.escape(form)}(?=$|[^{LETTER}])",
            text,
        )
    )


def _actual_refs(
    forms: list[str],
    book_ids: set[str],
    corpus: dict[str, list[dict[str, Any]]],
) -> tuple[list[str], list[dict[str, str]]]:
    refs: list[str] = []
    hits: list[dict[str, str]] = []
    forms = sorted(
        {form.strip() for form in forms if form and form.strip()},
        key=lambda form: (-len(form), form.casefold(), form),
    )
    for book_id, verses in corpus.items():
        if book_ids and book_id not in book_ids:
            continue
        for verse in verses:
            for form in forms:
                if form in verse["text"] and _whole_form(verse["text"], form):
                    refs.append(verse["ref"])
                    hits.append({"ref": verse["ref"], "vorm": form, "type": "naam"})
                    break
    return refs, hits


def _kind_for(item: dict[str, Any]) -> str:
    usage = (item.get("gebruik") or "").casefold()
    text = f"{item.get('naam', '')} {item.get('beschrijving', '')}".casefold()
    if "gelijkenis" in usage or "gelijkenis" in text:
        return "gelijkenis"
    if any(word in text for word in ("engel", "aartsengel", "demon", "satan", "duivel")):
        return "bovennatuurlijk"
    if item.get("id") == "jezus" or "de zoon, god geopenbaard" in text:
        return "goddelijk"
    return "mens"


def _candidate_policy(lex: dict[str, Any]) -> tuple[bool, str]:
    name = (lex.get("lemma") or "").strip()
    description = (lex.get("uitleg") or "").casefold()
    if not name or not name[0].isupper():
        return False, "categorie-onzeker"
    if " en " in name.casefold() or "/" in name:
        return False, "categorie-onzeker"
    if "(" in name or ")" in name:
        return False, "homoniem"
    if any(word in description for word in ("volk", "stam", "inwoners", "collectief")):
        return False, "categorie-onzeker"
    if any(word in description for word in ("godin", "afgod", "godheid")):
        return False, "categorie-onzeker"
    return True, ""


def _book_position(books: list[dict[str, Any]], corpus: dict[str, list[dict[str, Any]]]) -> dict[str, int]:
    position: dict[str, int] = {}
    index = 0
    for book in books:
        for verse in corpus[book["id"]]:
            position[verse["ref"]] = index
            index += 1
    return position


def _existing_entities(
    root: Path,
    books: list[dict[str, Any]],
    corpus: dict[str, list[dict[str, Any]]],
    queues: dict[str, list[dict[str, Any]]],
) -> tuple[list[dict[str, Any]], dict[str, set[str]]]:
    old = read_json(root / "data" / "naslag-personen.json")["items"]
    tree = read_json(root / "data" / "stamboom.json")["personen"]
    catalog = read_json(root / "data" / "naslag-catalogus.json")["personen"]
    catalog_items = {
        item["id"]: item
        for item in catalog.get("aanvullingen", []) + catalog.get("extra", [])
    }
    book_ids = {book["id"] for book in books}
    forms_by_id: dict[str, set[str]] = {}
    entities: list[dict[str, Any]] = []

    for item in old:
        tree_item = tree.get(item["id"], {})
        catalog_item = catalog_items.get(item["id"], {})
        forms = {item["naam"]}
        forms.update(tree_item.get("ookGenoemd", []))
        forms.update(catalog_item.get("zoekvormen", []))
        forms = {form for form in forms if form}
        forms_by_id[item["id"]] = forms
        entity = {
            "id": item["id"],
            "slug": stable_slug(item["id"]),
            "naam": item["naam"],
            "naamvormen": sorted(forms),
            "beschrijving": item["beschrijving"],
            "soort": _kind_for(item),
            "reviewStatus": "agent-reviewed",
            "herkomst": "bestaande-gecureerde-data",
            "verzen": list(item["verzen"]),
            "vermeldingen": [
                {"ref": ref, "vorm": "bestaande koppeling", "type": "bestaand"}
                for ref in item["verzen"]
            ],
        }
        if item.get("geslacht"):
            entity["geslacht"] = item["geslacht"]
        if item.get("onderscheiding"):
            entity["onderscheiding"] = item["onderscheiding"]
        if item.get("gebruik"):
            entity["gebruik"] = item["gebruik"]
        entities.append(entity)

    form_owners: dict[str, set[str]] = defaultdict(set)
    for person_id, forms in forms_by_id.items():
        for form in forms:
            form_owners[normalized_form(form)].add(person_id)

    position = _book_position(books, corpus)
    entity_by_id = {item["id"]: item for item in entities}
    for person_id, forms in forms_by_id.items():
        entity = entity_by_id[person_id]
        # Een stamboomnaam is buiten zijn bronregister niet vanzelf dezelfde
        # persoon (Daniël, Azaria, Joas enz.). Alleen de expliciete catalogus-
        # aanvullingen hebben voldoende identiteit/context om naamtreffers uit
        # andere hoofdstukken toe te voegen.
        safe = [
            form for form in forms
            if person_id in catalog_items
            if len(form) > 2
            and normalized_form(form) not in CONTEXT_SENSITIVE_FORMS
            and len(form_owners[normalized_form(form)]) == 1
        ]
        scoped = set(catalog_items.get(person_id, {}).get("boeken", [])) or book_ids
        found, hits = _actual_refs(safe, scoped, corpus)
        existing = set(entity["verzen"])
        for hit in hits:
            if hit["ref"] not in existing:
                entity["vermeldingen"].append(hit)
        entity["verzen"] = sorted(existing | set(found), key=position.__getitem__)

        unsafe = forms - set(safe)
        if unsafe:
            for book_id in scoped:
                refs, _ = _actual_refs(sorted(unsafe), {book_id}, corpus)
                for ref in refs:
                    if ref not in existing:
                        queues[book_id].append(
                            {
                                "ref": ref,
                                "kandidaat": entity["naam"],
                                "voorgesteldId": person_id,
                                "reden": "homoniem",
                                "reviewStatus": "agent-reviewed",
                            }
                        )
    return entities, forms_by_id


def _add_lexicon_candidates(
    root: Path,
    books: list[dict[str, Any]],
    corpus: dict[str, list[dict[str, Any]]],
    entities: list[dict[str, Any]],
    forms_by_id: dict[str, set[str]],
    queues: dict[str, list[dict[str, Any]]],
) -> None:
    lexicon = [
        item for item in read_json(root / "data" / "lexicon-master.json")
        if item.get("categorie") == "persoon"
    ]
    book_ids = {book["id"] for book in books}
    existing_forms = {
        normalized_form(form)
        for forms in forms_by_id.values()
        for form in forms
    }
    candidate_forms: dict[str, set[str]] = defaultdict(set)
    for item in lexicon:
        for form in [item.get("lemma", "")] + item.get("varianten", []):
            if form:
                candidate_forms[normalized_form(form)].add(item.get("lemma", ""))

    used_ids = {item["id"] for item in entities}
    position = _book_position(books, corpus)
    for lex in lexicon:
        name = (lex.get("lemma") or "").strip()
        allowed, reason = _candidate_policy(lex)
        scope = set(lex.get("ook_in_boeken", [])) & book_ids
        description = (lex.get("uitleg") or "").casefold()
        if "profeet" in description or "apostel" in description:
            for book in books:
                if normalized_form(book["nameDutch"]) == normalized_form(name):
                    scope.add(book["id"])
        if not scope:
            scope = book_ids
        forms = [name] + [form for form in lex.get("varianten", []) if form]
        normalized = {normalized_form(form) for form in forms if form}
        collision = bool(normalized & existing_forms) or any(
            len(candidate_forms[value]) > 1 for value in normalized
        )
        if collision:
            allowed, reason = False, "homoniem"
        refs, hits = _actual_refs(forms, scope, corpus)
        if not allowed or not refs:
            target_books = {ref.split(" ", 1)[0] for ref in refs} or scope
            for book_id in sorted(target_books):
                book_refs = [ref for ref in refs if ref.startswith(book_id + " ")]
                queues[book_id].append(
                    {
                        "ref": book_refs[0] if book_refs else None,
                        "kandidaat": name,
                        "reden": reason or "categorie-onzeker",
                        "reviewStatus": "agent-reviewed",
                    }
                )
            continue

        person_id = stable_slug(name)
        base = person_id
        suffix = 2
        while person_id in used_ids:
            person_id = f"{base}-{suffix}"
            suffix += 1
        used_ids.add(person_id)
        existing_forms.update(normalized)
        entity = {
            "id": person_id,
            "slug": person_id,
            "naam": name,
            "naamvormen": sorted(set(forms)),
            "beschrijving": lex.get("uitleg") or f"{name}, genoemd in de Bijbel.",
            "soort": _kind_for({"naam": name, "beschrijving": lex.get("uitleg", "")}),
            "reviewStatus": "agent-reviewed",
            "herkomst": "lexicon-kandidaat-contextueel-behouden",
            "verzen": sorted(set(refs), key=position.__getitem__),
            "vermeldingen": hits,
        }
        entities.append(entity)


def _relations(root: Path) -> list[dict[str, Any]]:
    tree = read_json(root / "data" / "stamboom.json")["personen"]
    relations: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for child_id, child in tree.items():
        if child.get("soort") == "volk":
            continue
        refs = [
            f"{verse['boek']} {verse['hoofdstuk']}:{verse['vers']}"
            for verse in child.get("verzen", [])[:1]
        ]
        for relation_type, parent_id in (("vader", child.get("vader")), ("moeder", child.get("moeder"))):
            if not parent_id or tree.get(parent_id, {}).get("soort") == "volk":
                continue
            key = (relation_type, parent_id, child_id)
            if key in seen:
                continue
            seen.add(key)
            relations.append(
                {
                    "type": relation_type,
                    "van": parent_id,
                    "naar": child_id,
                    "refs": refs,
                    "zekerheid": "waarschijnlijk",
                    "reviewStatus": "agent-reviewed",
                    "herkomst": "bestaande-stamboom",
                }
            )
        for partner_id in child.get("partners", []):
            if partner_id not in tree or tree.get(partner_id, {}).get("soort") == "volk":
                continue
            pair = tuple(sorted((child_id, partner_id)))
            key = ("partner", pair[0], pair[1])
            if key in seen:
                continue
            seen.add(key)
            shared = {
                (v["boek"], v["hoofdstuk"], v["vers"])
                for v in child.get("verzen", [])
            } & {
                (v["boek"], v["hoofdstuk"], v["vers"])
                for v in tree[partner_id].get("verzen", [])
            }
            partner_refs = [f"{b} {c}:{v}" for b, c, v in sorted(shared)] or refs
            relations.append(
                {
                    "type": "partner",
                    "van": pair[0],
                    "naar": pair[1],
                    "refs": partner_refs,
                    "zekerheid": "waarschijnlijk",
                    "reviewStatus": "agent-reviewed",
                    "herkomst": "bestaande-stamboom",
                }
            )
    return relations


def validate_register(register: dict[str, Any], root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    people = register.get("personen", [])
    ids = [item.get("id") for item in people]
    slugs = [item.get("slug") for item in people]
    if len(ids) != len(set(ids)):
        errors.append("dubbele persoon-id")
    if len(slugs) != len(set(slugs)):
        errors.append("dubbele persoon-slug")
    known = set(ids)
    books = {book["id"]: book for book in read_json(root / "data" / "books.json")["books"]}
    for item in people:
        if item.get("reviewStatus") == "human-reviewed":
            errors.append(f"onterecht human-reviewed: {item.get('id')}")
        for ref in item.get("verzen", []):
            try:
                book_id, location = ref.split(" ", 1)
                chapter, verse = (int(value) for value in location.split(":", 1))
            except (ValueError, AttributeError):
                errors.append(f"ongeldige ref: {ref}")
                continue
            if book_id not in books or not (root / "data" / book_id / f"{chapter}.json").exists():
                errors.append(f"verweesde ref: {ref}")
                continue
            data = read_json(root / "data" / book_id / f"{chapter}.json")
            if verse not in {int(item["number"]) for item in data.get("verses", [])}:
                errors.append(f"onbekend vers: {ref}")
    for rel in register.get("relaties", []):
        if rel.get("van") not in known or rel.get("naar") not in known:
            errors.append(f"verweesde relatie: {rel}")
        if not rel.get("refs") or not rel.get("zekerheid"):
            errors.append(f"relatie zonder bewijs: {rel}")
    return errors


def build_register(root: Path = ROOT, write: bool = True) -> dict[str, Any]:
    books, corpus = load_corpus(root)
    queues: dict[str, list[dict[str, Any]]] = {book["id"]: [] for book in books}
    entities, forms = _existing_entities(root, books, corpus, queues)
    _add_lexicon_candidates(root, books, corpus, entities, forms, queues)
    positions = _book_position(books, corpus)
    entities.sort(key=lambda item: positions.get(item["verzen"][0], 10**9))
    relations = _relations(root)
    book_names = {book["id"]: book["nameDutch"] for book in books}

    # Kernferentie wordt bewust niet gegokt. Iedere boekqueue houdt deze nog te
    # verrichten controleslag zichtbaar, ook wanneer er geen naambotsing was.
    for book in books:
        first_ref = corpus[book["id"]][0]["ref"] if corpus[book["id"]] else None
        queues[book["id"]].append(
            {
                "ref": first_ref,
                "kandidaat": "verwijzingen via titel of voornaamwoord",
                "reden": "mogelijke-kernferentie",
                "reviewStatus": "agent-reviewed",
            }
        )

    register = {
        "schemaVersion": SCHEMA_VERSION,
        "titel": "Personen en stambomen",
        "bron": "de hele Bijbel",
        "corpusbreed": True,
        "intro": "Personen uit alle 88 boeken, met hun naamvormen, relaties en gekoppelde Bijbelteksten.",
        "beleid": {
            "mensen": "opgenomen wanneer bij naam genoemd of individueel herkenbaar",
            "bovennatuurlijk": "benoemde goddelijke, engelachtige en demonische figuren afzonderlijk gemarkeerd",
            "gelijkenissen": "individueel herkenbare figuren afzonderlijk gemarkeerd",
            "collectieven": "niet als persoon gepubliceerd",
            "kernferentie": "niet automatisch toegewezen; twijfel gaat naar de reviewqueue",
            "reviewStatus": "alle nieuwe bevindingen zijn agent-reviewed, nooit human-reviewed",
        },
        "boeknamen": book_names,
        "personen": entities,
        "relaties": relations,
    }
    errors = validate_register(register, root)
    if errors:
        raise ValueError("\n".join(errors[:50]))

    per_book = []
    for book in books:
        prefix = book["id"] + " "
        per_book.append(
            {
                "id": book["id"],
                "naam": book["nameDutch"],
                "testament": book.get("testament", ""),
                "verzen": len(corpus[book["id"]]),
                "personen": sum(
                    any(ref.startswith(prefix) for ref in item["verzen"])
                    for item in entities
                ),
                "vermeldingen": sum(
                    sum(ref.startswith(prefix) for ref in item["verzen"])
                    for item in entities
                ),
                "twijfelgevallen": len(queues[book["id"]]),
                "status": "agent-reviewed",
            }
        )
    coverage = {
        "schemaVersion": SCHEMA_VERSION,
        "boekenTotaal": len(books),
        "verzenTotaal": sum(len(verses) for verses in corpus.values()),
        "personenTotaal": len(entities),
        "relatiesTotaal": len(relations),
        "perBoek": per_book,
    }
    review_queues = {
        book_id: {
            "boek": book_id,
            "reviewStatus": "agent-reviewed",
            "gevallen": cases,
        }
        for book_id, cases in queues.items()
    }
    result = {"register": register, "coverage": coverage, "reviewQueues": review_queues}

    if write:
        outputs = {
            "personen-register.json": register,
            "personen-dekking.json": coverage,
            "personen-reviewqueues.json": review_queues,
        }
        for filename, data in outputs.items():
            (root / "data" / filename).write_text(
                json.dumps(data, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
    return result


def main() -> int:
    result = build_register(ROOT, write=True)
    coverage = result["coverage"]
    print(
        f"Personenregister: {coverage['personenTotaal']} personen, "
        f"{coverage['relatiesTotaal']} relaties, "
        f"{coverage['boekenTotaal']} boeken en {coverage['verzenTotaal']} verzen."
    )
    for book in coverage["perBoek"]:
        print(
            f"{book['naam']}: {book['personen']} personen, "
            f"{book['vermeldingen']} verwijzingen, {book['twijfelgevallen']} twijfelgevallen"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
