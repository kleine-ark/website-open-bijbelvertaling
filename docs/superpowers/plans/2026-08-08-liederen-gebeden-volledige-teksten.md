# Liederen en Gebeden Volledige Teksten Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Nummer 31 liederen en 45 gebeden chronologisch, splits Paulus' drie gemeentebeden op en toon op iedere detailpagina de volledige letterlijke tekst, met alle 150 Psalmen als één lied-item.

**Architecture:** De twee naslagbestanden blijven de redactionele bron en krijgen expliciete `tekstpassages`. Een Python-builder valideert die grenzen tegen de hoofdstukdata en schrijft per item één browserbundel; `js/naslag.js` haalt alleen de gekozen bundel op en rendert nummer, passagekoppen en verzen.

**Tech Stack:** JSON, Python 3.11 standaardbibliotheek, statische HTML, vanilla JavaScript, CSS, pytest/unittest, Playwright.

## Global Constraints

- De liedreeks is exact `Lied 1` t/m `Lied 31`; de gebedsreeks exact `Gebed 1` t/m `Gebed 45`.
- Paulus wordt drie items: Efeziërs 1:16–23, Efeziërs 3:14–21 en Filippenzen 1:9–11.
- De negen gebedspsalmen zijn Psalm 17, 51, 72, 86, 90, 102, 119, 130 en 142.
- De 150 Psalmen blijven samen één lied-item met één liednummer en springlijst 1–150.
- Gebruik uitsluitend niet-lege `text2026`; geen fallback naar `text1637`, `textSV1888` of `text2026_html`.
- Knip een vers nooit middenin af en reconstrueer geen niet-overgeleverde woorden.
- Behoud de ontbrekende gebedenintro en het verwijderde lied van Lamech.
- Blijf geschikt voor iPadOS 15.4.
- Behoud reeds aanwezige wijzigingen in beide naslagdata, `js/naslag.js` en `css/naslag.css`.

---

## File Structure

- Modify `data/naslag-liederen.json`: volgorde, `nummerType`, `tekstpassages` en meldingen.
- Modify `data/naslag-gebeden.json`: 45 items, zeven nieuwe Psalm-items, drie Paulusitems en passages.
- Create `scripts/build_naslag_teksten.py`: passagevalidatie en bundelbouw.
- Create `data/naslag-teksten/liederen/*.json`: 31 gegenereerde bundels.
- Create `data/naslag-teksten/gebeden/*.json`: 45 gegenereerde bundels.
- Create `tests/test_naslag_liederen_gebeden.py`: data- en bouwtests.
- Create `tests/test_wiki_liederen_gebeden.py`: browsertests.
- Modify `js/naslag.js`: nummerlabels en volledige tekst.
- Modify `css/naslag.css`: nummer-, passage-, vers- en springlijstopmaak.
- Modify `.github/workflows/deploy.yml` en `desktop/build-dist.mjs`: bouw bundels vóór kopiëren.

### Task 1: Chronologische brondata en passagegrenzen

**Files:**
- Modify: `data/naslag-liederen.json`
- Modify: `data/naslag-gebeden.json`
- Create: `tests/test_naslag_liederen_gebeden.py`

**Interfaces:**
- Produces per bestand: `nummerType: "Lied" | "Gebed"`.
- Produces per item: `tekstpassages: Array<Passage>` en optioneel `tekstmelding: string`.
- Gewone passage: `{boek, hoofdstuk, van, tot, label}`.
- Boekreeks: `{boek, vanHoofdstuk, totHoofdstuk, label}`; alleen Psalm 1–150.

- [ ] **Step 1: Schrijf falende tests voor aantallen en hoofdkeuzes**

```python
def test_reeksen_zijn_compleet(liederen, gebeden):
    assert len(liederen["items"]) == 31
    assert len(gebeden["items"]) == 45
    assert liederen["nummerType"] == "Lied"
    assert gebeden["nummerType"] == "Gebed"

def test_paulus_is_opgesplitst(gebeden):
    ids = [x["id"] for x in gebeden["items"]]
    assert "paulus-gebeden-voor-de-gemeenten" not in ids
    assert ids[-3:] == ["paulus-eerste-gebed-voor-efeze",
                        "paulus-tweede-gebed-voor-efeze",
                        "paulus-gebed-voor-filippi"]
```

Test dat `de-psalmen` één lied-item is met boekreeks 1–150, Lamech ontbreekt en Gebeden geen `intro` heeft.

