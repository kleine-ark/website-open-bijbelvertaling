# Overdracht tekstronde verwerken Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** De overdracht van 20 augustus inhoudelijk toetsen, echte citaatproblemen herstellen en alle afgeleide gegevens weer in overeenstemming brengen met de huidige tekst.

**Architecture:** De bestaande JSON-versteksten blijven de bron. Een gerichte citaatcorrectiescript verwerkt alleen vooraf handmatig geclassificeerde verzen; tests bewaken tekstbehoud, spanbalans en exacte grenzen. De bestaande generators bouwen daarna principevindplaatsen en statistieken opnieuw op.

**Tech Stack:** Python 3, JSON, pytest/unittest, bestaande scripts in `scripts/`.

**Spec:** `docs/overdracht-2026-08-20.md`

## Global Constraints

- Werk uitsluitend in `C:\Users\rickd\Documents\GitHub\website-open-bijbelvertaling`.
- Raak bestaand parallel woordnummerwerk en de in de overdracht genoemde vuile bestanden niet aan.
- Wijzig geen kale verstekst bij citaatcorrecties; alleen `text2026_html` mag veranderen.
- Pas geen eigenaarskeuzes zoals `broeders`/`broers` of 2 Kronieken 24:7 stilzwijgend toe.
- Stage bestanden altijd expliciet; gebruik nooit `git add -A` of `git add .`.

---

### Task 1: Overdrachtsclaims als regressiecontrole vastleggen

**Files:**
- Create: `tests/test_overdracht_2026_08_20.py`
- Read: `docs/overdracht-2026-08-20.md`
- Read: `data/wijzigingsprincipes.json`

**Interfaces:**
- Consumes: bestaande principes V1504–V1528 en de JSON-versteksten.
- Produces: regressietests voor principe-aantal, unieke ids, geldige bereiken en afwezigheid van lege spraakspans.

- [ ] **Step 1: Write the failing test**

```python
def test_overdracht_principes_en_spans_zijn_consistent():
    assert alle_ids_uniek()
    assert principes_v1504_tot_v1528_aanwezig()
    assert lege_spraakspans() == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_overdracht_2026_08_20.py -q`
Expected: FAIL totdat de concrete hulpfuncties en invarianten zijn vastgelegd.

- [ ] **Step 3: Write minimal implementation**

Lees alle `data/*/*.json`, controleer `text2026_html` op lege `direct-speech`/`god-speaks`-spans en controleer in `data/wijzigingsprincipes.json` de ids en bereiken.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_overdracht_2026_08_20.py -q`
Expected: PASS.

### Task 2: De 27 B-gevallen handmatig classificeren en echte grensfouten herstellen

**Files:**
- Create: `scripts/apply_citation_review_overdracht.py`
- Modify: de betrokken `data/<boek>/<hoofdstuk>.json`-bestanden
- Modify: `tests/test_overdracht_2026_08_20.py`

**Interfaces:**
- Consumes: een mapping `CITATIEGRENZEN[(boek, hoofdstuk, vers)]` met expliciete klasse en begin/einde.
- Produces: idempotente `text2026_html` met ongewijzigde kale tekst en gebalanceerde spans.

- [ ] **Step 1: Add failing boundary tests**

```python
def test_verhaalintro_staat_buiten_het_citaat():
    html = vers_html("job", 42, 7)
    assert html.startswith("Het gebeurde nu")
    assert '<span class="god-speaks"><i>Mijn toorn' in html
