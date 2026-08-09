"""Browserverificatie voor de gedeelde onderwerpenervaring."""

import contextlib
import http.server
import json
from pathlib import Path
import re
import threading
import unittest

from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[1]


def test_alle_onderwerpverwijzingen_bestaan_in_de_bijbeldata():
    tags = []
    for relative in ("data/tags.json", "data/spreker-tags.json"):
        tags.extend(json.loads((ROOT / relative).read_text(encoding="utf-8"))["tags"])

    assert len({tag["id"] for tag in tags}) == len(tags)
    hoofdstukken = {}
    for tag in tags:
        for item in tag.get("verzen", []):
            ref = item if isinstance(item, str) else item["ref"]
            match = re.fullmatch(r"(.+) (\d+):(\d+)", ref)
            assert match, (tag["id"], ref)
            boek, hoofdstuk, vers = match.group(1), int(match.group(2)), int(match.group(3))
            key = (boek, hoofdstuk)
            if key not in hoofdstukken:
                pad = ROOT / "data" / boek / f"{hoofdstuk}.json"
                assert pad.exists(), (tag["id"], ref)
                hoofdstukken[key] = json.loads(pad.read_text(encoding="utf-8"))
            assert vers in {
                int(item["number"]) for item in hoofdstukken[key]["verses"]
            }, (tag["id"], ref)


class _QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, _format, *_args):
        pass


class _QuietServer(http.server.ThreadingHTTPServer):
    def handle_error(self, _request, _client_address):
        pass


class OnderwerpenErvaringTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        handler = lambda *args, **kwargs: _QuietHandler(
            *args, directory=str(ROOT), **kwargs
        )
        cls.server = _QuietServer(("127.0.0.1", 0), handler)
        cls.server_thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.server_thread.start()
        cls.playwright = sync_playwright().start()
        edge = Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe")
        options = {"headless": True}
        if edge.exists():
            options["executable_path"] = str(edge)
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

    def open_page(self, hash_value="", width=1280):
        page = self.browser.new_page(viewport={"width": width, "height": 900})
        page.goto(f"{self.base_url}/onderwerpen.html{hash_value}")
        return page

    def test_overzicht_geeft_orientatie_en_plaatst_sprekers_lager(self):
        page = self.open_page()
        try:
            page.locator(".ond-card").first.wait_for(state="visible")
            self.assertGreater(int(page.locator("#ond-topic-count").inner_text()), 20)
            self.assertGreater(int(page.locator("#ond-text-count").inner_text()), 0)
            headings = page.locator(".ond-cat-titel").all_inner_texts()
            self.assertNotEqual(headings[0].splitlines()[0], "Wie spreekt er in Gods Woord?")
            self.assertIn("Wie spreekt er in Gods Woord?", " ".join(headings))
            self.assertNotIn("Overige onderwerpen", " ".join(headings))
        finally:
            page.close()

    def test_groot_onderwerp_is_gepagineerd_en_op_boek_te_filteren(self):
        page = self.open_page("#tag=engelen")
        try:
            page.locator("#ond-detail.ond-detail-active").wait_for(state="visible")
            self.assertEqual(page.locator(".ond-vers").count(), 24)
            self.assertTrue(page.locator("#ond-meer").is_visible())
            self.assertGreater(page.locator("#ond-boekfilter option").count(), 10)
            page.locator("#ond-meer").click()
            self.assertEqual(page.locator(".ond-vers").count(), 48)

            page.locator("#ond-boekfilter").select_option("genesis")
            self.assertGreater(page.locator(".ond-vers").count(), 0)
            self.assertTrue(
                all(
                    ref.startswith("genesis ")
                    for ref in page.locator(".ond-vers").evaluate_all(
                        "els => els.map(el => el.dataset.ref)"
                    )
                )
            )
        finally:
            page.close()

    def test_citaten_volgen_de_globale_godsnaamoptie(self):
        page = self.browser.new_page(viewport={"width": 1000, "height": 900})
        page.add_init_script(
            """
            localStorage.setItem('sv2026_vertaalopties', JSON.stringify({
                godsnaam: 'klassiek', thema: 'licht'
            }));
            """
        )
        try:
            page.goto(f"{self.base_url}/onderwerpen.html#tag=jahweh-schepping")
            first = page.locator(".ond-vers-tekst .osv-vers").first
            first.wait_for(state="visible")
            self.assertIn("HEERE", first.inner_text())
            self.assertNotIn("JAHWEH", first.inner_text())
        finally:
            page.close()

    def test_browsergeschiedenis_herstelt_het_overzicht(self):
        page = self.open_page()
        try:
            page.locator(".ond-card").first.click()
            page.locator("#ond-detail.ond-detail-active").wait_for(state="visible")
            page.go_back()
            page.locator("#ond-grid").wait_for(state="visible")
            self.assertTrue(page.locator(".ond-card").first.is_visible())
        finally:
            page.close()

    def test_contextknoppen_en_themawissel_werken_eenmaal(self):
        page = self.open_page("#tag=schepping")
        try:
            page.locator(".ond-vers").first.wait_for(state="visible")
            self.assertTrue(page.locator(".ond-vers .ctx-min").first.is_hidden())
            page.locator(".ond-vers .ctx-plus").first.click()
            self.assertTrue(page.locator(".ond-vers .ctx-min").first.is_visible())

            page.locator("#topnav-theme-toggle").click()
            page.wait_for_function(
                "document.documentElement.dataset.theme === 'donker'"
            )
            self.assertEqual(
                page.evaluate(
                    "JSON.parse(localStorage.getItem('sv2026_vertaalopties')).thema"
                ),
                "donker",
            )
        finally:
            page.close()


if __name__ == "__main__":
    unittest.main()
