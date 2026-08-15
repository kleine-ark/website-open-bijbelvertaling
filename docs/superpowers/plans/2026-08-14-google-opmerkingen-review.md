# Google-opmerkingen verwerken — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** De 544 opmerkingen uit de gepubliceerde feedbacksheet gecontroleerd verwerken, zonder testmeldingen, dubbele meldingen of inhoudelijk onzekere suggesties als tekstwijziging te publiceren.

**Architecture:** `scripts/lees_opmerkingen.py` blijft de enige lezer van de gepubliceerde CSV. Een nieuwe lokale triage-uitvoer normaliseert verwijzingen, groepeert duplicaten en classificeert iedere rij als `test`, `tekst-eenduidig`, `techniek`, `tag/wiki` of `inhoudelijk-review`; alleen de eenduidige tekstgroep wordt via boekgebonden review-scripts op `text2026`, HTML en `phraseDiff` toegepast.

**Tech Stack:** Python 3, JSON-bronteksten in `data/<boek>/<hoofdstuk>.json`, bestaande `sweep_principe.py`/`synchroniseer_opmaak.py`, pytest.

**Spec:** `docs/opmerkingen-in-google-sheet.md`

## Global Constraints

- Werk uitsluitend in `C:\Users\rickd\Documents\GitHub\website-open-bijbelvertaling`.
- Gebruik de gepubliceerde CSV alleen leesbaar; wijzig geen Google Sheet-status zonder expliciete toestemming.
- Sla testmeldingen en ambiguÃ« suggesties niet als tekstwijziging op.
- Houd `text2026`, `text2026_html` en `phraseDiff` bij elke tekstwijziging synchroon.
- Maak van een corpus-brede keuze eerst een controleerbaar principe met regressietest.

---

### Task 1: Reproduceerbare triage van de feedbacksheet

**Files:**
- Create: `scripts/triage_google_opmerkingen.py`
- Test: `tests/test_triage_google_opmerkingen.py`

**Interfaces:**
- Consumes: lijst rijen met `vers`, `selectie`, `suggestie`, `status` uit `lees_opmerkingen.haal_op()`.
- Produces: JSON-object met `test`, `tekst_eenduidig`, `techniek`, `tag_wiki`, `inhoudelijk_review` en `dubbel`.

- [ ] **Step 1: Write the failing test**

```python
def test_classificeer_testmelding_en_eenduidige_pijlcorrectie():
    rows = [
        {"vers": "Genesis 1:1", "suggestie": "Testmelding via formulier - mag weggegooid."},
        {"vers": "Exodus 8:2", "suggestie": "Vorsen -> kikkers"},
    ]
    result = classificeer(rows)
    assert result["test"][0]["vers"] == "Genesis 1:1"
    assert result["tekst_eenduidig"][0]["vervangingen"] == [("Vorsen", "kikkers")]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_triage_google_opmerkingen.py -q`

Expected: FAIL because `classificeer` does not exist.

- [ ] **Step 3: Write minimal implementation**

```python
def classificeer(rows):
    result = {name: [] for name in CATEGORIEEN}
    for row in rows:
        suggestion = normaliseer(row.get("suggestie", ""))
        if "test" in suggestion or "mag weg" in suggestion:
            result["test"].append(row)
        elif "->" in suggestion:
            result["tekst_eenduidig"].append(parse_vervanging(row))
        else:
            result[bepaal_categorie(suggestion)].append(row)
    return result
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_triage_google_opmerkingen.py -q`

Expected: PASS.

### Task 2: Verwerk alleen eenduidige tekstcorrecties per boek

**Files:**
- Create: `scripts/apply_google_review_<boek>.py` per afgeronde boekbatch
- Modify: `data/<boek>/<hoofdstuk>.json`
- Test: `tests/test_google_review_<boek>.py`

**Interfaces:**
- Consumes: `tekst_eenduidig`-records met een bestaande `boek hoofdstuk:vers`-referentie.
- Produces: gesynchroniseerde `text2026`, `text2026_html` en `phraseDiff`.

