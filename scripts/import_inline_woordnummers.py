#!/usr/bin/env python3
"""Importeer gereviewde inline woordnummerkoppelingen uit een gepinde USJ-bron."""

import argparse
import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STRONG_RE = re.compile(r"[HG]\d+[A-Za-z]?")
REVIEWED = "handmatig_gecontroleerd"


# De Robinson/Scrivener-bron bewaart bij werkwoorden het lemma-Strongnummer.
# Oudere Strong-studiebijbels tonen voor enkele veelgebruikte vormen een eigen
# vormnummer.  Die presentatielaag blijft bewust gescheiden van het lemma.
TRADITIONAL_FORM_STRONGS = {
    ("G1510", "V-IAI-3S"): "G2258",  # ἦν — was
}

# De klassieke KJV/Strong-presentatielaag gebruikt voor ἦν bij G2258 de
# samengevatte werkwoordscode G5713. De UTR-bron bewaart daarnaast de
# expliciet actieve Robinson-analyse als G5707 / V-IAI-3S.
TRADITIONAL_TVM_OVERRIDES = {
    ("G2258", "V-IAI-3S"): "G5713",
}


def _strongs(value):
    if isinstance(value, list):
        values = value
    else:
        values = STRONG_RE.findall(str(value or ""))
    return list(dict.fromkeys(str(item) for item in values if STRONG_RE.fullmatch(str(item))))


def parse_usj(path):
    """Lees woordniveau-Strongdata uit een USJ 3.x-bestand."""
    document = json.loads(Path(path).read_text(encoding="utf-8"))
    if document.get("type") != "USJ":
        raise ValueError(f"Geen USJ-document: {path}")

    verses = {}
    chapter = None
    verse = None

    def visit(items):
        nonlocal chapter, verse
        for item in items or []:
            if not isinstance(item, dict):
                continue
            kind = item.get("type")
            if kind == "chapter":
                chapter = int(item["number"])
                verse = None
            elif kind == "verse":
                if chapter is None:
                    raise ValueError("Vers vóór hoofdstuk in USJ")
                verse = int(str(item["number"]).split("-")[0])
                verses.setdefault((chapter, verse), [])
            elif kind == "char" and item.get("marker") == "w" and verse is not None:
                numbers = _strongs(item.get("strong"))
                if numbers:
                    text = "".join(part for part in item.get("content", []) if isinstance(part, str))
                    verses[(chapter, verse)].append({"text": text, "strongs": numbers})
            if isinstance(item.get("content"), list):
                visit(item["content"])

    visit(document.get("content", []))
    return verses


def parse_tr_utr(path):
    """Lees Robinsons publieke TR-formaat met lemma en morfologie apart."""
    raw = Path(path).read_text(encoding="utf-8")
    records = {}
    current = None
    for line in raw.splitlines():
        match = re.match(r"^(\d+):(\d+)\s+(.*)$", line)
        if match:
            current = (int(match.group(1)), int(match.group(2)))
            records[current] = match.group(3)
        elif current is not None:
            records[current] += " " + line.strip()

    verses = {}
    token_pattern = re.compile(r"(\S+)\s+(\d+)(?:\s+(\d{4}))?\s+\{([^}]+)\}")
    for reference, text in records.items():
        # Robinson noteert enkele spellingvarianten als
        # ``| vorm_a | vorm_b | 3478 {N-PRI}``. Voor de tokenlaag kiezen we
        # de eerste vermelde TR-vorm; de varianten blijven in de bron zelf.
        text = re.sub(r"\|\s*([^|\s]+)\s*\|\s*[^|\s]+\s*\|\s*(\d+)", r"\1 \2", text)
        tokens = []
        for match in token_pattern.finditer(text):
            # Een beperkt aantal UTR-regels bevat na een woord twee mogelijke
            # morfologiecodes zonder herhaalde woordvorm. Zo'n numerieke of
            # accolade-voorloper is metadata en geen zelfstandig Grieks token.
            if match.group(1).isdigit() or "{" in match.group(1) or "}" in match.group(1):
                continue
            lemma = f"G{int(match.group(2))}"
            morphology = match.group(4)
            display_strong = TRADITIONAL_FORM_STRONGS.get(
                (lemma, morphology), lemma
            )
            raw_tvm = f"G{match.group(3)}" if match.group(3) else None
            tokens.append(
                {
                    "text": match.group(1),
                    "lemma_strong": lemma,
                    "display_strong": display_strong,
                    "morphology": morphology,
                    "tvm": TRADITIONAL_TVM_OVERRIDES.get(
                        (display_strong, morphology), raw_tvm
                    ),
                }
            )
        verses[reference] = tokens
    return verses


