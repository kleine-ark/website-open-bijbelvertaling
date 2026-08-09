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

    def open_reader(self, width=1280, height=900, location="genesis/1"):
        page = self.browser.new_page(viewport={"width": width, "height": height})
        page.goto(f"{self.base_url}/index.html#{location}", wait_until="domcontentloaded")
        opener = "#mobile-opties-btn" if width <= 768 else "#sidebar-right-open"
        page.locator(opener).wait_for(state="visible", timeout=15_000)
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

    def test_hoofdinstellingen_gebruiken_de_aangeleverde_iconen(self):
        expected = {
            "thema.svg",
            "lettertype.svg",
            "tekstgrootte.svg",
            "regelafstand.svg",
            "versnummers.svg",
            "godsnaam.svg",
            "voorkeurseditie.svg",
            "voorleesstem.svg",
        }
        page = self.open_reader()
        try:
            page.locator("#sidebar-right-open").click()
            sources = page.locator("#sidebar-right .option-icon").evaluate_all(
                "els => els.map(el => new URL(el.src).pathname.split('/').pop())"
            )
            self.assertEqual(set(sources), expected)
            self.assertEqual(len(sources), len(expected))
            self.assertTrue(page.locator("#sidebar-right .option-icon").evaluate_all(
                "els => els.every(el => el.complete && el.naturalWidth > 0)"
            ))
        finally:
            page.close()

    def test_lettertype_en_regelafstand_worden_toegepast_en_bewaard(self):
        page = self.open_reader()
        try:
            page.wait_for_function("window.Opties && window.Opties.state")
            page.locator("#sidebar-right-open").click()
            page.locator('[data-optie="lettertype"][value="rustig"]').check()
            page.locator('[data-optie="regelafstand"][value="ruim"]').check()

            self.assertTrue(page.locator("body").evaluate(
                "el => el.classList.contains('reader-font-rustig')"
            ))
            self.assertTrue(page.locator("body").evaluate(
                "el => el.classList.contains('reader-spacing-ruim')"
            ))
            verse = page.locator("#verses-container .verse-cell.col-2026").first
            verse.wait_for(timeout=5000)
            typography = verse.evaluate(
                "el => ({font: getComputedStyle(el).fontFamily, line: parseFloat(getComputedStyle(el).lineHeight)})"
            )
            self.assertIn("Fira Sans", typography["font"])
            self.assertGreater(typography["line"], 32)
            page.wait_for_function(
                """() => {
                    const state = JSON.parse(localStorage.getItem('sv2026_vertaalopties'));
                    return state.lettertype === 'rustig' && state.regelafstand === 'ruim';
                }"""
            )

            page.reload(wait_until="domcontentloaded")
            page.wait_for_function(
                "window.Opties && window.Opties.state.lettertype === 'rustig'"
            )
            self.assertTrue(page.locator("body.reader-font-rustig.reader-spacing-ruim").count())
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

    def test_zoom_staat_in_lezen_en_niet_meer_zwevend(self):
        page = self.open_reader()
        try:
            page.locator("#sidebar-right-open").click()
            self.assertEqual(page.locator("#options-panel-lezen #options-zoom").count(), 1)
            self.assertEqual(page.locator("body > #ov-zoom").count(), 0)
        finally:
            page.close()

    def test_boekvolgorde_staat_bij_lezen_en_niet_in_de_boekenzijbalk(self):
        page = self.open_reader()
        try:
            self.assertEqual(page.locator("#sidebar #sb-boekvolgorde").count(), 0)
            page.locator("#sidebar-right-open").click()
            keuze = page.locator('#options-panel-lezen [data-optie="boekvolgorde"]')
            self.assertEqual(keuze.count(), 1)
            self.assertEqual(keuze.get_attribute("aria-label"), "Boekvolgorde")
        finally:
            page.close()

    def test_boekenzijbalk_begint_direct_met_de_eerste_boekgroep(self):
        page = self.open_reader()
        try:
            sidebar = page.locator("#sidebar")
            eerste_groep = page.locator("#sidebar-tree .tree-group").first

            self.assertEqual(page.locator("#sidebar .sidebar-left-title").count(), 0)
            self.assertEqual(page.locator("#sidebar-search").count(), 0)
            self.assertEqual(page.locator("#book-search").count(), 0)
            self.assertLessEqual(
                eerste_groep.bounding_box()["y"] - sidebar.bounding_box()["y"],
                8,
            )

            inklappen = page.locator("#sidebar-toggle")
            self.assertTrue(inklappen.is_visible())
            inklappen.click()
            self.assertTrue(sidebar.evaluate("el => el.classList.contains('collapsed')"))
        finally:
            page.close()

    def test_boekvolgorde_in_leesvoorkeuren_wordt_bewaard(self):
        page = self.open_reader()
        try:
            page.locator("#sidebar-right-open").click()
            keuze = page.locator('#options-panel-lezen [data-optie="boekvolgorde"]')
            keuze.select_option("tenach")
            page.wait_for_function(
                "JSON.parse(localStorage.getItem('sv2026_vertaalopties')).boekvolgorde === 'tenach'"
            )
            page.reload(wait_until="domcontentloaded")
            page.locator("#sidebar-right-open").wait_for(state="visible", timeout=15_000)
            page.locator("#sidebar-right-open").click()
            self.assertEqual(keuze.input_value(), "tenach")
        finally:
            page.close()

    def test_mobiele_boekenpicker_herhaalt_de_boekvolgordekeuze_niet(self):
        page = self.open_reader(width=390, height=844)
        try:
            page.locator("#mobile-book-btn").click()
            page.locator("#mobile-picker").wait_for(state="visible", timeout=3_000)
            self.assertEqual(page.locator("#mobile-picker .mp-order").count(), 0)
            self.assertEqual(page.locator("#mobile-picker .mp-search").count(), 1)
        finally:
            page.close()

    def test_zoom_blijft_bewaard_na_herladen(self):
        page = self.open_reader()
        try:
            page.locator("#sidebar-right-open").click()
            page.locator("#options-zoom-in").click()
            page.wait_for_function("localStorage.getItem('ov_zoom') === '1.1'")
            self.assertEqual(page.locator("#options-zoom-value").inner_text(), "110%")

            page.reload(wait_until="domcontentloaded")
            page.locator("#sidebar-right-open").wait_for(state="visible", timeout=15_000)
            page.locator("#sidebar-right-open").click()
            self.assertEqual(page.locator("#options-zoom-value").inner_text(), "110%")
        finally:
            page.close()

    def test_grote_getallen_kunnen_ook_in_cijfers_worden_getoond(self):
        page = self.open_reader(location="numeri/2")
        try:
            page.locator("#sidebar-right-open").click()
            page.get_by_text("Grote getallen", exact=True).click()
            cijfers = page.locator('[data-optie="getalweergave"][value="cijfers"]')
            self.assertEqual(cijfers.count(), 1)
            cijfers.check()

            verse_acht = page.locator('.verse-row[data-verse="8"] .col-2026')
            verse_acht.wait_for(state="visible", timeout=5_000)
            self.assertIn("zeven en vijftig duizend en vierhonderd", verse_acht.inner_text())
            self.assertIn("57.400", verse_acht.inner_text())
        finally:
            page.close()

    def test_desktop_paneel_is_zwevend_en_ongeveer_520_px(self):
        for width in (1440, 1000):
            with self.subTest(width=width):
                page = self.open_reader(width=width, height=900)
                try:
                    page.locator("#sidebar-right-open").click()
                    page.wait_for_timeout(250)
                    box = page.locator("#sidebar-right").bounding_box()
                    self.assertGreaterEqual(box["width"], 500)
                    self.assertLessEqual(box["width"], 540)
                    self.assertAlmostEqual(box["x"] + box["width"], width - 16, delta=1)
                finally:
                    page.close()

    def test_achtergrond_blijft_op_desktop_onvervaagd(self):
        page = self.open_reader(width=1280, height=900)
        try:
            page.locator("#sidebar-right-open").click()
            backdrop = page.locator("#sidebar-right").evaluate(
                """el => {
                    const stijl = getComputedStyle(el, '::backdrop');
                    return {
                        achtergrond: stijl.backgroundColor,
                        vervaging: stijl.backdropFilter || stijl.webkitBackdropFilter,
                    };
                }"""
            )
            self.assertEqual(backdrop["achtergrond"], "rgba(0, 0, 0, 0)")
            self.assertEqual(backdrop["vervaging"], "none")
        finally:
            page.close()

    def test_mobiel_paneel_gebruikt_de_beschikbare_breedte(self):
        for width in (768, 545, 390):
            with self.subTest(width=width):
                page = self.open_reader(width=width, height=844)
                try:
                    page.locator("#mobile-opties-btn").click()
                    page.locator("#sidebar-right").wait_for(state="visible", timeout=3_000)
                    page.wait_for_timeout(250)
                    box = page.locator("#sidebar-right").bounding_box()
                    self.assertAlmostEqual(box["x"], 0, delta=1)
                    self.assertAlmostEqual(box["width"], width, delta=1)
                finally:
                    page.close()

    def test_mobiele_darkmode_volgt_het_goedgekeurde_bottomsheet_ontwerp(self):
        page = self.open_reader(width=390, height=844)
        try:
            page.evaluate(
                """localStorage.setItem('sv2026_vertaalopties',
                JSON.stringify({thema: 'donker'}))"""
            )
            page.reload(wait_until="domcontentloaded")
            page.locator("#mobile-opties-btn").click()
            panel = page.locator("#sidebar-right")
            panel.wait_for(state="visible", timeout=3_000)
            page.wait_for_timeout(250)

            box = panel.bounding_box()
            tabs = page.locator(".options-tabs").bounding_box()
            grip = page.locator(".options-sheet-grip").bounding_box()
            title = page.locator("#options-title").bounding_box()
            style = panel.evaluate(
                """el => ({
                    background: getComputedStyle(el).backgroundColor,
                    radius: parseFloat(getComputedStyle(el).borderTopLeftRadius)
                })"""
            )

            self.assertGreater(box["y"], 100)
            self.assertLess(tabs["y"], grip["y"])
            self.assertLess(grip["y"], title["y"])
            self.assertGreaterEqual(style["radius"], 30)
            self.assertGreater(int(style["background"].split("(")[1].split(",")[0]), 230)
            self.assertEqual(
                page.locator("#options-title").evaluate(
                    "el => getComputedStyle(el).textAlign"
                ),
                "center",
            )
            self.assertFalse(
                page.locator("#options-panel-lezen .options-section-heading")
                .first.is_visible()
            )
            self.assertEqual(
                page.locator("#options-tab-lezen").evaluate(
                    "el => getComputedStyle(el).backgroundColor"
                ),
                "rgba(0, 0, 0, 0)",
            )
        finally:
            page.close()

    def test_lange_keuzerij_toont_de_actuele_waarde(self):
        page = self.open_reader()
        try:
            page.locator("#sidebar-right-open").click()
            current = page.locator('[data-option-summary="godsnaam"] .option-current')
            self.assertEqual(current.count(), 1)
            self.assertEqual(current.inner_text(), "JAHWEH / God JAHWEH")
        finally:
            page.close()

    def test_desktop_opener_heeft_een_duidelijke_toegankelijke_naam(self):
        page = self.open_reader()
        try:
            self.assertEqual(
                page.locator("#sidebar-right-open").get_attribute("aria-label"),
                "Leesvoorkeuren openen",
            )
            self.assertEqual(
                page.locator("#sidebar-right-open").evaluate(
                    "el => getComputedStyle(el).display"
                ),
                "grid",
            )
        finally:
            page.close()

    def test_escape_sluit_en_herstelt_focus_naar_de_opener(self):
        page = self.open_reader()
        try:
            opener = page.locator("#sidebar-right-open")
            opener.click()
            page.keyboard.press("Escape")
            self.assertFalse(page.locator("#sidebar-right").evaluate("el => el.open"))
            self.assertEqual(page.evaluate("document.activeElement.id"), "sidebar-right-open")
        finally:
            page.close()

    def test_pijltjestoets_wisselt_tab_en_zichtbaar_paneel(self):
        page = self.open_reader()
        try:
            page.locator("#sidebar-right-open").click()
            page.locator("#options-tab-lezen").focus()
            page.keyboard.press("ArrowRight")
            self.assertEqual(
                page.locator('[role="tab"][aria-selected="true"]').text_content().strip(),
                "Vergelijken",
            )
            self.assertTrue(page.locator("#options-panel-vergelijken").is_visible())
            self.assertFalse(page.locator("#options-panel-lezen").is_visible())
        finally:
            page.close()

    def test_klik_op_verduisterde_achtergrond_sluit_het_paneel(self):
        page = self.open_reader(width=1440, height=900)
        try:
            page.locator("#sidebar-right-open").click()
            page.wait_for_timeout(250)
            page.mouse.click(100, 450)
            self.assertFalse(page.locator("#sidebar-right").evaluate("el => el.open"))
        finally:
            page.close()


if __name__ == "__main__":
    unittest.main()
