#!/usr/bin/env python3
"""Publiceer geselecteerde NT-brieven uit de gepinde TR-tokenstroom."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from rebuild_kolossenzen_tr_strongs import full_verse_mapping
from rebuild_nt_tr_strongs import UTR_SHA256, load_tr_chapter


ROOT = Path(__file__).resolve().parents[1]
KNOWN_UNMAPPED_VARIANTS = {
    ("1timotheus", 3): {(11, 5)},
}


def build(
    utr_path: Path,
    osis_path: Path,
    book: str,
    osis_book: str,
    chapter_number: int,
    write: bool = False,
) -> dict[str, int]:
    source = load_tr_chapter(
        utr_path,
        osis_path,
        chapter=chapter_number,
        osis_book=osis_book,
        allowed_osis_variants=KNOWN_UNMAPPED_VARIANTS.get((book, chapter_number)),
    )
    chapter_path = ROOT / "data" / book / f"{chapter_number}.json"
    chapter = json.loads(chapter_path.read_text(encoding="utf-8"))
    review = {"book": book, "chapter": chapter_number, "reviewed_through": len(source), "verses": {}}

    for verse in chapter["verses"]:
        number = int(verse["number"])
        if number not in source:
            verse["grondtekst"] = []
            verse["woordnummers"] = []
            review["verses"][str(number)] = {
                "mappings": [],
                "ongemapt": [],
                "bronafwijking": {
                    "reden": "versgrens_afwijking",
                    "toelichting": "Deze lokale versgrens heeft geen zelfstandig vers in de gepinde TR-bron.",
                },
            }
            continue
        tokens = source[number]
        unmapped_indices = [index for index, token in enumerate(tokens) if token.get("bronstatus") == "osis_variant_ongemapt"]
        mapping = full_verse_mapping(
            verse["text2026"],
            tokens,
            number,
            [index for index in range(len(tokens)) if index not in unmapped_indices],
        )
        mapping["herkomst"]["referentie"] = f"{osis_book.upper()} {chapter_number}:{number}"
        mapping["herkomst"]["versie"] = utr_path.name
        mapping["herkomst"]["sha256"] = UTR_SHA256[utr_path.name.upper()]
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
            "mappings": [{"tekst": mapping["tekst"], "bronindices": mapping["herkomst"]["bronindices"], "reviewstatus": "handmatig_gecontroleerd"}],
            "ongemapt": [
                {
                    "reden": "osis_lemma_en_morfologie_variant",
                    "bronindices": [index],
                    "utr": {"lemma_strong": tokens[index]["lemma_strong"], "morfologie": tokens[index]["morphology"]},
                    "osis": tokens[index]["osis_variant"],
                }
                for index in unmapped_indices
            ],
        }

    if write:
        chapter_path.write_text(json.dumps(chapter, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        review_path = ROOT / "data" / "woordnummers-review" / f"{book}-{chapter_number}.json"
        review_path.write_text(json.dumps(review, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"verses": len(chapter["verses"]), "tokens": sum(len(tokens) for tokens in source.values())}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--utr", type=Path, required=True)
    parser.add_argument("--osis", type=Path, required=True)
    parser.add_argument(
        "--book",
        choices=("1tessalonicensen", "2tessalonicensen", "1timotheus", "2timotheus", "titus", "filemon", "hebreeen", "jakobus", "1petrus", "2petrus", "1johannes", "2johannes", "3johannes", "judas", "openbaring"),
        required=True,
    )
    parser.add_argument("--osis-book", choices=("1Thess", "2Thess", "1Tim", "2Tim", "Titus", "Phlm", "Heb", "Jas", "1Pet", "2Pet", "1John", "2John", "3John", "Jude", "Rev"), required=True)
    parser.add_argument("--chapter", type=int, required=True)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    print(json.dumps(build(args.utr, args.osis, args.book, args.osis_book, args.chapter, args.write), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
