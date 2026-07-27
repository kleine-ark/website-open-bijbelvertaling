# Evangelisatietraktaat — ontwerp

**Datum:** 2026-07-26
**Map:** `22 Evangelisatietraktaat/`

## Doel

Een evangelisatieboekje op basis van de Open Staten Vertaling: een selectie van
194 bijbelhoofdstukken, in boekjevorm gepresenteerd met links de bijbeltekst en
rechts een afbeelding met uitleg. De tekst blijft gekoppeld aan de OSV — een
wijziging in `data/` staat bij het verversen van de pagina in het traktaat.

Het boekje wordt uiteindelijk een losstaande website. Het ontwerp houdt daar
rekening mee zonder er nu op vooruit te lopen.

## Werkmap

Al het werk gebeurt in de git-repo `~/Documents/GitHub/website-open-bijbelvertaling`.
De Dropbox-map `…/19 Open Vertaling` is een spiegel: `sync-dropbox.sh` doet
`rsync --delete` vanuit de repo naar Dropbox, dus alles wat daar wordt
aangemaakt verdwijnt bij de eerstvolgende sync.

## Bestandsindeling

```
22 Evangelisatietraktaat/
  index.html            de boekje-pagina
  css/traktaat.css      opmaak (wordt handmatig verder uitgewerkt)
  js/config.js          DATA_BASE / IMG_BASE / LEES_BASE
  js/selectie.js        window.TRAKTAAT_SELECTIE — de passagelijst
  js/render.js          pure functies: titels, url's, html-strings
  js/laden.js           ophalen van een hoofdstuk
  js/traktaat.js        dom, inhoudsopgave, lazy loading
  data/uitleg.json      per passage de uitleg (start: leeg object)
  scripts/controleer_selectie.py   valideert de selectie tegen data/
  tests/                unit-tests (node --test)
```

Let op: `sync-dropbox.sh` sluit `scripts/` uit van de sync. Het controlescript
komt daardoor niet in de Dropbox-spiegel te staan; dat is geen probleem, het is
een ontwikkelhulpmiddel.

## Koppeling met de OSV

`js/config.js` bevat drie instellingen:

| Instelling  | Waarde nu             | Betekenis                                  |
|-------------|-----------------------|--------------------------------------------|
| `DATA_BASE` | `../data/`            | waar `<boek>/<hoofdstuk>.json` wordt gehaald |
| `IMG_BASE`  | `../images/chapters/` | waar `{boek}_{hfst}.jpg` wordt gehaald      |
| `LEES_BASE` | `../lees.html`        | doel van de link naar de OSV-leesomgeving   |

De pagina haalt de verzen bij het openen op uit dezelfde JSON-bestanden die
openvertaling.nl gebruikt. Er wordt niets gekopieerd of gegenereerd; de OSV is
de enige bron.

Wordt het traktaat een losse website, dan worden deze drie waarden absolute
URL's (`https://openvertaling.nl/data/` enz.) en blijft de koppeling live.
GitHub Pages stuurt `Access-Control-Allow-Origin: *` mee, dus cross-origin
ophalen werkt.

**Bekende beperkingen.** De pagina werkt alleen via een webserver; `file://`
blokkeert `fetch`. Als losse website is het traktaat afhankelijk van de
bereikbaarheid van openvertaling.nl.

## De selectie

`js/selectie.js` bevat één lijst met per hoofdstuk één regel:

```js
window.TRAKTAAT_SELECTIE = [
  {"boek": "genesis", "hoofdstuk": 1},
  {"boek": "jesaja", "hoofdstuk": 5, "verzen": [1, 24]}
];
```

- `boek` — het `id` uit `data/books.json` (kleine letters, geen spaties)
- `hoofdstuk` — hoofdstuknummer
- `verzen` — optioneel `[eerste, laatste]`; ontbreekt het, dan het hele hoofdstuk
- `titel` — optioneel, overschrijft de automatisch gebouwde kop

Eén regel per hoofdstuk, omdat afbeelding en uitleg ook per hoofdstuk gaan. De
volgorde in de lijst is de volgorde in het boekje. Dit bestand is de enige plek
waar de inhoud van het traktaat wordt gewijzigd.

### Inhoud (194 passages)

**Oude Testament**

| Boek | Passages |
|------|----------|
| Genesis | 1-25 |
| Exodus | 19, 20 |
| Deuteronomium | 28 |
| Richteren | 13-16 |
| 1 Samuel | 16, 17 |
| 1 Koningen | 8:12-66, 9:1-12 |
| Job | 1-3, 38-42 |
| Psalmen | 1-25, 119:1-40, 122 |
| Spreuken | 1-9, 30 |
| Prediker | 1-3 |
| Jesaja | 1-4, 5:1-24, 44:1-8, 52:13-15, 53, 55, 64, 65:1-5 |
| Jeremia | 1:1-10 |
| Klaagliederen | 3 |
| Ezechiël | 28, 36:16-33 |
| Daniël | 1, 6, 7, 9, 10 |
| Hosea | 14:2-3 |
| Jona | 1-4 |
| Gebed van Manasse | (het hele boek) |
| Habakuk | 1, 2 |
| Zacharia | 10, 14 |
| Maleachi | 3 |

