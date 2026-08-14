import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "build_woordnummers_corpus", ROOT / "scripts" / "build_woordnummers_corpus.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

AUDIT_SPEC = importlib.util.spec_from_file_location(
    "audit_woordnummers_corpus", ROOT / "scripts" / "audit_woordnummers.py"
)
AUDIT = importlib.util.module_from_spec(AUDIT_SPEC)
AUDIT_SPEC.loader.exec_module(AUDIT)


def test_exact_dutch_lexicon_match_becomes_visible_high_confidence_mapping():
    verse = {
        "number": 1,
        "text2026": "In het begin schiep God.",
        "grondtekst": [
            {"woord": "בְּרֵאשִׁית", "strongs": "H7225", "transliteratie": "bereshit"},
            {"woord": "בָּרָא", "strongs": "H1254", "transliteratie": "bara"},
        ],
    }
    lexicon = {
        "H7225": {"glossNl": "begin, aanvang"},
        "H1254": {"glossNl": "scheppen, schiep"},
    }

    result = MODULE.project_verse(verse, lexicon, chapter_verified=True)

    assert result["visible_links"] == 2
    assert result["review_links"] == 0
    assert [item["tekst"] for item in result["mappings"]] == ["begin", "schiep"]
    assert all(item["reviewstatus"] == "automatisch_hoog_vertrouwen" for item in result["mappings"])
    assert all(item["confidence"] == 0.95 for item in result["mappings"])


def test_unmatched_or_unverified_projection_stays_in_review_queue():
    verse = {
        "number": 1,
        "text2026": "Een onbekend woord.",
        "grondtekst": [{"woord": "λόγος", "strongs": "G3056"}],
    }

    unmatched = MODULE.project_verse(verse, {"G3056": {"glossNl": "spraak"}}, True)
    unverified = MODULE.project_verse(verse, {"G3056": {"glossNl": "woord"}}, False)

    assert unmatched["visible_links"] == 0
    assert unmatched["review_links"] == 1
    assert unmatched["mappings"][0]["reviewstatus"] == "review_nodig"
    assert unverified["visible_links"] == 0
    assert unverified["review_links"] == 1


def test_lexicon_summary_does_not_create_an_anchor_for_a_related_name():
    verse = {
        "number": 1,
        "text2026": "Abraham en Izaäk.",
        "grondtekst": [{"woord": "Ισαακ", "strongs": "G2464"}],
    }
    lexicon = {
        "G2464": {
            "glossNl": "Izak",
            "samenvattingNl": "Izak, de patriarch, zoon van Abraham",
        }
    }

    result = MODULE.project_verse(verse, lexicon, chapter_verified=True)

    assert result["visible_links"] == 0
    assert result["review_links"] == 1


def test_secondary_words_in_a_lexicon_gloss_do_not_create_a_spurious_anchor():
    """Een uitlegwoord mag nooit een Strong achter een ander Nederlands woord zetten."""
    verse = {
        "number": 24,
        "text2026": "Jozef dan, opgewekt zijnde van de slaap.",
        "grondtekst": [{"woord": "Ἐγερθεὶς", "strongs": "G1453"}],
    }
    lexicon = {
        "G1453": {"glossNl": "wekken, opwekken uit de slaap"},
    }

    result = MODULE.project_verse(verse, lexicon, chapter_verified=True)

    assert result["visible_links"] == 0
    assert result["review_links"] == 1
    assert result["mappings"][0]["tekst"] == "Jozef"
    assert result["mappings"][0]["reviewstatus"] == "review_nodig"


def test_projectie_negeert_latijnse_projectnummers_maar_toont_een_exact_geez_anker():
    verse = {
        "number": 1,
        "text2026": "woord",
        "grondtekst": [
            {"woord": "woord", "strongs": "OVG123", "betekenis": "woord"},
            {"woord": "verbum", "strongs": "OVL456"},
        ],
    }

    result = MODULE.project_verse(verse, {}, True)

    assert result["visible_links"] == 1
    assert result["review_links"] == 0
    assert result["mappings"] == [{
        "tekst": "woord",
        "voorkomen": 1,
        "strongs": ["OVG123"],
        "bronwoorden": ["woord"],
        "transliteraties": [""],
        "glossen": ["woord"],
        "confidence": 0.95,
        "reviewstatus": "automatisch_hoog_vertrouwen",
    }]


