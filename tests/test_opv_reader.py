"""Browserregressies voor OPV als primaire, parallelle en citaateditie."""

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

    def copyfile(self, source, outputfile):
        with contextlib.suppress(ConnectionError):
            super().copyfile(source, outputfile)


class OpvReaderTests(unittest.TestCase):
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

    def new_page(self, settings=None):
        page = self.browser.new_page(viewport={"width": 1280, "height": 900})
        page.set_default_timeout(10_000)
        if settings is not None:
            page.add_init_script(
                "localStorage.setItem('sv2026_vertaalopties', "
                + json.dumps(json.dumps(settings))
                + ")"
            )
        return page

    @staticmethod
    def open_sources(page):
        page.locator("#topnav-tekstopties").click()
        sources = page.locator('details[data-options-category="bronnen"]')
        sources.evaluate("element => { element.open = true; }")

    def test_opv_is_primaire_editie_en_bewaart_readerdata(self):
        page = self.new_page()
        try:
            page.goto(
                f"{self.base_url}/index.html?editie=nl-opv#genesis/1",
                wait_until="domcontentloaded",
            )
            verse = page.locator('.verse-row[data-verse="1"] .col-2026')
            verse.wait_for()
            self.assertIn("hemel", verse.inner_text())
            self.assertEqual(verse.get_attribute("lang"), "nl")

            readerdata = page.evaluate(
                """async () => {
                    const chapter = await TekstEditie.loadChapterForEdition('nl-opv', 'genesis', 1);
                    const first = chapter.verses.find(verse => verse.number === 1);
                    const spoken = chapter.verses.find(verse => verse.number === 3);
                    return {
                        edition: chapter._translation.code,
                        block: chapter.blokken[0],
                        status: first.status,
                        source: first.bron,
                        concepts: first.begrippen,
                        citations: spoken.citaten,
                    };
                }"""
            )
            self.assertEqual(readerdata["edition"], "nl-opv")
            self.assertEqual(readerdata["block"]["kop"], "Het begin")
            self.assertEqual(readerdata["status"], "concept")
            self.assertEqual(readerdata["source"]["bestand"], "data/genesis/1.json")
            self.assertEqual(readerdata["concepts"][0]["conceptId"], "schepping")
            self.assertEqual(readerdata["citations"][0]["spreker"]["type"], "god")
        finally:
            page.close()

    def test_wisselen_naar_opv_gebeurt_zonder_reload_en_blijft_bewaard(self):
        page = self.new_page()
        try:
            page.goto(f"{self.base_url}/index.html#genesis/1", wait_until="domcontentloaded")
            page.locator('.verse-row[data-verse="1"]').wait_for()
            page.evaluate("window.__opvDocumentMarker = 'zelfde-document'")
            self.open_sources(page)
            edition = page.locator("#opt-teksteditie")
            edition.focus()
            edition.select_option("nl-opv")

            page.locator('.verse-row[data-verse="1"] .col-2026').filter(has_text="hemel").wait_for()
            self.assertEqual(page.evaluate("window.__opvDocumentMarker"), "zelfde-document")
            self.assertEqual(page.evaluate("document.activeElement.id"), "opt-teksteditie")
            self.assertIn("editie=nl-opv", page.url)
            self.assertEqual(
                page.evaluate(
                    "JSON.parse(localStorage.getItem('sv2026_vertaalopties')).teksteditie"
                ),
                "nl-opv",
            )
        finally:
            page.close()

    def test_opv_kan_parallel_naast_open_vertaling_worden_getoond(self):
        page = self.new_page()
        try:
            page.goto(f"{self.base_url}/index.html#genesis/1", wait_until="domcontentloaded")
            page.locator('.verse-row[data-verse="1"]').wait_for()
            self.open_sources(page)
            page.locator('[data-parallel-editie="nl-opv"]').check()

            parallel = page.locator(
                '.verse-row[data-verse="1"] .parallel-edition[data-editie="nl-opv"]'
            )
            parallel.wait_for()
            self.assertIn("maakte God de hemel", parallel.inner_text())
            self.assertEqual(parallel.get_attribute("lang"), "nl")
            self.assertEqual(
                page.evaluate(
                    "JSON.parse(localStorage.getItem('sv2026_vertaalopties')).parallelEdities"
                ),
                ["nl-opv"],
            )
        finally:
            page.close()

    def test_opv_toont_buiten_pilotdekking_een_explicitiete_melding(self):
        page = self.new_page()
        try:
            page.goto(
                f"{self.base_url}/index.html?editie=nl-opv#genesis/6",
                wait_until="domcontentloaded",
            )
            unavailable = page.locator(".translation-unavailable")
            unavailable.wait_for()
            self.assertIn("Genesis is niet beschikbaar", unavailable.inner_text())
            self.assertIn("Open Parafrase Vertaling (proef)", unavailable.inner_text())
            self.assertEqual(page.locator(".verse-row").count(), 0)
        finally:
            page.close()

    def test_wiki_citaat_volgt_de_globale_opv_editie_en_bronnaam(self):
        page = self.new_page({"teksteditie": "nl-opv"})
        try:
            page.goto(
                f"{self.base_url}/liederen.html?item=lied-bij-de-schelfzee",
                wait_until="domcontentloaded",
            )
            page.wait_for_function("typeof window.OSV !== 'undefined'")
            citation = page.evaluate(
                """async () => {
                    const result = await OSV.cite('genesis 1:1');
                    return {
                        edition: result.editie,
                        language: result.taal,
                        html: result.html,
                        plain: result.plain,
                    };
                }"""
            )
            self.assertEqual(citation["edition"], "nl-opv")
            self.assertEqual(citation["language"], "nl")
            self.assertIn("In het begin maakte God", citation["plain"])
            self.assertIn("Open Parafrase Vertaling (proef)", citation["html"])
            self.assertNotIn("(Open Vertaling)", citation["html"])
        finally:
            page.close()

    def test_opv_erft_geen_ov_verificatiestatus_of_audio(self):
        page = self.new_page()
        try:
            page.goto(
                f"{self.base_url}/index.html?editie=nl-opv#genesis/1",
                wait_until="domcontentloaded",
            )
            row = page.locator('.verse-row[data-verse="1"]')
            row.wait_for()
            self.assertEqual(row.get_attribute("data-status"), "concept")
            self.assertFalse(page.locator("#audio-play-big").is_visible())
            self.assertFalse(page.locator("#audio-play-mobile").is_visible())
            self.assertEqual(page.locator("#ai-concept-banner:visible").count(), 0)
            self.assertEqual(page.locator("#chapter-title .chapter-concept-tag").count(), 0)
        finally:
            page.close()


if __name__ == "__main__":
    unittest.main()
