# Ontwerp: geaccentueerde sectiekoppen in het optiescherm

## Doel

De volledige kopregel van ieder inklapbaar instellingenblok moet visueel herkenbaar zijn, zonder op een primaire actieknop te lijken.

## Vormgeving

- Licht thema: een lichtblauw vlak over de volledige breedte van de kopregel, met donkerblauwe tekst en een subtiele blauwe rand.
- Donker thema: een donkerblauw accentvlak over de volledige kopregel, met helder lichte tekst en voldoende contrast.
- Het plus- of minteken blijft goud als vast interactieaccent.
- De afgeronde buitenvorm van het bestaande instellingenblok blijft behouden.
- Alleen de kopregel krijgt kleur; de geopende inhoud behoudt de bestaande neutrale achtergrond.

## Gedrag en toegankelijkheid

Het in- en uitklapgedrag verandert niet. Tekst en interactieaccenten voldoen in beide thema's minimaal aan WCAG AA-contrast. Een browsertest controleert de berekende kleuren en het contrast van de sectiekoppen.

## Afbakening

Deze wijziging raakt uitsluitend de visuele presentatie van `.options-category > summary` en verandert geen instellingen, opslag, bediening of mobiele schermstructuur.
