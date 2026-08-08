# Bewegende wiki-logo's voor Liederen en Gebeden

## Doel

De tegels Liederen en Gebeden krijgen dezelfde handgetekende beeldtaal en subtiele bewegingslaag als de overige wiki-tegels.

## Visueel ontwerp

- **Liederen:** een handgetekende antieke lier op warm perkament. Een zachte goudglans loopt langzaam over de snaren.
- **Gebeden:** een handgetekende bronzen wierookschaal op warm perkament. De rook drijft nauwelijks zichtbaar en de kolen krijgen een zeer zachte gloed.
- Beide illustraties gebruiken fijne marineblauwe inktlijnen, gedempt goud en terughoudende aquareltextuur. De beeldbronnen staan in `images/wiki/bronnen/`.
- Beide animaties zijn 600 × 300 pixels, duren vijf seconden en sluiten naadloos aan op het eerste beeld.
- Geen tekst, camerabeweging, snelle beweging of nieuwe beeldelementen.

## Integratie

`wiki-overzicht.html` gebruikt per tegel een `<picture>`: de bewegende WebP voor bezoekers die beweging toestaan, en een SVG-verwijzing naar dezelfde handgetekende bron als stil alternatief bij `prefers-reduced-motion` of ontbrekende animatie-ondersteuning. De cacheversie van de site wordt verhoogd zodat oudere tegelbeelden worden vervangen.

## Controle

Een gerichte test bewaakt bestandsnamen, afmetingen, meerdere frames, een lusduur van 4–6 seconden, een oneindige loop en de twee `<picture>`-koppelingen.
