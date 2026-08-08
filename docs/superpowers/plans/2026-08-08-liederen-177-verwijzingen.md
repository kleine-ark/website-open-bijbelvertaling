# Liederen 177 en tegelverwijzingen Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Bouw een canonieke, doorlopend genummerde reeks van 177 liederen met 150 losse Psalmen, vijf losse Klaagliederen, een passage op iedere tegel en zonder dubbele vindplaatsensectie op lieddetailpagina’s.

**Architecture:** `data/naslag-liederen.json` blijft de expliciete bronvolgorde en bevat ieder zichtbaar lied als zelfstandig item. `scripts/build_naslag_teksten.py` valideert het vaste aantal en bouwt één tekstbundel per item; `js/naslag.js` rendert de bronitems en gebruikt `tekstpassages` voor de tegelverwijzing. De bestaande opruimstap in `write_collection()` verwijdert bundels van vervallen items.

**Tech Stack:** Statische HTML/CSS/JavaScript, JSON, Python 3, pytest, unittest en Playwright.

## Global Constraints

- De lijst bevat exact 177 lieditems en geen apocriefe liederen.
- Psalm 1–150 en Klaaglied 1–5 krijgen ieder een eigen liednummer en tekstbundel.
- Het lied bij de Schelfzee is Lied 1; Psalm 1 Lied 12; Psalm 150 Lied 161; Klaaglied 1 Lied 167; Klaaglied 5 Lied 171; Het nieuwe lied Lied 176; Mozes en het Lam Lied 177.
- De niet-overgeleverde lofzang bij het avondmaal en Paulus en Silas vervallen.
- Iedere tegel toont een passage, maar nooit een vindplaatsenaantal.
- Lieddetailpagina’s tonen geen sectie `Vindplaatsen in de hele Bijbel`; gebedspagina’s behouden die sectie.
- Bestaande, gelijktijdige wijzigingen buiten deze bestanden blijven ongemoeid.

---

### Task 1: Leg de nieuwe catalogus en nummergrenzen test-first vast

**Files:**
- Modify: `tests/test_naslag_liederen_gebeden.py`
- Modify: `tests/test_wiki_liederen_gebeden.py`
- Modify: `tests/test_wiki_reading_gutter.py`

**Interfaces:**
- Consumes: `data/naslag-liederen.json`, `build_all(ROOT, write=False)` en de DOM uit `js/naslag.js`.
- Produces: regressietests voor 177 items, nummergrenzen, uitsluitingen, tegelpassages en detailsecties.

- [ ] **Step 1: Vervang de oude lijstverwachting door de canonieke reeks**

```python
LIED_IDS = [
    "lied-bij-de-schelfzee",
    "lied-van-mirjam",
    "lied-van-de-bron",
    "lied-van-mozes",
    "lied-van-debora-en-barak",
    "lofzang-van-hanna",
    "beurtzang-van-de-vrouwen",
    "davids-klaaglied",
    "loflied-bij-de-ark",
    "davids-lied-van-bevrijding",
    "laatste-woorden-van-david",
    *[f"psalm-{number}" for number in range(1, 151)],
    "het-hooglied",
    "lied-van-de-wijngaard",
    "lied-van-de-sterke-stad",
    "lofzang-van-hizkia",
    "gebed-van-habakuk",
    *[f"klaaglied-{number}" for number in range(1, 6)],
    "lofzang-van-maria",
    "lofzang-van-zacharias",
    "engelenzang",
    "lofzang-van-simeon",
    "het-nieuwe-lied",
    "gezang-van-mozes-en-het-lam",
]
```

- [ ] **Step 2: Voeg gerichte catalogusasserties toe**

```python
def test_psalmen_en_klaagliederen_krijgen_eigen_liednummers(liederen):
    ids = [item["id"] for item in liederen["items"]]
    assert len(ids) == 177
    assert ids.index("psalm-1") + 1 == 12
    assert ids.index("psalm-150") + 1 == 161
    assert ids.index("klaaglied-1") + 1 == 167
    assert ids.index("klaaglied-5") + 1 == 171
    assert ids[-2:] == ["het-nieuwe-lied", "gezang-van-mozes-en-het-lam"]
```

```python
def test_liederen_zonder_overgeleverde_woorden_en_apocriefen_ontbreken(liederen):
    ids = {item["id"] for item in liederen["items"]}
    assert ids.isdisjoint({
        "lofzang-in-henoch", "loflied-van-tobit", "gezang-in-de-vuuroven",
        "loflied-van-judith", "dankgebed-van-jezus-sirach",
        "lofzang-bij-het-avondmaal", "paulus-en-silas",
    })
```

