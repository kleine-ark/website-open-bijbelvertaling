# Accounts, rechten en verificatie

De site gebruikt Firebase Authentication (Google-login via popup) als
identiteitsprovider. De API controleert bij ieder verzoek het Firebase ID-token:
handtekening, project, uitgever, geldigheid en geverifieerd e-mailadres.
Rechten en verificaties staan niet in Firebase-profielvelden of browseropslag,
maar in de private SQLite-database:

```text
/var/lib/openvertaling-collaboration/collaboration.sqlite3
```

## Gebruikers beheren

Beheerders openen `/gebruikers.html`, zoeken een account en wijzigen de rechten.
Een account verschijnt zodra het eenmaal met Google bij dit systeem is aangemeld,
met uitzondering van vooraf gereserveerde accounts.
Dit is geen overzicht van nog nooit aangemelde Firebase-accounts.

- Gewone accounts kunnen lezen, maar niet verifiëren.
- `reviewer` (“Mag verifiëren”) kan inhoud verifiëren en verificaties intrekken.
  Dezelfde rol mag correcties aanvragen en wijzigingsvoorstellen beoordelen.
- `administrator` kan daarnaast accounts/rechten beheren en verantwoordelijken
  en de volledige geschiedenis zien. Deze rol omvat altijd `reviewer`.

De vaste beheerders zijn `maartenvroegindeweij@gmail.com` en
`real.johnheikens@gmail.com`. Hun gereserveerde account wordt bij de eerste
sessie gekoppeld aan hun echte Firebase-uid. Hun beheerdersrecht kan niet via
de gebruikerspagina worden verwijderd. Iedere rolwijziging wordt gelogd.
Een gereserveerd account heeft nog geen login en staat als “Nog niet aangemeld”
in het beheerdersoverzicht. Het kan zelf geen handelingen uitvoeren.
De interne account-id (`uid`) blijft bij het aanmelden gelijk; de afzonderlijke
`firebase_uid` koppelt het account aan het gecontroleerde Google-token.
Koppelen gebeurt alleen bij een geverifieerd Google-e-mailadres dat exact
overeenkomt (hoofdletterongevoelig), nooit op basis van een naam of clientvelden.
Een al gekoppeld account kan niet door een ander Firebase-account worden overgenomen.
Rechten worden binnen de schrijftransactie opnieuw gecontroleerd: een oude
browsersessie kan een ingetrokken recht niet blijven gebruiken.

## Eén klik, geen toewijzingen

Een bevoegde gebruiker logt in, leest de inhoud en klikt **Verifiëren**.
De server legt zelf de interne account-id, naam, het e-mailadres, tijdstip en de
inhoudsrevisie vast. Er is geen persoonselector, eigenaarstoewijzing of
overdrachtsworkflow. Aangeleverde verifier-identiteiten worden geweigerd.

De knop staat bij:

- hoofdstukken en afzonderlijke verzen in `index.html` en `lees.html`;
- locaties in `plaats.html` en kaartpopups.

Het overzicht `/beoordelingen.html` heeft filters voor soort, status en zoektekst.
Van daaruit opent men de inhoud; een lijstregel zelf is geen verificatieknop.
Beheerders openen de geschiedenis via **Beoordelingsgeschiedenis** naast de
paginatitel. Deze knop gaat naar de aparte pagina `/beoordelingsgeschiedenis.html`,
met eigen bladerknoppen en **Terug naar beoordelingen** bovenaan. De geschiedenis
wordt alleen op die pagina geladen, na controle van de beheerdersrol. Ook bij een
rechtstreeks bezoek geldt die controle. Bij accountwisseling of het verlaten van
de pagina worden de geschiedenisgegevens gewist; zonder beheerdersrol wordt men
naar de leesomgeving teruggestuurd.

De eerste geslaagde klik legt de verantwoordelijke vast. Herhaalde of gelijktijdige
klikken overschrijven die persoon niet. **Intrekken** maakt een nieuwe gebeurtenis;
daarna kan iemand opnieuw verifiëren. Geschiedenis wordt nooit overschreven.
Een hoofdstukbeslissing geldt ook voor dezelfde beoordeelde onderdelen van de
afzonderlijke verzen. Dit blijft één auditgebeurtenis met dezelfde verantwoordelijke.
Een latere versintrekking maakt het betreffende onderdeel van het hoofdstuk
onbevestigd; een nieuwe hoofdstukverificatie kan die intrekking weer opvolgen.

