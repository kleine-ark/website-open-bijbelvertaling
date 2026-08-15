# Wijn en Top 10 voor onderwerpen

## Doel

Elke onderwerpdetailpagina opent met een compacte, herkenbare Top 10 van de belangrijkste teksten. Daarnaast komt er een nieuw onderwerp **Wijn in de Bijbel**, met alle letterlijke voorkomens van `wijn` in de beschikbare Bijbeltekst.

## Gebruikerservaring

- Een onderwerpdetail toont na titel, omschrijving en totalen eerst **Top 10 teksten**.
- De topselectie gebruikt dezelfde universele OV-citatiecomponent als de gewone onderwerpteksten; daardoor volgen taal, Godsnaam, citatieopmaak en andere globale leesinstellingen automatisch.
- Daarna volgt de bestaande volledige tekstlijst, met boekfilter, contextknoppen en `+ meer teksten`.
- Alle onderwerpen krijgen een Top 10 zonder dat elke individuele pagina een eigen template nodig heeft.

## Data en rangorde

- De bestaande velden `verzen[].rang` blijven leidend: rang 1, dan 2, dan 3; binnen een gelijke rang staat de canonieke boek-, hoofdstuk- en versvolgorde.
- Optioneel kan een tag `topTien` bevatten: een geordende lijst met maximaal tien verwijzingen. Als dat veld bestaat, gebruikt de UI die expliciete, redactioneel gekozen selectie. Zonder veld wordt de hierboven beschreven algemene rangorde gebruikt.
- Voor `wijn` wordt `topTien` expliciet vastgesteld; `verzen` bevat alle verzen met het zelfstandige woord `wijn`, inclusief hoofdlettervariant, zonder afgeleiden als `wijnstok` of `wijnpers` wanneer `wijn` niet zelfstandig in de tekst staat.

## Afbakening

Dit voegt geen nieuwe losse HTML-pagina per onderwerp toe: `onderwerpen.html#tag=wijn` is de eigen deelbare pagina. Het wijzigt geen bestaande onderwerpinhoud, behalve het uniforme Top 10-blok.

## Testbaarheid

- Een contracttest bewaakt de data voor de tag `wijn`, inclusief de verwachte kernteksten en dekking van alle letterlijke voorkomens.
- Een browser-/brontest bewaakt dat de detailweergave voor ieder onderwerp één Top 10-sectie rendert via `OVTekstweergave`.
