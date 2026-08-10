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


class WikiFrameSafetyTests(unittest.TestCase):
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

    def test_onderwerptekst_opent_de_volledige_lezer_buiten_het_wikiframe(self):
        page = self.browser.new_page(viewport={"width": 1280, "height": 900})
        try:
            page.goto(f"{self.base_url}/wiki.html#onderwerpen", wait_until="domcontentloaded")
            frame = page.frame_locator("#wiki-frame")
            frame.locator(".ond-card").first.wait_for(timeout=15_000)
            frame.locator(".ond-card").first.click()
            frame.locator(".ond-vers-kop a").first.wait_for(timeout=15_000)
            with page.expect_navigation(wait_until="domcontentloaded"):
                frame.locator(".ond-vers-kop a").first.click()
            self.assertIn("/index.html#", page.url)
            self.assertEqual(page.locator("#wiki-frame").count(), 0)
        finally:
            page.close()


if __name__ == "__main__":
    unittest.main()
