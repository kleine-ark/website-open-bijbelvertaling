# Integrale controle OPV-pilot

Datum: 8 september 2026

Reikwijdte: Open Parafrase Vertaling (proef), Genesis 1–5 en Johannes 1–5

Directe bron: SV1888; SV1637, kanttekeningen, Open Vertaling en lokale grondtekst alleen als controlelaag

## Samenvatting

De pilot bevat alle 352 verwachte verzen en is technisch en visueel volledig door de readerketen gegaan. De eerste onafhankelijke bron- en taalreviews vonden inhoudelijke en stilistische punten; die hebben tot twee herstelrondes en een gerichte finale bronrisicocorrectie geleid. Daarna zijn alle 352 verzen en alle 58 leesblokken opnieuw onafhankelijk beoordeeld. De einduitkomsten zijn `SOURCE PASS` en `LANGUAGE PASS`: er staat geen Critical of Important bron- of taalbevinding meer open.

Alle 352 verzen blijven bewust `concept`. De uitgevoerde agentreviews leveren controleerbaar kwaliteitsbewijs, maar zijn geen onafhankelijke menselijke goedkeuring en geven geen grond om een vers naar `bron_gecontroleerd`, `taal_gecontroleerd` of `definitief` te promoveren.

## Corpus- en annotatieaantallen

De volgende aantallen zijn rechtstreeks uit de actuele hoofdstukbestanden en het actuele conceptregister berekend:

| Onderdeel | Aantal |
| --- | ---: |
| Hoofdstukken | 10 |
| Verzen | 352 |
| Betekenisblokken | 58 |
| Segmenten | 947 |
| Begripkoppelingen | 230 |
| Begrippen in het register | 107 |
| Citatierecords | 212 |
| Veilige, bestaande bronpaden | 352/352 |
| Verzen met actuele bron- en inhoudshash | 352/352 |

De eerder gehanteerde werktelling noemde 948 segmenten. De definitieve directe hertelling van de huidige tien JSON-bestanden en de readercontrole leveren beide 947 segmenten. Dit verslag gebruikt daarom het actuele, bevestigde getal 947.

De citaattelling daalde tijdens de eerste herstelronde van 213 naar 212. Het afzonderlijke binnencitaat in Genesis 3:17 verviel terecht toen die woorden als indirecte rede werden geformuleerd. De overblijvende citaatbereiken reconstrueren uit bestaande segmenten en hebben een spreker-id met een geldig type.

## Redactionele status

| Status | Verzen |
| --- | ---: |
| `concept` | 352 |
| `bron_gecontroleerd` | 0 |
| `taal_gecontroleerd` | 0 |
| `definitief` | 0 |

Dit blijft zo totdat een echte onafhankelijke menselijke bron- én taalreview is vastgelegd.

## Reviewmatrix

| Controle | Dekking | Uitkomst | Bevindingen of bewijs |
| --- | --- | --- | --- |
| Initiële bronreview | 352/352 verzen en 213/213 citatierecords | **SOURCE FAIL** | 0 Critical, 2 Important, 4 Minor |
| Onafhankelijke risico-adjudicatie | Genesis 4:7 en Johannes 3:16 | **PASS voor herstelrichting** | Beide Important-bevindingen bevestigd; exacte hersteltekst en metadataroute vastgelegd |
| Initiële taalreview | 58/58 blokken en 352/352 verzen | **LANGUAGE FAIL** | 0 Critical, 26 Important, 15 gegroepeerde Minor; 670 zinnen, 0 boven 25 woorden |
| Eerste bronherreview | 82 gewijzigde verzen, plus metadata- en risicocontrole | **SOURCE FAIL** | 0 Critical, 6 Important, 4 Minor; de zes oorspronkelijke bronbevindingen waren opgelost |
| Eerste taalherreview | 58/58 blokken en 352/352 verzen | **LANGUAGE FAIL** | 0 Critical, 8 Important, 11 gegroepeerde Minor; 677 zinnen, 0 boven 25 woorden |
| Gerichte finale bronrisicocontrole | 10 geselecteerde herstelbesluiten | **FOLLOW-UP NODIG** | 4 inhoudelijk veilig; 5 hoofdtekstcorrecties en 1 metadataherstel nodig; daarnaast 1 schrijfbeleidscorrectie |
| Allerlaatste bronherreview | 352/352 verzen, 947/947 segmenten en 212/212 citaten | **SOURCE PASS** | 0 Critical, 0 Important en 1 gemotiveerd Minor in Johannes 4:42 |
| Allerlaatste taalherreview | 58/58 blokken en 352/352 verzen | **LANGUAGE PASS** | 0 Critical, 0 Important en 0 ongemotiveerde Minor; 12 bewust behouden kleine bronspanningen zijn per vindplaats verantwoord |
| Metadata en corpuscontract | 10 hoofdstukken en 352 verzen | **PASS** | Validator meldde exact `OPV geldig: 10 hoofdstukken, 352 verzen.`; alle bronpaden, hashes, segmenten en annotaties zijn geldig |
| Technische readercontrole | 183 regressietests, waaronder 36 OPV-readertests | **TECH PASS** | De definitieve werkboom gaf `Ran 183 tests in 63.852s` en `OK` |
| Finale visuele readercontrole | 36 combinaties, 24 mobiele zoomchecks en 6 reflowchecks | **UX PASS** | Nul overflow, afkapping, anker-, thema-, structuur-, pagina-, console- en HTTP-fouten; 7 screenshots handmatig bekeken |
| Onafhankelijke menselijke bronreview | 352 verzen | **Niet uitgevoerd** | Vereist vóór statuspromotie |
| Onafhankelijke menselijke taalreview | 58 blokken | **Niet uitgevoerd** | Vereist vóór statuspromotie |