- [ ] **Step 1: Write the failing test**

```python
def test_exodus_8_2_vervangt_vorsen_en_bewaart_html_opmaak():
    result = apply_replacements("exodus", 8, 2, [("vorsen", "kikkers")])
    assert "kikkers" in result["text2026"]
    assert kaal(result["text2026_html"]) == kaal(result["text2026"])
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_google_review_exodus.py -q`

Expected: FAIL before the batch script exists.

- [ ] **Step 3: Write minimal implementation**

```python
def apply_replacements(book, chapter, verse, replacements):
    item = verse_item(book, chapter, verse)
    item["text2026"] = vervang_exact(item["text2026"], replacements)
    item["text2026_html"] = bijtrekken(item["text2026_html"], item["text2026"])
    item["phraseDiff"] = nieuwe_diff(kaal(item["textSV1888"]), kaal(item["text2026"]), item.get("phraseDiff", []), None, reference)
    return item
```

- [ ] **Step 4: Run focused and full validation**

Run: `python -m pytest tests/test_google_review_exodus.py -q` followed by the project test command.

Expected: all relevant tests pass; no HTML/plain-text mismatch.

### Task 3: Maak techniek-, tag- en inhoudelijke opmerkingen traceerbaar

**Files:**
- Create: `data/google-opmerkingen-reviewqueue.json`
- Test: `tests/test_google_opmerkingen_queue.py`

**Interfaces:**
- Consumes: alle niet-eenduidige, niet-test-opmerkingen.
- Produces: stable records `{ref, suggestie, categorie, reden, status: "open"}` zonder persoonsgegevens.

- [ ] **Step 1: Write the failing test**

```python
def test_queue_bevat_technische_en_tagmeldingen_zonder_inzender():
    queue = maak_queue([{"vers": "Exodus 8:28", "suggestie": "Horizontale swipe"}])
    assert queue[0]["categorie"] == "techniek"
    assert "van" not in queue[0]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_google_opmerkingen_queue.py -q`

Expected: FAIL before queue generation exists.

- [ ] **Step 3: Write minimal implementation**

```python
def maak_queue(rows):
    return [{"ref": row["vers"], "suggestie": row["suggestie"], "categorie": categorie(row), "reden": "Vereist inhoudelijke of productbeslissing", "status": "open"} for row in rows]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_google_opmerkingen_queue.py -q`

Expected: PASS.

### Task 4: Verifieer en publiceer een reviewbatch

**Files:**
- Modify: betrokken `data/<boek>/<hoofdstuk>.json`
- Modify: `data/review-changes.json` via de bestaande generatiestap
- Test: relevante review-, data- en browsertests

- [ ] **Step 1: Run the book-specific scripts and inspect changed references**

Run: `python scripts/apply_google_review_exodus.py` then `git diff --check`.

Expected: alleen opgegeven verzen veranderen; iedere HTML-tekst blijft gelijk aan de platte tekst.

- [ ] **Step 2: Run tests**

Run: `python -m pytest tests/test_google_review_exodus.py tests/test_strongs_reader.py -q`

Expected: PASS.

- [ ] **Step 3: Record outcome without changing Google status**

Store only the non-personal reference, suggestion, result and local commit in `data/google-opmerkingen-reviewqueue.json`.

- [ ] **Step 4: Commit the completed batch**

```bash
git add data scripts tests docs/superpowers/plans/2026-08-14-google-opmerkingen-review.md
git commit -m "Verwerk Google-opmerkingen voor Exodus"
```

## Self-Review

- Scope coverage: testmeldingen, eenduidige tekstcorrecties, technische/tag/inhoudelijke meldingen en traceerbaarheid zijn ieder afzonderlijk behandeld.
- Placeholder scan: alle taken bevatten concrete bestanden, commando's en minimale test-/implementatievoorbeelden.
- Type consistency: triage produceert alleen records die de toepassings- en wachtrijfuncties consumeren.

## Execution Handoff

De gebruiker heeft directe uitvoering gevraagd; voer deze taken inline uit, per boekbatch en met een testcontrole na elke batch.
