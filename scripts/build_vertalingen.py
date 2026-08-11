"""Converteer de ongewijzigde USFM-bronnen naar het OV-hoofdstukformaat.

De converter is deterministisch: bronbestanden worden gesorteerd gelezen en JSON
wordt met vaste inspringing en sleutelvolgorde geschreven. Onbekende markeringen
komen in het controleverslag terecht; ze worden nooit als HTML doorgegeven.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import shutil
from collections import Counter
from pathlib import Path


BOOK_IDS = {
    "GEN": "genesis", "EXO": "exodus", "LEV": "leviticus", "NUM": "numeri",
    "DEU": "deuteronomium", "JOS": "jozua", "JDG": "richteren", "RUT": "ruth",
    "1SA": "1samuel", "2SA": "2samuel", "1KI": "1koningen", "2KI": "2koningen",
    "1CH": "1kronieken", "2CH": "2kronieken", "EZR": "ezra", "NEH": "nehemia",
    "EST": "esther", "JOB": "job", "PSA": "psalmen", "PRO": "spreuken",
    "ECC": "prediker", "SNG": "hooglied", "ISA": "jesaja", "JER": "jeremia",
    "LAM": "klaagliederen", "EZK": "ezechiel", "DAN": "daniel", "HOS": "hosea",
    "JOL": "joel", "AMO": "amos", "OBA": "obadja", "JON": "jona", "MIC": "micha",
    "NAM": "nahum", "HAB": "habakuk", "ZEP": "zefanja", "HAG": "haggai",
    "ZEC": "zacharia", "MAL": "maleachi", "MAT": "mattheus", "MRK": "markus",
    "LUK": "lukas", "JHN": "johannes", "ACT": "handelingen", "ROM": "romeinen",
    "1CO": "1korinthiers", "2CO": "2korinthiers", "GAL": "galaten", "EPH": "efeziers",
    "PHP": "filippenzen", "COL": "kolossenzen", "1TH": "1tessalonicensen",
    "2TH": "2tessalonicensen", "1TI": "1timotheus", "2TI": "2timotheus",
    "TIT": "titus", "PHM": "filemon", "HEB": "hebreeen", "JAS": "jakobus",
    "1PE": "1petrus", "2PE": "2petrus", "1JN": "1johannes", "2JN": "2johannes",
    "3JN": "3johannes", "JUD": "judas", "REV": "openbaring",
    "TOB": "tobit", "JDT": "judith", "WIS": "boekderwijsheid", "SIR": "jezussirach",
    "BAR": "baruch", "1MA": "1makkabeeen", "2MA": "2makkabeeen",
    "1ES": "3ezra", "2ES": "4ezra", "MAN": "gebedvanmanasse",
    "3MA": "3makkabeeen",
}

EDITIONS = {
    "fr-lsg1910": {"source": "fraLSG", "name": "Louis Segond 1910", "language": "fr", "direction": "ltr", "sha256": "3A0615E992FFD412B1AFCAED50D146BBA5EC8AE2378F04CA71459A4CD2D7CC33"},
    "en-webbe": {"source": "eng-webbe", "name": "World English Bible British Edition", "language": "en", "direction": "ltr", "sha256": "71BC006074BBEE6206F4B822814218FD64E6CB51C71647104C94D5B08FFAFC9F"},
    "ar-vd": {"source": "arb-vd", "name": "Arabic Van Dyck", "language": "ar", "direction": "rtl", "sha256": "E4A2AB9491B2AC2FF799BB2A80EC9322203A7C36E78210B4506DF84308C54948"},
    "uk-ukrfb": {"source": "ukrfb", "name": "Ukrainian Freedom Bible", "language": "uk", "direction": "ltr", "sha256": "C634DB3081690A9201E19F71276EAA6E5B4B487D1455637548305F220B2B6CD5"},
    "de-luther1912": {"source": "deu1912", "name": "Lutherbibel 1912", "language": "de", "direction": "ltr", "sha256": "650A8192134A8F0057286C469754EDCFAEE4FBB18800621AEE4563F3055BB39B"},
    "es-rv1909": {"source": "spaRV1909", "name": "Reina-Valera 1909", "language": "es", "direction": "ltr", "sha256": "B5BFAC87199A561FCBACB5E32BE5D8D280934B1C6830088D9EB8C68FFBFBE711"},
}

NOTE_RE = re.compile(r"\\f\s+(.*?)\\f\*", re.S)
XREF_RE = re.compile(r"\\x\s+(.*?)\\x\*", re.S)
WORD_RE = re.compile(r"\\\+?w\s+([^|\\]+)\|([^\\]+)\\\+?w\*")
CHAR_STYLE_RE = re.compile(r"\\\+?(?:it|bd|bdit|em|sc|sup|nd|add|wj|wh)\s+(.*?)\\\+?(?:it|bd|bdit|em|sc|sup|nd|add|wj|wh)\*", re.S)
MARKER_RE = re.compile(r"\\([A-Za-z0-9+]+)\*?")


def _normalise_space(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _note_text(value: str) -> str:
    value = re.sub(r"^[+a-z]\s+", "", value, count=1)
    value = re.sub(r"\\(?:fr|xo)\s+[^\\]+", " ", value)
    value = re.sub(r"\\(?:fr|fk|fq|fqa|fl|fp|ft|fdc|fv|xo|xk|xq|xt|xta)\s*", " ", value)
    value = MARKER_RE.sub("", value)
    return _normalise_space(value)


def _extract_rich_text(raw: str):
    footnotes = [{"tekst": _note_text(m.group(1))} for m in NOTE_RE.finditer(raw)]
    crossrefs = [{"tekst": _note_text(m.group(1))} for m in XREF_RE.finditer(raw)]
    raw = NOTE_RE.sub("", raw)
    raw = XREF_RE.sub("", raw)
    segments = []

    def word(match):
        text = _normalise_space(match.group(1))
        attrs = match.group(2)
        strong_match = re.search(r'(?:strong|x-strong)="([^"]+)"', attrs)
        strongs = re.findall(r"[HG]\d+[A-Za-z]?", strong_match.group(1)) if strong_match else []
        segment = {"tekst": text}
        if strongs:
            segment["strong"] = strongs
        lemma_match = re.search(r'lemma="([^"]+)"', attrs)
        if lemma_match:
            segment["lemma"] = lemma_match.group(1)
        segments.append(segment)
        return text

    plain = WORD_RE.sub(word, raw)
    plain = CHAR_STYLE_RE.sub(lambda m: m.group(1), plain)
    plain = MARKER_RE.sub("", plain)
    plain = _normalise_space(plain)
    return plain, html.escape(plain, quote=False), segments, footnotes, crossrefs


def parse_usfm(path: Path, edition: str, book_id: str):
    text = path.read_text(encoding="utf-8-sig")
    lines = text.splitlines()
    chapters = {}
    warnings = []
    current_chapter = None
    pending_heading = None
    pending_block = "alinea"
    current_verse = None

    def finish_verse():
        nonlocal current_verse
        if not current_verse or current_chapter is None:
            return
        raw = _normalise_space(" ".join(current_verse["raw"]))
        plain, safe_html, segments, notes, refs = _extract_rich_text(raw)
        verse = {
            "nummer": current_verse["number"], "tekst": plain, "html": safe_html,
            "segmenten": segments, "voetnoten": notes, "kruisverwijzingen": refs,
        }
        ch = chapters[current_chapter]
        ch["verzen"].append(verse)
        ch["blokken"].append({"type": current_verse["block"], "vers": current_verse["number"]})
        current_verse = None

    for line in lines:
        if not line.strip():
            continue
        if not line.startswith("\\"):
            if current_verse:
                current_verse["raw"].append(line)
            continue
        match = re.match(r"\\([A-Za-z0-9+]+)\s*(.*)$", line)
        if not match:
            continue
        marker, value = match.group(1), match.group(2)
        if marker == "c":
            finish_verse()
            current_chapter = int(value.split()[0])
            chapters[current_chapter] = {
                "editie": edition, "boek": book_id, "hoofdstuk": current_chapter,
                "kop": None, "blokken": [], "verzen": [],
            }
            pending_heading = None
        elif marker.startswith("s") and current_chapter is not None:
            finish_verse()
            pending_heading = _normalise_space(value)
            if pending_heading and not chapters[current_chapter]["kop"]:
                chapters[current_chapter]["kop"] = pending_heading
            chapters[current_chapter]["blokken"].append({"type": "kop", "niveau": marker, "tekst": pending_heading})
        elif marker in {"p", "m", "pi", "pi1", "pi2", "mi", "nb", "pc"}:
            finish_verse()
            pending_block = "alinea"
            if value and current_verse:
                current_verse["raw"].append(value)
        elif marker.startswith("q"):
            finish_verse()
            pending_block = "poezie"
            # Een vers kan op dezelfde regel na de q-marker beginnen.
            verse_match = re.match(r"\\v\s+(\d+[A-Za-z]?)\s+(.*)$", value)
            if verse_match:
                current_verse = {"number": verse_match.group(1), "raw": [verse_match.group(2)], "block": pending_block}
        elif marker in {"r", "mr", "d", "b", "ms", "ms1", "ms2", "ms3", "tr", "th1", "th2", "th3", "tc1", "tc2", "tc3", "li", "li1", "li2"}:
            # Structurele tekst tussen verzen hoort niet bij het voorgaande vers.
            finish_verse()
        elif marker == "v" and current_chapter is not None:
            finish_verse()
            verse_match = re.match(r"(\d+[A-Za-z]?)\s*(.*)$", value)
            if verse_match:
                number_raw = verse_match.group(1)
                number = int(number_raw) if number_raw.isdigit() else number_raw
                current_verse = {"number": number, "raw": [verse_match.group(2)], "block": pending_block}
            pending_block = "alinea"
        elif current_verse and marker not in {"id", "ide", "h", "toc1", "toc2", "toc3"}:
            # Karaktermarkeringen kunnen op een vervolgregel staan.
            current_verse["raw"].append(line)
        elif marker not in {"id", "ide", "h", "toc1", "toc2", "toc3", "mt", "mt1", "mt2", "mt3", "imt", "imt1", "imt2", "ip", "ipi", "im", "ie", "is", "is1", "r", "mr", "cl", "d", "b", "rem"}:
            warnings.append({"marker": marker, "line": line[:160]})
    finish_verse()
    return chapters, warnings


def _write_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")


def convert_all(source_root: Path, output: Path, editions=None):
    editions = tuple(editions or EDITIONS.keys())
    manifest = {"schema": 1, "edities": []}
    report = {"schema": 1, "edities": {}}
    for code in editions:
        meta = EDITIONS[code]
        source_dir = source_root / meta["source"] / "usfm"
        edition_output = output / code
        if edition_output.exists():
            shutil.rmtree(edition_output)
        edition_books = []
        counts = Counter()
        unsupported = Counter()
        for path in sorted(source_dir.glob("*.usfm")):
            id_match = re.search(r"^\\id\s+([A-Z0-9]+)", path.read_text(encoding="utf-8-sig"), re.M)
            usfm_code = id_match.group(1) if id_match else ""
            book_id = BOOK_IDS.get(usfm_code)
            if not book_id:
                if usfm_code not in {"FRT", "GLO", "PS2", "ESG", "DAG"}:
                    unsupported["boek:" + (usfm_code or path.name)] += 1
                continue
            chapters, warnings = parse_usfm(path, code, book_id)
            if not chapters:
                continue
            edition_books.append(book_id)
            counts["boeken"] += 1
            counts["hoofdstukken"] += len(chapters)
            for chapter_number, chapter in sorted(chapters.items()):
                counts["verzen"] += len(chapter["verzen"])
                counts["segmenten"] += sum(len(v["segmenten"]) for v in chapter["verzen"])
                counts["voetnoten"] += sum(len(v["voetnoten"]) for v in chapter["verzen"])
                counts["kruisverwijzingen"] += sum(len(v["kruisverwijzingen"]) for v in chapter["verzen"])
                _write_json(output / code / book_id / f"{chapter_number}.json", chapter)
            for warning in warnings:
                unsupported[warning["marker"]] += 1
        manifest["edities"].append({
            "code": code, "naam": meta["name"], "taal": meta["language"],
            "richting": meta["direction"], "rechten": "publiek domein",
            "bron": f"bronbestanden/vertalingen/{meta['source']}",
            "bronSha256": meta["sha256"], "boeken": sorted(edition_books),
        })
        report["edities"][code] = {**dict(counts), "onbekendeMarkeringen": dict(sorted(unsupported.items()))}
    _write_json(output / "manifest.json", manifest)
    _write_json(output / "rapport.json", report)
    return report


def main():
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=root / "bronbestanden" / "vertalingen")
    parser.add_argument("--output", type=Path, default=root / "data" / "vertalingen")
    args = parser.parse_args()
    report = convert_all(args.source, args.output)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
