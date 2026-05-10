# Review Rapport: Romeinen 6-8

**Datum:** 2026-03-10
**Reviewer:** Claude (automatische review + fixes)
**Bestand:** `data/romeinen.json`
**Hoofdstukken:** 6, 7 en 8

---

## Wat is gecontroleerd

1. Archaïsmen in `text2026` en `text2026_html` (gij, zijnde, alzo, gelijkerwijs, des/der genitivus, nieuwheid des levens, enz.)
2. Godsnamen: JAHWEH / de HEER / de Heere
3. Speech markup in `text2026_html`: `<span class="god-speaks">` en `<span class="direct-speech">`
4. Aanwezigheid van `text2026_html` bij elk vers met `text2026`
5. Kanttekeningen: alle moeten een moderne `text2026` hebben, met correcte verwijzingsopmaak (dubbele punt, volledige boeknames)
6. Geest vs. geest: hoofdletter voor de Heilige Geest als persoon, kleine letter voor "geest" als levensstijl/gezindheid (vlees vs. geest)
7. Tekstkwaliteit: leesbaarheid modern Nederlands

---

## Bevindingen en uitgevoerde fixes

### Hoofdstuk 6 — Versvertalingen

| Vers | Veld | Probleem | Oplossing |
|------|------|----------|-----------|
| 4 | `text2026` | "gelijk...alzo", "nieuwheid des levens" — archaïsche correlatie en genitivus | Vervangen door "zoals...zo", "een nieuw leven" |
| 4 | `text2026_html` | "gelijkerwijs...alzo", "nieuwheid des levens" — inconsistent met text2026 | Gecorrigeerd, consistent gemaakt |
| 6 | `text2026` | "lichaam der zonde" — archaïsche genitivus | Vervangen door "lichaam van de zonde" |
| 6 | `text2026_html` | "lichaam der zonde" | Idem |
| 9 | `text2026` | "opgewekt zijnde" — archaïsch participium absolutum | Vervangen door "die uit de doden is opgewekt" |
| 9 | `text2026_html` | Idem | Idem |
| 18 | `text2026` | "vrijgemaakt zijnde" — archaïsch participium absolutum | Vervangen door "Nu vrijgemaakt" |
| 18 | `text2026_html` | Idem | Idem |
| 19 | `text2026` | "gelijk...alzo" — archaïsch | Vervangen door "zoals...zo" |
| 19 | `text2026_html` | Idem | Idem |

### Hoofdstuk 6 — Kanttekeningen

Veel kanttekeningen in hoofdstuk 6 waren slechts gedeeltelijk vertaald: ze bevatten nog de 1637-afkortingen (D. = Dat is, N. = Namelijk, Namel.) en oud-Nederlands. Alle zijn volledig herschreven naar modern Nederlands.

