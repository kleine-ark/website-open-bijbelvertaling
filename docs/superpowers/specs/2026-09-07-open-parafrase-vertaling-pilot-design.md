# Open Parafrase Vertaling — pilotontwerp

## Doel

De Open Parafrase Vertaling (OPV) wordt een zelfstandige, zeer leesbare Nederlandse Bijbeleditie naast de tekstgetrouwe Open Vertaling. De eerste pilot omvat Genesis 1–5 en Johannes 1–5: 352 verzen in totaal.

De hoofdtekst moet direct begrijpelijk zijn voor een zestienjarige HAVO-lezer en prettig doorlezen als een boek. De tekst blijft tegelijk controleerbaar: iedere formulering is herleidbaar tot de Nederlandse basistekst en kan bij twijfel worden getoetst aan de Open Vertaling en de grondtekst.

## Positionering

De stijl combineert:

- gewone woorden, korte zinnen en expliciete verbanden;
- de natuurlijke vertelstroom en gedachte-voor-gedachtebenadering van een verhalende parafrase.

De OPV neemt geen formuleringen over uit moderne auteursrechtelijk beschermde Bijbeledities. Die edities dienen uitsluitend als algemene stijlcategorie. Iedere OPV-formulering wordt zelfstandig gemaakt vanuit de Statenvertaling.

## Bronnenhiërarchie

1. De Statenvertaling 1888 is de directe Nederlandse basistekst.
2. De Statenvertaling 1637 bewaart de historische formulering en kanttekeningen.
3. De Open Vertaling is een controlebron voor onderzochte moderniseringen, tekstvarianten en terminologische keuzes.
4. De Hebreeuwse of Griekse grondtekst wordt geraadpleegd bij dubbelzinnigheid, woordspel, tekstvariant of een inhoudelijk risicovolle parafrase.

De Statenvertaling is een vertaling en geen handschrift. Handschriftinformatie blijft een afzonderlijke documentatielaag en bepaalt niet automatisch de OPV-formulering.

## Redactionele rangorde

Bij iedere keuze geldt deze volgorde:

1. De betekenis direct begrijpelijk overbrengen.
2. Natuurlijk en meeslepend Nederlands schrijven.
3. Alle inhoudelijke onderdelen van de basistekst bewaren.
4. Pas daarna traditionele woorden, woordvolgorde en stijlfiguren behouden.

Leesbaarheid gaat dus vóór letterlijke zinsbouw. Dat geeft geen toestemming om nieuwe gebeurtenissen, emoties, motieven, leerstellige conclusies of historische verklaringen aan de tekst toe te voegen.

## Stijlregels

- Gebruik algemeen bekende, hedendaagse woorden.
- Schrijf korte, actieve zinnen met bij voorkeur één hoofdgedachte en hoogstens één bijzin.
- Maak steeds duidelijk wie spreekt, handelt of met een voornaamwoord bedoeld wordt.
- Maak een impliciet verband expliciet wanneer dit nodig is om de bestaande betekenis te begrijpen.
- Splits, combineer en herschik zinnen wanneer dat de leesbaarheid verhoogt.
- Behoud functionele herhaling, spanningsopbouw en ritme.
- Verduidelijk moeilijke beeldspraak. Behoud centrale Bijbelse beelden wanneer verlies van het beeld ook inhoudsverlies geeft; koppel dan uitleg als tweede laag.
- Schrijf dialogen natuurlijk en direct. God en Jezus worden met `U` en `Uw` aangesproken.
- Gebruik `HEERE` voor de Godsnaam in het Oude Testament.
- Gebruik eerbiedshoofdletters voor God, Jezus en de Heilige Geest: `Hij`, `Hem`, `Zijn`, `U` en `Uw`. Verwijzingen naar mensen blijven klein.
- Behoud herkenbare eigennamen en kernnamen zoals God, Jezus, Christus, Messias en Heilige Geest.

## Bijbelse begrippen: twee lagen

De hoofdtekst geeft moeilijke begrippen in gewone taal weer. Het traditionele of theologische begrip blijft als gestructureerde metadata aan het precieze tekstsegment gekoppeld. Zo kan `gerechtvaardigd worden` in de hoofdtekst worden omschreven als door God als rechtvaardig worden aangenomen, terwijl het begrip `rechtvaardiging` gekoppeld blijft.

Identiteitsbepalende begrippen blijven in de hoofdtekst staan wanneer omschrijven de inhoud versmalt of vervormt. Begrippenmetadata moet later woordenboek-, zoek- en vergelijkingsfuncties kunnen voeden zonder de rustige leesweergave te belasten.

## Leesstructuur

- De OPV wordt gepresenteerd in doorlopende alinea’s en korte betekenisblokken.
- Informatieve tussenkoppen benoemen de kern van een passage zonder interpretatieve conclusie.
- Versnummers blijven als subtiele ankers beschikbaar voor navigatie, delen, vergelijken en broncontrole.
- Een Nederlandse zin mag over een versgrens doorlopen wanneer dat natuurlijker leest. De technische verskoppeling blijft behouden.
- Directe rede krijgt universele citatiemetadata met spreker, aangesprokene en segmentbereik. De globale citatie-instelling bepaalt de zichtbare opmaak.

