# Evangelisatietraktaat Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Een boekje-pagina in `22 Evangelisatietraktaat/` die 194 geselecteerde bijbelhoofdstukken live uit de OSV-data toont, links de tekst en rechts een afbeelding met uitleg.

**Architecture:** De pagina laadt niets vooraf: `js/selectie.js` bepaalt welke passages er zijn, `js/render.js` bouwt HTML-strings uit gegevens (pure functies), `js/laden.js` haalt hoofdstukken op via `fetch`, en `js/traktaat.js` koppelt dat aan de DOM met een `IntersectionObserver` zodat elke spread pas laadt bij het naderen. De paden naar data, afbeeldingen en de leesomgeving staan in `js/config.js`, zodat het traktaat later als losse website kan draaien.

**Tech Stack:** Vanilla JavaScript (ES modules), HTML, CSS. Node 20 (`node --test`) voor de unit-tests, Python 3 voor het selectie-controlescript. Geen build-stap, geen dependencies.

## Global Constraints

- **Werkmap is de git-repo `/home/maarten/Documents/GitHub/website-open-bijbelvertaling`.** Werk nooit in de Dropbox-map `…/19 Open Vertaling`: die is een spiegel, en `sync-dropbox.sh` (`rsync --delete`) wist daar alles wat niet uit de repo komt.
- Alle paden in dit plan zijn relatief aan `22 Evangelisatietraktaat/` binnen die repo.
- Branch is `main`, single-developer workflow. `git pull --rebase` vóór je begint; per taak één commit.
- Alleen `text2026` wordt getoond. Geen kanttekeningen, geen hoofdstukinleiding, geen 1637-tekst.
- De godsnaam blijft zoals hij in `data/` staat (JAHWEH). Er wordt geen enkele tekstvervanging op de bijbeltekst gedaan.
- Geen dependencies, geen build-stap, geen framework. Vanilla JS, ES modules.
- `js/config.js` en `js/selectie.js` zijn klassieke scripts die op `window` schrijven (zoals `js/audio-available.js` in de repo-root). `js/render.js`, `js/laden.js` en `js/traktaat.js` zijn ES modules.
- `js/selectie.js` bevat tussen de eerste `[` en de laatste `]` **geldige JSON** (dubbele aanhalingstekens, geen commentaar), zodat het controlescript het zonder JS-parser kan lezen.
- Nederlandstalige namen voor bestanden, functies, variabelen en commentaar, in lijn met de rest van de repo.
- Ontwerpdocument: `docs/superpowers/specs/2026-07-26-evangelisatietraktaat-design.md`.

---

## File Structure

| Bestand | Verantwoordelijkheid |
|---------|----------------------|
| `js/config.js` | `window.TRAKTAAT_CONFIG` — `DATA_BASE`, `IMG_BASE`, `LEES_BASE` |
| `js/selectie.js` | `window.TRAKTAAT_SELECTIE` — de 194 passages, één regel per passage |
| `js/render.js` | Pure functies: URL's, titels, HTML-strings. Geen DOM, geen fetch |
| `js/laden.js` | Ophalen van een hoofdstuk en filteren op versbereik. Geen DOM |
| `js/traktaat.js` | DOM: inhoudsopgave, spread-skeletten, `IntersectionObserver`, invullen, opnieuw proberen |
| `index.html` | Structuur: zijbalk, boekje-container, scripts |
| `css/traktaat.css` | Opmaak: tweekoloms-spread, sticky rechterkolom, kaders |
| `data/uitleg.json` | Uitleg per passage, sleutel `boek_hoofdstuk` |
| `scripts/controleer_selectie.py` | Valideert de selectie tegen `../data/` |
| `tests/render.test.mjs` | Unit-tests voor `js/render.js` |
| `tests/laden.test.mjs` | Unit-tests voor `js/laden.js` |

---

### Task 1: Selectie en controlescript

**Files:**
- Create: `js/selectie.js`
- Create: `scripts/controleer_selectie.py`

**Interfaces:**
- Consumes: `../data/<boek>/<hoofdstuk>.json` en `../data/books.json` uit de repo-root.
- Produces: `window.TRAKTAAT_SELECTIE` — array van objecten `{boek: string, hoofdstuk: number, verzen?: [number, number], titel?: string}`. `verzen` is inclusief aan beide kanten. `titel` overschrijft de automatisch gebouwde titel (alleen gebruikt voor Gebed van Manasse).

- [ ] **Step 1: Schrijf het controlescript**

Maak `scripts/controleer_selectie.py`:

