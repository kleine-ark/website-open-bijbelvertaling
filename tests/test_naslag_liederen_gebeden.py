"""Datamodel- en bouwtests voor genummerde liederen en gebeden."""

import json
from pathlib import Path

import pytest

from scripts.build_naslag_teksten import build_all, build_collection, expand_passage


ROOT = Path(__file__).resolve().parents[1]

LIED_IDS = [
    "lofzang-in-henoch",
    "lied-bij-de-schelfzee",
    "lied-van-mirjam",
    "lied-van-de-bron",
    "lied-van-mozes",
    "lied-van-debora-en-barak",
    "lofzang-van-hanna",
    "beurtzang-van-de-vrouwen",
    "davids-klaaglied",
    "loflied-bij-de-ark",
    "davids-lied-van-bevrijding",
    "laatste-woorden-van-david",
    "de-psalmen",
    "het-hooglied",
    "lied-van-de-wijngaard",
    "lied-van-de-sterke-stad",
    "loflied-van-tobit",
    "lofzang-van-hizkia",
    "gebed-van-habakuk",
    "gezang-in-de-vuuroven",
    "klaagliederen",
    "loflied-van-judith",
    "dankgebed-van-jezus-sirach",
    "lofzang-van-maria",
    "lofzang-van-zacharias",
    "engelenzang",
    "lofzang-van-simeon",
    "lofzang-bij-het-avondmaal",
    "paulus-en-silas",
    "het-nieuwe-lied",
    "gezang-van-mozes-en-het-lam",
]

GEBED_IDS = [
    "abrahams-voorbede-voor-sodom",
    "jakobs-gebed-voor-de-ontmoeting-met-ezau",
    "mozes-voorbeden-voor-israel",
    "het-gebed-van-mozes-psalm-90",
    "het-gebed-van-jabez",
    "simsons-laatste-gebed",
    "het-gebed-van-hanna",
    "davids-gebed-in-de-grot-psalm-142",
    "davids-gebed-om-bewaring-psalm-17",
    "davids-dankgebed-over-de-belofte",
    "davids-boetgebed-psalm-51",
    "davids-gebed-in-benauwdheid-psalm-86",
    "gebed-om-leven-naar-gods-woord-psalm-119",
    "davids-gebed-voor-salomo-psalm-72",
    "salomos-gebed-om-wijsheid",
    "salomos-tempelwijdingsgebed",
    "het-gebed-van-agur",
    "elia-op-de-karmel",
    "josafats-gebed",
    "jonas-gebed-uit-de-vis",
    "de-gebeden-van-tobit-en-sara",
    "het-gebed-van-judith",
    "hizkias-gebed-om-uitredding",
    "hizkias-gebed-om-genezing",
    "het-gebed-van-manasse",
    "habakuks-gebed",
    "het-gebed-van-azaria",
    "het-gebed-van-de-ballingen-baruch",
    "daniels-boetgebed",
    "gebed-van-de-verdrukte-psalm-102",
    "mordechais-gebed",
    "esthers-gebed",
    "ezras-boetgebed",
    "nehemias-gebed",
    "het-boetgebed-onder-nehemia",
    "gebed-uit-de-diepten-psalm-130",
    "het-onze-vader",
    "het-gebed-van-de-tollenaar",
    "het-hogepriesterlijk-gebed",
    "jezus-in-gethsemane",
    "het-gebed-van-de-gemeente",
    "het-gebed-van-stefanus",
    "paulus-eerste-gebed-voor-efeze",
    "paulus-tweede-gebed-voor-efeze",
    "paulus-gebed-voor-filippi",
]


