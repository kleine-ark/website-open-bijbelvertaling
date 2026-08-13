"""Browserverificatie voor een eigen bronpagina van een plaats."""

import contextlib
import http.server
from pathlib import Path
import threading
import unittest

from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[1]


class _QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, _format, *_args):
        pass


class PlaatsdetailBrowserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        handler = lambda *args, **kwargs: _QuietHandler(*args, directory=str(ROOT), **kwargs)
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

    def test_plaatsdetail_toont_de_gepubliceerde_bron_en_alle_tekstverwijzingen(self):
        page = self.browser.new_page()
        try:
            page.goto(
                f"{self.base_url}/plaats.html?plaats=geo-abarim-a8275b",
                wait_until="domcontentloaded",
            )
            page.get_by_role("heading", name="Abarim").wait_for(timeout=15_000)
            self.assertTrue(page.get_by_role("heading", name="Alle tekstverwijzingen").is_visible())
            self.assertGreaterEqual(page.locator(".tekstverwijzingen a").count(), 5)
            self.assertTrue(page.get_by_role("heading", name="Brongegevens").is_visible())
            source = page.get_by_role("link", name="Bron openen ↗")
            self.assertEqual(
                source.get_attribute("href"),
                "https://github.com/openbibleinfo/Bible-Geocoding-Data",
            )
            self.assertEqual(
                page.get_by_role("link", name="Bekijk deze plaats op de kaart →").get_attribute("href"),
                "kaart.html?plaats=geo-abarim-a8275b",
            )
        finally:
            page.close()


if __name__ == "__main__":
    unittest.main()
