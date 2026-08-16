"""Regressies voor de eenduidige redactionele review van 2 Koningen."""

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def verse(hoofdstuk, nummer):
    data = json.loads((ROOT / "data" / "2koningen" / f"{hoofdstuk}.json").read_text(encoding="utf-8"))
    return next(item for item in data["verses"] if item["number"] == nummer)


def test_eenduidige_2_koningen_correcties_staan_in_de_leestekst():
    assert "zilver" in verse(5, 5)["text2026"]
    assert "verzorgers" in verse(10, 1)["text2026"]
    assert "samenzwoer" in verse(17, 4)["text2026"]
    assert "levensonderhoud" in verse(25, 30)["text2026"]
    assert "talenten zilver" in verse(15, 19)["text2026"]
    assert "talenten zilver" in verse(18, 14)["text2026"]
    assert "de schedel" in verse(9, 35)["text2026"]


def test_reviewscript_bevat_de_besproken_eenduidige_correcties():
    from scripts.apply_google_review_2koningen import CORRECTIES

    assert (5, 5) in CORRECTIES
    assert (10, 1) in CORRECTIES
    assert (17, 4) in CORRECTIES
    assert (25, 30) in CORRECTIES


def test_citatiecorrecties_markeren_alleen_de_uitgesproken_woorden():
    from scripts.apply_citations_2koningen import RANGES

    assert RANGES[(1, 4)] == [("god", "U zult niet afkomen", "maar u zult de dood sterven.")]
    assert RANGES[(23, 18)] == [("mens", "Laat hem liggen", "verroere.")]


def test_inhoudelijke_koppelingen_uit_de_review_staan_in_de_sitegegevens():
    tags = json.loads((ROOT / "data" / "tags.json").read_text(encoding="utf-8"))["tags"]
    by_id = {tag["id"]: tag for tag in tags}
    assert {item["ref"] for item in by_id["kinderoffers"]["verzen"]} >= {"2koningen 3:27"}
    assert {item["ref"] for item in by_id["afgoden"]["verzen"]} >= {"2koningen 17:31"}

    pericopen = json.loads((ROOT / "data" / "pericopen.json").read_text(encoding="utf-8"))
    assert { (item["c"], item["v"]) for item in pericopen["2koningen"] } >= {(13, 22)}


def test_alle_reviewcorrecties_hebben_een_geregistreerd_principe():
    from scripts.apply_google_review_2koningen import CORRECTIES
    from scripts.registreer_reviewprincipes_samuel_koningen import REVIEW_CORRECTIES

    geregistreerd = {
        (boek, hoofdstuk, vers, oud, nieuw)
        for boek, hoofdstuk, vers, oud, nieuw in REVIEW_CORRECTIES
    }
    verwacht = {
        ("2koningen", hoofdstuk, vers, oud, nieuw)
        for (hoofdstuk, vers), paren in CORRECTIES.items()
        for oud, nieuw in paren
    }
    assert verwacht <= geregistreerd


def test_instellingseisen_uit_de_review_zijn_universeel_uitgevoerd():
    index = (ROOT / "index.html").read_text(encoding="utf-8")
    feedback = (ROOT / "js" / "feedback.js").read_text(encoding="utf-8")
    lees = (ROOT / "js" / "lees.js").read_text(encoding="utf-8")
    stijl = (ROOT / "css" / "style.css").read_text(encoding="utf-8")

    assert 'id="toggle-contextmarkeringen"' in index
    assert 'id="toggle-tags"' not in index
    assert 'id="toggle-geo-markeren"' not in index
    assert "Tag onderwerp" in feedback
    assert "Spelling en grammatica" in feedback
    assert "scrollIntoView" in lees
    assert "height: 75dvh" in stijl


def test_veilige_algemene_principes_zijn_corpusbreed_doorgevoerd():
    verboden = (
        r"\bzilvers\b", r"\buit oorzake van\b", r"\btrawanten?\b",
        r"\bdrie jaren\b", r"\bvlied\b",
    )
    gevonden = []
    for pad in (ROOT / "data").glob("*/*.json"):
        if not pad.stem.isdigit():
            continue
        data = json.loads(pad.read_text(encoding="utf-8"))
        for item in data.get("verses", []):
            tekst = item.get("text2026", "").lower()
            for woord in verboden:
                if re.search(woord, tekst):
                    gevonden.append(f"{pad.parent.name} {pad.stem}:{item['number']} — {woord}")
    assert not gevonden, "Niet doorgevoerde veilige principes:\n" + "\n".join(gevonden)
