"""Browserverificatie van het instellingenpaneel op de Bijbelkaart."""

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


class KaartInstellingenBrowserTests(unittest.TestCase):
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

    def open_kaart(self, width=1280, height=800):
        page = self.browser.new_page(viewport={"width": width, "height": height})
        page.goto(f"{self.base_url}/kaart.html", wait_until="domcontentloaded")
        return page

    def test_bediening_opent_als_een_benoemd_paneel_boven_de_kaart(self):
        page = self.open_kaart()
        try:
            opener = page.get_by_role("button", name="Kaart instellen")
            panel = page.get_by_role("region", name="Kaartinstellingen")

            self.assertEqual(opener.get_attribute("aria-expanded"), "false")
            self.assertTrue(panel.is_hidden())
            opener.click()

            self.assertEqual(opener.get_attribute("aria-expanded"), "true")
            self.assertTrue(panel.is_visible())
            self.assertGreater(panel.bounding_box()["x"], page.locator("#map").bounding_box()["x"])
        finally:
            page.close()

    def test_keuzes_zijn_gegroepeerd_en_bestaande_waarden_blijven_beschikbaar(self):
        page = self.open_kaart()
        try:
            page.get_by_role("button", name="Kaart instellen").click()

            zekerheid = page.get_by_role("group", name="Zekerheid van locaties")
            achtergrond = page.get_by_role("group", name="Achtergrondkaart")
            self.assertEqual(zekerheid.get_by_role("checkbox").count(), 3)
            self.assertEqual(achtergrond.get_by_role("radio").count(), 4)
            self.assertEqual(
                achtergrond.get_by_role("radio").evaluate_all("els => els.map(el => el.value)"),
                ["kaart", "stil", "lucht", "land"],
            )
        finally:
            page.close()

    def test_escape_sluit_het_paneel_en_herstelt_focus(self):
        page = self.open_kaart()
        try:
            opener = page.get_by_role("button", name="Kaart instellen")
            opener.click()
            page.keyboard.press("Escape")

            self.assertTrue(page.get_by_role("region", name="Kaartinstellingen").is_hidden())
            self.assertEqual(page.evaluate("document.activeElement.id"), "kaart-instellingen-open")
        finally:
            page.close()

    def test_mobiel_paneel_blijft_binnen_het_scherm(self):
        page = self.open_kaart(width=390, height=844)
        try:
            page.get_by_role("button", name="Kaart instellen").click()
            box = page.get_by_role("region", name="Kaartinstellingen").bounding_box()

            self.assertGreaterEqual(box["x"], 8)
            self.assertLessEqual(box["x"] + box["width"], 382)
            self.assertGreaterEqual(box["width"], 340)
        finally:
            page.close()


if __name__ == "__main__":
    unittest.main()
