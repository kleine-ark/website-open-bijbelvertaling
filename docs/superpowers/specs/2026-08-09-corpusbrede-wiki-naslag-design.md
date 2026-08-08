# Corpusbrede wiki-naslag

**Datum:** 9 augustus 2026  
**Status:** goedgekeurd

## Doel

De wiki-pagina’s Materialen, Dieren en Bomen & planten bevatten nu alleen
Genesis. Ze worden uitgebreid naar alle 82 boeken waarvoor verstekst aanwezig
is. Daarnaast komen er twee zelfstandige wiki-pagina’s: Personen en
Muziekinstrumenten.

Iedere detailpagina toont alle gekoppelde vindplaatsen met de letterlijke Open
Vertaling en de bestaande `+`/`−`-bediening voor context. Canonieke en
apocriefe boeken worden gelijk behandeld. Ethiopische boeken zonder hoofdstukdata
worden pas meegenomen zodra er tekst beschikbaar is.

## Afbakening

Deze uitbreiding omvat vijf categorieën:

1. materialen en stoffen;
2. dieren;
3. bomen en planten;
4. personen;
5. muziekinstrumenten.

Personen en Muziekinstrumenten krijgen elk een aparte HTML-pagina, gegevensbron,
wiki-tegel en navigatielink. De bestaande stamboom blijft een afzonderlijke
genealogische weergave. `onderwerpen.html` blijft het thematische overzicht en
wordt niet gebruikt als opslagplaats voor deze encyclopedische categorieën.

## Inhoudelijke regels

### Vindplaatsen

- Alleen `text2026`/`text2026_html` uit echte verzen telt als vindplaats;
  kanttekeningen, boekinleidingen en hoofdstukinleidingen tellen niet mee.
- Een verwijzing heeft altijd de volledige vorm `<boek-id> <hoofdstuk>:<vers>`.
- De volgorde volgt `data/books.json`, daarna hoofdstuk en vers.
- Dubbele verwijzingen binnen één item worden verwijderd.
- Iedere verwijzing wordt tijdens de build gevalideerd tegen de hoofdstukdata.

### Letterlijk en symbolisch

Letterlijke en symbolische vermeldingen worden beide opgenomen. Een item kan
de aanduiding `letterlijk`, `symbolisch` of `beide` dragen. Voorbeelden zijn het
Lam, de Leeuw uit de stam van Juda en de boom van het leven. De markering
beschrijft het gebruik zonder een theologische uitleg aan de verstekst toe te
voegen.

### Personen

- Alle bij naam genoemde menselijke personen worden opgenomen.
- Individueel herkenbare naamloze personen worden eveneens opgenomen wanneer
  ze binnen één verhaal duurzaam aanwijsbaar zijn, bijvoorbeeld de Samaritaanse
  vrouw of de kamerling uit Ethiopië.
- Jezus Christus wordt opgenomen met de expliciete aanduiding dat Hij de Zoon
  is, God geopenbaard in het vlees. God de Vader, de Heilige Geest, engelen,
  demonen, volken en anonieme menigten worden niet als gewone menselijke
  personen gecatalogiseerd.
- Gelijknamige personen krijgen afzonderlijke items met een korte
  onderscheiding, bijvoorbeeld afkomst, familie of functie.
- Automatische naamdetectie mag nooit zelf gelijknamige personen samenvoegen.
  Dubbelzinnige vindplaatsen worden expliciet aan een item toegewezen.

### Taxonomie

Een gecontroleerde catalogus bevat per item:

- stabiel id en zichtbare naam;
- categorie en eventueel gebruikstype;
- zoekvormen en verbogen/meervoudige vormen;
- uitsluitingspatronen voor bekende valse treffers;
- optionele expliciete vindplaatsen en expliciete uitsluitingen;
- een korte beschrijving op basis van de verstekst;
- optionele synoniem- of verwijsrelaties zonder dubbele detailpagina.

De gepubliceerde JSON-bestanden zijn gegenereerde uitvoer. Handmatige correcties
horen in de catalogus, zodat een volgende build ze niet overschrijft.

## Bouwproces

Een nieuw script `scripts/build_corpus_naslag.py`:

