---
name: geez-vertalen
description: Gebruik wanneer een boek of hoofdstuk uit het Ge'ez (klassiek Ethiopisch) naar het Nederlands vertaald moet worden voor de Open Staten Vertaling — bijv. Henoch, Jubileeën of andere Ethiopische boeken uit de map ethiopische-boeken/.
---

# Ge'ez vertalen naar OSV-Nederlands

## Overzicht

Vertaal rechtstreeks uit de Ge'ez-grondtekst. Waar een publiek-domein
wetenschappelijke vertaling bestaat (Henoch, Jubileeën) is die een verplichte
controle achteraf; voor Meqabyan bestaat die niet en werk je uit het Ge'ez alleen.
Kernprincipe: **het Ge'ez is de bron; de Engelse vertaling is de vangrail, nooit de bron.**

## Bronnen per boek (vaste paden vanaf repo-root)

| Boek | Ge'ez-grondtekst (vertaalbasis) | Controlevertaling |
|---|---|---|
| 1 Henoch (108 hfst.) | `ethiopische-boeken/geez-grondtekst/henoch-geez-digitaal.txt` | Charles 1917: `ethiopische-boeken/1-henoch/henoch-charles-1917-engels.txt` |
| Jubileeën (50 hfst.) | `ethiopische-boeken/jubileeen/jubileeen-geez-digitaal.txt` | Charles 1902: `ethiopische-boeken/jubileeen/jubileeen-charles-1902-engels.txt` |
| 1 Meqabyan (36 hfst.) | `ethiopische-boeken/meqabyan/1meqabyan-geez-digitaal.txt` | **geen** — alleen Ge'ez |
| 2 Meqabyan (21 hfst.) | `ethiopische-boeken/meqabyan/2meqabyan-geez-digitaal.txt` | **geen** — alleen Ge'ez |
| 3 Meqabyan (10 hfst.) | `ethiopische-boeken/meqabyan/3meqabyan-geez-digitaal.txt` | **geen** — alleen Ge'ez |

De TEI-XML-bronbestanden (met kritisch apparaat / tweede editie) staan naast de
digitale teksten in `geez-grondtekst/`. Vaste termen: `woordenlijst.md` naast deze SKILL.md.

## Werkwijze per hoofdstuk

1. Lees het Ge'ez-hoofdstuk uit het grondtekstbestand. Vertaal éérst zelf,
   zin voor zin (። scheidt zinnen, ፡ scheidt woorden). Raadpleeg de
   controlevertaling pas als je eigen vertaling er staat.
2. **Als er een controlevertaling is** (Henoch, Jubileeën): vergelijk ermee.
   Bij verschil beslis je op grond van het Ge'ez; noteer een wezenlijk
   verschil als voetnoot. **Bij Meqabyan** is er geen controle: vertaal
   nauwgezet uit het Ge'ez en markeer élke onzekere passage met een voetnoot.
3. Versindeling:
   - Jubileeën en Meqabyan: de Ge'ez-grondtekst heeft al versnummers
     (`hoofdstuk:vers`) — neem die exact over.
   - Henoch: neem de versnummers van Charles 1917 over. Waar Charles de
     Ethiopische volgorde omzet (vooral in de Gelijkenissen, hfst. 37–71):
     volg de Ethiopische volgorde en meld het in een voetnoot.
4. Sla voor elke terugkerende term de woordenlijst na en gebruik de vaste
   weergave. Nieuwe terugkerende term of eigennaam? Voeg die toe aan de
   woordenlijst, mét Ge'ez-vorm.
5. Onzekere of corrupte Ge'ez-lezing? Vertaal de best verdedigbare lezing
   en zet een voetnoot. Nooit stilzwijgend uit de controlevertaling overnemen,
   nooit een elliptische zin gladstrijken.

## OSV-stijl (2026-laag)

- Aanspreekvorm "u", nooit "gij"; geen oude naamvallen (den/der/des/dien/denzelven).
  Uitzondering: vaste genitiefverbindingen uit de woordenlijst ("de Heere der
  geesten", "het Hoofd der dagen") behouden "der".
- Eerbiedshoofdletters voor God: Hij, Zijn, Hem. Voor de Mensenzoon: "de
  Mensenzoon" met hoofdletter, maar zijn voornaamwoorden met kleine letter
  (eindredactie kan dit later verhogen).
- Godsnamen: እግዚአብሔር en አምላክ = "God"; እግዚእ = "de Heere";
  እግዚአ ፡ መናፍስት (Gelijkenissen) = "de Heere der geesten" (vaste term).
- Register: Statenvertaling-achtig en formeel-equivalent — "inzettingen",
  "voleinding", "geslachten", "zie," — maar in moderne spelling en zinsbouw
  die de wijzigingsprincipes van de OSV volgt (data/wijzigingsprincipes.json).
- Ethiopische cijfers (፩ ፪ ፲ …) als voluit geschreven woorden.

## Uitvoerformaat

Schrijf per hoofdstuk één bestand `ethiopische-boeken/vertaling/<boek>/<hoofdstuk>.md`:

```markdown
# Henoch 46

1 En daar zag ik Een die een Hoofd der dagen had, …
2 En ik vroeg een van de engelen, …

## Voetnoten
- vers 2: Ge'ez ወርኢኩ "en ik zag" (1e persoon); met Charles als imperatief gelezen.

## Nieuwe termen
- ርእሰ ፡ መዋዕል — het Hoofd der dagen (toegevoegd aan woordenlijst)
```

Geen voetnoten of nieuwe termen? Laat die kop dan weg. Opname in
`data/*.json` is een aparte redactiestap en hoort niet bij deze skill.

## Valkuilen

| Fout | Correctie |
|---|---|
| Controlevertaling uit het geheugen naschrijven | Eerst zelf uit het Ge'ez vertalen; controle daarna |
| Elliptisch of moeilijk Ge'ez gladstrijken | Letterlijk vertalen; onduidelijkheid in een voetnoot |
| Bij Meqabyan een Engelse "vangnet"-vertaling verzinnen | Die bestaat niet; werk uit het Ge'ez en markeer twijfel |
| Zelfde term per hoofdstuk anders vertalen | Woordenlijst naslaan én bijwerken |
| "Heere" gebruiken voor እግዚአብሔር of አምላክ | Die zijn "God"; alleen እግዚእ is "de Heere" |
| Verzen hernummeren naar eigen inzicht | Grondtekst-/Charles-nummering volgen; afwijking → voetnoot |
| Vertaling direct in data/*.json zetten | Alleen het .md-staging-bestand schrijven |
