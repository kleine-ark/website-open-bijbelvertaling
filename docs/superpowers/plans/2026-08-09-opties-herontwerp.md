# Herontwerp optiescherm Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Vervang de rommelige optieszijbalk door één toegankelijk, modern en responsief paneel met de tabbladen Lezen, Vergelijken en Onderzoeken.

**Architecture:** `Opties` blijft eigenaar van opgeslagen vertaalkeuzes en tekstrendering. Een nieuwe `OptionsPanel`-controller beheert uitsluitend het modale paneel, tabnavigatie, focus en openen/sluiten; `OVZoom` blijft eigenaar van de zoomwaarde en levert een kleine interface aan het paneel. Bestaande control-ids, `data-optie` en `data-toggle-col` blijven ongewijzigd.

**Tech Stack:** Statische HTML, CSS, JavaScript zonder framework, Python `pytest`, Playwright-browserintegratietests.

## Global Constraints

- Desktop: zwevend paneel van ongeveer `520px`; mobiel tot en met `768px`: volledige beschikbare breedte en hoogte onder de bovenbalk.
- De leestekst verandert niet van breedte of scrollpositie wanneer Opties opent.
- De losse zoomknop verdwijnt; de opgeslagen zoomwaarde blijft bestaan.
- Alle bestaande voorkeuren, opslagkeys, control-ids en `data-*`-waarden blijven compatibel.
- Tabbladen en dialoog zijn volledig met toetsenbord en schermlezer bedienbaar.
- Licht, donker en `prefers-reduced-motion` krijgen volwaardige styling.
- Wijzig geen Bijbeldata of andere lopende werkboombestanden.

---

### Task 1: Toegankelijke paneelcontroller

**Files:**
- Create: `js/options-panel.js`
- Modify: `index.html:546-669`
- Modify: `js/sidebar.js:1-150`
- Modify: `js/mobile-nav.js:376-388`
- Test: `tests/test_opties_panel.py`

**Interfaces:**
- Consumes: bestaande openknoppen `#sidebar-right-open` en `#mobile-opties-btn`, dialoog `#sidebar-right`, sluitknop `#sidebar-right-toggle`.
- Produces: `window.OptionsPanel` met `init(): void`, `open(trigger?: HTMLElement): void`, `close(): void`, `activateTab(name: 'lezen'|'vergelijken'|'onderzoeken', focus?: boolean): void`.

- [ ] **Step 1: Schrijf de falende browsertests voor openen, sluiten en tabs**

```python
def test_opties_opent_modaal_zonder_de_leestekst_te_versmallen(page):
    page.goto(f"{base_url}/index.html#genesis/1")
    before = page.locator("#content").bounding_box()["width"]
    page.locator("#sidebar-right-open").click()
    assert page.locator("#sidebar-right").evaluate("el => el.open") is True
    assert page.locator("#content").bounding_box()["width"] == before

def test_opties_heeft_drie_toegankelijke_tabs(page):
    page.locator("#sidebar-right-open").click()
    assert page.get_by_role("tab").all_text_contents() == [
        "Lezen", "Vergelijken", "Onderzoeken"
    ]
```

- [ ] **Step 2: Draai de nieuwe tests en bevestig de verwachte mislukking**

Run: `python -m pytest tests/test_opties_panel.py -q`

Expected: FAIL omdat `#sidebar-right` nog geen modale dialoog en geen tabrollen heeft.

- [ ] **Step 3: Bouw de minimale dialoogstructuur en controller**

Gebruik in `index.html`:

```html
<dialog id="sidebar-right" class="options-panel" aria-labelledby="options-title">
  <header id="sidebar-right-header" class="options-header">
    <button id="sidebar-right-toggle" type="button" aria-label="Opties sluiten">×</button>
    <p class="options-eyebrow">Open Vertaling</p>
    <h2 id="options-title">Leesvoorkeuren</h2>
    <p class="options-preview">In de beginne schiep God de hemel en de aarde.</p>
    <div class="options-tabs" role="tablist" aria-label="Categorieën">
      <button role="tab" id="options-tab-lezen" aria-controls="options-panel-lezen" aria-selected="true">Lezen</button>
      <button role="tab" id="options-tab-vergelijken" aria-controls="options-panel-vergelijken" aria-selected="false" tabindex="-1">Vergelijken</button>
      <button role="tab" id="options-tab-onderzoeken" aria-controls="options-panel-onderzoeken" aria-selected="false" tabindex="-1">Onderzoeken</button>
    </div>
  </header>
  <div id="sidebar-right-body" class="options-body"></div>
</dialog>
```

