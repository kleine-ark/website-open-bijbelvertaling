# Ontwerp: meertalige Bijbelteksten en i18n-fundament

Datum: 9 augustus 2026

## Doel

Open Vertaling krijgt in de eerste fase vier aanvullende publiek-domeinvertalingen. De gebruiker kan de Bijbeltekst wisselen tussen Nederlands, Frans, Engels, Arabisch en Spaans. De bediening blijft in deze fase Nederlands, maar de UI-code wordt zo ingericht dat de interface later zonder herbouw van componenten vertaald kan worden.

## Vertalingen

| Interne code | Taal | Editie | Richting | Dekking |
|---|---|---|---|---|
| `nl-ov` | Nederlands | Open Vertaling | LTR | Huidige 88 boeken |
| `fr-lsg1910` | Frans | Louis Segond 1910 | LTR | 66 boeken |
| `en-webbe` | Engels | World English Bible British Edition with Deuterocanon | LTR | 83 USFM-boeken en onderdelen |
| `ar-vd` | Arabisch | Arabic Van Dyck | RTL | 66 boeken |
| `es-rv1909` | Spaans | Reina-Valera 1909 | LTR | 66 boeken |

De vier aanvullende edities zijn door de bron als publiek domein aangeduid. De geïmporteerde tekst blijft inhoudelijk ongewijzigd. De naam “World English Bible” is een merknaam; een aangepaste tekst wordt niet onder die naam verspreid.

## Fase 1

Fase 1 levert:

- een globale keuze voor de actieve Bijbeltekst in Leesvoorkeuren;
- de gekozen editie in de hoofdlezer en alle dynamische Bijbelcitaten op de site;
- rijke weergave van kopjes, alinea's, poëzie, voetnoten, kruisverwijzingen en Strong-nummers voor zover de bron die levert;
- tekstgetrouwe Arabische weergave met `lang="ar"` en `dir="rtl"` op tekstniveau;
- een Nederlandse interface waarvan zichtbare teksten uit een centrale Nederlandse berichtencatalogus komen;
- deelbare links die de editie optioneel vastleggen met `?editie=<code>`;
- een duidelijke melding wanneer de gekozen editie het geopende boek niet bevat.

Fase 1 levert geen vertaalde interface, geen automatisch vertaalde redactionele pagina's en geen wijzigingen aan de inhoud van de buitenlandse edities.

## Genormaliseerd vertaalformaat

De USFM-bestanden worden tijdens de build geconverteerd. De browser parseert geen USFM.

```text
data/vertalingen/
  manifest.json
  fr-lsg1910/<boek>/<hoofdstuk>.json
  en-webbe/<boek>/<hoofdstuk>.json
  ar-vd/<boek>/<hoofdstuk>.json
  es-rv1909/<boek>/<hoofdstuk>.json
```

Het manifest bevat per editie de code, naam, taal, tekstrichting, bron-URL, rechtenstatus, bronversie en beschikbare OV-boek-ID's.

Een hoofdstukbestand heeft een klein, editie-onafhankelijk schema:

```json
{
  "editie": "fr-lsg1910",
  "boek": "genesis",
  "hoofdstuk": 1,
  "kop": "La création",
  "blokken": [],
  "verzen": [
    {
      "nummer": 1,
      "tekst": "…",
      "html": "…",
      "segmenten": [],
      "voetnoten": [],
      "kruisverwijzingen": []
    }
  ]
}
```

`tekst` is platte brontekst. `html` bevat uitsluitend door de converter toegestane semantische elementen en klassen. `blokken` bewaart de volgorde van kopjes, alinea's en poëzieregels. `segmenten` bewaart woordmarkeringen zoals Strong-nummers zonder die in de platte tekst te mengen.

Het buitenlandse schema kopieert geen Nederlandse revisievelden zoals `text1637`, `phraseDiff`, `marginNotes` of reviewstatus. De Nederlandse hoofdstukbestanden blijven hun bestaande schema gebruiken; een gedeelde laadlaag biedt beide schema's aan de renderer aan.

## Conversie en validatie

Een deterministische converter:

