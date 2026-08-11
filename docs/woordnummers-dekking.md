# Dekking van Strong- en projectwoordnummers

Stand na de eerste corpusprojectie van 11 augustus 2026.

## Bronkeuze voor Nederlandse inline-koppelingen

De gekozen reviewleidraad is de release
[`v5.6`](https://github.com/BSB-publishing/bsb2usfm/releases/tag/v5.6) van
`BSB_full_strongs_usj.zip`. Deze release bevat USJ 3.1 met een Strong-veld per
Engels woord of woordgroep. De Nederlandse tekst wordt niet uit deze bron
afgeleid of vervangen: een redacteur koppelt uitsluitend de reeds aanwezige
Nederlandse woorden aan de Strong-volgorde, waarna de importer die koppeling
tegen de lokale Hebreeuwse of Griekse grondtekst controleert.

Exacte pin:

- release: `v5.6`, tag-object `dd0f4727faff9c955fb5490ba150556f6a47df88`;
- releasecommit: `1a8041f6423766e18910fd78b4269c79085cc6df`;
- archief-SHA-256: `F54D638DA042D6BDF11D6A5A2EEF4DE84AAE0CDC276011BD61F4B1C3E0E002C7`;
- pilotbestand `44JHNBSB_full_strongs.usj`, SHA-256
  `A2CA71DF29E4F7CBFBD126E763DDCCA1A82512F0B4AB19A862646A8372BBC45B`;
- licentie: de Bijbeldata in de USJ-release is door de uitgever aan het
  publieke domein gewijd; het project levert daarnaast een permissieve
  fallback voor rechtsgebieden waar een publieke-domeintoewijding niet
  volledig wordt erkend. Zie de primaire
  [licentie-uitleg](https://github.com/BSB-publishing/bsb2usfm/blob/main/LICENSING_INFO.md)
  en de [formele toewijding](https://github.com/BSB-publishing/bsb2usfm/blob/main/UNLICENSE).

Andere onderzochte primaire bronnen zijn bewust niet als aligneringsleidraad
gekozen:

- [Open Scriptures Hebrew Bible `v2.2`](https://github.com/openscriptures/morphhb/releases/tag/v.2.2)
  heeft uitstekende Hebreeuwse woord-, lemma- en morfologiedata. De WLC-tekst
  is publiek domein en de annotaties zijn CC BY 4.0, maar de dataset koppelt
  geen Engelse vertaalwoorden aan de brontokens.
- [MorphGNT SBLGNT](https://github.com/morphgnt/sblgnt) levert Griekse tekst en
  morfologie, maar geen Strong-gekoppelde Engelse woordalignering. Bovendien
  gelden voor tekst en parsing afzonderlijke licentievoorwaarden, zodat deze
  bron voor deze specifieke pipeline geen voordeel biedt.
- [unfoldingWord Literal Text `v89`](https://git.door43.org/unfoldingWord/en_ult/releases/tag/v89)
  bevat gecontroleerde aligneringen, maar is CC BY-SA 4.0. Omdat de gekozen
  publieke-domeinbron hetzelfde beperkte doel zonder share-alike- of
  attributieonzekerheid vervult, wordt deze bron niet geïmporteerd.

De Engelse woordvormen worden niet in het corpus opgeslagen. Alleen de
geverifieerde Strong-volgorde, lokale bronwoorden en de exacte bronpin blijven
als provenance bij iedere Nederlandse mapping bewaard.

## Reproduceerbare inline-pipeline

`data/woordnummers-pilot-johannes.json` bevat de handmatig gecontroleerde
Nederlandse ankers. `scripts/import_inline_woordnummers.py`:

1. controleert de SHA-256 van het uitgepakte USJ-boek;
2. leest de externe Strong-volgorde per vers;
3. vergelijkt elke selectie met expliciete indices in de lokale grondtekst;
4. accepteert alleen `reviewstatus: handmatig_gecontroleerd` met een confidence
   tussen 0 en 1;
5. bewaart dataset, versie, hash, versreferentie en bronindices per mapping;
6. laat een bestaand `(tekst, voorkomen)`-anker altijd ongemoeid.

Na het downloaden en uitpakken van het gepinde releasearchief:

```powershell
python scripts/import_inline_woordnummers.py `
  --review data/woordnummers-pilot-johannes.json `
  --source-dir C:\pad\naar\BSB_full_strongs_usj
```

Dit is standaard een droge run. Schrijven vereist expliciet `--write`. Een
herhaalde droge run na de pilot meldt `added: 0` en `preserved: 43`.

## Inline-dekking

Voor deze wijziging waren er nul gecontroleerde Nederlandse inline-mappings.
Na de pilot:

- Johannes 1:1-5: 5 verzen, 43 Nederlandse ankers en 61 gekoppelde
  Strong-voorkomens;
- 5 van 35.932 verzen met Hebreeuwse of Griekse Strongdata zijn inline gedekt
  (0,01392%);
- 61 van 519.959 Hebreeuwse/Griekse Strong-voorkomens zijn aan gecontroleerde
  Nederlandse ankers gekoppeld (0,01173%);
- alle 43 mappings hebben `confidence: 1.0` en
  `reviewstatus: handmatig_gecontroleerd`;
- de Nederlandse `text2026`-velden zijn ongewijzigd.

Volledige corpusdekking is niet veilig automatisch haalbaar. De externe
Engelse woordvolgorde wijkt geregeld af van zowel de Nederlandse woordvolgorde
als de lokale grondtekst; daarnaast bevat de bron alleen de 66 canonieke
boeken, terwijl dit corpus 88 boeken telt. Uitbreiding vereist daarom per
segment expliciete redactionele review.

## Gefaseerde corpusprojectie

`scripts/build_woordnummers_corpus.py` verwerkt inmiddels alle 88 boeken. De
projectie gebruikt de lokale bronwoorden en Strong-nummers en zoekt uitsluitend
exacte Nederlandse woordmatches in de bestaande Nederlandse BDB- en
Abbott-Smith-overlays. De bronbestanden zijn reproduceerbaar gepind met:

- `bdb-nl.json`: SHA-256
  `70C1D6375D25E482E80646C5CC0957EDB8EF135BC828C12D6C55064DDBEB9CCA`;
- `abbott-nl.json`: SHA-256
  `C6CFBA1DDEB56A3117F9BC8634CA5D77560AF7B44E2254F642350E699E1C43C1`.

Een exacte lexiconmatch wordt alleen zichtbaar wanneer het hoofdstuk ook in
`data/verified-chapters.json` als menselijk nagekeken staat. Zo'n mapping krijgt
`reviewstatus: automatisch_hoog_vertrouwen` en `confidence: 0.95`. Een
positionele fallback krijgt `reviewstatus: review_nodig`, wordt wel geteld maar
niet gepubliceerd. Bestaande handmatige `(tekst, voorkomen)`-ankers winnen
altijd van gegenereerde mappings.

De eerste fase omvat 54 boeken met geheel of gedeeltelijk nagekeken tekst:

- 20.376 verzen met H/G-brondata;
- 19.935 verzen met ten minste één zichtbare inline-link (97,84%);
- 298.041 Strong-voorkomens in totaal;
- 61 handmatig gecontroleerde en 226.986 automatisch hoog-vertrouwenlinks
  zichtbaar: samen 227.047, oftewel 76,18%;
- 70.994 koppelingen blijven in de menselijke reviewwachtrij.

De tweede fase inventariseert ook alle overige boeken, maar publiceert daar nog
geen automatische mappings zolang de Nederlandse hoofdstuktekst niet als
nagekeken geldt. Corpusbreed zijn 519.959 H/G-koppelingen geïnventariseerd:
227.047 zichtbaar en 292.912 wachtend op review. De precieze actuele status van
ieder boek staat in
[`woordnummers-status-per-boek.md`](woordnummers-status-per-boek.md) en de
machineleesbare bron staat in `data/woordnummers-inline/status.json`.

Reproduceer de volledige projectie en het statusrapport met:

```powershell
python scripts/build_woordnummers_corpus.py --write
python scripts/audit_woordnummers.py
```

## Wat automatisch is aangevuld

`scripts/fill_woordnummers_from_repo.py` hergebruikt alleen een nummer wanneer
dezelfde bronwoordvorm elders in het corpus exact gelijk is geschreven en daar
steeds aan precies hetzelfde nummer is gekoppeld. De controle is bovendien
beperkt tot de passende nummerfamilie:

- Grieks: `G`;
- Ge'ez: `OVG`;
- Latijn: `OVL`.

Hebreeuws is van deze automatische route uitgesloten. Een Hebreeuws
suffixsegment kan qua zichtbare vorm samenvallen met een ander lemma; een
oppervlaktevergelijking is daar dus geen betrouwbare koppeling.

De eerste ronde heeft 802 bestaande, deterministische koppelingen hersteld:

- 105 Griekse Strong-nummers;
- 697 Ge'ez-woordnummers.

Daarnaast bevatten de drie Meqabyan-bronbestanden in de repo expliciete
hoofdstuk- en versnummers. Daarmee zijn 638 ontbrekende grondtekstverzen
hersteld, samen goed voor 10.009 Ge'ez-tokens. Vanuit het bestaande
Ge'ez-lexicon konden daarvan 6.025 tokens direct worden genummerd. Een tweede
exacte vergelijkingsronde leverde vervolgens nog 149 eenduidige
`OVG`-koppelingen op. In totaal zijn daarmee 6.976 woordnummers toegevoegd.

Na de schrijfronde levert een nieuwe droge run nul verdere veilige kandidaten
op. Ambigue woordvormen worden altijd overgeslagen.

## Actuele dekking

- 88 van de 88 boeken bevatten woordnummers;
- 41.132 verzen in het corpus;
- 40.375 verzen met grondtekst, waarvan 40.366 ten minste één woordnummer
  bevatten;
- 607.694 grondteksttokens, waarvan 580.354 genummerd (95,50%);
- 297.919 `H`, 222.040 `G`, 13.802 `OVL` en 46.593 `OVG`-koppelingen;
- geen ongeldige nummerfamilies aangetroffen.

## Bewust niet automatisch ingevuld

Er blijven 27.340 grondteksttokens zonder nummer. Het absolute aantal is na
deze ronde hoger, omdat 10.009 eerder geheel ontbrekende brontokens nu wel
zichtbaar en controleerbaar zijn:

- 12.886 Ge'ez-lexemen zonder bestaande eenduidige `OVG`-koppeling;
- 7.250 Griekse lexemen zonder bestaande eenduidige `G`-koppeling;
- 5.925 Hebreeuwse grammaticale suffixsegmenten waarvoor geen zelfstandig
  Strong-lemma aanwezig is;
- 1.268 niet-lexicale bronmarkeringen, hoofdzakelijk versnummers en
  interpunctie in aangeleverde bronregels;
- 11 overige Hebreeuwse lexemen of namen waarvoor de repo geen eenduidige
  bronkoppeling bevat.

Deze tokens mogen pas worden aangevuld vanuit een expliciete lexicale bron of
na handmatige broncontrole. Een nummer afleiden uit de Nederlandse vertaling,
een gelijkende spelling of de context is nadrukkelijk niet toegestaan.

## Verzen zonder grondtekst

Voor 757 verzen is in de hoofdstukdata nog geen bruikbare grondtekstarray
aanwezig: bij 497 ontbreekt het veld en bij 260 is de array leeg. Dit betreft
vooral bronhiaten in de Ethiopische en apocriefe boeken, naast canonieke
versificatie- en tekstvariantplaatsen. Zonder een expliciete bron- en
versificatiekoppeling kunnen deze verzen niet veilig automatisch worden
ingevuld.

Het volledige, per boek en per vers uitgesplitste overzicht wordt steeds uit
de actuele corpusdata opgebouwd met:

```powershell
python scripts/audit_woordnummers.py
```

Een veilige droge proef en schrijfronde zijn respectievelijk:

```powershell
python scripts/fill_woordnummers_from_repo.py
python scripts/fill_woordnummers_from_repo.py --write
```
