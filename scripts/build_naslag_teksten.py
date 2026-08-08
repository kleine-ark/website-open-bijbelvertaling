#!/usr/bin/env python3
"""Bouw volledige tekstbundels voor de liederen- en gebedenwiki."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
COLLECTIONS = {
    "liederen": ("naslag-liederen.json", "Lied", 177),
    "gebeden": ("naslag-gebeden.json", "Gebed", 45),
}


def read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"ontbrekend of ongeldig JSON-bestand: {path}") from exc


def load_chapter(root: Path, book: str, chapter: int) -> dict:
    """Lees één hoofdstuk en geef een duidelijke bronverwijzing bij fouten."""

    path = root / "data" / book / f"{chapter}.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"ontbrekend of ongeldig hoofdstuk: {book} {chapter}") from exc
    if not isinstance(data.get("verses"), list):
        raise ValueError(f"ontbrekende verzenlijst: {book} {chapter}")
    return data


def bundle_verse(book: str, chapter: int, verse: dict) -> dict:
    number = verse.get("number")
    text = verse.get("text2026")
    if not isinstance(number, int):
        raise ValueError(f"ongeldig versnummer in {book} {chapter}")
    if not isinstance(text, str) or not text.strip():
        raise ValueError(f"lege text2026 voor {book} {chapter}:{number}")
    return {"nummer": number, "tekst": text}


def chapter_section(
    root: Path, book: str, chapter: int, first: int | None = None, last: int | None = None
) -> dict:
    data = load_chapter(root, book, chapter)
    by_number = {verse.get("number"): verse for verse in data["verses"]}

    if first is None or last is None:
        selected = data["verses"]
    else:
        selected = []
        for number in range(first, last + 1):
            verse = by_number.get(number)
            if verse is None:
                raise ValueError(f"ontbrekend vers: {book} {chapter}:{number}")
            selected.append(verse)

    return {
        "boek": book,
        "hoofdstuk": chapter,
        "verzen": [bundle_verse(book, chapter, verse) for verse in selected],
    }


def expand_passage(root: Path, passage: dict) -> dict:
    """Werk één gewone passage of hoofdstukreeks uit tot letterlijke tekst."""

    book = passage["boek"]
    label = passage["label"]
    if "hoofdstuk" in passage:
        sections = [
            chapter_section(
                root,
                book,
                int(passage["hoofdstuk"]),
                int(passage["van"]),
                int(passage["tot"]),
            )
        ]
    else:
        sections = [
            chapter_section(root, book, chapter)
            for chapter in range(
                int(passage["vanHoofdstuk"]), int(passage["totHoofdstuk"]) + 1
            )
        ]
    return {"label": label, "sections": sections}


def build_collection(root: Path, kind: str, source_name: str) -> dict[str, dict]:
    """Valideer en bouw één genummerde verzameling in bronvolgorde."""

    if kind not in COLLECTIONS:
        raise ValueError(f"onbekende verzameling: {kind}")
    _, expected_type, expected_count = COLLECTIONS[kind]
    source = read_json(root / "data" / source_name)
    items = source.get("items")
    if not isinstance(items, list) or len(items) != expected_count:
        raise ValueError(f"{kind} moet exact {expected_count} items bevatten")
    if source.get("nummerType") != expected_type:
        raise ValueError(f"{kind} mist nummerType {expected_type}")

    result: dict[str, dict] = {}
    for number, item in enumerate(items, start=1):
        item_id = item.get("id")
        if not isinstance(item_id, str) or not item_id.strip():
            raise ValueError(f"{kind} bevat een leeg item-id")
        if item_id in result:
            raise ValueError(f"dubbel item-id in {kind}: {item_id}")
        passages = item.get("tekstpassages")
        if not isinstance(passages, list) or not passages:
            raise ValueError(f"ontbrekende tekstpassages voor {item_id}")

        bundle = {
            "id": item_id,
            "nummerType": expected_type,
            "nummer": number,
            "naam": item["naam"],
            "passages": [expand_passage(root, passage) for passage in passages],
        }
        if item.get("tekstmelding"):
            bundle["tekstmelding"] = item["tekstmelding"]
        result[item_id] = bundle
    return result


def write_collection(root: Path, kind: str, bundles: dict[str, dict]) -> None:
    target = root / "data" / "naslag-teksten" / kind
    target.mkdir(parents=True, exist_ok=True)
    expected_files = {f"{item_id}.json" for item_id in bundles}

    for stale in target.glob("*.json"):
        if stale.name not in expected_files:
            stale.unlink()

    for item_id, bundle in bundles.items():
        destination = target / f"{item_id}.json"
        temporary = target / f".{item_id}.json.tmp"
        temporary.write_text(
            json.dumps(bundle, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        temporary.replace(destination)


def build_all(root: Path = ROOT, write: bool = True) -> dict[str, dict[str, dict]]:
    """Bouw beide verzamelingen en schrijf ze desgewenst naar de site-data."""

    built = {
        kind: build_collection(root, kind, source_name)
        for kind, (source_name, _, _) in COLLECTIONS.items()
    }
    if write:
        for kind, bundles in built.items():
            write_collection(root, kind, bundles)
    return built


def main() -> None:
    built = build_all()
    print(
        "naslagteksten gebouwd: "
        f"{len(built['liederen'])} liederen, {len(built['gebeden'])} gebeden"
    )


if __name__ == "__main__":
    main()