## Revisies en weergegeven inhoud

`scripts/build_review_catalog.py` bouwt `data/review-catalog.json` (schema 3).
Een onderwerp heeft een soort, stabiele id, label, link, bronbestand en SHA-256-revisie
van de beoordeelde inhoud. Die totaalrevisie bindt correctietaken en bronbestanden.
Verificatie heeft daarnaast onafhankelijke revisies voor de Bijbeltekst,
kanttekeningen, nootnummers, citaatopmaak, overige tekstopmaak en hoofdstukinleiding.
De tekstvingerafdruk omvat zowel de platte tekst als de woorden in de HTML, zonder
nootmarkeringen of opmaaktags. Locaties hebben één inhoudelijke revisie voor
geometrie en eigenschappen. Woordkoppelingen en historische reviewvlaggen zijn geen tekstbeslissing.

Verandert een onderdeel, dan is uitsluitend dat onderdeel onbevestigd. De oude beslissing,
verantwoordelijke en revisie blijven in het beheerderslog staan. Een nieuwe
gegevenssoort vereist een catalogusadapter en een `Verification.mount` naast de
weergegeven inhoud; accounts en auditopslag hoeven niet opnieuw ontworpen te worden.

De hoofdstukstatus en `verified-chapters` betreffen uitsluitend de Bijbeltekst.
Een intrekking bij één vers maakt het hoofdstuk onvolledig, maar trekt de
hoofdstukbeoordeling zelf niet in. Andere verzen blijven daarvan hun goedkeuring
erven. Na hernieuwde verificatie van het betrokken vers kan die bestaande
hoofdstukgoedkeuring weer volledig gelden, zonder een andere verantwoordelijke
aan het hoofdstuk toe te wijzen. Een expliciete hoofdstukintrekking blijft wel
alle verzen omvatten.
De waarschuwing benoemt alleen ongecontroleerde onderdelen die daadwerkelijk
getoond worden: verborgen kanttekeningen, nootnummers, inleidingen of citaatopmaak
tellen niet mee. Een geopende kanttekening krijgt haar eigen versgebonden melding.
De boodschap onderscheidt gewijzigde inhoud, ontbrekende verificatie, lokale
bewerkingen en correctieverzoeken; ze veronderstelt niet dat iedere wijziging door
AI is gemaakt. De instelling voor nootnummers heet **Nootnummers tonen — klik voor
de kanttekening** onder Weergave, Vertalingen, talen & kanttekeningen.

De leesknop verstuurt uitsluitend de zichtbare onderdelen plus hun revisies.
De API controleert de selectie en legt die vast in de immutable tabel
`review_components`, gekoppeld aan de bestaande auditgebeurtenis. Een expliciete
hele-onderwerpbeoordeling via de API kan `components` weglaten; dan worden alle
onderdelen beoordeeld. Herhaalde goedkeuringen nemen geen bestaande eigenaar over.
Alleen beheerders ontvangen verantwoordelijken, ook bij beoordelingen per onderdeel.

Elke componentbeslissing heeft expliciete dekking: `scope=subject` voor het
onderwerp zelf, of `scope=verses` voor uitsluitend de versrevisies in `members_json`.
Een versgebonden hoofdstukgebeurtenis telt mee bij de betrokken verzen en bij de
samengestelde hoofdstukstatus; zij vervangt geen volledige hoofdstukbeslissing.
De geschiedenis vermeldt bij zo'n gebeurtenis om welke verzen het gaat.

De browser hasht ook de daadwerkelijk geladen bronbytes. De server vergelijkt
deze `sourceHash` bij de klik met de actuele catalogus. Oude caches of een
deployment tussen lezen en klikken kunnen zo geen andere inhoud goedkeuren.
Lokale tekstbewerkingen zijn geen gepubliceerde inhoud en blokkeren verificatie.
De controles horen uitsluitend bij de Open Vertaling, niet bij parallelle edities.

## Privacy

