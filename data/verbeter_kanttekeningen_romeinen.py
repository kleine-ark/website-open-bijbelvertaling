#!/usr/bin/env python3
"""
Verbeter mechanisch hertaalde kanttekeningen in romeinen.json.
Alleen noten bij verzen met status='' worden aangepast (de 713 mechanisch hertaalde).
"""

import json
import re
import copy
import sys

INPUT  = "romeinen.json"
OUTPUT = "romeinen.json"

with open(INPUT, "r", encoding="utf-8") as f:
    data = json.load(f)

# Keep original for comparison
original = copy.deepcopy(data)

changed_count = 0
changed_notes = []  # (chapter, verse, marker, old, new)

def improve(text: str) -> str:
    """Pas hertaalregels toe op een kanttekeningtekst."""
    t = text

    # ── Boekafkortingen moderniseren ──
    # Punt naar dubbele punt in bijbelverwijzingen (bv. Gen. 3:5 -> Gen. 3:5 already ok)
    # Afkortingen updaten
    abbrevs = {
        "Hand.": "Hand.",       # already ok
        "Matth.": "Matt.",
        "Luk.": "Luk.",         # already ok
        "Joh.": "Joh.",         # already ok
        "Kor.": "Kor.",         # already ok - but 2 Kor -> 2 Kor. is fine
        "Galat.": "Gal.",
        "Efez.": "Ef.",
        "Filip.": "Fil.",
        "Koloss.": "Kol.",
        "Thessal.": "Thess.",
        "Filipp.": "Fil.",
        "Filippensen": "Filippenzen",
        "Hebr.": "Hebr.",       # ok
        "Openb.": "Openb.",     # ok
        "Deut.": "Deut.",       # ok
        "Richt.": "Richt.",     # ok
        "Pred.": "Pred.",       # ok
    }
    for old, new in abbrevs.items():
        if old != new:
            t = t.replace(old, new)

    # ── HEERE -> JAHWEH (already mostly done, but check) ──
    # (HEERE should have been done in mechanical step)

    # ── Heere -> Heer ──
    t = t.replace("de Heere", "de Heer")
    t = t.replace("den Heere", "de Heer")
    t = t.replace("des Heeren", "van de Heer")
    t = t.replace("de Heeren", "de Heer")
    t = t.replace("Heere", "Heer")  # catch remaining

    # ── Naamvallen ──

    # "des" + woord -> "van de/het" + woord
    # Common patterns: des Heeren, des geloofs, des verbonds, des Geestes, etc.
    # des + het-woord -> van het; des + de-woord -> van de
    het_woorden = {
        "geloofs": "geloof", "verbonds": "verbond", "lichaams": "lichaam",
        "kruises": "kruis", "Evangelies": "Evangelie", "vlees": "vlees",
        "vlezes": "vlees", "gebods": "gebod", "gericht": "gericht",
        "gerichts": "gericht", "doods": "dood", "levens": "leven",
        "licht": "licht", "lichts": "licht", "heil": "heil",
        "heils": "heil", "verstand": "verstand", "verstands": "verstand",
        "geslacht": "geslacht", "geslachts": "geslacht",
        "hart": "hart", "harts": "hart", "hoofd": "hoofd",
        "hoofds": "hoofd", "woord": "woord", "woords": "woord",
        "Koninkrijk": "Koninkrijk", "Koninkrijks": "Koninkrijk",
        "volk": "volk", "volks": "volk",
    }

    # "des Heiligen Geestes" -> "van de Heilige Geest"
    t = re.sub(r'\bdes Heiligen Geestes\b', 'van de Heilige Geest', t)
    t = re.sub(r'\bdes Nieuwen Testaments\b', 'van het Nieuwe Testament', t)
    t = re.sub(r'\bdes Ouden Testaments\b', 'van het Oude Testament', t)

    # General "des" patterns
    def replace_des(m):
        word = m.group(1)
        if word in het_woorden:
            return f"van het {het_woorden[word]}"
        # Default to "van de" for most
        # Remove trailing 's' if it's a genitive
        base = re.sub(r's$', '', word) if word.endswith('s') and not word.endswith('ss') else word
        return f"van de {base}"

    t = re.sub(r'\bdes (\w+)\b', replace_des, t)

    # "der" + woord -> "van de" + woord
    # But careful: "der" can also be "van de" already in text
    t = re.sub(r'\bder (\w+)\b', r'van de \1', t)

    # "den" as article before noun (not "den" in verbs like "verbrandden", "zouden")
    # Patterns: "den stam", "den dag", "den naam", "den dood", "den geest", etc.
    # This is tricky - "den" before a noun (capitalized or specific words)
    den_replacements = {
        "den stam": "de stam",
        "den dag": "de dag",
        "den naam": "de naam",
        "den dood": "de dood",
        "den geest": "de geest",
        "den Geest": "de Geest",
        "den mens": "de mens",
        "den persoon": "de persoon",
        "den apostel": "de apostel",
        "den Apostel": "de Apostel",
        "den brief": "de brief",
        "den zondaar": "de zondaar",
        "den dienst": "de dienst",
        "den tempel": "de tempel",
        "den staat": "de staat",
        "den tijd": "de tijd",
        "den weg": "de weg",
        "den wil": "de wil",
        "den koning": "de koning",
        "den Koning": "de Koning",
        "den rechter": "de rechter",
        "den profeet": "de profeet",
        "den Profeet": "de Profeet",
        "den priester": "de priester",
        "den goddeloze": "de goddeloze",
        "den arme": "de arme",
        "den rijke": "de rijke",
        "den naaste": "de naaste",
        "den broeder": "de broeder",
        "den vader": "de vader",
        "den Vader": "de Vader",
        "den Zoon": "de Zoon",
        "den zoon": "de zoon",
        "den man": "de man",
        "den heer": "de heer",
        "den Heer": "de Heer",
        "den Here": "de Heer",
        "den doop": "de doop",
        "den vrede": "de vrede",
        "den vloek": "de vloek",
        "den zegen": "de zegen",
        "den hemel": "de hemel",
        "den toorn": "de toorn",
        "den nood": "de nood",
        "den loop": "de loop",
        "den grond": "de grond",
        "den band": "de band",
        "den raad": "de raad",
        "den regel": "de regel",
        "den plicht": "de plicht",
        "den last": "de last",
        "den strijd": "de strijd",
        "den godsdienst": "de godsdienst",
        "den dood": "de dood",
        "den spot": "de spot",
        "den afval": "de afval",
    }
    for old, new in den_replacements.items():
        t = t.replace(old, new)

    # "den" before proper nouns/names (common in text)
    t = re.sub(r'\bden (Joden|Romeinen|Galaten|Korintiërs|Grieken|Hebreën|heidenen)\b', r'de \1', t)

    # Remaining "den" before capitalized words (likely nouns)
    # Be careful not to change "den" that's part of a word
    def replace_den_cap(m):
        word = m.group(1)
        # Skip if it's likely a place name ending in -den
        return f"de {word}"
    t = re.sub(r'\bden ([A-Z]\w+)\b', replace_den_cap, t)

    # ── Bezittelijke voornaamwoorden ──
    t = re.sub(r'\bzijne\b', 'zijn', t)
    t = re.sub(r'\bZijne\b', 'Zijn', t)
    t = re.sub(r'\bzijnen\b', 'zijn', t)
    t = re.sub(r'\bZijnen\b', 'Zijn', t)
    t = re.sub(r'\bzijner\b', 'zijn', t)
    t = re.sub(r'\bZijner\b', 'Zijn', t)
    t = re.sub(r'\bhunne\b', 'hun', t)
    t = re.sub(r'\bHunne\b', 'Hun', t)
    t = re.sub(r'\bhunnen\b', 'hun', t)

    # ── Aanwijzende voornaamwoorden ──
    t = re.sub(r'\bhetwelk\b', 'dat', t)
    t = re.sub(r'\bHetwelk\b', 'Dat', t)
    t = re.sub(r'\bdezen\b', 'deze', t)
    t = re.sub(r'\bDezen\b', 'Deze', t)
    t = re.sub(r'\bdien\b', 'die', t)
    t = re.sub(r'\bDien\b', 'Die', t)
    t = re.sub(r'\bwelken\b', 'welke', t)
    t = re.sub(r'\bWelken\b', 'Welke', t)
    t = re.sub(r'\bwelker\b', 'welke', t)
    t = re.sub(r'\bWelker\b', 'Welke', t)

    # dezelve, hetzelve, denzelven, deszelfs
    t = re.sub(r'\bdezelve\b', 'deze', t)
    t = re.sub(r'\bDezelve\b', 'Deze', t)
    t = re.sub(r'\bhetzelve\b', 'hetzelfde', t)
    t = re.sub(r'\bHetzelve\b', 'Hetzelfde', t)
    t = re.sub(r'\bdenzelven\b', 'dezelfde', t)
    t = re.sub(r'\bDenzelven\b', 'Dezelfde', t)
    t = re.sub(r'\bdeszelfs\b', 'daarvan', t)
    t = re.sub(r'\bDeszelfs\b', 'Daarvan', t)
    t = re.sub(r'\bdezelven\b', 'dezen', t)

    # ── Gij -> u/U ──
    t = re.sub(r'\bGij\b', 'U', t)
    t = re.sub(r'\bgij\b', 'u', t)

    # ── zeide -> zei ──
    t = re.sub(r'\bzeide\b', 'zei', t)
    t = re.sub(r'\bZeide\b', 'Zei', t)

    # ── D. -> "Dat wil zeggen:" ──
    # Be careful: only when "D." stands alone as abbreviation, not in names
    t = re.sub(r'(?<!\w)D\.\s', 'Dat wil zeggen: ', t)

    # ── T.w. -> "Namelijk" ──
    t = re.sub(r'\bT\.w\.\b', 'Namelijk', t)

    # ── Punt -> dubbele punt in bijbelverwijzingen ──
    # Pattern: Book chapter.verse -> Book chapter:verse  (already mostly done)
    # Fix remaining: e.g., "Gen. 3.5" -> "Gen. 3:5"
    t = re.sub(r'(\b\d+)\.(\d+\b)', r'\1:\2', t)

    # ── Fix broken genitive patterns from mechanical translation ──
    # "van de verbonds" -> "van het verbond"  (des verbonds -> van de verbonds was wrong)
    t = re.sub(r'van de verbonds\b', 'van het verbond', t)
    t = re.sub(r'van de geloofs\b', 'van het geloof', t)
    t = re.sub(r'van de lichaams\b', 'van het lichaam', t)
    t = re.sub(r'van de levens\b', 'van het leven', t)
    t = re.sub(r'van de doods\b', 'van de dood', t)
    t = re.sub(r'van de kruises\b', 'van het kruis', t)
    t = re.sub(r'van de volks\b', 'van het volk', t)
    t = re.sub(r'voor de Zijn\b', 'voor de Zijnen', t)  # fix "voor de Zijn erkend"

    # ── "welke" where "die" is more natural (relative pronoun for de-words) ──
    # Keep "welke" in most cases as it's acceptable formal Dutch

    # ── Clean up double spaces ──
    t = re.sub(r'  +', ' ', t)

    return t


