"""Gecontroleerde OpenBible-versverwijzingen naar de lokale OV-nummering.

OpenBible gebruikt ESV-verwijzingen en vermeldt afwijkingen per vertaling in
``alternate_verses``. De onderstaande KJV-naar-OV-afwijkingen zijn aan de lokale
hoofdstukteksten getoetst; dit is geen algemene versificatieconverter.

Bij een opgesplitst bronvers blijft de eerste lokale deelversverwijzing staan.
Alleen de gecontroleerde daaropvolgende verzen schuiven op. Meerduidige
deelverskoppelingen, zoals 1 Samuël 20:42, worden hier niet geraden.

Bronformaat: https://github.com/openbibleinfo/Bible-Geocoding-Data#verses-verses
"""

from __future__ import annotations

import re


# In deze lokale psalmen hebben de opschriften een eigen versnummer. De
# ongenummerde Engelse opschriften maken geen deel uit van de KJV-versnummering.
PSALM_SINGLE_TITLE = frozenset({
    3, 4, 5, 6, 7, 8, 9, 12, 13, 18, 19, 20, 21, 22, 30, 31, 34, 36,
    38, 39, 40, 41, 42, 44, 45, 46, 47, 48, 49, 53, 55, 56, 57, 58,
    59, 61, 62, 63, 64, 65, 67, 68, 69, 70, 75, 76, 77, 80, 81, 83,
    84, 85, 88, 89, 92, 102, 108, 140, 142,
})
PSALM_DOUBLE_TITLE = frozenset({51, 52, 54, 60})

# De geografische bronmentions onder deze verwijzingen staan in het opschrift,
# niet in het eerste vers van de psalmtekst: Gath, respectievelijk Aram-naharaim,
# Edom, het Zoutdal en Zoba. Daarom geldt hier niet de gewone lichaamstekstoffset.
SOURCE_TITLE_VERSES = {"Ps.56.1": "Ps.56.1", "Ps.60.1": "Ps.60.2"}

CHAPTER_BOUNDARIES = {
    "Exod.6.1": "Exod.5.24",
    "1Sam.23.29": "1Sam.24.1",
    "Dan.5.31": "Dan.6.1",
    "Hos.2.1": "Hos.1.12",
    "Hos.11.12": "Hos.12.1",
    "Hos.13.16": "Hos.14.1",
    "Isa.9.1": "Isa.8.23",
    "Mic.5.1": "Mic.4.14",
    "Hag.1.15": "Hag.2.1",
}

# (Boek, hoofdstuk): (eerste Engels vers, laatste Engels vers, OV-offset).
# De grenzen sluiten niet-gecontroleerde, ongeldige en gesplitste deelverzen uit.
VERSE_OFFSETS = {
    ("Exod", 6): (2, 30, -1),
    ("1Sam", 24): (1, 22, 1),
    ("1Kgs", 22): (44, 53, 1),
    ("Neh", 8): (1, 18, 1),
    ("Isa", 9): (2, 21, -1),
    ("Dan", 6): (1, 28, 1),
    ("Hos", 2): (2, 23, -1),
    ("Hos", 12): (1, 14, 1),
    ("Hos", 14): (1, 9, 1),
    ("Mic", 5): (2, 15, -1),
    ("Hag", 2): (1, 23, 1),
    ("John", 1): (39, 51, 1),
}


def source_osis(verse: dict) -> str:
    """Geef de lokale OSIS-verwijzing zonder het bronrecord te veranderen.

    Alleen enkelvoudige bronverzen worden geconverteerd. Onbekende boeken,
    reeksen en niet-gecontroleerde verwijzingen blijven intact voor de aanroeper.
    Bewaar ``verse['osis']`` afzonderlijk voor controle van de bronherkomst.
    """
    original = verse.get("osis") or ""
    osis = (verse.get("alternate_verses") or {}).get("kjv") or original

    # Jeruzalem staat in de KJV in Handelingen 4:6, maar lokaal/SV in 4:5.
    # Deze gedeeltelijke versovergang geldt voor de gedocumenteerde mention,
    # niet voor elke mogelijke geografische vermelding onder Handelingen 4:6.
    if original == "Acts.4.5" and osis == "Acts.4.6":
        return "Acts.4.5"

    match = re.fullmatch(r"([^.]+)\.([1-9]\d*)\.([1-9]\d*)", osis)
    if not match:
        return osis
    book, chapter, number = match.group(1), int(match.group(2)), int(match.group(3))

    if osis in SOURCE_TITLE_VERSES:
        return SOURCE_TITLE_VERSES[osis]
    if osis in CHAPTER_BOUNDARIES:
        return CHAPTER_BOUNDARIES[osis]

    if book == "Ps":
        if chapter in PSALM_DOUBLE_TITLE:
            return f"Ps.{chapter}.{number + 2}"
        if chapter in PSALM_SINGLE_TITLE:
            return f"Ps.{chapter}.{number + 1}"

    rule = VERSE_OFFSETS.get((book, chapter))
    if rule:
        first, last, offset = rule
        if first <= number <= last:
            return f"{book}.{chapter}.{number + offset}"
    return osis
