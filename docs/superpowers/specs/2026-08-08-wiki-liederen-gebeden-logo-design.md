# Bewegende wiki-logo's voor Liederen en Gebeden

## Doel

De tegels Liederen en Gebeden krijgen dezelfde subtiele bewegingslaag als de overige wiki-tegels, zonder de bestaande goedgekeurde illustraties opnieuw te ontwerpen.

## Visueel ontwerp

- **Liederen:** de vijf liersnaren bewegen nauwelijks zichtbaar rond hun rustpositie; de twee muzieknoten deinen rustig omhoog en omlaag. De lier, kleuren en compositie blijven gelijk aan `images/wiki/liederen.svg`.
- **Gebeden:** de drie wierooklijnen stijgen langzaam en vloeiend op; de drie gouden kolen krijgen een zeer zachte gloed. Altaar, kleuren en compositie blijven gelijk aan `images/wiki/gebeden.svg`.
- Beide animaties zijn 600 × 300 pixels, duren vijf seconden en sluiten naadloos aan op het eerste beeld.
- Geen tekst, camerabeweging, snelle beweging of nieuwe beeldelementen.

## Integratie

`wiki-overzicht.html` gebruikt per tegel een `<picture>`: de bewegende WebP voor bezoekers die beweging toestaan, en de bestaande SVG als stil en scherp alternatief bij `prefers-reduced-motion` of ontbrekende WebP-ondersteuning.

## Controle

Een gerichte test bewaakt bestandsnamen, afmetingen, meerdere frames, een lusduur van 4–6 seconden, een oneindige loop en de twee `<picture>`-koppelingen.
