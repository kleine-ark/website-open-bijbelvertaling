"""Dekking en synchronisatie van de inhoudelijke psalmtitels."""

import json
from pathlib import Path

from scripts.update_psalm_liedtitels import PSALM_TITELS, volledige_titel


ROOT = Path(__file__).resolve().parents[1]


def test_alle_150_psalmen_hebben_een_eigen_inhoudelijke_titel():
    assert set(PSALM_TITELS) == set(range(1, 151))
    assert len(set(PSALM_TITELS.values())) == 150
    assert all(titel.strip() for titel in PSALM_TITELS.values())


def test_catalogus_en_detailbundels_gebruiken_dezelfde_psalmtitels():
    catalogus = json.loads(
        (ROOT / "data" / "naslag-liederen.json").read_text(encoding="utf-8")
    )
    psalmen = {
        int(item["id"].removeprefix("psalm-")): item
        for item in catalogus["items"]
        if item["id"].startswith("psalm-")
    }

    assert set(psalmen) == set(range(1, 151))
    for nummer, item in psalmen.items():
        verwacht = volledige_titel(nummer)
        assert item["naam"] == verwacht

        detail = json.loads(
            (ROOT / "data" / "naslag-teksten" / "liederen" / f"psalm-{nummer}.json").read_text(
                encoding="utf-8"
            )
        )
        assert detail["naam"] == verwacht
        assert detail["nummer"] == nummer + 11
