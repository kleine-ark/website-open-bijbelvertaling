# Archeologie bij geografische plaatsen

## Eén gedeelde weergave

`plaats.html` gebruikt `js/plaats-archeologie.js` voor alle plaatsdossiers.
De kaart en het geografische overzicht verwijzen naar dezelfde plaatspagina.
De basisgegevens en Bijbelverwijzingen laden onafhankelijk van het optionele
archeologiedossier; een ontbrekend, ongeldig of traag dossier blokkeert die niet.

## Bronnen en onzekerheid

- Koppel een dossier uitsluitend aan het canonieke `properties.id` uit
  `data/geografie-runtime.geojson`, nooit automatisch op plaatsnaam.
- Houd gelijknamige plaatsen en alternatieve identificaties gescheiden.
- Maak onderscheid tussen archeologische waarnemingen, geografische
  identificatie, regionale context en interpretatie van Bijbelteksten.
- Elke bevinding bevat `bronIds` die verwijzen naar volledige bronvermeldingen
  in hetzelfde dossier. Gebruik bij voorkeur opgravingsrapporten, onderzoeks-
  publicaties, officiële erfgoeddossiers of de verantwoordelijke sitebeheerder.
- Vermeld beperkingen en onderzoeksdatum. Een opgraving bewijst niet zonder
  afzonderlijke onderbouwing een specifieke Bijbelse gebeurtenis.
- Automatisch voorbereid brononderzoek krijgt `humanReviewed: false`.

## Gegevens en generatie

Redactionele bestanden heten `data/geografie-archeologie-*.json` en bevatten
`schemaVersion: 1` en een lijst `dossiers`. Verplichte dossiergegevens zijn
`plaatsId`, `onderzoeksstatus`, `siteNaam`, `samenvatting`, `koppelingAanPlaats`,
`perioden`, `bevindingen`, `beperkingen`, `bronnen`, `gecontroleerdOp` en
`humanReviewed`. Bronvermeldingen hebben een uniek lokaal `id`, `titel`,
`organisatie`, een HTTPS-`url`, `type` en eventueel `jaar`.

```sh
python scripts/build_geografie_archeologie.py
```

De generator valideert bronkoppelingen, IDs, status en datum, en schrijft
`data/geografie-archeologie.json`. Deze gegenereerde index niet handmatig
bewerken. Elke runtimeplaats krijgt een record; zonder redactioneel dossier
blijft de status `nog-te-onderzoeken`. Een inventarisrecord telt dus niet als
afgerond onderzoek.

Onderzoeksstatussen:

- `archeologische-bron`: directe archeologische informatie voor deze site.
- `alleen-identificatie`: onderzoek naar ligging, geen bevestigde opgravingssite.
- `regionale-context`: informatie over de omgeving, niet over de exacte locatie.
- `geen-passende-bron-gevonden`: uitgevoerd onderzoek zonder geschikte bron;
  dit zegt niet dat er geen archeologie bestaat.
- `nog-te-onderzoeken`: nog geen redactioneel dossier.

## Controle

```sh
python -m unittest discover -s tests -p "test_geografie*.py"
node --test tests/test_plaats_archeologie.js tests/test_plaats_bronnen.js
```

De index telt afzonderlijk het aantal runtimeplaatsen, dossiers met uitgevoerd
brononderzoek en dossiers met directe archeologische bronnen. De eerste
inventaris bevat 1.269 plaatsen: 10 dossiers met brononderzoek, waarvan 9 met
archeologische bronnen en 1 met uitsluitend identificatieonderzoek; 1.259
dossiers staan nog open. De actuele telling staat altijd in de gegenereerde index.