1. leest de ongewijzigde USFM-bronnen uit `bronbestanden/vertalingen`;
2. koppelt USFM-boekcodes via een expliciete tabel aan `data/books.json`;
3. converteert alleen bekende markeringen;
4. rapporteert onbekende of niet-ondersteunde markeringen als buildfout of expliciete waarschuwing;
5. schrijft UTF-8 JSON zonder ASCII-escaping;
6. genereert een controleverslag met boek-, hoofdstuk-, vers- en markeringsaantallen.

De converter bewaart minimaal hoofdstukken, verzen, kopjes, alinea's, poëzie, voetnoten, kruisverwijzingen, cursief/vet en `\\w`-segmenten met Strong-nummers. Onveilige HTML uit bronbestanden wordt nooit rechtstreeks overgenomen.

De oude platte `data/arabisch`- en `data/kjv`-bestanden blijven bestaan totdat een vergelijking aantoont dat de nieuwe laadlaag minstens dezelfde dekking en correcte Unicode-weergave heeft. De Engelse standaard wordt daarna WEBBE; KJV kan als afzonderlijke vergelijkingseditie blijven bestaan, maar valt buiten deze eerste migratie.

## Globale editievoorkeur

De actieve editie wordt als `teksteditie` opgeslagen in `sv2026_vertaalopties`. `nl-ov` blijft de standaard.

De prioriteitsvolgorde is:

1. een expliciete editie in een citaat of embed;
2. `?editie=<code>` in de pagina-URL;
3. de globale gebruikersvoorkeur;
4. `nl-ov`.

Een wijziging in Leesvoorkeuren rendert het huidige hoofdstuk en zichtbare citaten opnieuw zonder paginaherlading. Andere open tabbladen ontvangen de wijziging via het `storage`-event.

Als een boek ontbreekt, valt de site niet stilzwijgend terug op Nederlands. De lezer toont de gekozen editie, het ontbrekende boek en een knop om dit boek in Open Vertaling te openen.

## Gedeelde tekstpresentatie

Alle componenten vragen tekst op via dezelfde editie- en presentatielaag:

- hoofdlezer;
- liederen en gebeden;
- onderwerpen en wiki-naslag;
- zoekresultaten;
- geselecteerde verzen in feedback;
- interne en externe citaten.

De citatie-API ondersteunt bijvoorbeeld:

```js
OSV.cite('johannes 3:16', { translation: 'fr-lsg1910' })
```

Zonder expliciete `translation` erft een citaat de globale editie. Passagekoppen en vers­nummers linken naar het exacte boek, hoofdstuk en vers met behoud van de actieve editie.

OV-presentatiekeuzes zoals de weergave van de Godsnaam, namen, maten en tijden worden sitebreed op Nederlandse OV-tekst toegepast. Ze veranderen nooit de opgeslagen tekst. Buitenlandse edities blijven tekstgetrouw; daar worden zulke keuzes alleen toegepast wanneer de bron een semantische markering biedt die de omzetting ondubbelzinnig maakt. Blinde vervanging van woorden als `LORD`, `Señor`, `Éternel` of `الرب` is niet toegestaan.

## Liederen

De liedbundelbouwer bewaart naast platte tekst ook de veilige rijke versinhoud en exacte versreferentie. Iedere liedpagina gebruikt de gedeelde presentatielaag en erft dus de actieve editie.

De volledige liedtekst staat in één rustig gearceerd vlak:

- een zachte goud-beige achtergrond en gouden zijlijn in het lichte thema;
- een warme donkere tint in het donkere thema;
- één blok per lied, niet één kader per vers;
- gouden, klikbare vers­nummers;
- behoud van citatie-, spreker- en poëzie-opmaak.

De beschrijving en overige metadata staan buiten het gearceerde tekstvlak.

## Voorbereiding van de interface

Zichtbare vaste UI-teksten worden stapsgewijs vervangen door sleutels uit een berichtencatalogus, te beginnen bij de lezer, Leesvoorkeuren, navigatie, foutmeldingen en citatiecomponenten.

```text
i18n/
  nl.json
```