```python
#!/usr/bin/env python3
"""Controleert js/selectie.js tegen de OSV-data in ../data/.

Meldt elke passage waarvan het boek of hoofdstuk niet bestaat of waarvan het
versbereik buiten het hoofdstuk valt. Exit-code 1 bij fouten.
"""
import json
import sys
from pathlib import Path

WERKMAP = Path(__file__).resolve().parent.parent
DATA = WERKMAP.parent / "data"


def lees_selectie(pad: Path):
    """Haalt de JSON-array uit js/selectie.js (tussen eerste [ en laatste ])."""
    tekst = pad.read_text(encoding="utf-8")
    start = tekst.index("[")
    einde = tekst.rindex("]")
    return json.loads(tekst[start:einde + 1])


def controleer(selectie, boeken):
    fouten = []
    for i, p in enumerate(selectie):
        plek = f"regel {i + 1} ({p.get('boek')} {p.get('hoofdstuk')})"
        boek, hoofdstuk = p.get("boek"), p.get("hoofdstuk")
        if boek not in boeken:
            fouten.append(f"{plek}: onbekend boek '{boek}'")
            continue
        bestand = DATA / boek / f"{hoofdstuk}.json"
        if not bestand.exists():
            fouten.append(f"{plek}: hoofdstuk bestaat niet ({bestand})")
            continue
        aantal = len(json.loads(bestand.read_text(encoding="utf-8"))["verses"])
        bereik = p.get("verzen")
        if bereik:
            eerste, laatste = bereik
            if eerste < 1 or eerste > aantal:
                fouten.append(f"{plek}: eerste vers {eerste} buiten 1-{aantal}")
            if laatste > aantal:
                fouten.append(f"{plek}: laatste vers {laatste} > {aantal} verzen")
            if laatste < eerste:
                fouten.append(f"{plek}: versbereik loopt achteruit")
    return fouten


def main():
    pad = WERKMAP / "js" / "selectie.js"
    if not pad.exists():
        print(f"js/selectie.js niet gevonden ({pad})")
        return 1
    selectie = lees_selectie(pad)
    boeken = {b["id"] for b in json.loads((DATA / "books.json").read_text(encoding="utf-8"))["books"]}
    fouten = controleer(selectie, boeken)
    if fouten:
        print(f"{len(fouten)} fout(en) in {len(selectie)} passages:")
        print("\n".join(f"  - {f}" for f in fouten))
        return 1
    print(f"{len(selectie)} passages: alle boeken en hoofdstukken gevonden, versbereiken binnen bereik")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: Draai het script om te zien dat het faalt**

Run (vanuit `22 Evangelisatietraktaat/`): `python3 scripts/controleer_selectie.py`
Expected: FAIL — exit-code 1, uitvoer `js/selectie.js niet gevonden (…)`

- [ ] **Step 3: Genereer js/selectie.js**

Draai dit vanuit `22 Evangelisatietraktaat/`. Het schrijft één regel per passage:

```bash
python3 - <<'EOF'
from pathlib import Path

sel = []

def voeg_toe(boek, hoofdstukken, verzen=None, titel=None):
    for h in hoofdstukken:
        p = {"boek": boek, "hoofdstuk": h}
        if verzen:
            p["verzen"] = list(verzen)
        if titel:
            p["titel"] = titel
        sel.append(p)

# --- Oude Testament ---
voeg_toe("genesis", range(1, 26))
voeg_toe("exodus", [19, 20])
voeg_toe("deuteronomium", [28])
voeg_toe("richteren", range(13, 17))
voeg_toe("1samuel", [16, 17])
voeg_toe("1koningen", [8], (12, 66))
voeg_toe("1koningen", [9], (1, 12))
voeg_toe("job", [1, 2, 3, 38, 39, 40, 41, 42])
voeg_toe("psalmen", range(1, 26))
voeg_toe("psalmen", [119], (1, 40))
voeg_toe("psalmen", [122])
voeg_toe("spreuken", range(1, 10))
voeg_toe("spreuken", [30])
voeg_toe("prediker", [1, 2, 3])
voeg_toe("jesaja", [1, 2, 3, 4])
voeg_toe("jesaja", [5], (1, 24))
voeg_toe("jesaja", [44], (1, 8))
voeg_toe("jesaja", [52], (13, 15))
voeg_toe("jesaja", [53, 55, 64])
voeg_toe("jesaja", [65], (1, 5))
voeg_toe("jeremia", [1], (1, 10))
voeg_toe("klaagliederen", [3])
voeg_toe("ezechiel", [28])
voeg_toe("ezechiel", [36], (16, 33))
voeg_toe("daniel", [1, 6, 7, 9, 10])
voeg_toe("hosea", [14], (2, 3))
voeg_toe("jona", range(1, 5))
voeg_toe("gebedvanmanasse", [1], titel="Gebed van Manasse")
voeg_toe("habakuk", [1, 2])
voeg_toe("zacharia", [10, 14])
voeg_toe("maleachi", [3])

# --- Nieuwe Testament ---
voeg_toe("markus", range(1, 17))
voeg_toe("johannes", range(1, 22))
voeg_toe("handelingen", list(range(1, 6)) + list(range(8, 11)))
voeg_toe("romeinen", range(1, 17))
voeg_toe("1korinthiers", [12])
voeg_toe("galaten", [5])
voeg_toe("efeziers", [6])
voeg_toe("filippenzen", [3])
voeg_toe("kolossenzen", range(1, 5))
voeg_toe("jakobus", [1, 4])
voeg_toe("1johannes", [1, 2, 3])
voeg_toe("openbaring", [1, 2, 3, 4, 22])


