"""Regressietests voor consistente releasegegevens."""

import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_json(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


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


def test_current_release_describes_numeri_and_uses_one_version():
    stats = read_json("data/stats.json")
    changelog = read_json("data/changelog.json")
    current_release = changelog["wijzigingen"][0]
    descriptions = " ".join(item["beschrijving"] for item in current_release["items"])

    assert "Numeri 1–20" in descriptions
    assert stats["version"] == current_release["versie"]
    assert service_worker_install_cache() == [f"shell-{current_release['versie']}"]
    assert current_release["datum"] == "2026-08-09"
    assert stats["date"] == "9 augustus 2026"


def test_human_review_statistics_include_numeri_1_tot_20():
    stats = read_json("data/stats.json")
    verified = read_json("data/verified-chapters.json")

    assert stats["books_verified"] == 49
    assert stats["chapters_verified"] == 650
    assert stats["verses_verified"] == 17474
    assert "Numeri 1–20" in stats["verified_books"]
    assert verified["numeri"] == list(range(1, 21))


def test_desktop_version_remains_independent():
    tauri = read_json("src-tauri/tauri.conf.json")

    assert tauri["version"] == "0.21.0"
