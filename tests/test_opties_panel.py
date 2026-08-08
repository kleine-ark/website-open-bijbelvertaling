"""Browserverificatie van het responsieve optiespaneel."""

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


class _QuietServer(http.server.ThreadingHTTPServer):
    def handle_error(self, _request, _client_address):
        pass


class OptionsPanelBrowserTests(unittest.TestCase):
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
                    Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
                    Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
                )
                if path.exists()
            ),
            None,
        )
        options = {"headless": True}
        if browser_path:
            options["executable_path"] = str(browser_path)
        cls.browser = cls.playwright.chromium.launch(**options)
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

    def open_reader(self, width=1280, height=900):
        page = self.browser.new_page(viewport={"width": width, "height": height})
        page.goto(f"{self.base_url}/index.html#genesis/1", wait_until="domcontentloaded")
        page.locator("#sidebar-right-open").wait_for(state="visible", timeout=15_000)
        return page

    def test_opties_opent_modaal_zonder_de_leestekst_te_versmallen(self):
        page = self.open_reader()
        try:
            content = page.locator("#content")
            before = content.bounding_box()["width"]
            page.locator("#sidebar-right-open").click()
            dialog_is_open = page.locator("#sidebar-right").evaluate(
                "el => el instanceof HTMLDialogElement && el.open"
            )
            after = content.bounding_box()["width"]

            self.assertTrue(dialog_is_open)
            self.assertAlmostEqual(after, before, delta=1)
        finally:
            page.close()

    def test_opties_heeft_drie_toegankelijke_tabs(self):
        page = self.open_reader()
        try:
            page.locator("#sidebar-right-open").click()
            self.assertEqual(
                page.get_by_role("tab").all_text_contents(),
                ["Lezen", "Vergelijken", "Onderzoeken"],
            )
        finally:
            page.close()


if __name__ == "__main__":
    unittest.main()