def load_json(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


@pytest.fixture
def liederen():
    return load_json("data/naslag-liederen.json")


@pytest.fixture
def gebeden():
    return load_json("data/naslag-gebeden.json")


def test_reeksen_zijn_compleet_en_chronologisch(liederen, gebeden):
    assert liederen["nummerType"] == "Lied"
    assert gebeden["nummerType"] == "Gebed"
    assert [item["id"] for item in liederen["items"]] == LIED_IDS
    assert [item["id"] for item in gebeden["items"]] == GEBED_IDS


def test_lamech_en_de_gebedenintro_blijven_verwijderd(liederen, gebeden):
    assert all("lamech" not in item["id"] for item in liederen["items"])
    assert "Lamech" not in liederen.get("intro", "")
    assert "intro" not in gebeden


def test_psalmen_blijven_een_lied_met_150_hoofdstukken(liederen):
    psalmen = next(item for item in liederen["items"] if item["id"] == "de-psalmen")
    assert psalmen["tekstpassages"] == [
        {
            "boek": "psalmen",
            "vanHoofdstuk": 1,
            "totHoofdstuk": 150,
            "label": "Psalm 1–150",
        }
    ]


def test_negen_gebedspsalmen_hebben_hun_volledige_passage(gebeden):
    expected = {
        17: ("davids-gebed-om-bewaring-psalm-17", 1, 15),
        51: ("davids-boetgebed-psalm-51", 1, 21),
        72: ("davids-gebed-voor-salomo-psalm-72", 1, 20),
        86: ("davids-gebed-in-benauwdheid-psalm-86", 1, 17),
        90: ("het-gebed-van-mozes-psalm-90", 1, 17),
        102: ("gebed-van-de-verdrukte-psalm-102", 1, 29),
        119: ("gebed-om-leven-naar-gods-woord-psalm-119", 1, 176),
        130: ("gebed-uit-de-diepten-psalm-130", 1, 8),
        142: ("davids-gebed-in-de-grot-psalm-142", 1, 8),
    }
    by_id = {item["id"]: item for item in gebeden["items"]}

    for chapter, (item_id, first, last) in expected.items():
        assert by_id[item_id]["tekstpassages"] == [
            {
                "boek": "psalmen",
                "hoofdstuk": chapter,
                "van": first,
                "tot": last,
                "label": f"Psalm {chapter}:1–{last}",
            }
        ]


def test_paulus_is_opgesplitst_in_drie_gebeden(gebeden):
    ids = [item["id"] for item in gebeden["items"]]
    assert "paulus-gebeden-voor-de-gemeenten" not in ids
    assert ids[-3:] == [
        "paulus-eerste-gebed-voor-efeze",
        "paulus-tweede-gebed-voor-efeze",
        "paulus-gebed-voor-filippi",
    ]


@pytest.mark.parametrize("fixture_name", ["liederen", "gebeden"])
def test_ieder_item_heeft_unieke_inhoud_en_passagegrenzen(request, fixture_name):
    collection = request.getfixturevalue(fixture_name)
    ids = [item["id"] for item in collection["items"]]
    assert len(ids) == len(set(ids))

    for item in collection["items"]:
        assert item["id"].strip()
        assert item["naam"].strip()
        assert item["beschrijving"].strip()
        assert item["verzen"]
        assert item["tekstpassages"]
        for passage in item["tekstpassages"]:
            assert passage["boek"].strip()
            assert passage["label"].strip()
            if "hoofdstuk" in passage:
                assert set(passage) == {"boek", "hoofdstuk", "van", "tot", "label"}
                assert passage["van"] <= passage["tot"]
            else:
                assert set(passage) == {
                    "boek",
                    "vanHoofdstuk",
                    "totHoofdstuk",
                    "label",
                }
                assert passage["vanHoofdstuk"] <= passage["totHoofdstuk"]


def test_niet_overgeleverde_liedwoorden_worden_niet_gereconstrueerd(liederen):
    by_id = {item["id"]: item for item in liederen["items"]}
    for item_id in ("lofzang-bij-het-avondmaal", "paulus-en-silas"):
        assert by_id[item_id]["tekstmelding"].strip()


@pytest.fixture(scope="module")
def built():
    return build_all(ROOT, write=False)


def test_builder_leidt_aaneengesloten_nummers_af(built):
    assert [bundle["nummer"] for bundle in built["liederen"].values()] == list(
        range(1, 32)
    )
    assert [bundle["nummer"] for bundle in built["gebeden"].values()] == list(
        range(1, 46)
    )
    assert all(bundle["nummerType"] == "Lied" for bundle in built["liederen"].values())
    assert all(bundle["nummerType"] == "Gebed" for bundle in built["gebeden"].values())


def test_gebouwd_vers_is_exact_text2026(built):
    verse = built["gebeden"]["abrahams-voorbede-voor-sodom"]["passages"][0][
        "sections"
    ][0]["verzen"][0]
    source = load_json("data/genesis/18.json")["verses"]
    expected = next(item["text2026"] for item in source if item["number"] == 23)

    assert verse == {"nummer": 23, "tekst": expected}


def test_psalmenbundel_heeft_precies_150_secties(built):
    psalmen = built["liederen"]["de-psalmen"]
    sections = psalmen["passages"][0]["sections"]

    assert len(sections) == 150
    assert sections[0]["hoofdstuk"] == 1
    assert sections[-1]["hoofdstuk"] == 150


def test_samengestelde_passages_behouden_de_opgegeven_volgorde(built):
    mozes = built["gebeden"]["mozes-voorbeden-voor-israel"]
    labels = [passage["label"] for passage in mozes["passages"]]

    assert labels == ["Exodus 32:11–14", "Numeri 14:13–19"]


def test_niet_overgeleverde_woorden_blijven_een_melding(built):
    avondmaal = built["liederen"]["lofzang-bij-het-avondmaal"]

    assert avondmaal["tekstmelding"].startswith("De woorden")
    assert len(avondmaal["passages"]) == 2


def write_test_chapter(root, verses):
    chapter_dir = root / "data" / "testboek"
    chapter_dir.mkdir(parents=True)
    (chapter_dir / "1.json").write_text(
        json.dumps({"verses": verses}, ensure_ascii=False), encoding="utf-8"
    )


def test_builder_weigert_lege_text2026(tmp_path):
    write_test_chapter(tmp_path, [{"number": 1, "text2026": ""}])

    with pytest.raises(ValueError, match="lege text2026.*testboek 1:1"):
        expand_passage(
            tmp_path,
            {"boek": "testboek", "hoofdstuk": 1, "van": 1, "tot": 1, "label": "Test"},
        )


def test_builder_weigert_ontbrekend_vers(tmp_path):
    write_test_chapter(tmp_path, [{"number": 1, "text2026": "Eerste vers"}])

    with pytest.raises(ValueError, match="ontbrekend vers.*testboek 1:2"):
        expand_passage(
            tmp_path,
            {"boek": "testboek", "hoofdstuk": 1, "van": 1, "tot": 2, "label": "Test"},
        )


def test_builder_weigert_verkeerd_aantal_items(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "bron.json").write_text(
        json.dumps({"nummerType": "Lied", "items": []}), encoding="utf-8"
    )

    with pytest.raises(ValueError, match="31 items"):
        build_collection(tmp_path, "liederen", "bron.json")
