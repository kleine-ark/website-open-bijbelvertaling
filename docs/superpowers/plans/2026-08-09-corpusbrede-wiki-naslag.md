# Corpusbrede Wiki-naslag Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Bouw vijf corpusbrede wiki-naslagpagina’s voor materialen, dieren, bomen en planten, personen en muziekinstrumenten, met gevalideerde vindplaatsen uit alle 82 boeken met verstekst.

**Architecture:** Een gecontroleerde catalogus bepaalt welke items en zoekvormen gepubliceerd mogen worden. Een deterministische Python-generator scant uitsluitend de zichtbare `text2026`-verstekst, combineert automatische treffers met expliciete correcties en schrijft de vijf bestaande/nieuwe naslag-JSON-bestanden plus een controleverslag. De bestaande browserrenderer blijft de enige detailrenderer en wordt uitgebreid voor volledige boekverwijzingen en type-aanduidingen.

**Tech Stack:** Python 3.12, JSON, vanilla JavaScript ES5-compatibel voor iPadOS 15.4, HTML/CSS, pytest en Playwright.

## Global Constraints

- Scan alle 82 boeken met hoofdstukdata uit `data/books.json`; sla de zes Ethiopische stub-boeken zonder verstekst over.
- Gebruik alleen `text2026_html`, met terugval op `text2026`; scan nooit kanttekeningen, boekinleidingen of hoofdstukinleidingen.
- Publiceer uitsluitend volledige verwijzingen in de vorm `<boek-id> <hoofdstuk>:<vers>`.
- Neem canonieke en apocriefe boeken gelijkwaardig mee.
- Neem letterlijke en symbolische vermeldingen op en markeer het gebruik als `letterlijk`, `symbolisch` of `beide`.
- Personen en Muziekinstrumenten zijn twee afzonderlijke pagina’s, gegevensbronnen, navigatielinks en overzichtstegels.
- Neem Jezus Christus op met de aanduiding: “De Zoon, God geopenbaard in het vlees.”
- Bewaar iPadOS 15.4-compatibiliteit: geen lookbehind en geen API zonder terugval.
- Genereer geen tijdelijke SVG-logo’s; gebruik voor nieuwe tegels een bestaande neutrale rasterachtergrond totdat afzonderlijk beeldontwerp is goedgekeurd.
- Wijzig geen verstekst, kanttekeningen of grondtekst in deze uitvoering.

---

### Task 1: Generatorcontract en corpusindex

**Files:**
- Create: `scripts/build_corpus_naslag.py`
- Create: `data/naslag-catalogus.json`
- Create: `tests/test_build_corpus_naslag.py`

**Interfaces:**
- Produces: `VerseRef(book_id: str, book_name: str, testament: str, chapter: int, verse: int, text: str)`.
- Produces: `load_corpus(root: Path) -> list[VerseRef]`.
- Produces: `build_all(root: Path, write: bool = True) -> dict[str, dict]`.
- Produces: `normalize_visible_text(markup: str) -> str`.

- [ ] **Step 1: Schrijf falende tests voor de corpusgrens**

```python
from scripts.build_corpus_naslag import build_all, load_corpus


def test_corpus_bevat_alleen_echte_verzen():
    corpus = load_corpus(ROOT)
    assert len(corpus) == read_json("data/stats.json")["verses_total"]
    assert all(item.text and item.chapter > 0 and item.verse > 0 for item in corpus)
    assert {item.testament for item in corpus} == {"OT", "NT", "AP"}


def test_bouwen_zonder_schrijven_is_deterministisch():
    assert build_all(ROOT, write=False) == build_all(ROOT, write=False)
```

- [ ] **Step 2: Draai de tests en bevestig dat imports ontbreken**

Run: `python -m pytest tests/test_build_corpus_naslag.py -q`

Expected: FAIL met `ModuleNotFoundError` voor `scripts.build_corpus_naslag`.

- [ ] **Step 3: Leg het catalogusschema vast**

Maak `data/naslag-catalogus.json` met deze vaste topstructuur:

```json
{
  "versie": 1,
  "categorieen": {
    "materialen": {"titel": "Materialen in de Bijbel", "items": []},
    "dieren": {"titel": "Dieren in de Bijbel", "items": []},
    "bomen-planten": {"titel": "Bomen en planten in de Bijbel", "items": []},
    "muziekinstrumenten": {"titel": "Muziekinstrumenten in de Bijbel", "items": []}
  },
  "personen": {
    "titel": "Personen in de Bijbel",
    "gebruikStamboom": true,
    "extra": []
  }
}
```

