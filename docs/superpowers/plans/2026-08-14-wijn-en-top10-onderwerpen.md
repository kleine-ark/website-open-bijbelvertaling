# Wijn en Top 10 voor onderwerpen Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Geef elk onderwerp een uniforme Top 10 en voeg Wijn in de Bijbel toe met alle letterlijke wijnverzen.

**Architecture:** `onderwerpen.html` krijgt een generieke renderer voor een Top 10 die de bestaande rangorde hergebruikt en via `OVTekstweergave.renderNaslagtekst` citeert. `data/tags.json` bevat de volledige wijn-tag en optionele expliciete topselectie; een klein script bouwt die deterministisch vanuit de Bijbeldata zodat dekking controleerbaar blijft.

**Tech Stack:** Statische HTML, browser-JavaScript, JSON-brondata, Python unittest/pytest.

**Spec:** `docs/superpowers/specs/2026-08-14-wijn-en-top10-onderwerpen-design.md`

## Global Constraints

- Werk uitsluitend in `C:\Users\rickd\Documents\GitHub\website-open-bijbelvertaling`.
- Gebruik de bestaande universele `OVTekstweergave`-component voor elke Top 10-citatie.
- Behoud het bestaande boekfilter, contextgedrag en globale leesinstellingen.

---

### Task 1: Contract voor Top 10 en wijngegevens

**Files:**
- Create: `tests/test_onderwerp_wijn_top10.py`
- Modify: `data/tags.json`
- Create: `scripts/build_wijn_onderwerp.py`

**Interfaces:**
- Consumes: `data/*/*.json` met `text2026`, `data/tags.json`.
- Produces: tag `{ id: 'wijn', topTien: string[], verzen: { ref: string, rang: number }[] }`.

- [ ] **Step 1: Write the failing test**

```python
def test_wijn_tag_covers_every_literal_wijn_vers():
    assert tagged_refs == literal_wijn_refs

def test_wijn_top_ten_contains_ten_curated_refs():
    assert len(wijn['topTien']) == 10
    assert 'genesis 14:18' in wijn['topTien']
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_onderwerp_wijn_top10.py -q`

Expected: FAIL because the `wijn` tag does not yet exist.

- [ ] **Step 3: Write minimal implementation**

```python
def collect_wijn_refs(data_root: Path) -> list[str]:
    return [ref for ref, text in iter_verses(data_root)
            if re.search(r'(?<![\\w-])wijn(?![\\w-])', text, re.I)]
```

Use the collector to update only the `wijn` tag in `data/tags.json`; give the ten agreed kernel passages rang 1 and store their ordered references in `topTien`.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_onderwerp_wijn_top10.py -q`

Expected: PASS.

### Task 2: Generieke Top 10-renderer

**Files:**
- Modify: `onderwerpen.html`
- Modify: `tests/test_onderwerp_wijn_top10.py`

**Interfaces:**
- Consumes: `tag.topTien?`, `verzenVan(tag)`, `OVTekstweergave.renderNaslagtekst`.
- Produces: `renderTopTien(tag)` which renders at most ten `.ond-top10-vers` items before `.ond-detail-lijst`.

- [ ] **Step 1: Write the failing test**

```python
def test_onderwerp_detail_has_universal_top_ten_renderer():
    assert 'function renderTopTien(tag)' in source
    assert 'OVTekstweergave.renderNaslagtekst' in renderer_body
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_onderwerp_wijn_top10.py -q`

Expected: FAIL because no generic Top 10 renderer exists.

- [ ] **Step 3: Write minimal implementation**

```javascript
function topTienVan(tag) {
  const ordered = verzenVan(tag);
  const byRef = new Map(ordered.map(item => [item.ref, item]));
  return Array.isArray(tag.topTien) && tag.topTien.length
    ? tag.topTien.map(ref => byRef.get(ref)).filter(Boolean).slice(0, 10)
    : ordered.slice(0, 10);
}
```

Render every item with `OVTekstweergave.renderNaslagtekst`, the existing link target, and no copied text formatting.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_onderwerp_wijn_top10.py -q`

Expected: PASS.

### Task 3: Regression verification

**Files:**
- Modify: `tests/test_onderwerp_wijn_top10.py`

**Interfaces:**
- Consumes: `onderwerpen.html`, `data/tags.json`.
- Produces: verified generic fallback behavior for a tag without `topTien`.

- [ ] **Step 1: Write the failing test**

```python
def test_all_topics_receive_top_ten_via_generic_fallback():
    assert source.count('renderTopTien(tag)') == 1
    assert 'ordered.slice(0, 10)' in source
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_onderwerp_wijn_top10.py -q`

Expected: FAIL until the generic renderer is wired into `toonDetail`.

- [ ] **Step 3: Wire and style the section**

Place the section between the topic metadata and the complete list. Reuse `.ond-vers` styling and add only scoped `.ond-top10*` rules.

- [ ] **Step 4: Run focused and existing subject tests**

Run: `python -m pytest tests/test_onderwerp_wijn_top10.py tests/test_onderwerpen_zegen_vloek_belofte_feest.py tests/test_onderwerp_engelen.py tests/test_onderwerp_demonen.py -q`

Expected: PASS.
