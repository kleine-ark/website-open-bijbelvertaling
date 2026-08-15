#!/usr/bin/env python3
"""Bouw Johannes 1 opnieuw op vanuit Robinsons Scrivener-TR.

De Nederlandse tekst blijft onaangeroerd. Ieder TR-token wordt precies eenmaal
inline gepubliceerd; niet afzonderlijk vertaalde tokens krijgen een zelfstandig
Strongknopje bij het dichtstbijzijnde gecontroleerde Nederlandse anker.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import sys
from collections import defaultdict
from difflib import SequenceMatcher
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from import_inline_woordnummers import parse_tr_utr  # noqa: E402


SOURCE_ID = "robinson-scrivener-tr"
SOURCE_VERSION = "7fd4d02c3e5adebd379ebfbc824040820dde10fc"
SOURCE_SHA256 = "77FBB830AE3E11B79F7F47A8E68A119DC77F0722EBCC99BB00111702797BFFE5"
WORDFORM_SOURCE_ID = "crosswire-kjv-tr-wordforms"
WORDFORM_SOURCE_VERSION = "d490be7e34762deb2c76cb2c1306d4808e27890d"
WORDFORM_SOURCE_SHA256 = "2BC5C343DA30125AF8D4D1E27F8444019030B6350D16E69EF8645BF9E17D5963"


# Lokale verzen 38 en 39 vormen samen Johannes 1:38 in de TR. Vanaf lokaal
# vers 40 loopt het bronvers daarom één nummer achter.
def correspondence(local_verse: int):
    if local_verse < 38:
        return local_verse, None
    if local_verse == 38:
        return 38, range(0, 10)
    if local_verse == 39:
        return 38, range(10, 23)
    return local_verse - 1, None


TAIL_SPECS = {
    39: [("Wat", 0, 0), ("zoekt u", 0, 1), ("En zij", 0, (2, 3)),
         ("zeiden tot Hem", 0, (4, 5)), ("Rabbi", 0, 6),
         ("dat is te zeggen, overgezet zijnde, Meester", 0, (7, 10)),
         ("waar", 0, 11), ("woont U", 0, 12)],
    40: [("Hij zei tot hen", 0, (0, 1)), ("Kom en ziet", 0, (2, 4)),
         ("Zij kwamen en zagen", 0, (5, 7)), ("waar Hij woonde", 0, (8, 9)),
         ("en bleven die dag bij Hem", 0, (10, 16)),
         ("En het was ongeveer het tiende uur", 0, (17, 21))],
    41: [("Andreas", 0, (0, 1)), ("de broer van Simon Petrus", 0, (2, 5)),
         ("één van de twee", 0, (6, 10)),
         ("die het van Johannes gehoord hadden", 0, (11, 13)),
         ("en Hem gevolgd waren", 0, (14, 16))],
    42: [("Deze vond eerst zijn broer Simon", 0, (0, 7)),
         ("en zei tot hem", 0, (8, 10)),
         ("Wij hebben gevonden de Messias", 0, (11, 13)),
         ("dat is, overgezet zijnde, de Christus", 0, (14, 18))],
    43: [("En hij leidde hem tot Jezus", 0, (0, 5)),
         ("En Jezus, hem aanziende, zei", 0, (6, 11)),
         ("U bent Simon, de zoon van Jonas", 0, (12, 17)),
         ("u zult genoemd worden Cefas", 0, (18, 20)),
         ("dat overgezet wordt Petrus", 0, (21, 23))],
    44: [("Op de andere dag wilde Jezus heengaan naar Galilea", 0, (0, 8)),
         ("en vond Filippus, en zei tot hem", 0, (9, 14)),
         ("Volg Mij", 0, (15, 16))],
    45: [("Filippus nu was", 0, (0, 3)), ("van Bethsaïda", 0, (4, 5)),
         ("uit de stad", 0, (6, 8)), ("van Andreas en Petrus", 0, (9, 11))],
    46: [("Filippus vond Nathanaël en zei tot hem", 0, (0, 6)),
         ("van Wie Mozes in de wet geschreven heeft, en de profeten", 0, (7, 15)),
         ("Wij hebben Die gevonden", 0, 16),
         ("namelijk Jezus, de zoon van Jozef, van Nazareth", 0, (17, 24))],
    47: [("En Nathanaël zei tot hem", 0, (0, 3)),
         ("Kan uit Nazareth iets goeds zijn", 0, (4, 9)),
         ("Filippus zei van hem", 0, (10, 12)), ("Kom en zie", 0, (13, 15))],
    48: [("Jezus zag Nathanaël tot Zich komen", 0, (0, 7)),
         ("en zei van hem", 0, (8, 11)),
         ("Zie, werkelijk een Israëliet", 0, (12, 14)),
         ("in wie geen bedrog is", 0, (15, 19))],
    49: [("Nathanaël zei tot Hem: Vanwaar kent U mij", 0, (0, 5)),
         ("Jezus antwoordde en zei tot hem", 0, (6, 11)),
         ("Voordat u Filippus riep", 0, (12, 16)),
         ("daar u onder de vijgeboom was, zag Ik u", 0, (17, 22))],
    50: [("Nathanaël antwoordde en zei tot Hem", 0, (0, 4)), ("Rabbi", 0, 5),
         ("U bent de Zoon van God", 0, (6, 11)),
         ("U bent de Koning van Israël", 0, (12, 17))],
    51: [("Jezus antwoordde en zei tot hem", 0, (0, 4)),
         ("Omdat Ik u gezegd heb: Ik zag u onder de vijgeboom", 0, (5, 12)),
         ("zo gelooft u", 0, 13),
         ("u zult grotere dingen zien dan deze", 0, (14, 16))],
    52: [("En Hij zei tot hem", 0, (0, 2)),
         ("Voorwaar, voorwaar zeg Ik u", 0, (3, 6)),
         ("Van nu aan zult u de hemel zien geopend", 0, (7, 12)),
         ("en de engelen van God", 0, (13, 17)), ("opklimmende", 0, 18),
         ("en nederdalende", 0, (19, 20)),
         ("op de Zoon des mensen", 0, (21, 25))],
}

# Handmatige beoordeling van tokens die niet door de oudere woordgroepreview
# waren geraakt. De sleutel gebruikt de nulgebaseerde TR-bronpositie. Alleen
# werkelijk niet afzonderlijk weergegeven woorden houden een lege tekst.
ORPHAN_REVIEWS = {
    (12, 5): ("", "macht", "voor", "niet_afzonderlijk_weergegeven"),
    (14, 0): ("En", None, None, "vertaald"),
    (14, 5): ("en heeft onder ons gewoond", None, None, "vertaald"),
    (14, 9): ("en wij hebben", None, None, "vertaald"),
    (14, 21): ("en waarheid", None, None, "vertaald"),
    (15, 4): ("en heeft geroepen", None, None, "vertaald"),
    (16, 0): ("En uit Zijn volheid", None, None, "vertaald"),
    (16, 8): ("ook genade", None, None, "vertaald"),
    (17, 0): ("Want de wet", None, None, "vertaald"),
    (17, 8): ("en de waarheid", None, None, "vertaald"),
    (18, 5): ("eniggeboren Zoon", None, None, "vertaald"),
    (18, 6): ("eniggeboren Zoon", None, None, "vertaald"),
    (18, 15): ("verklaard", None, None, "vertaald"),
    (19, 0): ("En dit", None, None, "vertaald"),
    (19, 3): ("de getuigenis", None, None, "vertaald"),
    (19, 5): ("van Johannes", None, None, "vertaald"),
    (19, 9): ("de Joden", None, None, "vertaald"),
    (19, 10): ("de Joden", None, None, "vertaald"),
    (20, 0): ("En hij beleed", None, None, "vertaald"),
    (20, 2): ("en ontkende", None, None, "vertaald"),
    (20, 3): ("niet", None, None, "vertaald"),
    (20, 5): ("en beleed", None, None, "vertaald"),
    (20, 7): ("", "Ik ben", "voor", "niet_afzonderlijk_weergegeven"),
    (21, 0): ("En zij vraagden", None, None, "vertaald"),
    (21, 8): ("En hij zei", None, None, "vertaald"),
    (21, 16): ("En hij antwoordde", None, None, "vertaald"),
    (24, 0): ("En de afgezondenen", None, None, "vertaald"),
    (24, 6): ("de Farizeeën", None, None, "vertaald"),
    (25, 0): ("En zij vraagden", None, None, "vertaald"),
    (25, 3): ("en spraken tot hem", None, None, "vertaald"),
    (26, 16): ("kent", None, None, "vertaald"),
    (27, 0): ("Deze", None, None, "vertaald"),
    (27, 16): ("zou ontbinden", None, None, "vertaald"),
    (27, 17): ("Zijn schoenriem", None, None, "vertaald"),
    (27, 18): ("Zijn schoenriem", None, None, "vertaald"),
    (27, 19): ("schoenriem", None, None, "vertaald"),
    (27, 20): ("Zijn schoenriem", None, None, "vertaald"),
    (27, 21): ("schoenriem", None, None, "vertaald"),
    (28, 1): ("in Bethabara", None, None, "vertaald"),
    (28, 2): ("Bethabara", None, None, "vertaald"),
    (28, 9): ("Johannes", None, None, "vertaald"),
    (29, 3): ("", "Jezus", "voor", "niet_afzonderlijk_weergegeven"),
    (29, 8): ("tot zich komende", None, None, "vertaald"),
    (29, 10): ("en zei", None, None, "vertaald"),
    (29, 21): ("van de wereld", None, None, "vertaald"),
    (29, 22): ("van de wereld", None, None, "vertaald"),
    (31, 16): ("dopende", None, None, "vertaald"),
    (32, 0): ("En Johannes", None, None, "vertaald"),
    (32, 4): ("Ik heb", None, None, "vertaald"),
    (32, 13): ("en bleef", None, None, "vertaald"),
    (33, 16): ("zult zien", None, None, "vertaald"),
    (33, 17): ("zult zien", None, None, "vertaald"),
    (33, 21): ("en op Hem blijven", None, None, "vertaald"),
    (34, 2): ("en heb getuigd", None, None, "vertaald"),
    (35, 4): ("", "Johannes", "voor", "niet_afzonderlijk_weergegeven"),
    (35, 6): ("en twee", None, None, "vertaald"),
    (36, 0): ("En ziende", None, None, "vertaald"),
    (36, 6): ("Zie", None, None, "vertaald"),
    (37, 0): ("En die twee", None, None, "vertaald"),
    (37, 7): ("en zij volgden", None, None, "vertaald"),
    (38, 1): ("En Jezus", None, None, "vertaald"),
    (38, 4): ("en ziende", None, None, "vertaald"),
}


def sha256(path: Path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def indices(value):
    if isinstance(value, int):
        return [value]
    start, end = value
    return list(range(start, end + 1))


def normal(number):
    digits = "".join(ch for ch in str(number) if ch.isdigit())
    return f"G{int(digits)}" if digits else ""


def align(old_words, source_tokens):
    old = [normal(word.get("lemma_strongs") or word.get("strongs")) for word in old_words]
    source = [normal(token.get("lemma_strong")) for token in source_tokens]
    result = {}
    matcher = SequenceMatcher(a=old, b=source, autojunk=False)
    for block in matcher.get_matching_blocks():
        for offset in range(block.size):
            result[block.a + offset] = block.b + offset
    return result


def parse_osis_tr_wordforms(path: Path):
    """Lees de exacte TR-woordvorm per Griekse bronpositie uit CrossWire OSIS."""
    if sha256(path) != WORDFORM_SOURCE_SHA256:
        raise ValueError("De gepinde CrossWire-OSIS-bron heeft een afwijkende SHA-256")
    xml = path.read_text(encoding="utf-8")
    chapters = {}
    for verse in range(1, 52):
        start = f'<verse osisID="John.1.{verse}" sID="John.1.{verse}"/>'
        end = f'<verse eID="John.1.{verse}"/>'
        body = xml.split(start, 1)[1].split(end, 1)[0]
        indexed = {}
        for match in re.finditer(r'<w\s+([^>]*?)(?:/>|>(.*?)</w>)', body, re.DOTALL):
            attrs = dict(re.findall(r'(\w+)="([^"]*)"', match.group(1)))
            source_indices = [int(value) for value in attrs.get("src", "").split()]
            strongs = re.findall(r'strong:(G\d+)', attrs.get("lemma", ""))
            forms = re.findall(r'lemma\.TR:([^\s]+)', attrs.get("lemma", ""))
            morphs = re.findall(r'robinson:([^\s]+)', attrs.get("morph", ""))
            if not (len(source_indices) == len(strongs) == len(forms)):
                raise ValueError(f"John.1.{verse}: onvolledige OSIS-tokenlaag bij {attrs!r}")
            for offset, source_index in enumerate(source_indices):
                indexed[source_index - 1] = {
                    "woord": html.unescape(forms[offset]),
                    "lemma_strong": strongs[offset],
                    "morfologie": morphs[offset] if offset < len(morphs) else "",
                }
        chapters[verse] = indexed
    return chapters


def source_word(token, exact_wordform, old_word=None):
    word = dict(old_word or {})
    word["woord"] = exact_wordform["woord"]
    word["strongs"] = token["display_strong"]
    word["lemma_strongs"] = token["lemma_strong"]
    word["morfologie"] = token["morphology"]
    return word


def mapping(anchor, occurrence, token_ids, tokens, source_verse, status="vertaald"):
    chosen = [tokens[index] for index in token_ids]
    record = {
        "tekst": anchor,
        "voorkomen": occurrence + 1,
        "strongs": [token["display_strong"] for token in chosen],
        "lemma_strongs": [token["lemma_strong"] for token in chosen],
        "morfologie": [token["morphology"] for token in chosen],
        "bronwoorden": [token["woord"] for token in chosen],
        "transliteraties": [str(token.get("transliteratie") or "") for token in chosen],
        "glossen": [str(token.get("gloss") or token.get("betekenis") or "") for token in chosen],
        "status": status,
        "confidence": 1.0,
        "reviewstatus": "handmatig_gecontroleerd",
        "herkomst": {
            "dataset": SOURCE_ID,
            "versie": SOURCE_VERSION,
            "sha256": SOURCE_SHA256,
            "referentie": f"JHN 1:{source_verse}",
            "bronindices": [tokens[index]["source_index"] for index in token_ids],
        },
    }
    return record


def build(utr_path: Path, osis_path: Path, write=False):
    if sha256(utr_path) != SOURCE_SHA256:
        raise ValueError("De gepinde JOH.UTR-bron heeft een afwijkende SHA-256")

    chapter_path = ROOT / "data" / "johannes" / "1.json"
    review_path = ROOT / "data" / "woordnummers-pilot-johannes.json"
    chapter = json.loads(chapter_path.read_text(encoding="utf-8"))
    old_ground = {int(v["number"]): list(v.get("grondtekst") or []) for v in chapter["verses"]}
    pilot = json.loads(review_path.read_text(encoding="utf-8"))["books"][0]["verses"]
    pilot_by_verse = {int(v["verse"]): v for v in pilot}
    source = parse_tr_utr(utr_path)
    exact_wordforms = parse_osis_tr_wordforms(osis_path)

    # Bestaande Griekse woorden worden alleen als presentatielaag hergebruikt;
    # Strong, lemma en morfologie komen altijd uit de gepinde TR-bron.
    greek_by_source = {}
    for source_verse in range(1, 52):
        old_local = source_verse if source_verse <= 38 else source_verse + 1
        words = old_ground.get(old_local, [])
        if source_verse == 38:
            words = old_ground[38]
        source_tokens = source[(1, source_verse)]
        old_to_source = align(words, source_tokens)
        reverse = {source_index: old_index for old_index, source_index in old_to_source.items()}
        if set(exact_wordforms[source_verse]) != set(range(len(source_tokens))):
            raise ValueError(f"Johannes 1:{source_verse}: OSIS- en UTR-tokenposities verschillen")
        for index, token in enumerate(source_tokens):
            exact = exact_wordforms[source_verse][index]
            if normal(exact["lemma_strong"]) != normal(token["lemma_strong"]):
                raise ValueError(
                    f"Johannes 1:{source_verse} token {index + 1}: "
                    f"OSIS {exact['lemma_strong']} != UTR {token['lemma_strong']}"
                )
        greek_by_source[source_verse] = [
            source_word(
                token,
                exact_wordforms[source_verse][index],
                words[reverse[index]] if index in reverse else None,
            )
            for index, token in enumerate(source_tokens)
        ]

    total_tokens = 0
    for verse in chapter["verses"]:
        local_verse = int(verse["number"])
        source_verse, selected = correspondence(local_verse)
        raw_tokens = source[(1, source_verse)]
        selection = list(selected) if selected is not None else list(range(len(raw_tokens)))
        tokens = []
        for source_index in selection:
            token = dict(raw_tokens[source_index])
            token.update(greek_by_source[source_verse][source_index])
            token["source_index"] = source_index
            tokens.append(token)
        verse["grondtekst"] = [
            {key: value for key, value in token.items() if key not in {"source_index", "text", "display_strong", "lemma_strong", "morphology", "tvm"}}
            for token in tokens
        ]

        mappings = []
        if local_verse in TAIL_SPECS:
            for anchor, occurrence, token_range in TAIL_SPECS[local_verse]:
                mappings.append(mapping(anchor, occurrence, indices(token_range), tokens, source_verse))
        else:
            old_words = old_ground[local_verse]
            old_to_source = align(old_words, raw_tokens)
            source_to_local = {source_index: local_index for local_index, source_index in enumerate(selection)}
            used = set()
            for reviewed in pilot_by_verse.get(local_verse, {}).get("mappings", []):
                source_ids = sorted({
                    old_to_source[index] for index in reviewed.get("grondindices", [])
                    if index in old_to_source and old_to_source[index] in source_to_local
                })
                local_ids = [source_to_local[index] for index in source_ids]
                if not local_ids:
                    continue
                item = mapping(
                    str(reviewed["tekst"]), int(reviewed.get("voorkomen", 1)) - 1,
                    local_ids, tokens, source_verse,
                )
                mappings.append(item)
                used.update(local_ids)

            covered = sorted(
                (min(item["herkomst"]["bronindices"]), item)
                for item in mappings if item["herkomst"]["bronindices"]
            )
            for local_index in range(len(tokens)):
                if local_index in used:
                    continue
                source_index = tokens[local_index]["source_index"]
                reviewed_orphan = ORPHAN_REVIEWS.get((local_verse, source_index))
                if reviewed_orphan:
                    anchor, insertion_anchor, place, status = reviewed_orphan
                    orphan = mapping(anchor, 0, [local_index], tokens, source_verse, status)
                    if not anchor:
                        orphan["anker"] = insertion_anchor
                        orphan["plaats"] = place
                    mappings.append(orphan)
                    continue
                after = next((item for start, item in covered if start > source_index), None)
                before = next((item for start, item in reversed(covered) if start < source_index), None)
                neighbour = after or before
                if not neighbour:
                    raise ValueError(f"Johannes 1:{local_verse} heeft geen Nederlands anker")
                orphan = mapping("", 0, [local_index], tokens, source_verse, "niet_afzonderlijk_weergegeven")
                orphan["anker"] = neighbour["tekst"]
                orphan["voorkomen"] = neighbour["voorkomen"]
                orphan["plaats"] = "voor" if after else "na"
                mappings.append(orphan)

        mappings.sort(key=lambda item: min(item["herkomst"]["bronindices"]))
        verse["woordnummers"] = mappings
        total_tokens += len(tokens)

    inline = {
        "source": {
            "type": "Textus Receptus met afzonderlijke vorm-, lemma- en morfologielaag",
            "id": SOURCE_ID,
            "version": SOURCE_VERSION,
            "sha256": SOURCE_SHA256,
            "woordvormbron": {
                "id": WORDFORM_SOURCE_ID,
                "version": WORDFORM_SOURCE_VERSION,
                "sha256": WORDFORM_SOURCE_SHA256,
            },
        },
        "book": "johannes",
        "chapters": {"1": {str(v["number"]): v["woordnummers"] for v in chapter["verses"]}},
    }
    if write:
        chapter_path.write_text(json.dumps(chapter, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        (ROOT / "data" / "woordnummers-inline" / "johannes.json").write_text(
            json.dumps(inline, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    return {"verses": 52, "tokens": total_tokens, "write": write}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--utr", type=Path, required=True)
    parser.add_argument("--osis", type=Path, required=True)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    print(json.dumps(build(args.utr, args.osis, args.write), indent=2))


if __name__ == "__main__":
    main()
