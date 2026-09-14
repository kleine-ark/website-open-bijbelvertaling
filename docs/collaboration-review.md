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
Een account verschijnt zodra het eenmaal met Google bij dit systeem is aangemeld.
Dit is geen overzicht van nog nooit aangemelde Firebase-accounts.

- Gewone accounts kunnen lezen, maar niet verifiëren.
- `reviewer` (“Mag verifiëren”) kan inhoud verifiëren en verificaties intrekken.
- `administrator` kan daarnaast accounts/rechten beheren en verantwoordelijken
  en de volledige geschiedenis zien. Deze rol omvat altijd `reviewer`.

De vaste beheerders zijn `maartenvroegindeweij@gmail.com` en
`real.johnheikens@gmail.com`. Hun gereserveerde account wordt bij de eerste
sessie gekoppeld aan hun echte Firebase-uid. Hun beheerdersrecht kan niet via
de gebruikerspagina worden verwijderd. Iedere rolwijziging wordt gelogd.
Rechten worden binnen de schrijftransactie opnieuw gecontroleerd: een oude
browsersessie kan een ingetrokken recht niet blijven gebruiken.

## Eén klik, geen toewijzingen

Een bevoegde gebruiker logt in, leest de inhoud en klikt **Verifiëren**.
De server legt zelf de ingelogde uid, naam, het e-mailadres, tijdstip en de
inhoudsrevisie vast. Er is geen persoonselector, eigenaarstoewijzing of
overdrachtsworkflow. Aangeleverde verifier-identiteiten worden geweigerd.

De knop staat bij:

- hoofdstukken en afzonderlijke verzen in `index.html` en `lees.html`;
- locaties in `plaats.html` en kaartpopups.

Het overzicht `/beoordelingen.html` heeft filters voor soort, status en zoektekst.
Van daaruit opent men de inhoud; een lijstregel zelf is geen verificatieknop.

De eerste geslaagde klik legt de verantwoordelijke vast. Herhaalde of gelijktijdige
klikken overschrijven die persoon niet. **Intrekken** maakt een nieuwe gebeurtenis;
daarna kan iemand opnieuw verifiëren. Geschiedenis wordt nooit overschreven.
Hoofdstuk- en versverificaties zijn afzonderlijke beslissingen: het systeem
verzint geen individuele versverificaties uit een hoofdstukbeslissing, of omgekeerd.

## Revisies en weergegeven inhoud

`scripts/build_review_catalog.py` bouwt `data/review-catalog.json` (schema 2).
Een onderwerp heeft een soort, stabiele id, label, link, bronbestand en SHA-256-revisie
van de beoordeelde inhoud. Hoofdstukken omvatten de hoofdstukinleiding,
verstekst/opmaak en kanttekeningen; locaties omvatten geometrie en inhoudelijke
eigenschappen. Woordkoppelingen en historische reviewvlaggen zijn geen tekstbeslissing.

Verandert deze inhoud, dan is de nieuwe revisie onbevestigd. De oude beslissing,
verantwoordelijke en revisie blijven in het beheerderslog staan. Een nieuwe
gegevenssoort vereist een catalogusadapter en een `Verification.mount` naast de
weergegeven inhoud; accounts en auditopslag hoeven niet opnieuw ontworpen te worden.

De browser hasht ook de daadwerkelijk geladen bronbytes. De server vergelijkt
deze `sourceHash` bij de klik met de actuele catalogus. Oude caches of een
deployment tussen lezen en klikken kunnen zo geen andere inhoud goedkeuren.
Lokale tekstbewerkingen zijn geen gepubliceerde inhoud en blokkeren verificatie.
De controles horen uitsluitend bij de Open Vertaling, niet bij parallelle edities.

## Privacy

Iedereen kan de status lezen, maar uitsluitend beheerders krijgen
`latestReview`, namen, uid's, e-mailadressen, tijdstippen en notities terug.
Reviewers hebben geen toegang tot het geschiedenisendpoint. Dit wordt op de
server afgedwongen, niet met alleen verborgen HTML.

API-responses zijn `no-store` en worden nooit in de service-worker-cache gezet.
Bij activatie worden eerder gecachete private responses verwijderd. Bij uitloggen
of accountwisseling worden identiteiten onmiddellijk uit de pagina verwijderd;
late requests mogen ze niet terugplaatsen. Accountwisseling tijdens tokenvernieuwing
mag evenmin een klik onder een ander account uitvoeren.

## Migratie en releasesnapshots

De vroegere, handmatig onderhouden hoofdstuklijst is vervangen door de vaste
migratie `migrations/review-history-v1.json`. Deze bewaart alle 1.141 oude records
met hun inhoudsrevisie en herkomst uit commit
`fcdc46f6773d9daea52b29108c0ac6ba761d44cd`.
Bij bestaande databases vult de idempotente migratie
`historical-review-import-v2` ontbrekende historische records aan, zonder
bestaande beslissingen te verwijderen of dubbele imports te maken.

Historische controles zonder bekend account blijven zichtbaar voor beheerders
als `historical-import`, maar gelden niet als nieuwe accountgebonden verificatie.
Er wordt geen verantwoordelijke afgeleid uit Git-auteurschap. Bestaande benoemde
verificaties blijven geldig zolang hun inhoudsrevisie niet verandert.

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
python3 -m unittest discover -s tests -p 'test_verification_exports.py'
node --test tests/verification-sw.test.cjs
node --test --test-timeout=60000 tests/verification.browser.test.cjs
```

Voor de browsertest zijn het Node-pakket `playwright` en Chrome vereist
(standaard `/usr/bin/google-chrome`, instelbaar met `CHROME_PATH`).
Deze test start zelf een echte lokale API en controleert beide lezers,
locaties, rechten, accountwisseling, bronrevisies en doorlopend lezen.

## Deployment

De websiteworkflow bouwt eerst de catalogus en publiceert de statische site.
Vervolgens installeert hij de API als `openvertaling-collaboration.service`,
met een Nginx-proxy onder `/api/collaboration/`. Na de healthcheck exporteert
de server de actuele status en bouwt hij statistieken en downloads.
Oude releasebestanden blijven tijdens het uploaden bewaard tot die stap slaagt.

De database staat buiten de webroot en blijft bij deployments intact; neem hem
op in de serverback-up. Serverbroncode en migratiebronbestanden worden uitgesloten
van de publieke site. De catalogus en brondata bevatten geen verifier-identiteiten.
De installer controleert Python-afhankelijkheden, service-health en Nginx-configuratie.