Ieder gewoon item gebruikt `id`, `naam`, `beschrijving`, `zoekvormen`,
`gebruik`, `expliciet` en `uitsluiten`. Een persoon-extra gebruikt daarnaast
`onderscheiding`; stamboompersonen worden uit `data/stamboom.json` afgeleid.

- [ ] **Step 4: Implementeer corpusladen en validatie**

`load_corpus()` leest `chaptersIncluded` in de volgorde van `books.json`, haalt
`<sup>…</sup>` en overige tags uit `text2026_html`, decodeert HTML-entiteiten en
valt terug op `text2026`. `validate_ref()` weigert onbekende boeken,
hoofdstukken en verzen. `build_all(write=False)` retourneert in deze stap lege,
geldige gegevenssets per categorie zonder bestanden te schrijven.

- [ ] **Step 5: Draai de contracttests groen**

Run: `python -m pytest tests/test_build_corpus_naslag.py -q`

Expected: PASS.

- [ ] **Step 6: Commit het generatorcontract**

```powershell
git add scripts/build_corpus_naslag.py data/naslag-catalogus.json tests/test_build_corpus_naslag.py
git commit -m "feat: leg corpusbrede naslaggenerator vast"
```

### Task 2: Zoekvormen, verwijzingen en controleverslag

**Files:**
- Modify: `scripts/build_corpus_naslag.py`
- Modify: `tests/test_build_corpus_naslag.py`
- Create: `data/naslag-controle.json`

**Interfaces:**
- Consumes: `load_corpus()` en het catalogusschema uit Task 1.
- Produces: `find_refs(corpus, item) -> list[str]`.
- Produces: `data/naslag-controle.json` met `boekenGescand`, `verzenGescand`, `itemsZonderVindplaats` en `onbekendeKandidaten`.

- [ ] **Step 1: Schrijf falende tests voor hele woorden en expliciete correcties**

```python
def test_zoekvormen_raken_hele_woorden_en_behouden_canonieke_volgorde():
    item = {"zoekvormen": ["ram", "rammen"], "expliciet": [], "uitsluiten": []}
    refs = find_refs(load_corpus(ROOT), item)
    assert "genesis 15:9" in refs
    assert len(refs) == len(set(refs))


def test_explicit_refs_worden_toegevoegd_en_uitsluitingen_verwijderd():
    item = {
        "zoekvormen": ["boom van het leven"],
        "expliciet": ["openbaring 22:2"],
        "uitsluiten": ["genesis 2:9"]
    }
    refs = find_refs(load_corpus(ROOT), item)
    assert "openbaring 22:2" in refs
    assert "genesis 2:9" not in refs
```

- [ ] **Step 2: Bevestig dat de zoektests falen**

Run: `python -m pytest tests/test_build_corpus_naslag.py -q`

Expected: FAIL omdat `find_refs` nog niet bestaat.

- [ ] **Step 3: Implementeer veilige zoekvormen**

Compileer per zoekvorm een hoofdletterongevoelig patroon met expliciete
letter-/cijferranden in plaats van lookbehind. Sorteer zoekvormen langste eerst,
voeg expliciete verwijzingen toe, verwijder uitsluitingen en sorteer via de
corpusindex. Sla bij elk automatisch resultaat de geraakte zoekvorm intern op,
zodat tests kunnen bewijzen waarom de verwijzing bestaat.

- [ ] **Step 4: Bouw het controleverslag**

Schrijf alleen deterministische velden. `onbekendeKandidaten` bevat woorden die
door de categorie-specifieke kandidaatpatronen worden gevonden maar niet in de
catalogus voorkomen. Publiceer die kandidaten niet. Een ongeldige expliciete
verwijzing of dubbel item-id stopt de build met `ValueError`.

- [ ] **Step 5: Draai de zoektests groen**

Run: `python -m pytest tests/test_build_corpus_naslag.py -q`

Expected: PASS.

- [ ] **Step 6: Commit de zoekmotor**

```powershell
git add scripts/build_corpus_naslag.py tests/test_build_corpus_naslag.py data/naslag-controle.json
git commit -m "feat: vind naslagverwijzingen in het hele corpus"
```

