import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_1samuel_is_marked_human_reviewed_after_the_full_review():
    reviewed = json.loads((ROOT / "data" / "verified-chapters.json").read_text(encoding="utf-8"))
    assert reviewed["1samuel"] == "all"


def test_1samuel_reviewed_sheet_corrections_are_visible_in_text_and_diff():
    chapter = json.loads((ROOT / "data" / "1samuel" / "17.json").read_text(encoding="utf-8"))
    verse = next(item for item in chapter["verses"] if item["number"] == 18)
    assert "een teken van leven" in verse["text2026"]
    assert any(item["new"] == "een teken van leven" for item in verse["phraseDiff"])
    note = next(item for item in verse["marginNotes"] if item["marker"] == "21")
    assert "teken van leven" in note["text2026"]
