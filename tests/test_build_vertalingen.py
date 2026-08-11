import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "build_vertalingen.py"


def load_builder():
    spec = importlib.util.spec_from_file_location("build_vertalingen", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_parse_usfm_preserves_structure_notes_crossrefs_and_strongs(tmp_path):
    builder = load_builder()
    source = tmp_path / "gen.usfm"
    source.write_text(
        "\\id GEN\n\\h Genesis\n\\c 1\n\\s1 Schepping\n\\p\n"
        "\\v 1 \\w In|strong=\"H7225\"\\w* het begin"
        "\\f + \\fr 1:1 \\ft Een noot.\\f*"
        "\\x a \\xo 1:1 \\xt Johannes 1:1.\\x*\n"
        "\\r Een structurele verwijzing die niet bij vers 1 hoort.\n"
        "\\q1 \\v 2 \\wj \\+w Een|strong=\"G1520\"\\+w* woord.\\wj*\n",
        encoding="utf-8",
    )

    chapters, warnings = builder.parse_usfm(source, "fr-lsg1910", "genesis")

    assert warnings == []
    chapter = chapters[1]
    assert chapter["kop"] == "Schepping"
    assert chapter["verzen"][0]["tekst"] == "In het begin"
    assert chapter["verzen"][0]["segmenten"] == [
        {"tekst": "In", "strong": ["H7225"]}
    ]
    assert chapter["verzen"][0]["voetnoten"][0]["tekst"] == "Een noot."
    assert chapter["verzen"][0]["kruisverwijzingen"][0]["tekst"] == "Johannes 1:1."
    assert any(block["type"] == "poezie" for block in chapter["blokken"])
    assert chapter["verzen"][1]["tekst"] == "Een woord."
    assert chapter["verzen"][1]["segmenten"] == [{"tekst": "Een", "strong": ["G1520"]}]


def test_convert_all_writes_utf8_manifest_report_and_is_idempotent(tmp_path):
    builder = load_builder()
    sources = tmp_path / "bronbestanden" / "vertalingen"
    usfm = sources / "fraLSG" / "usfm"
    usfm.mkdir(parents=True)
    (usfm / "02-GENfraLSG.usfm").write_text(
        "\\id GEN\n\\h Genèse\n\\c 1\n\\s1 Création\n\\v 1 Au commencement.\n",
        encoding="utf-8",
    )
    output = tmp_path / "data" / "vertalingen"

    report1 = builder.convert_all(sources, output, editions=("fr-lsg1910",))
    first = (output / "fr-lsg1910" / "genesis" / "1.json").read_bytes()
    report2 = builder.convert_all(sources, output, editions=("fr-lsg1910",))

    assert report1 == report2
    assert first == (output / "fr-lsg1910" / "genesis" / "1.json").read_bytes()
    assert "Création" in first.decode("utf-8")
    manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["edities"][0]["code"] == "fr-lsg1910"
    assert manifest["edities"][0]["boeken"] == ["genesis"]
    assert report1["edities"]["fr-lsg1910"]["verzen"] == 1


def test_standard_book_codes_match_open_vertaling_ids():
    builder = load_builder()
    assert builder.BOOK_IDS["GEN"] == "genesis"
    assert builder.BOOK_IDS["JHN"] == "johannes"
    assert builder.BOOK_IDS["PSA"] == "psalmen"
    assert builder.BOOK_IDS["TOB"] == "tobit"
    assert builder.BOOK_IDS["1CO"] == "1korinthiers"
    assert builder.BOOK_IDS["1TH"] == "1tessalonicensen"
    assert "4MA" not in builder.BOOK_IDS


def test_ukrainian_freedom_bible_is_registered_as_a_public_domain_edition():
    builder = load_builder()
    edition = builder.EDITIONS["uk-ukrfb"]

    assert edition["source"] == "ukrfb"
    assert edition["name"] == "Ukrainian Freedom Bible"
    assert edition["language"] == "uk"
    assert edition["direction"] == "ltr"


def test_german_luther_1912_is_registered_as_a_public_domain_edition():
    builder = load_builder()
    edition = builder.EDITIONS["de-luther1912"]

    assert edition["source"] == "deu1912"
    assert edition["name"] == "Lutherbibel 1912"
    assert edition["language"] == "de"
    assert edition["direction"] == "ltr"


def test_polish_gdansk_is_registered_as_a_public_domain_full_bible():
    builder = load_builder()
    edition = builder.EDITIONS["pl-gdanska1881"]

    assert edition["source"] == "pol-gdanska"
    assert edition["name"] == "Biblia Gdańska 1881"
    assert edition["language"] == "pl"
    assert edition["rights"] == "publiek domein"


def test_turkish_open_basic_is_registered_as_a_cc_by_sa_new_testament():
    builder = load_builder()
    edition = builder.EDITIONS["tr-open-basic-nt"]

    assert edition["source"] == "tur-open-basic-nt"
    assert edition["language"] == "tr"
    assert edition["rights"] == "CC BY-SA 4.0"
    assert edition["scope"] == "Nieuwe Testament"


def test_every_published_manifest_book_exists_in_site_manifest():
    site_ids = {
        book["id"]
        for book in json.loads((ROOT / "data" / "books.json").read_text(encoding="utf-8"))["books"]
    }
    translations = json.loads(
        (ROOT / "data" / "vertalingen" / "manifest.json").read_text(encoding="utf-8")
    )
    published = {
        book_id
        for edition in translations["edities"]
        for book_id in edition["boeken"]
    }
    assert published <= site_ids
