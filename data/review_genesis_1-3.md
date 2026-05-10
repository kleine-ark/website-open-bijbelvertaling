# Review Genesis 1-3 — 10 maart 2026

## Samenvatting
10 fixes toegepast, verder alles conform richtlijnen.

## Fixes

### 1. Hoofdletter "Uw/U" bij aanspreking God (H3)
Modern Nederlands: geen hoofdletter bij "u/uw" wanneer mensen God aanspreken.
- **3:10** text2026 + html: "Ik hoorde Uw stem" → "Ik hoorde uw stem"
- **3:12** text2026 + html: "De vrouw die U mij gegeven hebt" → "De vrouw die u mij gegeven hebt"

### 2. Archaïsme "om uwentwil" (H3)
- **3:17** text2026 + html: "om uwentwil vervloekt" → "omwille van u vervloekt"

### 3. Kapotte HTML — extra `</span>` tags (4 verzen)
Ongebalanceerde span-markup die rendering zou breken:
- **2:23** text2026_html: extra `</span>` verwijderd
- **3:13** text2026_html: extra `</span>` verwijderd
- **3:16** text2026_html: extra `</span>` verwijderd
- **3:22** text2026_html: extra `</span>` verwijderd

## Geen problemen gevonden
- Godsnamen: correct (JAHWEH, God JAHWEH volgorde)
- Geen "uitspansel", "wemelen", "grond" — al eerder gecorrigeerd
- Geen archaïsmen in verzen of kanttekeningen
- Alle text2026_html aanwezig met nootcijfers
- god-speaks en direct-speech spans correct
- Alle kanttekeningen hertaald met moderne verwijzingen
- Geest/geest correct (H1:2 = Heilige Geest → hoofdletter)
