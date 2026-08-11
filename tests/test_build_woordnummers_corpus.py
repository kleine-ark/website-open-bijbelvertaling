import importlib.util
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


def test_projectie_negeert_projecteigen_geez_en_latijnnummers():
    verse = {
        "number": 1,
        "text2026": "woord",
        "grondtekst": [
            {"woord": "woord", "strongs": "OVG123"},
            {"woord": "verbum", "strongs": "OVL456"},
        ],
    }

    result = MODULE.project_verse(verse, {}, True)

    assert result == {"mappings": [], "manual_links": 0, "visible_links": 0, "review_links": 0}


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

    assert report["corpus_projection"]["books"] == 88
    assert report["corpus_projection"]["automatic_visible_links"] == 226986
    assert report["corpus_projection"]["review_links"] == 292912