# Process all mechanically translated notes
for ch in data["chapters"]:
    for v in ch["verses"]:
        if v.get("status", "") != "":
            continue  # skip already-done verses
        for n in v.get("marginNotes", []):
            old_text = n.get("text2026", "")
            if not old_text:
                continue
            new_text = improve(old_text)
            if new_text != old_text:
                changed_count += 1
                changed_notes.append((
                    ch["number"], v["number"], n["marker"],
                    old_text, new_text
                ))
                n["text2026"] = new_text

# Write output
with open(OUTPUT, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

# Report
print(f"Totaal mechanisch hertaalde noten: 713")
print(f"Noten aangepast: {changed_count}")
print(f"Noten ongewijzigd: {713 - changed_count}")
print()

# Show 3 examples
print("=" * 70)
print("VOORBEELDEN VAN AANPASSINGEN:")
print("=" * 70)
for i, (ch, vs, marker, old, new) in enumerate(changed_notes[:3]):
    print(f"\n--- Voorbeeld {i+1}: Hoofdstuk {ch}:{vs}, noot {marker} ---")
    print(f"OUD:  {old[:300]}")
    print(f"NIEUW: {new[:300]}")

    # Show specific changes
    import difflib
    old_words = old.split()
    new_words = new.split()
    diffs = []
    sm = difflib.SequenceMatcher(None, old_words, new_words)
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == 'replace':
            diffs.append(f"  '{' '.join(old_words[i1:i2])}' -> '{' '.join(new_words[j1:j2])}'")
        elif tag == 'delete':
            diffs.append(f"  VERWIJDERD: '{' '.join(old_words[i1:i2])}'")
        elif tag == 'insert':
            diffs.append(f"  TOEGEVOEGD: '{' '.join(new_words[j1:j2])}'")
    if diffs:
        print("WIJZIGINGEN:")
        for d in diffs[:5]:
            print(d)

print()
print("=" * 70)
print("SAMENVATTING TYPEN WIJZIGINGEN:")
print("=" * 70)

# Count types of changes
counts = {
    "hunne->hun": 0, "zijne/zijnen/zijner->zijn": 0,
    "den->de": 0, "des->van de/het": 0, "der->van de": 0,
    "Heere->Heer": 0, "dezelve/hetzelve/deszelfs": 0,
    "hetwelk->dat": 0, "dezen->deze": 0, "dien->die": 0,
    "welken/welker->welke": 0,
    "boekafkortingen": 0, "overige": 0,
}
for ch, vs, marker, old, new in changed_notes:
    if "hunne" in old or "Hunne" in old: counts["hunne->hun"] += 1
    if re.search(r'\bzijne\b|\bZijne\b|\bzijnen\b|\bzijner\b', old): counts["zijne/zijnen/zijner->zijn"] += 1
    if "den " in old: counts["den->de"] += 1
    if re.search(r'\bdes \b', old): counts["des->van de/het"] += 1
    if re.search(r'\bder \b', old): counts["der->van de"] += 1
    if "Heere" in old: counts["Heere->Heer"] += 1
    if re.search(r'dezelve|hetzelve|deszelfs|denzelven', old): counts["dezelve/hetzelve/deszelfs"] += 1
    if "hetwelk" in old: counts["hetwelk->dat"] += 1
    if re.search(r'\bdezen\b', old): counts["dezen->deze"] += 1
    if re.search(r'\bdien\b', old): counts["dien->die"] += 1
    if re.search(r'\bwelken\b|\bwelker\b', old): counts["welken/welker->welke"] += 1
    if re.search(r'Matth\.|Galat\.|Efez\.|Filip\.|Koloss\.|Filippensen', old): counts["boekafkortingen"] += 1

for k, v in sorted(counts.items(), key=lambda x: -x[1]):
    if v > 0:
        print(f"  {k}: {v} noten")
