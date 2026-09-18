# Geografische gegevens: controle van 13 september 2026

## Actuele vervolgstand

De lokale kaartindex bevat nu **1.269 punten en 8.730 tekstverwijzingen**,
verspreid over 5.604 verzen in 62 boeken. Deze vervolgcontrole beoordeelt
292 unieke entiteit-verskoppelingen: **269 bevestigd, 6 afgewezen en 17 open**.
Bevestiging betreft de tekstuele plaatsidentiteit, niet automatisch de moderne
ligging. Geen enkele agentcontrole is als menselijke revisie aangemerkt.

| Controlebestand | Bevestigd | Afgewezen | Open |
| --- | ---: | ---: | ---: |
| Johannes, 92 bestaande bronverwijzingen in hoofdstukken 1–21 | 80 | 0 | 12 |
| Handelingen 1–10, 122 bestaande bronverwijzingen | 116 | 4 | 2 |
| 2 Makkabeeën 1–5 en twee oude apocriefe kwesties | 43 | 2 | 3 |
| Gelijknamige plaatsen uit elf oude kaartrecords | 31 | 0 | 1 |

Twee besluiten overlappen tussen de bestanden: Ethiopië/Handelingen 8:27 en
Samaria/Handelingen 8:5. Zij tellen in het totaal elk slechts eenmaal mee;
de onderbouwingen van beide controles blijven beschikbaar.

**Stand op main (18 september 2026).** Vier besluiten zijn bij het opnieuw
bouwen op main vervallen, omdat de verstekst daar afwijkt van de tekst waarop
ze zijn genomen: Bethlehem in Johannes 7:42, Cush (Morenland) in Jesaja 18:1,
en Joppe en Lydda in Handelingen 9:38. Die verwijzingen staan weer op
`needs-human-review`. Op main telt de index daardoor 265 bevestigde besluiten
en 4.357 verwijzingen met `needs-human-review`.

### Inhoudelijke verwerking

- Voor 2 Makkabeeën zijn 46 verwijzingen opgenomen, waarvan 43 bevestigd en
  drie herkenbaar voorlopig. Alle 186 verzen van hoofdstukken 1–5 zijn gelezen;
  dit is nog geen volledige controle van het boek.
