# Open Vertaling — Chunked audio (optionele godsnaam & kopjes)

**Datum:** 2026-07-15
**Status:** ontwerp
**Vervolg op:** `2026-05-06-tts-bijbel-design.md` (eerste TTS-opzet, één MP3 per hoofdstuk)

## Aanleiding (wens van de gebruiker)

1. **Verouderingscheck** — vergelijk de datum waarop de *tekst* van een hoofdstuk voor
   het laatst is gewijzigd met de datum van het *audiobestand*. Verschillen ze, dan is
   de audio verouderd en moet dat hoofdstuk opnieuw gegenereerd worden.
2. **Optionele godsnaam** — de lezer moet kunnen kiezen of de Godsnaam als
   **HEERE**, **JAHWEH** of **Jehova** wordt voorgelezen.
3. **Optionele kopjes (pericopen)** — als de lezer de kopjes aanzet, worden ze
   voorgelezen; anders niet.
4. **Boeknaam + hoofdstuknummer** aan het begin van elk hoofdstuk (nu wordt alleen
   "Hoofdstuk N" aangekondigd, zonder boeknaam).
5. **Hele Bijbel opnieuw** genereren met de nieuwste AI-stem; herhaalbaar.

Punten 2–4 kunnen niet met één MP3 per hoofdstuk: dan zou elke combinatie van
instellingen een apart volledig bestand vragen (3 godsnamen × wel/geen kopjes × 2
stemmen = 12 versies per hoofdstuk). Daarom: **losse audio-segmenten (chunks)** die de
speler in de browser aaneenrijgt op basis van de instellingen.

## Huidige architectuur (ter herinnering)

- Eén MP3 per hoofdstuk per stem: `audio/<book>/<ch>-<m|v>.mp3` (m = man, v = vrouw).
- `window.OV_AUDIO` (in `js/audio-available.js`): `.src(bookId, ch)`, `.getVoice()`, `.label()`.
- Beschikbaarheid: `window.AUDIO_AVAILABLE` in `js/audio-available.js`.
- Mee-lezen: per-woord timing in `data/audio-timing/<book>/<ch>-<m|v>.json`.
- Aankondiging: `audio/_announce/<voice>/<ch>.mp3` ("Hoofdstuk N"), met
  `App._announceThenPlay()` in `js/app.js`; browser-spraak als fallback.

## Nieuwe architectuur: chunks + manifest

### Segmenttypes per hoofdstuk

| Type | Inhoud | Altijd afgespeeld? |
|---|---|---|
| `intro` | "Het boek <Boeknaam>, hoofdstuk <N>" | optioneel (aan/uit), standaard aan |
| `heading` | een kopje (pericoop-titel) | alleen als kopjes aan staan |
| `verse` | de tekst van één vers (`text2026`) | ja |
| `verse` + godsnaam-variant | idem, maar met HEERE / JAHWEH / Jehova | ja (gekozen variant) |

### Bestandsindeling

```
audio/<book>/<ch>/<voice>/
    intro.mp3                 # "Het boek X, hoofdstuk N"
    h<afterVerse>.mp3         # kopje dat vóór vers <afterVerse> hoort (bv. h1, h7)
    v<N>.mp3                  # vers N, neutrale versie (geen godsnaam, of default HEERE)
    v<N>__heere.mp3           # vers N met "HEERE"    (alleen als vers de Godsnaam bevat)
    v<N>__jahweh.mp3          # vers N met "JAHWEH"
    v<N>__jehova.mp3          # vers N met "Jehova"
    manifest.json
```

- `<voice>` = `m` of `v`.
- Verzen zónder Godsnaam hebben alléén `v<N>.mp3` (geen varianten → geen extra opslag).
- Verzen mét Godsnaam hebben `v<N>__heere.mp3`, `__jahweh.mp3`, `__jehova.mp3`
  (de neutrale `v<N>.mp3` mag dan ontbreken of gelijk zijn aan `__heere`).

### Manifest-schema (`audio/<book>/<ch>/<voice>/manifest.json`)

```json
{
  "book": "genesis",
  "chapter": 1,
  "voice": "m",
  "model": "xtts-v2",
  "generatedAt": "2026-07-15T12:00:00Z",
  "textHash": "<sha1 van de gebruikte text2026 + kopjes>",
  "segments": [
    { "type": "intro", "file": "intro.mp3", "dur": 2.1 },
    { "type": "heading", "afterVerse": 1, "file": "h1.mp3", "dur": 1.8, "text": "De schepping" },
    { "type": "verse", "verse": 1, "file": "v1.mp3", "dur": 6.4,
      "divineName": false },
    { "type": "verse", "verse": 2, "file": "v2.mp3", "dur": 5.1, "divineName": false },
    { "type": "verse", "verse": 5, "divineName": true,
      "variants": { "heere": "v5__heere.mp3", "jahweh": "v5__jahweh.mp3", "jehova": "v5__jehova.mp3" },
      "dur": { "heere": 7.0, "jahweh": 7.2, "jehova": 7.1 } }
  ]
}
```

- `textHash` maakt de **verouderingscheck** triviaal: her-hash de huidige tekst; als hij
  afwijkt van `manifest.textHash`, is de audio verouderd.
