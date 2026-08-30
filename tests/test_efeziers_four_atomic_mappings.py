import json
import re
from collections import Counter
from pathlib import Path

from scripts.import_inline_woordnummers import _grondtekst_sha256


ROOT = Path(__file__).resolve().parents[1]
CHAPTER = ROOT / "data" / "efeziers" / "4.json"
REVIEW = ROOT / "data" / "woordnummers-review" / "efeziers-4.json"
GROUND_SHA = "CB9F9E61ADB4ADB2FEF52A2D84FE32D12F022BB2E9FDC311EB894FB0FF34AC73"
GUIDE_SHA = "6FAE4C585DE1D229E8F9A2E01722C995B9CA96B10902BC1EB264E4144D9CDF7F"
TR_SHA = "BC2D3631DE9B311C03BCFAED5D1B4F0C1E6DF4812C852FF54B3274AC03A7A0D1"


def _data():
    chapter = json.loads(CHAPTER.read_text(encoding="utf-8"))
    review = json.loads(REVIEW.read_text(encoding="utf-8"))
    verses = {verse["number"]: verse for verse in chapter["verses"]}
    reviewed = {verse["verse"]: verse for verse in review["books"][0]["verses"]}
    return chapter, review, verses, reviewed


def _matches(text, target):
    pattern = rf"(?<!\w){re.escape(target)}(?!\w)"
    return list(re.finditer(pattern, text, flags=re.IGNORECASE | re.UNICODE))


def test_ephesians_four_pins_and_complete_ground_coverage():
    chapter, review, verses, reviewed = _data()
    assert _grondtekst_sha256(chapter) == GROUND_SHA
    assert review["source"]["sha256"] == GUIDE_SHA
    assert review["grondtekst_bron"]["sha256"] == TR_SHA
    assert review["grondtekst_bron"]["lokale_grondtekst_sha256"] == GROUND_SHA
    assert sorted(verses) == list(range(1, 33))
    assert sorted(reviewed) == list(range(1, 33))

    for number, verse in verses.items():
        record = reviewed[number]
        covered = [
            index
            for mapping in record["mappings"]
            for index in mapping["grondindices"]
        ]
        covered += [
            index
            for item in record.get("ongemapt", [])
            for index in item["grondindices"]
        ]
        assert Counter(covered) == Counter(range(len(verse["grondtekst"])))


def test_ephesians_four_review_is_atomic_manual_and_reachable():
    _, _, verses, reviewed = _data()
    mappings = [mapping for verse in reviewed.values() for mapping in verse["mappings"]]
    assert len(mappings) == 478
    assert sum(len(mapping["grondindices"]) for mapping in mappings) == 486
    assert max(len(mapping["grondindices"]) for mapping in mappings) == 2
    assert sorted(
        (verse, mapping.get("tekst") or "<leeg>", mapping.get("anker", ""), mapping["grondindices"])
        for verse, record in reviewed.items()
        for mapping in record["mappings"]
        if len(mapping["grondindices"]) > 1
    ) == [
        (9, "dan", "", [5, 6]),
        (10, "alle dingen", "", [13, 14]),
        (15, "alleszins", "", [7, 8]),
        (16, "ieder", "", [17, 18]),
        (19, "begerig", "", [10, 11]),
        (24, "ware", "", [13, 14]),
        (29, "Geen", "", [0, 7]),
        (29, "nuttige", "", [15, 16]),
    ]
    assert max(len((mapping.get("tekst") or mapping["anker"]).split()) for mapping in mappings) <= 3
    assert all(mapping["confidence"] == 1 for mapping in mappings)
    assert all(mapping["reviewstatus"] == "handmatig_gecontroleerd" for mapping in mappings)
    assert "voorstel_" not in REVIEW.read_text(encoding="utf-8")

    for number, record in reviewed.items():
        text = verses[number]["text2026"]
        for mapping in record["mappings"]:
            target = mapping.get("tekst") or mapping["anker"]
            matches = _matches(text, target)
            assert matches, (number, target)
            occurrence = mapping.get("voorkomen", 1)
            assert 1 <= occurrence <= len(matches), (number, target, occurrence)
            if len(matches) > 1:
                assert "voorkomen" in mapping, (number, target, len(matches))

    assert {
        tuple(mapping["grondindices"]): (mapping["tekst"], mapping.get("voorkomen", 1))
        for mapping in reviewed[31]["mappings"]
        if mapping["grondindices"] in ([0], [2], [3], [4], [6], [8], [14], [15])
    } == {
        (0,): ("Alle", 1),
        (2,): ("en", 1),
        (3,): ("boosheid", 1),
        (4,): ("en", 2),
        (6,): ("en", 3),
        (8,): ("en", 4),
        (14,): ("alle", 2),
        (15,): ("boosheid", 2),
    }


def test_ephesians_four_documents_all_guide_tr_differences():
    _, _, _, reviewed = _data()
    deviations = {
        number: [
            (item["bron_strongs"], item["grondtekst_strongs"])
            for item in record.get("bronafwijkingen", [])
        ]
        for number, record in reviewed.items()
        if record.get("bronafwijkingen")
    }
    assert deviations == {
        6: [([], ["G4771"])],
        9: [([], ["G4412"])],
        15: [([], ["G3588"])],
        17: [([], ["G3062"])],
        18: [(["G4656"], ["G4654"])],
        21: [(["G1487", "G1065"], ["G1489"])],
        27: [(["G3366"], ["G3383"])],
        28: [(["G3588", "G2398"], ["G3588"])],
    }


def test_ephesians_four_publishes_every_link_at_an_atomic_target():
    chapter = json.loads(CHAPTER.read_text(encoding="utf-8"))
    inline = json.loads((ROOT / "data" / "woordnummers-inline" / "efeziers.json").read_text(encoding="utf-8"))
    inline_verses = inline["chapters"]["4"]

    for verse in chapter["verses"]:
        embedded = verse["woordnummers"]
        projected = inline_verses[str(verse["number"])]
        expected = len(verse["grondtekst"])

        for mappings in (embedded, projected):
            assert sum(len(mapping["strongs"]) for mapping in mappings) == expected
            assert not any(
                mapping.get("tekst", "").strip() == verse["text2026"].strip()
                for mapping in mappings
            )

    assert sum(len(verse["woordnummers"]) for verse in chapter["verses"]) == 478
    assert sum(len(items) for items in inline_verses.values()) == 478
