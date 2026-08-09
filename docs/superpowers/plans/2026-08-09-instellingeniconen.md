# Instellingeniconen Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Integreer de acht aangeleverde instellingeniconen en voeg blijvende voorkeuren voor lettertype en regelafstand toe.

**Architecture:** De SVG-assets worden lokaal opgenomen en vanuit het bestaande optiespaneel geladen. `Opties` blijft de enige toestandhouder; twee nieuwe waarden sturen CSS-klassen op `<body>`, zodat opnieuw gerenderde hoofdstukken automatisch de gekozen typografie erven.

**Tech Stack:** HTML, CSS, vanilla JavaScript, Python unittest/Playwright.

## Global Constraints

- Gebruik uitsluitend lokale SVG-assets voor de interface.
- Behoud alle bestaande instellingwaarden en opslagcompatibiliteit.
- De iconen zijn decoratief; tekstlabels blijven de toegankelijke naam.
- Ondersteun desktop, mobiel, licht thema en donker thema.

---

### Task 1: Assets en regressietests

**Files:**
- Create: `images/iconen/instellingen/*.svg`
- Modify: `tests/test_opties_panel.py`

**Interfaces:**
- Consumes: acht aangeleverde SVG-bestanden.
- Produces: lokale assetpaden en falende tests voor iconen en typografievoorkeuren.

- [ ] **Step 1: Kopieer de acht SVG-assets naar de repository.**
- [ ] **Step 2: Voeg een test toe die alle acht `<img class="option-icon">`-paden controleert.**
- [ ] **Step 3: Voeg een test toe die `lettertype=rustig` en `regelafstand=ruim` kiest en toepassing plus opslag controleert.**
- [ ] **Step 4: Draai de nieuwe tests en bevestig dat zij op ontbrekende HTML/werking falen.**

### Task 2: Bedieningen en toestand

**Files:**
- Modify: `index.html`
- Modify: `js/opties.js`

**Interfaces:**
- Consumes: `data-optie`-bindings en `sv2026_vertaalopties`.
- Produces: `Opties.state.lettertype`, `Opties.state.regelafstand` en `Opties.applyReaderStyleClasses()`.

- [ ] **Step 1: Voeg de acht iconen toe aan hun hoofdinstellingen.**
- [ ] **Step 2: Voeg radiokeuzes voor lettertype en regelafstand toe.**
- [ ] **Step 3: Voeg veilige standaardwaarden `klassiek` en `normaal` toe.**
- [ ] **Step 4: Pas bij initialisatie en wijziging de bodyklassen toe.**
- [ ] **Step 5: Draai de nieuwe tests en bevestig dat gedrag en opslag slagen.**

### Task 3: Vormgeving en volledige verificatie

**Files:**
- Modify: `css/style.css`
- Test: `tests/test_opties_panel.py`

**Interfaces:**
- Consumes: `.option-icon`, `.reader-font-*` en `.reader-spacing-*`.
- Produces: responsieve icoonrijen en typografie van de leestekst.

- [ ] **Step 1: Maak een vaste icoonkolom met rustige uitlijning.**
- [ ] **Step 2: Definieer klassieke/rustige letters en compacte/normale/ruime regelafstand.**
- [ ] **Step 3: Controleer licht/donker en mobiel/desktop via Playwright.**
- [ ] **Step 4: Draai de volledige optiespaneeltest en relevante regressietests.**
- [ ] **Step 5: Commit, push en merge de branch naar `main` wanneer de vuile hoofdwerkboom veilig behouden blijft.**
