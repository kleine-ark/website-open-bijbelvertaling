import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPAN = re.compile(r'<span class="(?:direct-speech|god-speaks)"><i>(.*?)</i></span>')


def vers(boek, hoofdstuk, nummer):
    data = json.loads((ROOT / "data" / boek / f"{hoofdstuk}.json").read_text(encoding="utf-8"))
    return next(item for item in data["verses"] if item["number"] == nummer)


def html(hoofdstuk, nummer):
    return re.sub(r"<sup[^>]*>.*?</sup>", "", vers("ezechiel", hoofdstuk, nummer)["text2026_html"])


def buiten_citaat(hoofdstuk, nummer):
    """De tekst die niet in een citaat staat."""
    return re.sub(r"<[^>]+>", "", SPAN.sub("", html(hoofdstuk, nummer)))


def principes(boek, hoofdstuk, nummer):
    return {item.get("principe") for item in vers(boek, hoofdstuk, nummer).get("phraseDiff", [])}


def test_de_keur_is_ook_op_het_scherm_het_beste_geworden():
    for hoofdstuk, nummer, fragment in ((24, 4, "met het beste van de beenderen"),
                                        (24, 5, "Neem het beste van de kudde"),
                                        (23, 7, "de besten van de kinderen van Assur")):
        zichtbaar = re.sub(r"<[^>]+>", "", html(hoofdstuk, nummer))
        assert fragment in zichtbaar, f"Ezechiël {hoofdstuk}:{nummer}"
        assert "keur" not in zichtbaar, f"Ezechiël {hoofdstuk}:{nummer}"


def test_mat_is_meette_in_de_boeken_die_nog_niet_definitief_waren():
    principe = next(
        item for item in json.loads((ROOT / "data" / "wijzigingsprincipes.json").read_text(encoding="utf-8"))["principes"]
        if item["id"] == "V1641"
    )
    assert principe["nieuw"] == "meette"
    assert "41:13" in principe["bereik"]["ezechiel"]
    assert principe["bereik"]["2samuel"] == ["8:2"]

    geteld = 0
    for boek, plaatsen in principe["bereik"].items():
        for plaats in plaatsen:
            hoofdstuk, nummer = map(int, plaats.split(":"))
            tekst = vers(boek, hoofdstuk, nummer)["text2026"]
            assert not re.search(r"\bmat\b", tekst), f"{boek} {plaats}"
            geteld += len(re.findall(r"\bmeette\b", tekst))
    assert geteld == 35
    assert "V1641" in principes("ezechiel", 40, 19)
    assert "V1641" in principes("ezechiel", 42, 16)


def test_gods_woorden_zijn_gemarkeerd_en_de_vertelling_niet():
    assert '<span class="god-speaks"><i>Mensenkind, eet' in html(3, 1)
    assert html(3, 25).startswith('<span class="god-speaks">')
    assert "en ik hief mijn ogen op" in buiten_citaat(8, 5)
    assert "En ik groef in die wand" in buiten_citaat(8, 8)
    for nummer in (9, 13, 15):
        assert "god-speaks" in html(8, nummer)
    for nummer in (1, 4, 5):
        assert "god-speaks" in html(9, nummer)
    assert "En zij gingen heen uit" in buiten_citaat(9, 7)
    assert "en hij ging in voor mijn ogen" in buiten_citaat(10, 2)
    assert "dat hij inging" in buiten_citaat(10, 6)
    assert "god-speaks" in html(23, 36)
    assert "god-speaks" in html(43, 18)
    assert "god-speaks" in html(44, 2) and "god-speaks" in html(44, 3)


def test_aangehaalde_woorden_staan_binnen_gods_rede():
    elf_drie = html(11, 3)
    assert elf_drie.startswith('<span class="god-speaks"><i>Die zeggen: <span class="direct-speech">')
    assert 'zeg daartoe: <span class="direct-speech"><i>U dorre beenderen!' in html(37, 4)
    assert 'zeg tot de geest: <span class="direct-speech"><i>Zo zegt Adonai JAHWEH' in html(37, 9)


def test_reviewlijst_beslist_over_elke_melding():
    lijst = json.loads((ROOT / "data" / "google-opmerkingen-ezechiel-reviewqueue.json").read_text(encoding="utf-8"))
    items = lijst["items"]
    assert len(items) == 33
    assert {item["status"] for item in items} <= {"verwerkt", "afgedekt", "gepland", "open", "vervallen"}
    assert all(item["resultaat"] for item in items)
