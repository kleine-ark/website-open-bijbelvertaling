#!/usr/bin/env python3
"""
Process romeinen.json to create/audit text2026 translations.
"""

import json
import re
import shutil

INPUT_FILE = '/home/maarten/3BM Dropbox/Maarten Vroegindeweij/de kleine ark/Projecten/19 Open Vertaling/data/romeinen.json'
OUTPUT_FILE = INPUT_FILE

# Make a backup
shutil.copy(INPUT_FILE, INPUT_FILE + '.bak')

with open(INPUT_FILE + '.bak', 'r', encoding='utf-8') as f:
    data = json.load(f)

stats = {'checked': 0, 'new': 0, 'fixed': 0}

# Het-words (neuter nouns that take "het" article) - include genitive forms
HET_WORDS = {
    'vlees', 'vleses', 'geloof', 'geloofs', 'leven', 'levens',
    'lichaam', 'lichaams', 'hart', 'harts',
    'kruis', 'bloed', 'bloeds', 'licht', 'lichts',
    'woord', 'woords', 'werk', 'werks', 'recht', 'rechts',
    'leem', 'verderf', 'verderfs', 'oordeel', 'oordeels',
    'evangelie', 'evangelies', 'gebod', 'gebods',
    'geweten', 'gewetens', 'volk', 'volks', 'verbond', 'verbonds',
    'begin', 'hoofd', 'hoofds', 'water', 'waters',
    'kind', 'kinds', 'getal', 'beeld',
    'maaksel', 'maaksels', 'goed', 'goeds', 'kwaad', 'kwaads',
    'midden', 'einde', 'graf', 'grafs', 'boek', 'boeks',
    'schrift', 'schrifts', 'zwaard', 'zwaards',
    'gevaar', 'gevaars', 'land', 'lands', 'gericht', 'gerichts',
    'deel', 'deels', 'doel', 'doels', 'lijf', 'lijfs',
    'krachtbetoon', 'verstand', 'verstands', 'gemoed', 'gemoeds',
}


