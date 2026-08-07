---
name: ov-herschrijven
description: Gebruik bij elke tekstwijziging aan de Open Vertaling — een woord moderniseren, een lezersmelding verwerken, citaatopmaak rechtzetten, of een principe Bijbelbreed doorvoeren. Ook bij het opruimen van schade uit eerdere sweeps (kromme zinnen als "van JAHWEH pascha", homoniemen die de verkeerde kant op zijn omgezet).
---

# De Open Vertaling herzien

## Overzicht

De Open Vertaling is een herziening van de Statenvertaling 1888, geen nieuwe
vertaling. Dat onderscheid stuurt alles.

**Kernprincipe: de zinsbouw van de Statenvertaling blijft staan; alleen wat een
hedendaagse lezer niet meer begrijpt gaat eruit.** Wie een zin herschrijft omdat
hij hem mooier vindt, is aan het vertalen en niet aan het herzien.

Elke wijziging loopt via een **principe** — een genummerde regel in
`data/wijzigingsprincipes.json` — zodat op elke plaats in de tekst na te gaan is
waaróm daar iets anders staat dan in 1888.

## Wat wel en niet

| Wel | Niet |
|---|---|
| `moei` → `tante`, `guichelaar` → `bezweerder` | zinnen inkorten of splitsen |
| `des HEEREN huis` → `het huis van JAHWEH` | beeldspraak uitleggen in de tekst zelf |
| aanvoegende wijs → gewone vorm | een vertaalkeuze stilzwijgend inbouwen |
| verouderde verbuiging herstellen | woordvolgorde moderniseren omdat het "vlotter leest" |

Bij een vertaalkeuze (Exodus 21:6 *goden* of *rechters*?) beslist de eigenaar van
het project, niet de herziener. Vraag het, en leg het antwoord vast in de
toelichting van het principe.

## De eerste-linie-regel

**Een principe werkt éénmalig, vanuit de Statenvertaling-1888 als basis. Wat een
principe heeft opgeleverd mag nooit door een tweede principe worden aangepakt.**

Bepaal dus wélke plaatsen in aanmerking komen door naar **`textSV1888`** te
kijken, nooit naar `text2026` — die bevat al eerdere vervangingen. Pas de
wijziging vervolgens toe op `text2026` én `text2026_html`.

Zonder deze regel hangt de uitkomst af van de volgorde waarin sweeps toevallig
draaien. Dat is echt gebeurd: `V139` (vroedvrouw → verloskundige) en `V969` (het
omgekeerde) hieven elkaar op totdat er één werd verwijderd.

`scripts/audit_principes.py` controleert op omkeringen, ketens, dubbele id's en
hetzelfde bronwoord met verschillende uitkomsten. Draai die na élke toevoeging.

Eén uitzondering waar de regel te strak is: als een eerdere sweep de vorm al
veranderde (`des heirs` werd `van het heir`), toets dan op de aanwezigheid van
het woord in `textSV1888`, niet op de exacte vorm. Anders blijft het werk half af.

## De vier valkuilen

Dit zijn geen bedachte risico's. Alle vier zijn in deze tekst voorgekomen.

### 1. Homoniemen

`wassen` betekent in het Nederlands zowel groeien als schoonmaken. Principe V45
(`wassen (groeien)` → `groeien`) is zonder onderscheid toegepast, en toen werd de
voetwassing in Johannes 13 een groei-wonder: *"Heere, zult U mij de voeten
groeien?"* Vijfentwintig plaatsen, waaronder Farao's dochter die zich ging
*groeien* in de rivier.

**Toets op de omgeving, niet op het woord.** Staat er water, kleren, handen,
voeten, een rivier in de buurt? Dan gaat het over wassen. Staat er vermeerderen,
overvloedig, gras, geloof? Dan over groeien. Kun je dat onderscheid niet
automatiseren, doe het dan met de hand.

Let ook op: `leger` (krijgsmacht én slaapplaats én kampement), `rok`, `hoed`,
`voeten` (lichaamsdeel én voetstuk), `rein` (schoon én ritueel rein).

