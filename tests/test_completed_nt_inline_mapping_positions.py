import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
COMPLETED_CHAPTERS = (
    ("handelingen", 1),
    ("handelingen", 2),
    ("handelingen", 3),
    ("handelingen", 4),
    ("handelingen", 5),
    ("handelingen", 6),
    ("handelingen", 7),
    ("handelingen", 8),
    ("handelingen", 9),
    ("handelingen", 10),
    ("3johannes", 1),
    ("titus", 1),
    ("titus", 2),
    ("titus", 3),
)


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_completed_nt_chapters_use_atomic_complete_reader_mappings():
    failures = []
    for book, chapter_number in COMPLETED_CHAPTERS:
        chapter = _load(ROOT / "data" / book / f"{chapter_number}.json")
        external = _load(ROOT / "data" / "woordnummers-inline" / f"{book}.json")
        external_chapter = external["chapters"][str(chapter_number)]

        for verse in chapter["verses"]:
            text = verse.get("text2026", "").strip()
            expected = sum(
                1 for token in verse.get("grondtekst", []) if token.get("strongs")
            )
            layers = {
                "hoofdstuk": verse.get("woordnummers", []),
                "inline": external_chapter.get(str(verse["number"]), []),
            }
            for layer, mappings in layers.items():
                actual = sum(len(mapping.get("strongs", [])) for mapping in mappings)
                if actual != expected:
                    failures.append(
                        f"{book} {chapter_number}:{verse['number']} "
                        f"{layer} {actual}!={expected}"
                    )
                if any(
                    mapping.get("tekst", "").strip() == text
                    and len(mapping.get("strongs", [])) > 1
                    for mapping in mappings
                ):
                    failures.append(
                        f"{book} {chapter_number}:{verse['number']} "
                        f"{layer} hele-verskoppeling"
                    )

    assert not failures, ", ".join(failures)
