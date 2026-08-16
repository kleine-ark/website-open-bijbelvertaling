"""Regressietests voor het compacte, sectiegewijze optiescherm."""

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


class OptionsRedesignTests(unittest.TestCase):
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

    def open_reader(self, width=390, height=844):
        page = self.browser.new_page(viewport={"width": width, "height": height})
        page.goto(f"{self.base_url}/index.html#genesis/1", wait_until="domcontentloaded")
        if width <= 768:
            page.locator("#topnav-hamburger").click()
            page.locator("#topnav-mobile-tekstopties").click()
        else:
            page.locator("#topnav-tekstopties").click()
        page.locator("#sidebar-right").wait_for(state="visible")
        return page

    def test_geen_hoofdtabs_en_vijf_inklapbare_categorieen(self):
        page = self.open_reader(width=1280)
        try:
            self.assertEqual(page.locator('#sidebar-right [role="tab"]').count(), 0)
            self.assertEqual(
                page.locator("#sidebar-right > .options-body > details.options-category > summary").all_text_contents(),
                ["Meest gebruikt", "Vertalingen, talen & kanttekeningen", "Weergave", "Theologie", "Voorlezen"],
            )
            self.assertTrue(page.locator("details.options-category").first.get_attribute("open") is not None)
        finally:
            page.close()

    def test_mobiel_is_drie_kwart_hoge_bottom_sheet_met_sluitkruis(self):
        page = self.open_reader()
        try:
            box = page.locator("#sidebar-right").bounding_box()
            self.assertAlmostEqual(box["x"], 0, delta=1)
            self.assertAlmostEqual(box["y"], 211, delta=2)
            self.assertAlmostEqual(box["width"], 390, delta=1)
            self.assertAlmostEqual(box["height"], 633, delta=2)
            self.assertTrue(page.locator("#sidebar-right-toggle").is_visible())
            self.assertEqual(page.locator("#sidebar-right-toggle").get_attribute("aria-label"), "Opties sluiten")
        finally:
            page.close()

    def test_defaults_en_geografie_schakelaar(self):
        page = self.open_reader(width=1280)
        try:
            page.wait_for_function("window.Opties && window.Opties.state")
            defaults = page.evaluate("Opties.state")
            self.assertEqual(defaults["thema"], "auto")
            self.assertEqual(defaults["godsnaam"], "ov")
            self.assertEqual(defaults["heereNT"], "heere")
            self.assertEqual(defaults["otSheol"], "dodenrijk")
            self.assertEqual(defaults["citaten"], "aan")
            self.assertEqual(defaults["versnummers"], "aan")
            self.assertEqual(defaults["apocriefeBoeken"], "aan")
            self.assertEqual(defaults["ethiopischeBoeken"], "uit")
            geo = page.locator('input[type="checkbox"][data-optie="geoMarkeren"]')
            self.assertEqual(geo.count(), 1)
            self.assertFalse(geo.is_checked())
        finally:
            page.close()

    def test_instelingen_zoeken_en_boekzichtbaarheid_zijn_globale_theologieopties(self):
        page = self.open_reader(width=1280)
        try:
            self.assertEqual(page.locator("#options-title").inner_text(), "Instellingen")
            search = page.locator("#options-search")
            self.assertEqual(search.get_attribute("placeholder"), "Zoek een instelling")

            search.fill("Ethiopische boeken")
            theology = page.locator('details[data-options-category="theologie"]')
            self.assertTrue(theology.is_visible())
            self.assertTrue(theology.get_attribute("open") is not None)
            self.assertEqual(page.locator('#toggle-ethiopische-boeken').count(), 1)
            self.assertTrue(page.locator('#toggle-apocriefe-boeken').is_checked())
            self.assertFalse(page.locator('#toggle-ethiopische-boeken').is_checked())

            page.locator('#toggle-ethiopische-boeken').check()
            page.wait_for_function("Opties.state.ethiopischeBoeken === 'aan'")
            page.wait_for_function("document.querySelector('[data-book-id=\"henoch\"]') !== null")
            self.assertGreater(page.locator('[data-book-id="henoch"]').count(), 0)

            page.locator('#toggle-apocriefe-boeken').uncheck()
            page.wait_for_function("Opties.state.apocriefeBoeken === 'uit'")
            page.wait_for_function("document.querySelector('[data-book-id=\"tobit\"]') === null")
            self.assertEqual(page.locator('[data-book-id="tobit"]').count(), 0)
        finally:
            page.close()

    def test_taalkeuze_bewaart_en_activeert_de_editie(self):
        page = self.open_reader(width=1280)
        try:
            section = page.locator('details.options-category[data-options-category="bronnen"]')
            section.locator("summary").click()
            page.locator("#opt-teksteditie").select_option("fr-lsg1910")
            page.wait_for_function(
                "JSON.parse(localStorage.getItem('sv2026_vertaalopties')).teksteditie === 'fr-lsg1910'"
            )
            self.assertIn("editie=fr-lsg1910", page.url)
            self.assertEqual(page.evaluate("TekstEditie.code()"), "fr-lsg1910")
        finally:
            page.close()

    def test_categorieen_bevatten_de_gevraagde_hoofdopties_en_spiegels(self):
        page = self.open_reader(width=1280)
        try:
            def labels(key):
                return set(page.locator(
                    f'details[data-options-category="{key}"] > .options-list > *'
                ).evaluate_all(
                    """rows => rows.map(row => {
                        const label = row.querySelector('strong') ||
                            row.querySelector('summary .option-label-with-icon > span:last-child') ||
                            row.querySelector('legend .option-label-with-icon > span:last-child');
                        return label ? label.textContent.trim() : '';
                    })"""
                ))

            self.assertTrue({
                "Dyslexiemodus", "Doorlopend lezen", "Godsnaam in het Oude Testament",
                "Thema", "Regelafstand", "Namen van personen", "Strong- en woordnummers",
                "Verschillen SV–OV",
            }.issubset(labels("meest-gebruikt")))
            self.assertTrue({
                "Dyslexiemodus", "Citaatopmaak", "Doorlopend lezen", "Versnummers",
                "Hoofdstuknummers", "Alternatief lettertype", "Thema", "Regelafstand",
            }.issubset(labels("weergave")))
            self.assertIn("Strong- en woordnummers", labels("bronnen"))
            self.assertTrue({
                "Godsnaam in het Oude Testament", "Namen van personen",
            }.issubset(labels("theologie")))

            duplicate_ids = page.locator("[id]").evaluate_all(
                "els => els.map(el => el.id).filter((id, i, ids) => ids.indexOf(id) !== i)"
            )
            self.assertEqual(duplicate_ids, [])
        finally:
            page.close()

    def test_spiegelcontrols_synchroniseren_direct_en_blijven_bewaard(self):
        page = self.open_reader(width=1280)
        try:
            most = page.locator('details[data-options-category="meest-gebruikt"]')
            view = page.locator('details[data-options-category="weergave"]')
            theology = page.locator('details[data-options-category="theologie"]')
            sources = page.locator('details[data-options-category="bronnen"]')
            for category in (view, theology, sources):
                category.locator("summary").first.click()

            mirror_dyslexia = most.locator('[data-option-mirror="dyslexie"] input')
            primary_dyslexia = view.locator("#toggle-dyslexia")
            mirror_dyslexia.check()
            self.assertTrue(primary_dyslexia.is_checked())
            self.assertEqual(page.evaluate("localStorage.getItem('dyslexia')"), "true")

            mirror_theme = most.locator('[data-option-mirror="thema"] select')
            primary_theme = view.locator('select[data-optie="thema"]')
            mirror_theme.select_option("donker")
            self.assertEqual(primary_theme.input_value(), "donker")
            self.assertEqual(page.evaluate("Opties.state.thema"), "donker")

            mirror_spacing = most.locator('[data-option-mirror="regelafstand"] input')
            primary_spacing = view.locator("#opt-regelafstand")
            mirror_spacing.fill("2")
            mirror_spacing.dispatch_event("change")
            self.assertEqual(primary_spacing.input_value(), "2")

            primary_arabic = theology.locator('[data-optie="arabischeNamen"][value="aan"]')
            mirror_arabic = most.locator('[data-option-mirror="arabische-namen"] input[value="aan"]')
            primary_arabic.locator("xpath=ancestor::details[1]/summary").click()
            primary_arabic.check()
            self.assertTrue(mirror_arabic.is_checked())
            self.assertEqual(page.evaluate("Opties.state.arabischeNamen"), "aan")

            mirror_strongs = most.locator('[data-option-mirror="strongs"] input')
            primary_strongs = sources.locator("#toggle-strongs")
            mirror_strongs.check()
            self.assertTrue(primary_strongs.is_checked())
            self.assertEqual(page.evaluate("Opties.state.strongs"), "aan")
        finally:
            page.close()


if __name__ == "__main__":
    unittest.main()
