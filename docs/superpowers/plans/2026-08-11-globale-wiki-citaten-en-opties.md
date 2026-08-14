# Globale Wiki-citaten en opties Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Laat alle Bijbelcitaten buiten de hoofdlezer via één renderer werken en maak tekstopties overal beschikbaar, inclusief de Wiki zonder navigatie naar de lezer.

**Architecture:** `OVTekstweergave` blijft de enige renderlaag boven `OSV.cite`. Een kleine globale opties-host levert het bestaande paneel op iedere pagina; hij zendt een wijzigingssignaal naar dezelfde pagina en de Wiki-parent zendt dat door naar zijn iframe. Citaatcontainers registreren zichzelf en renderen opnieuw op dat signaal.

**Tech Stack:** Statische HTML, vanilla JavaScript, CSS, bestaande `Opties`, `OptionsPanel`, `OVTekstweergave` en `OSV.cite`.

## Global Constraints

- De hoofdnavigatie is de enige ingang voor tekstopties; geen zwevende of mobiele leestekstknop.
- De Wiki blijft op zijn huidige pagina wanneer opties openen of wijzigen.
- Elke Bijbeltekst buiten de hoofdlezer gebruikt `OVTekstweergave` met `OSV.cite`.
- Veranderingen aan Godsnaam, taal/editie, citaatopmaak, versnummers, Strong-nummers, geografie, maten en tijd gelden globaal.
- Sectiekoppen van opties gebruiken het marineblauw van de hoofdnavigatie met goud accent en leesbaar contrast in beide thema's.

---

### Task 1: Globaal wijzigingssignaal en her-renderbare citaatcomponent

**Files:**
- Modify: `js/tekstweergave.js`
- Modify: `embed.js`
- Test: `tests/test_wiki_citation_template.py`

**Interfaces:**
- Produces: `window.OVTekstweergave.verversCitaten(root)`.
- Consumes: browser-event `ov:opties-gewijzigd` met `{ detail: { state } }`.

- [x] **Step 1: Write the failing test**

```python
def test_citation_runtime_exposes_global_refresh_contract():
    view = read("js/tekstweergave.js")
    assert "verversCitaten" in view
    assert "ov:opties-gewijzigd" in view
```

- [x] **Step 2: Run test to verify it fails**

Run: `python -m pytest -q tests/test_wiki_citation_template.py::test_citation_runtime_exposes_global_refresh_contract`

Expected: FAIL because the refresh contract does not exist.

- [x] **Step 3: Write minimal implementation**

```javascript
function verversCitaten(root) {
    (root || document).querySelectorAll('[data-ov-citaat-ref]').forEach(function (node) {
        renderNaslagtekst(node, node.dataset.ovCitaatRef, JSON.parse(node.dataset.ovCitaatOpties || '{}'));
    });
}
window.addEventListener('ov:opties-gewijzigd', function () { verversCitaten(document); });
```

Store the reference and serializable render options on every container created by `renderNaslagtekst`; have `embed.js` expose the same refresh through `OSV.renderAll` for raw embed containers.

- [x] **Step 4: Run test to verify it passes**

Run: `python -m pytest -q tests/test_wiki_citation_template.py::test_citation_runtime_exposes_global_refresh_contract`

Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
git add js/tekstweergave.js embed.js tests/test_wiki_citation_template.py
git commit -m "feat: refresh citations from global options"
```

### Task 2: Centrale opties-host voor gewone pagina's en Wiki

**Files:**
- Create: `js/global-options-host.js`
- Modify: `js/options-panel.js`
- Modify: `js/opties.js`
- Modify: `wiki.html`
- Modify: `js/topnav.js`
- Test: `tests/test_global_options_host.py`

**Interfaces:**
- Consumes: `window.OVTekstweergave.verversCitaten(root)`.
- Produces: `window.GlobalOptionsHost.ensure()` en het event `ov:opties-gewijzigd`.

- [x] **Step 1: Write the failing test**

```python
def test_wiki_loads_global_options_host_without_reader_redirect():
    wiki = read("wiki.html")
    host = read("js/global-options-host.js")
    assert 'js/global-options-host.js' in wiki
    assert 'index.html?opties=1' not in host
    assert 'ov:opties-gewijzigd' in host
```

- [x] **Step 2: Run test to verify it fails**

Run: `python -m pytest -q tests/test_global_options_host.py::test_wiki_loads_global_options_host_without_reader_redirect`

Expected: FAIL because the host is absent.

- [x] **Step 3: Write minimal implementation**

```javascript
window.GlobalOptionsHost = {
    ensure: function () { /* inject existing dialog template once, then OptionsPanel.init() */ },
    notify: function () {
        window.dispatchEvent(new CustomEvent('ov:opties-gewijzigd', { detail: { state: Opties.state } }));
    }
};
```

Load `opties.js`, `tekstweergave.js`, `embed.js`, the host and `options-panel.js` in `wiki.html`. Make `Opties.save()` call `GlobalOptionsHost.notify()` after writing storage. In `wiki.html`, forward the event to `wiki-frame.contentWindow` with `postMessage`; receive that message in iframe pages and dispatch the same event locally. Replace the topnav fallback redirect with `GlobalOptionsHost.ensure()`.

- [x] **Step 4: Run test to verify it passes**

Run: `python -m pytest -q tests/test_global_options_host.py::test_wiki_loads_global_options_host_without_reader_redirect`

Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
git add js/global-options-host.js js/options-panel.js js/opties.js wiki.html js/topnav.js tests/test_global_options_host.py
git commit -m "feat: make text options global in wiki"
```

