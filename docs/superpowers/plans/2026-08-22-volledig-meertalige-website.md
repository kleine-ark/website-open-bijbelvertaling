# Volledig meertalige Open Vertaling Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Maak iedere publieke pagina volledig beschikbaar in Nederlands, Engels, Frans, Duits, Spaans, Pools, Oekraïens, Arabisch en Turks, waarbij de globale interfacetaal automatisch de passende standaard-Bijbeleditie kiest.

**Architecture:** Eén locale-runtime beheert taal, richting, opslag, URL en editie. Korte interfacekopij staat in localecatalogi; langere redactionele inhoud staat in gelokaliseerde bestanden met dezelfde canonieke ids als de Nederlandse bron. Een buildscript genereert dunne, indexeerbare taalroutes die dezelfde HTML, JavaScript en CSS delen.

**Tech Stack:** Statische HTML, CSS, vanilla JavaScript, JSON, Python-buildscripts, pytest en Playwright.

**Spec:** `docs/superpowers/specs/2026-08-22-volledig-meertalige-website-design.md`

## Global Constraints

- Ondersteun exact `nl`, `en`, `fr`, `de`, `es`, `pl`, `uk`, `ar` en `tr`.
- De locale in de URL wint van opslag; opslag wint van browsertaal; Nederlands is de laatste fallback.
- Een taalwijziging kiest de gekoppelde standaard-Bijbeleditie; een handmatige editiekeuze blijft gelden totdat de taal opnieuw verandert.
- Arabisch gebruikt RTL voor de interface; elementen met een eigen taal behouden hun eigen richting.
- De Turkse editie bevat alleen het Nieuwe Testament; ontbrekende boeken tonen een Turkse melding en een gemarkeerde Nederlandse tekstfallback.
- Canonieke boek-, hoofdstuk-, vers-, onderwerp-, persoon-, plaats- en naslag-ids worden nooit vertaald.
- De publieke taalkeuze blijft verborgen totdat alle verplichte catalogi honderd procent dekking hebben.
- Stage nooit met `git add .`, een wildcard of een hele reeds bestaande map; gebruik de expliciete bestandspaden of de door de inventaris gegenereerde pathspecbestanden uit dit plan.
- Geen externe vertaaldienst wordt tijdens een paginabezoek aangeroepen.
- Bestaande Nederlandse inhoud en instellingen blijven functioneel.
- Elke taak volgt red-green-refactor en commit uitsluitend de genoemde bestanden.

---

### Task 1: Localeregister en i18n-runtime

**Files:**
- Create: `i18n/config.json`
- Modify: `js/i18n.js`
- Create: `tests/test_i18n_runtime.py`
- Modify: `i18n/nl.json`
- Modify: `index.html`
- Modify: `wiki.html`

**Interfaces:**
- Produces: `window.OVI18n.init(): Promise<void>`
- Produces: `window.OVI18n.t(key: string, vars?: object): string`
- Produces: `window.OVI18n.setLocale(locale: string, options?: {navigate?: boolean}): Promise<void>`
- Produces: `window.OVI18n.locale: string`
- Preserves: `window.I18n` as compatibility alias for existing consumers
- Produces: browser event `ov:localechange` with `{locale, edition, direction}`

- [ ] **Step 1: Write the failing runtime tests**

```python
def test_localeconfig_bevat_negen_talen_en_editiekoppelingen():
    config = json.loads((ROOT / "i18n/config.json").read_text("utf-8"))
    assert [item["locale"] for item in config["locales"]] == [
        "nl", "en", "fr", "de", "es", "pl", "uk", "ar", "tr"
    ]
    assert next(x for x in config["locales"] if x["locale"] == "ar")["direction"] == "rtl"
    assert next(x for x in config["locales"] if x["locale"] == "en")["defaultEdition"] == "en-webbe"

def test_urltaal_wint_van_opslag_en_browsertaal(page, site_url):
    page.add_init_script("localStorage.setItem('ov_locale', 'de')")
    page.goto(f"{site_url}/fr/index.html#johannes/1")
    assert page.evaluate("OVI18n.locale") == "fr"
    assert page.locator("html").get_attribute("lang") == "fr"
```

- [ ] **Step 2: Run the tests and verify missing files/API cause failure**

Run: `python -m pytest tests/test_i18n_runtime.py -q`
Expected: FAIL because `i18n/config.json` and `window.OVI18n` do not exist.

