"""De kaart vermeldt eerlijk dat de gegevens nog worden gecontroleerd."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_kaart_toont_beta_en_controlestatus_bij_de_titel():
    page = (ROOT / "kaart.html").read_text(encoding="utf-8")
    stylesheet = (ROOT / "css" / "kaart.css").read_text(encoding="utf-8")

    assert 'class="kaart-status"' in page
    assert "Bèta" in page
    assert "nog te controleren" in page
    assert ".kaart-status" in stylesheet


def test_luchtfoto_is_de_standaard_achtergrondlaag():
    page = (ROOT / "kaart.html").read_text(encoding="utf-8")

    assert 'name="kaartlaag" value="lucht" checked' in page
    assert 'name="kaartlaag" value="kaart" checked' not in page
    assert "document.querySelector('input[name=\"kaartlaag\"]:checked')" in page
