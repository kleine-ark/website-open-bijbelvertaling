# Overdracht — tekstronde 20 augustus 2026

Wat er op 20 augustus 2026 aan tekst en citaatopmaak is gewijzigd, wat het
opleverde, en wat er blijft liggen. Negentien commits, `5bd42d504` tot en met
`d486e8ed8`, alles op `main`. 237 bestanden, 234 daarvan versteksten in 55
boeken.

De ronde ging uitsluitend over **tekst en citaatopmaak** — `data/*/*.json`,
`data/wijzigingsprincipes.json` en `scripts/`. Statistieken, tags, perikopen,
`css/`, `js/` en `*.html` zijn niet aangeraakt.

---

## 1. Wat er is gewijzigd

### Vijfentwintig nieuwe principes, V1504 tot en met V1528

Het bestand telt nu 1528 principes. In volgorde van registratie:

| Id | Van | Naar | Bijzonderheid |
|---|---|---|---|
| V1504 | nooddruft | behoefte | |
| V1505 | roofs | buit | |
| V1506 | gevangenhuis | gevangenis | 20 verzen; geslacht verandert mee, zie V1527 |
| V1507 | branding | vuur | lijkverbranding bij een koningsbegrafenis, niet golfslag |
| V1508 | schatsteden | voorraadsteden | |
| V1509 | veel werks | veel werk | oude tweede naamval na een hoeveelheid |
| V1510 | ten krijge / ten oorloge | voor de oorlog | |
| V1511 | omgang van het jaar | wisseling van het jaar | |
| V1512 | veel waters / vol waters | veel water / vol water | |
| V1513 | dit lezende | dit lezend | |
| V1514 | opzieners | opzichters | **alleen werkbazen en bestuurders**; het kerkelijk ambt blijft opziener |
| V1515 | beroerte / beroerten | onrust / onlusten | valse vriend: nu een hersenbloeding, in de SV tumult |
| V1516 | in welke | waarin / in Wie | *in Wie* waar het over Christus gaat (Efeziërs 1:11, 1:13) |
| V1517 | zeel | touw | behalve Job 30:11, daar een pees → koord |
| V1518 | weinige | weinig | 30 verzen |
| V1519 | heffing | hefoffer | geslacht verandert mee: *deze heffing* → *dit hefoffer* |
| V1520 | stieten | stootten | 8 verzen; uitzondering 2 Kronieken 26:20, zie V1528 |
| V1521 | aan de zijde van het mijne | naast de mijne | |
| V1522 | zestien jaren was | zestien jaar was | |
| V1523 | kunnen niet weer opstaan | kunnen niet meer opstaan | |
| V1524 | gruwelen | gruwelijke dingen | 80 verzen; enkelvoud *gruwel* blijft |
| V1525 | verbintenis | samenzwering | alleen het complot; Numeri 30 is een gelofte en blijft |
| V1526 | behalve | naast / afgezien van | **bereik**; 26 van 85 vindplaatsen (de commit-boodschap zegt 28, dat is een telfout — het `bereik` in het principe klopt) |
| V1527 | het gevangenis / de vuur | de gevangenis / het vuur | herstel van sweepschade, zie §3 |
| V1528 | stieten … met haast van daar | verdreven … haastig vandaar | **bereik**: 2 Kronieken 26:20 |

Bij V1524 moest **V101** mee. Dat maakte van `verfoeiselen` eerst `gruwelen`, en
daarmee zou zijn uitvoer het bronwoord van V1524 worden — een keten waarvan de
uitkomst afhangt van de volgorde waarin sweeps draaien. V101 levert nu meteen
`gruwelijke dingen` op.

Twee uitzonderingen zijn bewust blijven staan:

- **2 Koningen 16:3** houdt `gruweldaden` uit een menselijke review
  (`MR-SK-025`), met de uitdrukkelijke aantekening die keuze niet buiten dat
  vers toe te passen.
- **1 Meqabyan 6:20** houdt `gruwelen`; dat boek heeft geen 1888-brontekst, dus
  de eerstelijnstoets slaat het over.

### Citaatopmaak, vier rondes

**Corpusbrede controle** op de ruim 18.000 spans leverde achttien verzen op. Twaalf
hadden de aankondiging binnen de span; bij negen daarvan bestond het vers uit
niets anders dan die aankondiging, dus is de span helemaal weg. Dat verklaarde
meteen de lege spans die hier vaker opdoken: wie de aankondiging naar buiten
haalt en de lege huls laat staan, levert een zwevend leesteken op. Vijftien
opgeruimd; corpusbreed staat die teller nu op nul.