### Task 3: Materialen, dieren en bomen/planten migreren

**Files:**
- Modify: `data/naslag-catalogus.json`
- Regenerate: `data/naslag-materialen.json`
- Regenerate: `data/naslag-dieren.json`
- Regenerate: `data/naslag-bomen-planten.json`
- Modify: `tests/test_build_corpus_naslag.py`
- Modify: `tests/test_wiki_gekoppelde_teksten.py`

**Interfaces:**
- Consumes: `find_refs()` en `build_all()` uit Tasks 1–2.
- Produces: drie gegevenssets waarvan elk item volledige verwijzingen gebruikt.

- [ ] **Step 1: Schrijf falende corpusdekkingstests**

```python
@pytest.mark.parametrize("naam,minimum", [
    ("naslag-materialen.json", 35),
    ("naslag-dieren.json", 55),
    ("naslag-bomen-planten.json", 45),
])
def test_natuurlijke_naslag_is_corpusbreed(naam, minimum):
    data = read_json("data/" + naam)
    assert len(data["items"]) >= minimum
    refs = [ref for item in data["items"] for ref in item["verzen"]]
    assert any(ref.startswith("genesis ") for ref in refs)
    assert any(ref.startswith("mattheus ") or ref.startswith("markus ") for ref in refs)
    assert any(ref.startswith("wijsheid ") or ref.startswith("jezus-sirach ") for ref in refs)
    assert "Voorlopig alleen Genesis" not in data["intro"]
```

Voeg een browsertest toe die `materialen.html?item=goud` opent en controleert
dat zowel `genesis 2:11` als `openbaring 21:18` als `.gt-vers` bestaat.

- [ ] **Step 2: Bevestig dat de bestaande Genesis-data de tests niet haalt**

Run: `python -m pytest tests/test_build_corpus_naslag.py tests/test_wiki_gekoppelde_teksten.py -q`

Expected: FAIL op itemaantallen, volledige verwijzingen en corpusspreiding.

- [ ] **Step 3: Vul de gecontroleerde catalogus**

Neem minimaal de volgende onderscheiden groepen op:

- materialen: metalen, edelstenen, bouwstoffen, houtsoorten, textiel, huid/leer,
  schrijfmaterialen, kleurstoffen, geurstoffen en brandstoffen;
- dieren: huisdieren, wilde zoogdieren, vogels, waterdieren, reptielen,
  insecten en symbolische dieren;
- bomen/planten: bomen, heesters, akkergewassen, groenten, kruiden, bloemen,
  doornen, waterplanten en symbolische bomen.

Behoud alle bestaande Genesis-items en beschrijvingen. Voeg verbogen,
enkelvoudige en meervoudige zoekvormen expliciet toe. Maak geen verzamelitem als
een benoemde soort al een eigen item heeft, behalve bij echte bijbelse
verzamelwoorden zoals `vee`, `gevogelte` en `gedierte`.

- [ ] **Step 4: Genereer en valideer de drie bestanden**

Run: `python scripts/build_corpus_naslag.py`

Expected: ieder bestand bevat alleen volledige verwijzingen; de console meldt
82 boeken en 37.235 verzen gescand.

- [ ] **Step 5: Draai data- en browsertests groen**

Run: `python -m pytest tests/test_build_corpus_naslag.py tests/test_wiki_gekoppelde_teksten.py -q`

Expected: PASS.

- [ ] **Step 6: Commit de drie corpusbrede categorieën**

```powershell
git add data/naslag-catalogus.json data/naslag-materialen.json data/naslag-dieren.json data/naslag-bomen-planten.json data/naslag-controle.json tests/test_build_corpus_naslag.py tests/test_wiki_gekoppelde_teksten.py
git commit -m "feat: maak natuur- en materiaalnaslag corpusbreed"
```

### Task 4: Personen uit stamboom en expliciete aanvullingen

**Files:**
- Modify: `scripts/build_corpus_naslag.py`
- Modify: `data/naslag-catalogus.json`
- Create: `data/naslag-personen.json`
- Modify: `tests/test_build_corpus_naslag.py`

**Interfaces:**
- Consumes: `data/stamboom.json` en `find_refs()`.
- Produces: `build_people(root, corpus, catalog) -> dict`.

- [ ] **Step 1: Schrijf falende tests voor identiteit en reikwijdte**

