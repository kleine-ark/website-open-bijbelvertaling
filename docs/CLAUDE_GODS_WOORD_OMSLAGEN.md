# Instructie voor Claude — omslagen van *Gods Woord*

Neem de omslagontwerpen in `images/covers/gods-woord/` mee bij verdere werkzaamheden aan de gedrukte Bijbel *Gods Woord*.

## Bestandsstructuur

Er zijn zes visuele richtingen, elk met en zonder vaste titeltekst:

1. klassiek landschap;
2. paradijstuin;
3. bergen en regenboog;
4. rivier bij zonsopkomst;
5. bloemenweide met olijfbomen;
6. sober nachtblauw linnen met goudfolie.

Elke variant bevat na verwerking:

- `volledige-omslag.png` — achterkant, rug en voorkant als doorlopend beeld;
- `achterkant.png` — losse achterkant;
- `rug.png` — losse rug;
- `voorkant.png` — losse voorkant.

De volledige omslag heeft altijd deze volgorde: **achterkant links, rug in het midden, voorkant rechts**.

## Bronnen verwerken

Voer vanuit de repositoryroot uit:

```powershell
python scripts/prepare_gods_woord_covers.py
```

Van elke variant staat `volledige-omslag.png` in de repository; het script snijdt daar de drie losse
delen uit volgens de eigen ruggrenzen van dat ontwerp. Staat de lokale map met de oorspronkelijk
gegenereerde beelden er nog, dan wordt daar eerst uit gekopieerd. De drie snijdsels worden niet
meegecommit: ze wegen samen ruim dertig megabyte en zijn in een seconde opnieuw te maken. Verander die grenzen niet zonder het volledige beeld visueel te controleren.

## Drukwerkregels

- Beschouw de huidige PNG's als ontwerpbronnen, niet als definitief druk-PDF.
- Vraag vóór definitieve opmaak om netto boekformaat, aantal pagina's, papiersoort, bindwijze en de drukkersspecificaties.
- Bereken de rugbreedte uit de specificatie van de gekozen drukker; schaal de bestaande gegenereerde rug niet blindelings.
- Bouw daarna een nieuw document op 300 dpi met minimaal 3 mm afloop rondom en voldoende veiligheidsmarge.
- Plaats bij voorkeur de versie **zonder tekst** en zet `GODS WOORD` en `OPEN VERTALING` opnieuw als echte vector-/lettertypografie. Gebruik de versie met tekst alleen als visuele referentie.
- Voeg achterflaptekst, ISBN en barcode pas toe als de definitieve inhoud beschikbaar is.
- Laat de drukker het vereiste CMYK-profiel bepalen en lever pas daarna een PDF/X-bestand aan.
- Houd titel, rugtitel, barcode en belangrijke ornamenten buiten afloop en vouw-/rilzones.

## Vaste naamgeving

De hoofdnaam op het boek is **Gods Woord**. De editieaanduiding is **Open Vertaling**. Gebruik geen alternatieve titel zonder expliciete opdracht.