- [ ] **Step 3: Add the exact locale registry**

```json
{
  "schema": 1,
  "storageKey": "ov_locale",
  "locales": [
    {"locale":"nl","selfName":"Nederlands","direction":"ltr","defaultEdition":"ov"},
    {"locale":"en","selfName":"English","direction":"ltr","defaultEdition":"en-webbe"},
    {"locale":"fr","selfName":"Français","direction":"ltr","defaultEdition":"fr-lsg1910"},
    {"locale":"de","selfName":"Deutsch","direction":"ltr","defaultEdition":"de-luther1912"},
    {"locale":"es","selfName":"Español","direction":"ltr","defaultEdition":"es-rv1909"},
    {"locale":"pl","selfName":"Polski","direction":"ltr","defaultEdition":"pl-gdanska1881"},
    {"locale":"uk","selfName":"Українська","direction":"ltr","defaultEdition":"uk-ukrfb"},
    {"locale":"ar","selfName":"العربية","direction":"rtl","defaultEdition":"ar-vd"},
    {"locale":"tr","selfName":"Türkçe","direction":"ltr","defaultEdition":"tr-open-basic-nt"}
  ]
}
```

- [ ] **Step 4: Implement locale resolution and translation lookup**

`js/i18n.js` must load `i18n/config.json` and `i18n/<locale>.json`, derive the
route locale from the first pathname segment, validate every locale against the
registry, set `document.documentElement.lang/dir`, interpolate `{name}` tokens
without evaluating HTML, store explicit choices, and dispatch
`ov:localechange`.

- [ ] **Step 5: Load the runtime before shared UI scripts**

Add `<script src="js/i18n.js"></script>` before `js/topnav.js` in
`index.html`, `wiki.html`, and the shared page-header template used by build
scripts. Call `OVI18n.init()` before rendering translated navigation.

- [ ] **Step 6: Run tests and commit**

Run: `python -m pytest tests/test_i18n_runtime.py -q`
Expected: PASS.

```bash
git add i18n/config.json i18n/nl.json js/i18n.js index.html wiki.html tests/test_i18n_runtime.py
git commit -m "Voeg centrale locale-runtime toe"
```

### Task 2: Taalroutes en URL-behoud

**Files:**
- Create: `scripts/build_localized_routes.py`
- Create: `tests/test_build_localized_routes.py`

**Interfaces:**
- Consumes: `i18n/config.json`
- Produces: `build_routes(root: Path, output_root: Path) -> list[Path]`
- Produces: `/<locale>/<page>.html` for every public top-level HTML page

- [ ] **Step 1: Write failing route-generation tests**

```python
def test_build_maakt_deelbare_routes_met_gedeelde_assets(tmp_path):
    generated = build_routes(ROOT, tmp_path)
    english = tmp_path / "en" / "wiki.html"
    assert english in generated
    html = english.read_text("utf-8")
    assert '<html lang="en" dir="ltr" data-locale="en">' in html
    assert '<base href="../">' in html
    assert 'hreflang="ar"' in html

def test_arabische_route_is_rtl(tmp_path):
    build_routes(ROOT, tmp_path)
    html = (tmp_path / "ar" / "index.html").read_text("utf-8")
    assert '<html lang="ar" dir="rtl" data-locale="ar">' in html
```

- [ ] **Step 2: Run and verify RED**

Run: `python -m pytest tests/test_build_localized_routes.py -q`
Expected: FAIL because the builder does not exist.

- [ ] **Step 3: Implement deterministic thin-route generation**

The builder must enumerate public root HTML files from a checked-in allowlist,
insert `<base href="../">`, set `lang`, `dir` and `data-locale`, rewrite
canonical/Open Graph URLs, and add nine `hreflang` links plus `x-default`.
Generated HTML must keep script and stylesheet paths shared through the base
element.

- [ ] **Step 4: Add clean-build and stale-route checks**

Build into a temporary directory, compare expected relative paths, then replace
only generated locale directories. Refuse unknown locales and duplicate
canonicals. Add locale directories to the deployment artifact, not to source
ignore rules that hide required published files.

- [ ] **Step 5: Run tests and commit**

Run: `python -m pytest tests/test_build_localized_routes.py -q`
Expected: PASS.

```bash
git add scripts/build_localized_routes.py tests/test_build_localized_routes.py
git commit -m "Genereer deelbare taalroutes"
```

