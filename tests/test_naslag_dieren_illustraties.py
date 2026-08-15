"""Regressies voor de gevalideerde dierillustraties in de wiki."""

import json
from pathlib import Path

from scripts.build_corpus_naslag import build_all


ROOT = Path(__file__).resolve().parents[1]


def test_dierenkaarten_tonen_vierkante_illustraties_vanaf_de_bovenkant():
    """De kop van een dier blijft zichtbaar in de brede overzichtstegel."""
    stylesheet = (ROOT / "css" / "naslag.css").read_text(encoding="utf-8")

    assert ".ns-kaart--dieren .ns-kaart-beeld" in stylesheet
    assert "object-position: center top" in stylesheet


def test_elke_dierkaart_heeft_een_korte_beschrijvingsregel():
    published = json.loads(
        (ROOT / "data" / "naslag-dieren.json").read_text(encoding="utf-8")
    )
    script = (ROOT / "js" / "naslag.js").read_text(encoding="utf-8")

    assert all(item["beschrijving"].strip() for item in published["items"])
    assert "ns-kaart-beschrijving" in script
    assert "eersteZin(it.beschrijving)" in script
    assert "d.titel === 'Dieren in de Bijbel'" in script
    assert all(
        "wordt als dier in de Bijbel genoemd" not in item["beschrijving"]
        for item in published["items"]
    )


def test_dierencatalogus_koppelt_elk_dier_aan_een_eigen_webbeeld():
    built = build_all(ROOT, write=False)["dieren"]

    assert len(built["items"]) == 94
    assert {
        item["afbeelding"] for item in built["items"]
    } == {
        f"images/wiki/dieren/{item['id']}.webp" for item in built["items"]
    }


def test_gepubliceerde_dierencatalogus_en_manifest_zijn_volledig_geintegreerd():
    published = json.loads(
        (ROOT / "data" / "naslag-dieren.json").read_text(encoding="utf-8")
    )
    manifest = json.loads(
        (ROOT / "images" / "wiki" / "manifests" / "dieren.json").read_text(encoding="utf-8")
    )

    images = [item["afbeelding"] for item in published["items"]]
    assert len(images) == 94
    assert len(set(images)) == len(images)
    assert all((ROOT / image).is_file() for image in images)
    assert {item["status"] for item in manifest["items"]} == {"integrated"}
