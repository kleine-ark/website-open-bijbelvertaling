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
