"""Datamodel- en bouwtests voor genummerde liederen en gebeden."""

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from scripts.build_gebeden_catalogus import BOOK_ORDER
from scripts.build_naslag_teksten import build_all, build_collection, expand_passage


ROOT = Path(__file__).resolve().parents[1]

GEBEDSPSALMEN = [
    3, 4, 5, 6, 7, 9, 10, 12, 13, 16, 17, 19, 20, 22, 25, 26, 27, 28,
    30, 31, 33, 35, 36, 38, 39, 40, 41, 42, 43, 44, 51, 54, 55, 56, 57,
    58, 59, 60, 61, 63, 64, 67, 69, 70, 71, 72, 74, 77, 79, 80, 82, 83,
    84, 85, 86, 88, 89, 90, 94, 102, 106, 108, 109, 115, 116, 118, 119,
    120, 122, 123, 125, 126, 129, 130, 132, 137, 138, 139, 140, 141, 142,
    143, 144,
]

MOZES_GEBEDEN = [
    "mozes-klacht-over-farao",
    "mozes-gebed-bij-refidim",
    "mozes-voorbede-na-het-gouden-kalf",
    "mozes-tweede-voorbede-na-het-gouden-kalf",
    "mozes-gebed-om-gods-tegenwoordigheid",
    "mozes-gebed-om-gods-heerlijkheid",
    "mozes-voorbede-na-de-verbondsvernieuwing",
    "mozes-gebeden-bij-het-optrekken-en-rusten-van-de-ark",
    "mozes-klacht-over-de-last-van-het-volk",
    "mozes-gebed-voor-mirjam",
    "mozes-voorbede-na-de-verspieders",
    "mozes-en-aaron-voor-de-gemeente",
    "mozes-gebed-om-een-opvolger",
    "mozes-gebed-om-kanaan-binnen-te-gaan",
]

