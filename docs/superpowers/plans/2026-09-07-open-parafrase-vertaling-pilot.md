# Open Parafrase Vertaling Pilot Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Bouw een selecteerbare proefeditie van de Open Parafrase Vertaling voor Genesis 1–5 en Johannes 1–5, met brontraceerbaarheid, begrippen- en citatiemetadata en boekachtige leesweergave.

**Architecture:** De OPV blijft buiten de bestaande OV-hoofdstukbestanden en buiten de gegenereerde buitenlandse vertalingen. Een zelfstandige editie-registry wijst naar genormaliseerde hoofdstukken onder `data/edities/opv`; de bestaande editie-, parallel- en wiki-infrastructuur leert gegevenswortels uit metadata laden. Een pure Python-validator bewaakt de corpuscontracten en Playwright-regressies bewaken gebruikersgedrag.

**Tech Stack:** Statische HTML, JavaScript zonder bundler, JSON, Python 3.12 `unittest`, Playwright.

**Spec:** `docs/superpowers/specs/2026-09-07-open-parafrase-vertaling-pilot-design.md`

## Global Constraints

- Werk uitsluitend in de geïsoleerde branch `codex/opv-pilot`.
- Gebruik editiecode `nl-opv` en zichtbare naam `Open Parafrase Vertaling (proef)`.
- SV1888 is de directe basistekst; SV1637, OV en grondtekst zijn controlebronnen.
- Formuleer alles zelfstandig; neem geen tekst over uit moderne beschermde Bijbeledities.
- Leesbaarheid gaat vóór letterlijke zinsbouw, maar er mag geen nieuwe inhoud worden toegevoegd.
- Gebruik `HEERE` voor de Godsnaam in Genesis en eerbiedshoofdletters voor God, Jezus en de Heilige Geest.
- Houd `data/vertalingen/manifest.json` gegenereerd en ongewijzigd; registreer OPV onder `data/edities`.
- Toon bij ontbrekende OPV-hoofdstukken een expliciete melding; val nooit stil terug op OV.
- Plak bestaande Strong-koppelingen niet automatisch op de parafrase.
- De complete pilot telt exact 138 Genesisverzen en 214 Johannesverzen.
- Schrijf productielogica test-first en leg ieder rood-groen-resultaat in het taakrapport vast.

---

### Task 1: OPV-contract, manifests en validator

**Files:**
- Create: `data/edities/manifest.json`
- Create: `data/edities/opv/manifest.json`
- Create: `data/edities/opv/concepten.json`
- Create: `scripts/validate_opv.py`
- Create: `tests/test_validate_opv.py`

**Interfaces:**
- Produces: `validate_corpus(repo_root: pathlib.Path) -> list[str]`
- Produces: interne validators `validate_manifest()`, `validate_chapter()`, `validate_verse()`, `validate_annotations()` en `validate_review()`.
- Produces: CLI `python scripts/validate_opv.py [--root PATH]`, exitcode 0 bij geldige data en 1 met één fout per regel bij ongeldige data.
- Produces: registryvelden `code`, `naam`, `taal`, `richting`, `dataRoot`, `boeken`, `hoofdstukken`, `status`.

- [ ] **Step 1: Write failing validator tests**

Maak tijdelijke mini-corpora en test letterlijk dat `validate_corpus()` fouten meldt voor een dubbel versnummer, leeg `tekst`, HTML in `tekst`, ontbrekende bron, onveilig bronpad, overlappende of onvolledige blokken, dubbele segment-id, onbekend begrip, onbekende segmentverwijzing en ontbrekend `spreker.id` of `spreker.type`. Voeg een geldige fixture toe met:

```python
chapter = {
    "schema": 1,
    "editie": "nl-opv",
    "boek": "genesis",
    "hoofdstuk": 1,
    "kop": "God maakt de hemel en de aarde",
    "blokken": [{"id": "gen-1-b1", "kop": "Het begin", "vanaf": 1, "tot": 1}],
    "verzen": [{
        "nummer": 1,
        "tekst": "God maakte in het begin de hemel en de aarde.",
        "bron": {"bestand": "data/genesis/1.json", "vers": 1, "tekstveld": "textSV1888"},
        "segmenten": [{"id": "GEN.1.1.s1", "tekst": "God maakte in het begin de hemel en de aarde."}],
        "begrippen": [],
        "citaten": [],
        "review": {
            "status": "concept",
            "inhoudSha256": "3de1d2d8d4735d49b002aca96ba7fc4b0227acabe72cf4d03f9330f10c99f45c",
            "bronSha256": "ad7db6a21814ca5d62e90b9d9f04b435d51c91f41fbea1dcd872f573e4d4d5ee",
            "controles": []
        }
    }]
}
```

