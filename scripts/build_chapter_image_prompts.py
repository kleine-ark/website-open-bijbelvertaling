#!/usr/bin/env python3
"""Generate AI image-generation prompts for every chapter in the bible.

Reads `data/books.json` and the per-chapter JSONs in `data/{bookId}/{n}.json`,
then writes `data/chapter-image-prompts.json` containing one entry per chapter
with: book, chapter, title_nl, subject, prompt, style.

The prompt uses a template-based approach categorised per book-type
(OT-narrative, OT-prophet, OT-wisdom, OT-psalm, NT-gospel, NT-acts,
NT-letter, NT-apocalypse, AP). The chapter-intro `text2026` (or fallback
`text1637`) is used as the source of the chapter subject.

No external AI calls — purely deterministic text manipulation. Output is a
sensible starting point for human refinement before sending to an
image-generation model.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
BOOKS_FILE = DATA / "books.json"
OUTPUT = DATA / "chapter-image-prompts.json"

# ---------------------------------------------------------------------------
# Book classification
# ---------------------------------------------------------------------------

OT_NARRATIVE = {
    "genesis", "exodus", "leviticus", "numeri", "deuteronomium",
    "jozua", "richteren", "ruth",
    "1samuel", "2samuel", "1koningen", "2koningen",
    "1kronieken", "2kronieken", "ezra", "nehemia", "esther",
}
OT_WISDOM = {"job", "spreuken", "prediker", "hooglied"}
OT_PSALM = {"psalmen"}
OT_PROPHET_MAJOR = {"jesaja", "jeremia", "klaagliederen", "ezechiel", "daniel"}
OT_PROPHET_MINOR = {
    "hosea", "joel", "amos", "obadja", "jona", "micha",
    "nahum", "habakuk", "zefanja", "haggai", "zacharia", "maleachi",
}
NT_GOSPEL = {"mattheus", "markus", "lukas", "johannes"}
NT_ACTS = {"handelingen"}
NT_LETTER = {
    "romeinen", "1korinthiers", "2korinthiers", "galaten", "efeziers",
    "filippenzen", "kolossenzen", "1tessalonicensen", "2tessalonicensen",
    "1timotheus", "2timotheus", "titus", "filemon", "hebreeen",
    "jakobus", "1petrus", "2petrus", "1johannes", "2johannes", "3johannes",
    "judas",
}
NT_APOCALYPSE = {"openbaring"}

AP_NARRATIVE = {
    "tobit", "judith", "1makkabeeen", "2makkabeeen", "3makkabeeen",
    "estherapocrief", "susanna", "belenddedraak",
}
AP_WISDOM = {"boekderwijsheid", "jezussirach"}
AP_PROPHET = {"baruch", "3ezra", "4ezra"}
AP_PRAYER = {"gebedvanazaria", "gezangindevuuroven", "gebedvanmanasse"}


def book_category(book_id: str) -> str:
    if book_id in OT_NARRATIVE:
        return "ot_narrative"
    if book_id in OT_WISDOM:
        return "ot_wisdom"
    if book_id in OT_PSALM:
        return "ot_psalm"
    if book_id in OT_PROPHET_MAJOR or book_id in OT_PROPHET_MINOR:
        return "ot_prophet"
    if book_id in NT_GOSPEL:
        return "nt_gospel"
    if book_id in NT_ACTS:
        return "nt_acts"
    if book_id in NT_LETTER:
        return "nt_letter"
    if book_id in NT_APOCALYPSE:
        return "nt_apocalypse"
    if book_id in AP_NARRATIVE:
        return "ap_narrative"
    if book_id in AP_WISDOM:
        return "ap_wisdom"
    if book_id in AP_PROPHET:
        return "ap_prophet"
    if book_id in AP_PRAYER:
        return "ap_prayer"
    return "unknown"


# ---------------------------------------------------------------------------
# Style suffixes per category
# ---------------------------------------------------------------------------

STYLE_OLD_MASTER = (
    "old master oil painting, Rembrandt-inspired chiaroscuro, warm earth tones, "
    "dramatic lighting, historically accurate Middle-Eastern garments, "
    "Semitic faces, no text, no captions"
)
STYLE_CARAVAGGIO = (
    "old master oil painting, Caravaggio-style chiaroscuro, deep shadows and "
    "warm golden highlights, historically accurate first-century garments, "
    "Semitic faces, no text, no captions"
)
STYLE_PRE_RAPHAELITE = (
    "Pre-Raphaelite oil painting, jewel tones, lush detail, symbolic imagery, "
    "historically accurate ancient Near-Eastern garments, no text, no captions"
)
STYLE_VISIONARY = (
    "visionary symbolic oil painting in the style of William Blake and Gustave "
    "Dore, dramatic celestial light, deep cosmic atmosphere, awe-inspiring "
    "composition, no text, no captions"
)
STYLE_PSALM = (
    "contemplative oil painting, soft golden hour light, devotional atmosphere, "
    "old master style, ancient Israelite setting, no text, no captions"
)
STYLE_LETTER = (
    "symbolic devotional oil painting, soft warm candlelight, old master style, "
    "first-century Mediterranean setting, no text, no captions"
)
STYLE_WISDOM = (
    "contemplative old master oil painting, golden warm light, ancient scroll "
    "and quiet study setting, no text, no captions"
)
STYLE_PROPHET = (
    "dramatic prophetic oil painting, stormy skies and shafts of divine light, "
    "old master style, ancient Near-Eastern setting, no text, no captions"
)


def style_for(cat: str) -> str:
    return {
        "ot_narrative": STYLE_OLD_MASTER,
        "ot_wisdom": STYLE_WISDOM,
        "ot_psalm": STYLE_PSALM,
        "ot_prophet": STYLE_PROPHET,
        "nt_gospel": STYLE_CARAVAGGIO,
        "nt_acts": STYLE_CARAVAGGIO,
        "nt_letter": STYLE_LETTER,
        "nt_apocalypse": STYLE_VISIONARY,
        "ap_narrative": STYLE_OLD_MASTER,
        "ap_wisdom": STYLE_WISDOM,
        "ap_prophet": STYLE_PROPHET,
        "ap_prayer": STYLE_PSALM,
    }.get(cat, STYLE_OLD_MASTER)


# ---------------------------------------------------------------------------
# Subject extraction
# ---------------------------------------------------------------------------

def clean_intro(text: str) -> str:
    """Strip verse-number markers and tidy punctuation.

    Handles patterns like "vers 1, 2", "vers 1-3", " 12 ", "1.", at the start,
    middle, and end of sentences. Removes the resulting artefacts ("vers ,",
    ", etc.", trailing commas) so the output reads naturally.
    """
    if not text:
        return ""
    t = text.strip()

    # Remove "vers X[, Y][-Z]" reference clauses (most common form is mid- or
    # end-sentence: "..., vers 1, 2."). "vers" or "versen" with optional number.
    t = re.sub(
        r"\s*,\s*vers(?:en)?\s*\d*(?:\s*[-,–]\s*\d+)*",
        "",
        t,
        flags=re.IGNORECASE,
    )
    t = re.sub(
        r"\bvers(?:en)?\s*\d+(?:\s*[-,–]\s*\d+)*",
        "",
        t,
        flags=re.IGNORECASE,
    )
    # Remove "etc." which often follows a stripped verse marker
    t = re.sub(r",\s*etc\.?", "", t, flags=re.IGNORECASE)
    # Remove standalone integers used as verse markers (1-3 digits) when
    # preceded by start/punctuation/space and followed by punctuation/end.
    t = re.sub(
        r"(^|[\s,;.])(\d{1,3})(?=[.,;\s]|$)",
        r"\1",
        t,
    )
    # Strip leading digits and surrounding whitespace
    t = re.sub(r"^\s*\d+\s*", "", t)
    # Clean up artefacts like ", ." or ".."
    t = re.sub(r"\s*,\s*\.", ".", t)
    t = re.sub(r"\.\s*\.+", ".", t)
    t = re.sub(r"\s*,\s*,+", ",", t)
    t = re.sub(r"\s+,", ",", t)
    t = re.sub(r"\s+\.", ".", t)
    # Drop dangling commas/periods at sentence start
    t = re.sub(r"^[\s,.;:]+", "", t)
    # Squeeze whitespace
    t = re.sub(r"\s+", " ", t).strip()
    # Trim trailing commas/semicolons/whitespace
    t = t.rstrip(" ,;:")
    return t


def first_sentence(text: str, max_chars: int = 220) -> str:
    """Return the first sentence of text, capped at max_chars.

    Strips any trailing period, comma or whitespace so callers can safely
    append their own punctuation.
    """
    if not text:
        return ""
    # Split on . ! ? followed by space
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    out = parts[0] if parts else text
    if len(out) > max_chars:
        out = out[:max_chars].rsplit(" ", 1)[0] + "..."
    return out.rstrip(" .,;:").strip()


def get_intro(chapter: dict) -> str:
    ci = chapter.get("chapterIntro") or chapter.get("chapter", {}).get("intro") or {}
    if isinstance(ci, dict):
        return ci.get("text2026") or ci.get("text1637") or ""
    if isinstance(ci, str):
        return ci
    return ""


def get_verse_text(verse: dict) -> str:
    return verse.get("text2026") or verse.get("textSV1888") or verse.get("text1637") or ""


def get_subject(chapter: dict) -> str:
    """Pick a one-sentence subject summary."""
    intro = get_intro(chapter)
    cleaned = clean_intro(intro)
    if cleaned:
        return first_sentence(cleaned)
    # Fallback: first verse
    verses = chapter.get("verses", [])
    if verses:
        return first_sentence(get_verse_text(verses[0]), max_chars=180)
    return ""


def get_context_snippet(chapter: dict, max_chars: int = 350) -> str:
    """Combine first 3 verses (or intro) for richer context within a prompt."""
    intro = clean_intro(get_intro(chapter))
    if intro:
        snippet = intro
    else:
        verses = chapter.get("verses", [])[:3]
        snippet = " ".join(get_verse_text(v) for v in verses)
    snippet = re.sub(r"\s+", " ", snippet).strip()
    if len(snippet) > max_chars:
        snippet = snippet[:max_chars].rsplit(" ", 1)[0] + "..."
    return snippet


# ---------------------------------------------------------------------------
# Prompt templates per category
# ---------------------------------------------------------------------------

def build_prompt(book_id: str, book_name: str, chapter_num: int,
                 cat: str, subject: str, context: str) -> str:
    """Build a visual prompt focused on the chapter's central scene."""
    if cat == "ot_narrative":
        return (
            f"Biblical scene from {book_name} {chapter_num}: {subject}. "
            f"Composition focuses on the central moment of the story, "
            f"set in the ancient Near East, with figures wearing historically "
            f"accurate Hebrew garments. Warm, dramatic lighting evoking "
            f"reverence."
        )
    if cat == "ot_wisdom":
        return (
            f"Symbolic illustration for {book_name} {chapter_num}: {subject}. "
            f"A contemplative scene evoking ancient wisdom — perhaps an aged "
            f"sage with a scroll, or a pair of paths in a desert landscape, "
            f"or a still olive grove at dawn. Quiet, meditative atmosphere."
        )
    if cat == "ot_psalm":
        return (
            f"Devotional scene inspired by Psalm {chapter_num}: {subject}. "
            f"Evocative imagery of an ancient Israelite at prayer, or of the "
            f"natural world (mountains, springs, a shepherd with sheep, a "
            f"fortress, a starry sky) reflecting the psalm's emotional tone. "
            f"Warm, contemplative lighting."
        )
    if cat == "ot_prophet":
        return (
            f"Prophetic vision from {book_name} {chapter_num}: {subject}. "
            f"A dramatic scene of a prophet receiving or proclaiming the word "
            f"of God, with stormy skies, shafts of divine light, or symbolic "
            f"imagery from the chapter (cities, armies, mountains, rivers, "
            f"or visionary creatures). Ancient Near-Eastern setting."
        )
    if cat == "nt_gospel":
        return (
            f"Gospel scene from {book_name} {chapter_num}: {subject}. "
            f"Jesus or his disciples in a first-century Galilean or Judean "
            f"setting; figures in historically accurate first-century garments "
            f"with Semitic features. Composition centred on the chapter's "
            f"key encounter, miracle, parable, or teaching moment."
        )
    if cat == "nt_acts":
        return (
            f"Scene from Acts {chapter_num}: {subject}. "
            f"First-century apostolic ministry — preaching in a city square, "
            f"a miracle in a Roman provincial setting, a sea voyage, or a "
            f"prison cell. Diverse Mediterranean people in period-correct "
            f"dress."
        )
    if cat == "nt_letter":
        return (
            f"Symbolic devotional scene for {book_name} {chapter_num}: "
            f"{subject}. Imagery suggested by the chapter's theme — a "
            f"first-century believer in prayer, an open scroll on a wooden "
            f"table by candlelight, a small house-church gathering, "
            f"a runner pressing toward a goal, armour of a Roman soldier, "
            f"or other symbolic motif drawn from the text."
        )
    if cat == "nt_apocalypse":
        return (
            f"Apocalyptic vision from Revelation {chapter_num}: {subject}. "
            f"Cosmic, symbolic imagery with celestial light, thrones, "
            f"creatures, seals, trumpets, or the heavenly Jerusalem as "
            f"appropriate. Awe-inspiring composition with an aged seer "
            f"(John of Patmos) optionally present in the foreground."
        )
    if cat == "ap_narrative":
        return (
            f"Scene from the apocryphal book {book_name} {chapter_num}: "
            f"{subject}. Ancient Near-Eastern or Hellenistic-era setting, "
            f"figures in period-correct garments, composition focused on the "
            f"central narrative moment of the chapter."
        )
    if cat == "ap_wisdom":
        return (
            f"Symbolic illustration for the apocryphal wisdom text "
            f"{book_name} {chapter_num}: {subject}. Contemplative scene with "
            f"a sage, a scroll, or symbolic imagery of virtue and folly. "
            f"Hellenistic-Jewish setting, quiet meditative atmosphere."
        )
    if cat == "ap_prophet":
        return (
            f"Visionary scene from the apocryphal book {book_name} "
            f"{chapter_num}: {subject}. A prophet or seer receiving a divine "
            f"vision, dramatic lighting and symbolic imagery from the text."
        )
    if cat == "ap_prayer":
        return (
            f"Devotional scene for {book_name}: {subject}. "
            f"A figure in earnest prayer, ancient garments, dramatic lighting "
            f"evoking penitence, deliverance, or praise."
        )
    # Fallback
    return (
        f"Biblical scene for {book_name} {chapter_num}: {subject}. "
        f"Old master oil painting, ancient Near-Eastern setting."
    )


