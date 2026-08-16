"""Regressies voor de geïllustreerde uitleg bij Bijbelse maateenheden."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_maatgroepen_hebben_hoogwaardige_rasterillustraties():
    page = (ROOT / "maateenheden.html").read_text(encoding="utf-8")

    for slug, alt in {
        "lengte": "Lengtematen: el, span, handbreed en riet",
        "inhoud": "Inhoudsmaten: graan- en vloeistofvaten",
        "gewicht": "Gewichten: balans, stenen gewichten en talent",
        "geld": "Bijbelse munten en geldwaarden",
    }.items():
        assert f'images/wiki/maateenheden/{slug}.webp' in page
        assert alt in page
        assert (ROOT / "images" / "wiki" / "maateenheden" / f"{slug}.webp").is_file()


def test_illustraties_vormen_een_responsieve_educatieve_kaart():
    page = (ROOT / "maateenheden.html").read_text(encoding="utf-8")

    assert page.count('class="me-illustratie"') == 4
    assert 'class="me-illustratie-tekst"' in page
    assert 'object-fit: cover' in page
    assert '@media (max-width: 620px)' in page


def test_maatgewicht_en_munten_hebben_detailillustraties():
    page = (ROOT / "maateenheden.html").read_text(encoding="utf-8")

    slugs = (
        "el", "span", "riet", "stadie",
        "homer-kor", "efa", "bath", "hin",
        "talent", "sikkel", "beka", "gera",
        "penning", "zilverling", "drachme", "stater", "oort",
    )

    for slug in slugs:
        assert f'images/wiki/maateenheden/{slug}.webp' in page
        assert (ROOT / "images" / "wiki" / "maateenheden" / f"{slug}.webp").is_file()

    assert page.count('class="me-detailgalerij"') == 4
    assert page.count('class="me-detailkaart"') == len(slugs)
