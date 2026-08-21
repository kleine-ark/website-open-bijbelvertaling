"""Regressietests voor parallelle Bijbeledities in de lezer."""

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


class ParallelEditionsTests(unittest.TestCase):
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

    def open_reader(self, width=1280):
        page = self.browser.new_page(viewport={"width": width, "height": 850})
        page.set_default_timeout(5_000)
        page.goto(f"{self.base_url}/index.html#johannes/1", wait_until="domcontentloaded")
        page.locator('.verse-row[data-verse="1"]').wait_for()
        return page

    def test_engelse_editie_verschijnt_parallel_en_wordt_bewaard(self):
        page = self.open_reader()
        try:
            page.locator('#topnav-tekstopties').click()
            page.locator('details[data-options-category="bronnen"]').evaluate("el => el.open = true")
            checkbox = page.locator('[data-parallel-editie="en-webbe"]')
            checkbox.check()
            parallel = page.locator('.verse-row[data-verse="1"] .parallel-edition[data-editie="en-webbe"]')
            parallel.wait_for()
            self.assertIn("In the beginning was the Word", parallel.inner_text())
            self.assertEqual(parallel.get_attribute("lang"), "en")
            self.assertTrue(page.locator('.edition-comparison[data-layout="naast"]').count())
            self.assertEqual(
                page.evaluate("JSON.parse(localStorage.getItem('sv2026_vertaalopties')).parallelEdities"),
                ["en-webbe"],
            )
        finally:
            page.close()

    def test_maximaal_drie_parallelle_edities_en_arabisch_is_rtl(self):
        page = self.open_reader()
        try:
            page.locator('#topnav-tekstopties').click()
            page.locator('details[data-options-category="bronnen"]').evaluate("el => el.open = true")
            for code in ("en-webbe", "fr-lsg1910", "ar-vd"):
                page.locator(f'[data-parallel-editie="{code}"]').check()
            self.assertTrue(page.locator('[data-parallel-editie="de-luther1912"]').is_disabled())
            arabic = page.locator('.verse-row[data-verse="1"] .parallel-edition[data-editie="ar-vd"]')
            arabic.wait_for()
            self.assertEqual(arabic.get_attribute("dir"), "rtl")
            self.assertEqual(page.locator('.parallel-edition:not(.primary-edition)').count(), 51 * 3)
        finally:
            page.close()

    def test_layout_keuze_zet_parallelle_edities_onder_elkaar(self):
        page = self.open_reader()
        try:
            page.locator('#topnav-tekstopties').click()
            page.locator('details[data-options-category="bronnen"]').evaluate("el => el.open = true")
            page.locator('[data-parallel-editie="en-webbe"]').check()
            page.locator('[data-optie="kolomLayout"][value="eronder"]').check()
            page.locator('.edition-comparison[data-layout="eronder"]').first.wait_for()
        finally:
            page.close()

    def test_opslaan_bewaart_alleen_de_primaire_tekst(self):
        page = self.open_reader()
        try:
            page.locator('#topnav-tekstopties').click()
            page.locator('details[data-options-category="bronnen"]').evaluate("el => el.open = true")
            page.locator('[data-parallel-editie="en-webbe"]').check()
            page.locator('.verse-row[data-verse="1"] .parallel-edition[data-editie="en-webbe"]').wait_for()
            saved = page.evaluate("""
                () => {
                    let captured = null;
                    Storage.saveVerse = (_book, _chapter, _verse, data) => { captured = data; };
                    const row = document.querySelector('.verse-row[data-verse="1"]');
                    Editor.saveVerse(row, 'johannes', 1, 1);
                    return captured.text2026;
                }
            """)
            self.assertIn("In het begin was het Woord", saved)
            self.assertNotIn("In the beginning was the Word", saved)
            self.assertNotIn("Open Vertaling", saved)
        finally:
            page.close()


if __name__ == "__main__":
    unittest.main()
