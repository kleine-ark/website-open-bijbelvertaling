import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHAPTER = ROOT / "data" / "2korinthiers" / "3.json"
REVIEW = ROOT / "data" / "woordnummers-review" / "2korinthiers-3.json"
INLINE = ROOT / "data" / "woordnummers-inline" / "2korinthiers.json"

def _data(path):
    return json.loads(path.read_text(encoding="utf-8"))

def _ground_hash(chapter):
    payload = {str(v["number"]): v.get("grondtekst", []) for v in chapter["verses"]}
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest().upper()

def test_review_pins_and_ground_coverage_are_exact():
    chapter, review = _data(CHAPTER), _data(REVIEW)
    book = review["books"][0]
    assert review["source"]["sha256"] == "23D82961D8924E4592FFEE2B62504E467A0E9E79725A72512C57127FBDDD1793"
    assert review["grondtekst_bron"]["sha256"] == "BD3EC4A493D06F9173F273FD1E9971623E3A29683C0E0B40963EC8A42AF8A40E"
    assert book["grondtekst_sha256"] == _ground_hash(chapter)
    local = {v["number"]: v for v in chapter["verses"]}
    for verse in book["verses"]:
        indices = [i for m in verse["mappings"] for i in m["grondindices"]]
        indices += [i for item in verse.get("ongemapt", []) for i in item["grondindices"]]
        assert sorted(indices) == list(range(len(local[verse["verse"]]["grondtekst"])))
        assert len(indices) == len(set(indices))

def test_review_is_atomic_and_has_no_proposals():
    review = _data(REVIEW)
    assert "voorstel_" not in json.dumps(review, ensure_ascii=False)
    for verse in review["books"][0]["verses"]:
        for mapping in verse["mappings"]:
            assert mapping["reviewstatus"] == "handmatig_gecontroleerd"
            assert mapping["confidence"] == 1
            assert len(mapping["grondindices"]) <= 3
            assert len(mapping["tekst"].split()) <= 4

def test_projected_chapter_has_all_299_links_at_atomic_anchors():
    chapter, review = _data(CHAPTER), _data(REVIEW)
    inline = _data(INLINE)["chapters"]["3"]
    reviewed = review["books"][0]["verses"]
    assert sum(len(v["mappings"]) for v in reviewed) == 211
    assert sum(len(m["grondindices"]) for v in reviewed for m in v["mappings"]) == 299
    assert sum(len(v["woordnummers"]) for v in chapter["verses"]) == 211
    assert sum(len(m["strongs"]) for v in chapter["verses"] for m in v["woordnummers"]) == 299
    assert sum(len(v) for v in inline.values()) == 211
    assert sum(len(m["strongs"]) for v in inline.values() for m in v) == 299
    for verse in chapter["verses"]:
        assert all(mapping["tekst"] != verse["text2026"] for mapping in verse["woordnummers"])
