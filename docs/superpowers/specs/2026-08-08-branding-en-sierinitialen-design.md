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

### Correctie van het koplogo

- Het woordmerk **Open Vertaling** wordt in de gedeelde bovenbalk tweemaal zo groot weergegeven als in de huidige integratie. Het folio-beeldmerk blijft ongeveer op zijn huidige visuele grootte, zodat vooral de te kleine merknaam wordt gecorrigeerd.
- De header gebruikt een afgeleide compositie van dezelfde goedgekeurde vectorpaden. De oorspronkelijke bronbestanden blijven ongewijzigd.
- Het logo behoudt altijd zijn ontworpen verhoudingen. Een combinatie van een vaste breedte en een botsende maximale hoogte mag het beeld niet meer horizontaal of verticaal vervormen.
- De volledige tekst **Open Vertaling** wordt geforceerd behouden: niet afkappen, niet verbergen en niet automatisch verkleinen. Het merkelement zelf mag niet krimpen.
- Zodra de beschikbare breedte te klein wordt, verhuizen het versienummer, de themaknop en de loginbediening eerder naar het hamburgermenu. De overige navigatie wijkt dus voor het woordmerk, niet andersom.
- Ook op zeer smalle schermen blijft de volledige naam zichtbaar. Als één regel niet genoeg ruimte biedt, mag de bovenbalk hoger worden; horizontaal afsnijden of alleen het beeldmerk tonen is niet toegestaan.

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
- Het koplogo heeft op ieder getest breekpunt zijn intrinsieke beeldverhouding en het woordmerk is visueel tweemaal zo groot als vóór deze correctie.
- Bij desktop-, tablet- en mobiele breedtes blijft de volledige tekst **Open Vertaling** zichtbaar zonder afkapping of krimp; concurrerende kopbedieningen staan waar nodig in het hamburgermenu.
