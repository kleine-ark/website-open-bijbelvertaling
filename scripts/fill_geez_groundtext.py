#!/usr/bin/env python3
"""Herstel Ge'ez-grondtekst waar de repo zelf expliciete versregels bevat."""

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
SOURCES = {
    "1meqabyan": ROOT / "ethiopische-boeken" / "meqabyan" / "1meqabyan-geez-digitaal.txt",
    "2meqabyan": ROOT / "ethiopische-boeken" / "meqabyan" / "2meqabyan-geez-digitaal.txt",
    "3meqabyan": ROOT / "ethiopische-boeken" / "meqabyan" / "3meqabyan-geez-digitaal.txt",
}
VERSE_RE = re.compile(r"^\s*(\d+):(\d+)\s+(.+?)\s*$")
SEPARATOR_RE = re.compile(r"[\s፡።፣፤፥፦፧፨]+")


def parse_source(source):
    verses = {}
    for line in source.splitlines():
        match = VERSE_RE.match(line)
        if match:
            verses[(int(match.group(1)), int(match.group(2)))] = match.group(3)
    return verses


def is_geez_letter(char):
    cp = ord(char)
    return 0x1200 <= cp <= 0x137F or 0x2D80 <= cp <= 0x2DDF


def tokenize_geez(source_line):
    result = []
    for raw in SEPARATOR_RE.split(source_line):
        token = raw.strip()
        while token and not is_geez_letter(token[0]):
            token = token[1:]
        while token and not is_geez_letter(token[-1]):
            token = token[:-1]
        if token and any(is_geez_letter(char) for char in token):
            result.append(token)
    return result


def load_lexicon(data_dir=DATA):
    entries = json.loads((data_dir / "lexicon-geez.json").read_text(encoding="utf-8"))["woorden"]
    return {entry["woord"]: entry for entry in entries if entry.get("woord")}


def existing_ovg_index(data_dir=DATA):
    numbers = defaultdict(set)
    books = json.loads((data_dir / "books.json").read_text(encoding="utf-8"))["books"]
    for book in books:
        for chapter in book.get("chaptersIncluded", []):
            path = data_dir / book["id"] / f"{chapter}.json"
            if not path.exists():
                continue
            data = json.loads(path.read_text(encoding="utf-8"))
            for verse in data.get("verses", []):
                if not isinstance(verse, dict):
                    continue
                for token in verse.get("grondtekst") or []:
                    if not isinstance(token, dict):
                        continue
                    word = str(token.get("woord") or "").strip()
                    number = str(token.get("strongs") or "").strip()
                    if word and number.startswith("OVG"):
                        numbers[word].add(number)
    return {
        ("geez", word): next(iter(values))
        for word, values in numbers.items()
        if len(values) == 1
    }


def build_groundtext(source_line, lexicon, exact_numbers):
    groundtext = []
    for word in tokenize_geez(source_line):
        entry = lexicon.get(word, {})
        token = {"woord": word}
        for key in ("transliteratie", "betekenis"):
            if entry.get(key):
                token[key] = entry[key]
        number = entry.get("ovg") or exact_numbers.get(("geez", word))
        if number:
            token["strongs"] = number
        groundtext.append(token)
    return groundtext


def dump_json_like(data, source):
    newline = "\r\n" if "\r\n" in source else "\n"
    indent_match = re.search(r"(?:\r?\n)([ \t]+)\"", source)
    indent = indent_match.group(1) if indent_match else "  "
    indent_arg = "\t" if "\t" in indent else len(indent)
    rendered = json.dumps(data, ensure_ascii=False, indent=indent_arg)
    if newline != "\n":
        rendered = rendered.replace("\n", newline)
    return rendered + (newline if source.endswith(("\n", "\r\n")) else "")


def fill(data_dir=DATA, sources=SOURCES, write=False):
    lexicon = load_lexicon(data_dir)
    exact_numbers = existing_ovg_index(data_dir)
    report = {"mode": "write" if write else "dry-run", "verses_filled": 0, "tokens_added": 0, "numbered_tokens_added": 0, "by_book": {}}
    for book, source_path in sources.items():
        source_verses = parse_source(source_path.read_text(encoding="utf-8"))
        book_count = 0
        for path in sorted((data_dir / book).glob("[0-9]*.json"), key=lambda item: int(item.stem)):
            source = path.read_bytes().decode("utf-8")
            data = json.loads(source)
            changed = False
            for verse in data.get("verses", []):
                if not isinstance(verse, dict) or (verse.get("grondtekst") or []):
                    continue
                key = (int(path.stem), int(verse["number"]))
                source_line = source_verses.get(key)
                if not source_line:
                    continue
                groundtext = build_groundtext(source_line, lexicon, exact_numbers)
                if not groundtext:
                    continue
                verse["grondtekst"] = groundtext
                report["verses_filled"] += 1
                report["tokens_added"] += len(groundtext)
                report["numbered_tokens_added"] += sum(bool(token.get("strongs")) for token in groundtext)
                book_count += 1
                changed = True
            if write and changed:
                path.write_bytes(dump_json_like(data, source).encode("utf-8"))
        report["by_book"][book] = book_count
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    print(json.dumps(fill(write=args.write), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
