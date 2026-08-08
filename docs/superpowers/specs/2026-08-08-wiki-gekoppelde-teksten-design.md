# Gekoppelde Bijbelteksten op wiki-naslagpagina's

**Datum:** 8 augustus 2026
**Status:** vastgesteld, nog niet geïmplementeerd

## Doel

De pagina's Tijdsaanduidingen, Materialen, Dieren en Bomen & planten tonen nu
alleen vindplaatsen of compacte verwijzingsknoppen. De lezer moet daardoor naar
de leesweergave vertrekken om vast te stellen wat er op een vindplaats staat.

Op iedere relevante naslagdetailpagina komen de gekoppelde verzen direct onder
de uitleg te staan. De interactie volgt Onderwerpen: de volledige reeks
gekoppelde vindplaatsen is zichtbaar en bij ieder vers toont een kleine `+`
maximaal twee voorafgaande en twee volgende verzen. Met `−` keert het blok terug
naar alleen de gekoppelde tekst.

## Reikwijdte

- `materialen.html` en alle detailpagina's uit `data/naslag-materialen.json`;
- `dieren.html` en alle detailpagina's uit `data/naslag-dieren.json`;
- `bomen-planten.html` en alle detailpagina's uit
  `data/naslag-bomen-planten.json`;
- de inhoudelijke tijdsgroepen op `tijdsaanduidingen.html`: daguren, nachturen,
  nachtwaken en andere tijdsaanduidingen;
- dezelfde letterlijke `text2026`-bron en contextbediening als Onderwerpen.

Liederen en Gebeden gebruiken hun afzonderlijk vastgestelde volledige
passageweergave en vallen niet onder deze uitbreiding.

## Weergave en interactie

### Materialen, dieren en bomen & planten

Op een detailpagina blijft de bestaande volgorde van teruglink, titel en
beschrijving staan. De huidige vindplaatschips worden vervangen door rustige
versblokken. Elk blok bevat:

1. een klikbare referentie naar het betreffende hoofdstuk in de leesweergave;
2. de letterlijke gekoppelde verstekst;
3. een knop `+` met toegankelijke naam `Meer context eromheen`;
4. na uitklappen maximaal twee bestaande verzen vóór en twee erna;
5. een knop `−` om de context weer in te klappen.

Alle gekoppelde vindplaatsen worden in de data-volgorde getoond. Er komt geen
aparte lijstknop die een verborgen restlijst opent.

### Tijdsaanduidingen

De bestaande tabellen en toelichtingen blijven intact. Onder iedere rij of
inhoudelijke groep met vindplaatsen komt een aanvullende tabelrij over de volle
breedte. Daarin staan dezelfde versblokken en contextknoppen.

De huidige pagina noemt bij grotere aantallen slechts enkele voorbeelden plus
een telling. De nieuwe gestructureerde tijdsdata bevat alle werkelijke
vindplaatsen; de getoonde telling wordt daaruit afgeleid. Rijen zonder
vindplaatsen krijgen geen leeg tekstvak.

Op een smal scherm valt de aanvullende rij als een gewoon blok onder de
betreffende tijdsaanduiding, zodat de relatie tussen uitleg en teksten zichtbaar
blijft.

## Techniek

Een nieuw gedeeld script `js/gekoppelde-teksten.js` bevat de renderer en de
contextbediening. Zowel `js/naslag.js` als `tijdsaanduidingen.html` gebruiken die
renderer. Onderwerpen blijft bij deze wijziging functioneel gelijk; het nieuwe
script neemt zijn bewezen gedrag als uitgangspunt zonder de hele Onderwerpen-
pagina in deze eerste stap te verbouwen.

De renderer gebruikt `window.OSV.cite(ref, {link: false})` uit `embed.js`. Dat
garandeert dat de wiki steeds de actuele Open Vertaling uit
`data/<boek>/<hoofdstuk>.json` toont en geen tweede tekstkopie introduceert.

De drie naslagdatabestanden bewaren hun bestaande compacte referentievorm. De
renderer normaliseert bijvoorbeeld `12:6` met het bijbehorende bronboek naar
een volledige OSV-referentie. Voor Tijdsaanduidingen komt één apart
gestructureerd gegevensbestand met volledige boek-id's en versreferenties,
omdat de statische voorbeeldtekst nu niet alle vindplaatsen bevat.

## Laden en foutafhandeling

De titel en referentie worden direct gerenderd. De verstekst wordt pas geladen
wanneer het blok het zichtbare deel van de pagina nadert, met
`IntersectionObserver`. Op oudere of afwijkende browsers zonder die API worden
de teksten direct geladen.

Een mislukte tekstaanvraag toont bij alleen dat blok de melding
`De tekst kon niet geladen worden.` De referentie blijft klikbaar en andere
blokken blijven laden. Een tweede klik of een fout in één contextvers mag het
oorspronkelijke gekoppelde vers niet verwijderen.

## Toegankelijkheid en vormgeving

- `+` en `−` zijn echte knoppen met een zichtbare toetsenbordfocus;
- de toegankelijke naam beschrijft de actie, niet alleen het teken;
- dynamisch geladen context wordt in hetzelfde tekstblok toegevoegd zonder de
  leespositie te verplaatsen;
- kleuren, typografie, randen en verticale afstand volgen de bestaande
  Onderwerpen- en wiki-vormtaal;
- donkere modus en de mobiele leesmarge blijven behouden;
- de implementatie blijft geschikt voor iPadOS 15.4.

## Tests

1. ieder naslagitem rendert evenveel hoofdblokken als er `verzen` zijn;
2. korte en boekbrede referentievormen leiden naar het juiste hoofdstuk;
3. een hoofdvers gebruikt exact `text2026` uit de hoofdstukdata;
4. `+` voegt maximaal twee bestaande verzen vóór en na het hoofdvers toe;
5. context stopt correct bij het begin en einde van een hoofdstuk;
6. `−` herstelt het oorspronkelijke hoofdvers;
7. de tijdsdata bevat alle vindplaatsen en de zichtbare aantallen worden
   daaruit afgeleid;
8. rijen zonder vindplaatsen krijgen geen leeg tekstblok;
9. een laadfout houdt de referentie en de rest van de pagina bruikbaar;
10. toetsenbordbediening, toegankelijke namen, donkere modus en mobiele
    stapeling worden in de browser gecontroleerd.

## Buiten scope

- de vertaaltekst, kanttekeningen of historische kolommen wijzigen;
- een tweede, los bijgehouden kopie van versteksten opslaan;
- automatisch context over een hoofdstukgrens heen laden;
- een verborgen restlijst achter `meer teksten weergeven`;
- Liederen en Gebeden samenvoegen met deze korte vindplaatsweergave.
