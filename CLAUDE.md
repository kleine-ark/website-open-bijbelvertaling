# Claude — projectinstructies

Korte regels voor elke Claude-sessie die in deze repo werkt.

## Audio-data (`AUDIO_AVAILABLE`)

De lijst van hoofdstukken die een MP3-voorlezing hebben staat in **`js/audio-available.js`** als `window.AUDIO_AVAILABLE`. **Niet** in `js/lees.js` of `js/app.js`.

Reden: meerdere parallelle Claude-sessies werken in deze repo (één voor tekstverbetering in `js/lees.js`/`js/app.js`, één voor TTS-rollouts). Toen de audio-map nog inline in beide JS-files stond, werd hij meerdere keren per ongeluk teruggezet bij niet-gerelateerde edits.

**Regels:**
- Ga je MP3's genereren? Update `js/audio-available.js` na de rollout.
- Edit je `js/lees.js` of `js/app.js`? Laat de audio-data met rust — die zit niet meer in deze files.
- Tijdens runtime gebruiken beide entry-points `window.AUDIO_AVAILABLE` (geladen via `<script src="js/audio-available.js">` in `lees.html` en `index.html`, vóór de hoofd-JS).

## TTS-pilot & rollout

Zie `docs/superpowers/specs/2026-05-06-tts-bijbel-design.md` en `docs/superpowers/plans/2026-05-06-tts-pilot-genesis-1.md` voor het ontwerp en plan.

Generatie-script: `scripts/tts/run_xtts.py` (voice-cloned XTTS-v2 in `.venv-xtts/`). Voorbeeld: `COQUI_TOS_AGREED=1 python -m scripts.tts.run_xtts --book efeziers --chapters 1-6`.

Het script bevat een Blackwell-patch voor RTX 5070 (sm_120). Niet weghalen tenzij je een PyTorch-build met native sm_120 nvrtc-support hebt.

## Werkstijl

- **Pull voor edit**: `git pull --rebase` of `git fetch && git rebase` voordat je begint, anders krijg je merge-conflicten met de andere sessie die ook op `main` werkt.
- **Push klein en vaak**: per logische eenheid één commit, niet alles opsparen.
- Branch is `main` — geen feature-branches in dit repo, single-developer workflow.
