# Accounts, rollen en beoordelingen

De site gebruikt Firebase Authentication uitsluitend als identiteitsprovider.
De browser stuurt het actuele Firebase ID-token naar dezelfde herkomst onder
`/api/collaboration/`. De API controleert handtekening, project, uitgever,
geldigheid en het geverifieerde e-mailadres voordat een account wordt gebruikt.

De samenwerkingstoestand staat niet in browseropslag of in publieke JSON. De
productieserver bewaart die in:

```text
/var/lib/openvertaling-collaboration/collaboration.sqlite3
```

De twee vaste beheerders zijn:

- `maartenvroegindeweij@gmail.com`
- `real.johnheikens@gmail.com`

Zij hebben ook de reviewbevoegdheid. Een beheerder kan op
`/gebruikers.html` aangemelde accounts doorzoeken en de rollen `administrator`
en `reviewer` toekennen. Een account komt in de lijst zodra het na invoering
van dit systeem eenmaal met Google is aangemeld. De twee vaste beheerders staan
al als nog niet aangemelde accounts in de lijst en worden bij hun eerste sessie
aan hun echte Firebase-uid gekoppeld. Rolwijzigingen worden eveneens als
onveranderlijke gebeurtenissen met uitvoerende beheerder bewaard.

## Generiek beoordelingsmodel

`scripts/build_review_catalog.py` maakt tijdens elke deployment
`data/review-catalog.json`. Een onderwerp heeft altijd:

- een soort, bijvoorbeeld `text-chapter` of `location`;
- een stabiele gegevens-id;
- een label, bronbestand en link naar de gegevens;
- een SHA-256-revisie van uitsluitend de inhoud die wordt beoordeeld.

Een beslissing geldt alleen voor die exacte revisie. Verandert beoordeelde
tekst of locatie-inhoud, dan verschijnt de nieuwe revisie automatisch als te
beoordelen. Nieuwe soorten gegevens worden toegevoegd als een nieuwe
catalogusadapter; rollen en auditopslag veranderen daarvoor niet.

Reviewers werken via `/beoordelingen.html`. Iedere goedkeuring en intrekking
is een nieuwe, onveranderlijke gebeurtenis met uid, naam en e-mailadres zoals
die op dat moment door Firebase zijn bevestigd. De actuele status is de laatste
beslissing voor dezelfde soort, id en revisie. De volledige geschiedenis blijft
zichtbaar voor reviewers en beheerders.

## Bestaande tekststatus

Het vroegere tekstsysteem is geen accountsysteem. De enige bron is
`data/verified-chapters.json`, met per boek `"all"` of een lijst
hoofdstuknummers. `scripts/build_stats.py` telt de verzen in die hoofdstukken en
schrijft totalen naar `data/stats.json`. `data/review-history.json` bevat alleen
gedateerde totaalaantallen; `js/review-chart.js` tekent daar de voortgang en
projectie van. Geen van die bestanden bevat een reviewer of afzonderlijke
beslissing.

Bij de eerste start importeert de API elke bestaande hoofdstukstatus als één
goedkeuring voor de toenmalige teksthash. De actor is bewust
`historical-import` met de zichtbare naam `Onbekend (bestaande reviewstatus)`.
Er wordt geen persoon uit Git-auteurschap afgeleid. Deze import wordt precies
eenmaal uitgevoerd. Een latere tekstwijziging vereist daardoor een nieuwe,
genoemde reviewer.

## Lokale controle

Bouw eerst de genegeerde runtimecatalogus:

```bash
python3 scripts/build_review_catalog.py
```

De API kan met een tijdelijke lokale database worden gestart door de
productievariabelen te overschrijven. Voor Google-login moet de gebruikte
localhost-herkomst in Firebase Authentication als toegestaan domein staan.

```bash
OV_COLLABORATION_DB=/tmp/openvertaling-review.sqlite3 \
OV_REVIEW_CATALOG="$PWD/data/review-catalog.json" \
OV_STATIC_ROOT="$PWD" \
python3 server/collaboration_api.py
```

Open daarna `http://localhost:8787/gebruikers.html` of
`http://localhost:8787/beoordelingen.html`.

## Deployment

De websiteworkflow bouwt de catalogus, installeert de API als de afgeschermde
systemd-service `openvertaling-collaboration.service`, en plaatst alleen een
Nginx-proxy onder `/api/collaboration/`. Serverbroncode wordt uitgesloten van
de publieke site. De installer controleert de Python-afhankelijkheid,
service-health en Nginx-configuratie en herstelt de vorige Nginx-site bij een
mislukte installatie.
