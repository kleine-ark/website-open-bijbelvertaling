import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def hoofdstukken(boek):
    for pad in sorted((ROOT / "data" / boek).glob("*.json"), key=lambda p: int(p.stem)):
        yield int(pad.stem), json.loads(pad.read_text(encoding="utf-8"))["verses"]


def vers(boek, hoofdstuk, nummer):
    data = json.loads((ROOT / "data" / boek / f"{hoofdstuk}.json").read_text(encoding="utf-8"))
    return next(item for item in data["verses"] if item["number"] == nummer)


def zichtbaar(boek, hoofdstuk, nummer):
    html = vers(boek, hoofdstuk, nummer)["text2026_html"]
    return re.sub(r"<[^>]+>", "", re.sub(r"<sup[^>]*>.*?</sup>", "", html))


def test_geen_oude_naamvallen_en_woorden_meer_in_jubileeen():
    for hoofdstuk, verzen in hoofdstukken("jubileeen"):
        for item in verzen:
            for veld in ("text2026", "text2026_html"):
                tekst = re.sub(r"<[^>]+>", " ", item[veld])
                gevonden = re.findall(r"\bdes\b|\bneder\w*|\bGods\b|\bwiens\b|\bwakers\b", tekst)
                assert not gevonden, f"Jubileeën {hoofdstuk}:{item['number']} {veld}: {gevonden}"


def test_wachters_ook_in_henoch_zonder_woorddiff():
    for hoofdstuk, verzen in hoofdstukken("henoch"):
        for item in verzen:
            assert "wakers" not in item["text2026"], f"Henoch {hoofdstuk}:{item['number']}"
            assert not item.get("phraseDiff"), f"Henoch {hoofdstuk}:{item['number']}"
    assert "de wachters zullen sidderen" in zichtbaar("henoch", 1, 5)


def test_gerichte_verbeteringen():
    assert "de engel van het aangezicht" in zichtbaar("jubileeen", 1, 27)
    assert "zij stonden 's nachts op" in zichtbaar("jubileeen", 12, 13)
    assert "van de toorn en van de gramschap" in zichtbaar("jubileeen", 36, 10)
    assert "dat u godvrezend bent" in zichtbaar("jubileeen", 18, 11)
    assert "waarvan de naam Lubar is" in zichtbaar("jubileeen", 7, 1)
    assert "het beviel hem niet" in zichtbaar("jubileeen", 7, 13)
    assert "dertien hele bakstenen" in zichtbaar("jubileeen", 10, 21)


def test_opdracht_van_de_engel_in_2_1_is_een_citaat():
    html = vers("jubileeen", 2, 1)["text2026_html"]
    assert 'zeggende: <span class="angel-speaks"><i>Schrijf heel het verhaal' in html


def test_voetnoten_bij_de_ontbrekende_tekst_en_de_bakstenen():
    for hoofdstuk, nummer, kern in ((3, 17, "editie van Charles"), (10, 21, "baksteen")):
        item = vers("jubileeen", hoofdstuk, nummer)
        assert any(kern in noot["text2026"] for noot in item["marginNotes"])
        assert 'class="note-marker"' in item["text2026_html"]


def test_woordenlijst_en_reviewlijst():
    woordenlijst = (ROOT / ".claude" / "skills" / "geez-vertalen" / "woordenlijst.md")
    if woordenlijst.exists():
        assert "| ትጉሃን | de wachters |" in woordenlijst.read_text(encoding="utf-8")
    lijst = json.loads((ROOT / "data" / "google-opmerkingen-jubileeen-reviewqueue.json").read_text(encoding="utf-8"))
    assert len(lijst["items"]) == 17
    assert {item["status"] for item in lijst["items"]} <= {"verwerkt", "afgedekt", "gepland", "open", "vervallen"}
