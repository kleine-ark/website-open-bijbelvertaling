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

    def test_g3588_heeft_nagekeken_opmaak_bronlinks_en_volledige_tekstlinks(self):
        page = self.browser.new_page(viewport={"width": 1280, "height": 1400})
        try:
            page.goto(
                f"{self.base_url}/lexicon-viewer.html?taal=grieks&entry=G3588",
                wait_until="domcontentloaded",
            )
            page.locator('.lex-lexlabel:has-text("Abbott-Smith")').wait_for(timeout=15_000)
            definitions = page.locator(".lex-def")
            abbott = definitions.nth(1)
            text = definitions.all_inner_texts()
            combined = "\n".join(text)

            self.assertNotIn("__", combined)
            self.assertIn("Blass-Debrunner-Funk, paragraaf 71", combined)
            self.assertIn("Moulton, Prolegomena, blz. 81 e.v.", combined)
            self.assertGreaterEqual(definitions.first.locator(".lex-section-title").count(), 2)
            self.assertGreaterEqual(definitions.first.locator(".lex-numbered-item").count(), 9)

            self.assertEqual(page.locator('a[href="wiki.html#homerus"]').count(), 2)
            self.assertEqual(page.locator('a[href="wiki.html#aratus"]').count(), 2)
            for href in (
                "index.html#handelingen/17/28",
                "index.html#1korinthiers/7/7",
                "index.html#galaten/4/22",
                "index.html#handelingen/14/4",
                "index.html#handelingen/17/32",
                "index.html#filippenzen/1/16",
                "index.html#mattheus/16/14",
                "index.html#johannes/7/12",
                "index.html#hebreeen/7/21",
                "index.html#hebreeen/7/23",
                "index.html#mattheus/2/14",
                "index.html#markus/1/45",
                "index.html#lukas/8/21",
                "index.html#johannes/9/38",
            ):
                self.assertGreaterEqual(abbott.locator(f'a[href="{href}"]').count(), 1, href)

            self.assertGreaterEqual(definitions.first.locator("a.lex-xref").count(), 6)
            for strong in ("G3303", "G1161", "G243"):
                self.assertGreaterEqual(
                    abbott.locator(f'a.lex-xref[data-key="{strong}"]').count(),
                    1,
                    strong,
                )
        finally:
            page.close()

    def test_homerus_en_aratus_openen_als_volwaardige_wikipaginas(self):
        for slug, heading in (("homerus", "Homerus"), ("aratus", "Aratus")):
            page = self.browser.new_page(viewport={"width": 1280, "height": 900})
            try:
                page.goto(f"{self.base_url}/wiki.html#{slug}", wait_until="domcontentloaded")
                frame = page.locator("#wiki-frame")
                page.wait_for_function(
                    "slug => document.querySelector('#wiki-frame').getAttribute('src').includes(slug + '.html')",
                    arg=slug,
                )
                self.assertEqual(frame.content_frame.locator("h1").inner_text(), heading)
            finally:
                page.close()
