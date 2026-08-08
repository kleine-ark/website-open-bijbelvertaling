# Versie en statistieken v0.30.3

## Doel

Publiceer de afgeronde menselijke controle van Prediker als een afzonderlijke websitepatch en laat alle zichtbare voortgangscijfers uit dezelfde bron komen.

## Afbakening

- Verhoog de websiteversie van `v0.30.2` naar `v0.30.3`.
- Voeg bovenaan het changelog een vermelding toe voor de verwerking van de opmerkingen bij Prediker, de menselijke reviewstatus en de opnieuw opgebouwde statistieken en downloads.
- Genereer `data/stats.json` opnieuw met versie `v0.30.3` en datum `8 augustus 2026`.
- Verhoog de serviceworker-versie naar `v0.30.3`, zodat bezoekers de nieuwe tekst en statistieken ontvangen.
- Laat de zelfstandige desktop-appversie `0.21.0` ongewijzigd; dit is geen desktoprelease.

## Bron van waarheid

`data/verified-chapters.json` bepaalt welke hoofdstukken door een mens zijn nagelezen. Het statistiekenscript leidt daaruit de gecontroleerde boeken, hoofdstukken en verzen af. De website leest versie en voortgang vervolgens uit `data/stats.json`.

## Controle

- Controleer dat changelog, statistieken en serviceworker allemaal `v0.30.3` noemen.
- Bouw statistieken en downloads opnieuw op.
- Draai de relevante tests voor reviewstatus, statistieken en downloads.
- Controleer dat de desktopversie niet is gewijzigd.
