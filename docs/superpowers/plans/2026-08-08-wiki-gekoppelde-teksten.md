# Wiki Gekoppelde Bijbelteksten Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Toon op Tijdsaanduidingen, Materialen, Dieren en Bomen & planten de actuele gekoppelde versteksten met dezelfde `+`/`−`-contextbediening als Onderwerpen.

**Architecture:** Eén gedeelde browsermodule rendert volledige referenties via `window.OSV.cite()` en beheert lazy loading plus context binnen hetzelfde hoofdstuk. De drie JSON-gedreven naslagpagina's normaliseren hun bestaande korte referenties voor die module; Tijdsaanduidingen krijgt gegenereerde referentiedata zodat voorbeelden en tellingen niet uiteenlopen.

**Tech Stack:** statische HTML, vanilla JavaScript zonder lookbehind, CSS, Python 3.11, pytest/unittest, Playwright, bestaande `embed.js`-API.

## Global Constraints

- Gebruik uitsluitend `text2026` via `window.OSV.cite(ref, {link: false})`; sla geen tweede verstekstkopie op.
- `+` toont maximaal twee bestaande verzen vóór en twee na het hoofdvers; `−` herstelt alleen het hoofdvers.
- Context gaat nooit over een hoofdstukgrens.
- Zonder `IntersectionObserver` laden de hoofdverzen direct.
- Een fout in één versblok mag de referentie en de overige pagina niet onbruikbaar maken.
- Blijf geschikt voor iPadOS 15.4: geen lookbehind en geen nieuwere ongeteste browser-API's.
- Behoud de reeds aanwezige wijzigingen in `css/naslag.css` en `js/naslag.js`; inspecteer vóór iedere commit uitsluitend bedoelde hunks.
- Liederen en Gebeden vallen buiten deze korte vindplaatsweergave.

---

## File Structure

- Create `js/gekoppelde-teksten.js`: renderer, lazy loading en contextinteractie.
- Create `scripts/build_tijdsaanduidingen_data.py`: leidt alle tijdsreferenties af uit `text2026` en `data/tijden.json`.
- Create `data/naslag-tijdsaanduidingen.json`: gegenereerde referenties per zichtbare tijdsgroep, zonder versteksten.
- Create `tests/test_wiki_gekoppelde_teksten.py`: browsergedrag.
- Create `tests/test_tijdsaanduidingen_data.py`: bouw- en bronvalidatie.
- Modify `js/naslag.js`: zet naslagreferenties om naar het gedeelde component.
- Modify `css/naslag.css`: versblok-, context-, fout-, focus- en mobiele opmaak.
- Modify `materialen.html`, `dieren.html`, `bomen-planten.html`: laad `embed.js` en de renderer vóór `js/naslag.js`.
- Modify `data/naslag-materialen.json`, `data/naslag-dieren.json`, `data/naslag-bomen-planten.json`: voeg het machineleesbare `bronId` toe.
- Modify `tijdsaanduidingen.html`: koppel tabelrijen en groepen aan de gegenereerde data.

### Task 1: Gedeelde renderer met lazy loading en context

**Files:**
- Create: `js/gekoppelde-teksten.js`
- Modify: `css/naslag.css`
- Create: `tests/test_wiki_gekoppelde_teksten.py`

**Interfaces:**
- Consumes: `window.OSV.cite(ref, {link: false}) -> Promise<{html, label, url}>`.
- Produces: `window.GekoppeldeTeksten.render(container, references, options) -> void`.
- `references`: `Array<{ref: string, label: string, href: string}>`; `ref` is `boek hoofdstuk:vers`.
- `options`: `{target?: string}`, standaard `{target: '_top'}`.

- [ ] **Step 1: Schrijf een falende browsertest voor hoofdtekst en knoppen**

Gebruik de stille HTTP-server en Playwright-opzet uit `tests/test_wiki_reading_gutter.py`. Laat een testfixture een pagina openen met `embed.js`, `js/gekoppelde-teksten.js`, `css/naslag.css` en:

```html
<ol id="houder" class="gt-lijst"></ol>
<script>
GekoppeldeTeksten.render(document.getElementById('houder'), [
  {ref: 'genesis 2:11', label: 'Genesis 2:11', href: 'index.html#genesis/2/11'}
]);
</script>
```

