# Opdracht voor de TTS-sessie — chunk-audio genereren

**Datum:** 2026-07-16
**Voor:** de parallelle TTS/GPU-sessie (RTX 5070, `scripts/tts/`, `.venv-xtts`)
**Ontwerp:** `docs/superpowers/specs/2026-07-15-chunked-audio-design.md` — lees dit eerst.

## Context

De voorlees-audio wordt herbouwd naar **losse segmenten (chunks)** zodat bij het voorlezen
optioneel zijn: de **Godsnaam** (HEERE / JAHWEH / Jehova), de **kopjes** (pericopen) en een
**boeknaam+hoofdstuk-intro**. De consumentkant is al klaar en getest:

- `js/chunked-audio.js` — speler die een hoofdstuk uit chunks afspeelt volgens een `manifest.json`.
  Valt terug op de losse-MP3-speler als er geen manifest is (dus niets breekt tijdens uitrol).
- Leesweergave (`js/lees.js`) is gewired + heeft een instellingen-UI (godsnaam/kopjes/intro).
- `scripts/audio_staleness.py` — meldt welke hoofdstukken verouderd zijn (nu 680/686).

**Jouw taak: de audio-chunks + manifests genereren op de GPU.** Raak de spelercode niet aan.

## Wat je oplevert, per (boek, hoofdstuk, stem m/v)

Map: `audio/<book>/<ch>/<voice>/`

```
intro.mp3                 # "Het boek <Boeknaam>, hoofdstuk <N>"
h<afterVerse>.mp3         # elk kopje, genoemd naar het vers waar het vóór staat (h1, h7, ...)
v<N>.mp3                  # vers N (geen Godsnaam)
v<N>__heere.mp3           # vers N mét Godsnaam, uitgesproken als "Heere"
v<N>__jahweh.mp3          # idem, "Jahweh"
v<N>__jehova.mp3          # idem, "Jehova"
manifest.json
```

- Verzen **zonder** Godsnaam: alleen `v<N>.mp3` (geen varianten → geen extra opslag).
- Verzen **met** Godsnaam: de drie `__heere/__jahweh/__jehova`-varianten (laat `v<N>.mp3` weg).

## Manifest-schema (exact)

```json
{
  "book": "genesis", "chapter": 2, "voice": "m",
  "model": "<gebruikte model + versie>",
  "generatedAt": "<ISO-8601>",
  "textHash": "<zie hieronder — MOET matchen met audio_staleness.py>",
  "segments": [
    { "type": "intro", "file": "intro.mp3", "dur": 2.1 },
    { "type": "heading", "afterVerse": 1, "file": "h1.mp3", "dur": 1.8, "text": "<kopje-titel>" },
    { "type": "verse", "verse": 1, "file": "v1.mp3", "dur": 6.4, "divineName": false },
    { "type": "verse", "verse": 4, "divineName": true,
      "variants": { "heere": "v4__heere.mp3", "jahweh": "v4__jahweh.mp3", "jehova": "v4__jehova.mp3" },
      "dur": { "heere": 7.0, "jahweh": 7.2, "jehova": 7.1 } }
  ]
}
```

- `dur` = werkelijke duur (sec) uit de gegenereerde audio; gebruikt voor de tijdsbalk.
- `segments` staat in afspeelvolgorde: intro, dan per vers (kopje ervoor als aanwezig).

## `textHash` — MOET identiek zijn aan de verouderingscheck

De speler/tool bepaalt veroudering op `textHash`. Bereken hem **precies** zoals
`scripts/audio_staleness.py::text_hash()`:

1. Neem uit `data/<book>/<ch>.json` van elk vers `text2026`, `.strip()`, laat lege weg.
2. Voeg de kopje-titels toe (uit `data/pericopen.json`, indien aanwezig voor dat hoofdstuk).
3. `sha1( "\n".join(parts) )` (UTF-8), hexdigest.

Zo weet de tool na een tekstwijziging automatisch dat het hoofdstuk opnieuw moet.
Draai daarna `python3 scripts/audio_staleness.py` om te controleren dat het hoofdstuk niet
meer als verouderd verschijnt.

## Godsnaam-varianten — welke verzen en hoe

- **Welke verzen:** verzen waarin de Godsnaam voorkomt. In de OSV-tekst is dat "HEERE" of
  "HEERE HEERE" (kleinkapitaal). Detecteer op het woord **HEERE** (en "HEERE HEERE") in
  `text2026`. (De brontekst-JHWH is de achterliggende reden.)
- **Synthese:** genereer per variant met een aangepaste uitspraak vóór de synthese:
  - `heere` → "Heere" (huidige uitspraak).
  - `jahweh` → "Jahweh".
  - `jehova` → "Jehova".
  Gebruik `scripts/tts/pronunciation_lexicon.json` voor de juiste klemtoon/uitspraak.
  Bij "HEERE HEERE" beide voorkomens vervangen.
- Verzen zonder HEERE: gewoon één `v<N>.mp3`.

## Kopjes (pericopen)

- Bron: `data/pericopen.json` (kop-titels per boek/hoofdstuk/vers). Genereer per kopje een
  `h<afterVerse>.mp3` waarbij `<afterVerse>` het versnummer is waar het kopje vóór staat.
- Neem de kopjes in het manifest op met hun `text`.

## Boeknaam + hoofdstuk-intro

- `intro.mp3`: "Het boek <Boeknaam>, hoofdstuk <N>" (boeknaam uit `data/books.json` → `nameDutch`).
  Dit vervangt/uitbreidt de huidige `announce_chapters.py` (die nu alleen "Hoofdstuk N" zegt).

## Aanpak (gefaseerd)

1. **Pilot: één hoofdstuk met Godsnaam** — bv. **Genesis 2** ("HEERE God"). Genereer alle chunks
   + manifest voor stem `m`. Controleer in de speler: open `lees.html#genesis/2`, klik het
   tandwiel, wissel HEERE→JAHWEH→Jehova, zet kopjes aan/uit, en luister of de segmenten kloppen.
2. **Beide stemmen** (m + v) voor de pilot.
3. **Uitrol** hoofdstuk voor hoofdstuk. Omdat de speler terugvalt op losse MP3 waar geen manifest
   is, kan dit zonder de site te breken.
4. **Hele Bijbel** opnieuw met het nieuwste model; `audio_staleness.py` geeft de werklijst.

## Randvoorwaarden

- **Raak de spelercode niet aan** (`js/chunked-audio.js`, `js/lees.js`, `js/app.js`).
- **Update `js/audio-available.js`** (`window.AUDIO_AVAILABLE`) na de rollout — dat blijft jouw
  bestand (zie `CLAUDE.md`).
- Gebruik het nieuwste/beste stemmodel. Idempotent per hoofdstuk op basis van `textHash`.
- De timing-JSON's (`data/audio-timing/`) voor mee-lezen mogen per segment of per vers; niet
  strikt nodig voor de eerste uitrol.

## Klaar-criterium pilot

`lees.html#genesis/2` speelt via chunks; godsnaam/kopjes/intro schakelen hoorbaar; en
`python3 scripts/audio_staleness.py` toont Genesis 2 niet meer als verouderd.
