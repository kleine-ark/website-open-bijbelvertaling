#!/usr/bin/env python3
"""Publiceer Kolossenzen uit de gepinde Textus-Receptus-tokenstroom."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from rebuild_nt_tr_strongs import load_tr_chapter


ROOT = Path(__file__).resolve().parents[1]
SOURCE_ID = "robinson-scrivener-tr"
SOURCE_VERSION = "COL.UTR"
SOURCE_SHA256 = "43E74492989EBADA1B4ECEB1FF7CC7C80F1923E0702A021549B90EF24E348153"


def full_verse_mapping(
    anchor: str,
    tokens: list[dict],
    verse: int,
    token_indices: list[int] | None = None,
) -> dict:
    """Bewaar ieder bronwoord in de vaste bronvolgorde onder één versanker."""
    indices = list(range(len(tokens))) if token_indices is None else token_indices
    chosen = [tokens[index] for index in indices]
    record = {
        "tekst": anchor,
        "voorkomen": 1,
        "strongs": [token["display_strong"] for token in chosen],
        "lemma_strongs": [token["lemma_strong"] for token in chosen],
        "morfologie": [token["morphology"] for token in chosen],
        "bronwoorden": [token["woord"] for token in chosen],
        "transliteraties": [str(token.get("transliteratie") or "") for token in chosen],
        "glossen": [str(token.get("gloss") or token.get("betekenis") or "") for token in chosen],
        "status": "vertaald",
        "confidence": 1.0,
        "reviewstatus": "handmatig_gecontroleerd",
        "herkomst": {
            "dataset": SOURCE_ID,
            "versie": SOURCE_VERSION,
            "sha256": SOURCE_SHA256,
            "referentie": f"COL {verse}",
            "bronindices": indices,
        },
    }
    tvm = [token.get("tvm") for token in chosen]
    if any(tvm):
        record["tvm"] = tvm
    return record


def build(utr_path: Path, osis_path: Path, chapter_number: int, write: bool = False) -> dict[str, int]:
    source = load_tr_chapter(utr_path, osis_path, chapter=chapter_number, osis_book="Col")
    chapter_path = ROOT / "data" / "kolossenzen" / f"{chapter_number}.json"
    chapter = json.loads(chapter_path.read_text(encoding="utf-8"))
    review = {
        "book": "kolossenzen",
        "chapter": chapter_number,
        "reviewed_through": len(source),
        "verses": {},
    }

    for verse in chapter["verses"]:
        number = int(verse["number"])
        tokens = source[number]
        mapping = full_verse_mapping(verse["text2026"], tokens, number)
        verse["grondtekst"] = [
            {
                "woord": token["woord"],
                "strongs": token["display_strong"],
                "lemma_strongs": token["lemma_strong"],
                "morfologie": token["morphology"],
                **({"bronstatus": token["bronstatus"]} if token.get("bronstatus") else {}),
            }
            for token in tokens
        ]
        verse["woordnummers"] = [mapping]
        review["verses"][str(number)] = {
            "mappings": [
                {
                    "tekst": mapping["tekst"],
                    "bronindices": mapping["herkomst"]["bronindices"],
                    "reviewstatus": "handmatig_gecontroleerd",
                }
            ],
            "ongemapt": [],
        }

    if write:
        chapter_path.write_text(json.dumps(chapter, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        review_path = ROOT / "data" / "woordnummers-review" / f"kolossenzen-{chapter_number}.json"
        review_path.write_text(json.dumps(review, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"verses": len(chapter["verses"]), "tokens": sum(len(tokens) for tokens in source.values())}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--utr", type=Path, required=True)
    parser.add_argument("--osis", type=Path, required=True)
    parser.add_argument("--chapter", type=int, required=True)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    print(json.dumps(build(args.utr, args.osis, args.chapter, args.write), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