### 2. Kromme zinnen na een sweep

De genitief-sweep maakte van `des HEEREN pascha` niet *het pascha van JAHWEH*
maar **`van JAHWEH pascha`** — het lidwoord verdween en de woordvolgorde bleef
die van de oude naamval. Zo bleven er ook staan: *"van het volk stem"*, *"van uw
hater ezel"*, *"aan van zijn naasten bezittingen"*.

Verwante schade uit hetzelfde soort ingreep:

| Wat er staat | Wat het moet zijn | Oorzaak |
|---|---|---|
| `de heel dag` | `de hele dag` | verbogen uitgang weggevallen |
| `een brandoffer JAHWEH` | `een brandoffer voor JAHWEH` | derde naamval zonder voorzetsel |
| `hernstig verheven` | `hoog verheven` | `hogelijk` verminkt geraakt |
| `diens bergs` | `van die berg` | naamval helemaal overgeslagen |

**Controleer na elke sweep wat hij heeft áchtergelaten, niet alleen wat hij heeft
veranderd.** Zoek op het patroon dat had moeten verdwijnen. Een sweep die 200
plaatsen raakt en er 40 half doet is erger dan geen sweep.

### 3. Congruentie

`jonge dochter` → `meisje` leverde *"En die meisje"* op: *meisje* is onzijdig en
*dochter* niet. `drenkte` → `gaf te drinken` leverde *"gaf te drinken haar
kudden"* op, want de woordvolgorde verandert mee bij een samengesteld werkwoord.

Lees na een sweep een handvol getroffen verzen helemaal door. Niet het fragment
rond het vervangen woord — de hele zin.

### 4. Bereik

Sommige woorden hebben alleen in bepaalde hoofdstukken een andere betekenis.
`voeten` zijn in Exodus 26–38 voetstukken van de tabernakel, maar op 360 andere
plaatsen gewoon voeten. `goden` zijn in Exodus 21–22 de rechtbank, maar in 40
boeken afgoden.

Zulke principes krijgen een **bereik**: het veld `bereik` in
`wijzigingsprincipes.json` beperkt ze tot genoemde boeken of hoofdstukken. Zonder
bereik zou je moeten kiezen tussen fout in de tabernakel of fout in de rest van
de Bijbel.

### 5. Half doorgevoerde principes

Een principe dat alleen de vorm uit het voorbeeld vervangt laat de rest van het
paradigma staan. `geschieden` → `gebeuren` was op de infinitief toegepast; 946
keer *geschiedde*, *geschied* en *geschiedt* stonden er nog, zodat oude en
nieuwe vormen door elkaar heen voorkwamen — opvallender dan wanneer er niets
was gebeurd. Neem bij élk principe meteen alle vervoegingen en verbuigingen
mee, en zet ze in de definitie.

## Werkwijze voor één principe

1. **Onderzoek de tekst.** Hoe vaak komt het woord voor in `textSV1888`, in
   hoeveel boeken, en in welke betekenissen? Zoek ook op **alle vervoegingen en
   verbuigingen** — `heir` bleek `heiren`, `heire`, `heirs`, `heirkracht` te
   hebben; `geschieden` had 946 vervoegde vormen die de eerste doorvoering liet
   staan. Bekijk de contexten voordat je een uitkomst kiest: bij `guichelaar`
   bleek uit Deuteronomium 18:10 dat *tovenaar* en *waarzegger* in dezelfde
   opsomming staan, dus die vielen af.
2. **Leg het principe vast, met alle vormen.** `oud` en `nieuw` noemen elke
   vervoeging: `zieden / ziedt / ziedende / gezoden / zood` →
   `koken / kook / kokende / gekookt / kookte`. Een principe dat alleen de
   infinitief noemt is half af. Controleer met `audit_principes.py` dat de
   uitkomst niet het bronwoord van een ander principe is, en dat het bronwoord
   niet al ergens anders behandeld wordt — dubbels sluipen erin.
3. **Vervang** op `text2026` én `text2026_html`, met de eerste-linie-toets op
   `textSV1888`. Regenereer `phraseDiff` en zet het principe-id op het paar.
