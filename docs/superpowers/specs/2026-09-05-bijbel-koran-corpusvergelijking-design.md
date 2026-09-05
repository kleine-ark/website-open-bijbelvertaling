# Bijbel–Koran-corpusvergelijking

**Datum:** 5 september 2026  
**Status:** goedgekeurd ontwerp  
**Bereik:** uitsluitend lokaal analysegereedschap

## Doel

Maak een lokale, reproduceerbare vergelijking tussen de Bijbel en de Koran. De vergelijking telt niet alleen de omvang van beide corpora, maar ook gecontroleerde categorieën zoals personen, plaatsen, materialen, dieren en planten. Iedere uitkomst vermeldt de gebruikte brontekst, corpusomvang, meeteenheid en dekkingsstatus.

De pagina is een onderzoeksinstrument. Zij wordt niet opgenomen in de openbare navigatie, sitemap, serviceworker of productie-uitvoer zolang de gebruiker daar niet afzonderlijk opdracht toe geeft.

## Corpuskeuze

### Bijbel

De gebruiker kan de Bijbelomvang kiezen:

1. **Canoniek** — de 66 canonieke boeken; dit is de standaard.
2. **Canoniek + apocrief** — canonieke en apocriefe boeken.
3. **Volledige Open Vertaling** — canoniek, apocrief en beschikbare Ethiopische boeken.

Een boek telt alleen mee wanneer de gekozen grondtekst daadwerkelijk beschikbaar is. Ontbrekende of onvolledige grondtekst wordt zichtbaar gerapporteerd en nooit stilzwijgend vervangen door een Nederlandse vertaling.

De oorspronkelijke talen zijn Hebreeuws en Aramees voor het Oude Testament, Grieks voor het Nieuwe Testament en de beschikbare oorspronkelijke of vroegste brontekst per apocrief of Ethiopisch boek. De uitvoer vermeldt per deelcorpus welke bron concreet is gebruikt.

### Koran

De Arabische bron is de **Tanzil Uthmani-tekst**, overeenkomstig Open Koran Weergave. De Koran omvat alle 114 soera's. De bronversie en importdatum worden in de gegenereerde gegevens vastgelegd.

Open Koran levert daarnaast gecontroleerde woord-, lemma-, wortel- en entiteitsgegevens. Die gegevens mogen als bron voor de lokale momentopname dienen, maar hun huidige catalogus is nog in uitbreiding. Dat onderscheid wordt in de interface zichtbaar gehouden.

## Gelijke meeteenheden

Iedere categorie toont waar mogelijk drie verschillende cijfers:

- **Entiteiten:** het aantal verschillende gecontroleerde begrippen, bijvoorbeeld `goud` of `Jeruzalem`.
- **Tekstplaatsen:** het aantal unieke Bijbelverzen of Koranverzen waarin een entiteit voorkomt.
- **Vermeldingen:** het aantal afzonderlijke voorkomens in de grondtekst.

Deze cijfers mogen niet tot één getal worden samengevoegd. Zo blijft zichtbaar of een corpus veel verschillende materialen kent of een kleiner aantal materialen zeer vaak noemt.

## Woordtelling

De woordtelling gebruikt uitsluitend de oorspronkelijke talen. De basiseenheid is het orthografische woordtoken zoals dat in de aangewezen bron is opgeslagen.

De teller:

- negeert leestekens, versmarkeringen, HTML en redactionele metadata;
- behoudt diakritische tekens in de bronweergave, maar normaliseert ze niet tot extra woorden;
- splitst voor- en achtervoegsels niet kunstmatig af wanneer de bron ze als één token opslaat;
- telt de basmala alleen waar deze in de gekozen Tanzil-versindeling als teksttoken voorkomt;
- rapporteert per taal zowel totale tokens als unieke genormaliseerde woordvormen;
- documenteert afwijkende tokenisatie per bron in de uitvoermetadata.

Omdat Hebreeuwse en Arabische clitica anders worden geschreven, presenteert de pagina de telling als brongebonden orthografische woordtelling en niet als absoluut taalkundig aantal woorden.

## Vergelijkingscategorieën

De eerste versie bevat:

1. corpuseenheden: boeken of soera's, hoofdstukken en verzen;
2. woordtokens en unieke woordvormen;
3. personen en profeten;
4. volken en geloofsgroepen;
5. plaatsen en geografie;
6. geschriften;
7. materialen en stoffen;
8. dieren;
9. planten en vruchten;
10. eten en drinken;
11. kleding en voorwerpen;
12. natuur en hemellichamen;
13. tijd, getallen en maten.

