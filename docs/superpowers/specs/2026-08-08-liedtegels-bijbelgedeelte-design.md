# Liedtegels met Bijbelgedeelte

## Doel

Op het overzicht van Liederen ziet de lezer bij iedere tegel meteen in welk Bijbelgedeelte het lied staat. Op de detailpagina vervalt de afzonderlijke sectie `Vindplaatsen in de hele Bijbel`, omdat de volledige liedtekst daar al met passagekoppen wordt weergegeven.

## Gekozen vorm

- Iedere liedtegel toont onder de titel één rustige, goudkleurige regel met de passage.
- Gewone liederen gebruiken het bestaande label uit `tekstpassages`, bijvoorbeeld `Exodus 15:1–18`.
- Meerdere korte passages worden met een middelpunt gescheiden, bijvoorbeeld `Mattheüs 26:30 · Markus 14:26`.
- Lange, aaneengesloten hoofdstukbundels worden compact weergegeven, bijvoorbeeld `Hooglied 1–8` en `Klaagliederen 1–5`.
- Het liednummer en de titel blijven ongewijzigd. Aantallen vindplaatsen keren niet terug.

## Detailpagina

Alleen bij liederen wordt de sectie `Vindplaatsen in de hele Bijbel` niet meer opgebouwd. De volledige tekst, de passagekoppen en de terugkoppeling naar het liederenoverzicht blijven staan. Gebedspagina’s behouden hun vindplaatsensectie.

## Techniek

De bestaande renderer in `js/naslag.js` maakt de tegelverwijzing uit `tekstpassages`. De datalaag blijft daarmee de enige bron voor passagegrenzen. Alleen voor lange hoofdstukbundels mag een compact overzichtslabel in het liederenbestand staan, zodat geen fragiele tekstherkenning nodig is.

## Controle

- Alle 31 liedtegels hebben een zichtbare, niet-lege passageverwijzing.
- De verwijzingen voor een enkel gedeelte, meerdere gedeelten en lange hoofdstukbundels worden gecontroleerd.
- Op een lieddetailpagina bestaat geen kop `Vindplaatsen in de hele Bijbel` meer.
- Op een gebedsdetailpagina blijft de vindplaatsensectie aanwezig.
