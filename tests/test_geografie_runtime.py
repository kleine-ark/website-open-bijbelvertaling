"""De kaart gebruikt één compacte geografische runtime-index."""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "data" / "geografie-runtime.geojson"


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_runtime_publiceert_de_brede_inventaris_en_niet_alleen_legacy():
    data = load(RUNTIME)
    meta = data["metadata"]
    assert data["type"] == "FeatureCollection"
    assert meta["punten"] == len(data["features"])
    assert meta["punten"] > 1000
    assert meta["verwijzingen"] > 8000
    assert meta["boekenMetPunten"] >= 60
    assert meta["humanReviewed"] is False
    assert set(meta["perZekerheid"]) == {"zeker", "waarschijnlijk", "onzeker"}
    assert meta["perZekerheid"]["onzeker"] > 0


def test_runtime_ids_punten_en_verwijzingen_zijn_valide():
    data = load(RUNTIME)
    ids = [feature["properties"]["id"] for feature in data["features"]]
    assert len(ids) == len(set(ids))
    refs = 0
    for feature in data["features"]:
        lon, lat = feature["geometry"]["coordinates"]
        assert -180 <= lon <= 180
        assert -90 <= lat <= 90
        props = feature["properties"]
        assert props["zekerheid"] in {"zeker", "waarschijnlijk", "onzeker"}
        assert props["humanReviewed"] is False
        assert props["refs"]
        refs += len(props["refs"])
        for ref in props["refs"]:
            assert ref["status"] in {"agent-reviewed", "needs-human-review"}
            assert ref["href"] == f"index.html#{ref['boek']}/{ref['hoofdstuk']}/{ref['vers']}"
    assert refs == data["metadata"]["verwijzingen"]


def test_torah_en_buiten_torah_zijn_op_dezelfde_kaart_ontsloten():
    per_book = load(RUNTIME)["metadata"]["perBoek"]
    for book in ("genesis", "exodus", "leviticus", "numeri", "deuteronomium"):
        assert per_book[book] > 0
    for book in ("jozua", "psalmen", "mattheus", "johannes", "handelingen", "openbaring"):
        assert per_book[book] > 0


def test_onbevestigde_extra_corpuskandidaten_worden_gerapporteerd_niet_geclaimd():
    excluded = load(RUNTIME)["metadata"]["uitgesloten"]
    assert excluded["apocrief-of-ethiopisch-naamskandidaat-zonder-bevestigde-puntkoppeling"] > 0


def test_kaart_heeft_boek_hoofdstuk_en_zekerheidfilters_met_deelbare_url():
    html = (ROOT / "kaart.html").read_text(encoding="utf-8")
    assert "data/geografie-runtime.geojson" in html
    assert 'id="f-boek"' in html
    assert 'id="f-hoofdstuk"' in html
    assert 'name="hoofdstuk" disabled' in html
    assert "searchParams.set('boek'" in html
    assert "searchParams.set('hoofdstuk'" in html
    assert "get('plaats')" in html
    assert 'id="f-waarschijnlijk" checked' in html
    assert 'id="f-onzeker" checked' in html


def test_geografielijst_gebruikt_dezelfde_canonieke_index():
    html = (ROOT / "geografie.html").read_text(encoding="utf-8")
    assert "data/geografie-runtime.geojson" in html
    assert "data/geografie-concept.json" not in html