def regel(p):
    delen = [f'"boek": "{p["boek"]}"', f'"hoofdstuk": {p["hoofdstuk"]}']
    if "verzen" in p:
        delen.append(f'"verzen": [{p["verzen"][0]}, {p["verzen"][1]}]')
    if "titel" in p:
        delen.append(f'"titel": "{p["titel"]}"')
    return "  {" + ", ".join(delen) + "}"


kop = (
    "/* De inhoud van het evangelisatietraktaat: een regel per passage.\n"
    " * Volgorde in deze lijst is de volgorde in het boekje.\n"
    " * Velden: boek (id uit data/books.json), hoofdstuk, verzen (optioneel,\n"
    " * inclusief begin en eind), titel (optioneel, overschrijft de kop).\n"
    " * Let op: de lijst zelf moet geldige JSON blijven (dubbele\n"
    " * aanhalingstekens, geen commentaar binnen de haken), omdat\n"
    " * scripts/controleer_selectie.py hem uitleest.\n"
    " */\n"
)
inhoud = kop + "window.TRAKTAAT_SELECTIE = [\n" + ",\n".join(regel(p) for p in sel) + "\n];\n"
Path("js").mkdir(exist_ok=True)
Path("js/selectie.js").write_text(inhoud, encoding="utf-8")
print(f"{len(sel)} passages geschreven naar js/selectie.js")
EOF
```

Expected: `194 passages geschreven naar js/selectie.js`

- [ ] **Step 4: Draai het controlescript opnieuw**

Run: `python3 scripts/controleer_selectie.py`
Expected: PASS — exit-code 0, uitvoer `194 passages: alle boeken en hoofdstukken gevonden, versbereiken binnen bereik`

- [ ] **Step 5: Controleer een handmatige steekproef**

Run:

```bash
python3 -c "
import json
t=open('js/selectie.js',encoding='utf-8').read()
s=json.loads(t[t.index('['):t.rindex(']')+1])
print(len(s))
print(s[0], s[25])
print([p for p in s if p['boek']=='1koningen'])
print([p for p in s if p['boek']=='gebedvanmanasse'])
print(s[-1])
"
```

Expected:
```
194
{'boek': 'genesis', 'hoofdstuk': 1} {'boek': 'exodus', 'hoofdstuk': 19}
[{'boek': '1koningen', 'hoofdstuk': 8, 'verzen': [12, 66]}, {'boek': '1koningen', 'hoofdstuk': 9, 'verzen': [1, 12]}]
[{'boek': 'gebedvanmanasse', 'hoofdstuk': 1, 'titel': 'Gebed van Manasse'}]
{'boek': 'openbaring', 'hoofdstuk': 22}
```

- [ ] **Step 6: Commit**

```bash
git add "22 Evangelisatietraktaat/js/selectie.js" "22 Evangelisatietraktaat/scripts/controleer_selectie.py"
git commit -m "feat(traktaat): selectie van 194 passages met controlescript"
```

---

### Task 2: Pure render-functies

**Files:**
- Create: `js/render.js`
- Test: `tests/render.test.mjs`

**Interfaces:**
- Consumes: passage-objecten uit Task 1; `config` met `DATA_BASE`, `IMG_BASE`, `LEES_BASE` (Task 4 maakt het echte bestand, de tests geven hun eigen object mee).
- Produces (alle exports van `js/render.js`):
  - `passageId(passage) -> string` — `"genesis_1"`
  - `passageTitel(passage, boekNaam) -> string` — `"Genesis 1"`, `"Jesaja 5:1-24"`, `"Gebed van Manasse"`
  - `dataUrl(config, passage) -> string`
  - `afbeeldingUrl(config, passage) -> string`
  - `leesUrl(config, passage) -> string`
  - `boekNamen(boeksJson) -> Record<string, string>` — id naar `nameDutch`
  - `escapeHtml(tekst) -> string`
  - `verzenHtml(verzen) -> string` — verzen zijn objecten `{number, text2026}`
  - `uitlegHtml(uitleg) -> string`
  - `spreadHtml({id, titel, leesHref, afbeelding, uitleg}) -> string` — skelet met lege tekstplek

- [ ] **Step 1: Schrijf de falende tests**

Maak `tests/render.test.mjs`:

```javascript
import test from 'node:test';
import assert from 'node:assert/strict';
import {
    passageId, passageTitel, dataUrl, afbeeldingUrl, leesUrl,
    boekNamen, escapeHtml, verzenHtml, uitlegHtml, spreadHtml,
} from '../js/render.js';

const config = {
    DATA_BASE: '../data/',
    IMG_BASE: '../images/chapters/',
    LEES_BASE: '../lees.html',
};

test('passageId koppelt boek en hoofdstuk', () => {
    assert.equal(passageId({ boek: 'genesis', hoofdstuk: 1 }), 'genesis_1');
    assert.equal(passageId({ boek: '1koningen', hoofdstuk: 8 }), '1koningen_8');
});

