# Opmerkingen in een Google Sheet

Meldingen van lezers gaan naar een **Google Formulier**, dat uit zichzelf naar
een gekoppelde spreadsheet schrijft. Die sheet is als CSV uit te lezen, zodat
`scripts/lees_opmerkingen.py` de opmerkingen kan ophalen en ze rechtstreeks
verwerkt kunnen worden tot tekstwijzigingen.

Eerder gingen de meldingen per mail. Dat werkte, maar gaf geen lijst: alles
stond los in het postvak, en er viel niets mee te sorteren of af te vinken.

Geen Zapier, geen extra dienst, geen sleutel in de repo.

## Hoe het in elkaar zit

```
lezer klikt "verbetering doorgeven"
        │
        └──► Google Formulier ──► gekoppelde spreadsheet ──► lees_opmerkingen.py
               (formResponse)                                 (gepubliceerde CSV)
```

Eén weg, verder niets. Er ging eerder ook een mail uit, en dat is eruit
gehaald: twee wegen naast elkaar betekent twee dingen die kunnen stukgaan en
twee plekken om na te kijken, terwijl de spreadsheet nu juist de lijst geeft
die een postvak niet gaf.

Het formulier laat niet weten of het gelukt is — Google staat geen CORS toe op
`formResponse`, dus het verzoek gaat eropuit zonder leesbaar antwoord. Wat we
er wél uit halen: ketst `fetch` af, dan is er geen verbinding. Dat is precies
de fout die de lezer zelf kan verhelpen, en daar hangt de melding aan die hij
te zien krijgt. Een fout aan Google's kant kan hij toch niet oplossen.

## Het formulier aanmaken — eenmalig, vijf minuten

1. Ga naar [forms.new](https://forms.new), of Drive → **Nieuw → Google
   Formulieren**.
2. Maak vier vragen, alle vier van het type **Kort antwoord**, in deze
   volgorde: `Vers`, `Geselecteerde tekst`, `Suggestie`, `Van`.
3. Tabblad **Antwoorden** → het groene spreadsheet-icoon → **Nieuwe
   spreadsheet maken**.
4. Rechtsboven **Verzenden** → het link-icoon 🔗 → kopieer de link.

> Gebruik niet de snelkoppeling `sheets.new` om vooraf zelf een spreadsheet te
> maken. Ben je met meerdere Google-accounts tegelijk ingelogd, dan gaat die
> naar het verkeerde account en krijg je "Kan het bestand momenteel niet
> openen". Laat het formulier de spreadsheet aanmaken; dan klopt het account
> per definitie.

### De veldnummers opzoeken

Elk antwoordveld heeft een nummer dat in `js/feedback.js` moet staan. Die zijn
uit het formulier zelf te lezen — inloggen is niet nodig, want een formulier is
openbaar:

```bash
python scripts/formulier_velden.py https://docs.google.com/forms/d/e/…/viewform
```

Zet de uitkomst in `FORMULIER` en `FORMULIER_VELDEN` in `js/feedback.js`.
Verander je later de volgorde of de naam van een vraag, dan blijven de nummers
gelijk; voeg je een vraag toe, draai het script dan opnieuw.

## De sheet leesbaar maken

De gekoppelde spreadsheet is standaard privé. Delen met "iedereen met de link"
is niet genoeg — dat geeft zicht in de browser, maar programmatisch uitlezen
levert dan een 401. Daarvoor moet hij gepubliceerd worden:

**Bestand → Delen → Publiceren op internet** → eerste blad → **Kommagescheiden
waarden (.csv)** → **Publiceren**.

Je krijgt een adres dat eindigt op `output=csv`. Zet dat in
`data/opmerkingen-bron.json`:

```json
{"csv": "https://docs.google.com/spreadsheets/d/e/…/pub?output=csv"}
```

Dat bestand staat in `.gitignore`, zodat het adres niet in de geschiedenis
belandt. Als alternatief kan het in de omgevingsvariabele
`OV_OPMERKINGEN_CSV`.

> Een gepubliceerde sheet is leesbaar voor iedereen die het adres kent. Zet er
> dus niets in dat niet openbaar mag zijn. De meldingen zelf zijn suggesties op
> een publieke Bijbeltekst; het mailadres van een inzender is dat niet, en dat
> wordt daarom niet naar het formulier gestuurd — alleen de naam die iemand
> zelf invulde. Het mailadres loopt uitsluitend via de mailweg.

## Uitlezen

```bash
python scripts/lees_opmerkingen.py                 # openstaande meldingen
python scripts/lees_opmerkingen.py --alles         # ook de afgehandelde
python scripts/lees_opmerkingen.py --boek genesis  # alleen dat boek
python scripts/lees_opmerkingen.py --json          # machineleesbaar
```

Voeg in de spreadsheet zelf een kolom **Status** toe om meldingen af te vinken;
alles wat niet leeg of `nieuw` is, valt buiten de standaardlijst.
