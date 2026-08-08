# Branding en sierinitialen Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Integreer het goedgekeurde Open Vertaling-logo in de websitebranding en vervang de tekstuele hoofdstukdrop-cap door de aangeleverde penkrulletters.

**Architecture:** `js/topnav.js` blijft de enige bron voor de gedeelde navigatiebranding; `lees.html` houdt zijn zelfstandige readerheader. `App._applyDropcap()` blijft verantwoordelijk voor alle eerste verzen en koppelt iedere letter aan een statisch SVG-bestand zonder de onderliggende tekst te verwijderen.

**Tech Stack:** Statische HTML/CSS/JavaScript, SVG/PNG, Python met pytest en Playwright.

## Global Constraints

- Behoud de volledige merknaam op mobiel.
- Behoud de originele aangeleverde SVG-bestanden ongewijzigd.
- Maak alleen voor donkere achtergronden afgeleide witte/gouden varianten.
- Behoud de oorspronkelijke eerste letter als kopieerbare en toegankelijke tekst.
- Raak gelijktijdige wijzigingen buiten deze bestanden niet aan.

---

### Task 1: Leg het branding- en initiaalcontract test-first vast

**Files:**
- Create: `tests/test_branding_en_initialen.py`

**Interfaces:**
- Consumes: statische assets, `js/topnav.js`, `js/app.js`, `css/style.css`, `lees.html` en `favicon.svg`.
- Produces: regressiecontract voor logo-assets, responsieve merknaam, favicon en letterkoppeling.

- [ ] **Step 1: Schrijf falende statische tests**

Controleer dat de vier brandingbronnen, 26 lichte letters en 26 donkere letters bestaan; dat `favicon.svg` `data-role="folio-o"` bevat en geen tekstnode `OV`; en dat de gedeelde navigatie een `.topnav-logo` gebruikt.

- [ ] **Step 2: Schrijf een browsertest voor de gedeelde navigatie**

Open `over-ov.html` bij 1440 en 390 pixels breed en controleer dat `.topnav-logo` zichtbaar blijft en dat de hamburger op mobiel zichtbaar is.

- [ ] **Step 3: Schrijf een browsertest voor twee hoofdstukletters**

Open `index.html#genesis/1` en `index.html#genesis/2`; controleer respectievelijk `I.svg` en `Z.svg` in de berekende achtergrond en controleer dat `textContent` de letter bewaart.

- [ ] **Step 4: Draai de nieuwe tests rood**

Run: `python -m pytest -q tests/test_branding_en_initialen.py`

Expected: FAIL omdat de nieuwe assets en logo-elementen nog ontbreken en de drop-cap nog geen SVG gebruikt.

---

### Task 2: Voeg de goedgekeurde merkassets en website-iconen toe

**Files:**
- Create: `images/branding/open-vertaling-logo.svg`
- Create: `images/branding/open-vertaling-logo.png`
- Create: `images/branding/open-folio-mark.svg`
- Create: `images/branding/open-folio-mark.png`
- Create: `images/branding/open-vertaling-logo-light.svg`
- Create: `images/branding/open-folio-mark-light.svg`
- Modify: `favicon.svg`
- Modify: `icons/app-icon.svg`
- Modify: `icons/app-icon-maskable.svg`
- Modify: `icons/icon-192.png`
- Modify: `icons/icon-512.png`
- Modify: `icons/icon-maskable-512.png`

**Interfaces:**
- Consumes: aangeleverde bronassets.
- Produces: `/images/branding/open-vertaling-logo.svg`, de lichte navigatievariant en vier browser/webapp-iconen.

- [ ] **Step 1: Kopieer de vier bronbestanden bytegetrouw**

Gebruik de aangeleverde map als bron en controleer de SHA-256-hashes na het kopiëren.

- [ ] **Step 2: Maak de twee donkere-achtergrondvarianten**

Vervang uitsluitend kleur `#143247` door `#ffffff`; behoud alle paden, het goud `#cba449`, titels en viewBoxen.

- [ ] **Step 3: Bouw favicon en webapp-iconen**

Gebruik het donkere beeldmerk op een lichte ondergrond voor het gewone pictogram en het witte/gouden beeldmerk op marineblauw voor het maskable pictogram. Render 192×192 en 512×512 PNG's uit de SVG-bronnen.

