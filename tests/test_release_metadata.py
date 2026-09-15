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
    assert datum == "22 augustus 2026"


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


def test_current_release_describes_review_en_uses_one_version():
    stats = read_json("data/stats.json")
    changelog = read_json("data/changelog.json")
    current_release = changelog["wijzigingen"][0]
    descriptions = " ".join(item["beschrijving"] for item in current_release["items"])

    assert current_release["versie"] == "v0.38.2"
    assert "volledige woordenboekartikel" in descriptions
    assert stats["version"] == current_release["versie"]
    assert service_worker_install_cache() == [f"shell-{current_release['versie']}-verification-v8"]
    assert current_release["datum"] == "2026-08-22"
    assert stats["date"] == "22 augustus 2026"


def test_statische_release_fallbacks_verwijzen_naar_de_actuele_versie():
    """Ook vóór het laden van stats.json mag de site geen oud nummer tonen."""
    current = read_json("data/changelog.json")["wijzigingen"][0]["versie"]
    for bestand in ("over-ov.html", "statistieken.html"):
        inhoud = (ROOT / bestand).read_text(encoding="utf-8")
        assert current in inhoud
        assert "v0.21.6" not in inhoud


def test_verification_snapshot_is_generated_from_the_api_not_hand_maintained():
    source = (ROOT / "scripts/export_review_status.py").read_text(encoding="utf-8")
    assert "/api/collaboration/verified-chapters" in source
    assert "catalogRevision" in source
    assert "data/verified-chapters.json" in (ROOT / ".gitignore").read_text()


def test_desktop_version_remains_independent():
    tauri = read_json("src-tauri/tauri.conf.json")

    assert tauri["version"] == "0.21.0"
