# Liederen en gebeden — chronologie en volledige tekst

**Datum:** 8 augustus 2026
**Status:** vastgesteld, nog niet geïmplementeerd

## Aanleiding en doel

De wiki bevat 31 lied-items en 36 gebedsitems. Een detailpagina toont nu alleen
een toelichting en enkele vindplaatsknoppen. Daardoor moet de lezer de wiki
verlaten om de eigenlijke tekst te lezen. De liederen staan bovendien
hoofdzakelijk in canonieke boekvolgorde, niet consequent in de volgorde van de
Bijbelse gebeurtenissen.

Deze uitbreiding heeft drie doelen:

1. alle lied- en gebedsitems krijgen binnen hun eigen reeks een zichtbaar,
   chronologisch volgnummer;
2. iedere lied- en gebedspagina toont de volledige relevante tekst uit de
   actuele Open Vertaling;
3. de 150 Psalmen blijven één lied-item en staan gezamenlijk op één
   detailpagina.

Liederen en gebeden hebben elk hun eigen nummerreeks. De eerder verwijderde
inleiding boven het gebedenoverzicht keert niet terug.

## Vastgestelde keuzes

| Onderwerp | Keuze |
|---|---|
| Liednummering | Eén reeks `1` t/m `31`, afgeleid van de volgorde in de liederen-data |
| Gebedsnummering | Eén afzonderlijke reeks `1` t/m `36`, afgeleid van de volgorde in de gebeden-data |
| Betekenis van chronologisch | Volgorde van de Bijbelse verhaallijn; niet de moderne datering van de uiteindelijke boekvorm |
| Psalmen | Eén genummerd item met Psalm 1 t/m 150 |
| Gebeden | Chronologisch genummerd en voorzien van de volledige tekst |
| Tekstbron | Uitsluitend `text2026` uit `data/<boek>/<hoofdstuk>.json` |
| Tekstselectie | Expliciete passagegrenzen per item; bestaande `verzen` blijven de navigatie-vindplaatsen |
| Levering aan browser | Automatisch gebouwde, afzonderlijke tekstbundel per item |
| Niet-overgeleverde woorden | Exacte verhalende vindplaats plus een eerlijke melding; geen gereconstrueerde liedtekst |

## Chronologische liedvolgorde

De data-array is de gezaghebbende volgorde. De renderer leidt het zichtbare
nummer af uit de positie in die array, zodat invoegen of verwijderen geen
handmatige hernummeringsfouten veroorzaakt.

| Nr. | Item | Volledige tekstpassage |
|---:|---|---|
| 1 | De lofzang van hen die niet sluimeren (Henoch) | Henoch 39:10–13 en 40:3–7 |
| 2 | Het lied bij de Schelfzee | Exodus 15:1–18 |
| 3 | Het lied van Mirjam | Exodus 15:20–21 |
| 4 | Het lied van de bron | Numeri 21:17–18 |
| 5 | Het lied van Mozes | Deuteronomium 32:1–43 |
| 6 | Het lied van Debora en Barak | Richteren 5:1–31 |
| 7 | De lofzang van Hanna | 1 Samuël 2:1–10 |
| 8 | De beurtzang van de vrouwen | 1 Samuël 18:6–7 |
| 9 | Davids klaaglied over Saul en Jonathan | 2 Samuël 1:17–27 |
| 10 | Het loflied bij de ark | 1 Kronieken 16:7–36 |
| 11 | Davids lied van bevrijding | 2 Samuël 22:1–51 |
| 12 | De laatste woorden van David | 2 Samuël 23:1–7 |
| 13 | De Psalmen — het liedboek | Psalm 1 t/m 150, als één item |
| 14 | Het Hooglied | Hooglied 1:1–8:14 |
| 15 | Het lied van de wijngaard | Jesaja 5:1–7 |
| 16 | Het lied van de sterke stad | Jesaja 26:1–21 |
| 17 | Het loflied van Tobit | Tobit 13:1–21 |
| 18 | De lofzang van Hizkia | Jesaja 38:9–20 |
| 19 | Het gebed van Habakuk, op Sjigjonoth | Habakuk 3:1–19 |
| 20 | Het gezang in de vuuroven | Gezang in de vuuroven 51–90 |
| 21 | Klaagliederen — de klaagzangbundel | Klaagliederen 1:1–5:22 |
| 22 | Het loflied van Judith | Judith 16:1–21 |
| 23 | Het dankgebed van Jezus Sirach | Jezus Sirach 51:1–16 |
| 24 | De lofzang van Maria | Lukas 1:46–55 |
| 25 | De lofzang van Zacharias | Lukas 1:67–79 |
| 26 | De engelenzang | Lukas 2:13–14 |
| 27 | De lofzang van Simeon | Lukas 2:28–32 |
| 28 | De lofzang bij het laatste avondmaal | Mattheüs 26:30 en Markus 14:26; woorden niet overgeleverd |
| 29 | Paulus en Silas in de gevangenis | Handelingen 16:25; woorden niet overgeleverd |
| 30 | Het nieuwe lied | Openbaring 5:8–10 en 14:2–3; alleen 5:9–10 bevat de woorden |
| 31 | Het gezang van Mozes en van het Lam | Openbaring 15:2–4 |