Laat `OptionsPanel.open()` `showModal()` gebruiken, bewaar de opener voor focusherstel en sluit bij een klik op de dialoogachtergrond. Laat de dialoog zelf de modaliteit en focusscherming verzorgen. Verwijder `setupRightToggle()` en `_closeRight()` uit `Sidebar`; laat `MobileNav._openOpties()` uitsluitend `OptionsPanel.open(optBtn)` aanroepen.

- [ ] **Step 4: Laat de controller- en dialoogtests slagen**

Run: `python -m pytest tests/test_opties_panel.py -q`

Expected: PASS voor openen, sluiten, `Escape`, focusherstel, klik op achtergrond en tabtoetsen.

- [ ] **Step 5: Commit de paneelbasis**

```powershell
git add -- js/options-panel.js js/sidebar.js js/mobile-nav.js index.html tests/test_opties_panel.py
git commit -m "feat: bouw toegankelijk optiespaneel"
```

### Task 2: Orden alle bestaande instellingen in drie tabbladen

**Files:**
- Modify: `index.html:546-669`
- Modify: `js/options-panel.js`
- Test: `tests/test_opties_panel.py`

**Interfaces:**
- Consumes: de paneel- en tabinterface uit Task 1; bestaande handlers in `Opties`, `App` en de kolomtogglelogica.
- Produces: drie `role="tabpanel"`-elementen met alle bestaande controls en onveranderde ids/waarden.

- [ ] **Step 1: Schrijf falende tests voor de control-indeling en compatibiliteit**

```python
EXPECTED_TAB = {
    "toggle-versnummers": "lezen",
    "toggle-citaten": "lezen",
    "toggle-doorlopend": "lezen",
    "toggle-kt-popup": "vergelijken",
    "toggle-tags": "onderzoeken",
    "toggle-hs-vers": "onderzoeken",
}

def test_bestaande_controls_staan_in_het_juiste_tabblad(page):
    for control_id, tab in EXPECTED_TAB.items():
        assert page.locator(f"#options-panel-{tab} #{control_id}").count() == 1

def test_data_optie_en_kolomwaarden_blijven_compatibel(page):
    assert page.locator('[data-optie="godsnaam"]').evaluate_all(
        "els => els.map(el => el.value)"
    ) == ["ov", "klassiek", "jehovah", "jhwh"]
    assert page.locator('[data-toggle-col]').evaluate_all(
        "els => els.map(el => el.dataset.toggleCol)"
    ) == ["1637", "sv1888", "2026", "margin1637", "marginSV1888", "margin2026", "hebrew", "diff", "noteDiff"]
```

- [ ] **Step 2: Draai de indelingstests en bevestig de mislukking**

Run: `python -m pytest tests/test_opties_panel.py -q`

Expected: FAIL omdat de controls nog niet in de drie panelen staan.

- [ ] **Step 3: Verplaats controls zonder hun gedrag te herschrijven**

Maak binnen `#sidebar-right-body`:

```html
<section id="options-panel-lezen" role="tabpanel" aria-labelledby="options-tab-lezen">...</section>
<section id="options-panel-vergelijken" role="tabpanel" aria-labelledby="options-tab-vergelijken" hidden>...</section>
<section id="options-panel-onderzoeken" role="tabpanel" aria-labelledby="options-tab-onderzoeken" hidden>...</section>
```

Plaats onder **Lezen** weergave, vertaalweergave en voorlezen; onder **Vergelijken** tekstedities, kanttekeningen, kolomindeling en verschillen; onder **Onderzoeken** grondtalen, oudste handschrift, tags, geografische markering en de Strong-status. Behoud alle bestaande ids, namen, values, `data-optie`, `data-toggle-col` en wijzigingshandlers letterlijk.