test('passageTitel zonder versbereik is boek en hoofdstuk', () => {
    assert.equal(passageTitel({ boek: 'genesis', hoofdstuk: 1 }, 'Genesis'), 'Genesis 1');
});

test('passageTitel met versbereik toont de verzen', () => {
    assert.equal(
        passageTitel({ boek: 'jesaja', hoofdstuk: 5, verzen: [1, 24] }, 'Jesaja'),
        'Jesaja 5:1-24',
    );
});

test('passageTitel gebruikt een eigen titel als die er is', () => {
    assert.equal(
        passageTitel({ boek: 'gebedvanmanasse', hoofdstuk: 1, titel: 'Gebed van Manasse' }, 'Gebed van Manasse'),
        'Gebed van Manasse',
    );
});

test('urls worden uit de config opgebouwd', () => {
    const p = { boek: 'genesis', hoofdstuk: 1 };
    assert.equal(dataUrl(config, p), '../data/genesis/1.json');
    assert.equal(afbeeldingUrl(config, p), '../images/chapters/genesis_1.jpg');
    assert.equal(leesUrl(config, p), '../lees.html#genesis/1');
});

test('boekNamen maakt een tabel van id naar Nederlandse naam', () => {
    const namen = boekNamen({ books: [
        { id: 'genesis', nameDutch: 'Genesis' },
        { id: '1koningen', nameDutch: '1 Koningen' },
    ] });
    assert.equal(namen['1koningen'], '1 Koningen');
});

test('escapeHtml maakt tekst veilig', () => {
    assert.equal(escapeHtml('<b>&amp;</b>'), '&lt;b&gt;&amp;amp;&lt;/b&gt;');
    assert.equal(escapeHtml('gewone tekst'), 'gewone tekst');
});

test('verzenHtml zet versnummer en tekst om', () => {
    const html = verzenHtml([
        { number: 1, text2026: 'In het begin schiep God de hemel en de aarde.' },
        { number: 2, text2026: 'De aarde nu was woest & leeg.' },
    ]);
    assert.match(html, /<span class="versnr">1<\/span>/);
    assert.match(html, /In het begin schiep God/);
    assert.match(html, /woest &amp; leeg/);
    assert.equal((html.match(/class="vers"/g) || []).length, 2);
});

test('uitlegHtml valt terug op "Uitleg volgt"', () => {
    assert.match(uitlegHtml(''), /Uitleg volgt/);
    assert.match(uitlegHtml(undefined), /Uitleg volgt/);
    assert.match(uitlegHtml('God is de Maker'), /God is de Maker/);
    assert.doesNotMatch(uitlegHtml('God is de Maker'), /Uitleg volgt/);
});

test('spreadHtml bevat kop, link, afbeelding en een lege tekstplek', () => {
    const html = spreadHtml({
        id: 'genesis_1',
        titel: 'Genesis 1',
        leesHref: '../lees.html#genesis/1',
        afbeelding: '../images/chapters/genesis_1.jpg',
        uitleg: '',
    });
    assert.match(html, /id="genesis_1"/);
    assert.match(html, /href="\.\.\/lees\.html#genesis\/1"/);
    assert.match(html, /Genesis 1/);
    assert.match(html, /src="\.\.\/images\/chapters\/genesis_1\.jpg"/);
    assert.match(html, /data-tekst="genesis_1"/);
    assert.match(html, /Uitleg volgt/);
});
```

- [ ] **Step 2: Draai de tests om te zien dat ze falen**

Run (vanuit `22 Evangelisatietraktaat/`): `node --test tests/render.test.mjs`
Expected: FAIL — `Cannot find module …/js/render.js`

- [ ] **Step 3: Schrijf js/render.js**

```javascript
/* Pure functies voor het traktaat: gegevens in, string uit.
 * Geen DOM, geen fetch — daardoor testbaar met `node --test`.
 */

export function passageId(passage) {
    return `${passage.boek}_${passage.hoofdstuk}`;
}

export function passageTitel(passage, boekNaam) {
    if (passage.titel) return passage.titel;
    const kop = `${boekNaam} ${passage.hoofdstuk}`;
    if (!passage.verzen) return kop;
    return `${kop}:${passage.verzen[0]}-${passage.verzen[1]}`;
}

export function dataUrl(config, passage) {
    return `${config.DATA_BASE}${passage.boek}/${passage.hoofdstuk}.json`;
}

export function afbeeldingUrl(config, passage) {
    return `${config.IMG_BASE}${passageId(passage)}.jpg`;
}

export function leesUrl(config, passage) {
    return `${config.LEES_BASE}#${passage.boek}/${passage.hoofdstuk}`;
}

export function boekNamen(boeksJson) {
    const namen = {};
    (boeksJson.books || []).forEach(b => { namen[b.id] = b.nameDutch; });
    return namen;
}

export function escapeHtml(tekst) {
    return String(tekst ?? '')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}

export function verzenHtml(verzen) {
    return verzen.map(v =>
        `<p class="vers"><span class="versnr">${v.number}</span> ${escapeHtml(v.text2026)}</p>`
    ).join('\n');
}

