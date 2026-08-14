import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def verse(chapter: int, number: int) -> dict:
    data = json.loads((ROOT / "data" / "2samuel" / f"{chapter}.json").read_text(encoding="utf-8"))
    return next(item for item in data["verses"] if item["number"] == number)


def visible_html(value: str) -> str:
    return re.sub(r"<sup[^>]*>.*?</sup>|<[^>]+>", "", value).strip()


def test_2samuel_sheet_language_corrections_are_in_the_reading_text():
    expected = {
        (1, 1): "teruggekomen",
        (1, 10): "armband",
        (2, 14): "vechten",
        (4, 4): "verlamd was aan beide voeten",
        (6, 8): "zware slag toegebracht",
        (7, 29): "Zo moge het U nu behagen",
        (10, 5): "gegroeid zal zijn",
        (11, 1): "bij het aanbreken van het nieuwe jaar",
        (12, 31): "kleioven",
        (15, 28): "verblijven",
        (18, 5): "voorzichtig",
        (20, 3): "hun dood",
        (23, 7): "op die plaats",
    }
    for (chapter, number), fragment in expected.items():
        item = verse(chapter, number)
        assert fragment in item["text2026"], f"2 Samuel {chapter}:{number}"
        assert fragment in visible_html(item["text2026_html"]), f"2 Samuel {chapter}:{number} html"


def test_2samuel_review_keeps_plain_and_formatted_text_in_sync():
    for chapter, number in ((1, 1), (4, 6), (11, 1), (12, 4), (15, 4), (18, 27)):
        item = verse(chapter, number)
        assert visible_html(item["text2026_html"]) == item["text2026"]