Alle automatische poorten en beide onafhankelijke agentreviews zijn daarmee gesloten. Dat verandert de redactionele status niet: agentreviews zijn controlebewijs, geen menselijke goedkeuring.

## Verwerkte bevindingen

### Eerste bron- en taalronde

De twee Important-bronbevindingen zijn verwerkt:

- Genesis 4:7 noemt Abel of een “goede band” niet langer als vaststaande betekenis. De hoofdtekst bewaart de onbesliste voornaamwoorden; de tweede laag legt de Abelduiding en de lezing met gepersonifieerde zonde naast elkaar.
- Johannes 3:16 beschrijft Gods liefde niet langer als een hoeveelheid. De gave van de Zoon laat zien *hoe* God Zijn liefde voor de wereld toont.

Ook de vier Minor-bronbevindingen zijn in de eerste herstelronde verwerkt: `één vlees` bleef zichtbaar in Genesis 2:24, wind en dag werden in Genesis 3:8 weer bij elkaar gehouden, Johannes 1:16 koos een bredere formulering voor ontvangen goedheid en Johannes 4:38 beschreef delen in het resultaat van andermans werk.

De 26 Important- en 15 gegroepeerde Minor-taalbevindingen leidden samen tot 23 herziene Genesisverzen en 59 herziene Johannesverzen. Daarbij zijn onder meer:

- zwevende referenten en onduidelijke handelende personen benoemd;
- vertellersuitleg bij Rabbi, Messias en Cefas van directe rede onderscheiden;
- de metreet in Johannes 2:6 in de leeslaag benaderd als 80–120 liter, met de oude maat in de tweede laag;
- vlees/Geest, wind/Geest, bruid/bruidegom en Vader/Zoon in eenvoudiger zinnen ontvouwd;
- spreekovergangen leesbaar gemaakt wanneer citaatopmaak uitstaat;
- oude uuraanduidingen herkenbaar als oude dagtelling gemarkeerd;
- formele reis-, getuigenis- en levensformuleringen vereenvoudigd;
- de hoofdstuktitel van Johannes 2 neutraler gemaakt.

### Tweede herstelronde na de eerste herreviews

De eerste bronherreview vond zes nieuwe of resterende Important-punten en vier Minor-punten. De actuele werkboom verwerkt die als volgt:

- Johannes 1:11 gebruikt `wat Hem toebehoorde` en maakt `het Zijne` niet tot de hele wereld.
- Johannes 2:24 bewaart de reflexieve objectrelatie: Jezus vertrouwde *Zichzelf* niet aan hen toe.
- Johannes 3:8 spreekt weer over merken en niet begrijpen, niet over menselijke beheersing van oorsprong en bestemming.
- Johannes 3:21 laat de daden zichtbaar worden en maakt de mens niet tot degene die ze bewust demonstreert.
- Johannes 3:31 voegt geen onbewezen sprekerintroductie toe; de neutrale blokkop luidt `Hij die uit de hemel komt`.
- Johannes 4:45 begint zonder het niet-bronmatige contrastwoord `Toch`.
- `kostbaar` bij bedolah is verwijderd, Jezus' zien in Johannes 1:48 is hersteld, de tijd van het Schriftcitaat in Johannes 2:17 is gecorrigeerd en Johannes 5:26 bewaart de vergelijking tussen Vader en Zoon.