- [ ] **Step 3: Pas de browserverwachtingen aan**

```python
def test_liederen_overzicht_is_genummerd_van_1_tot_177(self):
    page = self.open_page("liederen.html")
    try:
        labels = page.locator(".ns-kaart .ns-nummer").all_inner_texts()
        self.assertEqual(labels, [f"Lied {number}" for number in range(1, 178)])
        self.assertEqual(page.locator(".ns-kaart-passage").count(), 177)
    finally:
        page.close()
```

```python
def test_lieddetail_verbergt_vindplaatsen_en_gebed_behoudt_ze(self):
    lied = self.open_page("liederen.html?item=lied-bij-de-schelfzee")
    gebed = self.open_page("gebeden.html?item=abrahams-voorbede-voor-sodom")
    try:
        self.assertNotIn("Vindplaatsen in de hele Bijbel", lied.locator("#naslag").inner_text())
        self.assertIn("Vindplaatsen in de hele Bijbel", gebed.locator("#naslag").inner_text())
    finally:
        lied.close()
        gebed.close()
```

- [ ] **Step 4: Run de gerichte tests en controleer de juiste rode fouten**

Run: `python -m pytest -q tests/test_naslag_liederen_gebeden.py tests/test_wiki_liederen_gebeden.py tests/test_wiki_reading_gutter.py`

Expected: FAIL omdat de bron nog 31 items heeft, de renderer geen `.ns-kaart-passage` maakt en lieddetails de vindplaatsensectie nog tonen.

---

### Task 2: Bouw de expliciete catalogus van 177 liederen

**Files:**
- Modify: `data/naslag-liederen.json`
- Modify: `scripts/build_naslag_teksten.py`
- Regenerate: `data/naslag-teksten/liederen/*.json`
- Test: `tests/test_naslag_liederen_gebeden.py`

**Interfaces:**
- Consumes: hoofdstukdata in `data/psalmen/*.json` en `data/klaagliederen/*.json`.
- Produces: 177 bronitems en 177 overeenkomstige bundels met aaneengesloten `nummer`-waarden.

- [ ] **Step 1: Verwijder de zeven uitgesloten items**

Verwijder de ids `lofzang-in-henoch`, `loflied-van-tobit`, `gezang-in-de-vuuroven`, `loflied-van-judith`, `dankgebed-van-jezus-sirach`, `lofzang-bij-het-avondmaal` en `paulus-en-silas`.

- [ ] **Step 2: Vervang het Psalmen-verzamelitem door 150 zelfstandige items**

Gebruik per hoofdstuk het hoogste bestaande versnummer uit `data/psalmen/<n>.json`:

```json
{
  "id": "psalm-1",
  "naam": "Psalm 1",
  "beschrijving": "Psalm 1 uit het liedboek van de Bijbel.",
  "verzen": ["psalmen 1:1", "psalmen 1:6"],
  "tekstpassages": [
    {"boek": "psalmen", "hoofdstuk": 1, "van": 1, "tot": 6, "label": "Psalm 1"}
  ]
}
```

- [ ] **Step 3: Vervang het Klaagliederen-verzamelitem door vijf zelfstandige items**

```json
{
  "id": "klaaglied-1",
  "naam": "Klaaglied 1",
  "beschrijving": "Het eerste klaaglied uit Klaagliederen.",
  "verzen": ["klaagliederen 1:1", "klaagliederen 1:22"],
  "tekstpassages": [
    {"boek": "klaagliederen", "hoofdstuk": 1, "van": 1, "tot": 22, "label": "Klaagliederen 1:1–22"}
  ]
}
```

- [ ] **Step 4: Geef alleen de lange Hoogliedbundel een compact overzichtslabel**

```json
"overzichtLabel": "Hooglied 1–8"
```

- [ ] **Step 5: Verhoog het vaste bouwcontract**

```python
COLLECTIONS = {
    "liederen": ("naslag-liederen.json", "Lied", 177),
    "gebeden": ("naslag-gebeden.json", "Gebed", 45),
}
```

- [ ] **Step 6: Bouw alle tekstbundels opnieuw**

Run: `python scripts/build_naslag_teksten.py`

Expected: `naslagteksten gebouwd: 177 liederen, 45 gebeden`; de oude zeven bundles en de oude verzamelbundels `de-psalmen.json` en `klaagliederen.json` zijn verwijderd.

- [ ] **Step 7: Run de datamodeltests**

Run: `python -m pytest -q tests/test_naslag_liederen_gebeden.py`

Expected: PASS.

---

### Task 3: Toon passageverwijzingen en verwijder de dubbele liedsectie

