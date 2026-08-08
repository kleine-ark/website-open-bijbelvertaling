# Wiki Cinemagraphs Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Vervang de acht overgebleven statische wiki-onderwerpafbeeldingen door rustige geanimeerde WebP-lussen, met behoud van de bestaande SVG's als fallback voor bezoekers die minder beweging verkiezen.

**Architecture:** Elke van de negen bestaande `<img>`-elementen komt in een `<picture>`-element. Een WebP-`<source>` wordt alleen geselecteerd bij `prefers-reduced-motion: no-preference`; het bestaande SVG-`<img>` blijft de universele fallback. Een standaardbibliotheektest controleert zowel de HTML-koppeling als de WebP-container, afmetingen, animatieframes, lusduur en oneindige herhaling.

**Tech Stack:** Statische HTML/CSS, geanimeerde WebP, Python `unittest` met uitsluitend de standaardbibliotheek.

## Global Constraints

- Gebruik exact de acht basisnamen `kaart`, `stamboom`, `geografie`, `maateenheden`, `tijdsaanduidingen`, `materialen`, `dieren` en `bomen-planten`.
- Elke animatie is 600×300 pixels, duurt 4–6 seconden en herhaalt oneindig.
- Laat de tegels `liederen` en `gebeden` ongewijzigd.
- Bewaar de bestaande SVG-bestanden als fallback bij `prefers-reduced-motion: reduce` en voor browsers zonder WebP-ondersteuning.
- Voeg geen JavaScript of nieuwe runtime-afhankelijkheden toe.

---

### Task 1: Geanimeerde wiki-tegels integreren

**Files:**
- Create: `tests/test_wiki_cinemagraphs.py`
- Create: `images/wiki/kaart.webp`
- Create: `images/wiki/stamboom.webp`
- Create: `images/wiki/geografie.webp`
- Create: `images/wiki/maateenheden.webp`
- Create: `images/wiki/tijdsaanduidingen.webp`
- Create: `images/wiki/materialen.webp`
- Create: `images/wiki/dieren.webp`
- Create: `images/wiki/bomen-planten.webp`
- Modify: `wiki-overzicht.html`
- Modify: `css/naslag.css`

**Interfaces:**
- Consumes: de bestaande `.wo-kaart`-structuur en de negen SVG-fallbacks onder `images/wiki/`.
- Produces: acht nieuwe `<picture>`-elementen die `images/wiki/<naam>.webp` tonen als beweging is toegestaan en `images/wiki/<naam>.svg` tonen als fallback. De reeds bestaande Liederen- en Gebeden-tegels blijven ongewijzigd.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_wiki_cinemagraphs.py` with tests voor de motion-aware WebP `<source>`, de bestaande SVG-fallbacks en de verwijderde Begrippenpagina. De animatietest parseert RIFF-chunks en vereist een 600×300 canvas, een `ANIM`-luswaarde van nul, meer dan één `ANMF`-frame en een totale duur tussen 4.000 en 6.000 milliseconden.

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m unittest discover -s tests -p test_wiki_cinemagraphs.py -v`

Expected: FAIL because `wiki-overzicht.html` still refers directly to `.svg` and the nine `.webp` files are not yet in this checkout.

- [ ] **Step 3: Copy the approved WebP assets**

Copy the eight verified assets from the temporary transfer workspace to this repository's `images/wiki/` directory, preserving their exact filenames.

- [ ] **Step 4: Add motion-aware picture elements**

For each of the nine named cards, replace the direct image with this exact structure, substituting the matching basename:

```html
<picture>
    <source srcset="images/wiki/kaart.webp" type="image/webp" media="(prefers-reduced-motion: no-preference)">
    <img src="images/wiki/kaart.svg" alt="">
</picture>
```

Add the wrapper rule without changing existing image sizing:

```css
.wo-kaart picture { display: block; width: 100%; }
```

- [ ] **Step 5: Run focused tests to verify they pass**

Run: `python -m unittest discover -s tests -p test_wiki_cinemagraphs.py -v`

Expected: 2 tests pass.

- [ ] **Step 6: Run the existing test suite**

Run: `python -m unittest discover -s tests -v`

Expected: all Python tests pass.

- [ ] **Step 7: Review and commit the logical unit**

Run: `git diff --check && git status --short`

Commit only the plan, test, HTML/CSS and eight WebP assets plus de verwijdering van de Begrippenpagina met message `Wiki-tegels voorzien van rustige animaties`.
