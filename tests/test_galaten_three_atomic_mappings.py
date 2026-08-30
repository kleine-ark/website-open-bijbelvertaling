import json
import re
from collections import Counter
from pathlib import Path

from scripts.import_inline_woordnummers import _grondtekst_sha256


ROOT = Path(__file__).resolve().parents[1]
CHAPTER = ROOT / "data" / "galaten" / "3.json"
REVIEW = ROOT / "data" / "woordnummers-review" / "galaten-3.json"
GROUND_SHA = "4EF230489D1D484F036DFC5F814BBBD1BF50737A1F0ACAD1589050A89CA841B6"
GUIDE_SHA = "B174BEE2C87B305DB86862D810BE20B77706C7A87E2298147E7FC90C5D17A7C3"
TR_SHA = "6D4A37FDC317AB54A38876425267F98A691FCA6FDD2E7CF10098281C7B1BEF75"


def _data():
    chapter = json.loads(CHAPTER.read_text(encoding="utf-8"))
    review = json.loads(REVIEW.read_text(encoding="utf-8"))
    verses = {verse["number"]: verse for verse in chapter["verses"]}
    reviewed = {verse["verse"]: verse for verse in review["books"][0]["verses"]}
    return chapter, review, verses, reviewed


def _matches(text, target):
    pattern = rf"(?<!\w){re.escape(target)}(?!\w)"
    return list(re.finditer(pattern, text, flags=re.IGNORECASE | re.UNICODE))


def test_galatians_three_pins_and_complete_ground_coverage():
    chapter, review, verses, reviewed = _data()
    assert _grondtekst_sha256(chapter) == GROUND_SHA
    assert review["source"]["sha256"] == GUIDE_SHA
    assert review["grondtekst_bron"]["sha256"] == TR_SHA
    assert review["grondtekst_bron"]["lokale_grondtekst_sha256"] == GROUND_SHA
    assert sorted(verses) == list(range(1, 30))
    assert sorted(reviewed) == list(range(1, 30))

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


def test_galatians_three_review_is_atomic_manual_and_reachable():
    _, _, verses, reviewed = _data()
    mappings = [mapping for verse in reviewed.values() for mapping in verse["mappings"]]
    assert len(mappings) == 461
    assert sum(len(mapping["grondindices"]) for mapping in mappings) == 464
    assert max(len(mapping["grondindices"]) for mapping in mappings) <= 2
    assert max(len((mapping.get("tekst") or mapping["anker"]).split()) for mapping in mappings) <= 4
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


def test_galatians_three_keeps_the_tr_readings_and_semantic_source_order():
    _, _, verses, reviewed = _data()

    def mapping(verse, target, occurrence=1):
        return next(
            item
            for item in reviewed[verse]["mappings"]
            if (item.get("tekst") or item.get("anker")) == target
            and item.get("voorkomen", 1) == occurrence
        )

    assert mapping(16, "tot", 1)["bronindices"] == [4]
    assert mapping(16, "de", 1)["bronindices"] == [1]
    assert mapping(17, "Christus")["bronindices"] == []
    assert mapping(21, "zijn")["bronindices"] == [21]
    assert mapping(29, "en", 2)["bronindices"] == []

    ground_17 = verses[17]["grondtekst"]
    ground_21 = verses[21]["grondtekst"]
    ground_29 = verses[29]["grondtekst"]
    assert [ground_17[index]["strongs"] for index in mapping(17, "Christus")["grondindices"]] == ["G5547"]
    assert [ground_21[index]["strongs"] for index in mapping(21, "zijn")["grondindices"]] == ["G2258"]
    assert [ground_29[index]["strongs"] for index in mapping(29, "en", 2)["grondindices"]] == ["G2532"]


def test_galatians_three_publishes_every_link_at_its_atomic_target():
    chapter, _, verses, reviewed = _data()
    inline = json.loads(
        (ROOT / "data" / "woordnummers-inline" / "galaten.json").read_text(encoding="utf-8")
    )["chapters"]["3"]

    embedded_mappings = 0
    projected_mappings = 0
    embedded_links = 0
    projected_links = 0
    for verse in chapter["verses"]:
        number = verse["number"]
        expected_links = len(verse["grondtekst"])
        embedded = verse["woordnummers"]
        projected = inline[str(number)]
        expected_mappings = len(reviewed[number]["mappings"])

        assert len(embedded) == expected_mappings
        assert len(projected) == expected_mappings
        assert sum(len(item["strongs"]) for item in embedded) == expected_links
        assert sum(len(item["strongs"]) for item in projected) == expected_links
        assert not any(item.get("tekst", "").strip() == verse["text2026"].strip() for item in embedded)
        assert not any(item.get("tekst", "").strip() == verse["text2026"].strip() for item in projected)

        embedded_mappings += len(embedded)
        projected_mappings += len(projected)
        embedded_links += sum(len(item["strongs"]) for item in embedded)
        projected_links += sum(len(item["strongs"]) for item in projected)

    assert embedded_mappings == projected_mappings == 461
    assert embedded_links == projected_links == 464