De acht Important-taalbevindingen uit de eerste taalherreview zijn eveneens herschreven: Genesis 3:8 en 4:23; Johannes 2:17 en 2:24; Johannes 3:8 en 3:21; Johannes 4:10 en 4:36. De elf gegroepeerde Minor-punten zijn verwerkt of opnieuw als bewuste formulering beoordeeld. De allerlaatste taalherreview bevestigde vervolgens 0 Critical, 0 Important en geen ongemotiveerde Minor. Zij telde 667 zinnen en 7.062 woorden, gemiddeld 10,6 woorden per zin; geen zin is langer dan 25 woorden. Twaalf kleine spanningen blijven bewust staan waar verdere vereenvoudiging een bronambiguïteit of dragend kernbeeld zou vastleggen of verliezen.

De daaropvolgende gerichte bronrisicocontrole beoordeelde Johannes 2:24, 3:8 en 3:21 als veilig. Zij vroeg nog bronveilig herstel voor Genesis 3:8 en 4:23, Johannes 2:17, 4:10 en 4:36, plus herstel van de onzekerheidsnoot bij de sprekergrens in Johannes 3:31. Voor Johannes 5:26 resteerde alleen het afgesproken schrijfbeleid: `zichzelf` blijft klein. Al deze punten zijn in hoofdtekst, segmenten, begripankers, citaten en hashes verwerkt en in de definitieve bronreview opnieuw goedgekeurd.

De definitieve bronreview las alle 352 verzen rechtstreeks naast hun eigen lokale SV1888-bronveld. Zij herberekende 352 bron- en inhoudshashes, controleerde 947 bronfrases en reconstrueerde 212 citaten met spreker en aangesprokene. Uitkomst: 0 Critical, 0 Important en één geaccepteerd Minor. In Johannes 4:42 maakt `niet meer alleen vanwege jouw verhaal` de overgang naar zelf horen iets minder absoluut dan de bron. Dit is reeds gemotiveerd in besluit J33 en blijft een expliciet beslispunt voor de latere menselijke eindredacteur.

## Risicobesluiten

