import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPAN = re.compile(r'<span class="(?:direct-speech|god-speaks)"><i>(.*?)</i></span>')


def vers(hoofdstuk, nummer):
    data = json.loads((ROOT / "data" / "2samuel" / f"{hoofdstuk}.json").read_text(encoding="utf-8"))
    return next(item for item in data["verses"] if item["number"] == nummer)


def zonder_noten(html):
    return re.sub(r"<sup[^>]*>.*?</sup>", "", html)


def citaten(hoofdstuk, nummer):
    """De tekst binnen de spans, zonder de binnenste spans er apart uit te halen."""
    html = zonder_noten(vers(hoofdstuk, nummer)["text2026_html"])
    return [re.sub(r"<[^>]+>", "", deel) for deel in SPAN.findall(html)]


def principes(hoofdstuk, nummer):
    return {item.get("principe") for item in vers(hoofdstuk, nummer).get("phraseDiff", [])}


def test_woordkeus_is_verwerkt_en_aan_een_principe_gekoppeld():
    matrix = [
        (1, 9, "deze benauwdheid", "maliënkolder", "MR-2SA-001"),
        (1, 10, "de armband, die", "het armband", "MR-SK-009"),
        (3, 29, "nooit iemand ontbreken die een vloed heeft", "hebbe", "V779"),
        (4, 6, "alsof zij tarwe kwamen halen", "alsof zij tarwe halen", "MR-SK-007"),
        (12, 4, "de reizende man", "reizenden", "N1"),
        (14, 30, "staken die akker aan met vuur", "stuk akkers", "MR-SK-065"),
        (18, 27, "als die van Ahimaäz", "als de loop van", "MR-SK-026"),
        (19, 18, "Als men nu de doorwaadbare plaats overstak", "pont", "MR-2SA-002"),
        (22, 5, "beken van Belial", "Belials", "V448"),
        (22, 19, "mijn ongeluk; maar JAHWEH was mij een Steun.", "Steunsel", "MR-2SA-003"),
        (22, 19, "mijn ongeluk;", "ongeval", "V213"),
        (22, 21, "de reinheid van mijn handen", "reinigheid", "N7"),
        (22, 25, "naar mijn reinheid,", "reinigheid", "MR-2SA-004"),
        (23, 7, "verbrand worden ter plekke", "op die plaats", "MR-SK-101"),
    ]
    for hoofdstuk, nummer, nieuw, oud, principe in matrix:
        item = vers(hoofdstuk, nummer)
        assert nieuw in item["text2026"], f"2 Samuël {hoofdstuk}:{nummer}"
        assert oud not in item["text2026"], f"2 Samuël {hoofdstuk}:{nummer}"
        assert principe in principes(hoofdstuk, nummer), f"2 Samuël {hoofdstuk}:{nummer}"


def test_nieuwe_reviewprincipes_hebben_een_bereik_van_hun_eigen_vers():
    principes_data = json.loads((ROOT / "data" / "wijzigingsprincipes.json").read_text(encoding="utf-8"))
    per_id = {item["id"]: item for item in principes_data["principes"]}
    assert per_id["MR-2SA-001"]["bereik"] == {"2samuel": ["1:9"]}
    assert per_id["MR-2SA-002"]["bereik"] == {"2samuel": ["19:18"]}
    assert per_id["MR-2SA-003"]["bereik"] == {"2samuel": ["22:19"]}
    assert per_id["MR-2SA-004"]["bereik"] == {"2samuel": ["22:25"]}
    assert per_id["MR-SK-101"]["nieuw"] == "ter plekke"


def test_aankondiging_en_vertelling_staan_buiten_het_citaat():
    assert citaten(1, 5) == ["Hoe weet u, dat Saul dood is, en zijn zoon Jonathan?"]
    assert citaten(3, 16) == ["Ga weg, keer weer."]
    assert "de koning David ging achter de baar" not in " ".join(citaten(3, 31))
    assert "Toen huilde het hele volk" not in " ".join(citaten(3, 34))
    assert "dat wil zeggen" not in " ".join(citaten(5, 6))
    assert citaten(5, 8)[0].startswith("Al wie de Jebusieten slaat")
    assert "daarom zegt men" not in " ".join(citaten(5, 8))
    assert "maar hij wilde naar haar niet horen" not in " ".join(citaten(13, 16))
    assert "Absaloms knechten staken" not in " ".join(citaten(14, 30))
    assert "Als hij dan zei" not in " ".join(citaten(15, 2))
    assert citaten(17, 14) == ["De raad van Husai, de Archiet, is beter dan Achitofels raad."]
    html = vers(24, 16)["text2026_html"]
    assert 'maakte: <span class="god-speaks"><i>Het is genoeg' in html


def test_voortgezette_redes_zijn_gemarkeerd():
    for hoofdstuk, nummer in ((2, 7), (3, 9), (3, 10), (3, 29), (3, 39), (11, 20),
                              (11, 21), (12, 23), (19, 12), (19, 13), (23, 6), (23, 7)):
        assert "direct-speech" in vers(hoofdstuk, nummer)["text2026_html"], f"2 Samuël {hoofdstuk}:{nummer}"
    assert "god-speaks" in vers(5, 23)["text2026_html"]


def test_een_tweede_spreker_staat_binnen_het_citaat():
    for hoofdstuk, nummer, binnen in (
        (11, 20, '<span class="direct-speech"><i>Waarom bent u zo na'),
        (16, 3, '<span class="direct-speech"><i>Vandaag zal mij het huis'),
        (19, 13, '<span class="direct-speech"><i>Bent u niet mijn'),
    ):
        html = zonder_noten(vers(hoofdstuk, nummer)["text2026_html"])
        assert binnen in html, f"2 Samuël {hoofdstuk}:{nummer}"
    html = zonder_noten(vers(3, 12)["text2026_html"])
    assert "Van wie is het land?</i></span> zeggende verder:" in html
    assert html.count("<span") == 2 and "</i></span></i></span>" not in html


def test_gevraagde_tags_zijn_gekoppeld():
    tags = {item["id"]: item for item in json.loads((ROOT / "data" / "tags.json").read_text(encoding="utf-8"))["tags"]}
    verwacht = {
        "lhbtq": ["2samuel 1:26"],
        "verloren-bijbelse-bronnen": ["2samuel 1:18"],
        "liefde-man-vrouw": ["2samuel 3:16"],
        "ziekte-van-jahweh": ["2samuel 12:15"],
        "vervloekingen": ["2samuel 21:1", "2samuel 21:3"],
        "jezus-in-het-ot": ["2samuel 23:3", "2samuel 23:4"],
        "manipulatie": [f"2samuel 15:{n}" for n in range(1, 7)],
        "vaderliefde": ["2samuel 18:33", "2samuel 19:4"],
        "opdracht-tegen-geweten": ["2samuel 24:3", "2samuel 24:4"],
    }
    for tag, refs in verwacht.items():
        gekoppeld = {item["ref"] for item in tags[tag]["verzen"]}
        assert set(refs) <= gekoppeld, tag


def test_reviewlijst_beslist_over_elke_opmerking():
    lijst = json.loads((ROOT / "data" / "google-opmerkingen-2samuel-reviewqueue.json").read_text(encoding="utf-8"))
    items = lijst["items"]
    assert len(items) == 100
    assert {item["status"] for item in items} <= {"verwerkt", "afgedekt", "gepland", "open", "vervallen"}
    for item in items:
        assert item["resultaat"] and not re.fullmatch(r"[A-Z0-9_]+", item["resultaat"]), item["ref"]