Gebruik voor gekoppelde metadata exact deze vormen:

```json
{"conceptId":"schepping","segmenten":["GEN.1.1.s1"]}
{"id":"GEN.1.3.q1","semanticId":"spraak.god.licht","startSegment":"GEN.1.3.s2","endSegment":"GEN.1.3.s2","spreker":{"id":"god","type":"god","naam":"God"},"aangesprokene":[]}
```

`concepten.json` heeft vorm `{"schema":1,"concepten":[{"id":"schepping","label":"Schepping","uitleg":"God brengt de werkelijkheid tot bestaan."}]}`. Bereken `inhoudSha256` over de UTF-8-bytes van `tekst` en `bronSha256` over de UTF-8-bytes van het gekozen bronveld.

- [ ] **Step 2: Verify RED**

Run: `python -m unittest tests.test_validate_opv -v`  
Expected: FAIL omdat `scripts.validate_opv` nog niet bestaat.

- [ ] **Step 3: Implement the validator and manifests**

Sta alleen `concept`, `bron_gecontroleerd`, `taal_gecontroleerd` en `definitief` toe. Geef deterministisch gesorteerde fouten als `CODE bestand JSON-pad`. Controleer NFC-Unicode, afwezigheid van HTML en U+FFFD, de exacte verslijst, veilige bronpaden, bron- en inhoudshashes, volledige blokpartitie en corpusbreed unieke segment-id’s. Laat segmentteksten exact samen de leestekst vormen. Begrippen moeten in `concepten.json` bestaan. Citaten krijgen een unieke occurrence-id, canonieke semantic-id, bestaande begin- en eindsegmenten en een spreker met id plus type uit `god|human|angel|spirit|animal|group|narrator|unknown`. Weiger gekruiste citaatbereiken en ieder Strong-veld. `definitief` vereist actuele bron-, taal- en leesbaarheidsreviews op dezelfde inhoudshash. Registreer `nl-opv` met `dataRoot: data/edities/opv/chapters` en alleen hoofdstukken 1–5 van Genesis en Johannes.

- [ ] **Step 4: Verify GREEN**

Run: `python -m unittest tests.test_validate_opv -v`  
Expected: alle validatortests PASS.

- [ ] **Step 5: Commit**

```bash
git add data/edities/manifest.json data/edities/opv/manifest.json data/edities/opv/concepten.json scripts/validate_opv.py tests/test_validate_opv.py
git commit -m "feat: definieer OPV-corpuscontract"
```

### Task 2: Kalibratiehoofdstukken Genesis 1 en Johannes 1

**Files:**
- Create: `data/edities/opv/chapters/genesis/1.json`
- Create: `data/edities/opv/chapters/johannes/1.json`
- Modify: `tests/test_validate_opv.py`
- Create: `docs/opv/besluitregister.md`

**Interfaces:**
- Consumes: het hoofdstukcontract en `validate_corpus()` uit Task 1.
- Produces: 31 Genesisverzen en 52 Johannesverzen, met unieke segment-id’s, volledige bronverwijzingen, betekenisblokken en status `concept`.

- [ ] **Step 1: Add failing real-corpus tests**

Test dat Genesis 1 exact `range(1, 32)` en Johannes 1 exact `range(1, 53)` bevat, dat iedere bron naar hetzelfde boek/hoofdstuk/vers wijst en dat de twee hoofdstukken samen door `validate_corpus()` zonder fouten komen wanneer het manifest tijdelijk alleen deze hoofdstukken declareert.

- [ ] **Step 2: Verify RED**

Run: `python -m unittest tests.test_validate_opv -v`  
Expected: FAIL omdat de twee hoofdstukbestanden ontbreken.

- [ ] **Step 3: Author both chapters**

Werk per betekenisblok vanuit `textSV1888`, controleer aan `text1637` en `text2026`, en raadpleeg `grondtekst` voor de risicopassages uit de spec. Gebruik deze zichtbare hoofdstukkoppen:

- Genesis 1: `God maakt de hemel en de aarde`
- Johannes 1: `Het Woord wordt mens`

Leg minimaal beslissingen vast voor Genesis 1:2, 1:6–8, 1:14, 1:20 en 1:26–28 en Johannes 1:1–5, 1:9, 1:13–18, 1:29 en 1:52. Leg tevens vast waarom Johannes 1 in deze repository 52 verzen telt. Verdeel ieder hoofdstuk in de betekenisblokken uit het ontwerp. Splits tekstsegmenten op spreekwissels en gekoppelde begrippen; laat de segmentteksten exact de versregel vormen.

- [ ] **Step 4: Validate content and prose**

Run: `python scripts/validate_opv.py`  
Expected tijdens deze tussenslice: alleen meldingen dat de nog gedeclareerde hoofdstukken 2–5 ontbreken; geen fout over Genesis 1 of Johannes 1.

Lees beide hoofdstukken zonder versnummers hardop en noteer in het taakrapport iedere zin die langer is dan 25 woorden, plus de bewuste reden om die te behouden of de herziening.

- [ ] **Step 5: Commit**

```bash
git add data/edities/opv/chapters/genesis/1.json data/edities/opv/chapters/johannes/1.json tests/test_validate_opv.py docs/opv/besluitregister.md
git commit -m "content: voeg eerste OPV-hoofdstukken toe"
```

### Task 3: OPV kiezen, vergelijken en in wiki-citaten gebruiken

**Files:**
- Create: `tests/test_opv_reader.py`
- Modify: `js/teksteditie.js`
- Modify: `index.html`
- Modify: `embed.js`
- Modify: `js/app.js`

**Interfaces:**
- Consumes: `data/edities/manifest.json` en `dataRoot` uit Task 1.
- Produces: `TekstEditie.loadChapterForEdition('nl-opv', boek, hoofdstuk)`.
- Preserves: `verse.status`, `verse.bron`, `verse.begrippen`, `verse.citaten` en hoofdstukblokken in de genormaliseerde readerdata.

- [ ] **Step 1: Write failing browser tests**

Test echt gebruikersgedrag:

```python
page.goto(f"{base_url}/index.html?editie=nl-opv#genesis/1")
verse = page.locator('.verse-row[data-verse="1"] .col-2026')
verse.wait_for()
self.assertIn("hemel", verse.inner_text())
self.assertEqual(verse.get_attribute("lang"), "nl")
```

Voeg afzonderlijke tests toe voor wisselen zonder reload, OPV parallel naast OV, een expliciete onbeschikbaarheidsmelding bij Genesis 6, wiki-citaten die `nl-opv` volgen, geen OV-audio en geen geërfde OV-status.

- [ ] **Step 2: Verify RED**

Run: `python -m unittest tests.test_opv_reader -v`  
Expected: FAIL omdat `nl-opv` niet in de editielaag of instellingen staat.

- [ ] **Step 3: Implement registry-based loading**

Laat `js/teksteditie.js` het gegenereerde buitenlandse manifest en `data/edities/manifest.json` samenvoegen. Gebruik `meta.dataRoot` voor het hoofdstukpad, respecteer `meta.hoofdstukken[boek]` en behoud OPV-metadata in `chapterToReaderData()`. Voeg de primaire optie en parallelle checkbox toe aan `index.html`.

Laat `embed.js` dezelfde registry en `dataRoot` gebruiken en toon de werkelijke editienaam. Beperk in `js/app.js` OV-verificatiestatus en OV-audio expliciet tot `nl-ov`.

- [ ] **Step 4: Verify GREEN and regressions**

Run: `python -m unittest tests.test_opv_reader tests.test_teksteditie tests.test_parallel_editions tests.test_wiki_citation_template -v`  
Expected: alle tests PASS.

- [ ] **Step 5: Commit**

```bash
git add tests/test_opv_reader.py js/teksteditie.js index.html embed.js js/app.js
git commit -m "feat: integreer OPV in lezer en wiki"
```

### Task 4: Genesis 2–5 redigeren