- [ ] **Step 4: Draai de assettests groen**

Run: `python -m pytest -q tests/test_branding_en_initialen.py -k "asset or favicon"`

Expected: PASS.

---

### Task 3: Integreer het woordmerk in beide headers

**Files:**
- Modify: `js/topnav.js`
- Modify: `css/style.css`
- Modify: `lees.html`
- Modify: `css/lees.css`
- Test: `tests/test_branding_en_initialen.py`

**Interfaces:**
- Consumes: `/images/branding/open-vertaling-logo.svg` en `open-vertaling-logo-light.svg`.
- Produces: `.topnav-logo`, `.reader-logo` en een los `.topnav-version`-element.

- [ ] **Step 1: Vervang de gedeelde tekstnaam door het lichte woordmerk**

Maak `.topnav-brand` een merkblok met een gelinkte `<img class="topnav-logo">` en behoud het versienummer als zelfstandig element daarnaast.

- [ ] **Step 2: Voeg responsieve navigatiestijlen toe**

Gebruik een maximale breedte van 210 px op desktop en 150 px op mobiel; laat de merknaam niet verdwijnen bij het hamburgerbreekpunt.

- [ ] **Step 3: Vervang de titel in de readerheader**

Gebruik twee logo-images en toon met themaselectoren alleen de variant die op de actuele achtergrond leesbaar is.

- [ ] **Step 4: Draai de navigatietests groen**

Run: `python -m pytest -q tests/test_branding_en_initialen.py -k "logo or navigatie"`

Expected: PASS.

---

### Task 4: Koppel alle hoofdstukken aan de penkrulletters

**Files:**
- Create: `images/initialen/vrije-penkrul/A.svg` through `Z.svg`
- Create: `images/initialen/vrije-penkrul/donker/A.svg` through `Z.svg`
- Modify: `js/app.js`
- Modify: `css/style.css`
- Test: `tests/test_branding_en_initialen.py`

**Interfaces:**
- Consumes: eerste tekstletter van `.verse-row[data-verse="1"] .col-2026`.
- Produces: `.dropcap--penkrul` met `--dropcap-image-light` en `--dropcap-image-dark`; de span houdt de letter als tekstinhoud.

- [ ] **Step 1: Kopieer de 26 bronletters en maak 26 donkere varianten**

De donkere variant vervangt uitsluitend `#143247` door `#e8e4da`; goud blijft `#cba449`.

- [ ] **Step 2: Pas `_applyDropcap()` aan**

Normaliseer alleen A–Z naar een bestandsnaam, zet beide achtergrond-URL's als CSS-variabelen en laat `span.textContent` gelijk aan de oorspronkelijke letter. Gebruik `.dropcap--fallback` voor overige letters.

- [ ] **Step 3: Pas de drop-cap-CSS aan**

Geef de penkrul een vak van `2.55em × 3.2em` met `0.35em` rechtermarge en wissel in donker thema naar `--dropcap-image-dark`.

- [ ] **Step 4: Draai de initiaaltests groen**

Run: `python -m pytest -q tests/test_branding_en_initialen.py -k initiaal`

Expected: PASS.

---

### Task 5: Volledige controle en publicatie

**Files:**
- Verify: alle gewijzigde bestanden en volledige testsuite.

**Interfaces:**
- Consumes: Task 1–4.
- Produces: gecontroleerde, gecommitte en gepushte brandingseenheid.

- [ ] **Step 1: Controleer syntaxis en assets**

Run: `node --check js/topnav.js && node --check js/app.js && python -m pytest -q tests/test_branding_en_initialen.py`

Expected: alle controles slagen.

- [ ] **Step 2: Draai de volledige suite**

Run: `python -m pytest -q`

Expected: alle tests slagen.

- [ ] **Step 3: Controleer desktop, mobiel en donker thema visueel**

Bekijk `over-ov.html`, `lees.html` en `index.html#genesis/1` op 1440 en 390 pixels; controleer leesbaarheid, hamburger, lettermaat en tekstselectie.

- [ ] **Step 4: Commit en push uitsluitend deze eenheid**

Commit message: `feat: integreer nieuw logo en sierinitialen`.