export function uitlegHtml(uitleg) {
    if (!uitleg) return '<p class="uitleg leeg">Uitleg volgt</p>';
    return `<p class="uitleg">${escapeHtml(uitleg)}</p>`;
}

export function spreadHtml({ id, titel, leesHref, afbeelding, uitleg }) {
    return `<section class="spread" id="${id}">
  <div class="pagina tekst">
    <h2><a href="${leesHref}">${escapeHtml(titel)}</a></h2>
    <div class="verzen" data-tekst="${id}"><p class="laden">Laden…</p></div>
  </div>
  <div class="pagina beeld">
    <figure class="illustratie">
      <img src="${afbeelding}" alt="${escapeHtml(titel)}" loading="lazy">
      <figcaption>${escapeHtml(titel)}</figcaption>
    </figure>
    ${uitlegHtml(uitleg)}
  </div>
</section>`;
}
```

- [ ] **Step 4: Draai de tests tot ze slagen**

Run: `node --test tests/render.test.mjs`
Expected: PASS — alle 10 tests slagen

- [ ] **Step 5: Commit**

```bash
git add "22 Evangelisatietraktaat/js/render.js" "22 Evangelisatietraktaat/tests/render.test.mjs"
git commit -m "feat(traktaat): pure render-functies met tests"
```

---

### Task 3: Laadlaag

**Files:**
- Create: `js/laden.js`
- Test: `tests/laden.test.mjs`

**Interfaces:**
- Consumes: `dataUrl` uit `js/render.js` (Task 2).
- Produces (exports van `js/laden.js`):
  - `verzenInBereik(verzen, bereik) -> Array` — `bereik` is `[eerste, laatste]` of `undefined`
  - `async laadPassage(fetchFn, config, passage) -> {ok: true, verzen: Array} | {ok: false, fout: string}`

De `fetchFn` wordt meegegeven in plaats van de globale `fetch` te gebruiken, zodat de tests hem kunnen vervangen.

- [ ] **Step 1: Schrijf de falende tests**

Maak `tests/laden.test.mjs`:

```javascript
import test from 'node:test';
import assert from 'node:assert/strict';
import { verzenInBereik, laadPassage } from '../js/laden.js';

const config = { DATA_BASE: '../data/' };

const hoofdstuk = {
    number: 1,
    verses: [
        { number: 1, text2026: 'een' },
        { number: 2, text2026: 'twee' },
        { number: 3, text2026: 'drie' },
    ],
};

function nepFetch(antwoord) {
    return async () => antwoord;
}

test('verzenInBereik zonder bereik geeft alle verzen', () => {
    assert.equal(verzenInBereik(hoofdstuk.verses, undefined).length, 3);
});

test('verzenInBereik filtert inclusief begin en eind', () => {
    const uit = verzenInBereik(hoofdstuk.verses, [2, 3]);
    assert.deepEqual(uit.map(v => v.number), [2, 3]);
});

test('laadPassage geeft de gefilterde verzen bij een goed antwoord', async () => {
    const fetchFn = nepFetch({ ok: true, json: async () => hoofdstuk });
    const uit = await laadPassage(fetchFn, config, { boek: 'genesis', hoofdstuk: 1, verzen: [2, 2] });
    assert.equal(uit.ok, true);
    assert.deepEqual(uit.verzen.map(v => v.number), [2]);
});

test('laadPassage vraagt de juiste url op', async () => {
    let gevraagd = null;
    const fetchFn = async (url) => { gevraagd = url; return { ok: true, json: async () => hoofdstuk }; };
    await laadPassage(fetchFn, config, { boek: 'jona', hoofdstuk: 2 });
    assert.equal(gevraagd, '../data/jona/2.json');
});

test('laadPassage meldt een http-fout', async () => {
    const fetchFn = nepFetch({ ok: false, status: 404 });
    const uit = await laadPassage(fetchFn, config, { boek: 'genesis', hoofdstuk: 1 });
    assert.equal(uit.ok, false);
    assert.match(uit.fout, /404/);
});

test('laadPassage meldt een netwerkfout', async () => {
    const fetchFn = async () => { throw new Error('offline'); };
    const uit = await laadPassage(fetchFn, config, { boek: 'genesis', hoofdstuk: 1 });
    assert.equal(uit.ok, false);
    assert.match(uit.fout, /offline/);
});
```

- [ ] **Step 2: Draai de tests om te zien dat ze falen**

Run: `node --test tests/laden.test.mjs`
Expected: FAIL — `Cannot find module …/js/laden.js`

- [ ] **Step 3: Schrijf js/laden.js**

```javascript
/* Het ophalen van een hoofdstuk uit de OSV-data.
 * fetchFn wordt meegegeven zodat deze laag testbaar is zonder netwerk.
 */
import { dataUrl } from './render.js';

export function verzenInBereik(verzen, bereik) {
    if (!bereik) return verzen;
    const [eerste, laatste] = bereik;
    return verzen.filter(v => v.number >= eerste && v.number <= laatste);
}

