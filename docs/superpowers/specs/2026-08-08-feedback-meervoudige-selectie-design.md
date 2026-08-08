# Feedback bij een meervoudige versselectie

## Doel

Wanneer een lezer meerdere verzen selecteert en **Opmerking** kiest, moet de feedbackmelding de volledige selectie naar het bestaande Google Formulier en de gekoppelde spreadsheet sturen. De verwijzing mag niet langer alleen naar het eerste geselecteerde vers wijzen.

## Afbakening

Deze wijziging gebruikt de bestaande formulier- en spreadsheetvelden. Er worden geen nieuwe externe velden, opslagdiensten of inlogvereisten toegevoegd. Feedback bij een tekstselectie binnen één vers blijft ongewijzigd werken.

## Gegevensmodel

`VerseSelect` bouwt voor alle geselecteerde versrijen één gedeeld selectieobject met:

- een volledige, leesbare verwijzing;
- de geselecteerde verzen in DOM-volgorde;
- per vers boek-id, hoofdstuk, versnummer en platte tekst;
- de complete platte tekst voor verzending en weergave.

Aaneengesloten verzen worden als bereik weergegeven, bijvoorbeeld `Genesis 1:1-3`. Niet-aaneengesloten verzen worden compact samengevoegd, bijvoorbeeld `Genesis 1:1, 3, 5`. Een selectie over meerdere hoofdstukken of boeken krijgt per hoofdstuk of boek een afzonderlijk verwijzingsdeel, gescheiden door een puntkomma.

## Gebruikersinterface

Het feedbackvenster toont vóór verzending:

- de volledige samengestelde verwijzing;
- ieder geselecteerd vers op een eigen regel, met zijn volledige verwijzing en tekst;
- het bestaande invoerveld voor de suggestie.

Voor een selectie binnen één vers blijft de compacte bestaande presentatie behouden.

## Verzending

De bestaande Google Formulier-velden worden als volgt gevuld:

- **Vers**: de volledige samengestelde verwijzing;
- **Selectie**: één regel per geselecteerd vers in de vorm `Genesis 1:1 — In het begin…`;
- **Suggestie** en **Van**: ongewijzigd.

Het bestaande gedrag bij netwerkfouten blijft behouden: de suggestietekst blijft staan en de verzendknop wordt opnieuw beschikbaar.

## Testdekking

Geautomatiseerde tests controleren:

1. één geselecteerd vers;
2. een aaneengesloten versbereik;
3. niet-aaneengesloten verzen;
4. een selectie over meerdere hoofdstukken;
5. de waarden die naar de velden **Vers** en **Selectie** worden gestuurd;
6. behoud van de bestaande enkelvers-feedback.

## Acceptatiecriteria

- Geen geselecteerd vers ontbreekt in het feedbackvenster of de spreadsheetmelding.
- Ieder geselecteerd vers is zelfstandig herkenbaar aan boek, hoofdstuk en versnummer.
- De versvolgorde volgt de volgorde in de leestekst.
- De bestaande formulierkoppeling en enkelvers-feedback blijven werken.