- **Genesis 4:7 — referent blijft open.** De hoofdtekst kiest niet stilzwijgend tussen Abel en gepersonifieerde zonde. Zie [G17 in het besluitregister](besluitregister.md#g17--47-verhoging-zonde-aan-de-deur-en-onbesliste-referent).
- **Genesis 3:8 — wind en dag zonder ingevuld dagdeel.** De tekst bewaart hun samenhang zonder ochtend, avond of koelte als zekerheid in te voeren. Zie [G13](besluitregister.md#g13--38-13-stem-wind-en-aanspreekvorm).
- **Johannes 2:6 — begrijpelijke maat met bronterm in de tweede laag.** De hoofdtekst geeft een afgerond literbereik; `metreet` en de onzekerheid van de omrekening blijven raadpleegbaar. Zie [J14](besluitregister.md#j14--26-12-maten-feest-en-eerste-teken).
- **Johannes 3:16 — wijze, niet hoeveelheid.** `Zo liet God zien` bewaart dat het geven van de Zoon de wijze is waarop Gods liefde zichtbaar wordt. Zie [J20](besluitregister.md#j20--316-21-wereld-veroordeling-en-licht).
- **Johannes 3:31–36 — onzekere sprekergrens.** De hoofdtekst presenteert Johannes de Doper niet als bewezen spreker; de gekozen metadata en het serieuze alternatief blijven in de uitleglaag. Zie [J19](besluitregister.md#j19--316-21-en-331-36-redactionele-sprekergrenzen-en-onzekerheid).
- **Johannes 5:3–4 — tekstvariant blijft zichtbaar.** De SV/TR-lezing staat in de hoofdtekst; het afwijkende handschriftbewijs blijft een gekoppelde tweede-laagnoot. Zie [J26](besluitregister.md#j26--52-4-bethesda-en-de-handschriften).
- **Geen automatische Strong-koppelingen.** De parafrase erft geen woordniveaukoppelingen die op de woordvolgorde van een andere editie zijn uitgelijnd.

Het volledige inhoudelijke spoor staat in het [OPV-besluitregister](besluitregister.md). De reviewstatus en technische validatie veranderen deze exegetische beslissingen niet in menselijke goedkeuring.

## Technische en visuele controle

### Geautomatiseerde controles

De technische/visuele review legde eerst de volgende tussentijdse uitvoer vast:

```text
OPV geldig: 10 hoofdstukken, 352 verzen.
Ran 182 tests in 60.176s
OK
```

Daarnaast gaven syntaxcontrole van `js/app.js`, `js/teksteditie.js` en `js/opties.js` en `git diff --check` exitcode 0. De gemelde LF/CRLF-regelafbrekingen waren Git-waarschuwingen, geen whitespacefouten.

Finale uitvoer op de actuele eindstand:

```text
OPV geldig: 10 hoofdstukken, 352 verzen.
Ran 183 tests in 63.852s
OK
node --check js/app.js: exitcode 0
node --check js/teksteditie.js: exitcode 0
node --check js/opties.js: exitcode 0
git diff --check: exitcode 0
```

### Visuele matrix

De aparte Playwright-review controleerde Genesis 1 en Johannes 3 in licht en donker, in drie editiemodi: OPV primair, Open Vertaling primair met OPV parallel, en OPV primair met Open Vertaling parallel.

| Viewport | OPV primair | OV + OPV parallel | OPV + OV parallel | Resultaat |
| --- | ---: | ---: | ---: | --- |
| 1440×900, licht en donker | 4/4 | 4/4 | 4/4 | **PASS — 12/12** |
| 390×844, licht en donker | 4/4 | 4/4 | 4/4 | **PASS — 12/12** |
| 360×800, licht en donker | 4/4 | 4/4 | 4/4 | **PASS — 12/12** |
| **Totaal** | **12/12** | **12/12** | **12/12** | **PASS — 36/36** |

De teller `4/4` per cel bestaat uit twee hoofdstukken maal twee thema's. In alle 36 combinaties waren er nul gevallen van horizontale overflow, afgekapte OPV- of parallelcontainers, onbruikbare versankers, een verkeerd thema, paginafouten, consolefouten of HTTP-responses vanaf 400.

De volledige matrix is na de laatste broncorrecties opnieuw op de actuele werkboom uitgevoerd. Die eindrun bevestigde opnieuw 36/36 combinaties, 24/24 mobiele CSS-zoomchecks en 6/6 echte 720×450-reflowchecks. De technische reviewer herhaalde daarnaast de brede suite afzonderlijk: `Ran 183 tests in 68.962s` en `OK`. Zeven representatieve screenshots zijn handmatig op leesbaarheid, typografie, citaten, parallellayout en bediening bekeken.

Aanvullend zijn gecontroleerd:

- 200% CSS-zoom op 360 en 390 pixels;
- een echte 200%-browserzoom-equivalente reflow op 720×450;
- citaatopmaak aan en uit zonder tekstverlies;
- de begrippendialoog, focusval, Escape en focusherstel;
- toetsenbordbediening en `prefers-reduced-motion`;
- wisselen tussen OPV en OV zonder documentreload;
- doorgaand lezen en hoofdstuknavigatie aan beide pilotgrenzen;
- vaste mobiele hoofdstukbediening zonder bedekte tekst;
- globale OPV-editiekeuze in wiki-citaten.

Deze UI-controle hoeft alleen opnieuw als de tweede inhoudelijke herstelronde de readerstructuur of metadata zodanig heeft veranderd dat de bestaande 36-combinatiematrix niet meer representatief is. De finale regressiesuite blijft hoe dan ook verplicht.

## Open punten en vrijgavevoorwaarde

1. **Menselijke broncontrole:** de volledige pilot moet nog door een onafhankelijke menselijke bronreviewer worden beoordeeld.
2. **Menselijke taalcontrole:** alle 58 blokken moeten nog door een onafhankelijke menselijke taalreviewer als doorlopende tekst worden gelezen.
3. **Johannes 4:42:** een menselijke eindredacteur moet het gemotiveerde Minor-punt rond `alleen` bevestigen of kiezen voor de striktere formulering zonder dat woord.
4. **Statuspromotie:** ook met SOURCE PASS, LANGUAGE PASS, TECH PASS en UX PASS blijven alle 352 verzen `concept` totdat beide menselijke controles werkelijk zijn uitgevoerd en vastgelegd.

De pilot is technisch commitgereed. Publieke aanduiding als inhoudelijk definitief en iedere statuspromotie vereisen nog de menselijke controles hierboven.