### Task 3: Globale taalkiezer en toegankelijke navigatie

**Files:**
- Modify: `js/topnav.js`
- Modify: `css/style.css`
- Modify: `i18n/nl.json`
- Create: `tests/test_language_switcher.py`

**Interfaces:**
- Consumes: `OVI18n.setLocale(locale, {navigate: true})`
- Produces: `#topnav-language-button` and `#topnav-language-menu`

- [ ] **Step 1: Write failing desktop/mobile browser tests**

```python
def test_taalkiezer_is_globaal_en_toetsenbordbedienbaar(page, site_url):
    page.goto(f"{site_url}/index.html#johannes/1")
    page.locator("#topnav-language-button").click()
    assert page.locator("#topnav-language-menu [role=menuitemradio]").count() == 9
    page.get_by_role("menuitemradio", name="English").click()
    assert "/en/index.html" in page.url

def test_mobiel_toont_dezelfde_keuze_in_hamburger(page, site_url):
    page.set_viewport_size({"width": 390, "height": 844})
    page.goto(f"{site_url}/wiki.html")
    page.locator("#topnav-hamburger").click()
    assert page.locator("#topnav-language-button").is_visible()
```

- [ ] **Step 2: Run and verify RED**

Run: `python -m pytest tests/test_language_switcher.py -q`
Expected: FAIL because the controls are absent.

- [ ] **Step 3: Render the language menu from the registry**

Use self-names, `role="menu"`, `role="menuitemradio"`, `aria-checked`, Escape,
arrow-key navigation, focus restoration and click-outside closing. Preserve the
current page, query and hash when switching to the corresponding locale route.

- [ ] **Step 4: Style compactly for desktop and mobile**

Use existing navy, gold and surface tokens. Do not add flag emoji. Ensure the
menu stays within the viewport and that Arabic labels render correctly.

- [ ] **Step 5: Run tests and commit**

Run: `python -m pytest tests/test_language_switcher.py tests/test_topnav_quick_actions.py -q`
Expected: PASS.

```bash
git add js/topnav.js css/style.css i18n/nl.json tests/test_language_switcher.py
git commit -m "Voeg globale taalkiezer toe"
```

### Task 4: Taal koppelen aan standaardeditie

**Files:**
- Modify: `js/i18n.js`
- Modify: `js/teksteditie.js`
- Modify: `js/opties.js`
- Modify: `js/app.js`
- Create: `tests/test_locale_edition_binding.py`

**Interfaces:**
- Consumes: `ov:localechange`
- Produces: `Teksteditie.selectForLocale(locale: string): Promise<void>`
- Preserves: manual edition selection until the next locale change

- [ ] **Step 1: Write failing binding tests**

```python
@pytest.mark.parametrize("locale,edition", [
    ("en", "en-webbe"), ("fr", "fr-lsg1910"), ("de", "de-luther1912"),
    ("es", "es-rv1909"), ("pl", "pl-gdanska1881"), ("uk", "uk-ukrfb"),
    ("ar", "ar-vd"), ("tr", "tr-open-basic-nt"), ("nl", "ov")
])
def test_locale_kiest_standaardeditie(page, site_url, locale, edition):
    page.goto(f"{site_url}/{locale}/index.html#johannes/1")
    assert page.evaluate("Teksteditie.getActiveCode()") == edition
```

- [ ] **Step 2: Run and verify RED**

Run: `python -m pytest tests/test_locale_edition_binding.py -q`
Expected: FAIL because locale and edition are not coupled.

- [ ] **Step 3: Implement one-way coupling on locale change**

`selectForLocale` reads `defaultEdition` from the registry, validates it against
`data/vertalingen/manifest.json`, persists it through the existing edition
state, updates the settings UI and rerenders the active chapter exactly once.
Manual edition changes must not change `OVI18n.locale`.

- [ ] **Step 4: Implement generic partial-edition fallback**

When a book is absent from the selected edition, emit
`ov:editionunavailable`, render the locale message using `edition.unavailable`,
temporarily display `ov`, and retain both the interface locale and selected
edition. The next supported book automatically uses the selected edition again.

- [ ] **Step 5: Run tests and commit**

Run: `python -m pytest tests/test_locale_edition_binding.py tests/test_teksteditie.py tests/test_parallel_editions.py -q`
Expected: PASS.

