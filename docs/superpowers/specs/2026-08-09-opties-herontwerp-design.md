# Herontwerp van het optiescherm

## Doel

Het huidige optiescherm is een smalle kolom waarin leesweergave, vertaalkeuzes, vergelijking, onderzoek en voorlezen achter elkaar staan. Het nieuwe scherm brengt dezelfde functies onder in drie herkenbare tabbladen en opent als een ruim zwevend paneel. De leestekst blijft daardoor op zijn plaats en wordt niet smaller wanneer de gebruiker opties opent.

Het ontwerp volgt de bestaande vormtaal van Open Vertaling: marineblauw, goud, gebroken wit, EB Garamond voor de leesvoorvertoning en Fira Sans voor bediening en toelichting. De enige uitgesproken vorm is de tabregel bovenaan, opgevat als drie rustige registers van een naslagwerk.

## Paneel en bediening

- Op desktop opent het paneel vanaf rechts, boven de leestekst, met een breedte van ongeveer `520px`, een kleine marge tot de schermranden en afgeronde hoeken.
- Op schermen tot en met `768px` vult het paneel de beschikbare breedte en hoogte onder de bovenbalk. Het wordt geen smalle zijlade.
- Het openen van Opties verandert de breedte, kolomindeling en scrollpositie van de leestekst niet.
- De bestaande desktopknop en mobiele optieknop openen hetzelfde paneel.
- Het paneel sluit met de sluitknop, `Escape` of een klik op de verduisterde achtergrond. Daarna krijgt de oorspronkelijke knop de toetsenbordfocus terug.
- Tijdens het openen staat de focus in het paneel en is de onderliggende pagina voor toetsenbordbediening afgeschermd.
- De bovenkant bevat de titel **Leesvoorkeuren**, de voorvertoning „In de beginne schiep God de hemel en de aarde.” en de drie tabbladen **Lezen**, **Vergelijken** en **Onderzoeken**.
- Het laatst gekozen tabblad blijft tijdens de browsersessie actief. Een nieuwe sessie begint bij **Lezen**.

## Visuele hiërarchie

- De tabbladen staan op één regel en hebben voldoende grote aanraakvlakken. Het actieve tabblad krijgt een gouden onderstreping en marineblauwe tekst; inactieve tabbladen blijven rustig grijsblauw.
- Instellingen verschijnen als afzonderlijke rijen met links een korte naam en rechts de actuele keuze of een compacte bediening.
- Alleen de belangrijkste instellingsrijen krijgen een eenvoudig goudkleurig lijnicoon. Onderliggende keuzes krijgen geen eigen pictogram, zodat iconen de indeling verduidelijken in plaats van nieuwe drukte te veroorzaken.
- Schakelaars worden gebruikt voor aan/uit-keuzes, segmentknoppen voor twee of drie korte alternatieven en een vervolgscherm binnen hetzelfde paneel voor langere keuzelijsten.
- Lange uitleg staat niet permanent tussen de instellingen. Waar uitleg nodig is, staat een korte onderregel of een informatieknop die de toelichting in hetzelfde paneel opent.
- Sectiekoppen groeperen alleen inhoud die werkelijk bij elkaar hoort. Er komen geen decoratieve kaarten in kaarten.
- Het donkere thema gebruikt dezelfde hiërarchie met de bestaande donkere oppervlakken, niet een afzonderlijke visuele stijl.
- Beweging blijft beperkt tot het inschuiven van het paneel en de actieve tabindicator. Bij `prefers-reduced-motion: reduce` vervallen deze overgangen.

## Tabblad Lezen

Dit tabblad bevat alles wat de directe leeservaring of de weergegeven vertaling verandert:

1. **Weergave**
   - Thema: automatisch, licht of donker.
   - Tekstgrootte: de bestaande zoomstanden, bediend met min, percentage en plus.
   - Dyslexiemodus.
   - Citaatopmaak.
   - Versnummers, hoofdstuknummers en perikoopkopjes.
   - Boek- en hoofdstukinleiding.
   - Doorlopend lezen.

2. **Vertaalweergave**
   - Godsnaam in het Oude Testament.
   - Aanspreektitel in het Nieuwe Testament.
   - Weergave van Sheol.
   - Naam van Jezus en Nederlandse of Arabische persoonsnamen.
   - Bijbelse of omgerekende maten en tijdsaanduidingen.