```

Leg op dezelfde manier de werkelijk foutieve grenzen vast voor de handmatig beoordeelde verzen. Leg de gevallen die een doorgaande rede zijn expliciet vast als `BEHOUDEN`, zodat het detectiescript daar niet opnieuw blind op wordt toegepast.

- [ ] **Step 2: Run boundary tests to verify they fail**

Run: `python -m pytest tests/test_overdracht_2026_08_20.py -q`
Expected: FAIL op de huidige te ruime spans.

- [ ] **Step 3: Implement the idempotent citation correction script**

Gebruik `zonder_spraak`, `markeer` en `kaal` uit de bestaande citaatscripts. Controleer vóór schrijven per vers:

```python
assert kaal(oude_html) == kaal(nieuwe_html)
assert nieuwe_html.count('<span') == nieuwe_html.count('</span>')
assert nieuwe_html.count('<i>') == nieuwe_html.count('</i>')
```

- [ ] **Step 4: Run the script twice and verify idempotence**

Run: `python scripts/apply_citation_review_overdracht.py` tweemaal, gevolgd door `git diff --exit-code` op een tijdelijke tweede uitvoercontrole.
Expected: de tweede uitvoering verandert niets.

- [ ] **Step 5: Run focused and corpus citation checks**

Run:

```bash
python -m pytest tests/test_overdracht_2026_08_20.py -q
python scripts/span_om_vertelling.py --proef --soorten B --toon 200
```

Expected: alle vastgelegde grenzen slagen; resterende B-meldingen zijn expliciet als doorgaande/geneste rede beoordeeld en geen onbeoordeelde fout.

### Task 3: Afgeleide principe- en statistiekgegevens herbouwen

**Files:**
- Modify: `data/principes-data.json` of het bestaande uitvoerbestand van `build_principes_data.py`
- Modify: `data/stats.json`
- Test: `tests/test_overdracht_2026_08_20.py`

**Interfaces:**
- Consumes: actuele versteksten, `data/wijzigingsprincipes.json` en `data/verified-chapters.json`.
- Produces: actuele principevindplaatsen en statistieken met 1.528 principes.

- [ ] **Step 1: Add a failing stale-statistics test**

```python
def test_stats_volgen_de_principesbron():
    assert stats()["principes"] == len(principes()["principes"])
```

- [ ] **Step 2: Verify the stale-statistics test fails**

Run: `python -m pytest tests/test_overdracht_2026_08_20.py -q`
Expected: FAIL omdat `data/stats.json` nog 1503 principes vermeldt terwijl de bron 1528 bevat.

- [ ] **Step 3: Rebuild derived data**

Run:

```bash
python scripts/build_principes_data.py
python scripts/build_stats.py
```

- [ ] **Step 4: Verify generated data**

Run: `python -m pytest tests/test_overdracht_2026_08_20.py -q`
Expected: PASS en `stats.principes == 1528`.

### Task 4: Eindcontrole en afbakening van eigenaarskeuzes

**Files:**
- Modify: `docs/overdracht-2026-08-20.md` alleen wanneer een feitelijke statusregel achterhaald is.

**Interfaces:**
- Consumes: alle uitvoer van Tasks 1–3.
- Produces: gecontroleerde werkboom en een lijst met uitsluitend resterende eigenaarskeuzes.

- [ ] **Step 1: Run all relevant audits**

Run:

```bash
python scripts/audit_principes.py --snel
python -m pytest tests/test_overdracht_2026_08_20.py -q
python -c "import json,glob; [json.load(open(f,encoding='utf-8')) for f in glob.glob('data/*/*.json')]"
git diff --check
```

Expected: geen principeproblemen, geen JSON-fouten, alle tests groen en geen whitespacefouten.

- [ ] **Step 2: Inspect scope**

Run: `git status -sb` en `git diff --stat`.
Expected: alleen de expliciet verwerkte citaat-, test-, plan- en afgeleide databestanden zijn nieuw gewijzigd; parallel woordnummerwerk blijft onaangeraakt.

- [ ] **Step 3: Report remaining decisions**

Rapporteer afzonderlijk: `broeders`/`broers`, `leger`/`kamp`, 2 Kronieken 24:7 en overige meldingen waarbij de overdracht zelf een eigenaarskeuze noemt. Pas deze niet automatisch toe.