4. **Controleer met AI of de zinsbouw nog klopt.** Dit is een aparte stap, geen
   bijgedachte. Een woordvervanging die zelf goed is laat geregeld een kromme
   zin achter: het lidwoord hoort bij het oude woord (`de voorhang` → `het
   voorhangsel`), de woordvolgorde hoorde bij de oude naamval (`des HEEREN
   pascha` → *van JAHWEH pascha*), het betrekkelijk voornaamwoord loopt niet mee
   (`het voorhangsel, die`), of een samengesteld werkwoord eist een andere
   volgorde (`drenkte` → *gaf te drinken haar kudden*). Lees daarom de geraakte
   verzen als zín, niet als fragment rond het vervangen woord, en herstel wat
   krom staat — dat herstel is vaak méér werk dan de vervanging zelf, en het
   hoort bij het principe.
5. **Draai de naschriften**: `audit_principes.py`,
   `build_principes_data.py` (anders toont de principes-pagina verouderde
   aantallen), en bij een versie ook `build_stats.py` mét argumenten.

### Bekende vormen van kromme zinnen om op te zoeken

Na elke sweep gericht zoeken op wat de sweep kan hebben áchtergelaten:

| Patroon | Voorbeeld van de schade |
|---|---|
| lidwoord past niet bij het nieuwe woord | `de voorhangsel`, `die meisje` |
| naamval-volgorde bleef staan | `van JAHWEH pascha`, `van het volk stem` |
| derde naamval zonder voorzetsel | `een brandoffer JAHWEH`, `reuk JAHWEH` |
| verbogen uitgang weggevallen | `de heel dag`, `levenden os` |
| betrekkelijk voornaamwoord loopt niet mee | `het tentkleed, die` |
| woordvolgorde bij samengesteld werkwoord | `gaf te drinken haar kudden` |
| verminkt woord | `hernstig` (uit `hogelijk`) |

## Citaatopmaak

De conventie, aangehouden vanuit Genesis:

- De aankondiging blijft **buiten** de span: `En hij zei: <span…>de woorden</span>`
- `god-speaks` voor God, JAHWEH, en Jezus in de evangeliën
- `direct-speech` voor een mens — óók als die tot God spreekt (Mozes in Exodus
  5:22 is mensenspraak)
- Een citaat binnen een citaat is een span binnen een span; de CSS geeft dat het
  gele accent
- Een vers dat een rede voortzet zonder eigen aankondiging krijgt één span over
  het hele vers

`scripts/citaatopmaak.py` biedt `vertelling()`, `rede()`, `na()`, `nest()` en
`klasse()`, en bewaakt bij het opslaan dat de kále tekst onveranderd is en de
opmaak gebalanceerd. Die bewaking heeft meermalen ingegrepen — gebruik hem.

Wat wél te automatiseren is: de aankondiging uit een span halen die het vers
opent (`scripts/citaat_sweep.py`, 270 verzen). De spreker verandert daarbij niet,
alleen de grens.

Wat **niet** te automatiseren is: opmaak aanbrengen waar die helemaal ontbreekt.
De spreker is nog af te leiden, maar het einde van het citaat niet — het
Nederlands hervat de vertelling net zo vaak met een komma als met een punt:

> *"Zeker, die is de koning van Israël, en zij keerden zich naar hem, om te
> strijden"* — alleen het eerste deel is citaat.

`scripts/citaat_ontbreekt.py` maakt daarvan de werklijst, met een voorstel voor
de spreker. Elk vers moet gelezen worden.

## Leesbaarheid buiten de tekst om

Sommige begrippen worden niet duidelijker door een ander woord, maar door een
hulpmiddel naast de tekst. Die staan los van de principes en veranderen de
brontekst **niet** — het zijn weergave-opties.

| Wat | Waar |
|---|---|
| maten en gewichten omrekenen (bijbels / metrisch / imperiaal) | `js/opties.js`, `maateenheden.html` |
| aardrijkskundige namen | wiki, kaart |
| stamboom vanaf Adam | `stamboom.html` |
| begrippenlijst per boek | `data/begrippenlijst-*.json` |