export async function laadPassage(fetchFn, config, passage) {
    const url = dataUrl(config, passage);
    try {
        const antwoord = await fetchFn(url);
        if (!antwoord.ok) {
            return { ok: false, fout: `Ophalen mislukt (${antwoord.status})` };
        }
        const hoofdstuk = await antwoord.json();
        return { ok: true, verzen: verzenInBereik(hoofdstuk.verses, passage.verzen) };
    } catch (e) {
        return { ok: false, fout: `Ophalen mislukt: ${e.message}` };
    }
}
```

- [ ] **Step 4: Draai de tests tot ze slagen**

Run: `node --test tests/laden.test.mjs`
Expected: PASS — alle 6 tests slagen

- [ ] **Step 5: Draai alle tests samen**

Run: `node --test tests/`
Expected: PASS — 16 tests

- [ ] **Step 6: Commit**

```bash
git add "22 Evangelisatietraktaat/js/laden.js" "22 Evangelisatietraktaat/tests/laden.test.mjs"
git commit -m "feat(traktaat): laadlaag voor hoofdstukken met tests"
```

---

### Task 4: Pagina met inhoudsopgave en spread-skeletten

**Files:**
- Create: `js/config.js`
- Create: `index.html`
- Create: `css/traktaat.css`
- Create: `js/traktaat.js`
- Create: `data/uitleg.json`

**Interfaces:**
- Consumes: `window.TRAKTAAT_SELECTIE` (Task 1), alle exports van `js/render.js` (Task 2).
- Produces: `window.TRAKTAAT_CONFIG = {DATA_BASE, IMG_BASE, LEES_BASE}`; een DOM met `#inhoudsopgave` (lijst met links) en `#boekje` (de spreads). Task 5 hangt de lazy loading aan `[data-tekst]` op.

- [ ] **Step 1: Maak js/config.js**

```javascript
/* Waar het traktaat zijn gegevens vandaan haalt.
 * Nu relatief aan de OSV-repo. Wordt het traktaat een losse website, dan
 * worden dit absolute url's: 'https://openvertaling.nl/data/' enzovoort.
 */
window.TRAKTAAT_CONFIG = {
    DATA_BASE: '../data/',
    IMG_BASE: '../images/chapters/',
    LEES_BASE: '../lees.html',
};
```

- [ ] **Step 2: Maak data/uitleg.json**

```json
{}
```

- [ ] **Step 3: Maak index.html**

```html
<!DOCTYPE html>
<html lang="nl">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Evangelisatietraktaat — Open Staten Vertaling</title>
    <link rel="stylesheet" href="css/traktaat.css">
</head>
<body>
    <aside id="zijbalk">
        <h1>Traktaat</h1>
        <nav id="inhoudsopgave" aria-label="Inhoudsopgave"></nav>
    </aside>
    <main id="boekje"></main>

    <script src="js/config.js"></script>
    <script src="js/selectie.js"></script>
    <script type="module" src="js/traktaat.js"></script>
</body>
</html>
```

- [ ] **Step 4: Maak css/traktaat.css**

```css
/* Sobere basisopmaak: alleen wat de structuur nodig heeft.
 * De verdere vormgeving wordt hier handmatig uitgewerkt.
 */
* { box-sizing: border-box; }

body {
    margin: 0;
    display: flex;
    font-family: Georgia, 'Times New Roman', serif;
    color: #2b2b2b;
    background: #f6f3ec;
}

#zijbalk {
    width: 16rem;
    flex: 0 0 16rem;
    height: 100vh;
    overflow-y: auto;
    padding: 1.5rem 1rem;
    background: #efe9dc;
    border-right: 1px solid #ddd4c0;
}

#zijbalk h1 { font-size: 1.2rem; margin: 0 0 1rem; }

#inhoudsopgave a {
    display: block;
    padding: 0.15rem 0;
    font-size: 0.9rem;
    color: #4a3f2f;
    text-decoration: none;
}

#inhoudsopgave a:hover { text-decoration: underline; }

#boekje { flex: 1; padding: 2rem; max-width: 78rem; }

.spread {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 2.5rem;
    padding: 2rem 0 3rem;
    border-bottom: 1px solid #e2dac6;
    align-items: start;
}

.pagina.tekst { max-width: 34rem; }

.pagina.beeld {
    position: sticky;
    top: 2rem;
}

.spread h2 { font-size: 1.4rem; margin: 0 0 1rem; }
.spread h2 a { color: inherit; text-decoration: none; border-bottom: 1px dotted #b5a88c; }
.spread h2 a:hover { border-bottom-style: solid; }

.vers { margin: 0 0 0.6rem; line-height: 1.6; }
.versnr { font-size: 0.75rem; vertical-align: super; color: #8a7a5e; margin-right: 0.15rem; }

.laden, .fout { color: #8a7a5e; font-style: italic; }
.fout button { margin-left: 0.5rem; font: inherit; cursor: pointer; }

.illustratie { margin: 0 0 1rem; }
.illustratie img { width: 100%; aspect-ratio: 4 / 3; object-fit: cover; display: block; background: #e6dfcd; }
.illustratie figcaption { font-size: 0.8rem; color: #8a7a5e; padding-top: 0.3rem; }
.illustratie.ontbreekt img { display: none; }
.illustratie.ontbreekt {
    aspect-ratio: 4 / 3;
    border: 1px dashed #c9bfa5;
    display: flex;
    align-items: center;
    justify-content: center;
}

.uitleg { line-height: 1.6; }
.uitleg.leeg { color: #a2957a; font-style: italic; }

@media (max-width: 60rem) {
    body { display: block; }
    #zijbalk { width: auto; height: auto; border-right: none; border-bottom: 1px solid #ddd4c0; }
    .spread { grid-template-columns: 1fr; }
    .pagina.beeld { position: static; }
}
```

