"""Browserverificatie van het responsieve optiespaneel."""

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


class OptionsPanelBrowserTests(unittest.TestCase):
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

    def open_reader(self, width=1280, height=900):
        page = self.browser.new_page(viewport={"width": width, "height": height})
        page.goto(f"{self.base_url}/index.html#genesis/1", wait_until="domcontentloaded")
        page.locator("#sidebar-right-open").wait_for(state="visible", timeout=15_000)
        return page

    def test_opties_opent_modaal_zonder_de_leestekst_te_versmallen(self):
        page = self.open_reader()
        try:
            content = page.locator("#content")
            before = content.bounding_box()["width"]
            page.locator("#sidebar-right-open").click()
            dialog_is_open = page.locator("#sidebar-right").evaluate(
                "el => el instanceof HTMLDialogElement && el.open"
            )
            after = content.bounding_box()["width"]

            self.assertTrue(dialog_is_open)
            self.assertAlmostEqual(after, before, delta=1)
        finally:
            page.close()

    def test_opties_heeft_drie_toegankelijke_tabs(self):
        page = self.open_reader()
        try:
            page.locator("#sidebar-right-open").click()
            self.assertEqual(
                page.get_by_role("tab").all_text_contents(),
                ["Lezen", "Vergelijken", "Onderzoeken"],
            )
        finally:
            page.close()

    def test_bestaande_controls_staan_in_het_juiste_tabblad(self):
        expected_tab = {
            "toggle-versnummers": "lezen",
            "toggle-citaten": "lezen",
            "toggle-doorlopend": "lezen",
            "opt-audio-speed": "lezen",
            "toggle-kt-popup": "vergelijken",
            "toggle-tags": "onderzoeken",
            "toggle-hs-vers": "onderzoeken",
        }
        page = self.open_reader()
        try:
            for control_id, tab in expected_tab.items():
                with self.subTest(control=control_id):
                    self.assertEqual(
                        page.locator(f"#options-panel-{tab} #{control_id}").count(),
                        1,
                    )
        finally:
            page.close()

    def test_datawaarden_blijven_compatibel_met_bestaande_voorkeuren(self):
        page = self.open_reader()
        try:
            godsnaam_values = page.locator('[data-optie="godsnaam"]').evaluate_all(
                "els => els.map(el => el.value)"
            )
            column_values = page.locator("[data-toggle-col]").evaluate_all(
                "els => els.map(el => el.dataset.toggleCol)"
            )
            self.assertEqual(
                godsnaam_values,
                ["ov", "klassiek", "jehovah", "jhwh"],
            )
            self.assertEqual(
                set(column_values),
                {
                    "1637",
                    "sv1888",
                    "2026",
                    "margin1637",
                    "marginSV1888",
                    "margin2026",
                    "hebrew",
                    "diff",
                    "noteDiff",
                },
            )
        finally:
            page.close()

    def test_vertaalkeuze_blijft_bewaard_na_herladen(self):
        page = self.open_reader()
        try:
            page.wait_for_function(
                "window.Opties && window.Opties.state && window.Opties.state.godsnaam"
            )
            page.locator("#sidebar-right-open").click()
            page.get_by_text("Godsnaam in het Oude Testament", exact=True).click()
            klassiek = page.locator('[data-optie="godsnaam"][value="klassiek"]')
            klassiek.check()
            page.wait_for_function(
                "JSON.parse(localStorage.getItem('sv2026_vertaalopties')).godsnaam === 'klassiek'"
            )

            page.reload(wait_until="domcontentloaded")
            page.wait_for_function(
                "window.Opties && window.Opties.state.godsnaam === 'klassiek'"
            )
            self.assertTrue(klassiek.is_checked())
        finally:
            page.close()


if __name__ == "__main__":
    unittest.main()