```bash
git add js/i18n.js js/teksteditie.js js/opties.js js/app.js tests/test_locale_edition_binding.py
git commit -m "Koppel interfacetaal aan Bijbeleditie"
```

### Task 5: Eén localegevoelige citaatcomponent

**Files:**
- Modify: `js/tekstweergave.js`
- Modify: `js/gekoppelde-teksten.js`
- Modify: `js/naslag.js`
- Create: `tests/test_multilingual_citations.py`

**Interfaces:**
- Consumes: canonical reference `{bookId, chapter, verseStart, verseEnd}`
- Consumes: `ov:localechange` and active edition events
- Produces: `OVTekstweergave.renderNaslagtekst(citation, reference, options): Promise<void>` with locale-aware edition resolution

- [ ] **Step 1: Write failing cross-page citation tests**

```python
def test_wikicitaat_wisselt_direct_mee_naar_engels(page, site_url):
    page.goto(f"{site_url}/nl/wiki.html#materialen")
    dutch = page.locator("[data-bible-reference]").first.inner_text()
    page.locator("#topnav-language-button").click()
    page.get_by_role("menuitemradio", name="English").click()
    english = page.locator("[data-bible-reference]").first.inner_text()
    assert english != dutch
    assert page.locator("[data-bible-reference]").first.get_attribute("lang") == "en"
```

- [ ] **Step 2: Run and verify RED**

Run: `python -m pytest tests/test_multilingual_citations.py -q`
Expected: FAIL because wiki citations retain the previous edition.

- [ ] **Step 3: Consolidate render paths behind `OVCitaten.render`**

Remove page-specific verse-string construction. Keep canonical references in
data attributes/data objects, load the active edition at render time, reuse the
existing citation typography and add `lang`/`dir` to every rendered citation.

- [ ] **Step 4: Subscribe once to global state events**

Rerender mounted citation roots after locale or edition change. Debounce a
single microtask so a locale change plus its coupled edition change does not
render twice.

- [ ] **Step 5: Run tests and commit**

Run: `python -m pytest tests/test_multilingual_citations.py tests/test_wiki_citation_template.py -q`
Expected: PASS.

```bash
git add js/tekstweergave.js js/gekoppelde-teksten.js js/naslag.js tests/test_multilingual_citations.py
git commit -m "Maak Bijbelcitaten volledig localegevoelig"
```

### Task 6: Vertaalinventaris en harde dekkingstest

**Files:**
- Create: `scripts/i18n_inventory.py`
- Create: `scripts/validate_i18n.py`
- Create: `i18n/inventory.json`
- Create: `i18n/interface-paths.txt`
- Create: `i18n/content-paths.txt`
- Create: `i18n/page-paths.txt`
- Create: `tests/test_i18n_coverage.py`

**Interfaces:**
- Produces: `build_inventory(root: Path) -> dict`
- Produces: `validate_locale(locale: str, inventory: dict) -> list[str]`
- Consumes: `data-i18n`, `OVI18n.t(...)` and localized content schemas

- [ ] **Step 1: Write failing inventory and validation tests**

```python
def test_inventory_vindt_html_en_javascript_sleutels():
    inventory = build_inventory(ROOT)
    assert "nav.read" in inventory["interfaceKeys"]
    assert "settings.theme" in inventory["interfaceKeys"]

def test_iedere_locale_heeft_exact_dezelfde_verplichte_sleutels():
    inventory = json.loads((ROOT / "i18n/inventory.json").read_text("utf-8"))
    for locale in SUPPORTED_LOCALES:
        assert validate_locale(locale, inventory) == []
```

- [ ] **Step 2: Run and verify RED**

Run: `python -m pytest tests/test_i18n_coverage.py -q`
Expected: FAIL because inventory and validator are absent.

- [ ] **Step 3: Implement deterministic extraction and validation**

Scan public HTML and shared JavaScript only. Record key, source file and source
line. Validate missing keys, unexpected keys, interpolation-variable parity,
empty strings, untranslated Dutch values outside an explicit proper-name
allowlist, content-id parity and source-version parity. Write sorted, repository-
relative pathspec files for interface, content and page batches so commits can
stage exact files without wildcards.

- [ ] **Step 4: Generate and inspect the initial inventory**

Run: `python scripts/i18n_inventory.py --write i18n/inventory.json`
Expected: a stable sorted JSON file with no duplicate key definitions.