- [ ] **Step 4: Laat indeling en bestaande optiegedrag slagen**

Run: `python -m pytest tests/test_opties_panel.py tests/test_branding_en_initialen.py -q`

Expected: PASS; een wijziging aan Godsnaam, versnummers en tekstedities blijft ook na herladen actief.

- [ ] **Step 5: Commit de informatiearchitectuur**

```powershell
git add -- index.html js/options-panel.js tests/test_opties_panel.py
git commit -m "feat: groepeer opties in drie tabbladen"
```

### Task 3: Verplaats zoom naar Lezen

**Files:**
- Modify: `js/zoom.js:1-236`
- Modify: `index.html` binnen `#options-panel-lezen`
- Test: `tests/test_opties_panel.py`

**Interfaces:**
- Consumes: bestaande opslagkey `ov_zoom` en zoomstappen uit `js/zoom.js`.
- Produces: `window.OVZoom` met `get(): number`, `set(value: number): void`, `step(delta: -1|1): void`, `reset(): void`, `subscribe(listener: (value: number) => void): () => void`.

- [ ] **Step 1: Schrijf falende tests voor de zoomregel en het ontbreken van de zweefknop**

```python
def test_zoom_staat_in_lezen_en_niet_meer_zwevend(page):
    page.locator("#sidebar-right-open").click()
    assert page.locator("#options-panel-lezen #options-zoom").count() == 1
    assert page.locator("body > #ov-zoom").count() == 0

def test_zoom_blijft_bewaard_na_herladen(page):
    page.locator("#options-zoom-in").click()
    value = page.locator("#options-zoom-value").inner_text()
    page.reload()
    page.locator("#sidebar-right-open").click()
    assert page.locator("#options-zoom-value").inner_text() == value
```

- [ ] **Step 2: Draai de zoomtests en bevestig de mislukking**

Run: `python -m pytest tests/test_opties_panel.py -q`

Expected: FAIL omdat `#options-zoom` niet bestaat en `#ov-zoom` nog wordt geïnjecteerd.

- [ ] **Step 3: Scheid zoomtoestand van de oude zweefbediening**

Laat `OVZoom.set()` de bestaande begrenzing, opslag en toepassing gebruiken. Verwijder `createControls()` en de daarbij geïnjecteerde knop-CSS. Verbind in `OptionsPanel.init()` de drie paneelknoppen met `OVZoom.step(-1)`, `OVZoom.reset()` en `OVZoom.step(1)`; update `#options-zoom-value` via `OVZoom.subscribe()`.

- [ ] **Step 4: Laat de zoom- en regressietests slagen**

Run: `python -m pytest tests/test_opties_panel.py tests/test_branding_en_initialen.py -q`

Expected: PASS; zoomen wijzigt de leestekst, blijft na herladen actief en creëert geen zweefknop.

- [ ] **Step 5: Commit de zoomverplaatsing**

```powershell
git add -- js/zoom.js js/options-panel.js index.html tests/test_opties_panel.py
git commit -m "feat: verplaats zoom naar leesopties"
```

### Task 4: Bouw de definitieve visuele en responsieve vorm

**Files:**
- Modify: `css/style.css:946-1050`
- Modify: `css/style.css:2208-2250`
- Modify: `css/style.css:3925-3945`
- Test: `tests/test_opties_panel.py`

**Interfaces:**
- Consumes: de HTML-klassen `.options-panel`, `.options-header`, `.options-tabs`, `.options-body`, `.option-row`, `.option-switch`, `.option-segments` en `.options-zoom`.
- Produces: desktop- en mobiele lay-out, licht/donker thema, focusstijlen en gereduceerde beweging.

- [ ] **Step 1: Schrijf falende layouttests voor desktop en mobiel**

