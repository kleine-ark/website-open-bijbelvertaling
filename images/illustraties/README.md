# Illustraties bij de drukversie

De drukversie kan bij het begin van een hoofdstuk een plaat op de onderste
helft van het blad zetten. De platen staan hier.

## Bestandsnamen

`{boek-id}_{hoofdstuk}.jpg` — bijvoorbeeld `genesis_1.jpg`, `lukas_15.jpg`.
Het boek-id is het `id`-veld uit `data/books.json`. Ook `.png` en `.webp`
worden herkend.

## Lijst bijwerken

De browser leest `data/illustraties.json`; die wordt niet met de hand
onderhouden maar uit deze map afgeleid:

    python scripts/build_illustraties.py

Zolang een hoofdstuk hier geen bestand heeft, blijft de plaat weg en houdt
het blad zijn volle hoogte.

## Rechten

Het werk van Jan van 't Hoff is niet publiek domein: de rest van deze
uitgave is CC0, de platen zijn dat niet. Zet hier alleen bestanden neer
waarvoor de rechten geregeld zijn, en houd ze buiten de downloads en de
EPUB tenzij die toestemming dat toelaat.
