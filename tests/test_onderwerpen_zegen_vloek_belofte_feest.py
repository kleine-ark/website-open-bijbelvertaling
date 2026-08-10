"""Regressietests voor vier corpusbrede, handmatig afgebakende onderwerpen."""

import json
from pathlib import Path

import pytest

from scripts.build_onderwerpen_zegen_vloek_belofte_feest import build_onderwerpen


ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def built():
    return build_onderwerpen(ROOT, write=False)


def test_bouw_is_deterministisch_en_audit_omvat_het_hele_corpus():
    first = build_onderwerpen(ROOT, write=False)
    second = build_onderwerpen(ROOT, write=False)

    assert first == second
    assert first["report"]["boekenGescand"] == 88
    assert first["report"]["verzenGescand"] == 41132
    assert len(first["report"]["perBoek"]) == 88
    assert {tag["id"] for tag in first["tags"]} == {
        "zegeningen", "vervloekingen", "beloften", "bijbelse-feesten"
    }


def test_zegeningen_bevatten_de_priesterlijke_zegen_en_formele_zegeningen(built):
    tag = next(tag for tag in built["tags"] if tag["id"] == "zegeningen")
    by_ref = {item["ref"]: item for item in tag["verzen"]}

    assert {f"numeri 6:{verse}" for verse in range(22, 28)} <= set(by_ref)
    assert by_ref["numeri 6:22"]["passage"] == "numeri 6:22-27"
    assert by_ref["numeri 6:24"]["subcategorie"] == "priesterlijke-zegen"
    assert {
        "genesis 12:2", "genesis 25:11", "genesis 49:28", "mattheus 5:3",
        "markus 10:16", "lukas 24:50", "romeinen 12:14",
    } <= set(by_ref)


def test_vervloekingen_bevatten_uitgesproken_en_verbondsvloeken_geen_losse_vermelding(built):
    tag = next(tag for tag in built["tags"] if tag["id"] == "vervloekingen")
    refs = {item["ref"] for item in tag["verzen"]}

    assert {"genesis 3:14", "genesis 9:25", "deuteronomium 27:15", "galaten 3:10"} <= refs
    assert {f"deuteronomium 27:{verse}" for verse in range(15, 27)} <= refs
    assert {"psalmen 109:6", "psalmen 137:9", "markus 14:71"} <= refs
    assert "genesis 27:12" not in refs  # vrees voor een vloek, geen uitgesproken vloek
    assert "spreuken 26:2" not in refs  # onderwijs over een onverdiende vloek


def test_beloften_zijn_goddelijke_toezeggingen_en_geen_blinde_woordtreffers(built):
    tag = next(tag for tag in built["tags"] if tag["id"] == "beloften")
    refs = {item["ref"] for item in tag["verzen"]}

    assert {
        "genesis 3:15", "genesis 12:2", "2samuel 7:12", "jeremia 31:31",
        "johannes 3:16", "handelingen 2:39", "openbaring 21:5",
    } <= refs
    assert "handelingen 7:5" not in refs  # verwijst naar een belofte, maar is niet de toezegging zelf
    assert "hebreeen 11:13" not in refs


def test_bijbelse_feesten_omvatten_instelling_kalender_en_nieuwtestamentische_vieringen(built):
    tag = next(tag for tag in built["tags"] if tag["id"] == "bijbelse-feesten")
    refs = {item["ref"] for item in tag["verzen"]}

    assert {f"leviticus 23:{verse}" for verse in range(1, 45)} <= refs
    assert {"exodus 12:14", "numeri 29:1", "deuteronomium 16:13"} <= refs
    assert {"esther 9:21", "johannes 7:2", "johannes 10:22", "handelingen 2:1"} <= refs
    assert {
        "deuteronomium 31:10", "psalmen 81:4", "2kronieken 7:8",
        "johannes 12:12", "3ezra 1:1", "tobit 2:2",
    } <= refs


def test_alle_publicaties_bestaan_en_zijn_niet_als_menselijk_nagekeken_gemarkeerd(built):
    from scripts.build_corpus_naslag import load_corpus

    valid = {verse.ref for verse in load_corpus(ROOT, include_ethiopic=True)}
    for tag in built["tags"]:
        refs = [item["ref"] for item in tag["verzen"]]
        assert set(refs) <= valid
        assert len(refs) == len(set(refs))
        assert tag["reviewStatus"] == "agent-reviewed"
        assert tag["humanReviewed"] is False
        assert all(item["reviewStatus"] == "agent-reviewed" for item in tag["verzen"])
        assert all(item["humanReviewed"] is False for item in tag["verzen"])


def test_schrijvende_bouw_kan_zonder_dubbele_ids_in_tags_worden_geintegreerd(built):
    existing = json.loads((ROOT / "data" / "tags.json").read_text(encoding="utf-8"))["tags"]
    ids = {tag["id"] for tag in built["tags"]}
    merged = [tag for tag in existing if tag["id"] not in ids] + built["tags"]

    assert len({tag["id"] for tag in merged}) == len(merged)
    assert all(sum(tag["id"] == topic_id for tag in merged) == 1 for topic_id in ids)


def test_twijfelgevallen_blijven_buiten_de_publicatie(built):
    published = {item["ref"] for tag in built["tags"] for item in tag["verzen"]}
    queued = {item["ref"] for item in built["reviewqueue"]}

    assert published.isdisjoint(queued)
    assert all(item["reviewStatus"] == "agent-reviewed-needs-human-review" for item in built["reviewqueue"])
    assert all(item["humanReviewed"] is False for item in built["reviewqueue"])


def test_lexicale_audit_maakt_niet_gepubliceerde_corpustreffers_transparant(built):
    published = {item["ref"] for tag in built["tags"] for item in tag["verzen"]}
    candidates = built["auditCandidates"]

    assert len(candidates) > 500
    assert published.isdisjoint({item["ref"] for item in candidates})
    assert {item["onderwerp"] for item in candidates} == {
        "zegeningen", "vervloekingen", "beloften", "bijbelse-feesten"
    }
    assert all(item["status"] == "lexicale-treffer-niet-gepubliceerd" for item in candidates)
    assert built["report"]["lexicaleAudit"]["nietGepubliceerdeTreffers"] == len(candidates)
