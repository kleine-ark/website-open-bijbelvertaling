"""Regressies voor de bomen- en plantenillustraties in de wiki."""

import json
from pathlib import Path

from scripts.build_corpus_naslag import build_all


ROOT = Path(__file__).resolve().parents[1]


def test_bomen_en_planten_koppelen_ieder_item_aan_een_eigen_webbeeld():
    built = build_all(ROOT, write=False)["bomen-planten"]

    assert len(built["items"]) == 71
    assert {
        item["afbeelding"] for item in built["items"]
    } == {
        f"images/wiki/bomen-planten/{item['id']}.webp"
        for item in built["items"]
    }


def test_gepubliceerde_catalogus_bevat_alle_beelden_en_omschrijvingen():
    published = json.loads(
        (ROOT / "data" / "naslag-bomen-planten.json").read_text(encoding="utf-8")
    )
    manifest = json.loads(
        (ROOT / "images" / "wiki" / "manifests" / "bomen-planten.json").read_text(
            encoding="utf-8"
        )
    )

    images = [item["afbeelding"] for item in published["items"]]
    assert len(images) == 71
    assert len(set(images)) == len(images)
    assert all((ROOT / image).is_file() for image in images)
    assert all(len(item["beschrijving"].split()) >= 8 for item in published["items"])
    assert {item["status"] for item in manifest["items"]} == {"integrated"}
