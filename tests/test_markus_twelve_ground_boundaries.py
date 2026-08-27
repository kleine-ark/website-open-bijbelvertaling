import hashlib
import json
from pathlib import Path

from scripts.import_inline_woordnummers import _grondtekst_sha256


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_GROUND_SHA = "F80124D2374EA622B67DBCBD256E159F505348F947241C69F10C68A68419CE00"
EXPECTED_FLAT_SHA = "F9E5B33AFF25DF5D6A5730A05076BAA1B4F54DD5BB11C5CC8591E55253E034B7"


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_markus_twelve_fourteen_and_fifteen_have_the_correct_ground_boundary():
    chapter = _load(ROOT / "data" / "markus" / "12.json")
    verses = {int(verse["number"]): verse for verse in chapter["verses"]}
    review = _load(ROOT / "data" / "woordnummers-review" / "markus-12.json")

    flat = [token for verse in chapter["verses"] for token in verse.get("grondtekst", [])]
    flat_payload = json.dumps(
        flat,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")

    assert len(flat) == 838
    assert hashlib.sha256(flat_payload).hexdigest().upper() == EXPECTED_FLAT_SHA
    assert _grondtekst_sha256(chapter) == EXPECTED_GROUND_SHA
    assert review["books"][0]["grondtekst_sha256"] == EXPECTED_GROUND_SHA

    assert len(verses[14]["grondtekst"]) == 40
    assert len(verses[15]["grondtekst"]) == 16
    assert [token["strongs"] for token in verses[14]["grondtekst"][-4:]] == [
        "G1325",
        "G2228",
        "G3361",
        "G1325",
    ]
    assert [token["strongs"] for token in verses[15]["grondtekst"][:3]] == [
        "G3588",
        "G1161",
        "G1492",
    ]
    assert verses[14]["text2026"].endswith("Zullen wij geven, of niet geven?")
