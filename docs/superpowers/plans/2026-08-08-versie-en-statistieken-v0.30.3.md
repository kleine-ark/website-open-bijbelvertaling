# Versie en statistieken v0.30.3 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Publiceer de menselijke controle van Prediker als websiteversie v0.30.3 met consistente statistieken, downloadmetadata en cacheverversing.

**Architecture:** `data/verified-chapters.json` blijft de bron voor de menselijke reviewstatus. `scripts/build_stats.py` leidt daaruit `data/stats.json` af; `scripts/build_downloads.py` neemt de versie en gecontroleerde aantallen uit dat bestand over. Een regressietest bewaakt dat serviceworker, statistieken, changelog en downloadindex dezelfde websiteversie tonen, terwijl de desktopversie los blijft staan.

**Tech Stack:** JSON, JavaScript-serviceworker, Python 3, pytest

## Global Constraints

- De websiteversie wordt `v0.30.3`.
- De releasedatum wordt `8 augustus 2026` in zichtbare Nederlandse tekst en `2026-08-08` in machinaal leesbare metadata.
- De zelfstandige desktop-appversie blijft `0.21.0`.
- Alleen menselijk bevestigde boeken tellen als afgerond.
- Bestaande, niet-gerelateerde wijzigingen in de werkboom blijven onaangeroerd.

---

### Task 1: Release-metadata bewaken

**Files:**
- Create: `tests/test_release_metadata.py`
- Read: `sw.js`
- Read: `data/stats.json`
- Read: `data/changelog.json`
- Read: `downloads/index.json`
- Read: `src-tauri/tauri.conf.json`

**Interfaces:**
- Consumes: releasevelden uit bestaande JSON-bestanden en `const VERSION` uit `sw.js`
- Produces: pytest-regressiecontrole voor websiteversie `v0.30.3`, voortgangscijfers en zelfstandige desktopversie `0.21.0`

- [ ] **Step 1: Schrijf de falende regressietest**

```python
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WEBSITE_VERSION = "v0.30.3"


def read_json(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def test_website_release_metadata_is_consistent():
    stats = read_json("data/stats.json")
    changelog = read_json("data/changelog.json")
    downloads = read_json("downloads/index.json")
    service_worker = (ROOT / "sw.js").read_text(encoding="utf-8")
    match = re.search(r"const VERSION = '([^']+)'", service_worker)

    assert match and match.group(1) == WEBSITE_VERSION
    assert stats["version"] == WEBSITE_VERSION
    assert changelog["wijzigingen"][0]["versie"] == WEBSITE_VERSION
    assert downloads["versie"] == WEBSITE_VERSION
    assert changelog["wijzigingen"][0]["datum"] == "2026-08-08"
    assert stats["date"] == "8 augustus 2026"


def test_human_review_statistics_include_prediker():
    stats = read_json("data/stats.json")

    assert stats["books_verified"] == 49
    assert stats["chapters_verified"] == 630
    assert stats["verses_verified"] == 16738
    assert "Prediker" in stats["verified_books"]


def test_desktop_version_remains_independent():
    tauri = read_json("src-tauri/tauri.conf.json")

    assert tauri["version"] == "0.21.0"
```

- [ ] **Step 2: Draai de test en bevestig dat de websiteversie faalt**

Run: `python -m pytest tests/test_release_metadata.py -q`

Expected: FAIL doordat serviceworker, statistieken, changelog en downloadindex nog `v0.30.2` gebruiken; de desktopcontrole slaagt.

- [ ] **Step 3: Commit de regressietest**

```powershell
git add -- tests/test_release_metadata.py
git commit -m "test: bewaak releaseversie en statistieken"
```

### Task 2: Websitepatch publiceren

**Files:**
- Modify: `sw.js:11`
- Modify: `data/changelog.json:3`
- Regenerate: `data/stats.json`
- Regenerate: `data/review-history.json`
- Regenerate: `downloads/index.json`
- Regenerate: `downloads/open-vertaling-nagekeken.epub`
- Regenerate: `downloads/open-vertaling-brondata.zip`

**Interfaces:**
- Consumes: menselijke reviewstatus uit `data/verified-chapters.json`, versgegevens uit `data/*/*.json`, versieargument `v0.30.3` en datumargument `8 augustus 2026`
- Produces: consistente releasegegevens voor website, cache en downloads

- [ ] **Step 1: Voeg de changelogvermelding voor v0.30.3 toe**

Voeg vóór de bestaande v0.30.2-vermelding dit object toe:

```json
{
  "versie": "v0.30.3",
  "datum": "2026-08-08",
  "items": [
    {
      "type": "fix",
      "beschrijving": "De opmerkingen bij Prediker uit het feedbackoverzicht zijn verwerkt: 22 meldingen bij 21 unieke verzen zijn gecontroleerd en waar nodig gecorrigeerd."
    },
    {
      "type": "verbetering",
      "beschrijving": "Prediker is door een mens nagelezen en staat nu op afgerond. De voortgang is opnieuw berekend op 49 boeken, 630 hoofdstukken en 16.738 verzen."
    },
    {
      "type": "verbetering",
      "beschrijving": "De statistieken, nagekeken EPUB en brondata-download zijn opnieuw opgebouwd voor deze versie."
    }
  ]
}
```

- [ ] **Step 2: Verhoog de serviceworker-cacheversie**

Vervang in `sw.js`:

```javascript
const VERSION = 'v0.30.2'
```

door:

```javascript
const VERSION = 'v0.30.3'
```

- [ ] **Step 3: Genereer de statistieken opnieuw**

Run: `python scripts/build_stats.py v0.30.3 "8 augustus 2026"`

Expected: `stats.json geschreven` met 49 nagekeken boeken, 630 hoofdstukken en 16.738 verzen.

- [ ] **Step 4: Bouw de downloads opnieuw**

Run: `python scripts/build_downloads.py`

Expected: de nagekeken EPUB bevat 49 boeken, 630 hoofdstukken en 16.738 verzen; `downloads/index.json` noemt `v0.30.3`.

- [ ] **Step 5: Draai de gerichte controles**

Run: `python -m pytest tests/test_release_metadata.py tests/test_verified_chapters.py tests/test_build_downloads.py tests/test_prediker_feedback.py -q`

Expected: 16 tests slagen.

- [ ] **Step 6: Controleer dat de desktopversie ongemoeid bleef**

Run: `git diff -- src-tauri/tauri.conf.json src-tauri/Cargo.toml`

Expected: geen uitvoer.

- [ ] **Step 7: Commit uitsluitend de releasebestanden**

```powershell
git add -- sw.js data/changelog.json data/stats.json data/review-history.json downloads/index.json downloads/open-vertaling-nagekeken.epub downloads/open-vertaling-brondata.zip tests/test_release_metadata.py
git commit -m "chore: publiceer websiteversie v0.30.3"
```
