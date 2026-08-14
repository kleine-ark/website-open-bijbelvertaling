"""Contract voor de compacte, klikbare boekdateringsbalk."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_boekdatering_heeft_geen_losse_handschriftenlink_meer():
    for source_name in ("js/app.js", "js/lees.js"):
        source = (ROOT / source_name).read_text(encoding="utf-8")
        assert "Handschriften van dit boek ›" not in source
        assert "dating-icon" in source


def test_schrijftijd_en_oudste_handschrift_zijn_zelf_de_link():
    for source_name in ("js/app.js", "js/lees.js"):
        source = (ROOT / source_name).read_text(encoding="utf-8")
        assert source.count('<a class="dating-link" href="${handschriftenUrl}"') >= 2
        assert '<span class="dating-label">Schrijftijd:</span>' in source
        assert '<span class="dating-label">Oudste handschrift:</span>' in source
