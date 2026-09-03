# Claude — projectinstructies

Korte regels voor elke Claude-sessie die in deze repo werkt.

## Audio-data (`AUDIO_AVAILABLE`)

De lijst van hoofdstukken die een MP3-voorlezing hebben staat in **`js/audio-available.js`** als `window.AUDIO_AVAILABLE`. **Niet** in `js/lees.js` of `js/app.js`.

Reden: meerdere parallelle Claude-sessies werken in deze repo (één voor tekstverbetering in `js/lees.js`/`js/app.js`, één voor TTS-rollouts). Toen de audio-map nog inline in beide JS-files stond, werd hij meerdere keren per ongeluk teruggezet bij niet-gerelateerde edits.

**Regels:**
- Ga je audio genereren? Publiceer die eerst met `scripts/publish_audio.sh` en
  update `js/audio-available.js` pas nadat de checksumcontrole slaagt.
- Edit je `js/lees.js` of `js/app.js`? Laat de audio-data met rust — die zit niet meer in deze files.
- Tijdens runtime gebruiken beide entry-points `window.AUDIO_AVAILABLE` (geladen via `<script src="js/audio-available.js">` in `lees.html` en `index.html`, vóór de hoofd-JS).

## TTS-pilot & rollout

Zie `docs/superpowers/specs/2026-05-06-tts-bijbel-design.md` en `docs/superpowers/plans/2026-05-06-tts-pilot-genesis-1.md` voor het ontwerp en plan.

Generatie-script: `scripts/tts/run_xtts.py` (voice-cloned XTTS-v2 in `.venv-xtts/`). Voorbeeld: `COQUI_TOS_AGREED=1 python -m scripts.tts.run_xtts --book efeziers --chapters 1-6`.

Het script bevat een Blackwell-patch voor RTX 5070 (sm_120). Niet weghalen tenzij je een PyTorch-build met native sm_120 nvrtc-support hebt.

## Wijzigingsprincipes — vervang alleen in de eerste linie

**Een principe werkt éénmalig, vanuit de Statenvertaling-1888 als basis. Wat een
principe heeft opgeleverd mag nooit door een tweede principe worden aangepakt.**

Voorbeeld. Stel er zijn twee principes:

- `leger` → `bed`
- `legermacht` → `leger`

Dan mag de `leger` die uit `legermacht` is ontstaan **nooit** alsnog `bed`
worden. Hij is al vervangen en is daarmee klaar.

Wat dit voor een sweep betekent:

- Bepaal wélke plaatsen in aanmerking komen door te kijken naar **`textSV1888`**,
  niet naar `text2026`. Die laatste bevat immers al eerdere vervangingen.
- Pas de wijziging vervolgens toe op `text2026` en `text2026_html`.
- Draai nooit een sweep die zijn eigen uitvoer opnieuw als invoer kan zien.

Zonder deze regel hangt de uitkomst af van de volgorde waarin sweeps toevallig
draaien, en gaan principes elkaar terugdraaien. Dat is eerder gebeurd: `V139`
(vroedvrouw → verloskundige) en `V969` (het omgekeerde) hieven elkaar op tot
`V969` werd verwijderd.

Bij het toevoegen van een principe: controleer of de **uitkomst** ervan niet het
**bronwoord** van een ander principe is. Het script
`scripts/audit_principes.py` doet die controle.

## Werkstijl

- **Pull voor edit**: `git pull --rebase` of `git fetch && git rebase` voordat je begint, anders krijg je merge-conflicten met de andere sessie die ook op `main` werkt.
- **Push klein en vaak**: per logische eenheid één commit, niet alles opsparen.
- Branch is `main` — geen feature-branches in dit repo, single-developer workflow.
