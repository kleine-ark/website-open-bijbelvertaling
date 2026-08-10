#!/usr/bin/env python3
"""Geef Psalm 1–150 een vaste, inhoudelijke titel in het liederenboek."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

# De titels volgen de eigen inhoud van iedere psalm. Het psalmnummer blijft
# vooraan staan, zodat zoeken, nummering en herkenning ongewijzigd blijven.
PSALM_TITELS = {
    1: "De twee wegen",
    2: "De gezalfde Koning",
    3: "Veilig onder Gods schild",
    4: "In vrede neerliggen",
    5: "Morgengebed om leiding",
    6: "Gebed in ziekte",
    7: "De rechtvaardige Rechter",
    8: "Hoe heerlijk is Uw Naam",
    9: "God doet de verdrukte recht",
    10: "Waarom staat U van verre?",
    11: "JAHWEH is in Zijn heilige tempel",
    12: "De zuivere woorden van JAHWEH",
    13: "Hoelang, o JAHWEH?",
    14: "De dwaas zegt: Er is geen God",
    15: "Wie mag wonen op Uw heilige berg?",
    16: "Het pad van het leven",
    17: "Bewaar mij als Uw oogappel",
    18: "Mijn Rotssteen en mijn Verlosser",
    19: "De hemel en het Woord getuigen",
    20: "Gebed voor de koning",
    21: "Dank voor de overwinning van de koning",
    22: "Mijn God, waarom hebt U mij verlaten?",
    23: "JAHWEH is mijn Herder",
    24: "De Koning van de ere",
    25: "Maak mij Uw wegen bekend",
    26: "Doe mij recht, JAHWEH",
    27: "JAHWEH is mijn Licht en mijn Heil",
    28: "Hoor mijn smeking",
    29: "De stem van JAHWEH over de wateren",
    30: "Mijn rouw veranderd in vreugdedans",
    31: "In Uw hand beveel ik mijn geest",
    32: "Welgelukzalig wie vergeving ontvangt",
    33: "Zing een nieuw lied voor de Schepper",
    34: "Smaak en zie dat JAHWEH goed is",
    35: "Strijd tegen wie mij bestrijden",
    36: "Bij U is de bron van het leven",
    37: "Wees niet afgunstig op de kwaaddoeners",
    38: "Mijn zonden gaan over mijn hoofd",
    39: "Leer mij hoe vergankelijk ik ben",
    40: "Ik heb JAHWEH lang verwacht",
    41: "Welgelukzalig wie acht geeft op de arme",
    42: "Zoals een hert verlangt naar water",
    43: "Zend Uw licht en Uw waarheid",
    44: "Om U worden wij de hele dag gedood",
    45: "Bruiloftslied voor de Koning",
    46: "God is ons een Toevlucht en Sterkte",
    47: "God is Koning over de hele aarde",
    48: "De stad van de grote Koning",
    49: "Rijkdom kan geen mens verlossen",
    50: "God verschijnt als Rechter",
    51: "Schep in mij een rein hart",
    52: "De olijfboom in Gods huis",
    53: "Er is niemand die goed doet",
    54: "God is mijn Helper",
    55: "Werp uw zorg op JAHWEH",
    56: "Mijn tranen in Uw fles",
    57: "Onder de schaduw van Uw vleugels",
    58: "God richt recht op aarde",
    59: "Verlos mij van bloeddorstige mensen",
    60: "Herstel ons na de nederlaag",
    61: "Leid mij op de Rotssteen",
    62: "Alleen bij God rust mijn ziel",
    63: "Mijn ziel dorst naar U",
    64: "Verberg mij voor de samenzwering",
    65: "U hoort het gebed",
    66: "Kom en zie Gods daden",
    67: "Laat Uw aangezicht over ons lichten",
    68: "God trekt op voor Zijn volk",
    69: "De ijver voor Uw huis verteert mij",
    70: "Haast U om mij te helpen",
    71: "Verlaat mij niet in mijn ouderdom",
    72: "De rechtvaardige Koning en Zijn vrederijk",
    73: "God is het deel van mijn hart",
    74: "Gedenk Uw gemeente",
    75: "God is de Rechter",
    76: "God verbreekt de wapens van de oorlog",
    77: "Ik gedenk de daden van JAHWEH",
    78: "Israëls geschiedenis als waarschuwing",
    79: "Jeruzalem tot puinhopen gemaakt",
    80: "Herstel ons, God van de legermachten",
    81: "Doe uw mond wijd open",
    82: "God oordeelt de rechters",
    83: "Zwijg niet tegenover Uw vijanden",
    84: "Hoe lieflijk zijn Uw woningen",
    85: "Gerechtigheid en vrede kussen elkaar",
    86: "Leer mij Uw weg",
    87: "Sion, stad van God",
    88: "Mijn ziel is verzadigd van ellende",
    89: "Gods verbond met David",
    90: "Leer ons onze dagen tellen",
    91: "Veilig in de schuilplaats van de Allerhoogste",
    92: "Het is goed JAHWEH te loven",
    93: "JAHWEH regeert",
    94: "God van de vergeldingen",
    95: "Kom, laat ons aanbidden",
    96: "Verkondig Zijn heil onder de volken",
    97: "JAHWEH regeert, de aarde verheuge zich",
    98: "Een nieuw lied om Gods heil",
    99: "Heilig is Hij",
    100: "Dien JAHWEH met blijdschap",
    101: "Een oprecht huis voor de Koning",
    102: "Gebed van een verdrukte",
    103: "Loof JAHWEH, mijn ziel",
    104: "De Schepper en Onderhouder",
    105: "Gedenk Zijn wonderdaden",
    106: "Wij hebben gezondigd met onze vaderen",
    107: "Verlost uit alle benauwdheid",
    108: "Mijn hart is bereid",
    109: "Gebed tegen de goddeloze aanklager",
    110: "Priester-Koning aan Gods rechterhand",
    111: "Groot zijn de werken van JAHWEH",
    112: "Welgelukzalig wie JAHWEH vreest",
    113: "God verheft de geringe",
    114: "Toen Israël uit Egypte trok",
    115: "Niet ons, maar Uw Naam geef eer",
    116: "Ik heb lief, want JAHWEH hoort",
    117: "Alle volken, loof JAHWEH",
    118: "De verworpen Steen is tot Hoeksteen geworden",
    119: "Een lofzang op Gods Woord",
    120: "Vredezoeker tussen strijders",
    121: "Mijn hulp is van JAHWEH",
    122: "Bid om de vrede van Jeruzalem",
    123: "Onze ogen zijn op JAHWEH",
    124: "Onze hulp is in de Naam van JAHWEH",
    125: "Vast als de berg Sion",
    126: "Wie met tranen zaaien, zullen met gejuich maaien",
    127: "Als JAHWEH het huis niet bouwt",
    128: "De zegen van wie JAHWEH vreest",
    129: "Van mijn jeugd af verdrukt",
    130: "Uit de diepten roep ik tot U",
    131: "Mijn ziel is stil als een gespeend kind",
    132: "Gods belofte aan David en Sion",
    133: "Hoe goed is broederlijke eenheid",
    134: "Loof JAHWEH in de nacht",
    135: "JAHWEH is groot boven alle goden",
    136: "Zijn goedertierenheid is in eeuwigheid",
    137: "Aan de rivieren van Babel",
    138: "JAHWEH voltooit het voor mij",
    139: "U doorgrondt en kent mij",
    140: "Bewaar mij voor gewelddadige mensen",
    141: "Laat mijn gebed als reukwerk zijn",
    142: "Gebed in de grot",
    143: "Leer mij Uw wil te doen",
    144: "Welgelukzalig het volk wiens God JAHWEH is",
    145: "Uw Koninkrijk is van alle eeuwen",
    146: "Vertrouw niet op vorsten",
    147: "Hij geneest de gebrokenen van hart",
    148: "Hemel en aarde, loof JAHWEH",
    149: "Zing JAHWEH een nieuw lied",
    150: "Alles wat adem heeft, love JAHWEH",
}


def volledige_titel(psalmnummer: int) -> str:
    """Combineer het herkenbare nummer met de inhoudelijke psalmtitel."""

    return f"Psalm {psalmnummer} — {PSALM_TITELS[psalmnummer]}"


def update_catalogus(root: Path = ROOT) -> int:
    """Werk de psalmtitels in de liedcatalogus bij en geef de dekking terug."""

    path = root / "data" / "naslag-liederen.json"
    catalogus = json.loads(path.read_text(encoding="utf-8"))
    bijgewerkt = set()

    for item in catalogus["items"]:
        item_id = item.get("id", "")
        if not item_id.startswith("psalm-"):
            continue
        try:
            nummer = int(item_id.removeprefix("psalm-"))
        except ValueError as exc:
            raise ValueError(f"ongeldig psalm-id: {item_id}") from exc
        if nummer not in PSALM_TITELS:
            raise ValueError(f"onverwachte psalm in liedcatalogus: {nummer}")
        item["naam"] = volledige_titel(nummer)
        bijgewerkt.add(nummer)

    verwacht = set(range(1, 151))
    if bijgewerkt != verwacht:
        ontbrekend = sorted(verwacht - bijgewerkt)
        extra = sorted(bijgewerkt - verwacht)
        raise ValueError(f"psalmdekking onvolledig; ontbrekend={ontbrekend}, extra={extra}")

    path.write_text(
        json.dumps(catalogus, ensure_ascii=False, indent=1) + "\n",
        encoding="utf-8",
    )
    return len(bijgewerkt)


def main() -> None:
    aantal = update_catalogus()
    print(f"psalmtitels bijgewerkt: {aantal}/150")


if __name__ == "__main__":
    main()