**Esther** stond op vier manieren tegelijk scheef: vijf spans om verteltekst,
één aankondiging binnen de span (3:8), en 3:3 had juist helemaal geen markering
terwijl er een echte vraag staat.

**Nehemia** (acht verzen) en **1 en 2 Kronieken** (tien verzen): het citaat liep
telkens door in de vertelling. `1 Kronieken 10:4` had "Maar zijn wapendrager
wilde niet" binnen de woorden van Saul; `2 Kronieken 20:37` had het breken van de
schepen binnen de profetie.

**2 Kronieken** kreeg daarnaast achttien verzen met de hand — zie §4 voor wat
daar nog van openstaat.

---

## 2. Nieuw gereedschap

### `scripts/span_om_vertelling.py`

Zoekt de derde soort citaatfout: een heel vers vertelling in een spraak-span,
zodat de lezer cursief te zien krijgt wat niemand uitspreekt.

```bash
python scripts/span_om_vertelling.py --proef --boek 2kronieken
```

Drie soorten, elk met een eigen zekerheid:

- **A** — de span eindigt op een dubbele punt. Alles erin is aankondiging, het
  citaat staat pas in het volgende vers. Span kan weg.
- **B** — er staat een aankondiging in met tekst erachter. Alleen de grens hoeft
  te verschuiven.
- **C** — geen dubbele punt, en er wordt over spreken verteld in plaats van
  gesproken.

Vier remmen houden echte citaten tegen. Zonder die remmen komt het script op 327
verzen; met de remmen op 59.

1. Een **gebiedende wijs** vooraan betekent dat er iemand spreekt. "Spreek tot
   Aäron … en zeg tot hen:" is JAHWEH die Mozes een opdracht geeft.
2. Een **ik, mij of u** binnen de span betekent hetzelfde. Jósafats gebed in
   2 Kronieken 20:8 eindigt op "zeggende:" en zou anders zijn opmaak verliezen.
3. Staat er in de **aankondiging zelf** een ik of mij, dan haalt de spreker
   iemand aan — "God heeft tot mij gezegd:" — en hoort die aankondiging juist
   bínnen de span. Daar is een geneste span nodig, geen grensverlegging.
4. Loopt er vanuit het **vorige vers** al een rede van dezelfde klasse door, dan
   is vertelling hierbinnen vertelling die iemand uitspreekt. Zo vertelt Jezus in
   Lukas 19 een gelijkenis; die moet blijven staan. Dit onderscheidt Lukas 19:15
   (blijft) van Markus 11:6 (weg).

Na afloop wordt per vers getoetst dat de kale tekst niet is veranderd en dat de
opmaak gebalanceerd blijft.

### Bestaand gereedschap dat hierbij hoort

| Script | Waarvoor |
|---|---|
| `scripts/sweep_principe.py` | één principe corpusbreed, volgens de eerstelijnsregel |
| `scripts/citaat_sweep.py` | aankondiging binnen de span, aan het versbegin |
| `scripts/citaat_ontbreekt.py` | citaten zonder enige opmaak; maakt de werklijst |
| `scripts/synchroniseer_opmaak.py` | `text2026_html` bijtrekken op `text2026` |
| `scripts/audit_principes.py` | omkeringen, botsingen, ketens, half toegepast, bereik |
| `scripts/build_principes_data.py` | vindplaatsen voor `principes.html` |

---

## 3. Twee vondsten die het nalopen waard zijn

### Sweepschade vind je door het corpus met zichzelf te vergelijken

Verandert een woord van geslacht, dan blijft het lidwoord ervoor staan. V1506
maakte van `gevangenhuis` (het) `gevangenis` (de), en negentien verzen lang stond
er "in het gevangenis". V1507 maakte van `branding` (de) `vuur` (het), dus
"als de vuur van zijn vaders". **De sweep meldt niets**, want hij keek alleen
naar het woord zelf, en elk vers op zich leest langs zo'n fout heen.

De vondstmethode is het punt. Tel over het hele corpus hoe vaak elk nomen `de`
krijgt en hoe vaak `het`. Komt een woord 336× met `het` voor en 1× met `de`, dan
is die ene bijna altijd sweepschade. Dat gaf 37 treffers, waarvan er 14 echt
fout waren; de rest was gewoon Nederlands — `het beide`, `het wilde gedierte`,
`het is wijsheid` met een loos onderwerp.

