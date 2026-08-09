# Definitief Open Vertaling-logo Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Vervang de bestaande voorlopige merkset door de definitieve aangeleverde Open Vertaling-logo's en toon die scherp, onvervormd en cacheveilig in alle websitevarianten.

**Architecture:** De vier aangeleverde bestanden blijven de canonieke bronassets in `images/branding/`. Lichte SVG-varianten en favicon/PWA-iconen worden daar mechanisch van afgeleid; `js/topnav.js` en `lees.html` blijven de enige twee headerimplementaties. Regressietests leggen bronhashes, afgeleide SVG-geometrie, juiste beeldverhouding en responsief gedrag vast.

**Tech Stack:** Statische HTML/CSS/JavaScript, SVG/PNG, Python, Pillow, pytest en Playwright.

## Global Constraints

- Gebruik de aangeleverde bestanden bytegetrouw als canonieke donkere merkset.
- Vervang in lichte varianten uitsluitend marineblauw `#143247` door wit `#FFFFFF`; behoud goud `#C4A048`.
- Toon het volledige woordmerk in de kop, ook naast het hamburgermenu.
- Vervorm het logo op geen enkel breekpunt.
- Laat bestaande inhoud en hoofdstukinitialen ongemoeid.
- Voorkom dat een service-workercache de vorige merkset blijft tonen.

---

### Task 1: Leg de definitieve merkset test-first vast

**Files:**
- Modify: `tests/test_branding_en_initialen.py`

**Interfaces:**
- Consumes: vier canonieke bronassets, twee lichte SVG-varianten, favicon/PWA-SVG's en de twee headers.
- Produces: regressiecontract voor definitieve geometrie, hashes en onvervormde weergave.

- [ ] **Step 1: Voeg de vier verwachte SHA-256-hashes toe**

```python
EXPECTED_BRANDING_SHA256 = {
    "open-folio-mark.png": "3466DC4943EAD2C4D81FCB392FF84D015720B798FF8CF484AFF122ED14511209",
    "open-folio-mark.svg": "65DCDE5456A9045875CA0CA2BB0A81E3F9AD4B1066A25C5F5C8BF38E8F07AF39",
    "open-vertaling-logo.png": "66D9BBDFCBAFA6315ADE0CDA24E5D23215CCCAAD201D370EA785757FC1A93B3E",
    "open-vertaling-logo.svg": "5A96EE77D0E949D2F8D6B54429369E90605B72B9EE866799D3D4B55A720BFD25",
}
```

- [ ] **Step 2: Controleer afgeleide SVG-geometrie en kleuren**

Vergelijk voor de lichte varianten alle `d`- en `transform`-attributen met de donkere bron en sta als enige kleurverschil `#143247` naar `#FFFFFF` toe. Controleer dat `favicon.svg`, `icons/app-icon.svg` en `icons/app-icon-maskable.svg` dezelfde twee bronpaden bevatten in een groep met `data-role="open-folio-mark"`.

- [ ] **Step 3: Controleer de beeldverhouding in de browser**

```python
natural_ratio = logo.evaluate("img => img.naturalWidth / img.naturalHeight")
rendered_ratio = logo.evaluate(
    "img => img.getBoundingClientRect().width / img.getBoundingClientRect().height"
)
self.assertAlmostEqual(rendered_ratio, natural_ratio, delta=0.02)
```

- [ ] **Step 4: Draai de test rood**

Run: `python -m pytest -q tests/test_branding_en_initialen.py`

Expected: FAIL op de oude hashes/geometrie en mogelijk de oude vervormde kopweergave.

---

### Task 2: Vervang en leid de definitieve assets af

**Files:**
- Modify: `images/branding/open-folio-mark.png`
- Modify: `images/branding/open-folio-mark.svg`
- Modify: `images/branding/open-vertaling-logo.png`
- Modify: `images/branding/open-vertaling-logo.svg`
- Modify: `images/branding/open-folio-mark-light.svg`
- Modify: `images/branding/open-vertaling-logo-light.svg`
- Modify: `favicon.svg`
- Modify: `icons/app-icon.svg`
- Modify: `icons/app-icon-maskable.svg`
- Modify: `icons/icon-192.png`
- Modify: `icons/icon-512.png`
- Modify: `icons/icon-maskable-512.png`

**Interfaces:**
- Consumes: definitieve bronset met viewBoxen `0 0 315 315` en `0 0 961 315`.
- Produces: website-, browser- en installatie-assets met dezelfde beeldtaal.

- [ ] **Step 1: Kopieer de vier bronbestanden bytegetrouw**

Kopieer de vier bestanden uit de aangeleverde brandingmap naar `images/branding/` en verifieer de hashes uit Task 1.

- [ ] **Step 2: Bouw de lichte SVG-varianten**

Kopieer de SVG-geometrie en vervang mechanisch alleen `#143247` door `#FFFFFF`.

- [ ] **Step 3: Bouw de favicon- en PWA-SVG's**

Plaats de twee paden uit `open-folio-mark.svg` met voldoende binnenmarge op respectievelijk een lichte, afgeronde achtergrond en een marineblauwe maskable achtergrond.

- [ ] **Step 4: Render de drie PNG-iconen**

Render de gewone iconen op 192×192 en 512×512 en de veilige maskable variant op 512×512. Behoud transparante anti-aliasing en de exacte merk-kleuren.

- [ ] **Step 5: Draai de statische tests groen**

Run: `python -m pytest -q tests/test_branding_en_initialen.py -k "merkassets or favicon"`

Expected: PASS.

---

### Task 3: Borg kopformaat en cacheverversing

**Files:**
- Modify: `css/style.css`
- Modify: `css/lees.css`
- Modify: `sw.js`
- Test: `tests/test_branding_en_initialen.py`

**Interfaces:**
- Consumes: definitieve woordmerken.
- Produces: onvervormde headerlogo's en directe verversing van merkassets.

- [ ] **Step 1: Stuur beide logo's op hoogte en automatische breedte**

Gebruik `height` met `width: auto` en een responsieve `max-width`, zodat de nieuwe verhouding `961 / 315` intact blijft.

- [ ] **Step 2: Geef merkassets een network-first cachepad**

Laat `/images/branding/`, `/favicon.svg` en `/icons/` voor de shellcache online eerst de actuele asset ophalen.

- [ ] **Step 3: Draai de browsertests groen**

Run: `python -m pytest -q tests/test_branding_en_initialen.py`

Expected: PASS op desktop, tablet en mobiel.

---

### Task 4: Verifieer de volledige website

**Files:**
- Verify: alle gewijzigde assets, CSS, service worker en tests.

**Interfaces:**
- Consumes: Task 1–3.
- Produces: een gecontroleerde brandingupdate zonder neveneffecten.

- [ ] **Step 1: Draai gerichte en volledige tests**

Run: `python -m pytest -q tests/test_branding_en_initialen.py && python -m pytest -q`

Expected: alle tests slagen zonder waarschuwingen.

- [ ] **Step 2: Controleer desktop en mobiel visueel**

Bekijk `index.html#genesis/1`, `over-ov.html` en `lees.html` op 1440, 1000 en 390 pixels, plus donker thema in de reader.

- [ ] **Step 3: Controleer de werkboom**

Run: `git status --short && git diff --check`

Expected: uitsluitend de brandingupdate en dit plan zijn gewijzigd; geen whitespacefouten.
