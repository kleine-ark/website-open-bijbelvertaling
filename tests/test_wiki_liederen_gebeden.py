"""Browsertests voor genummerde liederen, gebeden en volledige teksten."""

import contextlib
import http.server
import json
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


class WikiLiederenGebedenTest(unittest.TestCase):
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

    def open_page(self, path, viewport=None):
        page = self.browser.new_page(viewport=viewport or {"width": 1280, "height": 900})
        page.goto(f"{self.base_url}/{path}")
        page.locator("#naslag h1").wait_for(state="visible")
        return page

    def test_liederen_overzicht_is_genummerd_van_1_tot_31(self):
        page = self.open_page("liederen.html")
        try:
            labels = page.locator(".ns-kaart .ns-nummer").all_inner_texts()
            self.assertEqual(labels, [f"Lied {number}" for number in range(1, 32)])
            self.assertNotIn("Lamech", page.locator("#naslag").inner_text())
        finally:
            page.close()

    def test_gebeden_overzicht_is_genummerd_van_1_tot_45(self):
        page = self.open_page("gebeden.html")
        try:
            labels = page.locator(".ns-kaart .ns-nummer").all_inner_texts()
            self.assertEqual(labels, [f"Gebed {number}" for number in range(1, 46)])
            self.assertEqual(page.locator(".ns-lead").count(), 0)
            names = page.locator(".ns-kaart-naam").all_inner_texts()
            self.assertEqual(
                names[-3:],
                [
                    "Paulus' eerste gebed voor de gemeente in Efeze",
                    "Paulus' tweede gebed voor de gemeente in Efeze",
                    "Paulus' gebed voor de gemeente in Filippi",
                ],
            )
        finally:
            page.close()

    def test_lieddetail_toont_nummer_en_volledige_eerste_en_laatste_regel(self):
        bundle = json.loads(
            (ROOT / "data/naslag-teksten/liederen/lied-bij-de-schelfzee.json").read_text(
                encoding="utf-8"
            )
        )
        page = self.open_page("liederen.html?item=lied-bij-de-schelfzee")
        try:
            page.locator(".ns-volledige-tekst .ns-tekstvers").first.wait_for()
            self.assertEqual(page.locator(".ns-nummer").first.inner_text(), "Lied 2")
            verses = page.locator(".ns-volledige-tekst .ns-tekstvers").all_inner_texts()
            expected = bundle["passages"][0]["sections"][0]["verzen"]
            self.assertIn(expected[0]["tekst"], verses[0])
            self.assertIn(expected[-1]["tekst"], verses[-1])
        finally:
            page.close()

    def test_gebed_met_meerdere_passages_toont_alle_koppen(self):
        page = self.open_page("gebeden.html?item=mozes-voorbeden-voor-israel")
        try:
            page.locator(".ns-volledige-tekst .ns-tekstvers").first.wait_for()
            self.assertEqual(page.locator(".ns-nummer").first.inner_text(), "Gebed 3")
            self.assertEqual(
                page.locator(".ns-passage > h3").all_inner_texts(),
                ["Exodus 32:11–14", "Numeri 14:13–19"],
            )
        finally:
            page.close()

    def test_psalmenpagina_heeft_150_sprongen_en_beide_uiteinden(self):
        page = self.open_page("liederen.html?item=de-psalmen")
        try:
            page.locator("#psalm-150").wait_for(state="visible")
            self.assertEqual(page.locator(".ns-psalm-sprongen a").count(), 150)
            self.assertEqual(page.locator("#psalm-1").inner_text(), "Psalm 1")
            self.assertEqual(page.locator("#psalm-150").inner_text(), "Psalm 150")
            self.assertGreater(page.locator("#psalm-150 + .ns-tekstvers").count(), 0)
        finally:
            page.close()

    def test_niet_overgeleverde_liedwoorden_krijgen_een_eerlijke_melding(self):
        page = self.open_page("liederen.html?item=lofzang-bij-het-avondmaal")
        try:
            page.locator(".ns-tekstmelding").wait_for(state="visible")
            self.assertIn("niet overgeleverd", page.locator(".ns-tekstmelding").inner_text())
            self.assertIn("Mattheüs 26:30", page.locator("#naslag").inner_text())
        finally:
            page.close()

    def test_mislukte_tekstfetch_laat_beschrijving_en_vindplaatsen_staan(self):
        page = self.browser.new_page(viewport={"width": 1280, "height": 900})
        try:
            page.route("**/data/naslag-teksten/liederen/lied-bij-de-schelfzee.json", lambda route: route.abort())
            page.goto(f"{self.base_url}/liederen.html?item=lied-bij-de-schelfzee")
            page.locator(".ns-tekstfout").wait_for(state="visible")
            self.assertTrue(page.locator(".ns-beschrijving").is_visible())
            self.assertGreater(page.locator(".ns-vers").count(), 0)
            self.assertEqual(
                page.locator(".ns-tekstfout").inner_text(),
                "De volledige tekst kon niet geladen worden.",
            )
        finally:
            page.close()


if __name__ == "__main__":
    unittest.main()