- [ ] **Step 5: Run tests and commit**

Run: `python -m pytest tests/test_i18n_coverage.py -q`
Expected: PASS for Dutch; other locales remain explicitly disabled in the
public locale registry until their catalog tasks pass.

```bash
git add scripts/i18n_inventory.py scripts/validate_i18n.py i18n/inventory.json i18n/interface-paths.txt i18n/content-paths.txt i18n/page-paths.txt tests/test_i18n_coverage.py
git commit -m "Borg volledige vertaaldekking"
```

### Task 7: Alle gedeelde interfacecomponenten vertalen

**Files:**
- Modify: the exact public root HTML files recorded in `i18n/inventory.json`
- Modify: `js/topnav.js`, `js/opties.js`, `js/search.js`, `js/app.js`, `js/lexicon.js`
- Create: `i18n/en.json`, `i18n/fr.json`, `i18n/de.json`, `i18n/es.json`
- Create: `i18n/pl.json`, `i18n/uk.json`, `i18n/ar.json`, `i18n/tr.json`
- Create: `tests/test_i18n_interface_catalogs.py`

**Interfaces:**
- Consumes: `OVI18n.t` and `i18n/inventory.json`
- Produces: complete interface catalogs for nine locales

- [ ] **Step 1: Add failing representative UI tests for all locales**

```python
@pytest.mark.parametrize("locale,expected", [
    ("nl", "Lezen"), ("en", "Read"), ("fr", "Lire"), ("de", "Lesen"),
    ("es", "Leer"), ("pl", "Czytaj"), ("uk", "Читати"),
    ("ar", "قراءة"), ("tr", "Oku")
])
def test_navigatie_is_vertaald(page, site_url, locale, expected):
    page.goto(f"{site_url}/{locale}/index.html#johannes/1")
    assert page.locator("[data-i18n='nav.read']").inner_text() == expected
```

- [ ] **Step 2: Run and verify RED**

Run: `python -m pytest tests/test_i18n_interface_catalogs.py -q`
Expected: FAIL for every non-Dutch locale.

- [ ] **Step 3: Replace visible literals with semantic keys**

Annotate static nodes with `data-i18n`; replace dynamic literals with
`OVI18n.t`. Cover navigation, hamburger, settings, search, book/chapter picker,
feedback, authentication, map controls, wiki navigation, downloads,
statistics, lexicon and all dialogs. Preserve project names and source titles
as proper nouns.

- [ ] **Step 4: Populate all eight non-Dutch interface catalogs**

Translate every key in `i18n/inventory.json`, preserving interpolation tokens
exactly. Use consistent locale terminology for Bible, book, chapter, verse,
settings, source text, dictionary and commentary.

- [ ] **Step 5: Validate catalogs and commit**

Run: `python scripts/validate_i18n.py --kind interface --all`
Expected: `9 locales, 100% interface coverage`.

Run: `python -m pytest tests/test_i18n_interface_catalogs.py -q`
Expected: PASS.

```bash
git add --pathspec-from-file=i18n/interface-paths.txt
git add i18n/en.json i18n/fr.json i18n/de.json i18n/es.json i18n/pl.json i18n/uk.json i18n/ar.json i18n/tr.json tests/test_i18n_interface_catalogs.py
git commit -m "Vertaal alle interfacecomponenten"
```

### Task 8: Localegebonden boeknamen en zoeken

**Files:**
- Create: `i18n/books/nl.json`, `i18n/books/en.json`, `i18n/books/fr.json`
- Create: `i18n/books/de.json`, `i18n/books/es.json`, `i18n/books/pl.json`
- Create: `i18n/books/uk.json`, `i18n/books/ar.json`, `i18n/books/tr.json`
- Modify: `js/navigation.js`
- Modify: `js/sidebar.js`
- Modify: `js/search.js`
- Modify: `js/app.js`
- Create: `tests/test_localized_book_names.py`

**Interfaces:**
- Produces: `OVI18n.bookName(bookId: string): string`
- Produces: locale-aware aliases used by search and URL labels

- [ ] **Step 1: Write failing book-name and search tests**

```python
def test_boeknamen_volgen_locale(page, site_url):
    page.goto(f"{site_url}/en/index.html#johannes/1")
    assert page.locator("#book-selector").input_value() == "John 1"
    page.goto(f"{site_url}/ar/index.html#johannes/1")
    assert "يوحنا" in page.locator("#book-selector").input_value()
```

