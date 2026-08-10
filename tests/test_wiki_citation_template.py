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
            self.assertGreater(citation.locator(".strongs-alignment").count(), 0)
            speech = citation.locator(".direct-speech").first
            self.assertIn("“", speech.evaluate("el => getComputedStyle(el, '::before').content"))
            self.assertIn("”", speech.evaluate("el => getComputedStyle(el, '::after').content"))
            self.assertNotIn("«", speech.evaluate("el => getComputedStyle(el, '::before').content"))
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