- [ ] **Step 5: Maak js/traktaat.js met inhoudsopgave en skeletten**

```javascript
/* Bouwt het boekje op: inhoudsopgave en een spread per passage.
 * De tekst zelf wordt in een volgende stap ingeladen.
 */
import {
    passageId, passageTitel, afbeeldingUrl, leesUrl, boekNamen, escapeHtml, spreadHtml,
} from './render.js';

const config = window.TRAKTAAT_CONFIG;
const selectie = window.TRAKTAAT_SELECTIE || [];

async function haalJson(url, terugval) {
    try {
        const antwoord = await fetch(url);
        if (!antwoord.ok) return terugval;
        return await antwoord.json();
    } catch (e) {
        return terugval;
    }
}

function bouwInhoudsopgave(namen) {
    document.getElementById('inhoudsopgave').innerHTML = selectie.map(p =>
        `<a href="#${passageId(p)}">${escapeHtml(passageTitel(p, namen[p.boek] || p.boek))}</a>`
    ).join('');
}

function bouwSpreads(namen, uitleg) {
    document.getElementById('boekje').innerHTML = selectie.map(p => spreadHtml({
        id: passageId(p),
        titel: passageTitel(p, namen[p.boek] || p.boek),
        leesHref: leesUrl(config, p),
        afbeelding: afbeeldingUrl(config, p),
        uitleg: uitleg[passageId(p)],
    })).join('\n');
}

async function start() {
    const [boeken, uitleg] = await Promise.all([
        haalJson(`${config.DATA_BASE}books.json`, { books: [] }),
        haalJson('data/uitleg.json', {}),
    ]);
    const namen = boekNamen(boeken);
    bouwInhoudsopgave(namen);
    bouwSpreads(namen, uitleg);
}

start();
```

- [ ] **Step 6: Controleer dat de pagina geserveerd wordt**

Run (vanuit `22 Evangelisatietraktaat/`):

```bash
python3 -m http.server 8123 &
sleep 1
curl -s -o /dev/null -w "%{http_code} index.html\n" http://localhost:8123/index.html
curl -s -o /dev/null -w "%{http_code} traktaat.js\n" http://localhost:8123/js/traktaat.js
curl -s -o /dev/null -w "%{http_code} selectie.js\n" http://localhost:8123/js/selectie.js
curl -s -o /dev/null -w "%{http_code} uitleg.json\n" http://localhost:8123/data/uitleg.json
curl -s -o /dev/null -w "%{http_code} books.json\n" http://localhost:8123/../data/books.json
kill %1
```

Expected: `200` voor index.html, js/traktaat.js, js/selectie.js en data/uitleg.json. De laatste regel (books.json via `..`) mag `404` geven — `http.server` weigert paden buiten de serveermap; dat is een beperking van deze controle, niet van de pagina. Serveer vanuit de repo-root (`python3 -m http.server 8123` een niveau hoger, dan `http://localhost:8123/22%20Evangelisatietraktaat/`) om ook `../data/` te kunnen bereiken.

- [ ] **Step 7: Commit**

```bash
git add "22 Evangelisatietraktaat/index.html" "22 Evangelisatietraktaat/css/traktaat.css" "22 Evangelisatietraktaat/js/config.js" "22 Evangelisatietraktaat/js/traktaat.js" "22 Evangelisatietraktaat/data/uitleg.json"
git commit -m "feat(traktaat): pagina met inhoudsopgave en spread-skeletten"
```

---

### Task 5: Tekst laden bij het scrollen, met fouten en afbeeldings-terugval

**Files:**
- Modify: `js/traktaat.js`

**Interfaces:**
- Consumes: `laadPassage` uit `js/laden.js` (Task 3), `verzenHtml` uit `js/render.js` (Task 2), de DOM uit Task 4.
- Produces: het afgeronde boekje. Geen nieuwe exports.

- [ ] **Step 1: Breid js/traktaat.js uit**

Vervang de import-regel bovenaan door:

```javascript
import {
    passageId, passageTitel, afbeeldingUrl, leesUrl, boekNamen, escapeHtml,
    spreadHtml, verzenHtml,
} from './render.js';
import { laadPassage } from './laden.js';
```

Voeg vóór `async function start()` toe:

```javascript
/* Laadt één passage en zet de verzen in zijn spread. */
async function vulTekst(passage, plek) {
    plek.innerHTML = '<p class="laden">Laden…</p>';
    // fetch als pijlfunctie doorgeven: los meegegeven raakt hij zijn binding
    // aan window kwijt en gooit de browser "Illegal invocation".
    const uit = await laadPassage(url => fetch(url), config, passage);
    if (uit.ok) {
        plek.innerHTML = verzenHtml(uit.verzen);
        return;
    }
    plek.innerHTML = `<p class="fout">${escapeHtml(uit.fout)}<button type="button">Opnieuw proberen</button></p>`;
    plek.querySelector('button').addEventListener('click', () => vulTekst(passage, plek));
}

/* Laat elke spread zijn tekst ophalen zodra hij in beeld komt. */
function bewaakSpreads() {
    const perId = {};
    selectie.forEach(p => { perId[passageId(p)] = p; });

    const kijker = new IntersectionObserver((waarnemingen) => {
        waarnemingen.forEach(w => {
            if (!w.isIntersecting) return;
            kijker.unobserve(w.target);
            vulTekst(perId[w.target.dataset.tekst], w.target);
        });
    }, { rootMargin: '600px 0px' });

    document.querySelectorAll('[data-tekst]').forEach(el => kijker.observe(el));
}

/* Toont een kader in plaats van een gebroken afbeelding. */
function bewaakAfbeeldingen() {
    document.querySelectorAll('.illustratie img').forEach(img => {
        img.addEventListener('error', () => {
            img.closest('.illustratie').classList.add('ontbreekt');
        });
    });
}
```

Vervang het einde van `start()` (`bouwSpreads(namen, uitleg);`) door:

```javascript
    bouwSpreads(namen, uitleg);
    bewaakAfbeeldingen();
    bewaakSpreads();
```

- [ ] **Step 2: Draai alle geautomatiseerde controles**

Run (vanuit `22 Evangelisatietraktaat/`):

```bash
node --test tests/
python3 scripts/controleer_selectie.py
node --check js/traktaat.js 2>&1 || echo "node --check begrijpt ES modules met import niet; negeer deze regel"
```

Expected: 16 tests slagen; het controlescript meldt 194 geldige passages.

- [ ] **Step 3: Controleer de opbouw zonder browser**

Run:

```bash
python3 - <<'EOF'
import json, re, pathlib
t = pathlib.Path('js/traktaat.js').read_text(encoding='utf-8')
for naam in ['vulTekst', 'bewaakSpreads', 'bewaakAfbeeldingen', 'IntersectionObserver',
             'Opnieuw proberen', 'laadPassage', 'verzenHtml']:
    assert naam in t, f'ontbreekt: {naam}'
assert t.count('bewaakSpreads()') >= 1 and t.count('bewaakAfbeeldingen()') >= 1
print('traktaat.js bevat alle onderdelen')
EOF
```

Expected: `traktaat.js bevat alle onderdelen`

- [ ] **Step 4: Commit**

```bash
git add "22 Evangelisatietraktaat/js/traktaat.js"
git commit -m "feat(traktaat): tekst laden bij scrollen, met foutherstel en terugval"
```

---

## Handmatige eindcontrole (door de mens, in de browser)

Deze stappen vragen een echte browser en horen bij de oplevering, niet bij een taak:

1. Serveer de repo-root: `python3 -m http.server 8123` en open
   `http://localhost:8123/22%20Evangelisatietraktaat/`.
2. De zijbalk toont 194 links, van "Genesis 1" tot "Openbaring 22"; "1 Koningen 8:12-66",
   "Jesaja 5:1-24" en "Gebed van Manasse" staan er correct in.
3. De eerste spread toont Genesis 1 vers 1-31 met versnummers.
4. Op het tabblad Netwerk verschijnen bij het openen slechts enkele hoofdstuk-verzoeken,
   niet 194; scrollen levert nieuwe verzoeken op.
5. Klik op "1 Koningen 8:12-66", "Hosea 14:2-3", "Jesaja 52:13-15" en "Psalmen 119:1-40":
   de versbereiken kloppen precies.
6. Zet `DATA_BASE` tijdelijk op `'../bestaat-niet/'`: elke spread toont "Ophalen mislukt (404)"
   met een werkende knop "Opnieuw proberen". Zet de waarde daarna terug.
7. Zet tijdelijk `{"genesis_1": "God is de Maker van hemel en aarde."}` in `data/uitleg.json`:
   bij Genesis 1 staat die zin, elders staat nog "Uitleg volgt". Zet daarna terug op `{}`.

## Na afloop

Het boekje staat er dan volledig in, met lege afbeeldingskaders en "Uitleg volgt". Vervolgstappen, buiten dit plan:

- Afbeeldingen genereren op basis van `data/chapter-image-prompts.json` en wegschrijven als `images/chapters/{boek}_{hoofdstuk}.jpg`.
- De uitleg per passage schrijven in `data/uitleg.json`.
- De vormgeving uitwerken in `css/traktaat.css`.
- Het traktaat als losse website deployen: de drie waarden in `js/config.js` op absolute url's zetten.