**Files:**
- Modify: `js/naslag.js`
- Modify: `css/naslag.css`
- Modify: `wiki-overzicht.html`
- Test: `tests/test_wiki_liederen_gebeden.py`
- Test: `tests/test_wiki_reading_gutter.py`

**Interfaces:**
- Consumes: `item.tekstpassages[].label` en optioneel `item.overzichtLabel`.
- Produces: `.ns-kaart-passage` op iedere liedtegel; lieddetails zonder `.ns-verzen`; gebeddetails ongewijzigd.

- [ ] **Step 1: Voeg een compacte tegelverwijzing toe**

```javascript
function overzichtPassage(it) {
    if (it.overzichtLabel) return it.overzichtLabel;
    var labels = [];
    for (var i = 0; i < it.tekstpassages.length; i++) {
        labels.push(it.tekstpassages[i].label);
    }
    return labels.join(' · ');
}
```

Voeg bij `d.nummerType === 'Lied'` na `.ns-kaart-naam` toe:

```javascript
'<span class="ns-kaart-passage">' + esc(overzichtPassage(it)) + '</span>'
```

- [ ] **Step 2: Geef de passage één rustige gouden regel**

```css
.ns-kaart-passage {
    margin-top: 2px;
    color: #9a7421;
    font-size: 12.5px;
    line-height: 1.45;
}
:root[data-theme="donker"] .ns-kaart-passage { color: #e2c77f; }
```

- [ ] **Step 3: Bouw vindplaatsen alleen nog voor Gebeden**

```javascript
if (d.nummerType === 'Gebed') {
    h += '<h2 class="ns-kop">Vindplaatsen in ' + esc(d.bron) + '</h2>';
    h += '<p class="ns-verzen">';
    for (var i = 0; i < it.verzen.length; i++) {
        h += versLink(d.bron, it.verzen[i]) + ' ';
    }
    h += '</p>';
} else if (!d.nummerType) {
    h += '<h2 class="ns-kop">Teksten in ' + esc(d.bron) + '</h2>';
    h += '<ol id="naslag-gekoppelde-teksten" class="gt-lijst"></ol>';
}
```

Verwijder de dode speciale `de-psalmen`-sprongnavigatie uit `toonVolledigeTekst()` en de bijbehorende `.ns-psalm-sprongen`-CSS.

- [ ] **Step 4: Werk de wiki-badge bij**

Vervang uitsluitend de badge `31 liederen` door `177 liederen`; behoud alle gelijktijdige wijzigingen in `wiki-overzicht.html`.

- [ ] **Step 5: Run de browsertests**

Run: `python -m pytest -q tests/test_wiki_liederen_gebeden.py tests/test_wiki_reading_gutter.py`

Expected: PASS.

- [ ] **Step 6: Commit de functionele wijziging**

```bash
git add data/naslag-liederen.json data/naslag-teksten/liederen scripts/build_naslag_teksten.py js/naslag.js css/naslag.css tests/test_naslag_liederen_gebeden.py tests/test_wiki_liederen_gebeden.py tests/test_wiki_reading_gutter.py
# stage wiki-overzicht.html alleen als een kleine indexpatch voor de badge
git commit -m "feat: nummer psalmen en klaagliederen afzonderlijk"
```

---

### Task 4: Volledige bouw- en regressiecontrole

**Files:**
- Verify: `desktop/build-dist.mjs`
- Verify: volledige testverzameling

**Interfaces:**
- Consumes: alle uit Task 1–3 gebouwde bestanden.
- Produces: aantoonbaar werkende website- en desktopdata zonder verouderde liedbundels.

- [ ] **Step 1: Controleer syntaxis**

Run: `node --check js/naslag.js`

Expected: exitcode 0.

- [ ] **Step 2: Controleer de desktopbouw via de bestaande integratietest**

Run: `python -m pytest -q tests/test_naslag_liederen_gebeden.py::test_desktopbouw_genereert_bundels_voordat_data_wordt_gekopieerd`

Expected: PASS.

- [ ] **Step 3: Run de volledige suite**

Run: `python -m pytest -q`

Expected: alle tests slagen.

- [ ] **Step 4: Controleer de nummergrenzen direct uit de bron**

Run een korte JSON-controle die exact `1, 12, 161, 167, 171, 176, 177` rapporteert voor de in de globale eisen genoemde ids.

- [ ] **Step 5: Controleer de echte pagina visueel**

Open `wiki.html#liederen` op desktop en mobiel, controleer Schelfzee, Psalm 1, Psalm 150, Klaaglied 1 en Mozes en het Lam, en bevestig dat de passage leesbaar is zonder vindplaatsenaantal.

- [ ] **Step 6: Push uitsluitend de liederenwijziging**

```bash
git push origin main
```
