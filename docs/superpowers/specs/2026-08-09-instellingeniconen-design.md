# Ontwerp instellingeniconen

## Doel

De aangeleverde goudkleurige lijniconen worden de vaste visuele signatuur van de hoofdinstellingen in het bestaande tabbladpaneel. De iconen verduidelijken de bediening zonder iedere secundaire schakelaar visueel even zwaar te maken.

## Visuele toepassing

- Gebruik uitsluitend de schaalbare SVG-bestanden op de website.
- Bewaar ze onder `images/iconen/instellingen/` met hun bestaande Nederlandse namen.
- Toon iconen op 28 × 28 pixels in een vaste kolom van 38 pixels.
- Laat de oorspronkelijke goudkleur `#C9912E` staan; die blijft herkenbaar in licht en donker thema.
- Gebruik iconen bij Thema, Lettertype, Tekstgrootte, Regelafstand, Versnummers, Godsnaam, Voorkeurseditie en Voorleesstem.
- Houd overige schakelaars tekstueel en rustig.

## Gedrag

- Lettertype krijgt de keuzes Klassiek en Rustig; Klassiek gebruikt EB Garamond en Rustig Fira Sans.
- Regelafstand krijgt Compact, Normaal en Ruim.
- Beide voorkeuren worden opgeslagen in dezelfde `sv2026_vertaalopties`-toestand als de andere globale leesvoorkeuren.
- De voorkeuren gelden direct voor de leestekst en blijven na herladen actief.
- Bestaande thema-, zoom-, versnummer-, editie- en audiobediening behoudt haar huidige gedrag.

## Toegankelijkheid en responsiviteit

- Iconen zijn decoratief en krijgen een lege `alt` plus `aria-hidden="true"`.
- Labels blijven volledig in tekst aanwezig.
- Op mobiel blijven icoon, label en bediening binnen één leesbare rij; op zeer smalle schermen mag de bediening onder het label vallen.
- Focusmarkering en toetsenbordbediening blijven ongewijzigd beschikbaar.

## Verificatie

- Browsertests controleren aanwezigheid van alle acht iconen.
- Browsertests controleren toepassing en opslag van lettertype en regelafstand.
- Bestaande optiespaneeltests bewaken tabbladen, mobiel gedrag, thema, zoom en voorkeurspersistentie.