```python
def test_personen_behouden_gelijknamigen_en_alle_testamenten():
    data = build_all(ROOT, write=False)["personen"]
    assert len(data["items"]) >= 385
    assert any(item["naam"] == "Jezus Christus" and
               "God geopenbaard in het vlees" in item["beschrijving"]
               for item in data["items"])
    refs = [ref for item in data["items"] for ref in item["verzen"]]
    assert any(ref.startswith("genesis ") for ref in refs)
    assert any(ref.startswith("handelingen ") for ref in refs)
    assert any(ref.startswith("tobit ") or ref.startswith("judith ") for ref in refs)


def test_gelijknamige_stamboompersonen_worden_niet_automatisch_samengevoegd():
    data = build_all(ROOT, write=False)["personen"]
    names = [item for item in data["items"] if item["naam"] == "Azaria"]
    assert len(names) > 1
    assert len({item["id"] for item in names}) == len(names)
```

- [ ] **Step 2: Bevestig dat Personen nog ontbreekt**

Run: `python -m pytest tests/test_build_corpus_naslag.py -q`

Expected: FAIL omdat `build_people` en de Personen-uitvoer ontbreken.

- [ ] **Step 3: Bouw stamboompersonen zonder identiteit te verliezen**

Gebruik de 385 stabiele ids uit `stamboom.json`. Voor unieke zichtbare namen
mag de generator corpusbreed zoeken. Als dezelfde zichtbare naam bij meerdere
ids hoort, gebruik dan uitsluitend de reeds aan die persoon gekoppelde
stamboomverzen plus expliciete catalogusverwijzingen; deel nooit één automatische
treffer uit aan alle gelijknamigen. Neem `opmerking` als beschrijving en maak
voor personen zonder opmerking een feitelijke tekst met hun eerste vindplaats.

- [ ] **Step 4: Voeg personen buiten de stamboom gecontroleerd toe**

Voeg afzonderlijke items toe voor ten minste Jezus Christus, Johannes de Doper,
Petrus, Paulus, Barnabas, Silas, Stefanus, Timotheüs, Titus, Lukas, Markus,
Martha, Lazarus, Maria Magdalena, Pontius Pilatus, de Samaritaanse vrouw, de
kamerling uit Ethiopië, Tobit, Tobias, Sara uit Tobit, Judith en Judas Makkabeüs.
Gebruik expliciete verwijzingen waar een losse naam meerdere personen kan
aanduiden.

- [ ] **Step 5: Genereer en draai de identiteitstests groen**

Run: `python scripts/build_corpus_naslag.py`

Run: `python -m pytest tests/test_build_corpus_naslag.py -q`

Expected: PASS; `data/naslag-personen.json` bevat minimaal 385 items en
verwijzingen uit OT, NT en AP.

- [ ] **Step 6: Commit de Personen-data**

```powershell
git add scripts/build_corpus_naslag.py data/naslag-catalogus.json data/naslag-personen.json data/naslag-controle.json tests/test_build_corpus_naslag.py
git commit -m "feat: voeg corpusbrede personennaslag toe"
```

### Task 5: Muziekinstrumenten als zelfstandige categorie

**Files:**
- Modify: `data/naslag-catalogus.json`
- Create: `data/naslag-muziekinstrumenten.json`
- Modify: `tests/test_build_corpus_naslag.py`

**Interfaces:**
- Consumes: generieke categoriebouw uit Tasks 1–2.
- Produces: minimaal twaalf onderscheiden muziekinstrument-items.

- [ ] **Step 1: Schrijf falende instrumenttests**

```python
def test_muziekinstrumenten_zijn_een_eigen_corpusbrede_categorie():
    data = build_all(ROOT, write=False)["muziekinstrumenten"]
    names = {item["naam"] for item in data["items"]}
    assert {"Harp", "Fluit", "Trompet", "Cimbalen"} <= names
    refs = [ref for item in data["items"] for ref in item["verzen"]]
    assert any(ref.startswith("genesis ") for ref in refs)
    assert any(ref.startswith("1korinthiers ") or ref.startswith("openbaring ") for ref in refs)
    assert any(ref.startswith("1makkabeeen ") or ref.startswith("jezus-sirach ") for ref in refs)
```

- [ ] **Step 2: Bevestig de rode test**

Run: `python -m pytest tests/test_build_corpus_naslag.py -q`

