# Downloads — ontwerp

**Datum:** 4 augustus 2026
**Status:** vastgesteld, nog niet geïmplementeerd

## Aanleiding

Bezoekers kunnen de Open Vertaling nu alleen op de site lezen. Er is geen manier
om de tekst mee te nemen naar een e-reader, en geen manier om de onderliggende
data te hergebruiken. `js/export.js` bestaat wel, maar dat is een editor-functie
voor de vertaler zelf (boek-JSON en eigen bewerkingen exporteren) en niet
geschikt voor publiek gebruik.

Doel: een downloadpagina met twee uitgaven — de ruwe brondata en een
leesuitgave als EPUB.

## Beslissingen

| Onderwerp | Keuze |
|---|---|
| Uitgaven | Ruwe brondata (zip) en EPUB |
| Ruwe data | Eén zip met de complete `data/`-map, ongefilterd |
| EPUB-inhoud | Alleen nagekeken hoofdstukken |
| EPUB-opmaak | Alleen verstekst; geen kanttekeningen, Strong's of parallelteksten |
| Bouwmoment | Tijdens de deploy in GitHub Actions |
| Licentie | CC0 / publiek domein |

**Waarom alleen nagekeken tekst in de EPUB:** van de 37.235 verzen is 35,8%
nagekeken. Het Nieuwe Testament is compleet (100%), het Oude Testament staat op
17,9%. Een uitgave die ongemerkt onnagekeken tekst bevat, geeft de lezer geen
manier om te zien wat wel en niet gecontroleerd is. De uitgave groeit vanzelf
mee naarmate er meer wordt nagekeken.

**Waarom bouwen tijdens de deploy:** de zip is ± 42 MB. Die bij elke herbouw
committen laat een repo van 8,8 GB verder oplopen. Bouwen in CI houdt de
artefacten per definitie synchroon met de data en de repo schoon. In de browser
genereren valt af: dat vergt 281 MB aan fetches en breekt op de
iPadOS 15.4-ondergrens.

## Eén bron voor "nagekeken"

`VERIFIED_CHAPTERS` staat nu tweemaal — [`js/app.js:65`](../../../js/app.js) en
[`js/lees.js:123`](../../../js/lees.js) — en `scripts/build_stats.py` haalt hem
met een regex uit `app.js`. De twee kopieën zijn op dit moment identiek, maar de
opzet nodigt uit tot drift; dit is hetzelfde probleem dat eerder met de audiodata
speelde en waarvoor `js/audio-available.js` is ingevoerd.

Het bouwscript heeft deze data ook nodig. Daarom wordt het één bestand:

**`data/verified-chapters.json`**

```json
{
  "genesis": [1, 2, 3, "…", 20],
  "markus": "all",
  "johannes": "all"
}
```

Waarde is `"all"` of een array met hoofdstuknummers — dezelfde vorm die
`_isVerified()` nu al verwerkt.

Consumenten:

| Bestand | Wijziging |
|---|---|
| `js/app.js` | Inline object weg; laadt de JSON in de bestaande async init |
| `js/lees.js` | Idem |
| `scripts/build_stats.py` | Regex weg; leest de JSON |
| `scripts/build_downloads.py` | Leest de JSON (nieuw) |

**Laadgedrag in de browser.** `renderChapter()` is al async en wacht op de
hoofdstukdata; de JSON (± 1,4 KB) wordt in diezelfde wachtstap meegenomen en na
de eerste keer gecached. Het bestand wordt toegevoegd aan `PRECACHE_URLS` in
`sw.js`.

**Faalgedrag.** Mislukt het laden, dan geldt elk hoofdstuk als *niet* nagekeken,
zodat de waarschuwingsbanner verschijnt. Nooit andersom: een technische storing
mag er niet toe leiden dat onnagekeken tekst zonder waarschuwing getoond wordt.

## Bouwscript

**`scripts/build_downloads.py`** — leest `data/`, schrijft naar `downloads/`.

Uitvoer:

| Bestand | Inhoud |
|---|---|
| `open-vertaling-brondata.zip` | De complete `data/`-map, ongefilterd |
| `open-vertaling-nagekeken.epub` | Alleen nagekeken hoofdstukken |
| `index.json` | Per uitgave: naam, bestandsnaam, omvang in bytes, datum, omschrijving |

Bestandsnamen zijn stabiel (geen versienummer erin), zodat links naar de
downloads blijven werken. De versie staat in `index.json`, in het colofon en op
de pagina.

`index.json` bestaat zodat `downloads.html` de omvang en datum toont zonder die
in HTML vast te leggen — anders veroudert die informatie stilletjes.

## EPUB-specificatie

- EPUB 3, standaardindeling: `mimetype` (ongecomprimeerd, als eerste item),
  `META-INF/container.xml`, `OEBPS/`
- Eén XHTML-bestand per boek
- `nav.xhtml` met geneste inhoudsopgave: boek → hoofdstuk
- `content.opf` met `dc:title` "Open Vertaling", `dc:language` `nl`,
  `dc:rights` CC0, `dc:date` en een stabiele `dc:identifier`
- Verstekst uit `text2026_html`, met terugval op `text2026` en `textHerzien` —
  dezelfde volgorde als `js/app.js:701`
- Site-specifieke opmaak in `text2026_html` (Strong's-spans, geo-markering)
  wordt gestript tot EPUB-veilige XHTML
- Versnummers als superscript vóór de verstekst
- Gedeeltelijk nagekeken boeken nemen alleen hun nagekeken hoofdstukken mee.
  Genesis verschijnt dus als hoofdstuk 1 t/m 20, met een regel bij het boek dat
  de rest nog niet is nagekeken.
- Colofonpagina: versie en datum uit `data/stats.json`, aantal opgenomen boeken,
  hoofdstukken en verzen, licentie CC0, en de site-URL

## Pagina

**`downloads.html`** — losse pagina in de stijl van de bestaande pagina's
(`<nav id="topnav">`, `css/style.css`). Leest `downloads/index.json` en toont per
uitgave een kaart met naam, omschrijving, omvang, datum en downloadknop.

Bij de EPUB staat expliciet welke tekst erin zit ("alleen nagekeken hoofdstukken")
met de actuele telling, zodat de lezer weet wat hij krijgt.

**`js/topnav.js`** — link `<a href="downloads.html">Downloads</a>` toevoegen aan
`.topnav-links`, na "Wiki".

## Deploy

- `.github/workflows/deploy.yml`: `build_command: python scripts/build_downloads.py`
- `.gitignore`: `downloads/*.zip` en `downloads/*.epub` en `downloads/index.json`
- De bestaande `downloads/4QGenb-Genesis1-transcriptie.txt` blijft in git staan
- `rsync --delete` ververst de artefacten bij elke deploy

## Tests

**`tests/test_build_downloads.py`** (pytest, aansluitend op de bestaande tests):

1. Het script maakt beide bestanden en `index.json`
2. De EPUB opent als zip; `mimetype` is het eerste item en ongecomprimeerd
3. `META-INF/container.xml`, `content.opf` en `nav.xhtml` zijn aanwezig en
   welgevormd XML
4. Uitsluitend nagekeken hoofdstukken zitten erin — controle met een boek dat
   gedeeltelijk is nagekeken: Genesis 20 aanwezig, Genesis 21 afwezig
5. De inhoudsopgave verwijst alleen naar bestanden die daadwerkelijk in de EPUB
   zitten
6. De omvang in `index.json` komt overeen met de bestanden op schijf
7. De zip bevat de brondata

`epubcheck` is niet beschikbaar zonder netwerk; de controle blijft structureel.

## Buiten scope

- PDF- en platte-tekstuitgaven
- Perikoopkoppen in de EPUB (`data/pericopen.json`)
- Kanttekeningen, Strong's-nummers en parallelvertalingen in de EPUB
- Per-boek downloads
- Audio in de downloads
