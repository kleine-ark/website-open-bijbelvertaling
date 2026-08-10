# Meertalige Bijbelteksten Fase 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Een reproduceerbare import en werkende teksteditiekeuze voor Frans, Engels, Arabisch en Spaans, met Nederlandse bediening en tekstgebonden RTL.

**Architecture:** Een Python-converter zet de ongewijzigde USFM-bronnen om naar een compact, editie-onafhankelijk hoofdstukschema en schrijft manifest plus controleverslag. Een kleine browsermodule bepaalt de actieve editie en past buitenlandse hoofdstukken aan op het bestaande lezerscontract; de bestaande lezer blijft eigenaar van navigatie en presentatie.

**Tech Stack:** Python 3, statische UTF-8 JSON, browser-JavaScript zonder buildstap, pytest en Playwright.

## Global Constraints

- `nl-ov` blijft de standaard en de bediening blijft Nederlands.
- Buitenlandse tekst wordt inhoudelijk niet gewijzigd en OV-weergavevervangingen worden daarop niet toegepast.
- Arabische tekstblokken krijgen `lang="ar"` en `dir="rtl"`; de pagina blijft `lang="nl"` en LTR.
- Ontbrekende boeken vallen niet stilzwijgend terug op Nederlands.
- Bronbestanden en gegenereerde bestanden blijven gescheiden.

---

### Task 1: Deterministische USFM-converter

**Files:**
- Create: `scripts/build_vertalingen.py`
- Create: `tests/test_build_vertalingen.py`
- Generate: `data/vertalingen/manifest.json`
- Generate: `data/vertalingen/rapport.json`
- Generate: `data/vertalingen/<editie>/<boek>/<hoofdstuk>.json`

**Interfaces:**
- Produces: `convert_all(root: Path, output: Path) -> dict` en het genormaliseerde hoofdstukschema uit de goedgekeurde specificatie.

- [ ] Schrijf tests voor boekcodekoppeling, Unicode, `\\w`, voetnoten, kruisverwijzingen en idempotente uitvoer.
- [ ] Voer de tests uit en bevestig dat ze falen omdat de converter ontbreekt.
- [ ] Implementeer de allowlist-parser en manifest/rapportgenerator.
- [ ] Voer unit-tests uit, converteer alle vier corpora en vergelijk de tweede run byte-voor-byte.

### Task 2: Editie- en laadlaag

**Files:**
- Create: `js/teksteditie.js`
- Modify: `js/data-loader.js`
- Create: `tests/test_teksteditie.py`

**Interfaces:**
- Produces: `window.TekstEditie.code()`, `.metadata()`, `.loadChapter(bookId, chapter)` en `.chapterToReaderData(chapter)`.

- [ ] Schrijf browsertests voor standaardeditie, `?editie=`-prioriteit, opslag zonder URL-overschrijving en ontbrekend boek.
- [ ] Bevestig de verwachte failures.
- [ ] Implementeer manifestladen, gecachte hoofdstukken en adaptatie naar `text2026_html`.
- [ ] Laat `DataLoader.loadChapter` voor niet-Nederlandse edities via deze laag lopen en valideer de tests.

### Task 3: Leesvoorkeur en RTL-presentatie

**Files:**
- Modify: `index.html`
- Modify: `js/opties.js`
- Modify: `js/app.js`
- Modify: `css/style.css`
- Test: `tests/test_teksteditie.py`

**Interfaces:**
- Consumes: `TekstEditie` uit Task 2.
- Produces: instelling `teksteditie` in `sv2026_vertaalopties` en `lang`/`dir` op `.col-2026`.

- [ ] Schrijf browsertests die editie wisselen zonder reload en Arabische tekst RTL tonen terwijl `document.documentElement.lang === 'nl'`.
- [ ] Bevestig de verwachte failures.
- [ ] Voeg de vijf teksteditiekeuzes toe en laat wijziging caches legen en het hoofdstuk opnieuw renderen.
- [ ] Sla OV-transformaties over voor buitenlandse edities en toon een expliciete dekkingsmelding.
- [ ] Voer gerichte en bestaande opties-/lezertests uit.

### Task 4: i18n-fundament en verslag

**Files:**
- Create: `i18n/nl.json`
- Create: `js/i18n.js`
- Modify: `index.html`
- Test: `tests/test_teksteditie.py`

**Interfaces:**
- Produces: `window.I18n.t(key, variables)` met Nederlandse fallbackcatalogus voor nieuwe editie-ui en foutmeldingen.

- [ ] Schrijf tests voor bestaande sleutels en zichtbare Nederlandse meldingen zonder sleutelcodes.
- [ ] Bevestig de verwachte failures.
- [ ] Implementeer cataloguslader en gebruik hem in de nieuwe editiecomponenten.
- [ ] Draai convertervalidatie, gerichte browsertests en de relevante regressiesuite; rapporteer exacte corpusdekking.
