"""De Open Vertaling is vrij van rechten (CC0), in alle 88 boeken; wat AI's en zoekmachines lezen moet dat ook zeggen."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CC0 = "https://creativecommons.org/publicdomain/zero/1.0/"


def lees(pad):
    return (ROOT / pad).read_text(encoding="utf-8")


def json_ld(pad):
    return [json.loads(blok) for blok in re.findall(r'<script type="application/ld\+json">(.*?)</script>', lees(pad), re.S)]


def licenties(knoop):
    if isinstance(knoop, dict):
        for sleutel, waarde in knoop.items():
            if sleutel == "license":
                yield waarde
            yield from licenties(waarde)
    elif isinstance(knoop, list):
        for waarde in knoop:
            yield from licenties(waarde)


def boeken():
    return json.loads(lees("data/books-index.json"))["boeken"]


def test_llms_txt_zegt_dat_alle_boeken_vrij_van_rechten_zijn():
    tekst = lees("llms.txt")
    assert "CC0" in tekst and CC0 in tekst
    assert re.search(r"vrij van rechten", tekst, re.I)
    for groep in ("apocrief", "Ethiopisch"):
        assert re.search(groep, tekst, re.I)
    # Niet-commercieel geldt alleen voor enkele brondatasets, nooit voor de Bijbeltekst zelf.
    for regel in tekst.splitlines():
        if re.search(r"niet-commercieel|non-commercial", regel, re.I):
            assert re.search(r"LXX|Rahlfs|Dillmann|BY-NC", regel), regel


def test_llms_txt_wijst_naar_de_volledige_tekst_en_de_leespaginas():
    tekst = lees("llms.txt")
    assert "https://openvertaling.nl/llms-full.txt" in tekst
    assert "https://openvertaling.nl/bijbel/{boek-id}/{hoofdstuk}.html" in tekst


def test_llms_txt_noemt_ieder_boek_met_zijn_data_id():
    tekst = lees("llms.txt")
    ontbrekend = [boek["id"] for boek in boeken() if f"`{boek['id']}`" not in tekst]
    assert not ontbrekend, ontbrekend


def test_boekenindex_noemt_cc0():
    licentie = json.loads(lees("data/books-index.json"))["licentie"]
    assert "CC0" in licentie and "niet-commercieel" not in licentie


def test_voor_ai_pagina_en_json_ld_noemen_cc0():
    pagina = lees("voor-ai.html")
    assert "niet-commerci" not in pagina
    gevonden = [waarde for blok in json_ld("voor-ai.html") for waarde in licenties(blok)]
    assert gevonden and all(waarde == CC0 for waarde in gevonden), gevonden


def test_citeervoorbeeld_op_de_ai_pagina_is_de_tekst_van_de_open_vertaling():
    # Een taalmodel neemt dit voorbeeld over als "de" Open Vertaling van Johannes 3:16.
    vers = next(v for v in json.loads(lees("data/johannes/3.json"))["verses"] if v["number"] == 16)
    citaat = re.search(r'<div class="ai-quote">&ldquo;(.*?)&rdquo;</div>', lees("voor-ai.html"), re.S).group(1)
    assert " ".join(citaat.split()) == vers["text2026"]


def test_homepage_wijst_crawlers_zonder_javascript_naar_de_leespaginas():
    noscript = re.search(r"<noscript>(.*?)</noscript>", lees("index.html"), re.S).group(1)
    assert 'href="bijbel/"' in noscript and 'href="llms-full.txt"' in noscript


def test_homepage_json_ld_draagt_de_cc0_licentie():
    grafen = [knoop for blok in json_ld("index.html") for knoop in blok.get("@graph", [blok])]
    boek = next(knoop for knoop in grafen if knoop.get("@type") == "Book")
    assert boek.get("license") == CC0
