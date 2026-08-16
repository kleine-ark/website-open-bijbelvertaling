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
        "handbreed", "vinger", "vadem", "schrede", "mijl", "sabbatsreis", "dagreis",
        "homer-kor", "efa", "bath", "sea", "hin", "gomer", "kab", "log", "metreet", "korenmaat", "maatje",
        "talent", "pond", "sikkel", "beka", "gera",
        "penning", "zilverling", "drachme", "stater", "oort",
        "uur", "nachtwake",
    )

    for slug in slugs:
        assert f'images/wiki/maateenheden/{slug}.webp' in page
        assert (ROOT / "images" / "wiki" / "maateenheden" / f"{slug}.webp").is_file()

    assert page.count('class="me-detailgalerij"') == 5
    assert page.count('class="me-detailkaart"') == len(slugs)
    assert 'aspect-ratio: 1' in page
    assert 'grid-template-rows: minmax(0, 1fr) auto' in page
