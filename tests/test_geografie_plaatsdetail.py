"""Regressies voor de bronpagina van een geografische entiteit."""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "data" / "geografie-runtime.geojson"


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_elke_gepubliceerde_plaats_heeft_een_traceerbare_bron_en_verwijzingen():
    data = load(RUNTIME)
    for feature in data["features"]:
        props = feature["properties"]
        assert props["refs"]
        assert props["bron"]["dataset"]
        assert props["bron"]["url"].startswith("https://")


def test_plaatsdetail_toont_bron_alle_verwijzingen_en_terugkoppeling_naar_de_kaart():
    html = (ROOT / "plaats.html").read_text(encoding="utf-8")
    for fragment in (
        "data/geografie-runtime.geojson",
        "new URLSearchParams(window.location.search).get('plaats')",
        "Alle tekstverwijzingen",
        "Brongegevens",
        "kaart.html?plaats=",
        "feature.properties.id",
    ):
        assert fragment in html


def test_kaart_en_geografielijst_verwijzen_naar_de_eigen_bronpagina():
    kaart = (ROOT / "kaart.html").read_text(encoding="utf-8")
    lijst = (ROOT / "geografie.html").read_text(encoding="utf-8")
    assert "plaats.html?plaats=" in kaart
    assert "plaats.html?plaats=" in lijst