- [ ] **Step 2: Run and verify RED**

Run: `python -m pytest tests/test_localized_book_names.py -q`
Expected: FAIL because Dutch names are hard-coded.

- [ ] **Step 3: Add complete canonical-id maps for all locales**

Every locale file must contain every id from `data/books.json`, including
apocryphal and Ethiopian books, plus safe search aliases. The displayed name
changes; hashes and data paths retain the canonical id.

- [ ] **Step 4: Use locale names in reader, navigation and search**

Sort only where the existing UI sorts alphabetically; canonical/theological
book order remains driven by shared data. Search matches locale aliases and
returns locale names.

- [ ] **Step 5: Run tests and commit**

Run: `python -m pytest tests/test_localized_book_names.py -q`
Expected: PASS.

```bash
git add i18n/books/nl.json i18n/books/en.json i18n/books/fr.json i18n/books/de.json i18n/books/es.json i18n/books/pl.json i18n/books/uk.json i18n/books/ar.json i18n/books/tr.json js/navigation.js js/sidebar.js js/search.js js/app.js tests/test_localized_book_names.py
git commit -m "Lokaliseer boeknamen en zoeken"
```

### Task 9: Gestructureerde wiki- en onderwerpinhoud lokaliseren

**Files:**
- Create: `scripts/extract_localizable_content.py`
- Create: `scripts/validate_localized_content.py`
- Create: `i18n/content/<locale>/*.json` for every supported locale
- Create: `js/localized-content.js`
- Modify: `js/naslag.js`, `js/gekoppelde-teksten.js`, `wiki.html`, `onderwerpen.html`
- Create: `tests/test_localized_wiki_content.py`

**Interfaces:**
- Produces: `OVI18n.loadContent(dataset: string): Promise<object>`
- Preserves: ids, references, image paths, coordinates, source URLs and ranks

- [ ] **Step 1: Write failing structure and rendering tests**

```python
def test_gelokaliseerde_inhoud_behoudt_alle_ids_en_referenties():
    for dataset in CONTENT_DATASETS:
        source = load_source(dataset)
        for locale in SUPPORTED_LOCALES:
            translated = load_translation(locale, dataset)
            assert translated_ids(translated) == source_ids(source)
            assert translated_references(translated) == source_references(source)

def test_materialenpagina_is_volledig_frans(page, site_url):
    page.goto(f"{site_url}/fr/wiki.html#materialen")
    assert page.locator("main").get_attribute("lang") == "fr"
    assert page.locator("[data-content-id]").count() > 0
    assert page.locator("main").get_by_text("Materialen", exact=True).count() == 0
```

- [ ] **Step 2: Run and verify RED**

Run: `python -m pytest tests/test_localized_wiki_content.py -q`
Expected: FAIL because localized content does not exist.

- [ ] **Step 3: Extract translatable fields with source hashes**

For every dataset, emit `{schema, sourceHash, items}` where each item is keyed
by canonical id and contains only translatable fields. Reject fields containing
references, coordinates, paths or URLs so they cannot diverge.

- [ ] **Step 4: Produce complete translations for all eight target locales**

Cover wiki overview, topics, materials, animals, plants, songs, prayers,
geography, persons, genealogies, peoples, nations, instruments, festivals,
blessings, curses, promises and every other dataset in the inventory. Preserve
Bible terminology using locale glossaries checked into
`i18n/glossaries/<locale>.json`.

- [ ] **Step 5: Switch renderers to merged shared/localized data**

Load the shared factual dataset and merge translated fields by id. On missing
content, render a development error marker and fail validation; do not silently
publish Dutch text in a non-Dutch locale.

- [ ] **Step 6: Validate and commit**

Run: `python scripts/validate_localized_content.py --all`
Expected: `9 locales, 100% content-id and field coverage`.

Run: `python -m pytest tests/test_localized_wiki_content.py -q`
Expected: PASS.

```bash
git add --pathspec-from-file=i18n/content-paths.txt
git add scripts/extract_localizable_content.py scripts/validate_localized_content.py js/localized-content.js js/naslag.js js/gekoppelde-teksten.js wiki.html onderwerpen.html tests/test_localized_wiki_content.py
git commit -m "Vertaal alle wiki- en onderwerpinhoud"
```

