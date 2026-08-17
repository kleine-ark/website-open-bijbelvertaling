import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def vers(hoofdstuk, nummer):
    data = json.loads((ROOT / "data" / "1kronieken" / f"{hoofdstuk}.json").read_text(encoding="utf-8"))
    return next(item for item in data["verses"] if item["number"] == nummer)


def test_tekstcorrecties_zijn_als_reviewprincipes_verwerkt():
    matrix = [
        (1, 43, "voordat", "eer"), (4, 23, "wonend", "wonende"),
        (4, 38, "waren vorsten", "zijnde vorsten"), (9, 22, "uitgekozen", "uitgelezen"),
        (12, 17, "één met u zijn", "tegelijk over u zijn"),
        (12, 30, "strijdbare helden", "kloeke helden"),
        (12, 30, "hun vaders", "hun vaderen"), (13, 2, "broeders", "broers"),
        (14, 10, "vroeg David", "vraagde David"), (15, 13, "straf gegeven", "scheur gedaan"),
        (16, 3, "een rond brood", "een bol broods"), (16, 22, "Raak", "Tas"),
        (18, 8, "veel koper", "veel kopers"),
        (20, 1, "aanbreken van het nieuwe jaar", "wederkomst van het jaar"),
        (20, 2, "veel roof", "veel roofs"), (21, 8, "dwaas", "zottelijk"),
        (21, 20, "verborgen zich", "verstaken zich"),
        (21, 28, "In die tijd", "Ter zelfder tijd"),
        (28, 11, "een ontwerp", "een voorbeeld"), (28, 12, "een ontwerp", "een voorbeeld"),
        (29, 28, "goede ouderdom", "goeden ouderdom"),
    ]
    for hoofdstuk, nummer, nieuw, oud in matrix:
        item = vers(hoofdstuk, nummer)
        assert nieuw in item["text2026"]
        assert not re.search(rf"(?<!\w){re.escape(oud)}(?!\w)", item["text2026"])
        assert any((diff.get("principe") or "").startswith("MR-1KR-") for diff in item.get("phraseDiff", []))


def test_citaten_begrenzen_uitspraak_en_vertelling():
    assert "direct-speech" not in vers(10, 5)["text2026_html"]
    assert '<span class="direct-speech"><i>Zie, wij zijn' in vers(11, 1)["text2026_html"]
    assert "David dan nog won" not in re.findall(r'<span class="direct-speech"><i>(.*?)</i></span>', vers(11, 5)["text2026_html"])[0]
    assert "En hij wilde het niet drinken" not in re.findall(r'<span class="direct-speech"><i>(.*?)</i></span>', vers(11, 19)["text2026_html"])[0]
    assert "Toen nam David hen aan" not in re.findall(r'<span class="direct-speech"><i>(.*?)</i></span>', vers(12, 18)["text2026_html"])[0]
    assert "direct-speech" not in vers(13, 4)["text2026_html"]
    assert "direct-speech" not in vers(14, 12)["text2026_html"]
    assert "direct-speech" not in vers(15, 3)["text2026_html"]
    assert "direct-speech" in vers(15, 12)["text2026_html"]
    assert "direct-speech" not in vers(15, 16)["text2026_html"]
    assert "direct-speech" in vers(16, 8)["text2026_html"]
    assert "En al het volk zei" not in re.findall(r'<span class="direct-speech"><i>(.*?)</i></span>', vers(16, 36)["text2026_html"])[0]
    assert "direct-speech" not in vers(17, 3)["text2026_html"]
    assert "Daarom zond David" not in re.findall(r'<span class="direct-speech"><i>(.*?)</i></span>', vers(19, 2)["text2026_html"])[0]
    assert "direct-speech" not in vers(21, 4)["text2026_html"]
    assert "direct-speech" not in vers(21, 20)["text2026_html"]
    assert "direct-speech" not in vers(22, 2)["text2026_html"]
    assert "god-speaks" in vers(22, 8)["text2026_html"]
    assert "direct-speech" in vers(22, 11)["text2026_html"]
    assert "god-speaks" not in vers(22, 11)["text2026_html"]
    assert "Toen loofde" not in re.findall(r'<span class="direct-speech"><i>(.*?)</i></span>', vers(29, 20)["text2026_html"])[0]


def test_reuzenverwijzing_dekt_het_hele_gedeelte():
    begrippen = json.loads((ROOT / "data" / "begrippenlijst-1kronieken.json").read_text(encoding="utf-8"))
    reuzen = next(item for item in begrippen if item["woord"] == "reuzen")
    assert reuzen["ref"] == "1 Kron 20:4-8"


def test_als_algemeen_opgegeven_principes_zijn_corpusbreed_geregistreerd():
    principes = json.loads((ROOT / "data" / "wijzigingsprincipes.json").read_text(encoding="utf-8"))["principes"]
    verwacht = {
        ("kloeke helden", "strijdbare helden"),
        ("vaderen", "vaders"),
        ("zottelijk", "dwaas"),
        ("verstaken zich", "verborgen zich"),
        ("Ter zelfder tijd", "In die tijd"),
    }
    gevonden = {(item.get("oud"), item.get("nieuw")): item for item in principes}
    for paar in verwacht:
        principe = gevonden[paar]
        assert principe["regex"]
        assert "bereik" not in principe
