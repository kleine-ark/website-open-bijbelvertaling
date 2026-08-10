"""Bronnen hoort bij de wiki en mag geen legacy-navigatie openen."""

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(name: str) -> str:
    return (ROOT / name).read_text(encoding="utf-8")


def test_bronnen_staat_in_de_wiki_en_de_hoofdpagina_linkt_naar_die_route():
    wiki = read("wiki.html")
    over_ov = read("over-ov.html")

    assert 'href="#bronnen" data-page="bronnen.html"' in wiki
    assert 'href="wiki.html#bronnen"' in over_ov


def test_geen_interne_pagina_linkt_rechtstreeks_naar_de_legacy_bronnenpagina():
    overtredingen = []
    patroon = re.compile(r'href=["\'](?:/)?bronnen\.html(?:[?#][^"\']*)?["\']')

    for path in ROOT.glob("*.html"):
        if path.name == "bronnen.html":
            continue
        if patroon.search(path.read_text(encoding="utf-8")):
            overtredingen.append(path.name)

    assert overtredingen == []


def test_legacy_url_stuurt_topniveau_naar_de_wiki_maar_blijft_inbedbaar():
    bronnen = read("bronnen.html")

    assert "window.self === window.top" in bronnen
    assert "wiki.html#bronnen" in bronnen
    assert "location.replace" in bronnen
    assert 'classList.add("ov-ingebed")' in bronnen


def test_bronnenlijst_beschrijft_ook_de_huidige_vertalingen_en_geografiebron():
    bronnen = read("bronnen.html")

    for naam in (
        "Louis Segond 1910",
        "World English Bible British Edition",
        "Arabic Van Dyck",
        "Reina-Valera 1909",
        "OpenBible.info Bible Geocoding Data",
    ):
        assert naam in bronnen

    assert "CC0 / publiek domein" in bronnen
    assert "niet-commercieel" not in bronnen.lower()


def test_interne_html_links_in_bronnen_verlaten_het_wikiframe():
    bronnen = read("bronnen.html")
    interne_links = re.findall(r"<a\b[^>]*href=[\"'](?!https?://|mailto:|#)([^\"']+\.html(?:[?#][^\"']*)?)[\"'][^>]*>", bronnen)

    assert interne_links
    for href in interne_links:
        tag = re.search(
            rf"<a\b[^>]*href=[\"']{re.escape(href)}[\"'][^>]*>", bronnen
        ).group(0)
        assert 'target="_top"' in tag


def test_machineleesbare_bestanden_openen_niet_binnen_het_wikiframe():
    bronnen = read("bronnen.html")
    bestandslinks = re.findall(
        r"<a\b[^>]*href=[\"'](?!https?://|mailto:|#)([^\"']+\.(?:json|txt))[\"'][^>]*>",
        bronnen,
    )

    assert bestandslinks
    for href in bestandslinks:
        tag = re.search(
            rf"<a\b[^>]*href=[\"']{re.escape(href)}[\"'][^>]*>", bronnen
        ).group(0)
        assert 'target="_blank"' in tag