def modernize_sv1888(text, chapter=0, verse=0):
    """Apply allowed modernizations to SV1888 text."""
    if not text or not text.strip():
        return text

    t = text

    # Fix encoding issues (mojibake)
    t = t.replace('Ã©', 'é').replace('Ã«', 'ë').replace('Ã¤', 'ä')
    t = t.replace('Ã¶', 'ö').replace('Ã¼', 'ü').replace('Ã®', 'î')
    t = t.replace('Ã‰', 'É').replace('Ã‹', 'Ë')

    # === Phase 1: Handle idiomatic expressions BEFORE general rules ===
    # "om der X wil" -> "om de X wil"
    t = re.sub(r'\bom der\b', 'om de', t)
    # "in der eeuwigheid" -> "in de eeuwigheid"
    t = re.sub(r'\bin der\b', 'in de', t)
    t = re.sub(r'\bIn der\b', 'In de', t)
    # "dezer" -> "deze"
    t = re.sub(r'\bdezer\b', 'deze', t)
    t = re.sub(r'\bDezer\b', 'Deze', t)

    # === Phase 2: Handle compound forms BEFORE their components ===

    # "Desgenen" / "desgenen" -> "van Degene" / "van degene"
    # In SV, "Desgenen" mid-sentence capitalizes to honor God, we keep that with "Degene"
    t = re.sub(r'\bDesgenen\b', 'van Degene', t)
    t = re.sub(r'\bdesgenen\b', 'van degene', t)
    # "Desgelijks" -> "Evenzo"
    t = re.sub(r'\bDesgelijks\b', 'Evenzo', t)
    t = re.sub(r'\bdesgelijks\b', 'evenzo', t)

    # "Den zelven" (with space) -> "Dezelfde"
    t = re.sub(r'\bDen zelven\b', 'Dezelfde', t)
    t = re.sub(r'\bden zelven\b', 'dezelfde', t)

    # === HEERE (YHWH) - before Heere/den/des rules ===
    t = re.sub(r'\bdes HEEREN\b', 'van JAHWEH', t)
    t = re.sub(r'\bde HEERE\b', 'JAHWEH', t)
    t = re.sub(r'\bden HEERE\b', 'JAHWEH', t)
    t = re.sub(r'\bHEERE\b', 'JAHWEH', t)

    # === Heere (Jesus) - before den/des rules ===
    t = re.sub(r'\bdes Heeren\b', 'van de Heer', t)
    t = re.sub(r'\bden Heere\b', 'de Heer', t)
    t = re.sub(r'\bde Heere\b', 'de Heer', t)
    t = re.sub(r'\bHeere\b', 'Heer', t)

    # === Handle "des + NOUN" genitive BEFORE den rule (since "des" doesn't match "den") ===
    def replace_des(m):
        prefix = m.group(1)  # "des" or "Des"
        next_word = m.group(2)
        next_lower = next_word.lower()
        # Strip genitive -s to find base form
        is_het = next_lower in HET_WORDS
        if not is_het and next_lower.endswith('s') and len(next_lower) > 2:
            base = next_lower[:-1]
            is_het = base in HET_WORDS
        if is_het:
            article = 'het'
        else:
            article = 'de'
        if prefix[0].isupper():
            return f'Van {article} {next_word}'
        return f'van {article} {next_word}'

    t = re.sub(r'\b(des|Des)\s+(\w+)', replace_des, t)
    # Standalone "des" (shouldn't remain, but just in case)
    t = re.sub(r'\bdes\b', 'van de', t)
    t = re.sub(r'\bDes\b', 'Van de', t)

    # === Handle "uws + NOUN" genitive ===
    t = re.sub(r'\buws\s+(\w+)', lambda m: 'van uw ' + m.group(1), t)
    t = re.sub(r'\bUws\s+(\w+)', lambda m: 'van Uw ' + m.group(1), t)
    # standalone uws
    t = re.sub(r'\buws\b', 'uw', t)

    # === Pronouns ===
    t = re.sub(r'\bGijlieden\b', 'U', t)
    t = re.sub(r'\bgijlieden\b', 'u', t)
    t = re.sub(r'\bGij\b', 'U', t)
    t = re.sub(r'\bgij\b', 'u', t)
    t = re.sub(r'\bUlieden\b', 'U', t)
    t = re.sub(r'\bulieden\b', 'u', t)

    # === Demonstrative/relative pronouns ===
    t = re.sub(r'\bHetwelk\b', 'Dat', t)
    t = re.sub(r'\bhetwelk\b', 'dat', t)
    t = re.sub(r'\bDenzelven\b', 'Dezelfde', t)
    t = re.sub(r'\bdenzelven\b', 'dezelfde', t)
    t = re.sub(r'\bDezelve\b', 'Dezelfde', t)
    t = re.sub(r'\bdezelve\b', 'dezelfde', t)
    t = re.sub(r'\bhetzelve\b', 'hetzelfde', t)
    t = re.sub(r'\bHetzelve\b', 'Hetzelfde', t)
    t = re.sub(r'\bdenzelfden\b', 'dezelfde', t)
    t = re.sub(r'\bDenzelfden\b', 'Dezelfde', t)
    t = re.sub(r'\bdeszelven\b', 'van dezelfde', t)
    t = re.sub(r'\bDeszelven\b', 'Van dezelfde', t)
    t = re.sub(r'\bdeszelfs\b', 'van dezelfde', t)
    t = re.sub(r'\bDeszelfs\b', 'Van dezelfde', t)

    t = re.sub(r'\bdezen\b', 'deze', t)
    t = re.sub(r'\bDezen\b', 'Deze', t)
    t = re.sub(r'\bdien\b', 'die', t)
    t = re.sub(r'\bDien\b', 'Die', t)
    # "diens" -> "wie" (objective relative, not possessive in Romans context)
    # In "diens Hij wil" = "wie Hij wil" (whom He wills)
    t = re.sub(r'\bdiens\b', 'wie', t)
    t = re.sub(r'\bDiens\b', 'Wie', t)
    t = re.sub(r'\bwelken\b', 'welke', t)
    t = re.sub(r'\bWelken\b', 'Welke', t)

    # dengenen -> degenen (plural), dengene -> degene (singular)
    t = re.sub(r'\bdengenen\b', 'degenen', t)
    t = re.sub(r'\bDengenen\b', 'Degenen', t)
    t = re.sub(r'\bdengene\b', 'degene', t)
    t = re.sub(r'\bDengene\b', 'Degene', t)

    # hetgeen -> wat (relative pronoun "that which")
    t = re.sub(r'\bHetgeen\b', 'Wat', t)
    t = re.sub(r'\bhetgeen\b', 'wat', t)

    # welker -> van wie / waarvan (genitive relative)
    t = re.sub(r'\bwelker\b', 'van wie', t)
    t = re.sub(r'\bWelker\b', 'Van wie', t)

    # === zeide -> zei ===
    t = re.sub(r'\bzeide\b', 'zei', t)
    t = re.sub(r'\bZeide\b', 'Zei', t)

    # === Possessive genitive forms ===
    t = re.sub(r'\bZijns\b', 'Zijn', t)
    t = re.sub(r'\bzijns\b', 'zijn', t)
    t = re.sub(r'\bmijns\b', 'mijn', t)
    t = re.sub(r'\bMijns\b', 'Mijn', t)

    # === Archaic possessive/adjective endings ===
    t = re.sub(r'\bonzen\b', 'onze', t)
    t = re.sub(r'\bOnzen\b', 'Onze', t)
    t = re.sub(r'\buwen\b', 'uw', t)
    t = re.sub(r'\bUwen\b', 'Uw', t)
    t = re.sub(r'\bzijnen\b', 'zijn', t)
    t = re.sub(r'\bZijnen\b', 'Zijn', t)
    t = re.sub(r'\bmijnen\b', 'mijn', t)
    t = re.sub(r'\bMijnen\b', 'Mijn', t)
    t = re.sub(r'\beenen\b', 'een', t)
    t = re.sub(r'\bEenen\b', 'Een', t)
    t = re.sub(r'\bgoeden\b', 'goede', t)

    # Archaic possessive adjective forms
    t = re.sub(r'\buwe\b', 'uw', t)
    t = re.sub(r'\bUwe\b', 'Uw', t)
    t = re.sub(r'\bmijne\b', 'mijn', t)
    t = re.sub(r'\bMijne\b', 'Mijn', t)
    t = re.sub(r'\bzijne\b', 'zijn', t)
    t = re.sub(r'\bZijne\b', 'Zijn', t)

    # === Reflexive pronouns ===
    t = re.sub(r'\bMijzelven\b', 'Mijzelf', t)
    t = re.sub(r'\bmijzelven\b', 'mijzelf', t)
    t = re.sub(r'\bZichzelven\b', 'Zichzelf', t)
    t = re.sub(r'\bzichzelven\b', 'zichzelf', t)
    t = re.sub(r'\bonszelven\b', 'onszelf', t)
    t = re.sub(r'\bOnszelven\b', 'Onszelf', t)
    t = re.sub(r'\buzelven\b', 'uzelf', t)
    t = re.sub(r'\bUzelven\b', 'Uzelf', t)
    t = re.sub(r'\bzichzelve\b', 'zichzelf', t)
    t = re.sub(r'\bZichzelve\b', 'Zichzelf', t)

    # === Verb: zijt -> bent ===
    t = re.sub(r'\bzijt\b', 'bent', t)
    t = re.sub(r'\bZijt\b', 'Bent', t)

    # === "den" -> "de" (accusative article) ===
    t = re.sub(r'\bden\b', 'de', t)
    t = re.sub(r'\bDen\b', 'De', t)

    # === Genitive "der" -> "van de" (remaining after idiomatic ones) ===
    t = re.sub(r'\bder\b', 'van de', t)
    t = re.sub(r'\bDer\b', 'Van de', t)

    # === Archaic noun genitive endings (strip genitive -s after "van de/het") ===
    t = re.sub(r'\bvleses\b', 'vlees', t)
    t = re.sub(r'\bGeestes\b', 'Geest', t)
    t = re.sub(r'\bgeestes\b', 'geest', t)
    t = re.sub(r'\bdoods\b', 'dood', t)
    t = re.sub(r'\blichaams\b', 'lichaam', t)
    t = re.sub(r'\bgeloofs\b', 'geloof', t)
    t = re.sub(r'\brijkdoms\b', 'rijkdom', t)
    t = re.sub(r'\btoorns\b', 'toorn', t)
    t = re.sub(r'\bgemoeds\b', 'gemoed', t)
    t = re.sub(r'\bEvangelies\b', 'Evangelie', t)
    t = re.sub(r'\bevangelies\b', 'evangelie', t)
    t = re.sub(r'\bverbonds\b', 'verbond', t)
    t = re.sub(r'\bbloeds\b', 'bloed', t)
    t = re.sub(r'\bwoords\b', 'woord', t)
    t = re.sub(r'\bverstands\b', 'verstand', t)
    t = re.sub(r'\bvolks\b', 'volk', t)  # careful: not in "volkslied" etc.
    # "levens" - tricky, could be genitive or plural. In "des levens" context -> "van het leven"
    t = re.sub(r'\bvan het levens\b', 'van het leven', t)
    t = re.sub(r'\bvan de levens\b', 'van het leven', t)

    # "onzes" -> "van ons"
    t = re.sub(r'\bonzes\b', 'van ons', t)

    # === Archaic adjective endings ===
    t = re.sub(r'\btegenwoordigen\b', 'tegenwoordige', t)
    t = re.sub(r'\bzondigen\s+vlees\b', 'zondige vlees', t)
    t = re.sub(r'\bontfermenden\b', 'ontfermende', t)
    # "Heiligen Geest(es)" -> "Heilige Geest" (adjective before noun)
    # Don't change "de heiligen" (saints, noun)
    t = re.sub(r'\bHeiligen\s+Geest', 'Heilige Geest', t)

    # "dezes" -> genitive demonstrative -> "van deze" or just "deze"
    # "dezes doods" = "van deze dood" but "het lichaam dezes doods" -> "het lichaam van deze dood"
    t = re.sub(r'\bdezes\b', 'van deze', t)
    t = re.sub(r'\bDezes\b', 'Van deze', t)

    # Genitive noun endings that appear after "van de/het"
    t = re.sub(r'\bvredes\b', 'vrede', t)
    t = re.sub(r'\bheerlijkheids\b', 'heerlijkheid', t)
    t = re.sub(r'\bgerechtigheids\b', 'gerechtigheid', t)

    # === Fix double spaces ===
    t = re.sub(r'  +', ' ', t)

    return t.strip()


