import contextlib
import http.server
import json
import pathlib
import threading
import unittest

from playwright.sync_api import sync_playwright


ROOT = pathlib.Path(__file__).resolve().parents[1]


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


class _QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, _format, *_args):
        pass


class _QuietServer(http.server.ThreadingHTTPServer):
    def handle_error(self, _request, _client_address):
        pass


class GekoppeldeTekstenTest(unittest.TestCase):
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

    def _open_fixture(self, without_observer=False):
        page = self.browser.new_page(viewport={"width": 900, "height": 900})
        if without_observer:
            page.add_init_script("delete window.IntersectionObserver")
        page.goto(f"{self.base_url}/tests/fixtures/wiki_gekoppelde_teksten.html")
        return page

    def test_loads_main_verse_and_keeps_its_link(self):
        page = self._open_fixture()
        try:
            first = page.locator('.gt-vers[data-ref="genesis 2:11"]')
            first.locator(".osv-vers").wait_for()
            self.assertIn("goud", first.locator(".gt-vers-tekst").inner_text().lower())
            self.assertEqual(
                first.locator(".gt-vers-kop a").get_attribute("href"),
                "index.html#genesis/2/11",
            )
        finally:
            page.close()

    def test_plus_and_minus_toggle_two_verses_of_context(self):
        page = self._open_fixture()
        try:
            first = page.locator('.gt-vers[data-ref="genesis 2:11"]')
            first.locator(".osv-vers").wait_for()
            self.assertTrue(first.locator(".gt-plus").is_visible())
            self.assertFalse(first.locator(".gt-min").is_visible())

            first.locator(".gt-plus").click()
            first.locator(".osv-vers").nth(4).wait_for()
            self.assertEqual(first.locator(".osv-vers").count(), 5)
            self.assertEqual(first.locator(".focus-vers").count(), 1)
            self.assertEqual(first.locator(".context-vers").count(), 4)
            self.assertTrue(first.locator(".gt-min").is_visible())

            first.locator(".gt-min").click()
            self.assertEqual(first.locator(".osv-vers").count(), 1)
            self.assertTrue(first.locator(".gt-plus").is_visible())
        finally:
            page.close()

    def test_context_stays_inside_the_chapter(self):
        page = self._open_fixture()
        try:
            first_verse = page.locator('.gt-vers[data-ref="genesis 2:1"]')
            first_verse.locator(".osv-vers").wait_for()
            first_verse.locator(".gt-plus").click()
            first_verse.locator(".osv-vers").nth(2).wait_for()
            self.assertEqual(first_verse.locator(".osv-vers").count(), 3)
        finally:
            page.close()

    def test_invalid_reference_shows_error_but_keeps_item(self):
        page = self._open_fixture()
        try:
            invalid = page.locator('.gt-vers[data-ref="ongeldig"]')
            invalid.wait_for()
            self.assertIn("niet geladen", invalid.inner_text().lower())
            self.assertEqual(invalid.locator(".gt-vers-kop a").count(), 1)
        finally:
            page.close()

    def test_loads_immediately_without_intersection_observer(self):
        page = self._open_fixture(without_observer=True)
        try:
            page.locator('.gt-vers[data-ref="genesis 2:11"] .osv-vers').wait_for(timeout=3000)
        finally:
            page.close()

    def test_materialen_shows_all_goud_texts_as_a_list(self):
        data = read_json(ROOT / "data" / "naslag-materialen.json")
        expected = len(next(item for item in data["items"] if item["id"] == "goud")["verzen"])
        page = self.browser.new_page(viewport={"width": 900, "height": 900})
        try:
            page.goto(f"{self.base_url}/materialen.html?item=goud")
            page.locator('.gt-vers[data-ref="genesis 2:11"] .osv-vers').wait_for()
            self.assertEqual(page.locator("#naslag-gekoppelde-teksten .gt-vers").count(), expected)
            self.assertEqual(page.locator("#naslag .ns-verzen").count(), 0)
        finally:
            page.close()

    def test_dieren_and_bomen_use_the_same_text_list(self):
        cases = (
            ("dieren.html?item=vee", "data/naslag-dieren.json", "vee"),
            ("bomen-planten.html?item=de-boom-van-het-leven", "data/naslag-bomen-planten.json", "de-boom-van-het-leven"),
        )
        for address, data_path, item_id in cases:
            with self.subTest(address=address):
                data = read_json(ROOT / data_path)
                expected = len(next(item for item in data["items"] if item["id"] == item_id)["verzen"])
                page = self.browser.new_page(viewport={"width": 900, "height": 900})
                try:
                    page.goto(f"{self.base_url}/{address}")
                    page.locator("#naslag-gekoppelde-teksten .gt-vers").first.wait_for(timeout=3000)
                    self.assertEqual(
                        page.locator("#naslag-gekoppelde-teksten .gt-vers").count(),
                        expected,
                    )
                finally:
                    page.close()

    def test_personen_and_instrumenten_have_separate_pages_with_full_refs(self):
        cases = (
            ("personen.html?item=tobias-oud", "tobit 1:1", "Tobit 1:1"),
            (
                "muziekinstrumenten.html?item=citer",
                "jezussirach 39:19",
                "Jezus Sirach 39:19",
            ),
        )
        for address, verse_ref, label in cases:
            with self.subTest(address=address):
                page = self.browser.new_page(viewport={"width": 1000, "height": 900})
                try:
                    page.goto(f"{self.base_url}/{address}")
                    verse = page.locator(f'.gt-vers[data-ref="{verse_ref}"]')
                    verse.locator(".osv-vers").wait_for(timeout=5000)
                    self.assertEqual(verse.locator(".gt-vers-kop a").inner_text(), label)
                    self.assertTrue(page.locator(".ns-type-detail").is_visible())
                finally:
                    page.close()

    def test_personen_overview_can_filter_equal_names(self):
        page = self.browser.new_page(viewport={"width": 1000, "height": 900})
        try:
            page.goto(f"{self.base_url}/personen.html")
            search = page.locator("#ns-zoeken")
            search.wait_for(timeout=5000)
            search.fill("Azaria")
            self.assertEqual(page.locator(".ns-kaart:visible").count(), 2)
            self.assertEqual(
                page.locator(".ns-kaart:visible .ns-kaart-onderscheiding").count(),
                2,
            )
        finally:
            page.close()

    def test_naslag_reading_column_has_desktop_left_margin(self):
        page = self.browser.new_page(viewport={"width": 1000, "height": 900})
        try:
            page.goto(f"{self.base_url}/materialen.html?item=goud")
            page.locator("#naslag h1").wait_for()
            left = page.locator("#naslag h1").evaluate(
                "element => element.getBoundingClientRect().left"
            )
            self.assertGreaterEqual(left, 32)
        finally:
            page.close()

    def test_tijdsaanduidingen_inserts_generated_text_lists_and_counts(self):
        page = self.browser.new_page(viewport={"width": 1100, "height": 900})
        try:
            page.goto(f"{self.base_url}/tijdsaanduidingen.html")
            page.locator('.gt-detail-rij[data-voor="dag-3"] .gt-vers').first.wait_for(timeout=3000)
            self.assertEqual(
                page.locator('.gt-detail-rij[data-voor="dag-3"] .gt-vers').count(),
                3,
            )
            self.assertEqual(
                page.locator('tr[data-tijdgroep="dag-3"] .me-tel').inner_text(),
                "3×",
            )
            self.assertEqual(page.locator('.gt-detail-rij[data-voor="dag-1"]').count(), 0)
            self.assertEqual(
                page.locator('.gt-detail-rij[data-voor="morgenwake"] .gt-vers').count(),
                3,
            )
            self.assertEqual(
                page.locator('.gt-detail-rij[data-voor="tweeavonden"] .gt-vers').count(),
                11,
            )
        finally:
            page.close()

    def test_tijdsaanduidingen_text_lists_fit_a_phone(self):
        page = self.browser.new_page(viewport={"width": 390, "height": 844})
        try:
            page.goto(f"{self.base_url}/tijdsaanduidingen.html")
            page.locator('.gt-detail-rij[data-voor="dag-3"]').wait_for(timeout=3000)
            dimensions = page.evaluate(
                "({scroll: document.documentElement.scrollWidth, width: innerWidth, "
                "left: document.querySelector('.page h1').getBoundingClientRect().left})"
            )
            self.assertLessEqual(dimensions["scroll"], dimensions["width"])
            self.assertGreaterEqual(dimensions["left"], 16)
        finally:
            page.close()


if __name__ == "__main__":
    unittest.main()
