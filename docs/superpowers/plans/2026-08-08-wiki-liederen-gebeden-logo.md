# Liederen en Gebeden Wiki Logo Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Voeg subtiel bewegende, naadloos lussende WebP-logo's toe aan de wiki-tegels Liederen en Gebeden.

**Architecture:** Twee gegenereerde handgetekende illustraties vormen de ontwerpbron. Een kleine bouwscript voegt alleen lokale, periodieke licht- en rookeffecten toe; `wiki-overzicht.html` kiest bewegend of stil via `<picture>` en `prefers-reduced-motion`.

**Tech Stack:** Python 3, Pillow, HTML `<picture>`, pytest.

## Global Constraints

- Sluit aan op het perkament, de fijne inktlijnen en de gedempte goud-/marineaccenten van de overige wiki-illustraties.
- De lus duurt 4–6 seconden, is naadloos en bevat alleen subtiele beweging.
- De gegenereerde rasterbron blijft de fallback voor verminderde beweging; gebruik voor deze twee tegels geen SVG.
- Raak het losse evangelisatietraktaat en andere niet-gerelateerde bestanden niet aan.

---

### Task 1: Contracttests voor de twee logo's

**Files:**
- Create: `tests/test_wiki_liederen_gebeden_logos.py`

**Interfaces:**
- Consumes: `images/wiki/liederen.webp`, `images/wiki/gebeden.webp`, `wiki-overzicht.html`
- Produces: pytest-contract voor twee geldige geanimeerde WebP's en de HTML-koppeling

- [x] **Step 1: Voeg falende tests toe voor beide bestanden, animatieduur en `<picture>`-koppelingen.**
- [x] **Step 2: Draai `python -m pytest -q tests/test_wiki_liederen_gebeden_logos.py` en bevestig dat de twee bestanden ontbreken.**

### Task 2: Bewegende WebP's bouwen

**Files:**
- Create: `scripts/build_wiki_liederen_gebeden_logos.py`
- Create: `images/wiki/liederen.webp`
- Create: `images/wiki/gebeden.webp`

**Interfaces:**
- Consumes: `images/wiki/bronnen/liederen.webp` en `images/wiki/bronnen/gebeden.webp`
- Produces: twee WebP's van 600 × 300, 50 frames, 100 ms per frame, oneindige loop

- [x] **Step 1: Render 50 periodieke frames per illustratie waarvan de laatste fase vloeiend op de eerste aansluit.**
- [x] **Step 2: Sla de frames op als verliesloze geanimeerde WebP met `loop=0`.**
- [x] **Step 3: Controleer afmetingen, frameaantal, duur en loopmetadata via de WebP-container.**

### Task 3: Tegels koppelen en verifiëren

**Files:**
- Modify: `wiki-overzicht.html`
- Create: `tests/test_wiki_liederen_gebeden_logos.py`

**Interfaces:**
- Consumes: de twee gebouwde WebP's
- Produces: bewegende tegels met gegenereerde rasterfallback

- [x] **Step 1: Vervang beide losse `<img>`-elementen door het bestaande `<picture>`-patroon.**
- [x] **Step 2: Draai `python -m pytest -q tests/test_wiki_liederen_gebeden_logos.py`.**
- [x] **Step 3: Draai de volledige relevante testsuite en controleer `git diff --check`.**
- [x] **Step 4: Bekijk beide animaties visueel en commit uitsluitend de wiki-logo-eenheid.**