- [ ] **Step 2: Schrijf falende tests voor negen gebedspsalmen**

```python
expected = {17: (1, 15), 51: (1, 21), 72: (1, 20),
            86: (1, 17), 90: (1, 17), 102: (1, 29),
            119: (1, 176), 130: (1, 8), 142: (1, 8)}
```

Controleer één item per hoofdstuk en de volgorde: 142 vóór 17, 17 vóór 2 Samuël 7, 51 vóór 72, 102 in het ballingschapsblok en 130 na Nehemia.

- [ ] **Step 3: Draai en bevestig de datagaten**

Run: `python -m pytest tests/test_naslag_liederen_gebeden.py -q`

Expected: FAIL op 36 gebeden, het Paulus-verzamelitem en ontbrekende passages.

- [ ] **Step 4: Werk de 31 liederen bij**

Gebruik exact de liedtabel in `docs/superpowers/specs/2026-08-08-liederen-gebeden-volledige-teksten-design.md`: Henoch is Lied 1, Schelfzee Lied 2, Psalmen Lied 13 en Openbaring 15 Lied 31. Splits passages over hoofdstukgrenzen in gewone passageobjecten. Geef niet-overgeleverde woorden een `tekstmelding`; verzin geen tekst.

- [ ] **Step 5: Werk de 45 gebeden bij**

Gebruik exact de gebedstabel uit dezelfde specificatie. Voeg deze id's toe: `davids-gebed-in-de-grot-psalm-142`, `davids-gebed-om-bewaring-psalm-17`, `davids-gebed-in-benauwdheid-psalm-86`, `gebed-om-leven-naar-gods-woord-psalm-119`, `davids-gebed-voor-salomo-psalm-72`, `gebed-van-de-verdrukte-psalm-102`, `gebed-uit-de-diepten-psalm-130`. Schrijf per nieuw item 2–4 feitelijke zinnen uit de volledig herlezen `text2026`-passage. Voeg de drie Paulusitems toe en verwijder het verzamelitem.

- [ ] **Step 6: Valideer vorm en unieke id's**

Test niet-lege unieke `id`, `naam`, `beschrijving`, `verzen` en `tekstpassages`; toegestane passagesleutels; `van <= tot`; en exact één `nummerType` per bestand.

- [ ] **Step 7: Draai en commit**

Run: `python -m pytest tests/test_naslag_liederen_gebeden.py -q`

Expected: datamodeltests PASS; bouwtests mogen nog falen omdat de builder ontbreekt.

```powershell
git add -- data/naslag-liederen.json data/naslag-gebeden.json tests/test_naslag_liederen_gebeden.py
git diff --cached --check
git commit -m "feat: orden liederen en 45 gebeden"
```

### Task 2: Gevalideerde tekstbundels bouwen

**Files:**
- Create: `scripts/build_naslag_teksten.py`
- Create: `data/naslag-teksten/liederen/*.json`
- Create: `data/naslag-teksten/gebeden/*.json`
- Modify: `tests/test_naslag_liederen_gebeden.py`

**Interfaces:**
- Consumes: passagevorm uit Task 1 en `data/<boek>/<hoofdstuk>.json`.
- Produces: `build_all(root: pathlib.Path, write: bool = True) -> dict[str, dict[str, dict]]`.
- Bundel: `{id, nummerType, nummer, naam, passages, tekstmelding?}`.
- Passagebundel: `{label, sections}`; sectie `{boek, hoofdstuk, verzen}`; vers `{nummer, tekst}`.

- [ ] **Step 1: Schrijf falende bouwtests**

```python
def test_gebouwd_vers_is_exact_text2026(built, root):
    verse = built["gebeden"]["abrahams-voorbede-voor-sodom"]["passages"][0]["sections"][0]["verzen"][0]
    source = load_chapter(root, "genesis", 18)["verses"]
    assert verse["tekst"] == next(v["text2026"] for v in source if v["number"] == 23)

def test_psalmenbundel_heeft_150_secties(built):
    assert len(built["liederen"]["de-psalmen"]["passages"][0]["sections"]) == 150
```

Test ook leeg `text2026` (`ValueError`), ontbrekend hoofdstuk/vers, dubbele id, verkeerde aantallen en eerste/laatste vers van iedere passage.

- [ ] **Step 2: Draai en bevestig ontbrekende builder**

