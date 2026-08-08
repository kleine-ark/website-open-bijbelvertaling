# Liedtegels met Bijbelgedeelte

## Doel

Op het overzicht van Liederen ziet de lezer bij iedere tegel meteen in welk Bijbelgedeelte het lied staat. De lijst bevat alleen liederen uit de canonieke Bijbelboeken. Op de detailpagina vervalt de afzonderlijke sectie `Vindplaatsen in de hele Bijbel`, omdat de volledige liedtekst daar al met passagekoppen wordt weergegeven.

## Afbakening en nummering

- De liederen uit Henoch, Tobit, het Gezang in de vuuroven, Judith en Jezus Sirach vervallen.
- De bronitems en de vijf bijbehorende gebouwde tekstbundels worden verwijderd, zodat ook rechtstreekse oude adressen deze liedpagina’s niet meer opleveren.
- Er blijven 26 liederen over. Zij worden opnieuw doorlopend genummerd als Lied 1 tot en met Lied 26.
- Het lied bij de Schelfzee wordt Lied 1. Het gezang van Mozes en van het Lam wordt Lied 26.
- De badge op het algemene wiki-overzicht verandert van `31 liederen` naar `26 liederen`.

## Gekozen vorm

- Iedere liedtegel toont onder de titel één rustige, goudkleurige regel met de passage.
- Gewone liederen gebruiken het bestaande label uit `tekstpassages`, bijvoorbeeld `Exodus 15:1–18`.
- Meerdere korte passages worden met een middelpunt gescheiden, bijvoorbeeld `Mattheüs 26:30 · Markus 14:26`.
- Lange, aaneengesloten hoofdstukbundels worden compact weergegeven, bijvoorbeeld `Hooglied 1–8` en `Klaagliederen 1–5`.
- De titel blijft ongewijzigd. Het liednummer volgt de nieuwe reeks van 1 tot en met 26. Aantallen vindplaatsen keren niet terug.

## Detailpagina

Alleen bij liederen wordt de sectie `Vindplaatsen in de hele Bijbel` niet meer opgebouwd. De volledige tekst, de passagekoppen en de terugkoppeling naar het liederenoverzicht blijven staan. Gebedspagina’s behouden hun vindplaatsensectie.

## Techniek

De bestaande renderer in `js/naslag.js` maakt de tegelverwijzing uit `tekstpassages`. De datalaag blijft daarmee de enige bron voor passagegrenzen. Alleen voor lange hoofdstukbundels mag een compact overzichtslabel in het liederenbestand staan, zodat geen fragiele tekstherkenning nodig is. De bouwcontrole verwacht voortaan exact 26 liederen.

## Controle

- De lijst bevat exact 26 liederen en geen van de vijf uitgesloten apocriefe werken.
- De nummering loopt zonder gaten van Lied 1 tot en met Lied 26.
- Alle 26 liedtegels hebben een zichtbare, niet-lege passageverwijzing.
- De verwijzingen voor een enkel gedeelte, meerdere gedeelten en lange hoofdstukbundels worden gecontroleerd.
- Op een lieddetailpagina bestaat geen kop `Vindplaatsen in de hele Bijbel` meer.
- Op een gebedsdetailpagina blijft de vindplaatsensectie aanwezig.
