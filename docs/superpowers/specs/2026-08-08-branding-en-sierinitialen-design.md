# Nieuwe branding en sierinitialen

## Doel

Het aangeleverde Open Vertaling-woordmerk en beeldmerk vervangen de oude tekstuele merkweergave en het `OV`-favicon. De aangeleverde reeks `A.svg` tot en met `Z.svg` vervangt de bestaande typografische drop-cap aan het begin van ieder hoofdstuk.

## Branding

- De vier originele bronbestanden komen ongewijzigd in `images/branding/`.
- De gedeelde bovenbalk toont het volledige woordmerk als link naar de leestekst. Het versienummer blijft er los naast staan.
- Omdat het bronlogo marineblauw op transparant is, krijgt de permanent marineblauwe bovenbalk een afgeleide witte/gouden variant van exact dezelfde tekening. Er komt geen kader, capsule of extra decoratie omheen.
- De volledige naam blijft op mobiel zichtbaar. Het logo schaalt daar kleiner, maar wordt niet vervangen door alleen het beeldmerk.
- De aparte header van `lees.html` gebruikt het donkere bronlogo op een lichte achtergrond en de witte/gouden variant in het donkere thema.
- `favicon.svg` gebruikt het nieuwe folio-beeldmerk. De webapp-iconen worden eveneens opnieuw opgebouwd met dit beeldmerk, zodat browserblad, beginscherm en geïnstalleerde webapp dezelfde identiteit voeren.

## Sierinitialen

- Alle 26 bronletters komen ongewijzigd in `images/initialen/vrije-penkrul/`.
- Ieder eerste vers van ieder zichtbaar hoofdstuk krijgt de bijbehorende SVG-letter; dit blijft werken wanneer meerdere hoofdstukken doorlopend zijn geladen.
- De oorspronkelijke letter blijft als echte tekst in de DOM staan voor selecteren, kopiëren en schermlezers. De SVG wordt alleen als visuele achtergrond van die letter gebruikt.
- Voor het donkere thema worden afgeleide varianten gemaakt waarin alleen het marineblauw licht wordt; het goud blijft gelijk.
- Accenten of andere begintekens waarvoor geen A–Z-bestand bestaat, vallen terug op de bestaande typografische drop-cap zonder tekstverlies.
- De bestaande behandeling van openingsaanhalingstekens bij vers 1 blijft behouden.

## Vorm

De marineblauwe en gouden merkkleuren blijven leidend. Het woordmerk is het enige opvallende element in de navigatie; de rest van de balk blijft rustig. De sierinitiaal krijgt een vak van `2.55em × 3.2em` met `0.35em` witruimte rechts, zonder beweging of extra ornament naast de al in de SVG opgenomen penkrul.

## Controle

- Het volledige woordmerk is zichtbaar op desktop en mobiel.
- Het woordmerk blijft leesbaar in licht en donker thema.
- Het favicon en de webapp-iconen bevatten het folio-beeldmerk en niet langer de letters `OV`.
- Alle 26 sierletterbestanden bestaan in een lichte en donkere variant.
- Genesis 1 begint visueel met `I.svg`, Genesis 2 met `Z.svg`, en kopiëren van het vers behoudt de eerste letter.
- Doorlopend lezen geeft ieder nieuw hoofdstuk zijn eigen sierinitiaal.