**Files:**
- Create: `data/edities/opv/chapters/genesis/2.json`
- Create: `data/edities/opv/chapters/genesis/3.json`
- Create: `data/edities/opv/chapters/genesis/4.json`
- Create: `data/edities/opv/chapters/genesis/5.json`
- Modify: `docs/opv/besluitregister.md`
- Modify: `tests/test_validate_opv.py`

**Interfaces:**
- Consumes: OPV-schema en redactionele regels uit Tasks 1–2.
- Produces: Genesis 1–5 als volledig valide corpus van 138 verzen.

- [ ] **Step 1: Add failing Genesis completeness tests**

Vergelijk per hoofdstuk de letterlijke lijst `nummer` met de bestaande brondata. Assert ook totaal 138, alle bronverwijzingen boek `genesis`, en minimaal één betekenisblok per hoofdstuk.

- [ ] **Step 2: Verify RED**

Run: `python -m unittest tests.test_validate_opv -v`  
Expected: FAIL met ontbrekende Genesis-hoofdstukken 2–5.

- [ ] **Step 3: Author Genesis 2–5**

Gebruik de hoofdstukkoppen en blokgrenzen uit het redactionele ontwerp. Behoud alle namen en leeftijden in Genesis 5. Leg besluiten vast voor Genesis 2:7, 2:18, 2:21–24, 3:5, 3:8, 3:15–16, 4:1, 4:7, 4:13, 4:15 en 4:23–24. Voeg geen oorzaak toe voor Gods verschillende reactie op de offers in Genesis 4.

- [ ] **Step 4: Verify GREEN**

Run: `python -m unittest tests.test_validate_opv -v`  
Expected: Genesiscontroles PASS; alleen nog ontbrekende Johannes-hoofdstukken mogen de volledige CLI blokkeren.

- [ ] **Step 5: Commit**

```bash
git add data/edities/opv/chapters/genesis docs/opv/besluitregister.md tests/test_validate_opv.py
git commit -m "content: voltooi Genesis 1 tot en met 5 in OPV"
```

### Task 5: Johannes 2–5 redigeren

**Files:**
- Create: `data/edities/opv/chapters/johannes/2.json`
- Create: `data/edities/opv/chapters/johannes/3.json`
- Create: `data/edities/opv/chapters/johannes/4.json`
- Create: `data/edities/opv/chapters/johannes/5.json`
- Modify: `docs/opv/besluitregister.md`
- Modify: `tests/test_validate_opv.py`

**Interfaces:**
- Consumes: OPV-schema en redactionele regels uit Tasks 1–2.
- Produces: Johannes 1–5 als volledig valide corpus van 214 verzen en daarmee de complete pilot van 352 verzen.

- [ ] **Step 1: Add failing Johannes completeness tests**

Vergelijk per hoofdstuk de letterlijke versnummerlijst met de brondata. Assert totaal 214, pilot totaal 352, alle bronverwijzingen boek `johannes`, unieke segment-id’s en geldige citatieverwijzingen.

- [ ] **Step 2: Verify RED**

Run: `python -m unittest tests.test_validate_opv -v`  
Expected: FAIL met ontbrekende Johannes-hoofdstukken 2–5.

- [ ] **Step 3: Author Johannes 2–5**

Gebruik de vastgelegde hoofdstukkoppen en betekenisblokken. Leg besluiten vast voor Johannes 2:4, 2:6, 2:19–25, 3:3–8, 3:13, 3:16–21, 3:31–36, 4:10–24, 4:44, 5:3–4, 5:17–30, 5:31, 5:39 en 5:45–47. Houd in Johannes 5:3–4 de SV/TR-lezing in de hoofdtekst en voeg de handschriftkwestie als gekoppelde noot toe.

- [ ] **Step 4: Verify GREEN**

Run: `python scripts/validate_opv.py`  
Expected: `OPV geldig: 10 hoofdstukken, 352 verzen.` en exitcode 0.

Run: `python -m unittest tests.test_validate_opv -v`  
Expected: alle tests PASS.

- [ ] **Step 5: Commit**

```bash
git add data/edities/opv/chapters/johannes docs/opv/besluitregister.md tests/test_validate_opv.py
git commit -m "content: voltooi Johannes 1 tot en met 5 in OPV"
```

### Task 6: Boekachtige OPV-weergave en tweede informatielaag

**Files:**
- Modify: `tests/test_opv_reader.py`
- Modify: `js/app.js`
- Modify: `css/style.css`

