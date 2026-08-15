"""Regressietests voor het onderwerp Wijn en de uniforme Top 10."""

import contextlib
import http.server
import json
from pathlib import Path
import re
import subprocess
import sys
import threading
import unittest

from playwright.sync_api import sync_playwright

from scripts.build_corpus_naslag import load_corpus
from scripts.build_wijn_onderwerp import build_wijn


ROOT = Path(__file__).resolve().parents[1]
WIJN = re.compile(r"(?<![0-9A-Za-zÀ-ÖØ-öø-ÿ-])wijn(?![0-9A-Za-zÀ-ÖØ-öø-ÿ-])", re.I)


def test_wijn_tag_dekt_ieder_letterlijk_voorkomen_in_het_corpus():
    """Een zoekpatroon mag geen wijnvers stilzwijgend uit de tag verliezen."""
    gebouwd = build_wijn(ROOT, write=False)
    tagged = {item["ref"] for item in gebouwd["tag"]["verzen"]}
    verwacht = {vers.ref for vers in load_corpus(ROOT, include_ethiopic=True) if WIJN.search(vers.text)}

    assert tagged == verwacht


def test_wijn_top_tien_bevat_kernteksten_uit_oude_en_nieuwe_testament():
    """Een lege of louter chronologische keuze zou het redactionele overzicht breken."""
    top_tien = build_wijn(ROOT, write=False)["tag"]["topTien"]

    assert len(top_tien) == 10
    assert len(set(top_tien)) == 10
    assert {
        "genesis 14:18",
        "psalmen 104:15",
        "johannes 2:9",
        "efeziers 5:18",
    } <= set(top_tien)


def test_wijn_builder_kan_rechtstreeks_worden_uitgevoerd_zonder_importfout():
    """Een uitvoerbare onderhoudsopdracht moet ook buiten pytest werken."""
    result = subprocess.run(
        [sys.executable, "scripts/build_wijn_onderwerp.py", "--check"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["verzenGetagd"] > 0


class _QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, _format, *_args):
        pass


class _QuietServer(http.server.ThreadingHTTPServer):
    def handle_error(self, _request, _client_address):
        pass


class OnderwerpTopTienBrowserTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        handler = lambda *args, **kwargs: _QuietHandler(*args, directory=str(ROOT), **kwargs)
        cls.server = _QuietServer(("127.0.0.1", 0), handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch(headless=True)
        cls.base_url = f"http://127.0.0.1:{cls.server.server_port}"

    @classmethod
    def tearDownClass(cls):
        with contextlib.suppress(Exception):
            cls.browser.close()
        with contextlib.suppress(Exception):
            cls.playwright.stop()
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)

    def test_ieder_onderwerp_toont_top_tien_met_de_universele_citatiecomponent(self):
        """Zonder gedeelde renderer zouden onderwerpen verschillende tekstweergaven krijgen."""
        page = self.browser.new_page(viewport={"width": 1280, "height": 900})
        try:
            page.goto(f"{self.base_url}/onderwerpen.html#tag=wijn")
            page.locator("#ond-detail.ond-detail-active").wait_for(state="visible")
            page.locator(".ond-top10-vers .osv-vers").first.wait_for(state="visible")
            self.assertEqual(page.locator(".ond-top10-vers").count(), 10)
            self.assertEqual(
                page.locator(".ond-top10-vers").first.get_attribute("data-ref"),
                "genesis 14:18",
            )
            self.assertEqual(page.locator(".ond-top10-vers .ov-naslagtekst").count(), 10)

            page.goto(f"{self.base_url}/onderwerpen.html#tag=schepping")
            page.locator("#ond-detail.ond-detail-active").wait_for(state="visible")
            page.locator(".ond-top10-vers .osv-vers").first.wait_for(state="visible")
            self.assertEqual(page.locator(".ond-top10-vers").count(), 10)
        finally:
            page.close()
