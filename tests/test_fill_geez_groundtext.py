import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "fill_geez_groundtext", ROOT / "scripts" / "fill_geez_groundtext.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_parse_source_requires_explicit_chapter_and_verse_markers():
    source = """HOOFDSTUK 2
2:1 ወሀሎ፡ ብእሲ።
doorlopende regel zonder versmarkering
2:2 ወቦቱ ፡ መቃብዮስ ።
"""

    assert MODULE.parse_source(source) == {
        (2, 1): "ወሀሎ፡ ብእሲ።",
        (2, 2): "ወቦቱ ፡ መቃብዮስ ።",
    }


def test_tokenize_geez_omits_source_markers_and_punctuation():
    assert MODULE.tokenize_geez("1:1 ወሀሎ፡ %፡ ብእሲ።") == ["ወሀሎ", "ብእሲ"]


def test_build_groundtext_adds_only_repo_backed_metadata():
    lexicon = {
        "ወሀሎ": {"transliteratie": "wähälo", "betekenis": "en er was", "ovg": "OVG0077"},
        "ብእሲ": {"transliteratie": "bəʾsi", "betekenis": "man"},
    }
    exact_numbers = {("geez", "ብእሲ"): "OVG1234"}

    assert MODULE.build_groundtext("ወሀሎ፡ ብእሲ።", lexicon, exact_numbers) == [
        {"woord": "ወሀሎ", "transliteratie": "wähälo", "betekenis": "en er was", "strongs": "OVG0077"},
        {"woord": "ብእሲ", "transliteratie": "bəʾsi", "betekenis": "man", "strongs": "OVG1234"},
    ]


def test_meqabyan_hiaat_is_hersteld_en_droge_run_is_leeg():
    import json

    data = json.loads((ROOT / "data" / "1meqabyan" / "2.json").read_text(encoding="utf-8"))
    verse = next(item for item in data["verses"] if item["number"] == 1)

    assert verse["grondtekst"]
    assert verse["grondtekst"][0]["woord"] == "ወሀሎ"
    assert MODULE.fill(write=False)["verses_filled"] == 0