Chronologische uitzonderingen worden niet verzwegen:

- Henoch staat bij zijn verhalende, vóór-de-zondvloedse setting; dit is geen
  uitspraak over de moderne datering van de boekvorm.
- De Psalmen beslaan meerdere eeuwen. Als één verzameling staan ze in de
  Davidische periode, vóór het Hooglied.
- Tobit en Judith staan bij de historische setting van hun verhaal.
- Liederen uit profetische visioenen staan bij de profeet; de eschatologische
  liederen uit Openbaring sluiten de reeks af.

## Chronologische gebedsvolgorde en volledige passages

De gebeden-data wordt de gezaghebbende volgorde voor een afzonderlijke reeks
`Gebed 1` t/m `Gebed 36`. Ook hier geldt de Bijbelse verhaallijn. Ondateerbare
wijsheids- en apocriefe passages staan bij hun traditionele of verhalende
historische setting.

| Nr. | Item | Volledige tekstpassage |
|---:|---|---|
| 1 | Abrahams voorbede voor Sodom | Genesis 18:23–33 |
| 2 | Jakobs gebed voor de ontmoeting met Ezau | Genesis 32:9–12 |
| 3 | Mozes' voorbeden voor Israël | Exodus 32:11–14 en Numeri 14:13–19 |
| 4 | Het gebed van Mozes (Psalm 90) | Psalm 90:1–17 |
| 5 | Het gebed van Jabez | 1 Kronieken 4:10 |
| 6 | Simsons laatste gebed | Richteren 16:28 |
| 7 | Het gebed van Hanna | 1 Samuël 1:10–11 |
| 8 | Davids dankgebed over de belofte | 2 Samuël 7:18–29 |
| 9 | Davids boetgebed (Psalm 51) | Psalm 51:1–21 |
| 10 | Salomo's gebed om wijsheid | 1 Koningen 3:6–9 |
| 11 | Salomo's tempelwijdingsgebed | 1 Koningen 8:22–53 |
| 12 | Het gebed van Agur | Spreuken 30:7–9 |
| 13 | Elia op de Karmel | 1 Koningen 18:36–37 |
| 14 | Josafats gebed | 2 Kronieken 20:5–12 |
| 15 | Jona's gebed uit de vis | Jona 2:1–9 |
| 16 | De gebeden van Tobit en Sara | Tobit 3:1–6 en 3:13–23 |
| 17 | Het gebed van Judith | Judith 9:1–14 |
| 18 | Hizkia's gebed om uitredding | 2 Koningen 19:15–19 |
| 19 | Hizkia's gebed om genezing | Jesaja 38:2–3 |
| 20 | Het Gebed van Manasse | Gebed van Manasse 1–14 |
| 21 | Habakuks gebed | Habakuk 3:1–19 |
| 22 | Het Gebed van Azaria | Gebed van Azaria 25–50 |
| 23 | Het gebed van de ballingen (Baruch) | Baruch 1:15–3:8 |
| 24 | Daniëls boetgebed | Daniël 9:4–19 |
| 25 | Mordechai's gebed | Esther apocrief 13:8–18 |
| 26 | Esthers gebed | Esther apocrief 14:1–19 |
| 27 | Ezra's boetgebed | Ezra 9:5–15 |
| 28 | Nehemia's gebed | Nehemia 1:5–11 |
| 29 | Het boetgebed onder Nehemia | Nehemia 9:5–37 |
| 30 | Het Onze Vader | Mattheüs 6:9–13 en Lukas 11:2–4 |
| 31 | Het gebed van de tollenaar | Lukas 18:13 |
| 32 | Het hogepriesterlijk gebed | Johannes 17:1–26 |
| 33 | Jezus in Gethsemane | Mattheüs 26:39–44 |
| 34 | Het gebed van de gemeente | Handelingen 4:24–30 |
| 35 | Het gebed van Stefanus | Handelingen 7:59–60 |
| 36 | Paulus' gebeden voor de gemeenten | Efeziërs 1:16–23, Efeziërs 3:14–21 en Filippenzen 1:9–11 |

