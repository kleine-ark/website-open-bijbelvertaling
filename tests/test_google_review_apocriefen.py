import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATUSSEN = {"verwerkt", "afgedekt", "gepland", "open", "vervallen"}


def vers(boek, hoofdstuk, nummer):
    data = json.loads((ROOT / "data" / boek / f"{hoofdstuk}.json").read_text(encoding="utf-8"))
    return next(item for item in data["verses"] if item["number"] == nummer)


def zichtbaar(boek, hoofdstuk, nummer):
    html = vers(boek, hoofdstuk, nummer)["text2026_html"]
    return re.sub(r"<[^>]+>", "", re.sub(r"<sup[^>]*>.*?</sup>", "", html))


def reviewlijst(boek):
    return json.loads((ROOT / "data" / f"google-opmerkingen-{boek}-reviewqueue.json").read_text(encoding="utf-8"))["items"]


def test_3ezra_laat_de_zaak_niet_liggen():
    assert "dit niet te laten liggen" in zichtbaar("3ezra", 2, 20)
    assert "verzuimen" not in vers("3ezra", 2, 20)["text2026"]
    assert len(reviewlijst("3ezra")) == 14


def test_judith_uitgekozen_mannen_en_de_naam_nabuchodonosor():
    assert "telde uitgekozen mannen" in zichtbaar("judith", 2, 7)
    lemma = next(
        item for item in json.loads((ROOT / "data" / "begrippenlijst-judith.json").read_text(encoding="utf-8"))
        if item["woord"] == "Nabuchodonosor"
    )
    assert "Griekse en Latijnse vorm" in lemma["uitleg"]
    assert "Nebukadnezar" in lemma["ook"]
    assert len(reviewlijst("judith")) == 6


def test_oude_verleden_tijd_op_t_is_weg():
    for boek, hoofdstuk, nummer, oud, nieuw in (
        ("4ezra", 3, 9, "deedt", "deed u na verloop van tijd"),
        ("4ezra", 3, 18, "verschriktet", "u verschrikte de wereld"),
        ("4ezra", 3, 23, "verwektet", "u verwekte voor uzelf een knecht"),
        ("4ezra", 5, 43, "Kondt", "Kon u niet maken"),
        ("4ezra", 6, 41, "schiept", "schiep U de lucht"),
        ("4ezra", 6, 46, "geboodt", "U gebood hun"),
        ("4ezra", 6, 53, "geboodt", "gebood U de aarde"),
        ("2samuel", 22, 40, "deedt", "U deed onder mij"),
        ("boekderwijsheid", 18, 5, "naamt", "nam u tot overtuiging"),
        ("3makkabeeen", 6, 5, "zondt", "maar U zond de vlam"),
        ("3meqabyan", 2, 18, "verleiddet", "verleidde u haar"),
        ("4baruch", 5, 20, "Waart", "Was u geen oude man"),
    ):
        tekst = zichtbaar(boek, hoofdstuk, nummer)
        assert nieuw in tekst, f"{boek} {hoofdstuk}:{nummer}"
        assert not re.search(rf"\b{oud}\b", tekst), f"{boek} {hoofdstuk}:{nummer}"


def test_ethiopische_boeken_krijgen_geen_woorddiff_tegen_een_lege_1888_tekst():
    assert not vers("3meqabyan", 2, 18).get("phraseDiff")
    assert not vers("4baruch", 5, 20).get("phraseDiff")


def test_datering_van_4ezra_noemt_de_latere_toevoegingen():
    datering = json.loads((ROOT / "data" / "book-dating.json").read_text(encoding="utf-8"))["4ezra"]
    assert "15–16" in datering["schrijftijd"]
    assert datering["schrijftijdKort"] == "± 100 n.Chr."


def test_reviewlijsten_zijn_volledig():
    for boek, aantal in (("3ezra", 14), ("4ezra", 11), ("judith", 6)):
        items = reviewlijst(boek)
        assert len(items) == aantal, boek
        assert {item["status"] for item in items} <= STATUSSEN, boek
        assert all(item["resultaat"] for item in items), boek