Een kleine `I18n`-module levert `t(sleutel, variabelen)` en zet documentmetadata voor de actieve UI-taal. In fase 1 bestaat alleen `nl.json`; ontbrekende sleutels zijn een testfout en worden niet als sleutelnaam aan bezoekers getoond.

De UI blijft in fase 1 `lang="nl"` en LTR. Ieder Bijbeltekstblok krijgt zijn eigen `lang` en `dir`. CSS gebruikt logische eigenschappen (`margin-inline`, `padding-inline`, `border-inline-start`) zodat een latere volledig Arabische interface geen tweede layout nodig heeft.

Gelokaliseerde routes en vertaalde SEO-pagina's worden pas toegevoegd wanneer een volledige UI-catalogus voor die taal bestaat. `?editie=` creëert daarom geen afzonderlijke canonieke pagina; canonical metadata blijft naar de basispagina wijzen.

## Zoeken en links

De datalaag krijgt editie-onafhankelijke referenties op basis van OV-boek-ID, hoofdstuk en vers. Daardoor blijven onderwerpen, personen, feesten en andere naslaggegevens aan één referentie gekoppeld en kan de zichtbare tekst uit iedere beschikbare editie komen.

Een intern kruisverwijzingsdoel wordt genormaliseerd naar dezelfde referentiestructuur. Bij een onherkenbare of niet-bestaande bronverwijzing blijft de noot leesbaar, maar wordt geen kapotte link gemaakt.

Fase 1 bouwt een zoekindex per geïmporteerde editie. De actieve editie bepaalt welke index en welk tekstfragment worden gebruikt. Redactionele Nederlandse pagina's blijven afzonderlijk doorzoekbaar in het Nederlands.

## Fouten en veiligheid

- Ontbrekende editie of ongeldig editie-ID: terugvallen op `nl-ov` met één niet-storende melding.
- Ontbrekend boek: geen tekstfallback; toon de dekkingsmelding en Nederlandse actieknop.
- Ontbrekend hoofdstuk of vers binnen een beschikbaar boek: als datafout rapporteren en geen aangrenzende tekst tonen.
- Beschadigde JSON of converterfout: build faalt voor productie.
- HTML wordt opgebouwd uit een allowlist van semantische USFM-markeringen.
- Bronbestanden en gegenereerde bestanden blijven duidelijk gescheiden.

## Tests en acceptatie

De implementatie is gereed wanneer:

1. alle bronarchieven dezelfde SHA-256 hebben als vastgelegd bij import;
2. boek-, hoofdstuk- en versaantallen per editie overeenkomen met het converterrapport;
3. Genesis 1:1 en Johannes 3:16 in alle vijf edities correct worden weergegeven;
4. Arabische tekst zonder tekenbeschadiging rechts-naar-links staat, terwijl de Nederlandse UI links-naar-rechts blijft;
5. een WEBBE-poëziepassage, voetnoot en kruisverwijzing hun structuur behouden;
6. een Frans en Spaans vers met Strong-markeringen gekoppelde woordsegmenten behoudt;
7. editie wisselen hoofdtekst, liedtekst, onderwerptekst en citaat zonder herladen bijwerkt;
8. een ontbrekend apocrief of Ethiopisch boek de afgesproken dekkingsmelding toont;
9. een gedeelde URL met `?editie=` dezelfde editie opent zonder de globale voorkeur onbedoeld te overschrijven;
10. alle Nederlandse UI-sleutels bestaan en de pagina geen onvertaalde sleutelcodes toont;
11. bestaande Nederlandse lees-, navigatie-, citatie- en optieschermtests blijven slagen.

## Uitrolvolgorde

1. Converter en schema plus validatieverslag.
2. Gedeelde vertalingenlader en citatie-API.
3. Globale editievoorkeur en ontbrekende-boekmelding.
4. Hoofdlezer en rijke liedweergave.
5. Onderwerpen, wiki, zoeken en feedbackselecties.
6. Nederlandse UI-catalogus en logische RTL-geschikte CSS.
7. Verwijderen of behouden van oude parallelbestanden na vergelijking.