Dezelfde vorm werkt breder, op elke verhouding die eigenlijk constant hoort te
zijn: bijvoeglijke naamwoorden (`een geheel grote vuur`), meervoudsuitgangen
(`de zijn` voor `de zijnen`), samenstellingen die uit elkaar vielen (`de koren
hoop`). **Draai zo'n telling na elke sweep die woorden vervangt.**

In Jesaja 42:7 onderscheidt de bron twee woorden, `gevangenis` en
`gevangenhuis`. Die zijn niet tot één samengevoegd: het tweede is `huis van
bewaring` geworden.

### Naast elkaar liggende wijzigingen klonteren samen in de woorddiff

Staan twee wijzigingen naast elkaar, dan voegt `difflib.SequenceMatcher` ze samen
tot één blok — en dan draagt dat blok nog maar één principe-id. Het werk van het
andere principe verdwijnt stilletjes uit de herkomst.

Zo raakten V944 in Ezra 1:6, N3 in 2 Kronieken 17:19 en N1 in Genesis 26:1 hun
koppeling kwijt toen `behalve` ernaast veranderde. `sweep_principe.py` meldt dit
zelf met `!! koppeling … is vervallen door hergroepering`, maar lost het niet op.
**Lees die melding; ze betekent dat er met de hand een blok gesplitst moet
worden.**

### De audit is voor het eerst schoon

`scripts/audit_principes.py` meldt nul punten. De twee resterende ketens zijn
dichtgezet:

- V1067 maakt van `veder` `veren`; V964 zou van `veer` een `doorwaadbare plaats`
  maken. Een sweep daarvan zou de vederen van de arend in 4 Ezra 11 tot
  doorwaadbare plaatsen maken.
- V1107 maakt van `vaarze` `vaars`; V896 zou daar `getemde jonge koe` van maken.

Beide hebben nooit gevuurd — alle tien doorwaadbare plaatsen en de ene getemde
jonge koe komen uit een 1888-tekst zonder `veder` of `vaarze`. Het gevaar zat in
de toekomst. V964 en V896 hebben nu een `bereik` met naam en toenaam, en **een
`bereik` haalt een principe uit de lijst die corpusbreed mag draaien**
(`audit_principes.py` regel 257). Dat is de rem.

---

## 4. Wat blijft liggen

### Verwerkt op 21 augustus 2026

**De 27 B-gevallen van `span_om_vertelling.py` zijn handmatig beoordeeld.**
Negen verzen hadden werkelijk een te ruime span; daar staat de vertellende
aankondiging nu buiten het citaat: Daniël 6:26, Exodus 33:21, Jeremia 4:11 en
46:17, Jesaja 10:13, 28:12 en 37:22, Job 42:7 en Mattheüs 18:22. De overige
achttien zijn doorgaande redes of als geheel aangehaalde Schriftpassages waarin
de spreker iemand anders aanhaalt. Die buitenste span is bewust behouden.

De volledige classificatie staat in
`scripts/apply_citation_review_overdracht.py`; regressietests staan in
`tests/test_overdracht_2026_08_20.py`. Een tweede uitvoering van het script
wijzigt nul verzen.

De oorspronkelijke lijst was:

```
4ezra 4:15, 4ezra 4:35, baruch 3:35, daniel 6:26, exodus 16:16, exodus 32:12,
exodus 33:21, ezechiel 26:2, jeremia 4:11, jeremia 46:17, jesaja 10:13,
jesaja 28:12, jesaja 37:22, job 42:7, johannes 7:36, leviticus 9:3,
lukas 19:20, markus 12:36, markus 7:10, mattheus 15:4, mattheus 18:22,
mattheus 19:5, mattheus 25:23, psalmen 83:5, richteren 9:8, romeinen 9:26,
ruth 2:7
```

```bash
python scripts/span_om_vertelling.py --proef --soorten B --toon 200
```

De achttien resterende detecties zijn dus beoordeelde uitzonderingen, geen open
automatische reparatielijst.

De afgeleide principevindplaatsen en statistieken zijn eveneens opnieuw
gebouwd. `data/stats.json` volgt nu de bron met 1528 principes.