```python
def test_desktop_paneel_is_zwevend_en_ongeveer_520px(page):
    page.set_viewport_size({"width": 1440, "height": 900})
    page.locator("#sidebar-right-open").click()
    box = page.locator("#sidebar-right").bounding_box()
    assert 500 <= box["width"] <= 540
    assert box["x"] + box["width"] < 1440

def test_mobiel_paneel_gebruikt_de_beschikbare_breedte(page):
    page.set_viewport_size({"width": 390, "height": 844})
    page.locator("#mobile-opties-btn").click()
    box = page.locator("#sidebar-right").bounding_box()
    assert box["x"] == 0
    assert box["width"] == 390
```

- [ ] **Step 2: Draai de layouttests en bevestig de mislukking**

Run: `python -m pytest tests/test_opties_panel.py -q`

Expected: FAIL omdat de oude `220px`-zijbalkregels nog actief zijn.

- [ ] **Step 3: Vervang de oude zijbalk-CSS volledig**

Gebruik voor desktop onder meer:

```css
#sidebar-right.options-panel {
  position: fixed;
  inset: 88px 16px 16px auto;
  width: min(520px, calc(100vw - 32px));
  max-width: none;
  max-height: none;
  margin: 0;
  padding: 0;
  border: 1px solid color-mix(in srgb, var(--gold) 34%, var(--border-light));
  border-radius: 26px;
  background: var(--bg-surface);
  color: var(--navy);
  box-shadow: -12px 18px 60px rgba(10, 31, 48, .24);
}
#sidebar-right::backdrop { background: rgba(14, 34, 50, .42); }
```

Bij `max-width: 768px` wordt `inset: 56px 0 0`, `width: 100vw`, `height: calc(100dvh - 56px)` en `border-radius: 22px 22px 0 0`. Gebruik Fira Sans voor controls, EB Garamond voor de preview, goud alleen voor lijniconen en actieve indicator. Voeg duidelijke `:focus-visible`-stijlen en een `prefers-reduced-motion`-regel toe.

- [ ] **Step 4: Laat alle paneel- en brandingtests slagen**

Run: `python -m pytest tests/test_opties_panel.py tests/test_branding_en_initialen.py -q`

Expected: PASS op `1440`, `1000`, `768`, `545` en `390` pixels.

- [ ] **Step 5: Commit de visuele vorm**

```powershell
git add -- css/style.css tests/test_opties_panel.py
git commit -m "feat: style modern responsief optiescherm"
```

### Task 5: Eindcontrole in de echte leespagina

**Files:**
- Modify only if verification exposes a defect: `index.html`, `css/style.css`, `js/options-panel.js`, `js/zoom.js`, `js/sidebar.js`, `js/mobile-nav.js`, `tests/test_opties_panel.py`

**Interfaces:**
- Consumes: het complete optiescherm uit Tasks 1-4.
- Produces: aantoonbaar werkende desktop- en mobiele integratie zonder regressie in bestaande branding of leesweergave.

- [ ] **Step 1: Draai alle relevante geautomatiseerde tests**

Run: `python -m pytest tests/test_opties_panel.py tests/test_branding_en_initialen.py -q`

Expected: alle tests slagen zonder waarschuwingen uit de applicatieconsole.

- [ ] **Step 2: Controleer de werkboom op onbedoelde wijzigingen**

Run: `git diff --check; git status --short`

Expected: geen whitespacefouten; alleen de geplande UI-bestanden en reeds aanwezige wijzigingen van andere werkzaamheden zijn zichtbaar.

- [ ] **Step 3: Controleer visueel in licht en donker thema**

Open `index.html#genesis/1`, test `1440`, `1000`, `768`, `545` en `390` pixels en leg screenshots vast. Controleer tabvolgorde, lange labels, scrollen binnen het paneel, zoom op `125%`, sluiten met `Escape` en onveranderde leespositie.

- [ ] **Step 4: Herstel alleen aantoonbare afwijkingen en herhaal de volledige testset**

Run: `python -m pytest tests/test_opties_panel.py tests/test_branding_en_initialen.py -q`

Expected: alle tests slagen na iedere correctie.

- [ ] **Step 5: Commit eventuele verificatiecorrecties**

```powershell
git add -- index.html css/style.css js/options-panel.js js/zoom.js js/sidebar.js js/mobile-nav.js tests/test_opties_panel.py
git commit -m "fix: rond optiescherm visueel af"
```
