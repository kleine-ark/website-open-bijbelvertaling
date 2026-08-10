from pathlib import Path

from bs4 import BeautifulSoup


ROOT = Path(__file__).resolve().parents[1]


def wiki_groups():
    html = (ROOT / "wiki.html").read_text(encoding="utf-8")
    soup = BeautifulSoup(html, "html.parser")
    return {
        group.get("data-groep"): {
            "title": group.select_one(".wiki-groep-kop").get_text(" ", strip=True),
            "links": [link.get_text(" ", strip=True) for link in group.select("a[data-page]")],
            "pages": [link.get("data-page") for link in group.select("a[data-page]")],
        }
        for group in soup.select(".wiki-groep")
    }


def test_wiki_begint_met_een_compacte_inhoudsgroep():
    groups = wiki_groups()

    assert groups["inhoud"]["title"] == "Inhoud"
    assert groups["inhoud"]["links"] == [
        "Onderwerpen",
        "Woordenboek",
        "Liederen",
        "Gebeden",
        "Kaart",
        "Personen en stambomen",
    ]


def test_de_wereld_van_het_oosten_bevat_de_inhoudelijke_naslag():
    groups = wiki_groups()

    assert groups["oosten"]["title"] == "De wereld van het Oosten"
    for page in (
        "personen.html",
        "volken-naties.html",
        "geografie.html",
        "maateenheden.html",
        "tijdsaanduidingen.html",
        "materialen.html",
        "dieren.html",
        "bomen-planten.html",
        "muziekinstrumenten.html",
    ):
        assert page in groups["oosten"]["pages"]


def test_dubbele_ingangen_gebruiken_unieke_hashes_maar_dezelfde_pagina():
    html = (ROOT / "wiki.html").read_text(encoding="utf-8")
    soup = BeautifulSoup(html, "html.parser")
    person_links = soup.select('a[data-page="personen.html"]')

    assert len(person_links) == 2
    assert {link.get("href") for link in person_links} == {
        "#personen",
        "#personen-en-stambomen",
    }
