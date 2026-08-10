"""Regressietests voor het onderwerp Demonen en duivelen."""

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
MANIFEST = DATA / "onderwerp-demonen-manifest.json"
MENTIONS = DATA / "onderwerp-demonen-vermeldingen.json"
REVIEW = DATA / "onderwerp-demonen-review.json"
SCRIPT = ROOT / "scripts" / "build_onderwerp_demonen.py"

CATEGORIES = {
    "satan-duivel",
    "demon-onreine-geest",
    "bezetenheid",
    "uitdrijving",
    "verzoeking-misleiding",
    "demonische-eredienst-afgoderij",
    "gevallen-machten",
    "visioen-symboliek",
    "twijfelgeval",
}
CERTAINTY = {"zeker", "waarschijnlijk", "onzeker"}


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def refs():
    return {item["ref"] for item in load(MENTIONS)["mentions"]}


def test_deterministische_builder_bestrijkt_alle_88_boeken():
    subprocess.run([sys.executable, str(SCRIPT)], cwd=ROOT, check=True)
    first = (MANIFEST.read_bytes(), MENTIONS.read_bytes(), REVIEW.read_bytes())
    subprocess.run([sys.executable, str(SCRIPT)], cwd=ROOT, check=True)
    second = (MANIFEST.read_bytes(), MENTIONS.read_bytes(), REVIEW.read_bytes())
    assert first == second

    manifest = load(MANIFEST)
    assert manifest["status"] == "agent-reviewed"
    assert manifest["humanReviewed"] is False
    assert manifest["publicatieStatus"] == "staging-niet-samenvoegen-zonder-afstemming"
    assert len(manifest["dekkingPerBoek"]) == 88
    assert all(book["verzenBeoordeeld"] > 0 for book in manifest["dekkingPerBoek"])


def test_vermeldingen_hebben_metadata_en_exacte_links():
    books = {book["id"] for book in load(DATA / "books.json")["books"]}
    seen = set()
    for item in load(MENTIONS)["mentions"]:
        assert item["ref"] not in seen
        seen.add(item["ref"])
        assert item["boek"] in books
        assert set(item["categorieen"]) <= CATEGORIES
        assert item["categorieen"]
        assert item["zekerheid"] in CERTAINTY
        assert item["status"] in {"agent-reviewed", "needs-human-review"}
        assert item["humanReviewed"] is False
        assert item["href"] == "index.html#" + item["ref"].replace(" ", "/").replace(":", "/")
        chapter, verse = item["ref"].rsplit(" ", 1)[1].split(":")
        chapter_data = load(DATA / item["boek"] / f"{chapter}.json")
        assert any(v["number"] == int(verse) for v in chapter_data["verses"])


def test_bekende_passages_uit_canon_apocriefen_en_ethiopische_boeken():
    found = refs()
    expected = {
        "leviticus 17:7", "deuteronomium 32:17", "job 1:6",
        "zacharia 3:1", "mattheus 4:1", "markus 5:9",
        "lukas 11:24", "handelingen 16:16", "efeziers 6:12",
        "2petrus 2:4", "judas 1:6", "openbaring 12:9",
        "tobit 3:8", "boekderwijsheid 2:24", "baruch 4:7",
        "henoch 15:8", "jubileeen 10:1", "1meqabyan 18:5",
        "2meqabyan 20:11", "3meqabyan 6:9",
        "henoch 8:1", "jubileeen 1:20", "jubileeen 11:5",
        "henoch 40:7", "henoch 65:6", "3meqabyan 1:20",
        "henoch 6:1", "henoch 7:1", "henoch 10:4",
        "1meqabyan 18:3", "1meqabyan 19:10", "2meqabyan 20:9",
    }
    assert expected <= found


def test_tekstbenamingen_omvatten_eigennaam_en_synoniemvormen():
    by_ref = {item["ref"]: item for item in load(MENTIONS)["mentions"]}
    assert "Asmodeüs" in by_ref["tobit 3:8"]["benamingenInTekst"]
    assert "Azazel" in by_ref["henoch 8:1"]["benamingenInTekst"]
    assert "Beliar" in by_ref["jubileeen 1:20"]["benamingenInTekst"]
    assert "Mastema" in by_ref["jubileeen 11:5"]["benamingenInTekst"]


def test_gewone_tegenstanders_bezit_en_ziekte_worden_niet_blind_getagd():
    found = refs()
    assert "2samuel 19:22" not in found  # satan = menselijke tegenstander
    assert "deuteronomium 30:5" not in found  # land erfelijk bezeten
    assert "nehemia 9:25" not in found  # land erfelijk bezeten
    assert "markus 1:30" not in found  # koorts zonder demonische duiding
    assert "johannes 9:1" not in found  # blindheid zonder demonische duiding


def test_betwiste_identificaties_staan_in_reviewqueue():
    queue = load(REVIEW)["reviewQueue"]
    queued = {item["ref"] for item in queue}
    assert {
        "genesis 3:1", "genesis 6:2", "leviticus 16:8",
        "1koningen 22:21", "jesaja 14:12", "ezechiel 28:14",
        "1petrus 3:19",
    } <= queued
    assert all(item["status"] == "needs-human-review" for item in queue)
    assert all(item["humanReviewed"] is False for item in queue)


def test_engelenoverlap_is_explicit_gelabeld():
    by_ref = {item["ref"]: item for item in load(MENTIONS)["mentions"]}
    for ref in ("2petrus 2:4", "judas 1:6", "openbaring 12:9", "1meqabyan 18:5"):
        assert "engelen" in by_ref[ref]["overlapTopics"]


def test_rapportage_telt_subcategorie_zekerheid_en_boekdekking():
    manifest = load(MANIFEST)
    assert set(manifest["aantallenPerCategorie"]) == CATEGORIES
    assert set(manifest["aantallenPerZekerheid"]) == CERTAINTY
    assert sum(manifest["aantallenPerZekerheid"].values()) == manifest["aantalGetagdeVerzen"]
    assert manifest["aantalReviewgevallen"] == len(load(REVIEW)["reviewQueue"])


def test_tag_is_eenmaal_in_bestaande_onderwerpdata_opgenomen():
    tags = load(DATA / "tags.json")["tags"]
    found = [tag for tag in tags if tag["id"] == "demonen-en-duivelen"]
    assert len(found) == 1
    tag = found[0]
    assert tag["reviewStatus"] == "agent-reviewed"
    assert tag["humanReviewed"] is False
    assert len(tag["verzen"]) == len(load(MENTIONS)["mentions"])
    assert all(item["humanReviewed"] is False for item in tag["verzen"])


def test_onderwerpenpagina_plaatst_tag_bij_de_geestelijke_wereld():
    html = (ROOT / "onderwerpen.html").read_text(encoding="utf-8")
    assert "id: 'geestelijke-wereld'" in html
    assert "ids: ['engelen', 'demonen-en-duivelen', 'reuzen']" in html
