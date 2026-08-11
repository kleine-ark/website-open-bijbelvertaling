"""Regressies voor de ene gedeelde OV-citatietemplate op naslagpagina's."""

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


class WikiCitationTemplateTests(unittest.TestCase):
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

    def open_page(self, path, settings=None):
        page = self.browser.new_page(viewport={"width": 1280, "height": 900})
        if settings:
            page.add_init_script(
                "localStorage.setItem('sv2026_vertaalopties', "
                + json.dumps(json.dumps(settings))
                + ")"
            )
        page.goto(f"{self.base_url}/{path}", wait_until="domcontentloaded")
        page.locator(".ov-naslagtekst .osv-vers").first.wait_for(timeout=15_000)
        return page

    def test_lied_gebruikt_hoofdlezer_aanhalingstekens_en_globale_opties(self):
        page = self.open_page(
            "liederen.html?item=lied-bij-de-schelfzee",
            {"godsnaam": "klassiek", "versnummers": "uit", "citaten": "aan", "strongs": "aan"},
        )
        try:
            citation = page.locator(".ov-naslagtekst").first
            text = citation.inner_text()
            self.assertIn("HEERE", text)
            self.assertNotIn("JAHWEH", text)
            self.assertEqual(citation.locator(".osv-num").count(), 0)
            strongs = citation.locator(".strongs-inline")
            self.assertGreater(strongs.count(), 0)
            self.assertTrue(strongs.first.is_visible())
            self.assertRegex(strongs.first.get_attribute("data-strongs") or "", r"^[HG]\d+")
            speech = citation.locator(".direct-speech").first
            self.assertIn("“", speech.evaluate("el => getComputedStyle(el, '::before').content"))
            self.assertIn("”", speech.evaluate("el => getComputedStyle(el, '::after').content"))
            self.assertNotIn("«", speech.evaluate("el => getComputedStyle(el, '::before').content"))
        finally:
            page.close()

    def test_lied_citaat_volgt_de_geselecteerde_franseteksteditie(self):
        page = self.open_page(
            "liederen.html?item=lied-bij-de-schelfzee",
            {"teksteditie": "fr-lsg1910"},
        )
        try:
            citation = page.locator('.gt-vers[data-ref="exodus 15:1-18"] .ov-naslagtekst')
            citation.locator('.osv-vers').first.wait_for(timeout=15_000)
            self.assertEqual(citation.get_attribute("lang"), "fr")
            self.assertEqual(citation.get_attribute("data-osv-editie"), "fr-lsg1910")
            self.assertIn("ternel", citation.inner_text())
        finally:
            page.close()

    def test_lied_citaat_volgt_de_geselecteerde_engelseteksteditie(self):
        page = self.open_page(
            "liederen.html?item=lied-bij-de-schelfzee",
            {"teksteditie": "en-webbe"},
        )
        try:
            citation = page.locator('.gt-vers[data-ref="exodus 15:1-18"] .ov-naslagtekst')
            citation.locator('.osv-vers').first.wait_for(timeout=15_000)
            self.assertEqual(citation.get_attribute("lang"), "en")
            self.assertEqual(citation.get_attribute("data-osv-editie"), "en-webbe")
            self.assertIn("song to the LORD", citation.inner_text())
        finally:
            page.close()

    def test_lied_citaat_volgt_de_geselecteerde_arabische_editie_en_rtl_link(self):
        page = self.open_page(
            "liederen.html?item=lied-bij-de-schelfzee",
            {"teksteditie": "ar-vd"},
        )
        try:
            item = page.locator('.gt-vers[data-ref="exodus 15:1-18"]')
            citation = item.locator('.ov-naslagtekst')
            citation.locator('.osv-vers').first.wait_for(timeout=15_000)
            self.assertEqual(citation.get_attribute("lang"), "ar")
            self.assertEqual(citation.get_attribute("dir"), "rtl")
            self.assertEqual(citation.get_attribute("data-osv-editie"), "ar-vd")
            self.assertEqual(
                item.locator('.gt-vers-kop a').get_attribute("href"),
                "index.html?editie=ar-vd#exodus/15/1",
            )
        finally:
            page.close()

    def test_lied_citaat_volgt_de_geselecteerde_oekraiense_editie(self):
        page = self.open_page(
            "liederen.html?item=lied-bij-de-schelfzee",
            {"teksteditie": "uk-ukrfb"},
        )
        try:
            item = page.locator('.gt-vers[data-ref="exodus 15:1-18"]')
            citation = item.locator('.ov-naslagtekst')
            citation.locator('.osv-vers').first.wait_for(timeout=15_000)
            self.assertEqual(citation.get_attribute("lang"), "uk")
            self.assertEqual(citation.get_attribute("dir"), None)
            self.assertEqual(citation.get_attribute("data-osv-editie"), "uk-ukrfb")
            self.assertEqual(
                item.locator('.gt-vers-kop a').get_attribute("href"),
                "index.html?editie=uk-ukrfb#exodus/15/1",
            )
        finally:
            page.close()

    def test_lied_citaat_volgt_de_geselecteerde_duitse_editie(self):
        page = self.open_page(
            "liederen.html?item=lied-bij-de-schelfzee",
            {"teksteditie": "de-luther1912"},
        )
        try:
            item = page.locator('.gt-vers[data-ref="exodus 15:1-18"]')
            citation = item.locator('.ov-naslagtekst')
            citation.locator('.osv-vers').first.wait_for(timeout=15_000)
            self.assertEqual(citation.get_attribute("lang"), "de")
            self.assertEqual(citation.get_attribute("dir"), None)
            self.assertEqual(citation.get_attribute("data-osv-editie"), "de-luther1912")
            self.assertEqual(
                item.locator('.gt-vers-kop a').get_attribute("href"),
                "index.html?editie=de-luther1912#exodus/15/1",
            )
        finally:
            page.close()

    def test_lied_hergebruikt_de_gekoppelde_teksten_bediening(self):
        page = self.open_page("liederen.html?item=lied-bij-de-schelfzee")
        try:
            item = page.locator('.gt-vers[data-ref="exodus 15:1-18"]')
            item.locator(".osv-vers").first.wait_for(timeout=15_000)
            self.assertTrue(item.locator(".gt-plus").is_visible())

            item.locator(".gt-plus").click()
            self.assertEqual(item.locator(".osv-vers").count(), 20)
            self.assertTrue(item.locator(".gt-min").is_visible())
        finally:
            page.close()

    def test_alle_naslagsoorten_gebruiken_dezelfde_template_en_frameveilige_link(self):
        pages = [
            "muziekinstrumenten.html?item=citer",
            "liederen.html?item=lied-bij-de-schelfzee",
            "gebeden.html?item=abrahams-voorbede-voor-sodom",
        ]
        for path in pages:
            with self.subTest(path=path):
                page = self.open_page(path)
                try:
                    component = page.locator(".ov-naslagtekst").first
                    self.assertEqual(component.count(), 1)
                    link = page.locator(".ov-naslagtekst-link").first
                    if not link.count():
                        link = component.locator("xpath=ancestor::li[1]//a[@target='_top']").first
                    self.assertEqual(link.get_attribute("target"), "_top")
                    self.assertIn("index.html#", link.get_attribute("href"))
                    self.assertEqual(component.locator("iframe").count(), 0)
                finally:
                    page.close()

    def test_renderpaden_roepen_niet_ieder_zelf_de_embed_api_aan(self):
        for relative in ("js/naslag.js", "js/gekoppelde-teksten.js"):
            source = (ROOT / relative).read_text(encoding="utf-8")
            self.assertNotIn("OSV.cite(", source, relative)
            self.assertIn("renderNaslagtekst", source, relative)


if __name__ == "__main__":
    unittest.main()