Run: `python -m pytest tests/test_naslag_liederen_gebeden.py -q`

Expected: FAIL op import van `scripts.build_naslag_teksten`.

- [ ] **Step 3: Implementeer exacte functies**

Definieer `load_chapter(root: Path, book: str, chapter: int) -> dict`,
`expand_passage(root: Path, passage: dict) -> dict`,
`build_collection(root: Path, kind: str, source_name: str) -> dict[str, dict]`
en `build_all(root: Path, write: bool = True) -> dict[str, dict[str, dict]]`.
`load_chapter()` leest exact `root / "data" / book / f"{chapter}.json"` als
UTF-8 JSON en geeft een duidelijke `ValueError` met boek en hoofdstuk bij een
ontbrekend of ongeldig bestand.

`expand_passage()` bewaart `text2026` ongewijzigd als `tekst` en weigert ontbrekende/lege tekst. Een boekreeks maakt één sectie per hoofdstuk. `build_collection()` leidt het nummer uitsluitend af uit de arraypositie en eist 31 of 45 items.

- [ ] **Step 4: Schrijf deterministisch en veilig**

Schrijf met `ensure_ascii=False`, `indent=2` en newline naar `data/naslag-teksten/liederen/<id>.json` en `data/naslag-teksten/gebeden/<id>.json`. Verwijder alleen verouderde JSON-bestanden binnen precies die twee gevalideerde doelmappen.

- [ ] **Step 5: Bouw, test en controleer determinisme**

```powershell
python scripts/build_naslag_teksten.py
python -m pytest tests/test_naslag_liederen_gebeden.py -q
python scripts/build_naslag_teksten.py
git diff --exit-code -- data/naslag-teksten
```

Expected: PASS, 31 liedbundels, 45 gebedsbundels, geen tweede-builddiff.

- [ ] **Step 6: Commit**

```powershell
git add -- scripts/build_naslag_teksten.py data/naslag-teksten tests/test_naslag_liederen_gebeden.py
git diff --cached --check
git commit -m "feat: bouw volledige lied- en gebedsteksten"
```

### Task 3: Nummerlabels en volledige tekst renderen

**Files:**
- Modify: `js/naslag.js`
- Modify: `css/naslag.css`
- Create: `tests/test_wiki_liederen_gebeden.py`

**Interfaces:**
- Consumes: `nummerType`, arraypositie en `data/naslag-teksten/<soort>/<id>.json`.
- Produces: `bundelPad(data, item) -> string` en `toonVolledigeTekst(container, bundle) -> void`.

- [ ] **Step 1: Schrijf falende overzichtstests**

Controleer op Liederen 31 labels `Lied 1`…`Lied 31`; op Gebeden 45 labels `Gebed 1`…`Gebed 45`; geen Lamech of gebedenintro; en drie losse Pauluskaarten als laatste items.

- [ ] **Step 2: Schrijf falende detailtests**

Controleer Schelfzee (`Lied 2`, Exodus 15:1 en 15:18), Abraham (`Gebed 1`, Genesis 18:23 en 18:33), Psalm 119 (vers 1 en 176), drie verschillende Paulus-URL's en tekstbundels, en de eerlijke melding bij het laatste avondmaal.

- [ ] **Step 3: Draai en bevestig ontbrekende UI**

Run: `python -m pytest tests/test_wiki_liederen_gebeden.py -q`

Expected: FAIL op `.ns-nummer` en `.ns-volledige-tekst`.

- [ ] **Step 4: Render nummers uit de arraypositie**

Gebruik `i + 1` in het overzicht en de gevonden itemindex op detail. Render vóór de naam/titel `<span class="ns-nummer">Lied 1</span>` of `<span class="ns-nummer">Gebed 1</span>`.

- [ ] **Step 5: Laad alleen de gekozen bundel**

Render een `<section class="ns-volledige-tekst">` met kop `Volledige tekst` en laadmelding. Fetch de bundel voor het gekozen id. Render passagelabels als `<h3>`, sectiekoppen met anker en elk vers als `<p class="ns-tekstvers"><sup>nummer</sup> tekst</p>`. Zet tekst met `textContent`, nooit `innerHTML`. Bij fout verschijnt alleen `De volledige tekst kon niet geladen worden.`; beschrijving en vindplaatsen blijven staan.

- [ ] **Step 6: Voeg Psalmen-springlijst toe**