### Task 3: Migrate all direct Wiki and subject citations

**Files:**
- Modify: `onderwerpen.html`
- Modify: `js/naslag.js`
- Modify: `js/gekoppelde-teksten.js`
- Modify: all page templates that contain `OSV.cite(` outside `embed.js`
- Test: `tests/test_wiki_citation_template.py`

**Interfaces:**
- Consumes: `OVTekstweergave.renderNaslagtekst(container, ref, options)`.
- Produces: no direct `OSV.cite(` calls in page-specific code.

- [x] **Step 1: Write the failing test**

```python
def test_wiki_pages_delegate_bible_text_to_central_component():
    for name in ("onderwerpen.html", "js/naslag.js", "js/gekoppelde-teksten.js"):
        assert "OVTekstweergave" in read(name)
    assert "OSV.cite(" not in read("onderwerpen.html")
```

- [x] **Step 2: Run test to verify it fails**

Run: `python -m pytest -q tests/test_wiki_citation_template.py::test_wiki_pages_delegate_bible_text_to_central_component`

Expected: FAIL because the subject page calls `OSV.cite` directly.

- [x] **Step 3: Write minimal implementation**

```javascript
OVTekstweergave.renderNaslagtekst(teksthouder, ref, {
    toonLink: false,
    target: '_top'
});
```

Use this call in the lazy subject list, context expansion and every fallback that currently prints raw verse strings. Preserve each page's existing plus/minus controls, focus styling and reader links.

- [x] **Step 4: Run test to verify it passes**

Run: `python -m pytest -q tests/test_wiki_citation_template.py::test_wiki_pages_delegate_bible_text_to_central_component`

Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
git add onderwerpen.html js/naslag.js js/gekoppelde-teksten.js tests/test_wiki_citation_template.py
git commit -m "refactor: unify wiki bible citations"
```

### Task 4: One entry point and options hierarchy styling

**Files:**
- Modify: `index.html`
- Modify: `js/mobile-nav.js`
- Modify: `js/options-panel.js`
- Modify: `css/style.css`
- Test: `tests/test_global_options_host.py`

**Interfaces:**
- Consumes: `GlobalOptionsHost.ensure()`.
- Produces: only `#topnav-tekstopties` as settings entry, including mobile hamburger menu.

- [x] **Step 1: Write the failing test**

```python
def test_reader_has_no_floating_or_mobile_options_opener():
    html = read("index.html")
    assert 'id="sidebar-right-open"' not in html
    assert 'id="mobile-opties-btn"' not in html
    assert 'topnav-tekstopties' in read("js/topnav.js")
```

- [x] **Step 2: Run test to verify it fails**

Run: `python -m pytest -q tests/test_global_options_host.py::test_reader_has_no_floating_or_mobile_options_opener`

Expected: FAIL because both reader-local buttons exist.

- [x] **Step 3: Write minimal implementation**

```css
.options-category > summary {
    background: var(--navy);
    color: #fff;
    border-color: var(--gold);
}
:root[data-theme="donker"] .options-category > summary { color: #fff; }
```

Remove the two reader-local opener elements and their listeners. Add a `Tekstopties` menu item to the mobile hamburger menu that calls the same topnav opener. Remove CSS only for the retired controls; retain dialog and keyboard behavior.

- [x] **Step 4: Run test to verify it passes**

Run: `python -m pytest -q tests/test_global_options_host.py::test_reader_has_no_floating_or_mobile_options_opener`

Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
git add index.html js/mobile-nav.js js/options-panel.js css/style.css tests/test_global_options_host.py
git commit -m "style: unify global text options entry"
```

### Task 5: End-to-end verification

**Files:**
- Modify: `tests/test_wiki_citation_template.py`
- Modify: `tests/test_global_options_host.py`

**Interfaces:**
- Consumes: Tasks 1–4.
- Produces: regression coverage for global citations and global options.

- [x] **Step 1: Add integration assertions**

```python
def test_wiki_forwards_option_updates_to_its_iframe():
    wiki = read("wiki.html")
    assert "postMessage" in wiki
    assert "ov:opties-gewijzigd" in wiki
```

- [x] **Step 2: Run focused suite**

Run: `python -m pytest -q tests/test_wiki_citation_template.py tests/test_global_options_host.py tests/test_uitgangspunten_principes_current.py`

Expected: PASS.

- [x] **Step 3: Run the relevant regression suite**

Run: `python -m pytest -q tests/test_build_vertalingen.py tests/test_teksteditie.py tests/test_strongs_reader.py tests/test_geografie_runtime.py`

Expected: PASS.

- [x] **Step 4: Manual browser verification**

Open Wiki → Onderwerpen, change Godsnaam, citation markup, verse numbers and English text. Verify the current iframe remains open and all visible citations update. Verify the same options in the reader and a standalone naslag page.

- [ ] **Step 5: Commit**

```powershell
git add tests/test_wiki_citation_template.py tests/test_global_options_host.py
git commit -m "test: cover global wiki citation settings"
```

## Self-review

- Spec coverage: tasks 1–3 provide the single citation renderer and live synchronization; task 2 keeps Wiki navigation in place; task 4 removes duplicate openings and applies the required palette; task 5 verifies all requirements.
- Placeholder scan: no unresolved implementation choices remain; the existing dialog template is injected by the dedicated host rather than duplicated per page.
- Type consistency: every task uses `OVTekstweergave.verversCitaten`, `GlobalOptionsHost.ensure`, and the `ov:opties-gewijzigd` event consistently.
