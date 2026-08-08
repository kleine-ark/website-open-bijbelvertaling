import contextlib
import http.server
import pathlib
import threading
import unittest

from playwright.sync_api import sync_playwright


ROOT = pathlib.Path(__file__).resolve().parents[1]


class _QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, _format, *_args):
        pass


class _QuietServer(http.server.ThreadingHTTPServer):
    def handle_error(self, _request, _client_address):
        pass


class WikiReadingGutterTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        handler = lambda *args, **kwargs: _QuietHandler(
            *args, directory=str(ROOT), **kwargs
        )
        cls.server = _QuietServer(("127.0.0.1", 0), handler)
        cls.server_thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.server_thread.start()

        cls.playwright = sync_playwright().start()
        browser_path = next(
            (
                path
                for path in (
                    pathlib.Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
                    pathlib.Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
                )
                if path.exists()
            ),
            None,
        )
        launch_options = {"headless": True}
        if browser_path:
            launch_options["executable_path"] = str(browser_path)
        cls.browser = cls.playwright.chromium.launch(**launch_options)
        cls.base_url = f"http://127.0.0.1:{cls.server.server_port}"

    @classmethod
    def tearDownClass(cls):
        with contextlib.suppress(Exception):
            cls.browser.close()
        with contextlib.suppress(Exception):
            cls.playwright.stop()
        cls.server.shutdown()
        cls.server.server_close()
        cls.server_thread.join(timeout=2)

    def _left_gutter(self, viewport_width):
        page = self.browser.new_page(
            viewport={"width": viewport_width, "height": 900}
        )
        try:
            page.goto(f"{self.base_url}/wiki.html#bomen-planten")
            article = page.frame_locator("#wiki-frame").locator("#naslag")
            article.wait_for(state="visible")
            return article.evaluate("node => node.getBoundingClientRect().left")
        finally:
            page.close()

    def test_desktop_wiki_article_has_a_reading_gutter(self):
        gutter = self._left_gutter(1450)
        self.assertGreaterEqual(gutter, 24)
        self.assertLessEqual(gutter, 48)

    def test_mobile_wiki_article_keeps_a_compact_reading_gutter(self):
        self.assertGreaterEqual(self._left_gutter(390), 16)

    def test_liederen_overview_omits_lamech(self):
        page = self.browser.new_page(viewport={"width": 1450, "height": 900})
        try:
            page.goto(f"{self.base_url}/wiki.html#liederen")
            article = page.frame_locator("#wiki-frame").locator("#naslag")
            article.wait_for(state="visible")
            self.assertNotIn("Lamech", article.inner_text())
        finally:
            page.close()

    def test_gebeden_overview_has_no_intro_panel(self):
        page = self.browser.new_page(viewport={"width": 1450, "height": 900})
        try:
            page.goto(f"{self.base_url}/wiki.html#gebeden")
            article = page.frame_locator("#wiki-frame").locator("#naslag")
            article.locator(".ns-rooster").wait_for(state="visible")
            self.assertEqual(article.locator(".ns-lead").count(), 0)
        finally:
            page.close()


if __name__ == "__main__":
    unittest.main()