### Task 10: Overige redactionele pagina's volledig lokaliseren

**Files:**
- Modify: the exact public HTML pages named in the checked-in route allowlist
- Create: `i18n/pages/<locale>/<page>.json` for every supported locale/page
- Modify: `js/i18n.js`
- Create: `tests/test_localized_public_pages.py`

**Interfaces:**
- Produces: `OVI18n.applyPageCatalog(pageId: string): Promise<void>`
- Consumes: nodes marked with `data-i18n-page`

- [ ] **Step 1: Write failing page-matrix tests**

```python
@pytest.mark.parametrize("locale", SUPPORTED_LOCALES)
@pytest.mark.parametrize("page_name", PUBLIC_PAGES)
def test_publieke_pagina_heeft_volledige_localecatalogus(locale, page_name):
    catalog = ROOT / "i18n" / "pages" / locale / f"{page_name}.json"
    assert catalog.exists()
    assert validate_page_catalog(locale, page_name) == []
```

- [ ] **Step 2: Run and verify RED**

Run: `python -m pytest tests/test_localized_public_pages.py -q`
Expected: FAIL for every missing page catalog.

- [ ] **Step 3: Mark page content with stable keys**

Cover Over OV, uitgangspunten, principes, bronnen, downloads, statistieken,
woordenboeken, kaart, personen/stambomen, handschriften, changelog and all
other allowlisted public pages. Put complete paragraphs, headings, captions,
tables and accessible labels in page catalogs; do not translate URLs or source
titles.

- [ ] **Step 4: Translate all page catalogs**

Populate every required key for every locale. Keep HTML markup outside
translations where possible; when inline emphasis is required, use a validated
rich-text field that permits only `em`, `strong`, `cite`, `a`, `sup` and `sub`.

- [ ] **Step 5: Run the complete page matrix and commit**

Run: `python -m pytest tests/test_localized_public_pages.py -q`
Expected: PASS for all locale/page combinations.

```bash
git add --pathspec-from-file=i18n/page-paths.txt
git add js/i18n.js tests/test_localized_public_pages.py
git commit -m "Vertaal alle publieke redactionele pagina's"
```

### Task 11: Volledige RTL-laag voor Arabisch

**Files:**
- Modify: `css/style.css`, `css/naslag.css`, `css/kaart.css`, `css/lees.css`
- Create: `tests/test_arabic_rtl.py`

**Interfaces:**
- Consumes: `html[dir="rtl"]`
- Preserves: explicit `dir` on Bible text, lexicon entries and technical tokens

- [ ] **Step 1: Write failing RTL geometry and direction tests**

```python
def test_arabische_interface_is_rtl_met_correcte_uitzonderingen(page, site_url):
    page.goto(f"{site_url}/ar/index.html#johannes/1")
    assert page.locator("html").get_attribute("dir") == "rtl"
    assert page.locator("#topnav-links").evaluate("e => getComputedStyle(e).direction") == "rtl"
    assert page.locator(".strongs-inline").first.get_attribute("dir") == "ltr"
```

- [ ] **Step 2: Run and verify RED**

Run: `python -m pytest tests/test_arabic_rtl.py -q`
Expected: FAIL on layout or explicit-direction assertions.

- [ ] **Step 3: Replace directional CSS with logical properties**

Use inline/block logical properties in shared layout, navigation, wiki sidebar,
cards, settings, dialogs and citation components. Add explicit `dir="ltr"` or
content-language direction only to tokens that must not inherit RTL.

- [ ] **Step 4: Verify representative desktop and mobile pages**

Run Playwright screenshots at 1440×1000 and 390×844 for reader, wiki,
materials, map, settings and lexicon. Assert no horizontal overflow with
`document.documentElement.scrollWidth <= window.innerWidth`.

- [ ] **Step 5: Run tests and commit**

Run: `python -m pytest tests/test_arabic_rtl.py -q`
Expected: PASS.

```bash
git add css/style.css css/naslag.css css/kaart.css css/lees.css tests/test_arabic_rtl.py
git commit -m "Maak Arabische interface volledig RTL"
```

### Task 12: Gelokaliseerde SEO, sitemap en manifesten

**Files:**
- Modify: `scripts/build_localized_routes.py`
- Modify: `manifest.json`
- Create: `scripts/build_multilingual_sitemap.py`
- Create: `tests/test_multilingual_seo.py`

