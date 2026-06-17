# Open Staten Vertaling (OSV)

Een vrij beschikbare **herziening van de Statenvertaling** (1637/1888) — leesbaar
hedendaags Nederlands, maar zo dicht mogelijk bij de oorspronkelijke Statenvertaling.

🌐 **[openvertaling.nl](https://openvertaling.nl)**

---

## Wat is de Open Staten Vertaling?

De Open Staten Vertaling is een herziening van de Statenvertaling uit 1637 (op basis
van de uitgave van 1888). Het doel: een vertaling die **zoveel mogelijk gelijk blijft
aan de oorspronkelijke Statenvertaling**, maar leesbaar is voor nieuwe gelovigen,
doordat onbekende 17e‑eeuwse woorden en zinsconstructies vervangen zijn.

Het is een eerlijke poging — een lastig project met veel afwegingen. We weten niet
zeker of het uiteindelijk volledig zal slagen, maar elke wijziging is traceerbaar en
omkeerbaar.

## Waarom heet het ‘Open’?

1. **Public domain.** De tekst is vrij van rechten (CC0) — vrij te gebruiken voor
   prediking, studie, apps of welk doel dan ook.
2. **Open keuzes.** Voor herzieningskeuzes waarover discussie mogelijk is, zijn er
   instelbare opties (bijvoorbeeld de weergave van de Godsnaam: JAHWEH / de HEERE /
   Jehovah / יהוה).
3. **Open einde.** Een project dat vermoedelijk nooit helemaal ‘af’ is, maar
   onderhevig blijft aan nieuwe inzichten — altijd gebaseerd op de Statenvertaling.

## Aanleiding

De directe aanleiding was de wens om een evangelisatietraktaat te drukken met
bijbelgedeelten in hedendaags Nederlands. Op bestaande herzieningen (zoals de HSV)
rust auteursrecht, waardoor vrij drukken en verspreiden niet mogelijk is. Daarom een
eigen, **rechtenvrije** herziening, rechtstreeks vanuit de Statenvertaling.

## Hoe het werkt: genummerde principes

Elke wijziging ten opzichte van de SV1888 wordt geregeld door een **genummerd
principe** (V1, V2, …). Zo blijft elke verandering traceerbaar en omkeerbaar. De
oorspronkelijke tekst (1637 en 1888) blijft naast de herziening bewaard.

## Stand van zaken

| | |
|---|---|
| Boeken | 82 (incl. apocriefen), waarvan **21 volledig nagelezen** |
| Hoofdstukken | 1.370, waarvan **356 vers‑voor‑vers gecontroleerd** |
| Verzen | 37.235 |
| Principes | 846 |
| Tekstwijzigingen t.o.v. SV1888 | ± 82.000 |

*(Actuele cijfers staan in [`data/stats.json`](data/stats.json) — de enige bron voor
alle aantallen op de site.)*

## Functies van de website

- **Parallelle weergave** van OSV naast SV1637, SV1888, grondtekst (Hebreeuws/Grieks
  met Strong's) en de kanttekeningen.
- **Citaatopmaak**: rood = God/Christus, blauw = engel, geel = de duivel, « » =
  directe rede; met een aparte indeling *de Vader / de Zoon / de Geest spreekt*.
- **Doorlopend lezen** (oneindig scrollen door alle hoofdstukken), **voorlezing**
  (TTS, man/vrouw‑stem), **pericoop‑kopjes**, boek‑ en hoofdstukinleidingen.
- **Onderwerpen**: bijbelteksten geordend op thema.
- **Citaat insluiten** op je eigen site via de meegeleverde
  [`embed.js`](embed.js) — één bron, geen kopie. Zie [`/insluiten.html`](insluiten.html).
- Instellingen: Godsnaam, versnummers, dyslexie‑modus, donker/licht thema, e.a.
- Werkt **offline** (service worker / PWA).

## Repository‑structuur

```
data/{boek}.json          boek‑metadata + boekinleiding
data/{boek}/{hoofdstuk}.json   verzen (SV1637, SV1888, OSV, grondtekst, kanttekeningen)
data/stats.json           enige bron voor alle aantallen
data/wijzigingsprincipes.json  de genummerde principes
data/tags.json, spreker-tags.json, pericopen.json   onderwerpen & indelingen
js/                       frontend (vanilla JS, geen build-stap)
css/style.css             styling
embed.js                  herbruikbare citaat-bibliotheek
sw.js                     service worker (offline cache)
scripts/                  o.a. build_stats.py
```

De site is **statisch** (HTML/CSS/vanilla JS) — geen build nodig; serveer de map met
een willekeurige statische server.

## Bijdragen

Correcties, suggesties en bijdragen zijn welkom — via een fout-melding op de site,
een GitHub‑issue of een pull request. Feedback op vertaalkeuzes is bijzonder waardevol.

## Licentie

De **bijbeltekst** (SV1637/1888 en de OSV‑herziening) is **publiek domein (CC0)** —
vrij te gebruiken, kopiëren, drukken en verspreiden voor elk doel. Voor de broncode:
zie de repository.

> *„Want het Woord van God is levend en krachtig.”* — Hebreeën 4:12