3. **Voorlezen**
   - Mannen- of vrouwenstem.
   - Afspeelsnelheid.

De losse mobiele zoomknop verdwijnt. De zoomwaarde en de bestaande opslag blijven behouden; alleen de bediening verhuist naar **Lezen**.

## Tabblad Vergelijken

Dit tabblad bevat opties die een tweede tekst of vergelijking naast de Open Vertaling tonen:

- Tekstedities: SV 1637, SV 1888 en Open Vertaling.
- Kanttekeningen: KT 1637, KT 1888 en de Open Vertaling-kanttekeningen als kolom of popup.
- Plaatsing van extra kolommen: ernaast of eronder.
- Verschillen tussen SV en Open Vertaling.
- Verschillen tussen de kanttekeningen.

## Tabblad Onderzoeken

Dit tabblad bevat aanvullende informatie die de gebruiker tijdens tekstonderzoek kan tonen:

- Hebreeuws, Grieks, Aramees, Latijn of Ge'ez.
- Oudste handschrift per vers.
- Tags.
- Geografische locaties markeren.
- Strong-nummers zodra die gegevens voor het geopende boek beschikbaar zijn.

Een nog niet beschikbare onderzoekslaag wordt niet als werkende schakelaar getoond. Strong-nummers verschijnen dus alleen voor boeken waarvoor de koppeling werkelijk bestaat; andere boeken krijgen een korte statusregel zonder dode bediening.

## Technische opzet

- `Opties` in `js/opties.js` blijft eigenaar van vertaalkeuzes, standaardwaarden, opslag en het opnieuw renderen van de tekst.
- Een afzonderlijke paneelcontroller beheert alleen openen, sluiten, tabnavigatie, focus, het vervolgscherm en de tijdelijke actieve tab. Hierdoor raakt paneelgedrag niet vermengd met teksttransformatie.
- De bestaande ids, `data-optie`-attributen, `data-toggle-col`-attributen en opgeslagen waarden blijven behouden. Bestaande lokale en cloudvoorkeuren blijven daardoor bruikbaar.
- Inline wijzigingshandlers worden alleen verplaatst wanneer dat voor de nieuwe component nodig is; hun gedrag en opslagkeys veranderen niet.
- `js/zoom.js` blijft de zoomwaarde toepassen en opslaan, maar levert een kleine publieke interface voor de bediening in het paneel. Het maakt geen losse zweefknop meer aan.
- De bestaande rechterzijbalklogica wordt niet half behouden. De opties worden volledig uit de flexindeling gehaald; de linker boekenbalk blijft ongewijzigd.

## Toegankelijkheid en foutafhandeling

- De tabkop gebruikt `role="tablist"`; tabknoppen en panelen zijn gekoppeld met `aria-controls`, `aria-selected` en `role="tabpanel"`.
- Pijltjestoetsen wisselen tussen tabbladen; `Home` en `End` gaan naar het eerste en laatste tabblad.
- Alle instellingen hebben een zichtbaar label en blijven zonder muis bedienbaar.
- Een foutieve of onbekende opgeslagen waarde valt terug op de bestaande standaardwaarde zonder het paneel onbruikbaar te maken.
- Een fout bij cloudopslag verandert de direct toegepaste lokale instelling niet. De bestaande synchronisatielaag mag de bediening later opnieuw synchroniseren.
- Het paneel voorkomt horizontale pagina-overloop op alle ondersteunde breedtes.

## Controle

Geautomatiseerde tests bewaken ten minste:

- openen en sluiten via desktopknop, mobiele knop, achtergrond en `Escape`;
- behoud en herstel van toetsenbordfocus;
- de drie toegankelijke tabbladen en toetsenbordnavigatie;
- de juiste indeling van iedere bestaande optie;
- behoud van bestaande ids, waarden en opslagkeys;
- directe toepassing van een instelling en behoud na herladen;
- verplaatsing van zoom naar **Lezen** en afwezigheid van de losse zweefknop;
- onveranderde breedte en scrollpositie van de leestekst bij openen;
- volledige breedte op mobiel en het zwevende paneel op desktop;
- licht thema, donker thema en gereduceerde beweging;
- behoud van het bestaande gedrag van de teksteditie-keuzes.

Visuele controle gebeurt bij minimaal `1440px`, `1000px`, `768px`, `545px` en `390px`, met bijzondere aandacht voor lange Nederlandse labels en grote tekstzoom.