def test_geez_woordnummer_blijft_alleen_zichtbaar_bij_exacte_nederlandse_betekenis():
    verse = {
        "number": 1,
        "text2026": "Een onbekende zegen.",
        "grondtekst": [{"woord": "\u1260\u1228\u12a8\u1275", "strongs": "OVG3907", "betekenis": "zegen"}],
    }

    result = MODULE.project_verse(verse, {}, False)

    assert result["visible_links"] == 1
    assert result["mappings"][0]["tekst"] == "zegen"


def test_existing_manual_anchor_wins_over_generated_mapping():
    verse = {
        "number": 1,
        "text2026": "In het begin.",
        "grondtekst": [{"woord": "ἀρχῇ", "strongs": "G746"}],
        "woordnummers": [{
            "tekst": "begin", "voorkomen": 1, "strongs": ["G746"],
            "reviewstatus": "handmatig_gecontroleerd",
        }],
    }

    result = MODULE.project_verse(verse, {"G746": {"glossNl": "begin"}}, True)

    assert result["manual_links"] == 1
    assert result["visible_links"] == 0
    assert result["mappings"] == []


def test_manual_number_is_not_projected_again_when_lexicon_match_is_missing():
    verse = {
        "number": 1,
        "text2026": "In het begin.",
        "grondtekst": [{"woord": "ἀρχῇ", "strongs": "G746"}],
        "woordnummers": [{
            "tekst": "begin", "voorkomen": 1, "strongs": ["G746"],
            "reviewstatus": "handmatig_gecontroleerd",
        }],
    }

    result = MODULE.project_verse(verse, {}, True)

    assert result == {"mappings": [], "manual_links": 1, "visible_links": 0, "review_links": 0}


def test_gebed_van_manasse_isaak_keeps_g2464_after_izaak_on_rebuild():
    """De gecorrigeerde Nederlandse naam blijft een handmatig anker bij herbouw."""
    chapter = json.loads(
        (ROOT / "data" / "gebedvanmanasse" / "1.json").read_text(encoding="utf-8")
    )
    verse = chapter["verses"][0]
    manual = verse.get("woordnummers", [])
    lexicon = json.loads((ROOT / "data" / "lexicon-nl" / "abbott-nl.json").read_text(encoding="utf-8"))

    mapping = next(item for item in manual if item.get("strongs") == ["G2464"])
    assert mapping["tekst"] == "Izaäk"
    assert mapping["voorkomen"] == 1
    assert mapping["reviewstatus"] == "handmatig_gecontroleerd"
    assert mapping["confidence"] == 1.0
    assert mapping["herkomst"]["bronindices"] == [10]
    projection = MODULE.project_verse(verse, lexicon, chapter_verified=True)
    assert projection["manual_links"] == 1
    assert all("G2464" not in mapping["strongs"] for mapping in projection["mappings"])


def test_status_markdown_reports_visible_and_review_links_per_book():
    status = {
        "books": {
            "genesis": {
                "phase": "nagekeken_tekst", "eligible_verses": 10,
                "visible_verses": 9, "source_links": 100,
                "manual_links": 2, "automatic_visible_links": 70, "review_links": 28,
            }
        }
    }

    markdown = MODULE.status_markdown(status)

    assert "| genesis | nagekeken_tekst | 9/10 | 2 | 70 | 28 | 72,00% |" in markdown


def test_audit_includes_generated_corpus_projection_status():
    report = AUDIT.audit()
    status = json.loads((ROOT / "data" / "woordnummers-inline" / "status.json").read_text(encoding="utf-8"))
    expected_visible = sum(
        item.get("automatic_visible_links", 0) for item in status["books"].values()
    )
    expected_review = sum(
        item.get("review_links", 0) for item in status["books"].values()
    )

    assert report["corpus_projection"]["books"] == 88
    assert report["corpus_projection"]["automatic_visible_links"] == expected_visible
    assert report["corpus_projection"]["review_links"] == expected_review


def test_johannes_shows_no_unreviewed_automatic_inline_projection():
    """Johannes blijft bij de eerste handmatige audit vrij van gokwerk.

    De Griekse woordvolgorde en Nederlandse woordvolgorde lopen geregeld uiteen.
    Tot een vers handmatig is gecontroleerd, mogen alleen de mappings in het
    eigen versbestand zichtbaar zijn; de gegenereerde boekprojectie blijft leeg.
    """
    mapping_book = json.loads(
        (ROOT / "data" / "woordnummers-inline" / "johannes.json").read_text(encoding="utf-8")
    )

    assert mapping_book["chapters"] == {}
