"""Historical reviews pin content revisions; attribution stays in the private API."""
import json
from pathlib import Path
from scripts.build_review_catalog import text_revision

ROOT = Path(__file__).resolve().parents[1]


def test_historical_chapters_have_stable_ids_and_revisions_but_no_public_verifier():
    history = json.loads((ROOT / "migrations/review-history-v1.json").read_text())
    assert history["schemaVersion"] == 1
    assert history["sourceCommit"] == "fcdc46f6773d9daea52b29108c0ac6ba761d44cd"
    subjects = history["subjects"]
    assert len(subjects) == 1141
    assert len({(item["type"], item["id"], item["revision"]) for item in subjects}) == len(subjects)
    for item in subjects:
        assert len(item["revision"]) == 64
        assert "actor" not in item and "verifierUid" not in item
        assert item["migrationSource"] in ("data/verified-chapters.json", "data/geografie-runtime.geojson")


def test_previous_full_chapter_lists_are_preserved_in_the_migration():
    history = json.loads((ROOT / "migrations/review-history-v1.json").read_text())
    identifiers = {item["id"] for item in history["subjects"] if item["type"] == "text-chapter"}
    for book, total in (("genesis", 50), ("exodus", 40), ("leviticus", 27),
                        ("1samuel", 31), ("esther", 10), ("openbaring", 22)):
        assert {f"{book}/{chapter}" for chapter in range(1, total + 1)} <= identifiers


def test_newly_completed_books_keep_their_current_revision_in_a_separate_migration():
    previous = json.loads((ROOT / "migrations/review-history-v1.json").read_text())
    history = json.loads((ROOT / "migrations/review-history-v2.json").read_text())
    assert history["schemaVersion"] == 1
    assert history["sourceCommit"] == "8f37805c8b9d93534fe3d9af7dd2a540cd29b743"
    expected = {f"{book}/{number}" for book, count in (
        ("2samuel", 24), ("ezechiel", 48), ("jubileeen", 50),
        ("3ezra", 9), ("4ezra", 16), ("judith", 16),
    ) for number in range(1, count + 1)}
    assert {item["id"] for item in history["subjects"]} == expected
    assert not expected.intersection(item["id"] for item in previous["subjects"])
    for item in history["subjects"]:
        assert item["revision"] == text_revision(json.loads((ROOT / item["source"]).read_text()))
        assert "actor" not in item and "verifierUid" not in item