LIED_IDS = [
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
] + [f"psalm-{number}" for number in range(1, 151)] + [
    "het-hooglied",
    "lied-van-de-wijngaard",
    "lied-van-de-sterke-stad",
    "lofzang-van-hizkia",
    "gebed-van-habakuk",
] + [f"klaaglied-{number}" for number in range(1, 6)] + [
    "lofzang-van-maria",
    "lofzang-van-zacharias",
    "engelenzang",
    "lofzang-van-simeon",
    "het-nieuwe-lied",
    "gezang-van-mozes-en-het-lam",
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
    assert len(gebeden["items"]) == 132

    positie = {boek: index for index, boek in enumerate(BOOK_ORDER)}
    sleutels = []
    for item in gebeden["items"]:
        passage = item["tekstpassages"][0]
        sleutels.append((
            positie[passage["boek"]],
            passage.get("hoofdstuk", passage.get("vanHoofdstuk", 0)),
            passage.get("van", 0),
        ))
    assert sleutels == sorted(sleutels)


def test_lamech_en_de_gebedenintro_blijven_verwijderd(liederen, gebeden):
    assert all("lamech" not in item["id"] for item in liederen["items"])
    assert "Lamech" not in liederen.get("intro", "")
    assert "intro" not in gebeden


def test_psalmen_en_klaagliederen_zijn_afzonderlijke_liederen(liederen):
    by_id = {item["id"]: item for item in liederen["items"]}

    assert [item_id for item_id in by_id if item_id.startswith("psalm-")] == [
        f"psalm-{number}" for number in range(1, 151)
    ]
    assert [item_id for item_id in by_id if item_id.startswith("klaaglied-")] == [
        f"klaaglied-{number}" for number in range(1, 6)
    ]
    assert by_id["psalm-1"]["tekstpassages"] == [
        {
            "boek": "psalmen",
            "hoofdstuk": 1,
            "van": 1,
            "tot": 6,
            "label": "Psalm 1",
        }
    ]
    assert by_id["klaaglied-1"]["tekstpassages"] == [
        {
            "boek": "klaagliederen",
            "hoofdstuk": 1,
            "van": 1,
            "tot": 22,
            "label": "Klaagliederen 1:1–22",
        }
    ]


def test_liednummering_heeft_de_afgesproken_grenspunten(liederen):
    nummers = {
        item["id"]: number
        for number, item in enumerate(liederen["items"], start=1)
    }

    assert nummers["lied-bij-de-schelfzee"] == 1
    assert nummers["psalm-1"] == 12
    assert nummers["psalm-150"] == 161
    assert nummers["klaaglied-1"] == 167
    assert nummers["klaaglied-5"] == 171
    assert nummers["het-nieuwe-lied"] == 176
    assert nummers["gezang-van-mozes-en-het-lam"] == 177


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


def test_alle_gebedspsalmen_staan_afzonderlijk_en_op_psalmnummer(gebeden):
    psalm_items = [
        item for item in gebeden["items"]
        if item["tekstpassages"][0]["boek"] == "psalmen"
    ]

    assert [item["tekstpassages"][0]["hoofdstuk"] for item in psalm_items] == GEBEDSPSALMEN
    assert all(len(item["tekstpassages"]) == 1 for item in psalm_items)


def test_ieder_gebed_van_mozes_is_een_afzonderlijk_item(gebeden):
    ids = [item["id"] for item in gebeden["items"]]

    assert "mozes-voorbeden-voor-israel" not in ids
    assert [item_id for item_id in ids if item_id in MOZES_GEBEDEN] == MOZES_GEBEDEN


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


def test_apocriefe_en_woordloze_liedvermeldingen_zijn_verwijderd(liederen):
    ids = {item["id"] for item in liederen["items"]}
    uitgesloten = {
        "lofzang-in-henoch",
        "loflied-van-tobit",
        "gezang-in-de-vuuroven",
        "loflied-van-judith",
        "dankgebed-van-jezus-sirach",
        "lofzang-bij-het-avondmaal",
        "paulus-en-silas",
        "de-psalmen",
        "klaagliederen",
    }

    assert ids.isdisjoint(uitgesloten)


@pytest.fixture(scope="module")
def built():
    return build_all(ROOT, write=False)


def test_builder_leidt_aaneengesloten_nummers_af(built):
    assert [bundle["nummer"] for bundle in built["liederen"].values()] == list(
        range(1, 178)
    )
    assert [bundle["nummer"] for bundle in built["gebeden"].values()] == list(
        range(1, 133)
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


def test_iedere_psalmbundel_heeft_precies_een_eigen_hoofdstuk(built):
    psalm_ids = [f"psalm-{number}" for number in range(1, 151)]

    assert all(item_id in built["liederen"] for item_id in psalm_ids)
    assert built["liederen"]["psalm-1"]["passages"][0]["sections"][0][
        "hoofdstuk"
    ] == 1
    assert built["liederen"]["psalm-150"]["passages"][0]["sections"][0][
        "hoofdstuk"
    ] == 150
    assert all(
        len(built["liederen"][item_id]["passages"][0]["sections"]) == 1
        for item_id in psalm_ids
    )


def test_samengestelde_passages_behouden_de_opgegeven_volgorde(built):
    mozes = built["gebeden"]["mozes-voorbede-na-het-gouden-kalf"]
    labels = [passage["label"] for passage in mozes["passages"]]

    assert labels == ["Exodus 32:11–14", "Deuteronomium 9:26–29"]


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

    with pytest.raises(ValueError, match="177 items"):
        build_collection(tmp_path, "liederen", "bron.json")


def test_geschreven_bundels_zijn_volledig_en_vers(built):
    for kind, bundles in built.items():
        target = ROOT / "data" / "naslag-teksten" / kind
        assert {path.stem for path in target.glob("*.json")} == set(bundles)
        for item_id, expected in bundles.items():
            actual = json.loads((target / f"{item_id}.json").read_text(encoding="utf-8"))
            assert actual == expected


def copy_builder_inputs(target_root):
    (target_root / "scripts").mkdir(parents=True)
    (target_root / "desktop").mkdir()
    (target_root / "data").mkdir()
    shutil.copy2(ROOT / "scripts/build_naslag_teksten.py", target_root / "scripts")
    shutil.copy2(ROOT / "desktop/build-dist.mjs", target_root / "desktop")

    for source_name in ("naslag-liederen.json", "naslag-gebeden.json"):
        source_path = ROOT / "data" / source_name
        shutil.copy2(source_path, target_root / "data")
        source = json.loads(source_path.read_text(encoding="utf-8"))
        for item in source["items"]:
            for passage in item["tekstpassages"]:
                if "hoofdstuk" in passage:
                    chapters = [passage["hoofdstuk"]]
                else:
                    chapters = range(
                        passage["vanHoofdstuk"], passage["totHoofdstuk"] + 1
                    )
                book_dir = target_root / "data" / passage["boek"]
                book_dir.mkdir(exist_ok=True)
                for chapter in chapters:
                    destination = book_dir / f"{chapter}.json"
                    if not destination.exists():
                        shutil.copy2(
                            ROOT / "data" / passage["boek"] / f"{chapter}.json",
                            destination,
                        )


def test_desktopbouw_genereert_bundels_voordat_data_wordt_gekopieerd(tmp_path):
    copy_builder_inputs(tmp_path)

    result = subprocess.run(
        ["node", "desktop/build-dist.mjs"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert (
        tmp_path
        / "desktop/dist/data/naslag-teksten/liederen/lied-bij-de-schelfzee.json"
    ).exists()
    assert (
        tmp_path
        / "desktop/dist/data/naslag-teksten/gebeden/paulus-gebed-voor-filippi.json"
    ).exists()
