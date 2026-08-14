# Zwevende optieknop bij leestekst verwijderen

## Doel

De leesinstellingen krijgen één vaste ingang in het hoofdmenu. De losse,
zwevende knop rechts naast de Bijbeltekst verdwijnt. Hetzelfde paneel is op
elke pagina bereikbaar, inclusief de Wiki, zonder naar de leestekst te gaan.
Elke Bijbeltekst buiten de hoofdlezer gebruikt daarbij dezelfde centrale
JavaScript-citatiecomponent.

## Afbakening

- Verwijder `#sidebar-right-open` uit de leestekstpagina en de JavaScript die
  deze als opener behandelt.
- Verwijder uitsluitend de bijbehorende CSS voor die knop.
- Behoud de globale knop in het hoofdmenu als enige ingang.
- Op mobiele schermen verhuist diezelfde ingang naar het uitklapmenu achter de
  hamburgerknop; de mobiele leestekstknop vervalt.
- Gebruik op elke pagina hetzelfde optiespaneel en dezelfde opgeslagen globale
  voorkeuren. Het openen vanuit de Wiki verandert de huidige pagina niet.
- Migreer alle losse Bijbeltekstweergaven op Wiki-, onderwerp-, naslag- en
  documentatiepagina's naar `OVTekstweergave` met `OSV.cite`; directe
  `OSV.cite`-aanroepen en handmatig opgebouwde versteksten vervallen.
- Zend een wijziging van de globale opties vanuit een Wiki-pagina door naar de
  actieve iframe-pagina, die vervolgens haar bestaande citaten opnieuw
  rendert zonder navigatie naar de hoofdlezer.
- Geef de sectiekoppen van het optiespaneel het identieke marineblauw van de
  hoofdnavigatie. Gebruik goud als accent en een contrastrijke lichte tekst;
  de donkere modus behoudt dezelfde hiërarchie met leesbare contrasten.

## Controle

- De instellingen zijn vanuit de hoofdnavigatie te openen en te sluiten, ook
  vanuit het mobiele hamburger-menu.
- Er staat geen zwevende of mobiele optieknop meer naast of boven de leestekst.
- De bestaande opties en opgeslagen voorkeuren blijven ongewijzigd werken.
- Een wijziging vanuit de Wiki wordt onmiddellijk toegepast op alle daar
  gebruikte, gekoppelde tekstcitaten en blijft ook voor de leestekst gelden.
- Elke Bijbeltekst buiten de hoofdlezer heeft hetzelfde citaat-DOM, dezelfde
  aanhalingstekens, versnummerweergave, taalkeuze, Godsnaam, Strong-nummers en
  verwijzing naar de lezer.
- De sectiebalken zijn visueel consistent met de hoofdnavigatie in licht en
  donker thema.