- `dur` per segment laat de speler een scrubber/tijdsbalk tonen zonder alles vooraf te laden.

## Speler-gedrag (js/lees.js + js/app.js)

De speler wordt een **segment-sequencer** rond één `<audio>`-element:

1. Laad `manifest.json` voor `(book, ch, voice)`. Geen manifest → **val terug op de
   huidige losse-MP3-speler** (`audio/<book>/<ch>-<voice>.mp3`). Volledige achterwaartse
   compatibiliteit.
2. Bouw de **afspeellijst** uit `segments`, gefilterd op instellingen:
   - `intro` alleen als "boekaankondiging" aan staat.
   - `heading` alleen als "kopjes voorlezen" aan staat.
   - `verse`: kies bij `divineName:true` het bestand `variants[gekozenGodsnaam]`.
3. Speel segmenten op volgorde: bij `ended` van segment *i* → laad en `play()` segment *i+1*.
4. Mee-lezen/markeren: per `verse`-segment het bijbehorende vers highlighten; timing-JSON
   wordt per segment (of per vers) geladen zoals nu.
5. Scrubber/tijd: som van `dur` van de actieve afspeellijst; huidige tijd = som van
   afgespeelde segmenten + `audioEl.currentTime`.

### Instellingen (UI)

Nieuwe voorleesopties (opslaan in `localStorage`, net als thema/kolommen):

- **Godsnaam bij voorlezen**: `HEERE` (standaard) · `JAHWEH` · `Jehova`.
- **Kopjes voorlezen**: aan/uit (standaard uit).
- **Boeknaam aankondigen**: aan/uit (standaard aan).

Wijzigen tijdens het afspelen herbouwt de afspeellijst vanaf het huidige vers.

## Generatie-eisen (voor de TTS-sessie, GPU)

Dit deel draait op de GPU via `scripts/tts/` en is het terrein van de TTS-sessie. Deze
sessie levert alleen het ontwerp + de niet-GPU tooling. Wat de generatie moet doen:

1. **Per vers een chunk** genereren i.p.v. per hoofdstuk (`v<N>.mp3`).
2. **Godsnaam-detectie**: verzen waarin de Godsnaam voorkomt (in de OSV weergegeven als
   "HEERE"/"HEERE HEERE"; brontekst-JHWH) krijgen drie varianten. Gebruik een aparte
   tekstsubstitutie per variant vóór de synthese (HEERE → "Heere" / "Jahweh" / "Jehova"
   met de juiste uitspraak in `pronunciation_lexicon.json`).
3. **Kopjes**: uit `data/pericopen.json` (of de kop-bron) per kopje een `h<afterVerse>.mp3`.
4. **Intro**: "Het boek <Boeknaam>, hoofdstuk <N>" i.p.v. alleen "Hoofdstuk N" —
   uitbreiding van `scripts/tts/announce_chapters.py`.
5. **Manifest** per (book, ch, voice) schrijven, incl. `dur` (uit de gegenereerde WAV/MP3)
   en `textHash` (sha1 van de exact gesynthetiseerde tekst).
6. **Nieuwste model**: hele Bijbel opnieuw met de huidige beste stem; herhaalbaar
   (idempotent per hoofdstuk op basis van `textHash`).

## Verouderingscheck (niet-GPU tooling — deze sessie)

Script dat losstaat van de GPU en aangeeft wélke hoofdstukken opnieuw moeten:

- Voor elk hoofdstuk: bereken `textHash` van de huidige `text2026` (+ kopjes).
- Vergelijk met `manifest.textHash` (of, bij oude losse MP3's, de git-/mtime-datum van
  `data/<book>/<ch>.json` versus `audio/<book>/<ch>-<voice>.mp3`).
- Output: lijst van verouderde/ontbrekende hoofdstukken die de TTS-sessie kan hergenereren.

## Opslag (schatting)

- ~1.189 hoofdstukken × ~gem. 25 verzen × 2 stemmen ≈ 60.000 versbestanden.
- Godsnaam-varianten alleen bij de ~5.500 OT-verzen met JHWH → 3× voor die verzen.
- MP3 ~30–60 kB per vers → grofweg 3–5 GB totaal. Acceptabel; per hoofdstuk laden.

## Gefaseerde uitrol

1. **Speler + manifest-formaat** (deze sessie): sequencer met terugval op losse MP3.
   Instellingen-UI voor godsnaam/kopjes/intro. Testbaar met een synthetisch manifest.
2. **Verouderingscheck-tool** (deze sessie).
3. **Generatie** (TTS-sessie): pilot op één hoofdstuk met godsnaam (bv. Genesis 2 — "HEERE
   God"), manifest schrijven, in de speler controleren; daarna uitrol.
4. **Hele Bijbel** opnieuw met het nieuwste model.

## Achterwaartse compatibiliteit

Zolang er voor een hoofdstuk geen `manifest.json` bestaat, speelt de bestaande losse-MP3
-speler ongewijzigd. De chunk-speler activeert alleen waar een manifest aanwezig is, dus
de uitrol kan hoofdstuk voor hoofdstuk zonder de site te breken.
