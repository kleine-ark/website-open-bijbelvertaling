#!/usr/bin/env python3
"""Vul uitsluitend bronvaste woordnummers aan uit reeds gekoppelde repo-data.

De koppeling is bewust streng: alleen een exact gelijke Griekse, Ge'ez- of
Latijnse woordvorm die elders in het corpus steeds hetzelfde nummer heeft,
mag worden hergebruikt. Hebreeuwse segmenten worden uitgesloten omdat een
ongerelateerde lexicale vorm visueel gelijk kan zijn aan een suffixsegment.
"""

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"


def detect_script(word):
    if not isinstance(word, str) or not word.strip():
        return None
    codepoints = [ord(char) for char in word if char.isalpha()]
    if not codepoints:
        return None
    if any(0x0370 <= cp <= 0x03FF or 0x1F00 <= cp <= 0x1FFF for cp in codepoints):
        return "greek"
    if any(0x1200 <= cp <= 0x139F or 0x2D80 <= cp <= 0x2DDF for cp in codepoints):
        return "geez"
    if all(
        0x0041 <= cp <= 0x005A
        or 0x0061 <= cp <= 0x007A
        or 0x00C0 <= cp <= 0x024F
        for cp in codepoints
    ):
        return "latin"
    return None


def expected_family(script):
    return {"greek": "G", "geez": "OVG", "latin": "OVL"}.get(script)


def family_matches(script, number):
    prefix = expected_family(script)
    if not prefix:
        return False
    if prefix == "G":
        return number.startswith("G") and not number.startswith("OVG")
    return number.startswith(prefix)


def build_exact_index(tokens):
    candidates = defaultdict(set)
    for token in tokens:
        if not isinstance(token, dict):
            continue
        word = str(token.get("woord") or "").strip()
        number = str(token.get("strongs") or "").strip()
        script = detect_script(word)
        if script and number and family_matches(script, number):
            candidates[(script, word)].add(number)

    index = {}
    ambiguous = {}
    for key, numbers in candidates.items():
        if len(numbers) == 1:
            index[key] = next(iter(numbers))
        else:
            ambiguous[key] = sorted(numbers)
    return index, ambiguous


def propose_fill(token, index):
    if not isinstance(token, dict) or str(token.get("strongs") or "").strip():
        return None
    word = str(token.get("woord") or "").strip()
    script = detect_script(word)
    if not script:
        return None
    number = index.get((script, word))
    return number if number and family_matches(script, number) else None


def dump_json_like(data, source):
    """Serializeer zonder de bestaande inspringing of regeleinden om te zetten."""
    newline = "\r\n" if "\r\n" in source else "\n"
    indent_match = re.search(r"(?:\r?\n)([ \t]+)\"", source)
    indent = indent_match.group(1) if indent_match else "  "
    indent_arg = "\t" if "\t" in indent else len(indent)
    rendered = json.dumps(data, ensure_ascii=False, indent=indent_arg)
    if newline != "\n":
        rendered = rendered.replace("\n", newline)
    return rendered + (newline if source.endswith(("\n", "\r\n")) else "")


def chapter_paths(data_dir=DATA):
    books = json.loads((data_dir / "books.json").read_text(encoding="utf-8"))["books"]
    for book in books:
        for chapter in book.get("chaptersIncluded", []):
            path = data_dir / book["id"] / f"{chapter}.json"
            if path.exists():
                yield book["id"], chapter, path


def corpus_tokens(data_dir=DATA):
    for _book, _chapter, path in chapter_paths(data_dir):
        data = json.loads(path.read_text(encoding="utf-8"))
        for verse in data.get("verses", []):
            if isinstance(verse, dict):
                yield from (verse.get("grondtekst") or [])


def fill_corpus(data_dir=DATA, write=False):
    index, ambiguous = build_exact_index(corpus_tokens(data_dir))
    report = {
        "mode": "write" if write else "dry-run",
        "filled": 0,
        "by_family": defaultdict(int),
        "by_book": defaultdict(int),
        "ambiguous_surface_forms": len(ambiguous),
    }
    for book, _chapter, path in chapter_paths(data_dir):
        source = path.read_bytes().decode("utf-8")
        data = json.loads(source)
        changed = False
        for verse in data.get("verses", []):
            if not isinstance(verse, dict):
                continue
            for token in verse.get("grondtekst") or []:
                number = propose_fill(token, index)
                if not number:
                    continue
                token["strongs"] = number
                report["filled"] += 1
                family = "OVG" if number.startswith("OVG") else (
                    "OVL" if number.startswith("OVL") else number[0]
                )
                report["by_family"][family] += 1
                report["by_book"][book] += 1
                changed = True
        if write and changed:
            path.write_bytes(dump_json_like(data, source).encode("utf-8"))
    report["by_family"] = dict(sorted(report["by_family"].items()))
    report["by_book"] = dict(sorted(report["by_book"].items()))
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true", help="schrijf veilige aanvullingen")
    args = parser.parse_args()
    print(json.dumps(fill_corpus(write=args.write), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
