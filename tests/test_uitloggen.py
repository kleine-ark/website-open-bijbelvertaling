"""Browserverificatie: wie is ingelogd, ziet waar hij kan uitloggen."""

import contextlib
import http.server
import json
from pathlib import Path
import threading
import unittest

from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[1]
GEBRUIKER = {"displayName": "Maarten Vroegindeweij", "photoURL": None, "email": "maarten@example.test"}


class _QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, _format, *_args):
        pass


class _QuietServer(http.server.ThreadingHTTPServer):
    def handle_error(self, _request, _client_address):
        pass


class UitloggenBrowserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        handler = lambda *args, **kwargs: _QuietHandler(*args, directory=str(ROOT), **kwargs)
        cls.server = _QuietServer(("127.0.0.1", 0), handler)
        cls.server_thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.server_thread.start()
        cls.playwright = sync_playwright().start()
        browser_path = next(
            (path for path in (
                Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
                Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
            ) if path.exists()),
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

    def ingelogd(self, width=1280, height=900):
        """Een lezer die eerder inlogde; Firebase blijft buiten beeld, zoals op een traag netwerk."""
        page = self.browser.new_page(viewport={"width": width, "height": height})
        page.add_init_script("localStorage.setItem('osv_auth_cache', %s)" % json.dumps(json.dumps(GEBRUIKER)))
        page.route("https://www.gstatic.com/**", lambda route: route.abort())
        page.goto(f"{self.base_url}/index.html#genesis/1", wait_until="domcontentloaded")
        page.locator("#auth-slot .auth-user").wait_for(state="attached", timeout=15_000)
        return page

    def test_op_desktop_staat_uitloggen_als_knop_met_tekst_in_de_balk(self):
        page = self.ingelogd()
        try:
            knop = page.get_by_role("button", name="Uitloggen")
            self.assertTrue(knop.is_visible())
            self.assertIn("Uitloggen", knop.inner_text())
        finally:
            page.close()

    def test_op_mobiel_staat_uitloggen_in_het_menu(self):
        page = self.ingelogd(width=375, height=812)
        try:
            page.locator("#topnav-hamburger").click()
            knop = page.get_by_role("button", name="Uitloggen")
            self.assertTrue(knop.is_visible())
            self.assertIn("Uitloggen", knop.inner_text())
        finally:
            page.close()

    def test_uitloggen_meldt_direct_af_ook_als_firebase_nog_niet_geladen_is(self):
        page = self.ingelogd()
        try:
            page.get_by_role("button", name="Uitloggen").click()
            page.get_by_role("button", name="Login").wait_for(state="visible", timeout=5_000)
            self.assertIsNone(page.evaluate("localStorage.getItem('osv_auth_cache')"))
            self.assertEqual(page.locator("#auth-slot .auth-user").count(), 0)
        finally:
            page.close()


if __name__ == "__main__":
    unittest.main()