Expected: FAIL omdat de instrumentcatalogus nog leeg is.

- [ ] **Step 3: Vul instrumenten en vertaalvarianten**

Neem ten minste harp, citer, luit, vedel, fluit, schalmei, trompet, bazuin,
ramshoorn, trommel/tamboerijn, cimbalen/bekkens en bellen op. Houd onzekere
identificaties als afzonderlijke vertaalnamen met een toelichting; voeg ze niet
zonder bewijs samen.

- [ ] **Step 4: Genereer en test**

Run: `python scripts/build_corpus_naslag.py`

Run: `python -m pytest tests/test_build_corpus_naslag.py -q`

Expected: PASS.

- [ ] **Step 5: Commit de instrumentdata**

```powershell
git add data/naslag-catalogus.json data/naslag-muziekinstrumenten.json data/naslag-controle.json tests/test_build_corpus_naslag.py
git commit -m "feat: voeg muziekinstrumenten als naslag toe"
```

### Task 6: Renderer voor volledige verwijzingen en typebadges

**Files:**
- Modify: `js/naslag.js`
- Modify: `css/naslag.css`
- Modify: `tests/test_wiki_gekoppelde_teksten.py`

**Interfaces:**
- Consumes: volledige verwijzingen en `boeknamen` uit de vijf gegenereerde JSON-bestanden.
- Produces: `naslagRef(data, ref) -> str` en typebadge `.ns-type`.

- [ ] **Step 1: Schrijf falende browsertests**

Controleer dat een volledig ref niet nogmaals met `bronId` wordt voorgevoegd,
dat de kop “Teksten in de hele Bijbel” luidt en dat een item met `gebruik` een
zichtbare `.ns-type` krijgt. Controleer tevens dat de kaarttelling gelijk is aan
`item.verzen.length`.

- [ ] **Step 2: Draai de browsertest rood**

Run: `python -m pytest tests/test_wiki_gekoppelde_teksten.py -q`

Expected: FAIL op dubbele boek-id en ontbrekende typebadge.

- [ ] **Step 3: Pas de renderer minimaal aan**

Als een ref al een spatie bevat, geef hem ongewijzigd aan
`GekoppeldeTeksten.render`. Bouw `boeknamen` uit `d.boeknamen`. Gebruik de oude
`bronId + korte ref`-route alleen voor historische data. Render `it.gebruik` als
tekstbadge na de titel en zet de detailkop op “Teksten in de hele Bijbel” zodra
`d.corpusbreed` waar is.

- [ ] **Step 4: Draai browsertests groen**

Run: `python -m pytest tests/test_wiki_gekoppelde_teksten.py -q`

Expected: PASS.

- [ ] **Step 5: Commit de renderer**

```powershell
git add js/naslag.js css/naslag.css tests/test_wiki_gekoppelde_teksten.py
git commit -m "feat: render corpusbrede naslagverwijzingen"
```

### Task 7: Twee nieuwe pagina’s en wiki-integratie

**Files:**
- Create: `personen.html`
- Create: `muziekinstrumenten.html`
- Modify: `wiki.html`
- Modify: `wiki-overzicht.html`
- Modify: `sw.js`
- Create: `tests/test_wiki_corpus_naslag.py`

**Interfaces:**
- Consumes: `data/naslag-personen.json`, `data/naslag-muziekinstrumenten.json` en `js/naslag.js`.
- Produces: hash-routes `wiki.html#personen` en `wiki.html#muziekinstrumenten`.

- [ ] **Step 1: Schrijf falende pagina- en navigatietests**

```python
def test_personen_en_instrumenten_zijn_aparte_wikipaginas():
    wiki = (ROOT / "wiki.html").read_text(encoding="utf-8")
    overview = (ROOT / "wiki-overzicht.html").read_text(encoding="utf-8")
    assert 'data-page="personen.html"' in wiki
    assert 'data-page="muziekinstrumenten.html"' in wiki
    assert 'href="wiki.html#personen"' in overview
    assert 'href="wiki.html#muziekinstrumenten"' in overview
```

Voeg Playwright-controles toe die beide routes openen, een item aanklikken en
bevestigen dat een `.gt-vers` met tekst verschijnt. Herhaal op 390 pixels en
controleer `scrollWidth <= innerWidth`.

- [ ] **Step 2: Bevestig dat pagina’s en routes ontbreken**