# ---------------------------------------------------------------------------
# Special hand-tuned prompts (for showcase chapters)
# ---------------------------------------------------------------------------

SPECIAL_PROMPTS: dict[tuple[str, int], str] = {
    ("genesis", 1): (
        "Cosmic creation scene: God's Spirit hovering over dark, formless "
        "waters; first light breaking through, separating day from night; "
        "warm golden glow against deep blue cosmic void. No human figures."
    ),
    ("genesis", 2): (
        "The Garden of Eden: lush ancient paradise with rivers, fruit trees, "
        "and the tree of life at the centre; Adam newly formed from the dust, "
        "morning light filtering through leaves."
    ),
    ("genesis", 3): (
        "Adam and Eve beneath the tree of knowledge; a serpent coiled around "
        "the trunk; the moment of the temptation, with shadow falling across "
        "the garden."
    ),
    ("genesis", 6): (
        "Noah inspecting the great wooden ark under construction; storm "
        "clouds gathering on the horizon over an ancient Mesopotamian "
        "landscape."
    ),
    ("genesis", 22): (
        "Abraham on Mount Moriah, knife raised over Isaac bound on a stone "
        "altar; an angel staying his hand; a ram caught in a thicket nearby."
    ),
    ("exodus", 3): (
        "Moses before the burning bush in the Sinai wilderness, removing his "
        "sandals on holy ground; the bush ablaze with golden flame yet "
        "unconsumed."
    ),
    ("exodus", 14): (
        "The parting of the Red Sea: walls of water on either side, Moses "
        "with arm outstretched, the Israelites crossing on dry ground at "
        "dawn, Pharaoh's chariots in the distance."
    ),
    ("exodus", 20): (
        "Moses on Mount Sinai receiving the two stone tablets of the law amid "
        "thunder, lightning, and dense cloud; the people gathered in awe at "
        "the foot of the mountain."
    ),
    ("psalmen", 23): (
        "A shepherd in ancient Israelite garments leading a small flock of "
        "sheep beside still waters in a green pasture, with a rod and staff "
        "in hand; soft golden hour light."
    ),
    ("jesaja", 53): (
        "A solitary suffering servant figure walking a barren road at dusk, "
        "head bowed under the weight of grief; a faint cross-shadow on the "
        "ground; sombre dignified atmosphere."
    ),
    ("daniel", 6): (
        "Daniel in the lions' den, kneeling in prayer; lions resting "
        "peacefully around him; a single shaft of light from above through a "
        "stone opening."
    ),
    ("jona", 2): (
        "Jonah in prayer inside the belly of the great fish; surrounded by "
        "swirling deep-sea darkness; a single ray of golden light reaching "
        "him."
    ),
    ("mattheus", 2): (
        "The Magi presenting gifts of gold, frankincense, and myrrh to the "
        "infant Jesus in Bethlehem; Mary holding the child; warm lamplight "
        "in a humble first-century house."
    ),
    ("mattheus", 5): (
        "Jesus seated on a hillside above the Sea of Galilee, teaching the "
        "Sermon on the Mount to a gathered crowd at sunrise."
    ),
    ("markus", 5): (
        "Jesus standing on the lakeshore at dawn, calmly facing a wild man "
        "emerging from rocky tombs, broken chains around his ankles. A herd "
        "of pigs in the distance. Sea of Galilee mist."
    ),
    ("lukas", 2): (
        "The nativity in Bethlehem: Mary and Joseph beside the manger with "
        "the infant Jesus; shepherds arriving in awe; warm lamplight in a "
        "stone stable, a star above."
    ),
    ("lukas", 15): (
        "The prodigal son returning home, kneeling in tattered clothes; his "
        "father running to embrace him with open arms; warm sunset light "
        "over an ancient Judean farmstead."
    ),
    ("johannes", 1): (
        "Symbolic scene of the divine Word: a bright cosmic light piercing "
        "darkness over a primordial landscape; John the Baptist as a small "
        "figure pointing toward the light."
    ),
    ("johannes", 4): (
        "Jesus seated at Jacob's well at noon, speaking with the Samaritan "
        "woman holding a clay water jar; ancient stone well, hot Judean "
        "sunlight."
    ),
    ("johannes", 19): (
        "Christ on the cross at Golgotha; a darkening sky; Mary and the "
        "beloved disciple at the foot of the cross; sombre dignified "
        "atmosphere."
    ),
    ("johannes", 20): (
        "The empty tomb at sunrise: the stone rolled away, linen cloths "
        "folded inside, Mary Magdalene weeping in the garden as the risen "
        "Christ approaches; first light of Easter morning."
    ),
    ("handelingen", 2): (
        "Pentecost in Jerusalem: tongues of fire resting on the heads of the "
        "apostles in an upper room; a rushing wind visible as swirling "
        "golden light; Peter rising to speak."
    ),
    ("romeinen", 8): (
        "A first-century believer in earnest prayer at a wooden table by "
        "candlelight, an open scroll before him; through a window, dawn "
        "light breaking — symbolising no condemnation, the Spirit of life, "
        "and hope of glory."
    ),
    ("1korinthiers", 13): (
        "A symbolic scene of love: a quiet act of compassion in a "
        "first-century home — a woman tending the sick, an old man embracing "
        "a child — in soft warm candlelight."
    ),
    ("efeziers", 6): (
        "A first-century believer arrayed in symbolic spiritual armour — "
        "belt, breastplate, sandals, shield, helmet, sword — standing firm "
        "against a stormy backdrop."
    ),
    ("openbaring", 1): (
        "The aged apostle John on the rocky island of Patmos, kneeling in "
        "awe before a vision of the glorified Christ amid seven golden "
        "lampstands, eyes like flame, voice like rushing waters."
    ),
    ("openbaring", 21): (
        "The new Jerusalem descending from heaven: a radiant golden city "
        "with twelve gates of pearl, walls of jasper, on a renewed earth; "
        "bright cosmic light."
    ),
    ("openbaring", 22): (
        "The river of the water of life flowing from the throne of God and "
        "of the Lamb; the tree of life on either side bearing twelve fruits; "
        "radiant heavenly city in the background."
    ),
}


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    with BOOKS_FILE.open(encoding="utf-8") as f:
        books_meta = json.load(f)

    entries: list[dict] = []
    fallbacks_used: list[str] = []

    for book in books_meta["books"]:
        book_id = book["id"]
        book_name = book["nameDutch"]
        chapters = book.get("chaptersIncluded", [])
        cat = book_category(book_id)
        if cat == "unknown":
            fallbacks_used.append(f"unknown-category:{book_id}")

        for ch in chapters:
            ch_path = DATA / book_id / f"{ch}.json"
            if not ch_path.exists():
                fallbacks_used.append(f"missing-file:{book_id}/{ch}")
                subject = f"{book_name} hoofdstuk {ch}"
                context = ""
            else:
                with ch_path.open(encoding="utf-8") as cf:
                    chapter_data = json.load(cf)
                subject = get_subject(chapter_data)
                context = get_context_snippet(chapter_data)
                if not subject:
                    fallbacks_used.append(f"empty-subject:{book_id}/{ch}")
                    subject = f"{book_name} hoofdstuk {ch}"

            key = (book_id, ch)
            if key in SPECIAL_PROMPTS:
                prompt = SPECIAL_PROMPTS[key]
            else:
                prompt = build_prompt(book_id, book_name, ch, cat,
                                      subject, context)

            entries.append({
                "book": book_id,
                "chapter": ch,
                "title_nl": f"{book_name} {ch}",
                "subject": subject,
                "prompt": prompt,
                "style": style_for(cat),
            })

    # Sort by book order in books.json, then chapter number
    book_order = {b["id"]: i for i, b in enumerate(books_meta["books"])}
    entries.sort(key=lambda e: (book_order.get(e["book"], 999), e["chapter"]))

    OUTPUT.write_text(
        json.dumps(entries, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    size_kb = OUTPUT.stat().st_size / 1024
    print(f"Wrote {len(entries)} prompts to {OUTPUT} ({size_kb:.1f} KB)")
    if fallbacks_used:
        print(f"Fallbacks used: {len(fallbacks_used)}")
        for fb in fallbacks_used[:20]:
            print(f"  - {fb}")


if __name__ == "__main__":
    main()