def parse_tagnt_tr(path, book="Jhn", chapter=None):
    """Lees alleen de Scrivener/TR-woorden uit STEPBible TAGNT."""
    pattern = re.compile(rf"^{re.escape(book)}\.(\d+)\.(\d+)#(\d+)=")
    verses = {}
    for line in Path(path).read_text(encoding="utf-8-sig").splitlines():
        columns = line.split("\t")
        match = pattern.match(columns[0]) if columns else None
        if not match or len(columns) < 13:
            continue
        current_chapter, verse, sequence = map(int, match.groups())
        if chapter is not None and current_chapter != int(chapter):
            continue
        if "TR" not in columns[5].split("+"):
            continue
        tagged = re.match(r"(G\d+[A-Za-z]?)=([^\s]+)", columns[3])
        if not tagged:
            continue
        lemma, morphology = tagged.groups()
        alternatives = _strongs(columns[12])
        display = alternatives[0] if alternatives else lemma
        greek = columns[1].split(" (", 1)[0].strip().rstrip(",.;·")
        verses.setdefault((current_chapter, verse), []).append({
            "text": greek,
            "lemma_strong": lemma,
            "display_strong": display,
            "morphology": morphology,
            "sequence": sequence,
        })
    for tokens in verses.values():
        tokens.sort(key=lambda item: item["sequence"])
    return verses


def build_inline_mapping(
    review, external_tokens, local_tokens, source, reference, lemma_afwijking=None
):
    if review.get("reviewstatus") != REVIEWED:
        raise ValueError(f"Ongeldige reviewstatus voor {reference}: {review.get('reviewstatus')!r}")
    confidence = review.get("confidence")
    if not isinstance(confidence, (int, float)) or not 0 <= confidence <= 1:
        raise ValueError(f"Ongeldige confidence voor {reference}")

    source_indices = review.get("bronindices") or []
    ground_indices = review.get("grondindices", source_indices)
    try:
        external = [external_tokens[index] for index in source_indices]
        local = [local_tokens[index] for index in ground_indices]
    except (IndexError, TypeError):
        raise ValueError(f"Ongeldige bronvolgorde voor {reference}") from None

    external_numbers = [number for token in external for number in _strongs(token.get("strongs"))]
    local_numbers = [number for token in local for number in _strongs(token.get("strongs"))]
    # Een vers kan meer dan één, inhoudelijk onafhankelijke afwijking tussen
    # de uitlijngids en de lokale grondtekst bevatten. Elke afwijking blijft
    # daarom atomair in het reviewbestand; de importer accepteert uitsluitend
    # de record die precies bij deze mapping hoort.
    differences = lemma_afwijking if isinstance(lemma_afwijking, list) else [lemma_afwijking]
    documented_difference = any(
        isinstance(difference, dict)
        and difference.get("reden") == "lemma_afwijking"
        and difference.get("bronindices") == list(source_indices)
        and difference.get("grondindices") == list(ground_indices)
        and difference.get("bron_strongs") == external_numbers
        and difference.get("grondtekst_strongs") == local_numbers
        for difference in differences
    )
    if not external_numbers or (
        external_numbers != local_numbers and not documented_difference
    ):
        raise ValueError(
            f"Afwijkende bronvolgorde voor {reference}: extern {external_numbers}, lokaal {local_numbers}"
        )

    mapping = {
        "tekst": str(review["tekst"]),
        "voorkomen": int(review.get("voorkomen", 1)),
        # De lokale WLC/OSHB-tokenlaag is leidend. Een expliciet vastgelegde
        # gidsafwijking blijft zichtbaar naast, maar vervangt nooit dit lemma.
        "strongs": local_numbers,
        "bronwoorden": [str(token.get("woord") or "") for token in local],
        "transliteraties": [
            str(token.get("transliteratie") or token.get("translit") or "") for token in local
        ],
        "glossen": [str(token.get("gloss") or token.get("betekenis") or "") for token in local],
        "confidence": float(confidence),
        "reviewstatus": REVIEWED,
        "herkomst": {
            "dataset": source["id"],
            "versie": source["version"],
            "sha256": source["sha256"],
            "referentie": reference,
            "bronindices": list(source_indices),
        },
    }
    if external_numbers != local_numbers:
        mapping["gids_strongs"] = external_numbers
    for key in ("anker", "plaats", "status", "toelichting"):
        if key in review:
            mapping[key] = review[key]
    return mapping


def _anchor_key(mapping):
    return (str(mapping.get("tekst") or "").casefold(), int(mapping.get("voorkomen", 1)))


