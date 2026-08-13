"""Regressietest voor de materiaalillustraties in de wiki."""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_ieder_gepubliceerd_materiaal_heeft_een_eigen_webbeeld():
    published = json.loads(
        (ROOT / "data" / "naslag-materialen.json").read_text(encoding="utf-8")
    )

    items = published["items"]
    images = [item["afbeelding"] for item in items]

    assert len(images) == 59
    assert len(set(images)) == len(images)
    assert all(image.startswith("images/wiki/materialen/") for image in images)
    assert all((ROOT / image).is_file() for image in images)


def test_ieder_materiaal_heeft_een_korte_toelichting_en_wikipedia_link():
    published = json.loads(
        (ROOT / "data" / "naslag-materialen.json").read_text(encoding="utf-8")
    )

    for item in published["items"]:
        with_material_placeholder = "wordt als materiaal of stof in de Bijbel genoemd"
        assert item["beschrijving"].strip().endswith(".")
        assert len(item["beschrijving"].split()) >= 8
        assert with_material_placeholder not in item["beschrijving"]
        assert item["naam"].strip()
