from scripts.sync_google_reviewqueue_1koningen import bouw_queue, classificeer, referenties


def test_classificeer_houdt_tekst_en_citatie_uit_elkaar():
    assert classificeer("1 Koningen 10:15", "Kramers - marskramers")[1] == "verwerkt"
    assert classificeer("1 Koningen 12:10", "Citatie")[0] == "citatieopmaak"


def test_bouw_queue_slaat_dubbelen_en_inzenders_over():
    rijen = [
        {"Vers": "1 Koningen 17:12", "Suggestie": "Meels - meel", "Van": "iemand"},
        {"Vers": "1 Koningen 17:12", "Suggestie": "Meels - meel", "Van": "iemand anders"},
    ]
    items = bouw_queue(rijen)
    assert len(items) == 1
    assert items[0]["status"] == "verwerkt"
    assert "van" not in items[0]


def test_referenties_leest_meerdere_verzen_en_bereiken():
    assert referenties("1 Koningen 3:11,20") == [(3, 11), (3, 20)]
    assert referenties("1 Koningen 14:12-16") == [
        (14, 12), (14, 13), (14, 14), (14, 15), (14, 16)
    ]


def test_verwerkte_correctie_wordt_ook_bij_meervoudige_ref_herkend():
    assert classificeer("1 Koningen 3:11,20", "doden zoon")[1] == "verwerkt"
    assert classificeer("1 Koningen 10:20", "geen enkel koninkrijk")[1] == "verwerkt"


def test_bestaande_tags_en_eenheden_zijn_afgedekt():
    assert classificeer("1 Koningen 3:3", "tag dubbelhartigheid")[1] == "afgedekt"
    assert classificeer("1 Koningen 7:14", "Tag vakmanschap")[1] == "afgedekt"
    assert classificeer("1 Koningen 8:32", "Tag zaaien en oogsten")[1] == "afgedekt"
    assert classificeer("1 Koningen 10:16", "Unuts: 600 sikkels")[1] == "afgedekt"
