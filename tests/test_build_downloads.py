"""Tests voor scripts/build_downloads.py.

Draaien:  python -m pytest tests/test_build_downloads.py -q

Vereist dat de downloads al gebouwd zijn:
    python scripts/build_downloads.py
"""
import json
import os
import re
import zipfile
import xml.etree.ElementTree as ET

import pytest

WORTEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UIT = os.path.join(WORTEL, "downloads")
EPUB = os.path.join(UIT, "open-vertaling-nagekeken.epub")
ZIP = os.path.join(UIT, "open-vertaling-brondata.zip")
INDEX = os.path.join(UIT, "index.json")

pytestmark = pytest.mark.skipif(
    not os.path.exists(EPUB),
    reason="downloads nog niet gebouwd — draai eerst scripts/build_downloads.py",
)


@pytest.fixture(scope="module")
def epub():
    with zipfile.ZipFile(EPUB) as z:
        yield z


@pytest.fixture(scope="module")
def verified():
    with open(os.path.join(WORTEL, "data", "verified-chapters.json"), encoding="utf-8") as fh:
        return json.load(fh)


def test_bestanden_bestaan():
    for pad in (EPUB, ZIP, INDEX):
        assert os.path.exists(pad), f"ontbreekt: {pad}"
        assert os.path.getsize(pad) > 0


def test_mimetype_eerst_en_ongecomprimeerd(epub):
    """De EPUB-standaard eist dit; e-readers weigeren het bestand anders."""
    eerste = epub.infolist()[0]
    assert eerste.filename == "mimetype"
    assert eerste.compress_type == zipfile.ZIP_STORED
    assert epub.read("mimetype").decode() == "application/epub+zip"


def test_verplichte_onderdelen_aanwezig(epub):
    namen = set(epub.namelist())
    for nodig in ("META-INF/container.xml", "OEBPS/content.opf",
                  "OEBPS/nav.xhtml", "OEBPS/colofon.xhtml"):
        assert nodig in namen, f"ontbreekt in EPUB: {nodig}"


def test_xml_is_welgevormd(epub):
    for naam in epub.namelist():
        if naam.endswith((".xhtml", ".opf", ".xml")):
            ET.fromstring(epub.read(naam))


def test_alleen_nagekeken_hoofdstukken(epub, verified):
    """Genesis is deels nagekeken: 1 t/m 20 wel, 21 en verder niet."""
    gen = verified["genesis"]
    assert gen != "all", "test gaat ervan uit dat Genesis deels nagekeken is"
    hoogste = max(gen)
    inhoud = epub.read("OEBPS/genesis.xhtml").decode("utf-8")
    koppen = set(re.findall(r'<h2 id="h(\d+)">', inhoud))
    assert str(hoogste) in koppen, f"Genesis {hoogste} hoort erin te staan"
    assert str(hoogste + 1) not in koppen, f"Genesis {hoogste + 1} is niet nagekeken"
    for nr in koppen:
        assert int(nr) in gen, f"Genesis {nr} staat erin maar is niet nagekeken"


def test_inhoudsopgave_verwijst_alleen_naar_bestaande_bestanden(epub):
    nav = epub.read("OEBPS/nav.xhtml").decode("utf-8")
    namen = set(epub.namelist())
    for href in re.findall(r'href="([^"#]+)', nav):
        assert f"OEBPS/{href}" in namen, f"inhoudsopgave verwijst naar ontbrekend {href}"


def test_manifest_dekt_alle_documenten(epub):
    opf = epub.read("OEBPS/content.opf").decode("utf-8")
    hrefs = set(re.findall(r'<item[^>]+href="([^"]+)"', opf))
    for naam in epub.namelist():
        if naam.startswith("OEBPS/") and naam.endswith(".xhtml"):
            kort = naam[len("OEBPS/"):]
            assert kort in hrefs, f"{kort} zit niet in het manifest"


def test_geen_site_opmaak_in_de_tekst(epub):
    """Kanttekening-markers en Strong's-spans horen niet in een leesuitgave."""
    inhoud = epub.read("OEBPS/genesis.xhtml").decode("utf-8")
    for rest in ("note-marker", "strongs-inline", "geo-locatie", "<sup"):
        assert rest not in inhoud, f"site-opmaak lekt door in de EPUB: {rest}"


def test_licentie_in_colofon(epub):
    colofon = epub.read("OEBPS/colofon.xhtml").decode("utf-8")
    assert "CC0" in colofon


def test_index_klopt_met_de_bestanden():
    with open(INDEX, encoding="utf-8") as fh:
        index = json.load(fh)
    assert index["uitgaven"], "index.json noemt geen uitgaven"
    for u in index["uitgaven"]:
        pad = os.path.join(UIT, u["bestand"])
        assert os.path.exists(pad), f"index noemt ontbrekend bestand {u['bestand']}"
        assert u["bytes"] == os.path.getsize(pad), f"omvang klopt niet voor {u['bestand']}"
        assert u["omschrijving"].strip()


def test_zip_bevat_de_brondata():
    with zipfile.ZipFile(ZIP) as z:
        namen = z.namelist()
    assert any(n.endswith("data/books.json") or n.endswith("data\\books.json") for n in namen)
    hoofdstukken = [n for n in namen if re.search(r"data[\\/]genesis[\\/]\d+\.json$", n)]
    assert len(hoofdstukken) >= 50, "niet alle Genesis-hoofdstukken zitten in de zip"