Controleer `.gt-vers[data-ref="genesis 2:11"]`, tekst met `goud`, een zichtbare `.gt-plus[aria-label="Meer context eromheen"]` en een verborgen `.gt-min[aria-label="Minder context"]`.

- [ ] **Step 2: Draai de test en bevestig de verwachte fout**

Run: `python -m pytest tests/test_wiki_gekoppelde_teksten.py -q`

Expected: FAIL omdat de module en `.gt-vers` ontbreken.

- [ ] **Step 3: Implementeer de publieke API en basis-DOM**

Publiceer `window.GekoppeldeTeksten.render(container, references, options)` en
`window.GekoppeldeTeksten.refParts(ref)`. `refParts()` gebruikt
`/^(\S+)\s+(\d+):(\d+)$/` en retourneert bij een geldige invoer
`{book: m[1], chapter: Number(m[2]), verse: Number(m[3])}`, anders `null`.

Elk item wordt:

```html
<li class="gt-vers" data-ref="genesis 2:11" data-level="0">
  <div class="gt-vers-kop">
    <a target="_top" href="index.html#genesis/2/11">Genesis 2:11</a>
    <button type="button" class="gt-min" aria-label="Minder context" hidden>−</button>
    <button type="button" class="gt-plus" aria-label="Meer context eromheen">+</button>
  </div>
  <div class="gt-vers-tekst osv-cite"></div>
</li>
```

Gebruik één gedelegeerde click-handler. `renderContext(li, level)` berekent `span = 2 * level`, roept `OSV.cite()` aan en markeert teruggegeven `.osv-vers` als `focus-vers` of `context-vers`. Bij een fout toont alleen dat blok `De tekst kon niet geladen worden.` Een `IntersectionObserver` gebruikt `rootMargin: '400px'`; de fallback laadt direct.

- [ ] **Step 4: Voeg component-CSS toe**

Gebruik de bestaande Onderwerpen-vormtaal met de nieuwe, afgeschermde klassen `.gt-lijst`, `.gt-vers`, `.gt-vers-kop`, `.gt-vers-tekst`, `.gt-plus`, `.gt-min`, `.focus-vers`, `.context-vers` en `.gt-fout`. Neem ook `:focus-visible`, donker thema en de bestaande mobiele 16px-leesmarge op; wijzig de huidige `.page`-regels niet.

- [ ] **Step 5: Voeg context-, grens- en fouttests toe**

Test Genesis 2:1 (`+` blijft in hoofdstuk 2), Genesis 2:11 (`+` toont 9–13 en markeert 11), `−` (alleen vers 11) en een ongeldige referentie (foutmelding, link blijft bestaan).

- [ ] **Step 6: Draai en commit**

Run: `python -m pytest tests/test_wiki_gekoppelde_teksten.py -q`

Expected: PASS.

```powershell
git add -- js/gekoppelde-teksten.js css/naslag.css tests/test_wiki_gekoppelde_teksten.py
git diff --cached --check
git commit -m "feat: voeg gedeelde wikiversteksten toe"
```

### Task 2: Materialen, dieren en bomen & planten aansluiten

**Files:**
- Modify: `js/naslag.js`
- Modify: `materialen.html`
- Modify: `dieren.html`
- Modify: `bomen-planten.html`
- Modify: `data/naslag-materialen.json`
- Modify: `data/naslag-dieren.json`
- Modify: `data/naslag-bomen-planten.json`
- Modify: `tests/test_wiki_gekoppelde_teksten.py`

**Interfaces:**
- Consumes: `GekoppeldeTeksten.render()` uit Task 1.
- Produces: `naslagRef(data, ref) -> {ref, label, href}` binnen `js/naslag.js`.

- [ ] **Step 1: Schrijf falende integratietests**

Open `/materialen.html?item=goud`, `/dieren.html?item=vee` en `/bomen-planten.html?item=de-boom-van-het-leven`. Controleer 8, 34 en 3 `.gt-vers`-items, niet-lege eerste tekst en een correcte eerste link naar `index.html#genesis/<hoofdstuk>/<vers>`.

- [ ] **Step 2: Draai de test en bevestig dat alleen chips bestaan**

