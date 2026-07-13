# Voortgang Ge'ez-vertaling — VOLTOOID (eerste versie)

Vertaling van de Ethiopische boeken uit het Ge'ez naar OSV-Nederlands.
Werkwijze: zie `.claude/skills/geez-vertalen/`. Staging-bestanden per hoofdstuk
in `vertaling/<boek>/<hoofdstuk>.md`.

| Boek | Hoofdstukken | Verzen | Bron | Controle | Status |
|---|---|---|---|---|---|
| 1 Henoch | 108 | 1057 | Ge'ez digitaal | Charles 1917 | ✓ compleet |
| Jubileeën | 50 | 1257 | Ge'ez digitaal | Charles 1902 | ✓ compleet |
| 1 Meqabyan | 36 | 754 | Ge'ez digitaal | geen | ✓ compleet |
| 2 Meqabyan | 21 | 424 | Ge'ez digitaal | geen | ✓ compleet |
| 3 Meqabyan | 10 | 208 | Ge'ez digitaal | geen | ✓ compleet |

**Totaal: 225 hoofdstukken, ~3.700 verzen — alle 5 boeken vertaald.**

## Uitgevoerde kwaliteitscontroles

- Volledigheid: alle 225 hoofdstukbestanden aanwezig, geen gaten.
- Structuur: elk bestand heeft een `# <boek> <nr>`-kop en genummerde verzen.
- Terminologie: kernterm "Heere der geesten" consistent (31 Henoch-hoofdstukken).
- OSV-huisstijl: alle "gij"-vormen omgezet naar "u" (694 vervangingen in 88
  bestanden), met correcte werkwoordsvormen (zijt→bent, zoudt→zou, waart→was,
  hadt→had, enz.). Nul resterende archaïsche 2e-persoonsvormen. Geverifieerd
  tegen de bestaande OSV-tekst (37.322 verzen: "gij" komt daar 0× voor).

## Opgenomen in de site-data ✓

De vertalingen zijn omgezet naar het `data/`-formaat van de OSV-site:
- `data/<id>/<n>.json` per hoofdstuk (verses met `text2026`), voor alle 225 hfst.
- `data/<id>.json` bijgewerkt (chapters + boekintro) voor alle 5 boeken.
- `data/books.json` manifest bijgewerkt (`chaptersIncluded`, `totalChapters`).
- Zoekindex herbouwd (`scripts/build_search_index.py`) — 3.700 verzen doorzoekbaar.
- Statistieken herbouwd (`scripts/build_stats.py`).

Let op: deze boeken hebben `ethiopic: true` en zijn in de site standaard
verborgen; ze verschijnen in de weergavemodus **"ethiopisch"** (bestaand gedrag).

## Nog te doen (redactie / vervolg)

- **Termconsolidatie**: 320 automatisch geoogste termen staan ongecureerd in
  `.claude/skills/geez-vertalen/corpus-termen-ongecureerd.md`. Bij een
  redactieronde de juiste termen in `woordenlijst.md` opnemen.
- **Voetnoten**: Meqabyan en delen van Henoch bevatten voetnoten bij onzekere
  of beschadigde Ge'ez-lezingen (bewaard in de `.md`-staging-bestanden, niet in
  de site-data). Die vragen om een inhoudelijke eindredactie; eventueel als
  echte vers-noten in de site opnemen.
- **Vocatieven**: enkele plaatsen hebben na de gij→u-conversie "u <volk>" als
  aanspreekvorm (bijv. "u Macedoniërs"); eventueel tot "o <volk>" bijschaven.