**Nieuwe Testament**

| Boek | Passages |
|------|----------|
| Markus | 1-16 |
| Johannes | 1-21 |
| Handelingen | 1-5, 8-10 |
| Romeinen | 1-16 |
| 1 Korinthiërs | 12 |
| Galaten | 5 |
| Efeziërs | 6 |
| Filippenzen | 3 |
| Kolossenzen | 1-4 |
| Jakobus | 1, 4 |
| 1 Johannes | 1-3 |
| Openbaring | 1-4, 22 |

Jesaja 52:13-53:12 is in de lijst gesplitst in `jesaja 52:13-15` en
`jesaja 53` (heel), omdat de eenheid van selectie het hoofdstuk is.

`scripts/controleer_selectie.py` loopt de hele lijst na tegen `data/` en meldt
elke passage die niet bestaat of waarvan het versbereik buiten het hoofdstuk
valt. Bij de huidige lijst zijn alle 194 passages geldig.

## Weergave

Per passage één spread:

- **links** — de OSV-tekst: versnummer gevolgd door `text2026`. Geen
  kanttekeningen, geen hoofdstukinleiding, geen 1637-tekst. De godsnaam blijft
  zoals hij in de data staat (JAHWEH); er wordt niets omgezet.
- **rechts** — `IMG_BASE/{boek}_{hoofdstuk}.jpg` met daaronder de uitleg uit
  `data/uitleg.json`.

Bij lange gedeelten scrollt de linkerkolom door terwijl de rechterkolom
meeloopt (`position: sticky`). Er wordt doorlopend gescrold van spread naar
spread; een inhoudsopgave in de zijbalk springt naar een passage.

De kop van elke spread ("Genesis 1") is een link naar `LEES_BASE#genesis/1`,
zodat de brontekst in de OSV-leesomgeving één klik verderop ligt.

`css/traktaat.css` houdt de opmaak sober en beperkt zich tot wat de structuur
nodig heeft: de tweekoloms-indeling, leesbare regellengte, en de kaders voor
ontbrekende afbeelding en uitleg. De verdere vormgeving gebeurt handmatig in
dit bestand.

### Uitleg

`data/uitleg.json` is een object met per passage een sleutel `boek_hoofdstuk`:

```json
{
  "genesis_1": "God is de Maker van alles wat bestaat …",
  "jona_2": "…"
}
```

Het bestand begint leeg (`{}`) en wordt later gevuld.

### Ontbrekende onderdelen

Er zijn nog geen hoofdstukafbeeldingen gegenereerd (`images/chapters/` bevat
alleen een README) en er is nog geen uitleg. Beide worden zichtbaar maar
onopvallend afgehandeld:

- geen afbeelding → een kader met de hoofdstuktitel, in de verhouding van de
  latere afbeelding, zodat de opmaak niet verspringt
- geen uitleg → de regel "Uitleg volgt"

Zodra een bestand of een regel in `uitleg.json` wordt toegevoegd, verschijnt
het — zonder codewijziging.

### Laden en fouten

De inhoudsopgave staat er direct volledig. Elke spread laadt zijn hoofdstuk pas
wanneer hij in beeld komt (`IntersectionObserver`), zodat niet 194
JSON-bestanden tegelijk worden opgehaald. Tot dat moment houdt de spread zijn
plaats in met een placeholder.

Mislukt het ophalen van een hoofdstuk, dan toont die spread de melding met een
knop "Opnieuw proberen"; de rest van het boekje blijft werken.

## Testen

- `scripts/controleer_selectie.py` — valideert alle passages tegen `data/`:
  bestaat het boek, bestaat het hoofdstuk, valt het versbereik binnen het
  aantal verzen. Draait zonder afhankelijkheden en is de regressietest op de
  selectie.
- `node --test tests/` — unit-tests op de pure render-functies en de laadlaag.
- Handmatige controle in de browser via een lokale webserver
  (`python3 -m http.server`): eerste spread toont Genesis 1, versbereiken
  kloppen (1 Koningen 8 begint bij vers 12, Hosea 14 toont twee verzen),
  ontbrekende afbeelding en uitleg tonen hun kader, en de kop linkt naar de
  juiste plaats in `lees.html`.

## Buiten scope

- Print-PDF of andere export-formaten
- Godsnaam-varianten (HEERE, Jehovah, יהוה)
- Kanttekeningen, hoofdstukinleidingen, 1637-tekst
- Het genereren van de afbeeldingen
- Het schrijven van de uitleg
- Het traktaat als losstaande deploy — het ontwerp bereidt het voor via
  `js/config.js`, maar de verhuizing zelf is later werk