Een grens selecteert altijd volledige verzen. Als een vers eerst de bidder
introduceert en daarna de gebedswoorden geeft, blijft het hele vers staan; de
tekst wordt nooit midden in een vers afgeknipt of herschreven.

## Datamodel

`data/naslag-liederen.json` en `data/naslag-gebeden.json` krijgen per item een
veld `tekstpassages`. Een gewone passage heeft deze vorm:

```json
{
  "boek": "exodus",
  "hoofdstuk": 15,
  "van": 1,
  "tot": 18,
  "label": "Exodus 15:1–18"
}
```

Een passage over meerdere hoofdstukken wordt opgesplitst in één object per
hoofdstuk. Voor de Psalmen mag een compacte boekreeks worden gebruikt:

```json
{
  "boek": "psalmen",
  "vanHoofdstuk": 1,
  "totHoofdstuk": 150,
  "label": "Psalm 1–150"
}
```

Items waarvan de woorden niet zijn overgeleverd krijgen naast hun verhalende
passage een `tekstmelding`. Die melding is redactionele uitleg en wordt niet als
Bijbeltekst vormgegeven.

De bestaande `verzen` blijven bestaan. Ze dienen als compacte vindplaatsen en
links naar de leesweergave; ze bepalen niet langer welke tekst op de
detailpagina verschijnt.

## Bouw en gegevensstroom

Een nieuw script `scripts/build_naslag_teksten.py`:

1. leest beide naslagbestanden;
2. valideert iedere passagegrens tegen de hoofdstukdata;
3. leest uitsluitend `text2026` van ieder geselecteerd vers;
4. schrijft per item één compact bestand naar
   `data/naslag-teksten/<soort>/<id>.json`;
5. stopt met een fout bij een ontbrekend hoofdstuk, vers, tekstveld, dubbel
   item-id, een ander aantal dan 31 geordende lied-items of een ander aantal
   dan 36 geordende gebedsitems.

Er is bewust geen terugval op `text1637`, `textSV1888` of `text2026_html`.
Daardoor kan een onvolledige Open Vertaling niet ongemerkt worden vermengd met
een andere tekst of met redactionele HTML.

Afzonderlijke item-bestanden voorkomen dat een bezoek aan één kort gebed de
tekst van alle liederen en gebeden downloadt. De uitzonderlijk grote
Psalmen-bundel is één verzoek in plaats van 150 losse hoofdstukverzoeken. De
bundels zijn afgeleid materiaal: het bouwscript wordt opgenomen in de lokale
sitebuild en de deploybuild, en tests bewaken dat het resultaat overeenkomt met
de bronhoofdstukken.

