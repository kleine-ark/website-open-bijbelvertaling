import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OPEN = ["2samuel", "3ezra", "4ezra", "tobit", "judith", "boekderwijsheid", "jezussirach",
        "estherapocrief", "2makkabeeen", "3makkabeeen", "ezechiel", "henoch", "jubileeen",
        "1meqabyan", "2meqabyan", "4baruch"]


def vers(boek, hoofdstuk, nummer):
    data = json.loads((ROOT / "data" / boek / f"{hoofdstuk}.json").read_text(encoding="utf-8"))
    return next(item for item in data["verses"] if item["number"] == nummer)


def zichtbaar(boek, hoofdstuk, nummer):
    html = vers(boek, hoofdstuk, nummer)["text2026_html"]
    return re.sub(r"<[^>]+>", "", re.sub(r"<sup[^>]*>.*?</sup>", "", html))


def alle_verzen(boek):
    for pad in sorted((ROOT / "data" / boek).glob("*.json"), key=lambda p: int(p.stem)):
        for item in json.loads(pad.read_text(encoding="utf-8"))["verses"]:
            yield int(pad.stem), item


def test_geen_wiens_wier_bij_geval_of_kinderen_ammons_in_de_open_boeken():
    for boek in OPEN:
        for hoofdstuk, item in alle_verzen(boek):
            gevonden = re.findall(r"\b[Ww]iens\b|\b[Ww]ier\b|\b[Bb]ij geval\b|kinderen Ammons",
                                  item["text2026"])
            assert not gevonden, f"{boek} {hoofdstuk}:{item['number']}: {gevonden}"


def test_de_definitieve_boeken_zijn_niet_aangeraakt():
    assert "bij geval" in zichtbaar("ruth", 2, 3)
    assert "bij geval" in zichtbaar("lukas", 10, 31)


def test_zinnen_lopen_na_de_vervanging():
    verwacht = [
        ("2samuel", 12, 24, "en zij baarde een zoon, die zij Salomo noemde"),
        ("2samuel", 17, 25, "van wie de naam Jethra was"),
        ("ezechiel", 9, 11, "die de inktkoker aan zijn middel had"),
        ("4ezra", 2, 18, "op hun raad heb Ik voor u geheiligd en bereid twaalf bomen"),
        ("jezussirach", 34, 26, "van wie zal de Heere de stem verhoren?"),
        ("henoch", 76, 5, "die de oostenwind heet"),
        ("1meqabyan", 17, 1, "Die het oordeel van hemel en aarde in Zijn hand heeft"),
        ("2samuel", 1, 1, "was teruggekeerd"),
        ("2samuel", 12, 23, "hij zal tot mij niet terugkeren"),
        ("2samuel", 20, 1, "daar toevallig een Belials man"),
        ("boekderwijsheid", 2, 2, "Want toevallig zijn wij geboren"),
        ("4baruch", 3, 1, "zij bleven daar, wachtende"),
        ("jezussirach", 18, 22, "op de juiste tijd"),
        ("2makkabeeen", 13, 26, "verantwoordde dat op gepaste wijze"),
        ("2samuel", 10, 1, "de koning van de kinderen van Ammon"),
        ("judith", 6, 1, "alle kinderen van Moab"),
        ("3makkabeeen", 7, 19, "De Verlosser van Israël"),
        ("2samuel", 6, 20, "zoals een van de ijdele mensen"),
        ("henoch", 20, 2, "Uriël, een van de heilige engelen"),
    ]
    for boek, hoofdstuk, nummer, fragment in verwacht:
        assert fragment in zichtbaar(boek, hoofdstuk, nummer), f"{boek} {hoofdstuk}:{nummer}"


def test_een_blijft_een_telwoord_waar_het_er_een_is():
    assert "niet één van hen" in zichtbaar("2samuel", 13, 30)
    assert "één van deze, en één van de andere zijde" in zichtbaar("ezechiel", 40, 49)
    assert "bekwaam toe ben" in zichtbaar("4ezra", 4, 44)


def test_principes_zijn_bijgewerkt():
    principes = {item["id"]: item for item in json.loads(
        (ROOT / "data" / "wijzigingsprincipes.json").read_text(encoding="utf-8"))["principes"]}
    assert principes["MR-SK-137"]["nieuw"] == "teruggekeerd"
    assert "2:2" in principes["MR-OPM-002"]["bereik"]["boekderwijsheid"]
    assert all(principes[pid].get("bereik") for pid in ("MR-OPM-001", "MR-OPM-002", "MR-OPM-003", "MR-OPM-004"))
    assert "zonder nadruk" in principes["V735"]["toelichting"]
