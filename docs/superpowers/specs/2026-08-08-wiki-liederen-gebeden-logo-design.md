# Bewegende wiki-logo's voor Liederen en Gebeden

## Doel

De tegels Liederen en Gebeden krijgen dezelfde handgetekende beeldtaal en subtiele bewegingslaag als de overige wiki-tegels.

## Visueel ontwerp

- **Liederen:** een handgetekende Bijbelse muzikant die bij zonsopgang op een houten lier speelt. Een zachte goudglans loopt langzaam door het ochtendlicht en over de snaren.
- **Gebeden:** een handgetekende geknielde figuur onder een olijfboom, met de heuvels en stad in de verte. Alleen het ochtendlicht ademt bijna onmerkbaar.
- Beide illustraties gebruiken fijne marineblauwe inktlijnen, gedempt goud en terughoudende aquareltextuur. De beeldbronnen staan in `images/wiki/bronnen/`.
- Beide animaties zijn 600 × 300 pixels, duren vijf seconden en sluiten naadloos aan op het eerste beeld.
- Geen tekst, camerabeweging, snelle beweging of nieuwe beeldelementen.

## Integratie

`wiki-overzicht.html` gebruikt per tegel een `<picture>`: de bewegende WebP voor bezoekers die beweging toestaan, en de echte gegenereerde rasterbron als stil alternatief bij `prefers-reduced-motion` of ontbrekende animatie-ondersteuning. Er is geen SVG-route voor deze twee tegels. De service worker haalt deze vier rasterbestanden online altijd vers op, zodat oudere tegelbeelden worden vervangen.

## Controle

Een gerichte test bewaakt bestandsnamen, afmetingen, meerdere frames, een lusduur van 4–6 seconden, een oneindige loop en de twee `<picture>`-koppelingen.