Run: `python -m pytest tests/test_wiki_gekoppelde_teksten.py -q`

Expected: FAIL op ontbrekende `.gt-vers`.

- [ ] **Step 3: Voeg een stabiel bron-id en scripts toe**

Voeg in elk van de drie databestanden naast `bron: "Genesis"` toe:

```json
"bronId": "genesis"
```

Laad in elk HTML-bestand direct vóór `js/naslag.js`:

```html
<script src="embed.js"></script>
<script src="js/gekoppelde-teksten.js"></script>
```

- [ ] **Step 4: Vervang de chipweergave door de gedeelde renderer**

Definieer in `js/naslag.js`:

```javascript
function naslagRef(d, ref) {
    var i = ref.indexOf(' ');
    var volledig = i > 0 ? ref.toLowerCase() : d.bronId + ' ' + ref;
    var m = volledig.match(/^(\S+)\s+(\d+):(\d+)$/);
    return {
        ref: volledig,
        label: i > 0 ? ref.charAt(0).toUpperCase() + ref.slice(1) : d.bron + ' ' + ref,
        href: 'index.html#' + m[1] + '/' + m[2] + '/' + m[3]
    };
}
```

Laat `toonItem()` `<ol class="gt-lijst" id="naslag-gekoppelde-teksten"></ol>`
renderen en roep daarna `GekoppeldeTeksten.render()` aan met
`it.verzen.map(function (ref) { return naslagRef(d, ref); })`. Behoud de kop
`Vindplaatsen in <bron>`.

- [ ] **Step 5: Draai en commit**

Run: `python -m pytest tests/test_wiki_gekoppelde_teksten.py -q`

Expected: PASS voor alle drie pagina's.

```powershell
git add -- js/naslag.js materialen.html dieren.html bomen-planten.html data/naslag-materialen.json data/naslag-dieren.json data/naslag-bomen-planten.json tests/test_wiki_gekoppelde_teksten.py
git diff --cached --check
git commit -m "feat: toon teksten bij wiki-naslagitems"
```

### Task 3: Volledige tijdsreferenties genereren

**Files:**
- Create: `scripts/build_tijdsaanduidingen_data.py`
- Create: `data/naslag-tijdsaanduidingen.json`
- Create: `tests/test_tijdsaanduidingen_data.py`

**Interfaces:**
- Consumes: `data/books.json`, `data/tijden.json` en `data/<boek>/<hoofdstuk>.json`.
- Produces: `collect_time_references(root: pathlib.Path) -> dict` met `groups`.
- Groep: `{"id": str, "label": str, "references": [{"ref": str, "label": str}]}`.

- [ ] **Step 1: Schrijf falende bouwtests**

Controleer deze koppelingen:

```python
assert "markus 15:25" in refs(data, "dag-3")
assert "johannes 4:52" in refs(data, "dag-7")
assert "handelingen 23:23" in refs(data, "nacht-3")
assert "4baruch 1:11" in refs(data, "nacht-6")
assert "richteren 7:19" in refs(data, "middelste-waak")
assert "exodus 14:24" in refs(data, "morgenwake")
```

Valideer daarnaast dat iedere referentie naar een bestaand, niet-leeg `text2026`-vers wijst en dat de verzameling omgerekende verzen precies 52 unieke referenties bevat.

- [ ] **Step 2: Draai en bevestig het ontbreken van builder/data**

Run: `python -m pytest tests/test_tijdsaanduidingen_data.py -q`

Expected: FAIL op import of ontbrekend JSON.

- [ ] **Step 3: Implementeer de builder**

De builder compileert Python-regexen zonder lookbehind uit `rangtelwoorden`, `genoemdeWaken`, `frases` en `toelichtingen` in `data/tijden.json`; scant uitsluitend `verse["text2026"]`; onderscheidt dag/nacht aan expliciete dagdeelwoorden; past `alleenIn` toe; dedupliceert per groep; en sorteert canoniek via `data/books.json`, dan hoofdstuk en vers.

`main()` schrijft deterministisch:

```python
output.write_text(
    json.dumps(collect_time_references(root), ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
)
```

- [ ] **Step 4: Bouw, test determinisme en commit**

