# Volledig meertalige Open Vertaling

Datum: 22 augustus 2026  
Status: goedgekeurd ontwerp, gereed voor uitvoeringsplan

## Doel

De volledige website wordt beschikbaar in dezelfde talen als de aanwezige
Bijbeledities: Nederlands, Engels, Frans, Duits, Spaans, Pools, Oekraïens,
Arabisch en Turks. Een taalkeuze geldt voor de hele website en kiest tegelijk
de bijbehorende Bijbeleditie als standaard. De keuze blijft bewaard en werkt
ook in Bijbelcitaten op wiki-, onderwerp- en naslagpagina's.

De meertaligheid omvat niet alleen navigatie en knoppen, maar ook vaste
paginateksten, instellingen, meldingen, metadata, wiki-artikelen,
onderwerppagina's, naslagteksten en andere redactionele inhoud.

## Talen en standaard-Bijbeledities

| Taal | Locale | Schrijfrichting | Standaardeditie |
|---|---|---|---|
| Nederlands | `nl` | LTR | Open Vertaling |
| Engels | `en` | LTR | World English Bible British Edition |
| Frans | `fr` | LTR | Louis Segond 1910 |
| Duits | `de` | LTR | Lutherbibel 1912 |
| Spaans | `es` | LTR | Reina-Valera 1909 |
| Pools | `pl` | LTR | Biblia Gdańska 1881 |
| Oekraïens | `uk` | LTR | Ukrainian Freedom Bible |
| Arabisch | `ar` | RTL | Arabic Van Dyck |
| Turks | `tr` | LTR | Open Basic Turkish New Testament |

De koppeling staat in één configuratiebestand en wordt niet verspreid over
pagina's of componenten vastgelegd.

## Architectuur

### 1. Centrale localeconfiguratie

Een centrale module beheert:

- ondersteunde locales;
- namen van talen in de eigen taal;
- tekstrichting;
- gekoppelde standaard-Bijbeleditie;
- locale uit URL, opgeslagen voorkeur en browservoorkeur;
- wijziging van `lang` en `dir` op het hoofddocument;
- localegevoelige getal- en datumopmaak.

Resolutievolgorde bij openen:

1. locale in de URL-route;
2. eerder opgeslagen globale taalkeuze;
3. ondersteunde browsertaal;
4. Nederlands.

Een expliciete taalroute wint altijd van een opgeslagen voorkeur. Na zo'n
bezoek wordt die taal de nieuwe globale voorkeur.

### 2. Deelbare taalroutes

Elke publieke pagina krijgt een taalroute onder de localecode, bijvoorbeeld:

- `/en/index.html#john/1`;
- `/fr/wiki.html#materiaux`;
- `/de/kaart.html`;
- `/ar/woordenboeken.html`.

De gegenereerde routebestanden zijn dunne toegangspagina's. Zij bevatten geen
gekopieerde applicatielogica of handmatig onderhouden inhoud, maar laden
dezelfde templates, scripts en stijlen als de Nederlandse bronpagina. Zo zijn
links deelbaar en indexeerbaar, terwijl gedrag slechts één keer wordt
onderhouden.

Iedere route krijgt een juiste canonical URL, `hreflang`-verwijzingen voor alle
beschikbare talen en gelokaliseerde Open Graph-, Twitter- en JSON-LD-metadata.

### 3. Interfacevertalingen

Interfacekopij komt in `i18n/<locale>.json`. Sleutels zijn semantisch en stabiel,
bijvoorbeeld `nav.read`, `settings.theme`, `search.inputHint` en
`edition.unavailable`. HTML gebruikt `data-i18n`-attributen; dynamische
JavaScriptcomponenten vragen teksten op via dezelfde centrale i18n-module.

Er komen geen localechecks zoals `if (lang === 'de')` in componentcode. Voor
meervoud, variabelen en ontbrekende waarden biedt de module vaste helpers.

Ontbrekende sleutels zijn tijdens ontwikkeling zichtbare fouten en laten de
build falen. In productie is Nederlands uitsluitend een technische noodfallback,
niet een geaccepteerde eindtoestand.

### 4. Redactionele inhoud

Langere inhoud wordt per inhoudsobject vertaald en niet als grote HTML-string in
interfacebestanden geplaatst. De Nederlandse brondata blijft leidend; per
locale komt een bestand met dezelfde stabiele identifiers en vertaalbare
velden. Dit geldt onder meer voor:

- wiki-overzicht en wiki-artikelen;
- onderwerpen en hun inleidingen;
- materialen, dieren, bomen en planten;
- liederen en gebeden;
- geografie, personen en stambomen;
- kaartbeschrijvingen en bronpagina's;
- uitgangspunten, principes, bronnen, downloads en statistieken;
- boek- en hoofdstukinleidingen voor zover zij redactionele website-inhoud zijn.

Feitelijke relaties, versverwijzingen, afbeeldingspaden, coördinaten en andere
niet-talige data blijven gedeeld. Alleen vertaalbare velden worden per locale
opgeslagen. Daardoor blijven alle talen inhoudelijk aan hetzelfde object en
dezelfde Bijbelteksten gekoppeld.

Een validatiescript vergelijkt per locale de identifier- en velddekking met de
Nederlandse bron en rapporteert ontbrekende of verouderde vertalingen.

### 5. Gekoppelde taal- en editievoorkeur

De globale taalkeuze en Bijbeleditie blijven afzonderlijke waarden, maar zijn
bewust gekoppeld:

- een taalwijziging stelt de standaardeditie voor die taal in;
- daarna mag de gebruiker binnen die taal handmatig een andere editie kiezen;
- een volgende taalwijziging kiest opnieuw de standaardeditie van de nieuwe
  taal;
- dezelfde toestand geldt in de lezer, zoekresultaten, wiki, onderwerpen,
  liederen, gebeden en alle gedeelde citaatcomponenten;
- onderdelen luisteren naar één centraal wijzigingsevent en verversen zonder
  volledige pagina-herlaad waar dat veilig kan.

Bijbelcitaten bewaren canonieke verwijzingen als boek-id, hoofdstuk en vers.
Weergavetekst wordt pas bij renderen uit de actieve editie geladen. Er worden
geen vertaalde citaten als los redactioneel tekstveld gedupliceerd.

### 6. Onvolledige edities

De Turkse editie bevat momenteel alleen het Nieuwe Testament. Bij een boek dat
niet in de actieve editie staat:

1. blijft de Turkse interface actief;
2. verschijnt een Turkse melding dat de gekozen editie dit boek niet bevat;
3. wordt de Bijbeltekst tijdelijk uit Open Vertaling getoond en duidelijk als
   Nederlandse fallback gemarkeerd;
4. kan de gebruiker vanuit de melding een andere beschikbare editie kiezen;
5. de opgeslagen globale interfacetaal verandert niet.

Dezelfde generieke regel geldt voor iedere toekomstige gedeeltelijke editie.

### 7. Arabisch en bidirectionele tekst

Bij Arabisch krijgt het hoofddocument `lang="ar"` en `dir="rtl"`. Layout,
navigatie, instellingen en redactionele tekst spiegelen mee. Elementen met een
eigen taal houden hun eigen richting:

- Latijnse, Griekse en Hebreeuwse lemmata;
- Strong-nummers en technische codes;
- URL's, coördinaten en bronverwijzingen;
- Bijbelcitaten uit een editie met een andere schrijfrichting.

CSS gebruikt logische eigenschappen (`margin-inline`, `padding-inline`,
`inset-inline`) in plaats van losse links/rechts-correcties.

## Taalkeuze in de interface

De taalkeuze wordt globaal bereikbaar vanuit de hoofdnavigatie en het
hamburgermenu. De bediening toont de taalnamen in hun eigen taal, met de actieve
taal duidelijk gemarkeerd. De keuzelijst is met toetsenbord en schermlezer te
bedienen en blijft bruikbaar op kleine schermen.

De taalkeuze staat los van de bestaande optie om parallelle Bijbeledities te
tonen. De primaire taal bepaalt de interface en standaardeditie; parallelle
edities blijven een leesvergelijking.

## Vertaalworkflow

1. Extraheer alle interface- en redactionele bronteksten naar stabiele sleutels
   en inhoudsidentifiers.
2. Maak per doeltaal een volledige conceptvertaling.
3. Valideer automatisch structuur, variabelen, HTML-fragmenten,
   versverwijzingen en ontbrekende velden.
4. Controleer vaste terminologie met localegebonden woordenlijsten.
5. Markeer vertaalstatus en bronversie zodat gewijzigde Nederlandse brontekst
   doelvertalingen aantoonbaar opnieuw ter controle aanbiedt.
6. Publiceer alleen wanneer de verplichte dekking voor de betreffende release
   honderd procent is.

Vertalingen veranderen nooit canonieke ids, links, Bijbelreferenties of
bronvermeldingen. Namen van Bijbelboeken komen uit een localegebonden
boeknamenregister.

## Migratievolgorde

De implementatie wordt technisch in fasen gebouwd, maar `main` krijgt pas een
zichtbare taalkeuze wanneer alle negen talen de afgesproken volledige dekking
hebben.

1. Centrale localeconfiguratie, i18n-runtime en tests.
2. Globale navigatie, instellingen, lezer en gedeelde citaatcomponent.
3. Boeknamen, zoekinterface, meldingen en overige dynamische componenten.
4. Gestructureerde wiki- en onderwerpdata.
5. Overige publieke pagina's en redactionele inhoud.
6. Taalroutes, metadata, sitemap en `hreflang`.
7. Volledige dekkingstest, visuele RTL-controle en publicatie.

## Teststrategie en acceptatiecriteria

De wijziging is gereed wanneer:

- iedere publieke pagina in alle negen talen bereikbaar is;
- geen zichtbare Nederlandse interface- of inhoudstekst overblijft buiten de
  Nederlandse locale;
- iedere taalroute de juiste standaard-Bijbeleditie activeert;
- taalkeuze direct doorwerkt in alle gedeelde Bijbelcitaten;
- een handmatig gekozen alternatieve editie behouden blijft totdat de taal
  opnieuw wordt gewijzigd;
- Arabische pagina's volledig RTL werken zonder foutieve richting in
  grondtekstvelden;
- Turkse oudtestamentische pagina's de vastgelegde fallback en melding tonen;
- refresh, interne navigatie en openen van een gedeelde link dezelfde locale
  behouden;
- alle locale- en inhoudsbestanden structureel volledig zijn;
- alle publieke pagina's correcte canonical- en `hreflang`-metadata hebben;
- geautomatiseerde browsertests desktop en mobiel voor alle locales afdekken;
- bestaande Nederlandse functies en leesinstellingen regressievrij blijven.

## Buiten scope

- Het maken van een ontbrekende volledige Turkse Bijbelvertaling.
- Het inhoudelijk moderniseren van de buitenlandse Bijbeledities.
- Automatische vertaling door een externe dienst tijdens een paginabezoek.
- Negen afzonderlijk onderhouden kopieën van de websitecode.