Bouw je zo'n hulpmiddel: volg de opzet van het maatstelsel. Een optie, een
functie die op de gerenderde tekst werkt, en een uitlegpagina met bronvermelding.
Raak `data/` niet aan — wat er in de vertaling staat blijft staan.

## Lezersmeldingen

Komen binnen via een Google Formulier in een spreadsheet. Ophalen:

```bash
python scripts/lees_opmerkingen.py            # openstaande
python scripts/lees_opmerkingen.py --alles    # ook afgehandelde
```

Een melding is niet altijd een suggestie. Tussen 117 opmerkingen over Exodus
zaten vier echte fouten die de lezer als suggestie formuleerde — waaronder de
voetwassing. Lees ze dus als waarnemingen, en ga na of er iets stuk is voordat je
een woord vervangt.

## Een boek afronden — uitgavechecklist

Telkens dezelfde stappen, in deze volgorde; het overslaan van één ervan is elke
keer opgevallen:

1. `data/verified-chapters.json`: het boek op `"all"` — dit stuurt de
   concept-markering in de inhoudsopgave.
2. `python scripts/build_stats.py vX.Y.Z "d maand jjjj"` — **mét argumenten**,
   anders zet hij de versie stilletjes terug.
3. `python scripts/build_principes_data.py` — anders toont de principes-pagina
   verouderde aantallen en missen nieuwe principes hun vindplaatsen.
4. Changelog (`data/changelog.json`): **concreet**. Elk gewijzigd woord met het
   aantal plaatsen (`vorsen → kikkers (15)`), niet "diverse woorden
   gemoderniseerd". Beperkt aantal regels mag; vaagheid niet.
5. `sw.js`: `VERSION` ophogen — anders serveert de service worker oude
   bestanden en lijkt de wijziging niet aangekomen. Let op: de regel is al
   eens door een slordige `sed` afgekapt; controleer met `node --check`.
6. Push, en **controleer dat de uitrol echt gedraaid heeft**: de push-trigger
   heeft weleens niets gedaan. `gh run list` na de push; zo nodig
   `gh workflow run deploy.yml --ref main`, en daarna live nameten
   (`curl` op `sw.js` en een gewijzigd databestand).

Het versienummer in de bovenbalk komt uit `data/stats.json` en hoeft nergens
met de hand gezet.

## Lezersmeldingen verwerken

Ophalen: `python scripts/lees_opmerkingen.py` (via de gepubliceerde CSV van de
spreadsheet). Regels met "Test" of "mag weg" zijn controleregels.

Een melding is kort ("Citatie", "alternatief") en wijst vaak naar iets dat
groter is dan het genoemde vers — één melding over Exodus 8 bleek voor 24 van
de 32 verzen te gelden, en één woordmelding bleek een Bijbelbreed patroon.
Onderzoek dus eerst de omvang, meld terug wat er wérkelijk aan de hand was, en
verwerk de melding als principe en niet als losse correctie.

## Veelgemaakte fouten

| Fout | Gevolg |
|---|---|
| JSON wegschrijven met een vaste inspringing | De repo heeft per bestand 1 of 2 spaties; een vaste waarde herschrijft duizenden regels. Detecteer met `re.search(r'\n( +)"', ruw)`. |
| `build_stats.py` zonder argumenten draaien | Zet de versie stilletjes terug. Altijd `python scripts/build_stats.py v0.27.0 "5 augustus 2026"`. |
| `sw.js` niet ophogen | De service worker serveert oude bestanden; de wijziging lijkt niet aan te komen. |
| Alleen `text2026` wijzigen | De site toont `text2026_html`; de wijziging is onzichtbaar. |
| Een regex met lookbehind | Werkt niet op iPadOS 15.4 en maakt de hele Bijbeltekst onzichtbaar. |

## Volgorde van werken

`git pull --rebase` vooraf — er werken meerdere sessies op `main`. Commit per
logische eenheid, niet alles opgespaard. De commit-boodschap legt uit waaróm, en
noemt wat er níet gedaan is en waarom niet.