```powershell
python scripts/build_tijdsaanduidingen_data.py
python -m pytest tests/test_tijdsaanduidingen_data.py -q
git diff --exit-code -- data/naslag-tijdsaanduidingen.json
git add -- scripts/build_tijdsaanduidingen_data.py data/naslag-tijdsaanduidingen.json tests/test_tijdsaanduidingen_data.py
git diff --cached --check
git commit -m "feat: bouw vindplaatsen voor tijdsaanduidingen"
```

Expected: tests PASS en een tweede build veroorzaakt geen diff.

### Task 4: Tijdstabellen aan tekstweergave koppelen

**Files:**
- Modify: `tijdsaanduidingen.html`
- Modify: `tests/test_wiki_gekoppelde_teksten.py`

**Interfaces:**
- Consumes: `data/naslag-tijdsaanduidingen.json` en `GekoppeldeTeksten.render()`.
- Produces: `data-tijdgroep="<group-id>"` op relevante rijen en `.me-teksten-rij` direct eronder.

- [ ] **Step 1: Schrijf falende tests voor vier soorten tijdsgroepen**

Controleer op `/tijdsaanduidingen.html` dat `dag-3`, `nacht-6`, `morgenwake` en `tweeavonden` elk `.gt-vers` bevatten, `dag-1` geen lege `.me-teksten-rij` krijgt en `.me-tel` voor `dag-3` overeenkomt met de gegenereerde referenties.

- [ ] **Step 2: Draai en bevestig dat de tabel statisch is**

Run: `python -m pytest tests/test_wiki_gekoppelde_teksten.py -q`

Expected: FAIL op ontbrekende groepen.

- [ ] **Step 3: Voeg bronnen, scripts en dynamische rijen toe**

Laad `css/naslag.css` in `<head>` en onderaan:

```html
<script src="embed.js"></script>
<script src="js/gekoppelde-teksten.js"></script>
```

Geef bronrijen `data-tijdgroep`. Maak voor nachtwaken benoemde bronregels waar nu één lopende vindplaatsenalinea staat. Een IIFE laadt de JSON, bouwt uitsluitend voor gevulde groepen `<tr class="me-teksten-rij"><td colspan="3"><ol class="gt-lijst"></ol></td></tr>`, leidt `.me-tel` af uit `references.length` en roept de renderer aan.

- [ ] **Step 4: Voeg mobiele tests toe**

Bij 390 px moet de detailrij als blok onder de bronrij staan, niet horizontaal overlopen en minstens 16 px leesmarge houden.

- [ ] **Step 5: Draai en commit**

```powershell
python -m pytest tests/test_wiki_gekoppelde_teksten.py tests/test_wiki_reading_gutter.py -q
git add -- tijdsaanduidingen.html tests/test_wiki_gekoppelde_teksten.py
git diff --cached --check
git commit -m "feat: toon teksten bij tijdsaanduidingen"
```

Expected: PASS.

### Task 5: Eindverificatie en lokale visuele controle

**Files:**
- Verify only; wijzig uitsluitend bij een aantoonbare test- of weergavefout.

**Interfaces:**
- Consumes: alle deliverables uit Tasks 1–4.
- Produces: geverifieerde statische site.

- [ ] **Step 1: Draai de relevante suite**

```powershell
python -m pytest tests/test_wiki_gekoppelde_teksten.py tests/test_tijdsaanduidingen_data.py tests/test_wiki_reading_gutter.py tests/test_wiki_cinemagraphs.py -q
```

Expected: alle tests PASS.

- [ ] **Step 2: Controleer data en diffhygiëne**

```powershell
python scripts/build_tijdsaanduidingen_data.py
git diff --check
git status --short
```

Expected: geen onverwachte nieuwe wijziging of whitespacefout.

- [ ] **Step 3: Controleer visueel**

Open lokaal Materialen/goud, Dieren/vee, Bomen & planten/boom van het leven en Tijdsaanduidingen. Controleer hoofdvers, `+`, `−`, focusaccent, foutgedrag, donker thema, 1450 px en 390 px.

- [ ] **Step 4: Corrigeer en herhaal alleen indien nodig**

Stage uitsluitend een aantoonbare correctie, herhaal Step 1 en commit met een specifieke boodschap zoals `fix: herstel mobiele tijdsteksten`.
