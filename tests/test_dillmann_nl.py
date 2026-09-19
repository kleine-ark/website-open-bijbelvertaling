"""De Nederlandse vertaling van Dillmanns Ge'ez-woordenboek (data/lexicon-nl/dillmann-nl.json).

De vertaling mag de tekst vervangen, maar niets van wat Dillmann aanhaalt: de Ge'ez-citaten
moeten ongeschonden blijven en elke link moet naar een bestaand vers in de Open Vertaling wijzen.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GEZ = re.compile(r"<gez>.*?</gez>", re.S)
LINK = re.compile(r'<a class="lex-reflink" data-ref="([a-z0-9]+) (\d+):(\d+)"')


def lees(pad):
    return json.loads((ROOT / pad).read_text(encoding="utf-8"))


VERTALING = lees("data/lexicon-nl/dillmann-nl.json")
BRON = {str(w["n"]): w for w in lees("data/lexicon-dillmann-geez.json")["woorden"]}


def test_elk_vertaald_artikel_hoort_bij_een_lemma_en_heeft_uitleg_en_gloss():
    for n, artikel in VERTALING.items():
        assert n in BRON, n
        assert artikel.get("definitieNl", "").strip(), n
        gloss = artikel.get("glossNl", "")
        assert gloss.strip() and "<" not in gloss and len(gloss) <= 100, (n, gloss)


def test_de_ge_ez_citaten_zijn_ongeschonden():
    for n, artikel in VERTALING.items():
        assert GEZ.findall(artikel["definitieNl"]) == GEZ.findall(BRON[n]["definitie"]), n


def test_elke_link_wijst_naar_een_bestaand_vers():
    verzen = {}
    for n, artikel in VERTALING.items():
        for boek, hoofdstuk, vers in LINK.findall(artikel["definitieNl"]):
            sleutel = (boek, hoofdstuk)
            if sleutel not in verzen:
                pad = ROOT / "data" / boek / f"{hoofdstuk}.json"
                verzen[sleutel] = {v["number"] for v in json.loads(pad.read_text(encoding="utf-8"))["verses"]} if pad.exists() else set()
            assert int(vers) in verzen[sleutel], (n, boek, hoofdstuk, vers)


def test_de_opmaak_is_in_balans():
    for n, artikel in VERTALING.items():
        html = artikel["definitieNl"]
        for tag in ("span", "i", "b", "abbr", "a", "gez"):
            assert len(re.findall(rf"<{tag}[\s>]", html)) == html.count(f"</{tag}>"), (n, tag)