1. leest de boekvolgorde en alle beschikbare hoofdstukbestanden;
2. projecteert `text2026_html` naar schone zichtbare verstekst;
3. zoekt gecontroleerde hele-woordvormen hoofdletterongevoelig;
4. voegt expliciete vindplaatsen toe en verwijdert expliciete uitsluitingen;
5. valideert boek, hoofdstuk, vers, ids, aliassen en dubbele items;
6. schrijft de vijf `data/naslag-*.json`-bestanden deterministisch;
7. schrijft een controleverslag met onbekende kandidaattermen, zodat mogelijke
   uitbreidingen zichtbaar blijven zonder ze ongecontroleerd te publiceren.

De bestaande `js/naslag.js` accepteert zowel de oude korte Genesis-verwijzingen
als de nieuwe volledige verwijzingen. Na de migratie gebruiken alle vijf
gegevensbronnen uitsluitend volledige verwijzingen.

## Pagina-opbouw

De vijf pagina’s delen de bestaande naslagrenderer en vormgeving:

- overzicht met zoekveld en alfabetische items;
- detailpagina met teruglink, titel, type-aanduiding en beschrijving;
- alle gekoppelde versteksten in canonieke volgorde;
- per verstekst de bestaande contextknoppen;
- mobiel minimaal 16 pixels leesmarge en geen horizontaal scrollen;
- donkere modus en toetsenbordfocus gelijk aan de bestaande wiki.

Personen toont aanvullend een korte onderscheiding bij gelijknamigen.
Muziekinstrumenten groepeert verwante vertaalnamen niet stilzwijgend: als de
identificatie onzeker is, vermeldt de beschrijving dat en blijft de gebruikte
vertaalnaam zichtbaar.

## Navigatie en beeld

`wiki.html` en het wiki-zijmenu krijgen de links Personen en
Muziekinstrumenten als twee afzonderlijke regels. De overzichtstegels gebruiken
dezelfde beeldverhouding, typografie en rustige animatiestijl als de bestaande
wiki-tegels. In deze gegevensuitbreiding worden geen tijdelijke SVG-symbolen
gebruikt. Als nog geen goedgekeurd rasterbeeld beschikbaar is, gebruikt de
tegel een bestaande neutrale achtergrond totdat een afzonderlijk beeldontwerp
is goedgekeurd.

## Foutafhandeling

- De build stopt bij ongeldige referenties, dubbele ids of ontbrekende verplichte
  velden.
- Een item zonder vindplaatsen wordt niet gepubliceerd en wordt in het
  controleverslag genoemd.
- Een onzekere automatische kandidaat komt alleen in het controleverslag.
- Een fout bij het laden van één verstekst laat de referentie en de overige
  teksten bruikbaar, conform `js/gekoppelde-teksten.js`.

## Tests en acceptatie

1. De generator levert bij twee opeenvolgende runs bytegelijk resultaat.
2. Iedere gepubliceerde verwijzing bestaat en wijst naar een echt vers.
3. Iedere automatisch gevonden verwijzing bevat een zoekvorm in de zichtbare
   verstekst; expliciete uitzonderingen zijn traceerbaar in de catalogus.
4. De gegevens bevatten verwijzingen uit Oude Testament, Nieuwe Testament en
   apocriefe boeken wanneer de categorie daar voorkomt.
5. Geen van de drie bestaande pagina’s noemt nog “Voorlopig alleen Genesis”.
6. Personen en Muziekinstrumenten zijn afzonderlijk bereikbaar via wiki-overzicht
   en zijmenu.
7. Overzicht, detailweergave, zoeken, volledige verwijzingen en contextknoppen
   werken voor alle vijf categorieën.
8. Browsertests controleren desktop, 390-pixelweergave, donkere modus en
   toetsenbordbediening.
9. De volledige bestaande testsuite blijft groen.

## Buiten scope

- de Bijbelvertaling, kanttekeningen of grondtekst aanpassen;
- automatisch biografieën of natuurhistorische verklaringen verzinnen;
- externe afbeeldingen genereren zonder afzonderlijke ontwerpgoedkeuring;
- de stamboom vervangen door de Personen-pagina;
- niet-menselijke geestelijke wezens als gewone personen catalogiseren;
- boeken zonder verstekst als afgedekte corpusbron rapporteren.
