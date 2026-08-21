import json
import re
import subprocess
import sys
from pathlib import Path

from scripts.apply_citation_review_overdracht import CLEAR_RANGES, REVIEWED_KEEP, kaal


ROOT = Path(__file__).resolve().parents[1]
OPEN = re.compile(r'<span class="(?:god-speaks|direct-speech|angel-speaks|devil-speaks)"><i>')


B_CASES = {
    ("4ezra", 4, 15), ("4ezra", 4, 35), ("baruch", 3, 35),
    ("daniel", 6, 26), ("exodus", 16, 16), ("exodus", 32, 12),
    ("exodus", 33, 21), ("ezechiel", 26, 2), ("jeremia", 4, 11),
    ("jeremia", 46, 17), ("jesaja", 10, 13), ("jesaja", 28, 12),
    ("jesaja", 37, 22), ("job", 42, 7), ("johannes", 7, 36),
    ("leviticus", 9, 3), ("lukas", 19, 20), ("markus", 12, 36),
    ("markus", 7, 10), ("mattheus", 15, 4), ("mattheus", 18, 22),
    ("mattheus", 19, 5), ("mattheus", 25, 23), ("psalmen", 83, 5),
    ("richteren", 9, 8), ("romeinen", 9, 26), ("ruth", 2, 7),
}


def verse(book, chapter, number):
    data = json.loads((ROOT / "data" / book / f"{chapter}.json").read_text(encoding="utf-8"))
    return next(item for item in data["verses"] if item["number"] == number)


def test_all_b_cases_are_explicitly_classified():
    assert set(CLEAR_RANGES) | set(REVIEWED_KEEP) == B_CASES
    assert not (set(CLEAR_RANGES) & set(REVIEWED_KEEP))


def test_clear_ranges_leave_the_announcement_outside_the_span():
    for ref, ranges in CLEAR_RANGES.items():
        html = verse(*ref)["text2026_html"]
        first_quote = ranges[0][1]
        opening = OPEN.search(html)
        assert opening is not None, ref
        quoted_html = html[opening.start():]
        assert first_quote in kaal(quoted_html), ref
        announcement = html[:opening.start()]
        assert announcement.strip(), ref


def test_principles_v1504_through_v1528_are_unique_and_global_audit_inputs_valid():
    payload = json.loads((ROOT / "data" / "wijzigingsprincipes.json").read_text(encoding="utf-8"))
    ids = [item["id"] for item in payload["principes"]]
    assert len(ids) == len(set(ids))
    for number in range(1504, 1529):
        assert f"V{number}" in ids


def test_no_empty_speech_spans_exist_in_verse_html():
    empty = re.compile(r'<span class="(?:god-speaks|direct-speech|angel-speaks|devil-speaks)"><i>\s*</i></span>')
    found = []
    for path in (ROOT / "data").glob("*/*.json"):
        payload = json.loads(path.read_text(encoding="utf-8"))
        for item in payload.get("verses", []):
            if isinstance(item, dict) and empty.search(item.get("text2026_html", "")):
                found.append(f"{path.parent.name} {path.stem}:{item.get('number')}")
    assert found == []


def test_stats_follow_current_principles_source():
    stats = json.loads((ROOT / "data" / "stats.json").read_text(encoding="utf-8"))
    principles = json.loads((ROOT / "data" / "wijzigingsprincipes.json").read_text(encoding="utf-8"))
    assert stats["principes"] == len(principles["principes"])


def test_reviewed_b_cases_are_not_offered_as_automatic_repairs():
    result = subprocess.run(
        [sys.executable, "scripts/span_om_vertelling.py", "--proef", "--soorten", "B", "--toon", "0"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert "B=0" in result.stdout
