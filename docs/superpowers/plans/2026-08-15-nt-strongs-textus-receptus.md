# Strongs voor het volledige Nieuwe Testament — implementatieplan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ieder woord van de Textus Receptus éénmaal en controleerbaar inline verbinden met de Nederlandse tekst van het volledige Nieuwe Testament.

**Architecture:** Een generieke, gepinde TR-importlaag combineert Robinson/Scrivener voor Strong en morfologie met CrossWire OSIS voor de exacte Griekse woordvorm. Per hoofdstuk staat daarnaast een afzonderlijk handmatig reviewbestand met Nederlandse ankers, expliciete niet-afzonderlijk vertaalde tokens en eventuele versindelingsafwijkingen. Alleen volledig gecontroleerde hoofdstukken worden naar de leesdata en het inlinebestand gepubliceerd.

**Tech Stack:** Python 3.12, JSON, bestaand JavaScript-component `js/woordnummers.js`, pytest en Playwright.

**Spec:** `strongs-en-grondtekst.html`

## Global Constraints

- Nieuwe Testament: Textus Receptus.
- Alle bronbestanden zijn gepind met commit en SHA-256.
- Ieder TR-token komt precies eenmaal in de inlineprojectie voor.
- Niet-afzonderlijk vertaalde grondwoorden blijven zichtbaar met een lege Nederlandse tekst en een expliciet anker.
- Grondtekst- of versindelingsafwijkingen worden vastgelegd en nooit speculatief gekoppeld.
- Publicatie gebeurt per volledig gecontroleerd hoofdstuk.

---

### Task 1: Generieke TR-hoofdstukbouwer

**Files:**
- Create: `scripts/rebuild_nt_tr_strongs.py`
- Modify: `scripts/rebuild_johannes1_tr_strongs.py`
- Test: `tests/test_import_inline_woordnummers.py`

**Interfaces:**
- Consumes: een UTR-boekbestand, `kjv.osis.xml`, een repo-boeknaam, hoofdstuknummer en review-JSON.
- Produces: `build_chapter(book, chapter, utr_path, osis_path, review_path, write=False) -> dict`.

- [ ] Schrijf een falende test die Johannes 1 via de generieke interface op 846 unieke tokens controleert.
- [ ] Voer de test uit en bevestig dat `rebuild_nt_tr_strongs` nog ontbreekt.
- [ ] Verplaats de generieke bronparsers en validatie zonder het bestaande Johannes-resultaat te veranderen.
- [ ] Voer de gegevens- en Johannes-browsertests uit.
- [ ] Commit de generieke bouwer en tests.

### Task 2: Johannes 2 handmatig controleren

**Files:**
- Create: `data/woordnummers-review/johannes-2.json`
- Modify: `data/johannes/2.json`
- Modify: `data/woordnummers-inline/johannes.json`
- Test: `tests/test_strongs_reader.py`

**Interfaces:**
- Consumes: `build_chapter(...)` uit Task 1 en de Nederlandse `text2026` per vers.
- Produces: een volledige review met `tekst`, `voorkomen`, `bronindices`, `status`, `anker` en `plaats`.

- [ ] Schrijf een falende gegevenstest voor volledige tokenbedekking en unieke bronindices in Johannes 2.
- [ ] Maak per vers de Nederlandse woordgroepen en niet-afzonderlijk vertaalde tokens expliciet.
- [ ] Bouw Johannes 2 en controleer dat iedere Strong exact eenmaal voorkomt.
- [ ] Voeg browserankertests toe voor vers 1, vers 11 en vers 25, inclusief één niet-afzonderlijk vertaald token.
- [ ] Voer de volledige Johannes- en auditset uit.
- [ ] Commit de gecontroleerde hoofdstukbatch.

### Task 3: Johannes 3–21 in hoofdstukbatches

**Files:**
- Create: `data/woordnummers-review/johannes-<hoofdstuk>.json`
- Modify: `data/johannes/<hoofdstuk>.json`
- Modify: `data/woordnummers-inline/johannes.json`
- Test: `tests/test_strongs_reader.py`

**Interfaces:**
- Consumes: dezelfde reviewstructuur en bouwer als Task 2.
- Produces: één aantoonbaar volledig gecontroleerd hoofdstuk per batch.

- [ ] Schrijf vóór iedere batch een falende hoofdstukdekkingstest.
- [ ] Controleer elk vers en leg afwijkingen expliciet vast.
- [ ] Bouw het hoofdstuk en voer gegevens-, anker- en browsertests uit.
- [ ] Commit alleen de groene hoofdstukbatch.

### Task 4: Overige NT-boeken

**Files:**
- Create: `data/woordnummers-review/<boek>-<hoofdstuk>.json`
- Modify: `data/<boek>/<hoofdstuk>.json`
- Modify: `data/woordnummers-inline/<boek>.json`
- Modify: `data/woordnummers-inline/status.json`
- Test: `tests/test_strongs_reader.py`

**Interfaces:**
- Consumes: gepinde boekcode→UTR/OSIS-koppeling en de hoofdstukbouwer.
- Produces: complete, handmatig gecontroleerde NT-inlinegegevens en voortgang per boek/hoofdstuk.

- [ ] Werk boek voor boek en hoofdstuk voor hoofdstuk.
- [ ] Voeg per hoofdstuk minimaal drie representatieve browserankertests toe.
- [ ] Houd ongemapte afwijkingen traceerbaar in het reviewbestand.
- [ ] Werk de status alleen bij na groene hoofdstuktests.
- [ ] Publiceer kleine, terug te draaien batches.

### Task 5: Eindcontrole Nieuwe Testament

**Files:**
- Modify: `docs/woordnummers-status-per-boek.md`
- Modify: `data/woordnummers-inline/status.json`
- Test: `tests/test_build_woordnummers_corpus.py`

**Interfaces:**
- Consumes: alle gecontroleerde NT-hoofdstukken.
- Produces: een audit waarin ieder aanwezige TR-token exact eenmaal is gepubliceerd en alle uitzonderingen traceerbaar zijn.

- [ ] Controleer bronhashes en tokenaantallen van alle 27 boeken.
- [ ] Draai de volledige gegevens-, audit- en browserset.
- [ ] Vergelijk alle ongemapte afwijkingen met de reviewmetadata.
- [ ] Werk de openbare status en methodedocumentatie bij.
- [ ] Publiceer de eindbatch pas zonder NT-gerelateerde regressies.
