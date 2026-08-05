# Opmerkingen in een Google Sheet

Meldingen van lezers komen nu per mail binnen via FormSubmit. Dat werkt, maar
je hebt geen lijst: alles staat los in je postvak, en er valt niets mee te
sorteren of af te vinken.

Met een Google Apps Script schrijven we elke melding weg in een spreadsheet
**en** krijg je nog steeds een mail. Bijkomend voordeel: die sheet is als CSV
uit te lezen, zodat `scripts/lees_opmerkingen.py` de opmerkingen kan ophalen
en ik ze rechtstreeks kan verwerken tot tekstwijzigingen.

Geen Zapier, geen extra dienst, geen sleutel in de repo.

## Eenmalig instellen — ongeveer tien minuten

### 1. Maak de spreadsheet

Ga naar [sheets.new](https://sheets.new) en noem hem bijvoorbeeld
**Opmerkingen Open Vertaling**. Verder niets invullen; het script maakt de
kolomkoppen zelf.

### 2. Plak het script erin

In diezelfde spreadsheet: **Extensies → Apps Script**. Verwijder wat er staat
en plak dit:

```javascript
// Ontvangt meldingen van openvertaling.nl, schrijft ze in de spreadsheet
// en stuurt een mail. Retourneert JSON, zodat de site kan zien of het lukte.

var MAIL_NAAR = 'maartenvroegindeweij@gmail.com';

function doPost(e) {
  try {
    var d = JSON.parse(e.postData.contents);
    var blad = SpreadsheetApp.getActiveSpreadsheet().getSheets()[0];

    // Kolomkoppen aanmaken bij de eerste melding
    if (blad.getLastRow() === 0) {
      blad.appendRow(['Ontvangen', 'Vers', 'Geselecteerde tekst', 'Suggestie',
                      'Van', 'Status', 'Browser']);
      blad.setFrozenRows(1);
    }

    blad.appendRow([
      new Date(),
      d.ref || '',
      d.selected || '',
      d.suggestion || '',
      d.van || 'anoniem',
      'nieuw',
      d.userAgent || ''
    ]);

    MailApp.sendEmail({
      to: MAIL_NAAR,
      subject: 'Opmerking bij ' + (d.ref || 'de vertaling'),
      body: 'Vers: ' + (d.ref || '-') +
            '\n\nGeselecteerde tekst:\n' + (d.selected || '(geen)') +
            '\n\nSuggestie:\n' + (d.suggestion || '') +
            '\n\nVan: ' + (d.van || 'anoniem')
    });

    return uit({ ok: true });
  } catch (err) {
    return uit({ ok: false, fout: String(err) });
  }
}

function uit(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj))
                       .setMimeType(ContentService.MimeType.JSON);
}
```

### 3. Publiceer het als web-app

**Implementeren → Nieuwe implementatie → Type: Web-app.**

Twee instellingen zijn cruciaal:

| | |
|---|---|
| Uitvoeren als | **Ikzelf** |
| Wie heeft toegang | **Iedereen** |

Zonder die tweede kan de site niets versturen. Google vraagt eenmalig
toestemming; je krijgt een waarschuwing dat het script niet geverifieerd is —
dat klopt, het is je eigen script. Kies *Geavanceerd* en ga door.

Je krijgt een adres van de vorm
`https://script.google.com/macros/s/AKfy…/exec`. **Dat adres heb ik nodig.**

### 4. Zet de sheet open voor uitlezen

Om de opmerkingen automatisch te kunnen inlezen: in de spreadsheet
**Bestand → Delen → Publiceren op internet**, kies het eerste blad en
**Kommagescheiden waarden (.csv)**, en publiceer.

Je krijgt een tweede adres, eindigend op `output=csv`. **Dat heb ik ook
nodig.**

> Let op: een gepubliceerde sheet is voor iedereen leesbaar die het adres
> kent. Zet er dus geen gegevens in die niet openbaar mogen zijn. De
> meldingen zelf zijn suggesties op een publieke Bijbeltekst, maar het
> mailadres van een inzender is dat niet — daarom slaat het script alleen op
> wat de inzender zelf invulde, en niet zijn adres.

## Daarna

Geef me beide adressen door. Ik zet het eerste in `js/feedback.js` en het
tweede in `scripts/lees_opmerkingen.py`, en dan kan ik met één opdracht alle
openstaande opmerkingen ophalen en verwerken.
