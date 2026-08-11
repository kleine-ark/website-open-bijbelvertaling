import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "import_inline_woordnummers", ROOT / "scripts" / "import_inline_woordnummers.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

AUDIT_SPEC = importlib.util.spec_from_file_location(
    "audit_woordnummers", ROOT / "scripts" / "audit_woordnummers.py"
)
AUDIT = importlib.util.module_from_spec(AUDIT_SPEC)
AUDIT_SPEC.loader.exec_module(AUDIT)


def _write_usj(path):
    path.write_text(
        json.dumps(
            {
                "type": "USJ",
                "version": "3.1",
                "content": [
                    {"type": "chapter", "marker": "c", "number": "1"},
                    {
                        "type": "para",
                        "marker": "p",
                        "content": [
                            {"type": "verse", "marker": "v", "number": "1"},
                            {"type": "char", "marker": "w", "strong": "G1722", "content": ["In"]},
                            " ",
                            {"type": "char", "marker": "w", "strong": "G746", "content": ["beginning"]},
                        ],
                    },
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def test_parse_usj_extracts_word_level_strongs_per_verse(tmp_path):
    source = tmp_path / "44JHN.usj"
    _write_usj(source)

    verses = MODULE.parse_usj(source)

    assert verses[(1, 1)] == [
        {"text": "In", "strongs": ["G1722"]},
        {"text": "beginning", "strongs": ["G746"]},
    ]


def test_build_mapping_requires_review_and_matching_source_sequence():
    local = [
        {"woord": "Ἐν", "strongs": "G1722", "transliteratie": "En", "gloss": "in"},
        {"woord": "ἀρχῇ", "strongs": "G746", "transliteratie": "arche", "gloss": "begin"},
    ]
    external = [
        {"text": "In", "strongs": ["G1722"]},
        {"text": "beginning", "strongs": ["G746"]},
    ]
    source = {"id": "bsb-full-strongs-usj", "version": "v5.6", "sha256": "abc"}

    with pytest.raises(ValueError, match="reviewstatus"):
        MODULE.build_inline_mapping(
            {"tekst": "In", "voorkomen": 1, "bronindices": [0], "reviewstatus": "voorstel"},
            external,
            local,
            source,
            "JHN 1:1",
        )

    with pytest.raises(ValueError, match="bronvolgorde"):
        MODULE.build_inline_mapping(
            {
                "tekst": "In",
                "voorkomen": 1,
                "bronindices": [1],
                "confidence": 1.0,
                "reviewstatus": "handmatig_gecontroleerd",
            },
            [{"text": "In", "strongs": ["G1722"]}],
            local,
            source,
            "JHN 1:1",
        )

    result = MODULE.build_inline_mapping(
        {
            "tekst": "het begin",
            "voorkomen": 1,
            "bronindices": [1],
            "confidence": 1.0,
            "reviewstatus": "handmatig_gecontroleerd",
        },
        external,
        local,
        source,
        "JHN 1:1",
    )
    assert result["strongs"] == ["G746"]
    assert result["bronwoorden"] == ["ἀρχῇ"]
    assert result["herkomst"] == {
        "dataset": "bsb-full-strongs-usj",
        "versie": "v5.6",
        "sha256": "abc",
        "referentie": "JHN 1:1",
        "bronindices": [1],
    }


def test_merge_preserves_existing_manually_checked_mapping():
    existing = {
        "tekst": "In",
        "voorkomen": 1,
        "strongs": ["G1722"],
        "reviewstatus": "handmatig_gecontroleerd",
        "confidence": 1.0,
        "herkomst": {"dataset": "redactie"},
    }
    verse = {"text2026": "In het begin", "woordnummers": [existing.copy()]}
    proposed = [
        {**existing, "strongs": ["G9999"], "herkomst": {"dataset": "import"}},
        {
            "tekst": "begin",
            "voorkomen": 1,
            "strongs": ["G746"],
            "reviewstatus": "handmatig_gecontroleerd",
            "confidence": 1.0,
            "herkomst": {"dataset": "import"},
        },
    ]

    added, preserved = MODULE.merge_reviewed_mappings(verse, proposed)

    assert (added, preserved) == (1, 1)
    assert verse["woordnummers"][0] == existing
    assert verse["woordnummers"][1]["strongs"] == ["G746"]


def test_pilot_johannes_1_1_tot_5_is_reviewed_without_text_changes():
    data = json.loads((ROOT / "data" / "johannes" / "1.json").read_text(encoding="utf-8"))
    verses = {verse["number"]: verse for verse in data["verses"]}

    for number in range(1, 6):
        mappings = verses[number].get("woordnummers", [])
        assert mappings, f"Johannes 1:{number} mist inline woordnummers"
        assert all(item["reviewstatus"] == "handmatig_gecontroleerd" for item in mappings)
        assert all(item["confidence"] == 1.0 for item in mappings)
        assert all(item["herkomst"]["versie"] == "v5.6" for item in mappings)

    assert verses[1]["text2026"] == "In het begin was het Woord, en het Woord was bij God, en het Woord was God."


def test_audit_reports_exact_inline_pilot_coverage_and_valid_provenance():
    report = AUDIT.audit()

    assert report["inline_eligible_verses"] > report["verses_with_inline_mappings"]
    assert report["verses_with_inline_mappings"] == 5
    assert report["inline_mappings"] == 43
    assert report["inline_number_links"] == 61
    assert report["inline_review_status"] == {"handmatig_gecontroleerd": 43}
    assert report["invalid_inline"] == []
