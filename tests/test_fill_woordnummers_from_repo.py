import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "fill_woordnummers_from_repo", ROOT / "scripts" / "fill_woordnummers_from_repo.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

AUDIT_SPEC = importlib.util.spec_from_file_location(
    "audit_woordnummers", ROOT / "scripts" / "audit_woordnummers.py"
)
AUDIT = importlib.util.module_from_spec(AUDIT_SPEC)
AUDIT_SPEC.loader.exec_module(AUDIT)


def test_build_exact_index_keeps_only_unambiguous_compatible_numbers():
    tokens = [
        {"woord": "λόγος", "strongs": "G3056"},
        {"woord": "λόγος", "strongs": "G3056"},
        {"woord": "Ἰερουσαλήμ", "strongs": "G2414"},
        {"woord": "Ἰερουσαλήμ", "strongs": "G2419"},
        {"woord": "ቃለ", "strongs": "OVG3174"},
        {"woord": "verbum", "strongs": "OVL0001"},
        {"woord": "ב֖/וֹ", "strongs": "H871"},
    ]

    index, ambiguous = MODULE.build_exact_index(tokens)

    assert index == {
        ("greek", "λόγος"): "G3056",
        ("geez", "ቃለ"): "OVG3174",
        ("latin", "verbum"): "OVL0001",
    }
    assert ambiguous == {("greek", "Ἰερουσαλήμ"): ["G2414", "G2419"]}


def test_propose_fill_requires_exact_surface_form_and_expected_family():
    index = {
        ("greek", "λόγος"): "G3056",
        ("geez", "ቃለ"): "OVG3174",
        ("latin", "verbum"): "OVL0001",
    }

    assert MODULE.propose_fill({"woord": "λόγος"}, index) == "G3056"
    assert MODULE.propose_fill({"woord": "ቃለ"}, index) == "OVG3174"
    assert MODULE.propose_fill({"woord": "verbum"}, index) == "OVL0001"
    assert MODULE.propose_fill({"woord": "Λόγος"}, index) is None
    assert MODULE.propose_fill({"woord": "ב֖/וֹ", "morph": "HR/Sp3ms"}, index) is None
    assert MODULE.propose_fill({"woord": "1:1"}, index) is None
    assert MODULE.propose_fill({"woord": "..."}, index) is None
    assert MODULE.propose_fill({"woord": "λόγος", "strongs": "G3056"}, index) is None


def test_dump_json_like_preserves_indent_and_line_endings():
    source = '{\r\n "number": 1,\r\n "verses": []\r\n}\r\n'

    rendered = MODULE.dump_json_like({"number": 1, "verses": []}, source)

    assert rendered == source


def test_audit_classificeert_bewust_ongenummerde_brontokens():
    assert AUDIT.classify_unnumbered({"woord": "לָ/הֶם", "morph": "HR/Sp3mp"}) == "hebrew_grammatical_segment"
    assert AUDIT.classify_unnumbered({"woord": "σταγόνας"}) == "greek_unmapped_lexeme"
    assert AUDIT.classify_unnumbered({"woord": "እኩያን"}) == "geez_unmapped_lexeme"
    assert AUDIT.classify_unnumbered({"woord": "verbum"}) == "latin_unmapped_lexeme"
    assert AUDIT.classify_unnumbered({"woord": "1:1"}) == "non_lexical_source_marker"


def _verse(book, chapter, number):
    data = __import__("json").loads(
        (ROOT / "data" / book / f"{chapter}.json").read_text(encoding="utf-8")
    )
    return next(verse for verse in data["verses"] if verse["number"] == number)


def test_corpus_bevat_de_bronvaste_griekse_en_geez_aanvullingen():
    greek = next(
        token for token in _verse("1makkabeeen", 1, 1)["grondtekst"]
        if token["woord"] == "Μήδων"
    )
    geez = next(
        token for token in _verse("1meqabyan", 1, 1)["grondtekst"]
        if token["woord"] == "እዴሁ"
    )

    assert greek["strongs"] == "G3370"
    assert geez["strongs"] == "OVG5872"


def test_droge_run_vindt_geen_resterende_eenduidige_exacte_koppelingen():
    assert MODULE.fill_corpus(write=False)["filled"] == 0
