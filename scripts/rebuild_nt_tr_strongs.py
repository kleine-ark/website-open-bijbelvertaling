#!/usr/bin/env python3
"""Gepinde Textus-Receptus-bronlaag voor handmatig beoordeelde NT-hoofdstukken."""

from __future__ import annotations

import hashlib
import html
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from import_inline_woordnummers import parse_tr_utr  # noqa: E402


UTR_SHA256 = {
    "JOH.UTR": "77FBB830AE3E11B79F7F47A8E68A119DC77F0722EBCC99BB00111702797BFFE5",
}
OSIS_SHA256 = "2BC5C343DA30125AF8D4D1E27F8444019030B6350D16E69EF8645BF9E17D5963"
FORM_STRONG_OVERRIDES = {
    ("G4183", "A-APM-C"): "G4119",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def normal(number: str) -> str:
    digits = "".join(character for character in str(number) if character.isdigit())
    return f"G{int(digits)}" if digits else ""


def parse_osis_chapter(path: Path, osis_book: str, chapter: int) -> dict[int, dict[int, dict]]:
    if sha256(path) != OSIS_SHA256:
        raise ValueError("De gepinde CrossWire-OSIS-bron heeft een afwijkende SHA-256")
    xml = path.read_text(encoding="utf-8")
    pattern = re.compile(
        rf'<verse osisID="{re.escape(osis_book)}\.{chapter}\.(\d+)" '
        rf'sID="{re.escape(osis_book)}\.{chapter}\.\1"/>(.*?)'
        rf'<verse eID="{re.escape(osis_book)}\.{chapter}\.\1"/>',
        re.DOTALL,
    )
    verses = {}
    for verse_match in pattern.finditer(xml):
        verse = int(verse_match.group(1))
        indexed = {}
        for word_match in re.finditer(r'<w\s+([^>]*?)(?:/>|>(.*?)</w>)', verse_match.group(2), re.DOTALL):
            attrs = dict(re.findall(r'(\w+)="([^"]*)"', word_match.group(1)))
            source_indices = [int(value) for value in attrs.get("src", "").split()]
            strongs = re.findall(r'strong:(G\d+)', attrs.get("lemma", ""))
            forms = re.findall(r'lemma\.TR:([^\s]+)', attrs.get("lemma", ""))
            morphs = re.findall(r'robinson:([^\s]+)', attrs.get("morph", ""))
            if not (len(source_indices) == len(strongs) == len(forms)):
                raise ValueError(f"{osis_book}.{chapter}.{verse}: onvolledige OSIS-tokenlaag")
            for offset, source_index in enumerate(source_indices):
                indexed[source_index - 1] = {
                    "woord": html.unescape(forms[offset]),
                    "lemma_strong": strongs[offset],
                    "morfologie": morphs[offset] if offset < len(morphs) else "",
                }
        verses[verse] = indexed
    if not verses:
        raise ValueError(f"Geen OSIS-verzen gevonden voor {osis_book}.{chapter}")
    return verses


def load_tr_chapter(
    utr_path: Path,
    osis_path: Path,
    *,
    chapter: int,
    osis_book: str,
) -> dict[int, list[dict]]:
    expected_utr = UTR_SHA256.get(utr_path.name.upper())
    if not expected_utr or sha256(utr_path) != expected_utr:
        raise ValueError(f"De UTR-bron {utr_path.name} is niet gepind of heeft een afwijkende SHA-256")
    utr = parse_tr_utr(utr_path)
    osis = parse_osis_chapter(osis_path, osis_book, chapter)
    result = {}
    for verse, indexed in osis.items():
        source = utr[(chapter, verse)]
        if set(indexed) != set(range(len(source))):
            raise ValueError(f"{osis_book}.{chapter}.{verse}: OSIS- en UTR-tokenposities verschillen")
        tokens = []
        for index, token in enumerate(source):
            exact = indexed[index]
            display_strong = FORM_STRONG_OVERRIDES.get(
                (normal(token["lemma_strong"]), token["morphology"]),
                token["display_strong"],
            )
            if normal(token["lemma_strong"]) == "G4183" and token["morphology"].endswith("-C"):
                display_strong = "G4119"
            if normal(exact["lemma_strong"]) not in {
                normal(token["lemma_strong"]), normal(display_strong)
            }:
                raise ValueError(
                    f"{osis_book}.{chapter}.{verse} token {index + 1}: "
                    f"OSIS {exact['lemma_strong']} != UTR {token['lemma_strong']}"
                )
            enriched = dict(token)
            enriched["woord"] = exact["woord"]
            enriched["display_strong"] = display_strong
            enriched["source_index"] = index
            tokens.append(enriched)
        result[verse] = tokens
    return result
