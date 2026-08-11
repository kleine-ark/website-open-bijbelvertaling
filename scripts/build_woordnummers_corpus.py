#!/usr/bin/env python3
"""Bouw gefaseerde Nederlandse inline-Strongprojecties en een reviewstatus."""

import argparse
import hashlib
import json
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUTPUT = DATA / "woordnummers-inline"
WORD_RE = re.compile(r"[^\W\d_]+", re.UNICODE)
NUMBER_RE = re.compile(r"(?:H\d+[A-Za-z]?|G\d+[A-Za-z]?)")


def normalize(value):
    decomposed = unicodedata.normalize("NFD", str(value or "").casefold())
    return "".join(char for char in decomposed if unicodedata.category(char) != "Mn")


def dutch_tokens(text):
    occurrences = defaultdict(int)
    result = []
    for index, match in enumerate(WORD_RE.finditer(str(text or ""))):
        word = match.group(0)
        key = normalize(word)
        occurrences[key] += 1
        result.append({"tekst": word, "norm": key, "voorkomen": occurrences[key], "index": index})
    return result


def lexicon_terms(entry):
    if not isinstance(entry, dict):
        return set()
    text = " ".join(str(entry.get(field) or "") for field in ("glossNl", "samenvattingNl"))
    return {normalize(match.group(0)) for match in WORD_RE.finditer(text)}


def project_verse(verse, lexicon, chapter_verified):
    tokens = dutch_tokens(verse.get("text2026") or verse.get("textHerzien") or "")
    source = []
    for word in verse.get("grondtekst") or []:
        for raw_number in str(word.get("strongs") or "").split():
            if not NUMBER_RE.fullmatch(raw_number):
                continue
            number = raw_number
            source.append({"number": number, "word": word})

    manual = [item for item in verse.get("woordnummers") or [] if isinstance(item, dict)]
    manual_numbers = Counter(
        number
        for item in manual
        for number in item.get("strongs") or []
        if NUMBER_RE.fullmatch(str(number))
    )
    remaining_source = []
    for item in source:
        if manual_numbers[item["number"]]:
            manual_numbers[item["number"]] -= 1
        else:
            remaining_source.append(item)
    source = remaining_source
    manual_keys = {
        (normalize(item.get("tekst")), int(item.get("voorkomen", 1))) for item in manual
    }
    manual_links = sum(len(item.get("strongs") or []) for item in manual)
    if not tokens or not source:
        return {"mappings": [], "manual_links": manual_links, "visible_links": 0, "review_links": len(source)}

    grouped = defaultdict(list)
    source_denominator = max(1, len(source) - 1)
    token_denominator = max(1, len(tokens) - 1)
    for source_index, item in enumerate(source):
        terms = lexicon_terms(lexicon.get(item["number"]))
        exact = [token for token in tokens if token["norm"] in terms]
        candidates = exact or tokens
        expected = source_index / source_denominator
        target = min(candidates, key=lambda token: abs(token["index"] / token_denominator - expected))
        is_visible = bool(exact and chapter_verified)
        grouped[(target["index"], is_visible)].append(item)

    mappings = []
    visible_links = 0
    review_links = 0
    for (token_index, visible), items in sorted(grouped.items()):
        token = tokens[token_index]
        key = (token["norm"], token["voorkomen"])
        if key in manual_keys:
            continue
        numbers = [item["number"] for item in items]
        status = "automatisch_hoog_vertrouwen" if visible else "review_nodig"
        mappings.append({
            "tekst": token["tekst"],
            "voorkomen": token["voorkomen"],
            "strongs": numbers,
            "confidence": 0.95 if visible else 0.35,
            "reviewstatus": status,
        })
        if visible:
            visible_links += len(numbers)
        else:
            review_links += len(numbers)
    return {
        "mappings": mappings,
        "manual_links": manual_links,
        "visible_links": visible_links,
        "review_links": review_links,
    }


def is_verified(selection, chapter):
    return selection == "all" or isinstance(selection, list) and chapter in selection


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest().upper()