**Interfaces:**
- Produces: locale-aware title, description, Open Graph, Twitter and JSON-LD
- Produces: sitemap entries with nine alternate-language links
- Produces: `/<locale>/manifest.json`

- [ ] **Step 1: Write failing SEO tests**

```python
def test_iedere_route_heeft_canonical_en_negen_hreflangs(localized_build):
    for locale in SUPPORTED_LOCALES:
        doc = parse(localized_build / locale / "wiki.html")
        assert doc.canonical == f"https://openvertaling.nl/{locale}/wiki.html"
        assert set(doc.hreflangs) == set(SUPPORTED_LOCALES) | {"x-default"}
        assert doc.og_locale == OG_LOCALES[locale]
```

- [ ] **Step 2: Run and verify RED**

Run: `python -m pytest tests/test_multilingual_seo.py -q`
Expected: FAIL because localized metadata is incomplete.

- [ ] **Step 3: Generate localized metadata and manifests**

Read titles/descriptions from page catalogs. Set locale-specific Open Graph
locale, canonical and alternates. Generate a manifest whose name, description,
start URL, shortcuts and language match the route locale.

- [ ] **Step 4: Generate sitemap alternates**

Emit one URL entry per locale/page with XHTML alternate links for all available
locales and `x-default` to Dutch. Validate URL uniqueness and existence in the
built artifact.

- [ ] **Step 5: Run tests and commit**

Run: `python -m pytest tests/test_multilingual_seo.py tests/test_brand_metadata.py -q`
Expected: PASS.

```bash
git add scripts/build_localized_routes.py scripts/build_multilingual_sitemap.py manifest.json tests/test_multilingual_seo.py
git commit -m "Voeg meertalige SEO en manifests toe"
```

### Task 13: Publicatiepoort en volledige browsermatrix

**Files:**
- Create: `scripts/check_multilingual_release.py`
- Create: `tests/test_multilingual_release.py`
- Modify: `.github/workflows/deploy.yml`
- Modify: `i18n/config.json`

**Interfaces:**
- Produces: exit code `0` only at complete nine-locale coverage
- Produces: machine-readable `build/i18n-report.json`

- [ ] **Step 1: Write failing release-gate tests**

```python
def test_releasepoort_weigert_ontbrekende_vertaling(tmp_path):
    result = check_release(fixture_with_missing_key(tmp_path))
    assert result.ok is False
    assert result.errors[0]["locale"] == "fr"

def test_volledige_fixture_mag_publiceren(tmp_path):
    result = check_release(complete_fixture(tmp_path))
    assert result.ok is True
```

- [ ] **Step 2: Run and verify RED**

Run: `python -m pytest tests/test_multilingual_release.py -q`
Expected: FAIL because the gate is absent.

- [ ] **Step 3: Implement the release report**

Aggregate interface, content, page, route, metadata, edition and RTL checks.
Report counts and exact source ids for failures. Exit nonzero on any missing
key, stale source hash, broken link, missing route or Dutch leakage.

- [ ] **Step 4: Run the complete browser matrix**

For each locale test desktop and mobile: reader, language switch, settings,
search, wiki overview, one topic, one material, map, lexicon, downloads and one
partial-edition failure. Confirm chosen locale and edition survive refresh and
internal navigation.

- [ ] **Step 5: Enable public locale entries only after the gate passes**

Set every locale entry in `i18n/config.json` to `"public": true` in the same
commit in which `check_multilingual_release.py` exits zero against the actual
repository.

- [ ] **Step 6: Run final verification and commit**

Run: `python scripts/check_multilingual_release.py`
Expected: `9 locales, 137 pages, 100% interface and content coverage` and exit
code `0`.

Run: `python -m pytest tests/test_i18n_runtime.py tests/test_build_localized_routes.py tests/test_language_switcher.py tests/test_locale_edition_binding.py tests/test_multilingual_citations.py tests/test_i18n_coverage.py tests/test_i18n_interface_catalogs.py tests/test_localized_book_names.py tests/test_localized_wiki_content.py tests/test_localized_public_pages.py tests/test_arabic_rtl.py tests/test_multilingual_seo.py tests/test_multilingual_release.py -q`
Expected: PASS.

```bash
git add scripts/check_multilingual_release.py tests/test_multilingual_release.py i18n/config.json .github/workflows/deploy.yml
git commit -m "Publiceer volledige meertalige website"
```