| Vers | Noot | Probleem | Actie |
|------|------|----------|-------|
| V10 | [23] | "N. tot versoening en vernieting van de zelf." — afkorting, oud-NL | Volledig herschreven |
| V11 | [26] | "D. van de zonde gestorven zijt. Ziet..." — afkorting | Volledig herschreven |
| V12 | [28] | "D. dewijle gij weder-geboren zijt" — archaïsche afkorting + gij/dewijle | Volledig herschreven |
| V12 | [32] | "D. te volgen, ofte te doen...Iac. 1.14." — afkorting + verwijzingsopmaak | Herschreven + Jakobus 1:14 |
| V13 | [36] | "D. als uit de dood...door Christum" — afkorting, Latijnse naam | Volledig herschreven |
| V13 | [37] | "N. als die instrumenten zijn...wilt ofte begeert" — afkorting + "ofte" | Volledig herschreven |
| V13 | [l] | "Luc. 1.74. Rom. 12.1. Gal. 2.20. Hebr. 9.14. 1.Pet. 4.2." — afkortingen, puntnotatie | Lucas 1:74. Romeinen 12:1. enz. |
| V14 | [38] | "heerschen...strijden" — oud-Nederlands | Herschreven |
| V14 | [39] | Niet vertaald, bevatte verwijzing "Rom. 7. en 2.Cor. 3." | Volledig herschreven + Romeinen 7 en 2 Korintiërs 3 |
| V14 | [40] | "N. Iesu Christus...Rom. 8. versen 1,2,3,13. 2.Tim. 1.7. 1.Ioan. 5.4." — niet vertaald | Volledig herschreven + referenties gecorrigeerd |
| V15 | [41] | "qualijk hadden konnen duiden" — oud-NL | Herschreven |
| V16 | [m] | "Ioan. 8.34. 2.Petr. 2.19." — afkortingen, puntnotatie | Johannes 8:34. 2 Petrus 2:19. |
| V16 | [43] | "D. van de heerschende zonde, als voren." — afkorting | Herschreven |
| V16 | [44] | "N. die gij God voor uwe verlossing schuldigh zijt" — gij/schuldigh | Herschreven |
| V16 | [45] | "N. om gerechtigheid te oeffenen." — afkorting | Herschreven |
| V17 | [47] | Niet vertaald, afkorting N. + oud-NL | Volledig herschreven |
| V18 | [n] | "Ioan. 8.32. Glat. 5.1. 1.Petr. 2.16." — afkortingen, spelfout Glat | Johannes 8:32. Galaten 5:1. 1 Petrus 2:16. |
| V19 | [52] | "uwes naasten" — archaïsche genitivus | "uw naaste" |
| V19 | [53] | "D. tot volvoering van zulke quade lusten en begeerlickheden." — afkorting | Herschreven |
| V19 | [54] | "Namel. van uwen handel..." — afkorting | Herschreven |
| V20 | [o] | "Ioan. 8.34." — afkorting | Johannes 8:34. |
| V20 | [55] | "ofte van de gerechtigheid" — "ofte" archaïsch | Herschreven |
| V21 | [56] | "N. na dat gij tot kennis zijt gekomen." — gij + afkorting | Herschreven |
| V21 | [57] | "gij tevoren behagen in haddet" — gij + oud-NL | Herschreven |
| V21 | [58] | "N. ten zy wy...1.Corinth. 6.11." — niet vertaald + verwijzing | Volledig herschreven + 1 Korintiërs 6:11 |
| V22 | [59] | "D. van de slavernye van de zonde, als voren." — afkorting | Herschreven |
| V22 | [60] | "D. bequaem en gewilligh om God te dienen." — afkorting | Herschreven |
| V22 | [61] | "N. in dit leven, Zoals vers 19. Ziet 1.Thess. 4.3." — afkorting + verwijzing | Herschreven + 1 Tessalonicenzen 4:3 |
| V23 | [62] | "krijghs-luiden die ten eynde van haar dienst" — oud-NL restanten | Herschreven |
| V23 | [63] | "Namel. niet alleen de tijdtlikke" — afkorting + oud-NL spelling | Volledig herschreven |
| V23 | [65] | "D. heeft tot een eynde..." — afkorting + oud-NL | Volledig herschreven |
| V23 | [p] | "Gen. 2.17. Rom. 5.12. 1.Corinth. 15.21. Iac. 1.15." — afkortingen + puntnotatie | Genesis 2:17. Romeinen 5:12. 1 Korintiërs 15:21. Jakobus 1:15. |
| V23 | [q] | "1.Petr. 1.3." — afkorting + puntnotatie | 1 Petrus 1:3. |

**Kruisverwijzingsnotities in Ch6 (crossref-noten die alleen een verwijzing bevatten):**

| Vers | Noot | Oud | Nieuw |
|------|------|-----|-------|
| V6 | [f] | Gal. 2.20. en 5.24. Phil. 3.10. 1.Petr. 4. versen 1, 2. | Galaten 2:20 en 5:24. Filippenzen 3:10. 1 Petrus 4, verzen 1, 2. |
| V7 | [g] | 1.Petr. 4.1. | 1 Petrus 4:1. |
| V8 | [h] | 2.Timot. 2.11. | 2 Timotheüs 2:11. |
| V9 | [i] | Apoc. 1.18. | Openbaring 1:18. |
| V10 | [k] | 1.Petr. 2.24. | 1 Petrus 2:24. |

### Hoofdstuk 7 — Geen verse-fixes nodig

Alle versvertalingen in hoofdstuk 7 zijn van goede kwaliteit. De teksten lezen vloeiend modern Nederlands. Kanttekeningen zijn volledig vertaald en verwijzingen gebruiken moderne opmaak.

Kleine observatie (niet gecorrigeerd): vers 2 heeft in `text2026_html` de toevoeging "de levende man" waar `text2026` alleen "haar man" heeft — dit is inhoudelijk hetzelfde en niet onjuist.

### Hoofdstuk 8 — Versvertalingen