Voor `de-psalmen` komt `<nav class="ns-psalm-sprongen" aria-label="Ga naar een psalm">` met links 1–150. Secties krijgen `id="psalm-N"` en `scroll-margin-top`.

- [ ] **Step 7: Voeg toegankelijke opmaak toe**

Definieer `.ns-nummer`, `.ns-volledige-tekst`, `.ns-passage`, `.ns-sectie-kop`, `.ns-tekstvers`, `.ns-tekstvers sup`, `.ns-tekstmelding` en `.ns-psalm-sprongen`; behoud 16px mobiel, donker thema en zichtbare toetsenbordfocus.

- [ ] **Step 8: Draai en commit**

```powershell
python -m pytest tests/test_wiki_liederen_gebeden.py tests/test_wiki_reading_gutter.py -q
git add -- js/naslag.js css/naslag.css tests/test_wiki_liederen_gebeden.py
git diff --cached --check
git commit -m "feat: toon genummerde liederen en gebeden"
```

Expected: PASS.

### Task 4: Bouwstappen en versheid afdwingen

**Files:**
- Modify: `.github/workflows/deploy.yml`
- Modify: `desktop/build-dist.mjs`
- Modify: `tests/test_naslag_liederen_gebeden.py`

**Interfaces:**
- Consumes: `python scripts/build_naslag_teksten.py`.
- Produces: verse bundels vóór deploy en desktopdist.

- [ ] **Step 1: Schrijf een versheidstest**

Roep `build_all(ROOT, write=False)` aan en vergelijk elk verwacht object met het ingelezen bestand onder `data/naslag-teksten`; controleer ook dat geen extra JSON-bestanden bestaan.

- [ ] **Step 2: Werk de deploybuild bij**

```yaml
build_command: python scripts/build_naslag_teksten.py && python scripts/build_downloads.py
```

- [ ] **Step 3: Bouw vóór desktopkopie**

Importeer `spawnSync` uit `node:child_process` en voer vóór het schoonmaken uit:

```javascript
const built = spawnSync('python', [join(root, 'scripts', 'build_naslag_teksten.py')], {
  cwd: root, stdio: 'inherit'
});
if (built.status !== 0) throw new Error('bouwen naslagteksten mislukt');
```

- [ ] **Step 4: Verifieer website- en desktopbuild**

```powershell
python scripts/build_naslag_teksten.py
node desktop/build-dist.mjs
python -m pytest tests/test_naslag_liederen_gebeden.py tests/test_wiki_liederen_gebeden.py -q
```

Expected: PASS; `desktop/dist/data/naslag-teksten` bevat 31 + 45 bestanden.

- [ ] **Step 5: Commit**

```powershell
git add -- .github/workflows/deploy.yml desktop/build-dist.mjs tests/test_naslag_liederen_gebeden.py
git diff --cached --check
git commit -m "build: ververs wiki-tekstbundels"
```

### Task 5: Eindverificatie en lokale sitecontrole

**Files:**
- Verify only; wijzig uitsluitend bij een aangetoonde fout.

**Interfaces:**
- Consumes: Tasks 1–4.
- Produces: lokaal en bij deploy bruikbare lied- en gebedspagina's.

- [ ] **Step 1: Draai relevante tests**

```powershell
python -m pytest tests/test_naslag_liederen_gebeden.py tests/test_wiki_liederen_gebeden.py tests/test_wiki_reading_gutter.py tests/test_wiki_cinemagraphs.py -q
```

Expected: alle tests PASS.

- [ ] **Step 2: Controleer aantallen en determinisme**

```powershell
python scripts/build_naslag_teksten.py
git diff --exit-code -- data/naslag-teksten
git diff --check
```

Expected: 31 liedbundels, 45 gebedsbundels en geen diff.

- [ ] **Step 3: Controleer lokaal kritieke pagina's**

Open Liederen-overzicht, Schelfzee, Psalmen, Gebeden-overzicht, Psalm 119 en de drie Paulusgebeden. Controleer nummers, eerste/laatste verzen, springlijst, laadfoutgedrag, donker thema, desktop en 390px mobiel.

- [ ] **Step 4: Corrigeer en herhaal alleen indien nodig**

Stage uitsluitend een aantoonbare correctie, herhaal Steps 1–3 en commit met een specifieke boodschap zoals `fix: herstel psalmsprongen op mobiel`.
