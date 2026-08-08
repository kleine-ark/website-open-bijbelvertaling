# Liedtegels met Bijbelgedeelte

## Doel

Op het overzicht van Liederen ziet de lezer bij iedere tegel meteen in welk Bijbelgedeelte het lied staat. De lijst bevat alleen liederen uit de canonieke Bijbelboeken. Op de detailpagina vervalt de afzonderlijke sectie `Vindplaatsen in de hele Bijbel`, omdat de volledige liedtekst daar al met passagekoppen wordt weergegeven.

## Afbakening en nummering

- De liederen uit Henoch, Tobit, het Gezang in de vuuroven, Judith en Jezus Sirach vervallen.
- De bronitems en de vijf bijbehorende gebouwde tekstbundels worden verwijderd, zodat ook rechtstreekse oude adressen deze liedpagina’s niet meer opleveren.
- De lofzang bij het laatste avondmaal vervalt eveneens: de Bijbel meldt dat er gezongen werd, maar levert geen woorden van het lied over. Ook dit bronitem en de bijbehorende tekstbundel worden verwijderd.
- De Psalmen vormen niet langer één verzamelitem. Psalm 1 tot en met Psalm 150 worden 150 afzonderlijke lieditems, ieder met een eigen detailpagina, volledige tekst en liednummer.
- Klaagliederen vormt niet langer één verzamelitem. De vijf hoofdstukken worden vijf afzonderlijke lieditems: `Klaaglied 1` tot en met `Klaaglied 5`.
- Er blijven daardoor 178 genummerde lieditems over. Zij worden doorlopend genummerd als Lied 1 tot en met Lied 178.
- Het lied bij de Schelfzee wordt Lied 1. Psalm 1 wordt Lied 12, Psalm 150 wordt Lied 161, Klaaglied 1 wordt Lied 167 en Klaaglied 5 wordt Lied 171. Het gezang van Mozes en van het Lam wordt Lied 178.
- De badge op het algemene wiki-overzicht verandert van `31 liederen` naar `178 liederen`.

## Gekozen vorm

- Iedere liedtegel toont onder de titel één rustige, goudkleurige regel met de passage.
- Gewone liederen gebruiken het bestaande label uit `tekstpassages`, bijvoorbeeld `Exodus 15:1–18`.
- Meerdere korte passages worden met een middelpunt gescheiden, bijvoorbeeld `Openbaring 5:8–10 · Openbaring 14:2–3`.
- Lange, aaneengesloten hoofdstukbundels worden compact weergegeven, bijvoorbeeld `Hooglied 1–8`.
- Iedere psalmtegel toont als titel `Psalm 1` tot en met `Psalm 150` en als passage dezelfde psalm. De vijf klaagliedtegels tonen `Klaaglied 1` tot en met `Klaaglied 5`, met de overeenkomstige passage uit Klaagliederen.
- De overige titels blijven ongewijzigd. Het liednummer volgt de nieuwe reeks van 1 tot en met 178. Aantallen vindplaatsen keren niet terug.

## Detailpagina

Alleen bij liederen wordt de sectie `Vindplaatsen in de hele Bijbel` niet meer opgebouwd. De volledige tekst, de passagekoppen en de terugkoppeling naar het liederenoverzicht blijven staan. Iedere psalm- en klaagliedpagina toont alleen de volledige tekst van het eigen hoofdstuk; de oude psalmsprongen binnen één verzamelpagina vervallen. Gebedspagina’s behouden hun vindplaatsensectie.

## Techniek

De bestaande renderer in `js/naslag.js` maakt de tegelverwijzing uit `tekstpassages`. De datalaag blijft daarmee de enige bron voor passagegrenzen. Alleen voor lange hoofdstukbundels mag een compact overzichtslabel in het liederenbestand staan, zodat geen fragiele tekstherkenning nodig is. De Psalmen en Klaagliederen worden als afzonderlijke items en tekstbundels opgebouwd; er wordt geen hoofdstuktekst gedupliceerd tussen items. De bouwcontrole verwacht voortaan exact 178 liederen.

## Controle

- De lijst bevat exact 178 lieditems, geen van de vijf uitgesloten apocriefe werken en geen lofzang bij het laatste avondmaal.
- De nummering loopt zonder gaten van Lied 1 tot en met Lied 178.
- Er bestaan precies 150 afzonderlijke psalmitems en vijf afzonderlijke klaaglieditems.
- Alle 178 liedtegels hebben een zichtbare, niet-lege passageverwijzing.
- De verwijzingen voor een enkel gedeelte, meerdere gedeelten en lange hoofdstukbundels worden gecontroleerd.
- Op een lieddetailpagina bestaat geen kop `Vindplaatsen in de hele Bijbel` meer.
- Op een gebedsdetailpagina blijft de vindplaatsensectie aanwezig.