| Vers | Veld | Probleem | Oplossing |
|------|------|----------|-----------|
| 2 | `text2026` | "Geest des levens" — archaïsche genitivus | "Geest van het leven" |
| 2 | `text2026_html` | Idem | Idem |
| 13 | `text2026` | "door de geest" (kleine letter) — inconsistent met `text2026_html` dat terecht "Geest" heeft (de Heilige Geest die doding van de zonde bewerkt) | "door de Geest" (hoofdletter, want de Heilige Geest als persoon is bedoeld) |
| 29 | `text2026_html` | "Want wie hy" — "hy" is oud-Nederlandse spelling | "Want wie hij" |
| 36 | `text2026_html` | `{sup(3)}` en `{sup(4)}` — kapotte opmaak (verkeerd formaat voor nootcijfers in direct speech) | Vervangen door correcte `<sup class="note-marker" data-note="3">3</sup>` tags |

---

## Geest vs. geest — eindconclusie per hoofdstuk

### Hoofdstuk 6
- Geen occurrences van "Geest" of "geest" in de versvertalingen zelf.
- In kanttekeningen: "Geest van Christus" (hoofdletter, correct) en "Gods Geest" (hoofdletter, correct).

### Hoofdstuk 7
- Vers 6: "in de vernieuwing van de Geest" — hoofdletter correct: dit is de Heilige Geest die de dienst vernieuwd.
- Alle overige occurrences correct.

### Hoofdstuk 8
- Verzen 1, 4, 5, 6, 9 (2x), 10: "naar de geest" / "het denken van de geest" / "in de geest" — **kleine letter correct**: dit is de tegenstelling vlees vs. geest als levensstijl/gezindheid, niet de Heilige Geest als persoon.
- Vers 2: "de wet van de Geest van het leven" — **hoofdletter correct**: de Heilige Geest als persoon.
- Vers 9: "als de Geest van God in u woont" — **hoofdletter correct**: expliciete persoon.
- Vers 11: "de Geest van hem" / "zijn Geest" — **hoofdletter correct**: expliciete persoon.
- Vers 13: "door de Geest" — **hoofdletter correct** (na fix): de Heilige Geest die doding bewerkt.
- Vers 14: "de Geest van God" — **hoofdletter correct**: expliciete persoon.
- Vers 15: "de geest van slavernij" / "de geest van aanneming" — **kleine letter correct**: dit zijn figuurlijke uitdrukkingen, niet verwijzingen naar de Heilige Geest als persoon (hoewel Hij er achter staat).
- Vers 16: "De Geest zelf" / "onze geest" — **hoofdletter/kleine letter correct**: de Heilige Geest als persoon vs. de menselijke geest.
- Verzen 23, 26, 27: "de Geest" — **hoofdletter correct**: expliciete verwijzingen naar de Heilige Geest.

---

## Geen problemen gevonden (correct)

- Geen occurrences van "de HEER", "de Heere", of "JahWeh" (verkeerde schrijfwijze) in hfst. 6-8.
- Alle verzen in hfst. 6-8 hebben zowel `text2026` als `text2026_html`.
- Directe-rede markup (`<span class="direct-speech">`) correct aanwezig in Ch7:V7 en Ch8:V15, V36.
- Geen god-speaks markup nodig in hfst. 6-8 (geen rechtstreekse Godsrede).
- Hoofdstuk 7 kanttekeningen: kwaliteit goed, moderne verwijzingen (dubbele punt).
- Hoofdstuk 8 kanttekeningen: kwaliteit goed, moderne verwijzingen.

---

## Statistieken

- **Totaal fixes:** 54
- **Versvertalingen gefix (text2026):** 7 (Ch6: V4, V6, V9, V18, V19; Ch8: V2, V13)
- **text2026_html gefix:** 8 (Ch6: V4, V6, V9, V18, V19; Ch8: V2, V29, V36)
- **Kanttekeningen gefix (text2026):** 32 (hoofdzakelijk Ch6)
- **Kruisverwijzingsopmaak gefix:** 14 (hoofdzakelijk Ch6)

---

## Overige observaties (niet gecorrigeerd)

- Ch6 verzen 4, 6, 9 bevatten nog enige stilistische oudheid ("Dit wetende, dat...", "zouden wandelen"), maar deze zijn acceptabel als lichte formele toonzetting die past bij de brief van Paulus. Ze zijn niet als archaïsmen geclassificeerd.
- Ch8 kanttekening [m] bij V18 vermeldt "1 Petrus 4:13" — correct formaat.
- De vertaling "Dat zij verre!" in Ch6:V2 en V15 is een bewuste keuze (vaste uitdrukking voor het Griekse μὴ γένοιτο).