def apply_rom8_geest_rules(text, verse_num):
    """
    In Romans 8, use lowercase "geest" when contrasted with "vlees".
    """
    if not text:
        return text

    if verse_num in (1, 4, 5, 6):
        # geest (principle) contrasted with vlees
        text = text.replace('de Geest', 'de geest')
        text = text.replace('van de Geest', 'van de geest')

    elif verse_num == 9:
        # First "de Geest" = contrasted with vlees (lowercase)
        # "de Geest Gods" and "de Geest van Christus" = Holy Spirit (uppercase)
        text = re.sub(r'de Geest(?! Gods| van God| van Christus)', 'de geest', text)

    elif verse_num == 10:
        # "de geest is leven" - human spirit renewed
        text = text.replace('de Geest', 'de geest')

    elif verse_num == 15:
        # "geest van dienstbaarheid" and "geest van aanneming" - dispositions
        text = re.sub(r'de Geest van de (dienstbaarheid|aanneming)', r'de geest van de \1', text)

    return text


# Read original data from backup for comparison
with open(INPUT_FILE + '.bak', 'r', encoding='utf-8') as f:
    orig_data = json.load(f)

# We need the ORIGINAL text2026 values (before first script run) to properly count.
# But we don't have them anymore. So we re-read from the backup (which is the current state).
# We count: if textSV1888 exists and text2026 was empty -> new
# Otherwise if we change it -> fixed

