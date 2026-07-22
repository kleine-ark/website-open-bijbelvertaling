# Open Bijbelvertaling — TTS-audio per hoofdstuk

**Datum:** 2026-05-06
**Status:** ontwerp, in pilotfase

## Doel

Voor elk hoofdstuk in de Open Vertaling een MP3-bestand genereren van de
voorgelezen bijbeltekst. Eenmalig genereren, opslaan op de server, afspelen
via de bestaande audio-speler (`js/lees.js`) op `audio/{book}/{ch}.mp3`.

De gegenereerde stem moet qua kwaliteit zo dicht mogelijk bij de bestaande
Artlist-MP3's (`audio/Genesis 1.mp3`, `audio/Johannes 1.mp3`) komen.

## Scope

**Wat wel voorgelezen wordt:**
- De `verses[].text2026` van elk hoofdstuk, achter elkaar — exact zoals op de
  website weergegeven, in moderne Nederlandse spelling.

**Wat niet:**
- Geen versnummers ("vers één, vers twee" — kan later, niet nu)
- Geen `chapterIntro` (samenvatting bij begin hoofdstuk)
- Geen `marginNotes` (kanttekeningen)
- Geen `text1637` (originele Statenvertaling — TTS struikelt over
  archaïsche woorden)

**Bronbestanden:** `data/{book}/{chapter}.json`

## Aanpak: open-source TTS, lokaal op GPU

Hardware: **RTX 5070, 12 GB VRAM** — voldoende voor alle moderne
voice-cloning modellen.

### Pilot — 3 kandidaten

Eerst pilot op één hoofdstuk (Genesis 1, 31 verzen, ~5 min audio) om te
beslissen welk model voor de volledige Bijbel gebruikt wordt.

| # | Model | Aanpak | Doel |
|---|---|---|---|
| 1 | **XTTS-v2** (Coqui, fork `idiap/coqui-ai-TTS`) | Voice-clone vanuit Artlist Genesis 1 sample | Bewezen NL-kwaliteit, beste kandidaat om dichtbij Artlist te komen |
| 2 | **Higgs Audio v2** (Boson AI, 2025) | Voice-clone vanuit zelfde sample | Nieuwere generatie, mogelijk beter dan XTTS |
| 3 | **Piper** (`nl_NL-mls-medium`) | Vaste TTS-stem, geen cloning | Ondergrens-referentie. Als dit al goed genoeg klinkt zijn 1+2 niet nodig. |

### Voice-clone-sample

Uit de bestaande `audio/Genesis 1.mp3` (5:05, 128 kbps mono) een schoon
fragment van **15–30 seconden** knippen via `ffmpeg`. `faster-whisper` wordt
gebruikt om het gesproken Nederlands te transcriberen, zodat we de voice-
clone-stappen van XTTS-v2 / Higgs Audio kunnen voeden met audio + transcript.

### Pilot-uitvoer

```
audio/_pilot/xtts/genesis-1.mp3
audio/_pilot/higgs/genesis-1.mp3
audio/_pilot/piper/genesis-1.mp3
```

**Beslismoment:** gebruiker luistert deze drie naast `audio/Genesis 1.mp3`
(Artlist) en kiest een winnaar — of besluit alsnog naar een betaalde API
(ElevenLabs, Google Chirp HD) over te stappen.

## Productie — uitrol over alle hoofdstukken

Na pilot-keuze:

1. **Generatie-script** (`scripts/generate_audio.py`):
   - Loop over `data/*/[0-9]*.json`
   - Concat `verses[].text2026` met enkele spatie tussen verzen
   - Voer aan gekozen TTS-pipeline → schrijf `audio/{book}/{ch}.mp3`
   - Idempotent: skip als output al bestaat (override met `--force`)
   - Resumable: schrijft progress naar `audio/_progress.json`
   - Logt fouten per hoofdstuk in `audio/_errors.log` zonder de hele run
     te laten klappen

2. **Output-formaat:**
   - MP3, 128 kbps, mono, 44.1 kHz (matcht Artlist-baseline)

3. **Integratie met `js/lees.js`:**
   - De `AUDIO_AVAILABLE`-whitelist in `js/lees.js` en `js/app.js`
     uitbreiden naar elke `{book: [chapters]}` die op de server staat
   - Eventueel runtime-detectie via `HEAD audio/{book}/{ch}.mp3` zodat de
     whitelist niet handmatig hoeft te worden bijgewerkt — in
     vervolg-spec te beslissen

4. **Volgorde:** Genesis → Mattheüs → daarna alfabetisch / naar voorkeur.
   Per boek incrementeel committen zodat de site al bruikbaar is voordat
   het hele corpus klaar is.

## Schaalvraagstuk (informatief)

- ~1200 hoofdstukken × ~5 min = ~100 uur GPU-tijd (XTTS-realtime is ~0.5–1×
  realtime op een 5070).
- ~5 GB MP3 totaal — past in een Git LFS-store of aparte CDN-bucket.
- Repo-impact: deze 5 GB **niet** in de hoofd-Git-repo committen. Apart
  hosten of via Git LFS — beslissen na pilot.

## Buiten scope (latere fase)

- Versnummers uitspreken
- Kanttekeningen voorlezen
- Hoofdstuk-intro voorlezen
- Verschillende stemmen per Bijbelboek
- SSML-controls (pauzes, klemtonen)
- Kwaliteitsscan (Whisper terug-transcriberen om misuitspraken te detecteren)

## Succescriterium pilot

Gebruiker beoordeelt subjectief: **"klinkt minstens één van de drie open-
source outputs goed genoeg om de hele Bijbel mee te genereren?"**
- Ja → uitrol met dat model
- Nee → herzien: andere modellen testen, of betaalde API-route
