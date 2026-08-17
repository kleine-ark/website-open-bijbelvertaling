"""Regressietests voor consistente releasegegevens."""

import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_json(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def test_build_stats_defaults_follow_current_changelog():
    result = subprocess.run(
        [
            "python",
            "-c",
            (
                "import json; "
                "from scripts.build_stats import default_release_metadata; "
                "print(json.dumps(default_release_metadata()))"
            ),
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    version, datum = json.loads(result.stdout)
    release = read_json("data/changelog.json")["wijzigingen"][0]

    assert version == release["versie"]
    assert datum == "17 augustus 2026"


def service_worker_install_cache():
    script = r"""
const handlers = {};
global.self = {
  addEventListener: (name, handler) => { handlers[name] = handler; },
  skipWaiting: () => Promise.resolve(),
  clients: {
    claim: () => Promise.resolve(),
    matchAll: () => Promise.resolve([])
  },
  location: { origin: 'http://localhost' }
};
const opened = [];
global.caches = {
  open: async (name) => {
    opened.push(name);
    return { add: async () => undefined };
  },
  keys: async () => [],
  delete: async () => true
};
require('./sw.js');
let installation;
handlers.install({ waitUntil: (promise) => { installation = promise; } });
installation.then(() => process.stdout.write(JSON.stringify(opened)));
"""
    result = subprocess.run(
        ["node", "-e", script],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


def test_current_release_describes_talen_en_uses_one_version():
    stats = read_json("data/stats.json")
    changelog = read_json("data/changelog.json")
    current_release = changelog["wijzigingen"][0]
    descriptions = " ".join(item["beschrijving"] for item in current_release["items"])

    assert current_release["versie"] == "v0.38.0"
    assert "Inline Strongs" in descriptions
    assert stats["version"] == current_release["versie"]
    assert service_worker_install_cache() == [f"shell-{current_release['versie']}"]
    assert current_release["datum"] == "2026-08-17"
    assert stats["date"] == "17 augustus 2026"


def test_statische_release_fallbacks_verwijzen_naar_de_actuele_versie():
    """Ook vóór het laden van stats.json mag de site geen oud nummer tonen."""
    current = read_json("data/changelog.json")["wijzigingen"][0]["versie"]
    for bestand in ("over-ov.html", "statistieken.html"):
        inhoud = (ROOT / bestand).read_text(encoding="utf-8")
        assert current in inhoud
        assert "v0.21.6" not in inhoud


def test_human_review_statistics_include_nehemia_and_esther():
    stats = read_json("data/stats.json")
    verified = read_json("data/verified-chapters.json")

    assert stats["books_verified"] == 59
    assert stats["chapters_verified"] == 860
    assert stats["verses_verified"] == 23393
    assert stats["verses_verified_pct"] == 62.8
    assert "Numeri" in stats["verified_books"]
    assert "Deuteronomium" in stats["verified_books"]
    assert "Jozua" in stats["verified_books"]
    assert "Richteren" in stats["verified_books"]
    assert "2 Koningen" in stats["verified_books"]
    assert "Nehemia" in stats["verified_books"]
    assert "Esther" in stats["verified_books"]
    assert stats["ot_verses_verified"] == 14214
    assert stats["ot_verses_verified_pct"] == 61.2
    assert stats["nt_verses_verified"] == 7960
    assert stats["nt_verses_verified_pct"] == 100.0
    assert stats["ap_verses_verified"] == 1219
    assert stats["ap_verses_verified_pct"] == 20.1
    assert verified["numeri"] == "all"
    assert verified["deuteronomium"] == "all"
    assert verified["jozua"] == "all"
    assert verified["richteren"] == "all"
    assert verified["1samuel"] == "all"
    assert verified["2koningen"] == "all"
    assert verified["nehemia"] == "all"
    assert verified["mattheus"] == "all"
    assert verified["openbaring"] == "all"
    assert verified["psalmen"] == "all"
    assert verified["prediker"] == "all"
    for kleine_profeet in (
        "hosea", "joel", "amos", "obadja", "jona", "micha", "nahum",
        "habakuk", "zefanja", "haggai", "zacharia", "maleachi",
    ):
        assert verified[kleine_profeet] == "all"
    assert verified["1makkabeeen"] == "all"
    assert verified["baruch"] == "all"
    assert verified["gebedvanmanasse"] == "all"
    assert verified["susanna"] == "all"


def test_desktop_version_remains_independent():
    tauri = read_json("src-tauri/tauri.conf.json")

    assert tauri["version"] == "0.21.0"