# Actually, let's reload the very first version. The .bak is the already-modified version.
# We need to check: for ch 11-16, text2026 was originally empty.
# For ch 1-10, text2026 had values that we're now replacing.

# Process all chapters
for ch_idx, chapter in enumerate(data['chapters']):
    ch_num = chapter['number']

    for v_idx, verse in enumerate(chapter['verses']):
        v_num = verse['number']
        stats['checked'] += 1

        sv1888 = verse.get('textSV1888', '').strip()

        if not sv1888:
            continue

        # Generate the correct text2026 from SV1888
        new_text = modernize_sv1888(sv1888, ch_num, v_num)

        # Apply Romans 8 geest rules
        if ch_num == 8:
            new_text = apply_rom8_geest_rules(new_text, v_num)

        # For chapters 11-16, these are new translations
        if ch_num >= 11:
            verse['text2026'] = new_text
            verse['text2026_html'] = new_text
            stats['new'] += 1
        else:
            # Chapters 1-10: these had existing text2026, we're auditing/fixing
            old_text2026 = verse.get('text2026', '').strip()
            verse['text2026'] = new_text
            verse['text2026_html'] = new_text
            if old_text2026 != new_text:
                stats['fixed'] += 1

# Write output
with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"Total checked: {stats['checked']}")
print(f"New translations (ch 11-16): {stats['new']}")
print(f"Fixed/updated (ch 1-10): {stats['fixed']}")
print(f"Unchanged (ch 1-10): {stats['checked'] - stats['new'] - stats['fixed']}")