Bij de validatie zijn daarnaast zes menselijke reviewprincipes uit
1 Kronieken (MR-1KR-006, -007, -014, -016, -017 en -018) alsnog tot hun
beoordeelde vers begrensd. De twee omzettingen van *geheiligde dingen* naar
*gewijde gaven* in 2 Koningen 12:18 zijn aan MR-SK-045 gekoppeld. Ook zijn de
release-cacheverwijzingen en regressieverwachtingen gelijkgetrokken met v0.38.0
en de menselijke afronding van 1 Kronieken.

### Concreet en klaar om op te pakken

**De overige open meldingen uit de sheet.** Van de 962 meldingen bleven er 88
open; de eenduidige woorden daaruit zijn nu V1504–V1528. Wat overblijft vraagt
eerst een beslissing. De twee zwaarste:

- `broeders` versus `broers` — ongeveer 700 plaatsen, per geval context
  afhankelijk.
- `leger` → `kamp` (Leviticus 14:8) — **gevaarlijk**: `leger` in de huidige tekst
  is op veel plaatsen juist de uitvoer van V321 (`legermacht`) en O2 (`heir`).
  Een sweep hierop moet de eerstelijnsregel strikt volgen.

### Buiten deze ronde gelaten

- **`data/eenheden.json`** — de meldingen "honderden en duizenden moeten niet als
  eenheid meegenomen worden" (2 Kronieken 23:1, 23:9, 25:23, 27:5) en "mist
  getal" (14:8) gaan over de weergavefunctie die dat bestand uitleest. Dat is
  opmaak.
- **`[Tag onderwerp]`-meldingen** (2 Kronieken 12:15, 16:12, 21:16, 21:18,
  33:19) en de mobiele weergave bij 14:3.
- **2 Kronieken 24:7** is als citaat gemeld, maar er wordt niemand aangehaald:
  "Want als Athalia goddeloos handelde, hadden haar zonen het huis van God
  opengebroken." Vertalingen verschillen of dit nog Joas' woorden zijn of de
  kroniekschrijver. Ongewijzigd gelaten — dit is een eigenaarskeuze.
- **`beroerten` in 2 Kronieken 15:5** staat als `onlusten` via V1515, niet als
  het in de sheet voorgestelde `verwarring`. Het principe bestond al en is niet
  overreden.

---

## 5. Werkafspraken die in deze ronde bleken te tellen

**Nooit `git add -A` of `git add .`.** De werkboom bevat ongecommit werk van een
parallelle woordnummer-sessie. Deze bestanden zijn de hele ronde met rust
gelaten en moeten dat blijven tot die sessie zelf commit:

```
data/1timotheus/6.json   data/ezechiel/32.json   data/ezechiel/33.json
data/ezechiel/37.json    data/ezechiel/45.json   data/ezechiel/48.json
data/jakobus/5.json      data/jeremia/22.json    data/psalmen/18.json
```

**Nootmarkeringen breken de opmaak stil.** Een sweep vervangt een woord in
`text2026` en `text2026_html` met hetzelfde patroon. Staat er een
`<sup class="note-marker">` middenin het zinsdeel — `ten<sup>21</sup> zondoffer`
— dan grijpt de regex wel op de platte tekst en niet op de opmaak. De sweep
meldt niets, maar vanaf dat moment leest de leestekst iets anders dan wat de
bezoeker ziet. **De opmaak is wat de site toont, dus dat is de ernstige kant.**
Draai `scripts/synchroniseer_opmaak.py` na elke sweep.

**Inspringing en regeleindes verschillen per bestand.** De repo mengt 1- en
2-spatie-inspringing, en `wijzigingsprincipes.json` heeft CRLF waar de
databestanden LF hebben. `lees()`/`schrijf()` in `sweep_principe.py` detecteren
dat per bestand; ga daar niet omheen, anders herformatteert de diff hele
bestanden.

**Bij het toevoegen van een principe:** controleer of de uitkomst ervan niet het
bronwoord van een ander is. `scripts/audit_principes.py` doet die controle en
staat nu op nul.

### Vaste volgorde per eenheid werk

```bash
python scripts/sweep_principe.py --id V#### --sv "…" --zoek "…" --vervang "…" --droog
python scripts/sweep_principe.py --id V#### --sv "…" --zoek "…" --vervang "…"
python scripts/synchroniseer_opmaak.py
python scripts/audit_principes.py --snel
python -c "import json,glob; [json.load(open(f,encoding='utf-8')) for f in glob.glob('data/*/*.json')]"
python scripts/build_principes_data.py
```