Iedereen kan de status lezen, maar uitsluitend beheerders krijgen
`latestReview`, namen, uid's, e-mailadressen, tijdstippen en notities terug.
Reviewers hebben geen toegang tot het verificatiegeschiedenisendpoint. Correctietaken
hebben een afzonderlijke, voor reviewers zichtbare taakgeschiedenis met redenen
en voorstellen, maar zonder accountidentiteiten. Dit wordt op de
server afgedwongen, niet met alleen verborgen HTML.

API-responses zijn `no-store` en worden nooit in de service-worker-cache gezet.
Bij activatie worden eerder gecachete private responses verwijderd. Bij uitloggen
of accountwisseling worden identiteiten onmiddellijk uit de pagina verwijderd;
late requests mogen ze niet terugplaatsen. Accountwisseling tijdens tokenvernieuwing
mag evenmin een klik onder een ander account uitvoeren.

## Migratie en releasesnapshots

`migrations/review-components-v1.json` reconstrueert 1.442 bestaande beoordeelde
revisies uit hun exacte Git-bronnen. Bij catalogussynchronisatie koppelt
`component-reviews-v1` die onderdelen transactioneel aan de bestaande beslissingen.
Audit-ids, personen, besluiten, tijden en volgorde blijven ongewijzigd. Dit keurt
geen gewijzigde inhoud goed. Ongewijzigde nootmarkeringen/opmaak en tekst behouden
wel hun oorspronkelijke beoordeling. Zonder passende historische bron stopt de
migratie met een serverfout; er wordt nooit een oude revisie uit huidige tekst geraden.

Controleer vóór publicatie of sinds de laatste migratiebouw nieuwe oude-formatreviews
zijn toegevoegd. De audit leest de productiedatabase alleen; Git wordt uitsluitend
door dit bouwscript gebruikt, nooit door de draaiende API:

```bash
python3 scripts/build_component_history.py --audit-host root@open-aec.com
python3 scripts/build_review_catalog.py
```

Optioneel controleert `--database /pad/naar/collaboration.sqlite3` ook een lokale
database. Maak vóór de eerste nieuwe API-start een SQLite-back-up; de eerste
catalogussynchronisatie voert de eenmalige migratie uit. Publiceer schema-3-catalogus,
nieuwe servermodules en lezermodules samen; oude catalogi worden niet ondersteund.

De vroegere, handmatig onderhouden hoofdstuklijst is vervangen door de vaste
migratie `migrations/review-history-v1.json`. Deze bewaart alle 1.141 oude records
met hun inhoudsrevisie en herkomst uit commit
`fcdc46f6773d9daea52b29108c0ac6ba761d44cd`.
`migrations/review-history-v2.json` bewaart daarnaast de 163 hoofdstukken van
de zes op main afgeronde boeken uit commit
`8f37805c8b9d93534fe3d9af7dd2a540cd29b743`. De eerste migratie blijft ongewijzigd.
Bij bestaande databases vult de idempotente migratie
`historical-review-import-v3` ontbrekende historische records aan, zonder
bestaande beslissingen te verwijderen of dubbele imports te maken.

De eigenaar heeft bevestigd dat Maarten Vroegindeweij de bestaande controles
heeft uitgevoerd. Alle historische controles zijn daarom gekoppeld aan zijn
gereserveerde account voor `maartenvroegindeweij@gmail.com`, ook zolang Google-login
nog niet gelukt is. Ongewijzigde, gecontroleerde inhoud blijft geverifieerd;
ontbrekende login is geen ontbrekende controle. Alleen beheerders zien zijn naam
en, zolang nodig, “nog niet aangemeld”. Zijn eerste Google-login activeert hetzelfde
account zonder dubbele gebruiker of herschreven auditgebeurtenissen.

Bij het opstarten voert `server/collaboration_schema.py` de versiegebonden migraties
`account-identity-v1` en `historical-review-attribution-v3` transactioneel uit.
Ook bestaande databases met een ongewijzigde catalogus worden bijgewerkt:
geregistreerde accounts behouden hun id, oude verwijzingen naar inmiddels gekoppelde
placeholderaccounts worden hersteld, en alle historische controles krijgen Maarten
als verantwoordelijke. De migratie bewaart ids, volgorde, inhoudsrevisies, herkomst
en importtijdstippen. Normale API-handelingen kunnen auditgegevens niet wijzigen.

