# Gedeeld thema

Elke sitepagina laadt `/js/theme.js` synchroon in de head, vóór de stylesheets.
Er staan geen eigen thema-opstartscripts of themaknop-handlers meer in de HTML.
Ook de beheerpagina's en de losstaande lezer gebruiken deze module.

De bestaande opslag blijft `sv2026_vertaalopties.thema`: `auto`, `licht` of
`donker`. Een ontbrekende voorkeur betekent `auto`. Alleen `auto` raadpleegt
de systeemvoorkeur. Laden en toepassen veranderen de opgeslagen instelling niet.

- `OVTheme.apply(choice)` past het thema toe en synchroniseert de themaselectie
  in het optiespaneel. Opties, cloudherstel en iframe-berichten gebruiken dit.
- `OVTheme.toggle()` wisselt licht/donker en bewaart de expliciete keuze, met
  behoud van de overige opties. Als Opties al is geïnitialiseerd, loopt opslaan
  via `Opties.save()` zodat ook de bestaande cloud-sync blijft werken.
- Alleen `js/topnav.js` koppelt de themaknop aan `OVTheme.toggle()`.
- `ov:theme-changed` laat de wiki het thema doorgeven aan het geopende iframe.

Het optiespaneel blijft lui geladen; openen past geen andere voorkeur toe dan
de pagina bij het laden al gebruikte. De maten/getallenfuncties staan in
`js/optie-maten.js`, dat vóór `js/opties.js` wordt geladen. De bestaande
Opties-methoden en het gegevensformaat zijn daarbij ongewijzigd gebleven.

Regressietests staan in `tests/theme.test.cjs`, `tests/options-units.test.cjs`
en de thematests in `tests/verification.browser.test.cjs`.
