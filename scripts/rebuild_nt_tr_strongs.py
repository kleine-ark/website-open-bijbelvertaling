#!/usr/bin/env python3
"""Gepinde Textus-Receptus-bronlaag voor handmatig beoordeelde NT-hoofdstukken."""

from __future__ import annotations

import hashlib
import html
import re
import sys
import unicodedata
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from import_inline_woordnummers import parse_tr_utr  # noqa: E402


UTR_SHA256 = {
    "JOH.UTR": "77FBB830AE3E11B79F7F47A8E68A119DC77F0722EBCC99BB00111702797BFFE5",
    "MT.UTR": "5AA69DC0F3119DE714907E9279302E6BDADA20F5C1C2F5A1FB0ED365BE90DFE5",
    "MR.UTR": "214B774BFA4BFB29C67D02E92BB90E7CC20FD2C5A523557E51902E61E3A6BCFD",
    "LU.UTR": "03E1B6480F666C7D04D6F7B00275F3F500FE09FC407683EE757CC1B11D8D1BA1",
    "AC.UTR": "B5695B6027866CE6DBAA398A84571B92F27B4A964340810858C0AA134EF71049",
    "RO.UTR": "01097A0D4322240C0620F198D49101FEB5E55E87CC0D5EA2C8077A154003CFEC",
    "1CO.UTR": "37682DF58A5DBD56C69D5B4D019A353B11443A3DE96E686095546506F02DB8B9",
    "2CO.UTR": "BD3EC4A493D06F9173F273FD1E9971623E3A29683C0E0B40963EC8A42AF8A40E",
    "GA.UTR": "6D4A37FDC317AB54A38876425267F98A691FCA6FDD2E7CF10098281C7B1BEF75",
    "EPH.UTR": "BC2D3631DE9B311C03BCFAED5D1B4F0C1E6DF4812C852FF54B3274AC03A7A0D1",
    "PHP.UTR": "DF5C55B552DBF44460AE33E39CC0238F112049F67BA05B46F15303B5A496BD58",
    "COL.UTR": "43E74492989EBADA1B4ECEB1FF7CC7C80F1923E0702A021549B90EF24E348153",
    "1TH.UTR": "1C1BA0F30DBE30D972E42241672DFE641F372EB182B26A2620556DEE8CB17186",
    "2TH.UTR": "D73D610D017ED8CC4A2090AA70F0E64838C51D7F870B603306C96C61D85215F5",
    "1TI.UTR": "3326733E97A59DF0BF35EB9CE0810DEE0A0D482D11D5B90C7325B01DBAEF6DA8",
    "2TI.UTR": "D1EFC2A29B89527D134FD84F39688F30A0740A7DA3A5A473EF3731F8278A73B0",
    "TIT.UTR": "7AEA80E604446267A9AD09A8871A642766E579C725457A1B6C0143DF1B3486D9",
    "PHM.UTR": "A6A39A7AB3C55331A19A0814229EDEB6B1A3D86C99DE377A11C710DE83604F4B",
    "HEB.UTR": "5A3C907DA1F2D88795905D1C626F3765B507B39C11C6CCC1396484CA8C346387",
    "JAS.UTR": "FB3A867EFCB0BE09AA3C5104F594A93F4767E602DBECEC71D3F9EE65BBC13663",
    "1PE.UTR": "1D0E91F7F08C77DB05D4DDB7367105A4DF11B7936808E89BD27CE8A2F0AB1FC8",
    "2PE.UTR": "8D864C32B383DB350D4B8D269AA1C2545C41B1F1D22E539F9459EF087E7AC478",
    "1JO.UTR": "4D47F13A274A6AFD8BE33B71CBC9F30D4B458704710DC0B060C16FCD9DE80FEB",
    "2JO.UTR": "D726F61B2F23F0839680AE0AE22ABE059EB9C4FE72E14A0922336662B5CA262F",
    "3JO.UTR": "CDAC972DB4CD7D9752D893434B604C8C9E175F125EE964510EC5528DC3932617",
    "JUDE.UTR": "46724D6AC953166269CC6B85FB44031DD33EEF2B8E32F471DA0AF0448C087B90",
    "RE.UTR": "1C641BACA7E65947C583F5CD9723F0497E771EF819708F8817F803FAD39E6624",
}
OSIS_SHA256 = "2BC5C343DA30125AF8D4D1E27F8444019030B6350D16E69EF8645BF9E17D5963"
FORM_STRONG_OVERRIDES = {
    ("G4183", "A-APM-C"): "G4119",
    # Matt.11:20 πλείσται: UTR bewaart lemma G4183 en A-NPF-S;
    # de gepinde OSIS presenteert dezelfde vorm als G4118.
    ("G4183", "A-NPF-S"): "G4118",
    # Matt.21:8: identieke vorm en morfologie, alleen OSIS-lemmaweergave.
    ("G4183", "A-NSM-S"): "G4118",
    ("G4183", "A-ASN-S"): "G4118",
    ("G3778", "D-DSN"): "G5129",
    ("G3062", "A-GSN"): "G3064",
    # Matt.26:45 λοιπον: identieke UTR/OSIS-vorm en A-ASN; alleen de
    # OSIS-presentatie verwijst naar de verwante lemmaweergave G3063.
    ("G3062", "A-ASN"): "G3063",
    ("G1326", "V-APP-NSM"): "G1453",
}


