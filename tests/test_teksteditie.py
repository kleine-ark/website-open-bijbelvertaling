"""Verticale-slice tests voor meertalige Bijbeltekst met Nederlandse UI."""

import contextlib
import http.server
import json
from pathlib import Path
import threading
import unittest

from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[1]


class _QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, _format, *_args):
        pass


class TekstEditieTests(unittest.TestCase):
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

    def open_reader(self, edition, location="genesis/1"):
        page = self.browser.new_page(viewport={"width": 1280, "height": 900})
        page.goto(
            f"{self.base_url}/index.html?editie={edition}#{location}",
            wait_until="domcontentloaded",
        )
        return page

    def test_manifest_contains_all_approved_editions(self):
        manifest = json.loads((ROOT / "data" / "vertalingen" / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(
            [item["code"] for item in manifest["edities"]],
            ["fr-lsg1910", "en-webbe", "ar-vd", "es-rv1909"],
        )

    def test_french_query_renders_french_text_with_text_language(self):
        page = self.open_reader("fr-lsg1910")
        try:
            verse = page.locator('.verse-row[data-verse="1"] .col-2026')
            verse.wait_for(timeout=20_000)
            self.assertIn("commencement", verse.inner_text())
            self.assertEqual(verse.get_attribute("lang"), "fr")
            self.assertEqual(page.locator("html").get_attribute("lang"), "nl")
        finally:
            page.close()

    def test_arabic_text_is_rtl_but_interface_remains_ltr(self):
        page = self.open_reader("ar-vd")
        try:
            verse = page.locator('.verse-row[data-verse="1"] .col-2026')
            verse.wait_for(timeout=20_000)
            self.assertIn("ٱلْبَدْءِ", verse.inner_text())
            self.assertEqual(verse.get_attribute("dir"), "rtl")
            self.assertEqual(page.locator("html").get_attribute("dir"), None)
        finally:
            page.close()

    def test_option_switches_edition_without_page_reload(self):
        page = self.open_reader("nl-ov")
        try:
            page.locator('.verse-row[data-verse="1"]').wait_for(timeout=20_000)
            marker = page.evaluate("window.__editionMarker = Math.random(); window.__editionMarker")
            page.locator("#sidebar-right-open").click()
            page.locator('details[data-options-category="bronnen"] > summary').click()
            page.locator('[data-optie="teksteditie"]').select_option("en-webbe")
            page.locator('.verse-row[data-verse="1"] .col-2026').wait_for(timeout=20_000)
            page.wait_for_function("document.querySelector('.col-2026').innerText.includes('beginning')")
            self.assertEqual(page.evaluate("window.__editionMarker"), marker)
            self.assertIn("editie=en-webbe", page.url)
        finally:
            page.close()

    def test_missing_book_shows_coverage_message_without_dutch_fallback(self):
        page = self.open_reader("fr-lsg1910", "henoch/1")
        try:
            message = page.locator(".translation-unavailable")
            message.wait_for(timeout=20_000)
            self.assertIn("niet beschikbaar", message.inner_text())
            self.assertEqual(page.locator(".verse-row").count(), 0)
            dutch_link = message.locator("a")
            self.assertIn("editie=nl-ov", dutch_link.get_attribute("href"))
            dutch_link.click()
            page.locator('.verse-row[data-verse="1"]').wait_for(timeout=20_000)
        finally:
            page.close()

    def test_i18n_catalog_does_not_expose_key_names(self):
        catalog = json.loads((ROOT / "i18n" / "nl.json").read_text(encoding="utf-8"))
        self.assertEqual(catalog["edition.unavailable"], "{boek} is niet beschikbaar in {editie}.")


if __name__ == "__main__":
    unittest.main()
