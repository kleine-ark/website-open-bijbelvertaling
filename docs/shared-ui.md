# Gedeelde navigatie en login-opstart

## Login

Alle 136 pagina's met de bovenbalk of een eigen login-consument laden in de head:

```html
<script type="module" src="/js/auth-bootstrap.js"></script>
```

Deze module importeert achtereenvolgens Firebase-configuratie, Auth en
Collaboration. Hij koppelt de sessieluisteraar en start Auth één keer, vóór
DOMContentLoaded. Firebase zelf laadt asynchroon; `Auth.stateResolved` en
`Collaboration.ready` blijven de bestaande status aangeven. Paginaluisteraars
kunnen vanaf DOMContentLoaded aan Auth en Collaboration gekoppeld worden.

Topnav maakt alleen de bovenbalk en het login-slot; hij injecteert geen
auth-scripts meer. Auth en Collaboration hebben geen eigen auto-init of
duplicaatguards. Ook de losstaande lezer, beheerpagina's, manuscriptpagina's
en iframe-documenten gebruiken hetzelfde entrypoint.

## Iframe-links

De 18 documentatie-/naslagpagina's laden `js/iframe-navigation.js` in de body.
Die markeert een ingebed document en geeft de bestaande relatieve links bij
DOMContentLoaded `target="_top"`. Hashlinks, mailto-, http(s)- en javascript-links
blijven ongewijzigd. De elf naslagpagina's gebruiken `data-preserve-query` om ook
querylinks in het frame te houden; de zeven overige pagina's niet.

De aparte klikafhandeling in `wiki.html` blijft verantwoordelijk voor dynamisch
toegevoegde Bijbellinks en tekstverwijzingen. Topnav en de algemene CSS blijven
de ingebedde bovenbalk en documentatiezijbalk verbergen.

## Documentatiemenu's

De zeven pagina's kiezen een `data-doc-menu` op een lege `.doc-sidebar` en laden
`js/doc-sidebar.js` direct erna. Het script bevat één linkcatalogus en vijf
menuvarianten. De huidige pagina krijgt `aria-current="page"`; de bestaande
linkvolgorde, labels en manuscript-inspringing zijn behouden.

`css/doc-sidebar.css` bevat de menuopmaak voor desktop, mobiel en donker thema
en wordt vóór `css/style.css` geladen. Er zijn geen inline menu-stijlen of
CSS-selectors op de oude inline-attributen meer.

## Boeken

Navigation en Sidebar gebruiken rechtstreeks `getBookOrderGroups` uit
`js/book-orders.js`. De gekopieerde canonieke fallbacklijsten zijn verwijderd.
De centrale zichtbaarheid en Ethiopische subgroep worden ook rechtstreeks
gebruikt; de volgorde van scripts in `index.html` legt deze afhankelijkheid vast.

Deze refactors wijzigen geen opgeslagen opties, gebruikers of beoordelingen.
Service-worker-cache `verification-v9` neemt de nieuwe bestanden op en vervangt
de vorige shell-cache. Browser- en structuurtests staan in
`tests/shared-ui.browser.test.cjs` en `tests/shared-ui.test.cjs`; de browserfixture
wordt gedeeld met de bestaande verificatietests.
