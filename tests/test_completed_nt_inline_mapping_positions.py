import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
COMPLETED_CHAPTERS = (
    ("mattheus", 14),
    ("mattheus", 15),
    ("mattheus", 16),
    ("mattheus", 17),
    ("mattheus", 18),
    ("mattheus", 19),
    ("mattheus", 20),
    ("mattheus", 21),
    ("mattheus", 22),
    ("mattheus", 23),
    ("mattheus", 24),
    ("mattheus", 25),
    ("mattheus", 26),
    ("mattheus", 27),
    ("mattheus", 28),
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
    ("handelingen", 11),
    ("handelingen", 12),
    ("handelingen", 13),
    ("handelingen", 14),
    ("handelingen", 15),
    ("handelingen", 16),
    ("handelingen", 17),
    ("handelingen", 18),
    ("handelingen", 19),
    ("handelingen", 20),
    ("handelingen", 21),
    ("handelingen", 22),
    ("handelingen", 23),
    ("handelingen", 24),
    ("handelingen", 25),
    ("handelingen", 26),
    ("handelingen", 27),
    ("handelingen", 28),
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
