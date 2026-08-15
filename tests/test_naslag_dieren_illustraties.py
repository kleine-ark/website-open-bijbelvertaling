"""Regressies voor de gevalideerde dierillustraties in de wiki."""

import json
from pathlib import Path

from scripts.build_corpus_naslag import build_all


ROOT = Path(__file__).resolve().parents[1]


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
