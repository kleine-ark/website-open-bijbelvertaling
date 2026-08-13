"""Regressies voor de leesbare woordenboekweergave."""

import contextlib
import http.server
from pathlib import Path
import re
import threading
import unittest

from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[1]


class _QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, _format, *_args):
        pass


class LexiconViewerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        handler = lambda *args, **kwargs: _QuietHandler(
            *args, directory=str(ROOT), **kwargs
        )
        cls.server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
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

    def test_verborgen_verwijzingen_laten_geen_losse_kommas_achter(self):
        """Het verbergen van Schriftverwijzingen mag geen ', ,' of ', ;' tonen."""
        page = self.browser.new_page(viewport={"width": 1280, "height": 900})
        try:
            page.goto(
                f"{self.base_url}/lexicon-viewer.html?taal=grieks&entry=G1605",
                wait_until="domcontentloaded",
            )
            definition = page.locator(".lex-def").first
            definition.wait_for(timeout=15_000)
            page.locator("#lex-refs-toggle").uncheck()
            text = definition.inner_text()
            self.assertIsNone(
                re.search(r",\s*(?:,|;|\])", text),
                text,
            )
        finally:
            page.close()

    def test_veelgebruikte_bronafkortingen_worden_voluit_getoond(self):
        """De lezer ziet bronnamen, niet alleen LXX en AS."""
        page = self.browser.new_page(viewport={"width": 1280, "height": 900})
        try:
            page.goto(
                f"{self.base_url}/lexicon-viewer.html?taal=grieks&entry=G1605",
                wait_until="domcontentloaded",
            )
            definition = page.locator(".lex-def").first
            definition.wait_for(timeout=15_000)
            text = definition.inner_text()
            self.assertIn("Septuaginta", text)
            self.assertIn("Abbott-Smith", text)
            self.assertNotRegex(text, r"\bLXX\b")
            self.assertNotRegex(text, r"\(AS\)")
            self.assertGreaterEqual(
                definition.locator('a[href="bronnen.html#grondteksten"]').count(),
                1,
            )
        finally:
            page.close()