Categorieën krijgen stabiele, taalneutrale concept-ID's. Bronwoorden en Nederlandse labels zijn aliassen van zo'n concept en worden niet gebruikt als primaire sleutel. Alleen daardoor zijn bijvoorbeeld Hebreeuws, Grieks en Arabisch `goud` onderling vergelijkbaar zonder de grondtekst te vernederlandsen.

## Bronnen en dekking

De Bijbelse categoriegegevens worden ontleend aan de bestaande corpusbrede naslagbestanden, waaronder materialen, dieren, bomen en planten, personen en geografie. De Koran-categorieën worden ontleend aan de gecontroleerde catalogus van Open Koran.

Elk resultaat krijgt een van deze statussen:

- **volledig geteld:** afgeleid uit het volledige geselecteerde grondtekstcorpus;
- **gecontroleerde catalogus:** exact binnen de catalogus, maar niet noodzakelijk volledig voor het corpus;
- **gedeeltelijk:** een of meer vereiste bronnen ontbreken;
- **niet vergelijkbaar:** definities of dekking zijn te verschillend voor een verantwoord cijfer.

De interface toont de status naast het cijfer en biedt een toelichting met bronbestand, bronversie, bouwdatum en eventuele ontbrekende boeken of categorieën. Een onvolledige catalogus mag nooit worden gepresenteerd als volledige inventarisatie.

## Architectuur

### Bouwstap

Een nieuw lokaal bouwscript leest twee adapters:

- een Bijbeladapter voor grondtekstbestanden en bestaande naslag-JSON;
- een Koranadapter voor de lokale Tanzil/Open Koran-momentopname.

Beide adapters leveren hetzelfde interne schema. De aggregator genereert één afgeleid bestand, bijvoorbeeld `data/lokaal/corpusvergelijking.json`. Het bestand bevat samenvattingen, ranglijsten, bronmetadata, dekking en waarschuwingen. De browser voert geen corpusanalyse uit en haalt tijdens gebruik niets van een externe website op.

### Lokale bronmomentopname

De geïmporteerde Koran-data wordt lokaal en versieerbaar opgeslagen met:

- bron-URL en bronnaam;
- licentie- en attributiegegevens;
- importdatum en, indien beschikbaar, bronversie of checksum;
- de gebruikte Arabische vers- en woord-ID's;
- gecontroleerde entiteiten en verwijzingen.

De import is een expliciete ontwikkelstap. De analysepagina blijft daardoor snel, reproduceerbaar en bruikbaar zonder netwerkverbinding.

### Presentatie

`corpusvergelijking.html` toont:

- een corpuskeuze voor de Bijbel;
- overzichtskaarten met kerncijfers;
- horizontale vergelijkingsbalken met zowel absolute aantallen als aantallen per 10.000 woordtokens;
- tabellen per categorie met entiteiten, tekstplaatsen en vermeldingen;
- bron- en dekkingsbadges;
- een uitklapbare methodieksectie.

Normalisatie per 10.000 woorden staat naast, niet in plaats van, absolute aantallen. Dat voorkomt dat het veel grotere corpus automatisch bij iedere categorie 'wint'.

## Fouten en validatie

De bouw stopt met een duidelijke fout bij ongeldige bron-ID's, dubbele concept-ID's, verwijzingen naar ontbrekende verzen of onbekende corpusboeken. Ontbrekende optionele categorieën leiden tot een zichtbare dekkingswaarschuwing, niet tot een verzonnen nul.

Geautomatiseerde controles bewaken ten minste:

- 114 Koran-soera's en de verwachte versstructuur;
- de boekenlijst van iedere Bijbelomvang;
- deterministische woordtellingen;
- onderscheid tussen entiteiten, tekstplaatsen en vermeldingen;
- geldige verwijzingen naar beide corpora;
- stabiele resultaten bij herhaald bouwen;
- afwezigheid van de lokale pagina in publieke navigatie en sitemap.

## Niet in deze eerste versie

- inhoudelijke conclusies over waarheid, inspiratie of superioriteit;
- automatische semantische gelijkstelling zonder gecontroleerde concept-ID;
- vergelijking op basis van Nederlandse vertalingen;
- live scraping wanneer de pagina wordt geopend;
- publicatie op de productiewebsite;
- hadithvergelijking.

## Herkomst

- Koran-grondtekst: Tanzil Uthmani, zoals vermeld door Open Koran Weergave.
- Koran-woord- en categoriegegevens: Open Koran Weergave, met de door die site opgegeven dekkingsbeperkingen.
- Bijbeldata: de bestaande grondtekst- en naslagbronnen van Open Vertaling, beperkt tot de gekozen corpusomvang.