## Weergave

### Overzicht Liederen

- iedere tegel krijgt een compact gouden nummerlabel `Lied 1`, `Lied 2`, …;
- de tegelnaam en het bestaande aantal vindplaatsen blijven staan;
- de DOM-volgorde is tevens de chronologische volgorde;
- het overzicht Gebeden krijgt op dezelfde wijze `Gebed 1` t/m `Gebed 36` en
  behoudt geen inleidende tekst of lege introductiebox.

### Detailpagina

De volgorde wordt:

1. teruglink;
2. klein nummerlabel `Lied N` of `Gebed N`;
3. titel en bestaande beschrijving;
4. kop `Volledige tekst`;
5. één of meer passageblokken met referentiekop, versnummer en letterlijke
   `text2026`-tekst;
6. eventuele melding dat woorden niet zijn overgeleverd;
7. bestaande vindplaatsknoppen.

De renderer toont eerst titel en beschrijving, daarna een rustige laadmelding
voor de tekstbundel. Bij een netwerk- of parseerfout blijft de rest van de
pagina bruikbaar en verschijnt: `De volledige tekst kon niet geladen worden.`
De vindplaatsknoppen blijven dan beschikbaar.

### Psalmen

De ene Psalmen-detailpagina bevat alle 150 psalmen. Boven de tekst staat een
compacte springlijst 1–150. Iedere psalm heeft een eigen anker en kop; daaronder
staan alle verzen. De psalmen worden niet als 150 afzonderlijke wiki-items of
liednummers gepresenteerd.

## Vormgeving en toegankelijkheid

- nummerlabels gebruiken de bestaande goud/marineblauwe wiki-vormtaal;
- passageblokken blijven sober: geen kaartenraster voor lange tekst;
- versnummering wordt semantisch van de verstekst onderscheiden en blijft ook
  bij kopiëren begrijpelijk;
- ankers en links zijn met het toetsenbord bereikbaar;
- de mobiele kolom houdt de bestaande 16px-leesmarge;
- de implementatie blijft geschikt voor iPadOS 15.4 en gebruikt geen
  lookbehind of niet-ondersteunde nieuwe browser-API's.

## Tests

### Bouwtests

1. alle `tekstpassages` verwijzen naar bestaande hoofdstukken en verzen;
2. elk geselecteerd vers heeft een niet-lege `text2026`;
3. de gebouwde tekst is byte-voor-byte gelijk aan de tekst uit de brondata;
4. de 31 liednummers en 36 gebedsnummers zijn per reeks uniek, oplopend en
   aaneengesloten;
5. de Psalmen zijn één lied-item en de bundel bevat precies 150 psalmkoppen;
6. samengestelde items bewaren de opgegeven passagevolgorde;
7. niet-overgeleverde liedwoorden hebben een `tekstmelding`.

### Browsertests

1. het liederenoverzicht toont `Lied 1` t/m `Lied 31` in DOM-volgorde;
2. het gebedenoverzicht toont `Gebed 1` t/m `Gebed 36` in DOM-volgorde;
3. een gewone lieddetailpagina toont de volledige eerste en laatste versregel;
4. een gebed met meerdere passages toont alle passagekoppen en zijn nummer;
5. de Psalmen-pagina biedt ankers 1 t/m 150 en toont de tekst van Psalm 1 en
   Psalm 150;
6. een item zonder overgeleverde woorden toont de melding en geen verzonnen
   liedtekst;
7. een mislukte tekstfetch laat titel, beschrijving en vindplaatslinks staan;
8. het gebedenoverzicht bevat geen `.ns-lead`.

## Buiten scope

- afzonderlijke liednummers voor de 150 Psalmen;
- reconstructie van niet-overgeleverde liedwoorden;
- kanttekeningen, Strong's-nummers, grondtekst of parallelvertalingen in de
  volledige tekstblokken;
- audio of meezingweergave;
- wijzigingen aan de Bijbelvertaling zelf.
