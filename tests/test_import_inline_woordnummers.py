import importlib.util
import json
from collections import Counter
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


def test_parse_tr_utr_separates_display_strong_morphology_and_lemma(tmp_path):
    source = tmp_path / "JOH.UTR"
    source.write_text(
        "1:1 en 1722 {PREP} arch 746 {N-DSF} hn 1510 5707 {V-IAI-3S} "
        "o 3588 {T-NSM} logov 3056 {N-NSM} 5740 {V-PNP-ASM} "
        "2064 5740 {V-PNP-NSN}\n",
        encoding="utf-8",
    )

    verses = MODULE.parse_tr_utr(source)

    assert verses[(1, 1)] == [
        {"text": "en", "lemma_strong": "G1722", "display_strong": "G1722", "morphology": "PREP", "tvm": None},
        {"text": "arch", "lemma_strong": "G746", "display_strong": "G746", "morphology": "N-DSF", "tvm": None},
        {"text": "hn", "lemma_strong": "G1510", "display_strong": "G2258", "morphology": "V-IAI-3S", "tvm": "G5707"},
        {"text": "o", "lemma_strong": "G3588", "display_strong": "G3588", "morphology": "T-NSM", "tvm": None},
        {"text": "logov", "lemma_strong": "G3056", "display_strong": "G3056", "morphology": "N-NSM", "tvm": None},
    ]


def test_parse_tagnt_tr_prefers_traditional_form_number(tmp_path):
    source = tmp_path / "TAGNT.txt"
    source.write_text(
        "Jhn.1.1#03=NKO\tἦν (ēn)\twas\tG1510=V-IAI-3S\tεἰμί=to be\tNA28+TR+Byz"
        "\t\t\t\tto be\t#03\tG1510_A\tG2258\n",
        encoding="utf-8",
    )

    verses = MODULE.parse_tagnt_tr(source, "Jhn", 1)

    assert verses[(1, 1)] == [{
        "text": "ἦν",
        "lemma_strong": "G1510",
        "display_strong": "G2258",
        "morphology": "V-IAI-3S",
        "sequence": 3,
    }]


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


def test_johannes_1_1_tot_5_is_tr_reviewed_without_text_changes():
    data = json.loads((ROOT / "data" / "johannes" / "1.json").read_text(encoding="utf-8"))
    verses = {verse["number"]: verse for verse in data["verses"]}

    for number in range(1, 6):
        mappings = verses[number].get("woordnummers", [])
        assert mappings, f"Johannes 1:{number} mist inline woordnummers"
        assert all(item["reviewstatus"] == "handmatig_gecontroleerd" for item in mappings)
        assert all(item["confidence"] == 1.0 for item in mappings)
        assert all(item["herkomst"]["dataset"] == "robinson-scrivener-tr" for item in mappings)
        assert all(item["herkomst"]["versie"] == "7fd4d02c3e5adebd379ebfbc824040820dde10fc" for item in mappings)

    assert verses[1]["text2026"] == "In het begin was het Woord, en het Woord was bij God, en het Woord was God."


def test_johannes_1_publiceert_ieder_tr_grondwoord_inline_ook_zonder_vertaling():
    data = json.loads((ROOT / "data" / "johannes" / "1.json").read_text(encoding="utf-8"))
    assert len(data["verses"]) == 52

    for verse in data["verses"]:
        ground = [str(word.get("strongs") or "") for word in verse.get("grondtekst", [])]
        mappings = verse.get("woordnummers", [])
        linked = [number for mapping in mappings for number in mapping.get("strongs", [])]
        assert ground, f"Johannes 1:{verse['number']} mist de TR-grondtekst"
        source_indices = [
            index for mapping in mappings
            for index in mapping.get("herkomst", {}).get("bronindices", [])
        ]
        assert Counter(linked) == Counter(ground), f"Johannes 1:{verse['number']} publiceert niet ieder TR-woord"
        assert len(source_indices) == len(ground)
        assert len(set(source_indices)) == len(source_indices), f"Johannes 1:{verse['number']} koppelt een TR-token dubbel"
        assert all(mapping.get("reviewstatus") == "handmatig_gecontroleerd" for mapping in mappings)
        assert all(mapping.get("herkomst", {}).get("dataset") == "robinson-scrivener-tr" for mapping in mappings)
        assert all(
            any("\u0370" <= char <= "\u03ff" for char in str(word.get("woord") or ""))
            for word in verse["grondtekst"]
            ), f"Johannes 1:{verse['number']} bevat geen eenduidige Griekse TR-woordvorm"


def test_johannes_1_onderscheidt_vertaalde_en_niet_afzonderlijk_vertaalde_tr_woorden():
    data = json.loads((ROOT / "data" / "johannes" / "1.json").read_text(encoding="utf-8"))
    verses = {int(verse["number"]): verse for verse in data["verses"]}

    def mapping(verse, source_index):
        return next(
            item for item in verses[verse]["woordnummers"]
            if source_index in item.get("herkomst", {}).get("bronindices", [])
        )

    assert mapping(14, 0)["tekst"] == "En"
    assert mapping(14, 0)["status"] == "vertaald"
    assert mapping(18, 5)["tekst"] == "eniggeboren Zoon"
    assert mapping(18, 5)["status"] == "vertaald"
    assert mapping(12, 5)["tekst"] == ""
    assert mapping(12, 5)["status"] == "niet_afzonderlijk_weergegeven"

    first_was = next(
        mapping for mapping in data["verses"][0]["woordnummers"]
        if mapping.get("tekst") == "was" and mapping.get("voorkomen") == 1
    )
    assert first_was["strongs"] == ["G2258"]
    assert first_was["lemma_strongs"] == ["G1510"]

    assert data["verses"][37]["text2026"].endswith("zei tot hen:")
    assert data["verses"][38]["text2026"].startswith("Wat zoekt u?")
    assert data["verses"][51]["grondtekst"][-1]["strongs"] == "G444"


def test_audit_reports_johannes_tr_coverage_and_valid_provenance():
    report = AUDIT.audit()

    assert report["inline_eligible_verses"] > report["verses_with_inline_mappings"]
    # Johannes 1:1-5 plus de gecontroleerde Izaäk-koppeling in Gebed van
    # Manasse 1 vormen samen de huidige, handmatig gereviewde basis.
    assert report["verses_with_inline_mappings"] >= 52
    assert report["inline_review_status"].get("handmatig_gecontroleerd", 0) >= 52
    assert not [item for item in report["invalid_inline"] if item.get("book") == "johannes"]