De herkomst blijft `historical-import`; de UI vermeldt dat de oorspronkelijke
controledatum onbekend is en onderscheidt deze van het importtijdstip.
Er wordt geen datum of verantwoordelijke afgeleid uit Git-auteurschap. Latere
accountgebonden goedkeuringen en intrekkingen krijgen voorrang boven imports.
Een gewijzigde inhoudsrevisie vereist opnieuw verifiëren.

Beide lezers halen actuele hoofdstukstatus uit
`GET /api/collaboration/verified-chapters`. De gegenereerde, Git-genegeerde
`data/verified-chapters.json` is alleen een releasesnapshot voor de bouwscripts.
Die bevat uitsluitend lijsten hoofdstuknummers, nooit `"all"` of identiteiten:

```bash
python3 scripts/export_review_status.py --api http://127.0.0.1:8787
python3 scripts/build_stats.py
python3 scripts/build_downloads.py
```

De export weigert een catalogus van een andere release. Statistieken en downloads
weerspiegelen het exportmoment; live leesstatus gebruikt deze snapshot niet.
Zonder geverifieerde hoofdstukken wordt geen EPUB aangeboden en wordt een eerdere
gegenereerde EPUB verwijderd. De ongefilterde brondata-ZIP blijft beschikbaar.
`data/review-history.json` bewaart historische totaalaantallen, geen accountbeslissingen.

## Lokale controle

Bouw de catalogus en start de API met een eigen testdatabase:

```bash
python3 scripts/build_review_catalog.py
OV_COLLABORATION_DB=/tmp/openvertaling-review.sqlite3 \
OV_REVIEW_CATALOG="$PWD/data/review-catalog.json" \
OV_STATIC_ROOT="$PWD" \
python3 server/collaboration_api.py
```

Open `http://localhost:8787/index.html` of `/gebruikers.html`.
Voor echte Google-login moet localhost in Firebase Authentication toegestaan zijn.
Python 3 met `cryptography` is vereist. De automatische tests gebruiken uitsluitend
tijdelijke databases en synthetische testidentiteiten, nooit echte accounts:

```bash
python3 -m unittest discover -s tests -p 'test_collaboration_system.py'
python3 -m unittest discover -s tests -p 'test_direct_verification.py'
python3 -m unittest discover -s tests -p 'test_ghost_verification.py'
python3 -m unittest discover -s tests -p 'test_verification_exports.py'
node --test tests/verification-sw.test.cjs
node --test --test-timeout=60000 tests/verification.browser.test.cjs
```

Voor de browsertest zijn het Node-pakket `playwright` en Chrome vereist
(standaard `/usr/bin/google-chrome`, instelbaar met `CHROME_PATH`).
Deze test start zelf een echte lokale API en controleert beide lezers,
locaties, rechten, accountwisseling, bronrevisies en doorlopend lezen.

## Deployment

De workflow voor aanvragen, handmatige AI-verwerking en acceptatie staat in
[`correction-workflow.md`](correction-workflow.md). Een geaccepteerd voorstel
verandert geen live bestanden en wordt nooit automatisch geverifieerd.

De GitHub-deployworkflow is op main verwijderd; publicatie gebeurt rechtstreeks
via de bestaande servertoegang. Publiceer een gecontroleerde commit vanuit een
private stagingmap, niet vanuit een volledige lokale werkmap.

Maak vóór publicatie een SQLite-back-up en bewaar de vorige website en API.
Bouw de naslagbundels, illustratie-index en reviewcatalogus in staging. De
statische site krijgt geen `.git`, `.github`, `.claude`, `server` of `migrations`.
Bewaar de bestaande externe audio en gegenereerde verificatiesnapshot/downloads
tot hun vervangers zijn gebouwd.

`server/install_collaboration_api.sh` installeert de API als
`openvertaling-collaboration.service`, met een Nginx-proxy onder
`/api/collaboration/`. Na de healthcheck exporteert
`scripts/export_review_status.py` de actuele status; bouw daarna statistieken
en downloads. Controleer vervolgens ook de publieke URL en accountkoppeling.

De database staat buiten de webroot en blijft bij deployments intact; neem hem
op in de serverback-up. Serverbroncode en migratiebronbestanden worden uitgesloten
van de publieke site. De catalogus en brondata bevatten geen verifier-identiteiten.
De installer controleert Python-afhankelijkheden, service-health en Nginx-configuratie.