**Interfaces:**
- Consumes: hoofdstuk-`blokken`, segmenten, begrippen en citaten uit het OPV-corpus.
- Produces: `.opv-reading-flow`, `.opv-passage`, subtiele `.opv-verse-anchor` en aanklikbare `[data-opv-concept]`.
- Preserves: de bestaande versrijweergave voor alle andere edities.

- [ ] **Step 1: Write failing rendering tests**

Test dat een OPV-hoofdstuk één `.opv-reading-flow` heeft, dat ieder betekenisblok precies één passagekop krijgt, dat alle 31 Genesis 1-versankers bestaan en dat een begrippenknop zijn gekoppelde uitleg opent. Test tevens dat `nl-ov` geen `.opv-reading-flow` krijgt.

- [ ] **Step 2: Verify RED**

Run: `python -m unittest tests.test_opv_reader -v`  
Expected: FAIL omdat OPV nog via gewone versrijen wordt gerenderd.

- [ ] **Step 3: Implement edition-specific flow**

Voeg in `App.renderChapter()` één vroege vertakking toe voor editiecode `nl-opv`. Bouw passages uit de blokken, plaats iedere versinhoud in leesvolgorde, behoud een deelbaar versanker en gebruik uitsluitend DOM-`textContent` voor leestekst. Laat citatieopmaak de globale instelling volgen en open begrippeninformatie als tweede laag; wijzig het pad voor andere edities niet.

Stijl de OPV als rustige boekpagina met dezelfde CSS-variabelen als de hoofdlezer. Versankers zijn zichtbaar maar ondergeschikt en de weergave blijft bruikbaar op 360 px breedte.

- [ ] **Step 4: Verify GREEN**

Run: `python -m unittest tests.test_opv_reader tests.test_parallel_editions -v`  
Expected: alle tests PASS.

- [ ] **Step 5: Commit**

```bash
git add tests/test_opv_reader.py js/app.js css/style.css
git commit -m "feat: geef OPV een boekachtige leesweergave"
```

### Task 7: Integrale pilotcontrole

**Files:**
- Create: `docs/opv/pilot-review.md`
- Modify when findings require it: `data/edities/opv/chapters/**/*.json`
- Modify when findings require it: `docs/opv/besluitregister.md`

**Interfaces:**
- Consumes: alle eerdere taken.
- Produces: een controleverslag met aantallen, open redactionele punten, risicobesluiten en exacte testuitvoer.

- [ ] **Step 1: Run corpus validation**

Run: `python scripts/validate_opv.py`  
Expected: `OPV geldig: 10 hoofdstukken, 352 verzen.`

- [ ] **Step 2: Run the relevant regression suite**

Run: `python -m unittest tests.test_validate_opv tests.test_opv_reader tests.test_teksteditie tests.test_parallel_editions tests.test_wiki_citation_template tests.test_global_options_host -v`  
Expected: alle tests PASS zonder warnings uit de websiteconsole.

- [ ] **Step 3: Perform independent source and language reviews**

Laat twee verschillende reviewers alle tien hoofdstukken beoordelen. De bronreview vergelijkt ieder vers met SV1888 en markeert weglating, toevoeging, veranderde ontkenning, veranderd getal of onjuiste spreker. De taalreview leest ieder betekenisblok zonder bronkolom en markeert onbekende woorden, dubbelzinnige voornaamwoorden, zinnen boven 25 woorden en onnatuurlijke overgangen. Verwerk iedere Critical of Important bevinding en herhaal de betreffende review.

- [ ] **Step 4: Perform visual checks**

Controleer minimaal Genesis 1 en Johannes 3 bij 1440×900 en 390×844, zowel licht als donker, als primaire editie en OPV parallel naast OV. Leg in `pilot-review.md` per combinatie PASS of de concrete bevinding vast.

- [ ] **Step 5: Record honest status**

Laat alle teksten op `concept` staan totdat onafhankelijke bron- en taalreview daadwerkelijk zijn afgerond. Noteer aantallen per status en alle resterende beslispunten in `pilot-review.md`; gebruik nergens `definitief` als alleen technische validatie is uitgevoerd.

- [ ] **Step 6: Commit**

```bash
git add docs/opv data/edities/opv
git commit -m "docs: leg OPV-pilotcontrole vast"
```