def merge_reviewed_mappings(verse, proposed):
    """Voeg alleen nieuwe ankers toe; bestaande mappings zijn autoritatief."""
    existing = verse.setdefault("woordnummers", [])
    existing_keys = {_anchor_key(mapping) for mapping in existing if isinstance(mapping, dict)}
    added = 0
    preserved = 0
    text = str(verse.get("text2026") or verse.get("textHerzien") or "")
    for mapping in proposed:
        key = _anchor_key(mapping)
        if key in existing_keys:
            preserved += 1
            continue
        if mapping.get("reviewstatus") != REVIEWED:
            continue
        if text.casefold().count(key[0]) < key[1]:
            raise ValueError(f"Anker {mapping.get('tekst')!r}#{key[1]} ontbreekt in Nederlandse tekst")
        existing.append(mapping)
        existing_keys.add(key)
        added += 1
    return added, preserved


def replace_reviewed_mappings(verse, proposed, provenance):
    """Vervang uitsluitend bronrecords van één expliciet gereviewd vers.

    Een reviewbestand kan deze route alleen per vers inschakelen. Daarmee
    blijven redactionele ankers en records van andere bronverzen onaangeraakt.
    """
    existing = verse.setdefault("woordnummers", [])
    keys = ("dataset", "versie", "sha256", "referentie")
    kept = []
    replaced = 0
    for mapping in existing:
        origin = mapping.get("herkomst", {}) if isinstance(mapping, dict) else {}
        if all(origin.get(key) == provenance.get(key) for key in keys):
            replaced += 1
        else:
            kept.append(mapping)
    verse["woordnummers"] = kept + proposed
    return replaced


def _sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def apply_review_file(review_path, source_dir, data_dir=None, write=False, verse_numbers=None):
    """Bouw en merge alle gereviewde mappings uit één reproduceerbaar reviewbestand."""
    review = json.loads(Path(review_path).read_text(encoding="utf-8"))
    source = review["source"]
    source_dir = Path(source_dir)
    data_dir = Path(data_dir or ROOT / "data")
    report = {
        "mode": "write" if write else "dry-run",
        "added": 0,
        "preserved": 0,
        "replaced": 0,
        "verses": 0,
    }

    for book in review.get("books", []):
        source_path = source_dir / book["source_file"]
        expected_hash = str(book.get("source_file_sha256") or "").upper()
        if expected_hash and _sha256(source_path) != expected_hash:
            raise ValueError(f"SHA-256 wijkt af voor {source_path.name}")
        external_verses = parse_usj(source_path)
        chapter_path = data_dir / book["repo_book"] / f"{book['chapter']}.json"
        original = chapter_path.read_text(encoding="utf-8")
        chapter = json.loads(original)
        by_number = {int(verse["number"]): verse for verse in chapter.get("verses", [])}

        chapter_changed = False
        for verse_review in book.get("verses", []):
            number = int(verse_review["verse"])
            if verse_numbers is not None and number not in verse_numbers:
                continue
            source_number = int(verse_review.get("source_verse", number))
            # Optioneel: het gidsvers kan in een ander hoofdstuk liggen dan het
            # lokale vers, bijvoorbeeld 1 Samuel 24:1 dat bij gids 23:29 hoort.
            source_chapter = int(verse_review.get("source_chapter", book["chapter"]))
            verse = by_number[number]
            reference = f"{book['code']} {source_chapter}:{source_number}"
            external = external_verses.get((source_chapter, source_number), [])
            local = verse.get("grondtekst") or []
            proposed = [
                build_inline_mapping(
                    item,
                    external,
                    local,
                    source,
                    reference,
                    lemma_afwijking=verse_review.get(
                        "bronafwijkingen", verse_review.get("bronafwijking")
                    ),
                )
                for item in verse_review.get("mappings", [])
            ]
            if verse_review.get("vervang_bronrecords"):
                if not proposed:
                    raise ValueError(f"Geen vervangende mappings voor {reference}")
                provenance = {
                    "dataset": source["id"],
                    "versie": source["version"],
                    "sha256": source["sha256"],
                    "referentie": reference,
                }
                replaced = replace_reviewed_mappings(verse, proposed, provenance)
                added, preserved = len(proposed), 0
                report["replaced"] += replaced
                chapter_changed = chapter_changed or bool(replaced or proposed)
            else:
                added, preserved = merge_reviewed_mappings(verse, proposed)
                chapter_changed = chapter_changed or bool(added)
            report["added"] += added
            report["preserved"] += preserved
            report["verses"] += 1

        if write and chapter_changed:
            rendered = json.dumps(chapter, ensure_ascii=False, indent=2) + "\n"
            chapter_path.write_text(rendered, encoding="utf-8")
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--review", type=Path, required=True)
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data")
    parser.add_argument(
        "--verses",
        type=int,
        nargs="+",
        help="beperk de import tot deze versnummers binnen het reviewhoofdstuk",
    )
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    report = apply_review_file(
        args.review,
        args.source_dir,
        args.data_dir,
        args.write,
        verse_numbers=set(args.verses) if args.verses else None,
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
