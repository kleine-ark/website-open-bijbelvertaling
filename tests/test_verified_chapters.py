"""All old chapter statuses are pinned migration history, never current sign-off."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_historical_chapters_have_stable_ids_and_revisions_but_no_invented_verifier():
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
