"""Browser- en datacontracten voor bronvaste Strong-verwijzingen."""

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


class _QuietServer(http.server.ThreadingHTTPServer):
    def handle_error(self, _request, _client_address):
        pass


class StrongsReaderBrowserTests(unittest.TestCase):
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

    def open_reader(self, location="genesis/1", width=1280, height=900):
        page = self.browser.new_page(viewport={"width": width, "height": height})
        page.goto(f"{self.base_url}/index.html#{location}", wait_until="domcontentloaded")
        page.locator('.verse-row[data-verse="1"]').wait_for(timeout=15_000)
        return page

    def enable_strongs(self, page, expect_alignment=True):
        opener = "#mobile-opties-btn" if page.viewport_size["width"] <= 768 else "#sidebar-right-open"
        page.locator(opener).click()
        page.locator("#options-tab-onderzoeken").click()
        page.locator("#toggle-strongs").check()
        page.locator("#sidebar-right-toggle").click()
        if expect_alignment:
            page.locator('.verse-row[data-verse="1"] .strongs-alignment').wait_for(timeout=5_000)

    def test_strongs_voorkeur_staat_standaard_uit_en_wordt_bewaard(self):
        page = self.open_reader()
        try:
            page.locator("#sidebar-right-open").click()
            page.locator("#options-tab-onderzoeken").click()
            toggle = page.locator("#toggle-strongs")
            self.assertFalse(toggle.is_checked())
            toggle.check()
            page.wait_for_function(
                "JSON.parse(localStorage.getItem('sv2026_vertaalopties')).strongs === 'aan'"
            )
            page.reload(wait_until="domcontentloaded")
            page.locator("#sidebar-right-open").wait_for(state="visible", timeout=15_000)
            page.locator("#sidebar-right-open").click()
            page.locator("#options-tab-onderzoeken").click()
            self.assertTrue(toggle.is_checked())
        finally:
            page.close()

    def test_bronwoord_en_strongnummer_blijven_een_bronvaste_eenheid(self):
        page = self.open_reader("genesis/1")
        try:
            self.enable_strongs(page)
            first = page.locator('.verse-row[data-verse="1"] .strongs-token').first
            self.assertIn("H7225", first.inner_text())
            self.assertEqual(first.locator('[data-strongs="H7225"]').inner_text(), "<H7225>")
            self.assertTrue(first.locator(".strongs-source-word").inner_text().strip())
            self.assertEqual(
                page.locator('.verse-row[data-verse="1"] .col-2026 > .strongs-inline').count(),
                0,
                "Strong-nummers mogen niet sequentieel aan Nederlandse woorden worden gegokt",
            )
        finally:
            page.close()

    def test_klik_op_strong_opent_toegankelijke_bottom_sheet_met_woordenboeklink(self):
        page = self.open_reader("johannes/1")
        try:
            self.enable_strongs(page)
            trigger = page.locator('.verse-row[data-verse="1"] [data-strongs="G1722"]').first
            trigger.click()
            sheet = page.locator("#strongs-sheet")
            sheet.wait_for(state="visible", timeout=5_000)
            self.assertEqual(sheet.get_attribute("role"), "dialog")
            self.assertEqual(sheet.get_attribute("aria-modal"), "true")
            self.assertIn("G1722", page.locator("#strongs-sheet-number").inner_text())
            self.assertTrue(page.locator("#strongs-sheet-word").inner_text().strip())
            self.assertTrue(page.locator("#strongs-sheet-definition").inner_text().strip())
            self.assertIn(
                "entry=G1722",
                page.locator("#strongs-sheet-full-link").get_attribute("href"),
            )

            page.locator("#strongs-sheet-definition").click()
            self.assertTrue(sheet.is_visible(), "interactie binnen het paneel mag het niet sluiten")

            page.locator(".strongs-sheet-close").focus()
            page.keyboard.press("Shift+Tab")
            self.assertEqual(page.evaluate("document.activeElement.id"), "strongs-sheet-full-link")
            page.keyboard.press("Tab")
            self.assertIn("strongs-sheet-close", page.evaluate("document.activeElement.className"))

            page.keyboard.press("Escape")
            self.assertFalse(sheet.is_visible())
            self.assertTrue(trigger.evaluate("el => document.activeElement === el"))
        finally:
            page.close()

    def test_meerdere_strongnummers_worden_afzonderlijk_aanklikbaar(self):
        page = self.open_reader()
        try:
            html = page.evaluate(
                """() => App.renderStrongLinks([
                    {woord: 'testwoord', strongs: 'H1 G3056', transliteratie: 'test'}
                ])"""
            )
            self.assertIn('data-strongs="H1"', html)
            self.assertIn('data-strongs="G3056"', html)
            self.assertIn("&lt;H1&gt;", html)
            self.assertIn("&lt;G3056&gt;", html)
        finally:
            page.close()

    def test_griekse_alignering_leest_van_links_naar_rechts(self):
        page = self.open_reader("johannes/1")
        try:
            self.enable_strongs(page)
            alignment = page.locator('.verse-row[data-verse="1"] .strongs-alignment')
            self.assertEqual(alignment.evaluate("el => getComputedStyle(el).direction"), "ltr")
            self.assertEqual(
                alignment.locator(".strongs-source-word").first.get_attribute("lang"),
                "grc",
            )
        finally:
            page.close()

    def test_bottom_sheet_past_op_mobiel_en_sluit_via_de_achtergrond(self):
        page = self.open_reader("johannes/1", width=390, height=844)
        try:
            self.enable_strongs(page)
            trigger = page.locator('.verse-row[data-verse="1"] [data-strongs="G1722"]').first
            trigger.click()
            sheet = page.locator("#strongs-sheet")
            sheet.wait_for(state="visible", timeout=5_000)
            panel_box = page.locator(".strongs-sheet-panel").bounding_box()
            self.assertLessEqual(panel_box["width"], 390)
            self.assertAlmostEqual(panel_box["y"] + panel_box["height"], 844, delta=1)

            sheet.click(position={"x": 4, "y": 4})
            self.assertFalse(sheet.is_visible())
            self.assertTrue(trigger.evaluate("el => document.activeElement === el"))
        finally:
            page.close()

    def test_latijnse_en_geez_eigen_nummers_worden_niet_als_strongs_getoond(self):
        page = self.open_reader("4ezra/1")
        try:
            self.enable_strongs(page, expect_alignment=False)
            self.assertEqual(page.locator('.strongs-alignment [data-strongs^="OVL"]').count(), 0)
            self.assertEqual(page.locator('.strongs-alignment [data-strongs^="OVG"]').count(), 0)
        finally:
            page.close()

    def test_stronglabels_blijven_buiten_gekopieerde_bijbeltekst(self):
        page = self.open_reader("genesis/1")
        try:
            self.enable_strongs(page)
            source_word = page.locator(
                '.verse-row[data-verse="1"] .strongs-source-word'
            ).first.inner_text()
            copied = page.evaluate(
                """() => {
                    VerseSelect.selected = new Set(['genesis/1/1']);
                    return VerseSelect._buildRefAndText().plain;
                }"""
            )
            self.assertNotIn("H7225", copied)
            self.assertNotIn(source_word, copied)
            self.assertIn("begin", copied.lower())
        finally:
            page.close()


class StrongsDataTests(unittest.TestCase):
    def test_strongverwijzingen_zijn_alleen_bronnummers(self):
        prefixes = set()
        for chapter_file in ROOT.glob("data/*/[0-9]*.json"):
            data = json.loads(chapter_file.read_text(encoding="utf-8"))
            for verse in data.get("verses", []):
                if not isinstance(verse, dict):
                    continue
                for word in verse.get("grondtekst", []) or []:
                    if not isinstance(word, dict):
                        continue
                    value = str(word.get("strongs") or "")
                    if value:
                        prefixes.add(value[:1])
        self.assertTrue({"H", "G"}.issubset(prefixes))
        self.assertTrue(prefixes.issubset({"H", "G", "O"}))


if __name__ == "__main__":
    unittest.main()
