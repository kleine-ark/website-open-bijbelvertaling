import json
import re
from pathlib import Path

from scripts.import_inline_woordnummers import _grondtekst_sha256


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_GROUND_SHA = "BDAE9E3CCA31BF420BA40BD2EE5329E8A08A145518864BC1D9A93583BC021CE2"
EXPECTED_GUIDE_SHA = "03E6B838F39595459FBC66D010309274D4210B8147B0530B59988DD2EB32A12B"
EXPECTED_COUNTS = [
    10, 9, 11, 17, 17, 8, 21, 21, 23, 18, 14, 15, 30, 10, 11, 21,
    18, 18, 14, 23, 22, 4, 18, 21, 25, 22, 35, 20, 13, 10, 5, 23,
]


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _whole_word_occurrences(text: str, target: str):
    pattern = rf"(?<!\w){re.escape(target)}(?!\w)"
    return list(re.finditer(pattern, text, re.IGNORECASE | re.UNICODE))


def test_romeinen_one_ground_layer_has_the_verified_tr_boundaries():
    chapter = _load(ROOT / "data" / "romeinen" / "1.json")
    assert _grondtekst_sha256(chapter) == EXPECTED_GROUND_SHA
    assert [verse["number"] for verse in chapter["verses"]] == list(range(1, 33))
    assert [len(verse["grondtekst"]) for verse in chapter["verses"]] == EXPECTED_COUNTS
    assert sum(EXPECTED_COUNTS) == 547


def test_romeinen_one_restored_ground_boundaries_are_explicit():
    chapter = _load(ROOT / "data" / "romeinen" / "1.json")
    verses = {verse["number"]: verse for verse in chapter["verses"]}

    assert [token["strongs"] for token in verses[4]["grondtekst"][-5:]] == [
        "G2424",
        "G5547",
        "G3588",
        "G2962",
        "G1473",
    ]
    assert [token["strongs"] for token in verses[10]["grondtekst"][:5]] == [
        "G3842",
        "G1909",
        "G3588",
        "G4335",
        "G1473",
    ]
    assert verses[29]["grondtekst"][-1]["strongs"] == "G2550"
    assert verses[30]["grondtekst"][0]["strongs"] == "G5588"


def test_romeinen_one_review_is_atomic_complete_pinned_and_reachable():
    chapter = _load(ROOT / "data" / "romeinen" / "1.json")
    review_path = ROOT / "data" / "woordnummers-review" / "romeinen-1.json"
    review = _load(review_path)
    book = review["books"][0]
    verses = {verse["number"]: verse for verse in chapter["verses"]}

    assert book["grondtekst_sha256"] == EXPECTED_GROUND_SHA
    assert review["uitlijngids"]["sha256"] == EXPECTED_GUIDE_SHA
    assert [record["verse"] for record in book["verses"]] == list(range(1, 33))
    assert "voorstel_" not in review_path.read_text(encoding="utf-8")

    mapping_count = 0
    link_count = 0
    runtime_keys = set()
    for record in book["verses"]:
        verse = verses[record["verse"]]
        mappings = record["mappings"]
        mapping_count += len(mappings)
        indices = [index for mapping in mappings for index in mapping["grondindices"]]
        link_count += len(indices)

        assert sorted(indices) == list(range(len(verse["grondtekst"])))
        assert len(indices) == len(set(indices))
        assert all(mapping["bronindices"] == mapping["grondindices"] for mapping in mappings)
        assert all(mapping["reviewstatus"] == "handmatig_gecontroleerd" for mapping in mappings)
        assert all(mapping["confidence"] == 1 for mapping in mappings)
        assert all(len(mapping["grondindices"]) == 1 for mapping in mappings)

        for index, mapping in enumerate(mappings):
            target = mapping.get("tekst") or mapping.get("anker")
            occurrences = _whole_word_occurrences(verse["text2026"], target)
            assert occurrences, (record["verse"], index, target)
            occurrence = mapping.get("voorkomen", 1)
            assert 1 <= occurrence <= len(occurrences)
            strong = verse["grondtekst"][mapping["grondindices"][0]]["strongs"]
            key = (record["verse"], target.casefold(), occurrence, strong)
            assert key not in runtime_keys, key
            runtime_keys.add(key)

    assert mapping_count == 547
    assert link_count == 547
