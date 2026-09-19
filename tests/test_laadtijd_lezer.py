"""De lezer haalt bij het openen alleen op wat nodig is om de tekst te tonen.

Wat pas bij een instelling zichtbaar wordt (Strong-nummers, tekstverbanden,
het instellingenpaneel), mag de eerste weergave niet ophouden: via een
mobiele verbinding kostte het boekbestand met woordnummers alleen al seconden.
"""
import contextlib
import http.server
import json
import threading
from pathlib import Path

import pytest
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
BROWSERS = (
    Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
    Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
)


class _StilleHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, _format, *_args):
        pass


@pytest.fixture(scope="module")
def basis_url():
    handler = lambda *args, **kwargs: _StilleHandler(*args, directory=str(ROOT), **kwargs)
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_port}"
    server.shutdown()
    server.server_close()


@pytest.fixture(scope="module")
def browser():
    with sync_playwright() as playwright:
        opties = {"headless": True}
        pad = next((pad for pad in BROWSERS if pad.exists()), None)
        if pad:
            opties["executable_path"] = str(pad)
        instantie = playwright.chromium.launch(**opties)
        yield instantie
        with contextlib.suppress(Exception):
            instantie.close()


@contextlib.contextmanager
def lezer(browser, basis_url, plek, opties=None):
    context = browser.new_context(viewport={"width": 1280, "height": 900}, service_workers="block")
    if opties is not None:
        waarde = json.dumps(json.dumps(opties))
        context.add_init_script(f"localStorage.setItem('sv2026_vertaalopties', {waarde});")
    page = context.new_page()
    verzoeken = []
    page.on("request", lambda request: verzoeken.append(request.url))
    try:
        page.goto(f"{basis_url}/index.html#{plek}", wait_until="domcontentloaded")
        page.locator('.verse-row[data-verse="1"]').wait_for(timeout=20_000)
        page.wait_for_load_state("networkidle")
        yield page, verzoeken
    finally:
        context.close()


def opgehaald(verzoeken, einde):
    return [url for url in verzoeken if url.split("?", 1)[0].endswith(einde)]


def open_weergave(page):
    page.locator("#topnav-weergave").click()
    page.locator("#sidebar-right[open]").wait_for()


def zet_aan(page, zoekterm, vinkje):
    open_weergave(page)
    page.locator("#options-search").fill(zoekterm)
    page.locator(vinkje).check()
    page.locator("#sidebar-right-toggle").click()


def test_genesis_1_haalt_zonder_strongweergave_geen_boekbestand_met_woordnummers_op(browser, basis_url):
    with lezer(browser, basis_url, "genesis/1") as (_page, verzoeken):
        assert not [url for url in verzoeken if "/data/woordnummers-inline/" in url]


def test_psalm_23_vult_woordnummers_aan_zodra_de_strongweergave_aangaat(browser, basis_url):
    with lezer(browser, basis_url, "psalmen/23") as (page, verzoeken):
        assert not opgehaald(verzoeken, "/data/woordnummers-inline/psalmen.json")
        zet_aan(page, "Strong", "#toggle-strongs")
        page.locator('.verse-row[data-verse="1"] .col-2026 [data-strongs="H1732"]').first.wait_for(timeout=15_000)
        assert opgehaald(verzoeken, "/data/woordnummers-inline/psalmen.json")


def test_psalm_23_met_bewaarde_strongweergave_toont_de_aanvulling_meteen(browser, basis_url):
    with lezer(browser, basis_url, "psalmen/23", {"strongs": "aan"}) as (page, _verzoeken):
        page.locator('.verse-row[data-verse="1"] .col-2026 [data-strongs="H1732"]').first.wait_for(timeout=15_000)


def test_genesis_1_met_strongweergave_heeft_het_boekbestand_niet_nodig(browser, basis_url):
    # Elk vers van Genesis 1 draagt zijn woordnummers zelf; het boekbestand voegt niets toe.
    with lezer(browser, basis_url, "genesis/1", {"strongs": "aan"}) as (page, verzoeken):
        assert page.locator('.verse-row[data-verse="1"] .col-2026 .strongs-inline').count() > 0
        assert not opgehaald(verzoeken, "/data/woordnummers-inline/genesis.json")


def test_instellingeniconen_laden_pas_als_het_paneel_opengaat(browser, basis_url):
    with lezer(browser, basis_url, "genesis/1") as (page, verzoeken):
        assert not opgehaald(verzoeken, "/images/iconen/instellingen/thema.png")
        with page.expect_request(lambda request: request.url.endswith("/images/iconen/instellingen/thema.png")):
            open_weergave(page)


def test_tekstverbanden_en_torageodata_laden_pas_als_de_optie_aangaat(browser, basis_url):
    with lezer(browser, basis_url, "genesis/12") as (page, verzoeken):
        for bestand in ("/data/genesis-geo.json", "/data/tags.json", "/data/naslag-verzen.json"):
            assert not opgehaald(verzoeken, bestand), bestand
        zet_aan(page, "Tekstverbanden", "#toggle-contextmarkeringen")
        page.locator(".verse-row .geo-locatie").first.wait_for(timeout=15_000)
        page.locator('.verse-row[data-verse="1"] .verse-tag').first.wait_for(timeout=15_000)
        for bestand in ("/data/genesis-geo.json", "/data/tags.json", "/data/naslag-verzen.json"):
            assert opgehaald(verzoeken, bestand), bestand


def test_tag_toevoegen_werkt_ook_zonder_tekstverbanden(browser, basis_url):
    with lezer(browser, basis_url, "genesis/12") as (page, _verzoeken):
        fouten = []
        page.on("pageerror", lambda fout: fouten.append(str(fout)))
        page.locator('.verse-row[data-verse="1"] .verse-num').click(button="right")
        page.locator("#tag-add-popup").wait_for(timeout=10_000)
        assert page.locator("#tag-add-popup button").count() > 0
        assert not fouten


def test_bewaarde_tekstverbanden_staan_meteen_in_beeld(browser, basis_url):
    with lezer(browser, basis_url, "genesis/12", {"geoMarkeren": "aan"}) as (page, _verzoeken):
        page.locator(".verse-row .geo-locatie").first.wait_for(timeout=15_000)
        page.locator('.verse-row[data-verse="1"] .verse-tag').first.wait_for(timeout=15_000)