## Zelfstandige gegevenslaag

De OPV wordt niet als extra veld aan de bestaande hoofdstukbestanden toegevoegd. De editie krijgt een eigen, versieerbare gegevenslaag:

```text
data/edities/opv/
  manifest.json
  chapters/genesis/1.json … 5.json
  chapters/johannes/1.json … 5.json
```

De centrale editiemetadata verwijst naar deze map, zodat de bestaande primaire en parallelle-editiebediening de OPV kan laden.

### Manifest

Het manifest legt minimaal editiecode `nl-opv`, naam, taal, richting, pilotstatus, versie, doelgroep, bronnenbeleid, geplande hoofdstukken, gepubliceerde hoofdstukken en redactionele statussen vast. `hoofdstukken` beschrijft de geplande pilotdekking; `gepubliceerdeHoofdstukken` is in zowel het centrale register als het OPV-manifest verplicht en bevat uitsluitend de bestanden die werkelijk onder `dataRoot` staan. Wanneer een hoofdstuk wordt toegevoegd, worden bestand en beide publicatielijsten atomair bijgewerkt.

### Hoofdstuk

Een hoofdstuk bevat minimaal:

- editiecode, boekcode, hoofdstuknummer en hoofdstukkop;
- geordende betekenisblokken met passagekop en versbereik;
- ieder vers exact eenmaal;
- per vers platte leesbare tekst en optionele veilige HTML;
- bronverwijzingen naar het bestaande SV-/OV-hoofdstukbestand;
- stabiele segment-id’s voor begrippen, spraak en latere grondtekstkoppeling;
- begrippenmetadata, citatiemetadata en reviewstatus.

Bronkoppelingen gebruiken stabiele segment-id’s en bronfrases of grondtekstindices. Alleen tekenposities gebruiken is onvoldoende, omdat een redactionele wijziging die posities verschuift.

De opgeslagen inhouds- en bronhash maken zichtbaar wanneer een eerdere beoordeling door een tekst- of bronwijziging verouderd is.

## Status- en reviewmodel

Iedere passage doorloopt vier onafhankelijke statussen:

1. `concept`: zelfstandig geparafraseerd vanuit de Statenvertaling;
2. `bron_gecontroleerd`: betekenis, weglatingen en toevoegingen gecontroleerd;
3. `taal_gecontroleerd`: gewone taal, ritme en verwijzingen gecontroleerd;
4. `definitief`: inhoudelijke en redactionele controle afgerond.

Een redacteur keurt zijn eigen tekst niet als definitief goed. Risicopassages krijgen een expliciet besluit in het besluitregister. Voor de pilot gelden onder meer Genesis 1:2, 1:26–28, 2:18, 3:15, 4:7, Johannes 1:1–18, 3:3–8, 3:16–18, 4:10–24 en 5:3–4 als risicopassages.

## Pilotworkflow

1. Bouw de gegevensstructuur, validator en een verticale slice met Genesis 1 en Johannes 1.
2. Controleer de slice in de lezer als primaire en parallelle editie.
3. Kalibreer de stijl op inhoud, gewone taal en vertelritme.
4. Werk Genesis 2–5 en Johannes 2–5 uit.
5. Voer broncontrole, taalcontrole en technische corpuscontrole uit.
6. Publiceer de pilot uitsluitend met `Proefeditie — in bewerking` zolang niet alle statussen zijn afgerond.

## Technische acceptatiecriteria

- De pilot bevat exact 138 verzen voor Genesis 1–5 en 214 verzen voor Johannes 1–5.
- Johannes 1 volgt de versificatie van deze repository en telt daarom 52 verzen; die bewuste afwijking wordt in het besluitregister vastgelegd.
- Geen vers ontbreekt, komt dubbel voor of is leeg.
- Boek- en hoofdstuknummers komen overeen met de canonieke gegevens.
- Iedere versregel heeft een geldige bronverwijzing naar het corresponderende hoofdstuk.
- Iedere passage heeft een kop, versbereik en reviewstatus.
- Segment-id’s zijn binnen een hoofdstuk uniek en metadata verwijst naar bestaande segmenten.
- Citatiebereiken verwijzen naar bestaande segmenten en benoemen ten minste het type spreker.
- De editie is selecteerbaar als primaire tekst en als parallelle editie.
- Niet-beschikbare hoofdstukken tonen expliciet dat de OPV daar nog niet beschikbaar is; er is geen stille terugval naar de Open Vertaling.
- Bestaande edities en opgeslagen voorkeuren blijven werken.
- Geautomatiseerde validatie en relevante browsertests slagen.

## Buiten de pilot

De rest van de Bijbel, audio, exports en een volledig nieuwe Strong-koppeling vallen buiten deze eerste pilot. De gegevensstructuur moet die uitbreidingen wel mogelijk maken. Bestaande Strong-koppelingen worden niet automatisch op geparafraseerde woorden geplakt; daarvoor is later afzonderlijke inhoudelijke uitlijning nodig.
