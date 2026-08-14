import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from sweep_principe import koppel_bestaande_diff  # noqa: E402


def test_koppel_bestaande_diff_verfijnt_alleen_de_bedoelde_naamval():
    source = "Hij ziet den hemel en den dag."
    current = "Hij ziet de hemel en de dag."
    previous = [
        {"old": "den", "new": "de", "principe": "N1"},
        {"old": "den", "new": "de", "principe": "N1"},
    ]

    diff = koppel_bestaande_diff(
        source,
        current,
        previous,
        "N1b",
        re.compile(r"\bden hemel\b"),
    )

    assert [item["principe"] for item in diff] == ["N1b", "N1"]