Run: `python -m pytest tests/test_wiki_corpus_naslag.py -q`

Expected: FAIL op ontbrekende bestanden en links.

- [ ] **Step 3: Maak beide pagina’s volgens het bestaande sjabloon**

Kopieer de structuur van `materialen.html`, wijzig titel, metadata en
`data-naslag`. Laad `embed.js`, `js/gekoppelde-teksten.js` en `js/naslag.js` in
dezelfde volgorde. Voeg beide links als zelfstandige regels toe in het
wiki-zijmenu.

- [ ] **Step 4: Voeg overzichtstegels zonder nep-logo toe**

Plaats twee kaarten in “Wat de Bijbel noemt”. Gebruik als tijdelijke
rasterachtergrond `images/wiki/materialen.webp` voor Personen en
`images/wiki/liederen.webp` voor Muziekinstrumenten, met lege `alt` omdat titel
en beschrijving de koppeling benoemen. Voeg geen SVG toe. Zet de badges op
“hele Bijbel”.

- [ ] **Step 5: Verhoog de serviceworker naar v0.31.1**

Wijzig uitsluitend `const VERSION` in `sw.js` van `v0.31.0` naar `v0.31.1`,
zodat de nieuwe HTML-, JS- en JSON-routes niet achter een oude shellcache
blijven hangen.

- [ ] **Step 6: Draai navigatie- en browsertests groen**

Run: `python -m pytest tests/test_wiki_corpus_naslag.py tests/test_wiki_gekoppelde_teksten.py tests/test_wiki_reading_gutter.py -q`

Expected: PASS.

- [ ] **Step 7: Commit de pagina-integratie**

```powershell
git add personen.html muziekinstrumenten.html wiki.html wiki-overzicht.html sw.js tests/test_wiki_corpus_naslag.py
git commit -m "feat: voeg personen en instrumenten aan wiki toe"
```

### Task 8: Releasegegevens, build en volledige verificatie

**Files:**
- Modify: `data/changelog.json`
- Modify: `data/stats.json`
- Modify: `data/review-history.json` only if `build_stats.py` changes today’s value
- Regenerate: `data/naslag-controle.json`
- Modify: `tests/test_release_metadata.py`

**Interfaces:**
- Consumes: alle eerdere taken.
- Produces: consistente websiteversie `v0.31.1` en reproduceerbare build.

- [ ] **Step 1: Schrijf de releaseverwachting eerst in de test**

Pas `tests/test_release_metadata.py` aan zodat changelog, stats en serviceworker
`v0.31.1` noemen en de releasedatum `2026-08-09` blijft. Laat de beschrijvingen
“Materialen”, “Dieren”, “Bomen & planten”, “Personen” en
“Muziekinstrumenten” bevatten.

- [ ] **Step 2: Bevestig dat de releasecontrole rood is**

Run: `python -m pytest tests/test_release_metadata.py -q`

Expected: FAIL zolang changelog en stats nog `v0.31.0` noemen.

- [ ] **Step 3: Voeg changelog v0.31.1 toe en bouw statistieken**

Beschrijf de vijf corpusbrede naslagcategorieën, de 82 gescande boeken, de twee
nieuwe pagina’s en de reproduceerbare generator. Draai:

```powershell
python scripts/build_stats.py v0.31.1 "9 augustus 2026"
python scripts/build_corpus_naslag.py
python scripts/build_naslag_teksten.py
python scripts/build_downloads.py
```

- [ ] **Step 4: Controleer determinisme**

Run de corpusgenerator opnieuw en controleer:

```powershell
python scripts/build_corpus_naslag.py
git diff --exit-code -- data/naslag-materialen.json data/naslag-dieren.json data/naslag-bomen-planten.json data/naslag-personen.json data/naslag-muziekinstrumenten.json data/naslag-controle.json
```

Expected: geen nieuwe diff na de tweede run.

- [ ] **Step 5: Draai JavaScript-syntax en volledige testsuite**

```powershell
node --check js/naslag.js
python -m pytest -q
git diff --check
```

Expected: exitcode 0, alle tests groen en geen whitespacefouten.

- [ ] **Step 6: Commit de release**

```powershell
git add data/changelog.json data/stats.json data/review-history.json data/naslag-*.json tests/test_release_metadata.py
git commit -m "chore: publiceer corpusbrede naslag in v0.31.1"
```
