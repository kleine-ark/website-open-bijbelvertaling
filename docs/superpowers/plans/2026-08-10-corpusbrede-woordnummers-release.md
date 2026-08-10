# Corpusbrede woordnummers en release

> **Uitvoering:** werk elk onderdeel testgestuurd af en verifieer de volledige release voordat er naar GitHub wordt gepusht.

**Doel:** de bestaande bronwoordnummers in alle 88 boeken zichtbaar en aanklikbaar maken, met een bruikbaar woordenboekpaneel voor Hebreeuws, Grieks, Latijn en Ge’ez, en de reeds gebouwde afgesproken sitewijzigingen veilig publiceren.

**Uitgangspunt:** woordnummers blijven gekoppeld aan het grondtekstwoord uit de brondata. Er wordt geen onbewezen woord-voor-woordkoppeling met de Nederlandse vertaling verzonnen. H/G zijn Strong-nummers; OVL/OVG zijn project-eigen lexicale nummers voor Latijn en Ge’ez.

---

## 1. Datacontract en regressietests

- Inventariseer per boek en taalfamilie welke `grondtekst[].strongs`-waarden aanwezig zijn.
- Breid de tests uit voor de vier toegestane nummerfamilies: H, G, OVL en OVG.
- Leg vast dat de instelling standaard uit staat, bewaard blijft en alleen bronvaste nummers toont.

## 2. Centrale renderer

- Voeg `js/woordnummers.js` toe als gedeelde parser en HTML-renderer.
- Laat `js/app.js` deze module gebruiken voor de hoofdlezer.
- Toon het bronwoord met blauwe `<nummer>`-knoppen, correcte taalcode en tekstrichting.
- Houd nummerlabels buiten gekopieerde Bijbeltekst.

## 3. Woordenboekpaneel

- Breid `js/lexicon.js` uit zodat H/G de bestaande woordenboeken openen.
- Laat OVL/OVG hetzelfde toegankelijke onderpaneel openen met lokale lemma-, transliteratie- en betekenisgegevens en een volledige woordenboeklink.
- Verifieer toetsenbordbediening, focusherstel en mobiele afmetingen.

## 4. Globale weergave

- Laat interne citaties de globale woordnummerinstelling overnemen wanneer grondtekstdata beschikbaar is.
- Zorg dat Godsnaam-, citaat-, versnummer-, lettertype- en regelafstandkeuzes onafhankelijk blijven werken.
- Test minstens hoofdlezer, onderwerpen en een wiki-naslagpagina.

## 5. Release-afbakening

- Neem alleen de aantoonbaar afgesproken pakketten mee: citatiemodule, navigatie, gebedencatalogus, muziekinstrumentbeelden en instellingeniconen.
- Laat losse vertaalcorrecties, lege bestanden en niet-gerelateerde redactionele wijzigingen buiten de release.
- Stage gedeelde bestanden per hunk waar nodig.

## 6. Verificatie en publicatie

- Draai gerichte tests tijdens de implementatie, daarna de volledige testsuite.
- Draai `git diff --check` en inspecteer staged bestanden en diff.
- Commit logisch, push de geverifieerde branch naar GitHub en rapporteer exact wat wel en niet is gepubliceerd.