GREEK_TO_UTR = str.maketrans({
    "α": "a", "β": "b", "γ": "g", "δ": "d", "ε": "e", "ζ": "z",
    "η": "h", "θ": "q", "ι": "i", "κ": "k", "λ": "l", "μ": "m",
    "ν": "n", "ξ": "x", "ο": "o", "π": "p", "ρ": "r", "σ": "s",
    "ς": "v", "τ": "t", "υ": "u", "φ": "f", "χ": "c", "ψ": "y",
    "ω": "w",
})


def utr_spelling(greek: str) -> str:
    plain = "".join(
        char for char in unicodedata.normalize("NFD", str(greek).lower())
        if unicodedata.category(char) != "Mn"
    )
    return plain.translate(GREEK_TO_UTR)


def select_osis_variant_stream(source: list[dict], indexed: dict[int, dict]) -> list[dict]:
    """Kies UTR-varianten en vul aantoonbaar ontbrekende tokens uit OSIS aan."""
    exact = [indexed[index] for index in sorted(indexed)]

    @lru_cache(maxsize=None)
    def choose(source_at: int, exact_at: int):
        if exact_at == len(exact):
            return (0, ())
        if source_at == len(source):
            return (
                100 * (len(exact) - exact_at),
                tuple(("osis", index) for index in range(exact_at, len(exact))),
            )
        best = choose(source_at + 1, exact_at)
        inserted_tail = choose(source_at, exact_at + 1)
        if inserted_tail is not None:
            inserted = (inserted_tail[0] + 100, (("osis", exact_at),) + inserted_tail[1])
            if best is None or inserted < best:
                best = inserted
        candidate = source[source_at]
        target = exact[exact_at]
        if (
            normal(candidate["lemma_strong"]) == normal(target["lemma_strong"])
            and candidate["morphology"] == target["morfologie"]
        ):
            tail = choose(source_at + 1, exact_at + 1)
            if tail is not None:
                spelling_penalty = int(candidate["text"] != utr_spelling(target["woord"]))
                matched = (tail[0] + spelling_penalty, (("utr", source_at),) + tail[1])
                if best is None or matched < best:
                    best = matched
        return best

    selected = choose(0, 0)
    if selected is None or len(selected[1]) != len(exact):
        raise ValueError("UTR-varianten kunnen niet bronvast met de OSIS-stroom worden verenigd")
    merged = []
    for kind, index in selected[1]:
        if kind == "utr":
            merged.append(source[index])
            continue
        token = exact[index]
        merged.append({
            "text": utr_spelling(token["woord"]),
            "lemma_strong": token["lemma_strong"],
            "display_strong": token["lemma_strong"],
            "morphology": token["morfologie"],
            "bronstatus": "osis_aanvulling",
        })
    return merged


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
            raw_source_indices = attrs.get("src", "").split()
            numeric_offsets = [offset for offset, value in enumerate(raw_source_indices) if value.isdigit()]
            source_indices = [int(raw_source_indices[offset]) for offset in numeric_offsets]
            strongs = re.findall(r'G\d+', attrs.get("lemma", ""))
            forms = re.findall(r'lemma\.TR:([^\s]+)', attrs.get("lemma", ""))
            morphs = re.findall(r'robinson:([^\s]+)', attrs.get("morph", ""))
            if not source_indices:
                continue
            strongs = [strongs[offset] for offset in numeric_offsets]
            forms = [forms[offset] for offset in numeric_offsets]
            morphs = [morphs[offset] for offset in numeric_offsets]
            # John 21:11 bewaart voor πεντηκοντατριων naast het lemma ook
            # het traditionele vormnummer in dezelfde OSIS-token. De UTR
            # levert één bronwoord met het lemma; de vormcode blijft daar
            # beschikbaar als presentatiecode, dus deze ene OSIS-vorm is
            # bronvast naar het lemma te reduceren.
            if len(source_indices) == len(forms) == 1 and len(strongs) > 1:
                strongs = strongs[:1]
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
    allowed_osis_variants: set[tuple[int, int]] | None = None,
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
            source = select_osis_variant_stream(source, indexed)
            # Een echte variant kan OSIS-bronposities overslaan (Matt. 23:14).
            # Na de bronvaste selectie vormen UTR en OSIS één nieuwe, oplopende
            # tokenstroom; herindexeer uitsluitend die geselecteerde OSIS-vormen.
            indexed = {
                position: token
                for position, token in enumerate(indexed[index] for index in sorted(indexed))
            }
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
            is_allowed_variant = (verse, index) in (allowed_osis_variants or set())
            if normal(exact["lemma_strong"]) not in {
                normal(token["lemma_strong"]), normal(display_strong)
            } and not is_allowed_variant:
                raise ValueError(
                    f"{osis_book}.{chapter}.{verse} token {index + 1}: "
                    f"OSIS {exact['lemma_strong']} != UTR {token['lemma_strong']}"
                )
            enriched = dict(token)
            enriched["woord"] = exact["woord"]
            enriched["display_strong"] = display_strong
            enriched["source_index"] = index
            if is_allowed_variant:
                enriched["bronstatus"] = "osis_variant_ongemapt"
                enriched["osis_variant"] = {
                    "lemma_strong": exact["lemma_strong"],
                    "morfologie": exact["morfologie"],
                }
            tokens.append(enriched)
        result[verse] = tokens
    return result