def status_markdown(status):
    lines = [
        "# Inline-Strongstatus per boek",
        "",
        "Automatisch opgebouwd door `scripts/build_woordnummers_corpus.py`. Alleen handmatige mappings en exacte lexiconmatches in reeds nagekeken hoofdstukken zijn zichtbaar; de overige koppelingen blijven in de reviewwachtrij.",
        "",
        "| Boek | Fase | Verzen zichtbaar/geschikt | Handmatig | Automatisch zichtbaar | Review nodig | Linkdekking |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    totals = defaultdict(int)
    for book_id, item in status.get("books", {}).items():
        source = item.get("source_links", 0)
        visible = item.get("manual_links", 0) + item.get("automatic_visible_links", 0)
        percentage = f"{(visible / source * 100 if source else 0):.2f}%".replace(".", ",")
        lines.append(
            f"| {book_id} | {item.get('phase', '')} | {item.get('visible_verses', 0)}/{item.get('eligible_verses', 0)} | "
            f"{item.get('manual_links', 0)} | {item.get('automatic_visible_links', 0)} | {item.get('review_links', 0)} | {percentage} |"
        )
        for key in ("source_links", "manual_links", "automatic_visible_links", "review_links", "visible_verses", "eligible_verses"):
            totals[key] += item.get(key, 0)
    visible = totals["manual_links"] + totals["automatic_visible_links"]
    percentage = f"{(visible / totals['source_links'] * 100 if totals['source_links'] else 0):.2f}%".replace(".", ",")
    lines.append(
        f"| **Totaal** |  | **{totals['visible_verses']}/{totals['eligible_verses']}** | "
        f"**{totals['manual_links']}** | **{totals['automatic_visible_links']}** | **{totals['review_links']}** | **{percentage}** |"
    )
    return "\n".join(lines) + "\n"


def build(output_dir=OUTPUT, write=False):
    books = json.loads((DATA / "books.json").read_text(encoding="utf-8"))["books"]
    verified = json.loads((DATA / "verified-chapters.json").read_text(encoding="utf-8"))
    lexicon = {}
    lexicon_paths = [DATA / "lexicon-nl" / "bdb-nl.json", DATA / "lexicon-nl" / "abbott-nl.json"]
    for path in lexicon_paths:
        lexicon.update(json.loads(path.read_text(encoding="utf-8")))

    source = {
        "type": "lokale-grondtekst-met-nederlandse-lexiconprojectie",
        "pipeline_version": 1,
        "lexicon_sha256": {path.name: sha256(path) for path in lexicon_paths},
    }
    status = {"source": source, "books": {}}
    output_dir = Path(output_dir)
    if write:
        output_dir.mkdir(parents=True, exist_ok=True)

    for book in books:
        selection = verified.get(book["id"])
        book_output = {"source": source, "book": book["id"], "chapters": {}}
        counters = defaultdict(int)
        for chapter in book.get("chaptersIncluded", []):
            path = DATA / book["id"] / f"{chapter}.json"
            if not path.exists():
                continue
            data = json.loads(path.read_text(encoding="utf-8"))
            chapter_verified = is_verified(selection, chapter)
            if chapter_verified:
                counters["verified_chapters"] += 1
            verse_output = {}
            for verse in data.get("verses", []):
                result = project_verse(verse, lexicon, chapter_verified)
                total = result["manual_links"] + result["visible_links"] + result["review_links"]
                if not total:
                    continue
                counters["eligible_verses"] += 1
                counters["source_links"] += total
                counters["manual_links"] += result["manual_links"]
                counters["automatic_visible_links"] += result["visible_links"]
                counters["review_links"] += result["review_links"]
                if result["manual_links"] or result["visible_links"]:
                    counters["visible_verses"] += 1
                visible_mappings = [
                    mapping for mapping in result["mappings"]
                    if mapping["reviewstatus"] == "automatisch_hoog_vertrouwen"
                ]
                if visible_mappings:
                    verse_output[str(verse["number"])] = visible_mappings
            if verse_output:
                book_output["chapters"][str(chapter)] = verse_output
        status["books"][book["id"]] = {
            "phase": "nagekeken_tekst" if selection else "resterend_corpus",
            **dict(counters),
        }
        if write:
            (output_dir / f"{book['id']}.json").write_text(
                json.dumps(book_output, ensure_ascii=False, separators=(",", ":")) + "\n",
                encoding="utf-8",
            )

    if write:
        (output_dir / "status.json").write_text(
            json.dumps(status, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        (ROOT / "docs" / "woordnummers-status-per-boek.md").write_text(
            status_markdown(status), encoding="utf-8"
        )
    return status


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=OUTPUT)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    status = build(args.output_dir, args.write)
    totals = defaultdict(int)
    for item in status["books"].values():
        for key, value in item.items():
            if isinstance(value, int):
                totals[key] += value
    print(json.dumps({"mode": "write" if args.write else "dry-run", **totals}, indent=2))


if __name__ == "__main__":
    main()