- Persepolis is opnieuw geplaatst met een gecontroleerde identificatie en
  [UNESCO-coördinaten](https://whc.unesco.org/en/list/114/), 29.93444, 52.89028.
  De bronpagina bevat 2 Makkabeeën 9:2; het punt lokaliseert de stad, niet de
  precieze tempel uit het verhaal. De oude Persepolis-link werkt via `legacyIds`.
- Pella/1 Makkabeeën 5:52 blijft afgewezen. De Romeinse provincie Asia is niet
  de juiste identiteit voor de Seleucidische rijkstitel in 2 Makkabeeën 3:3.
- Vier bestaande Handelingen-koppelingen zijn verwijderd: Judea bij 2:14,
  Egypte bij 7:14 en 7:18, en de Nijl bij 7:19. De expliciete plaatsvorm ontbreekt
  of de aangewezen woordgroep heeft geen eenduidige geografische betekenis.
- De nettoproductie is daardoor 46 toegevoegde verwijzingen min vier verwijderde:
  8.688 → 8.730. Niet alle zes afwijzingen waren al gepubliceerde verwijzingen.
- Bethsaïda, Efraïm, voorhof van Salomo, Schaapspoort en andere lokale
  naamvormen zijn expliciet vastgelegd. Stad Tiberias en zee van Tiberias
  blijven gescheiden. Herkomstnamen zoals Nazarener krijgen `mentionType: origin`.
- Indirecte Johannesvermeldingen, Samaria als stad/streek in Handelingen 8:5,
  de Antiochische burgerstatus in 2 Makkabeeën 4:9/19 en Arabië bij 5:8
  worden niet onvoorwaardelijk bevestigd.

### Behoud bij volgende builds

De runtimegenerator verwerkt `data/geografie-staging/reviews/*.json` na de
broninventarisatie. Ieder besluit is gekoppeld aan SHA-256 van de exacte
`text2026`-versinhoud. Bij gewijzigde tekst vervalt de bevestiging en ontstaat
opnieuw een reviewstatus; een oude afwijzing verwijdert dan geen nieuwe tekst.
Tegenstrijdige besluiten en meerdere bevestigde identiteiten voor één
eenmalige naamvermelding stoppen de build. Onopgeloste namen krijgen geen
verzonnen punt. Nieuwe coördinaten vereisen een afzonderlijke bron.

De volledige index bevat nog **4.353** verwijzingen met `needs-human-review`,
naast **1.078** niet-afgehandelde naamkandidaten in de niet-canonieke inventaris.
Zes aanvullende apocriefe vermeldingen zonder passend punt zijn apart bewaard:
Celo-Syrië (drie verzen), Mallo, Dafne en Lacedemoniërs. De moderne locatiekeuzes
van veel homoniemen blijven onzeker, ook wanneer de bronentiteit in het vers
wel is bevestigd. Twaalf oude samengestelde kaartrecords zijn nog niet tot één
legacy-bestemming teruggebracht; per-verscontrole rechtvaardigt geen samenvoeging.

### Verificatie vervolgcontrole

- 38 Python-regressietests, 30 JavaScript-gedragstests en 22 bestaande
  integriteitscontroles geslaagd: 90 controles in totaal.
- Alle 8.730 verwijzingen bestaan in de lokale tekst, hebben een werkende
  reader-href en bevatten hun eventuele opgeslagen naamvorm.
- Alle besluiten uit de vier reviewbestanden tegen de gebouwde runtime
  gecontroleerd: geen ontbrekende toepassing of verouderde teksthash.
- Browsercontrole: filter 2 Makkabeeën 9 toont precies Persepolis; luchtfoto
  en bronpagina werken, inclusief UNESCO-link en link naar 9:2.
- Geen Bijbeltekst, e-book of release gewijzigd; deze controle is lokaal.

## Eerste controle: resultaat en afbakening

De lokale kaartindex bevat **1.268 bronpunten en 8.688 verwijzingen**, verspreid
over 5.572 verzen in 61 boeken. De controle omvat de volledige technische
integriteit van deze index, de bronselectieregels, 135 nummeringscorrecties en
een inhoudelijke steekproef van twaalf locaties. Dit is **geen verklaring dat
alle Bijbelse locaties inhoudelijk zijn nagekeken**.

Er blijven 4.423 verwijzingen met `needs-human-review`. Ook `humanReviewed`
blijft overal `false`. De locatiecategorieën zijn 334 zeker, 378 waarschijnlijk
en 556 onzeker; die broncategorieën zijn geen historische bewijspercentages.

## Hersteld

- Bronselectie volgt de gewogen identificatie en eventuele tussenstappen in
  plaats van de gemiddelde stemwaarde. Niet-geografische voorkeurslezingen
  worden niet meer als zekere stad gepubliceerd.
- De bronpagina is rechtstreeks gekoppeld. Het werkelijk opgeloste moderne
  locatie-ID staat los van een tussenliggende identificatie. Moderne namen
  horen bij de gekozen coördinaat; bronalternatieven blijven zichtbaar.
- 135 bronverwijzingen zijn naar de lokale versnummering omgezet, waaronder
  Basan bij Psalm 22:13, En-gedi bij 1 Samuël 24:1 en Samaria bij Hosea 14:1.
  De oorspronkelijke bronverwijzing blijft opgeslagen.
- Asan wordt niet meer als Ain gemarkeerd, Gibeä niet als Geba en Seïr niet
  als Edom. Een gedeeld label voor verschillende plaatsen vereist review.
- Zestig expliciete Nederlandse naamkoppelingen voorkomen dat bekende namen
  zoals Jeruzalem, Jordaan en Kapernaüm onvindbaar worden. Een gedeeld vers
  alleen is geen bewijs dat twee plaatsen dezelfde zijn.
- Boek-, hoofdstuk- en zekerheidsfilters gelden ook voor een via de URL
  geselecteerde plaats. Popups sluiten bij een filterwijziging.
- GeoJSON gebruikt de datacache met online verversing en offline-terugval.
  Dataverzoeken herbevestigen ook de browser-HTTP-cache; alleen de
  serviceworkercache omzeilen bleek onvoldoende.

De betekenis van bronweging en afwijkende versnummering is beschreven in de
[primaire datasetdocumentatie](https://github.com/openbibleinfo/Bible-Geocoding-Data).

## Inhoudelijke steekproef

| Locatie | Bevinding en verwerking |
| --- | --- |
| Kalach | Fout oud punt circa 71 km te zuidelijk; de bronidentiteit gebruikt Nimrud. Vergelijk de [universitaire gazetteer](https://oracc.museum.upenn.edu/geonames/cbd/qpn/x000002130.html). |
| Rabba | Oud punt westelijk van Amman; gekoppeld aan [Rabbah 1](https://www.openbible.info/geo/ancient/ae067b5/rabbah-1). |
| Sion | Oud punt ligt buiten de passende context; niet met één moderne bergidentiteit versmolten. [Bron en alternatieven](https://www.openbible.info/geo/ancient/abd9596/mount-zion). |
| Ur | Runtimepunt bij Tell el-Muqayyar behouden; zekerheid over de site niet verwarren met Abrahams herkomst. [UNESCO-kaarten](https://whc.unesco.org/en/list/1481/maps/). |
| Gebal | Byblos en het andere Gebal gescheiden; [Gebal 1](https://www.openbible.info/geo/ancient/a9a2541/gebal-1) heeft sterke bronweging. |
| Hazor | Zwak gemiddeld stemcijfer betekende niet dat de plaats onbekend was; [Hazor 1](https://www.openbible.info/geo/ancient/a6f33c5/hazor-1) opnieuw gewogen. |
| Sodom | Voorkeursregio uit de bron gebruikt; geen schijnzekere stad. [Bronalternatieven](https://www.openbible.info/geo/ancient/a0aa664/sodom). |
| Sichar | Askar volgt de bronvoorkeur, niet Tell Balatah. [Bron](https://www.openbible.info/geo/ancient/a27b472/sychar). |
| Timna | Tel Batash vervangt de onjuist hoger gerangschikte kandidaat Horbat Timna. [Bron](https://www.openbible.info/geo/ancient/a21f909/timnah-1). |
| Gibea | De mogelijke persoon uit 1 Kronieken 2:49 krijgt geen informatie over Sauls woonplaats. [Broninterpretaties](https://www.openbible.info/geo/ancient/ad15169/gibea). |
| Kana | Twee moderne kandidaten zijn niet twee Bijbelse plaatsen. [Bron](https://www.openbible.info/geo/ancient/a031bda/cana). |
| Nebo | Berg en gelijknamige steden blijven gescheiden; bergalternatieven niet als losse plaatsen tellen. [Bron](https://www.openbible.info/geo/ancient/aefaa2d/mount-nebo). |

## Bewaard controlewerk

Het oude bestand `data/geografie.geojson` is niet overschreven. In de afgeleide
kaart zijn twaalf losse legacy-punten vervallen: deels duplicaten, deels
onvoldoende onderbouwde koppelingen. Tien eerder geplaatste bronentiteiten
krijgen geen kaartpunt meer op basis van de bronweging/voorkeursinterpretatie.
Dit verklaart de overgang van 1.290 naar 1.268 punten. Geldige oude plaats-ID's
van bewezen dubbele punten blijven via `legacyIds` bereikbaar.

- `data/geografie-staging/buiten-torah/legacy-review.json`: dertien oude
  records met niet-eenduidige identiteit, waaronder Sion, Cus en Petra, en
  samengestelde verwijzingen bij Jericho, Samaria, Berseba, Gilgal, Gebal,
  Hamath, Moab en Aram. De bronentiteiten verdwijnen daarmee niet van de kaart.
- Pella en Persepolis zijn niet meer als bewezen apocriefe koppelingen
  gepubliceerd. Daarom daalt het aantal boeken met kaartpunten van 63 naar 61.
- `niet-gepubliceerde-punten.json`: zeventien bronentiteiten zonder
  publiceerbaar punt, inclusief zeven die eerder al niet geplaatst waren.
- De niet-canonieke inventaris bevat 1.104 naamkandidaten. Zij zijn geen
  bevestigde plaatskoppelingen; geografische dekking van apocriefe en
  Ethiopische boeken blijft onvolledig.
- De wiki bewaart kaartfilters nog niet in de bovenliggende wiki-URL;
  directe `kaart.html?boek=…&hoofdstuk=…`-links doen dat wel.

## Reproduceerbaarheid

Bron: de lokaal beschikbare `ancient.jsonl` van OpenBible.info (CC BY 4.0).
De bron is niet als de nieuwste externe versie geclaimd. SHA-256:
`b8187aa4737e8517ccc090f765d2be11da4c548cd2a59d3cdcb62e952cb8c0f2`.

Generatorvolgorde: `scripts/build_geografie_buiten_torah.py`, daarna
`scripts/build_geografie_runtime.py`, met dezelfde `--source`.
De wijzigingen raken geen Bijbelhoofdstukteksten en bouwen geen publicatie
of e-book. De technische regressies staan in de nieuwe geografische Python-
en JavaScript-tests naast de bestaande integriteitscontroles.

## Uitgevoerde verificatie

- 20 Python-bronselectie/versificatieregressies, 30 JavaScript-gedragstests
  en 22 bestaande integriteitscontroles geslaagd.
- Alle 8.688 verwijzingen gecontroleerd tegen 851 lokale hoofdstukbestanden:
  geen ontbrekende verzen, ongeldige hrefs of afwezige opgeslagen labels.
- 111 expliciete oude-ID-koppelingen zijn ondubbelzinnig; geen dubbele
  `agent-reviewed` labelkoppelingen binnen een vers.
- In de echte browser: 1.268 punten totaal; boek/hoofdstukfilter Johannes 4
  toont 8 plaatsen; bronpagina Sichar toont Askar en Tell Balatah als
  alternatief; oude Kalach-link opent Calah; kaart werkt binnen de wiki.
- De bestaande Python-browsertest is aangepast aan de directe bronlink, maar
  niet via Playwright uitgevoerd omdat die Python-afhankelijkheid ontbreekt.
  De betreffende schermen zijn met de beschikbare browserbediening getest.
