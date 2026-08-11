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

    def test_opties_heeft_inklapbare_categorieen_in_plaats_van_tabs(self):
        page = self.open_reader()
        try:
            page.locator("#sidebar-right-open").click()
            self.assertEqual(page.get_by_role("tab").count(), 0)
            self.assertEqual(page.locator("details.options-category").count(), 5)
        finally:
            page.close()

    def test_hoofdinstellingen_gebruiken_de_aangeleverde_iconen(self):
        expected = {
            "thema.png",
            "lettertype.png",
            "tekstgrootte.png",
            "regelafstand.png",
            "versnummers.png",
            "godsnaam.png",
            "voorkeurseditie.png",
            "voorleesstem.png",
        }
        page = self.open_reader()
        try:
            page.locator("#sidebar-right-open").click()
            sources = page.locator("#sidebar-right .options-list > :not(.option-mirror) .option-icon").evaluate_all(
                "els => els.map(el => new URL(el.src).pathname.split('/').pop())"
            )
            self.assertTrue(expected.issubset(set(sources)))
            self.assertTrue(page.locator("#sidebar-right .options-list > :not(.option-mirror) .option-icon").evaluate_all(
                "els => els.every(el => el.complete && el.naturalWidth > 0)"
            ))
        finally:
            page.close()

    def test_iedere_zichtbare_instelling_heeft_een_eigen_icoon(self):
        expected = {
            "thema.png", "lettertype.png", "tekstgrootte.png", "regelafstand.png",
            "versnummers.png", "godsnaam.png", "voorkeurseditie.png", "voorleesstem.png",
            "boekinleiding.png", "hoofdstukinleiding.png", "dyslexiemodus.png",
            "citaatopmaak.png", "hoofdstuknummers.png", "perikoopkopjes.png",
            "doorlopend-lezen.png", "boekvolgorde.png", "aanspreektitel-nt.png",
            "sheol.png", "namen-personen.png", "naam-jezus.png",
            "maten-gewichten.png", "grote-getallen.png", "tijdsaanduidingen.png",
            "afspeelsnelheid.png", "kanttekeningen.png", "extra-kolommen.png",
            "vergelijkingsedities.png",
            "verschillen-vertalingen.png", "verschillen-kanttekeningen.png",
            "grondtalen.png", "oudste-handschrift.png", "onderwerptags.png",
            "geografische-locaties.png", "strong-nummers.png",
        }
        page = self.open_reader()
        try:
            page.locator("#sidebar-right-open").click()
            sources = page.locator("#sidebar-right .options-list > :not(.option-mirror) .option-icon").evaluate_all(
                "els => els.map(el => new URL(el.src).pathname.split('/').pop())"
            )
            self.assertEqual(set(sources), expected)
            self.assertEqual(len(sources), len(expected))
            self.assertTrue(page.locator("#sidebar-right .options-list > :not(.option-mirror) .option-icon").evaluate_all(
                "els => els.every(el => el.complete && el.naturalWidth > 0)"
            ))
        finally:
            page.close()

    def test_ieder_instellingenblok_heeft_exact_een_rastericoon(self):
        page = self.open_reader()
        try:
            page.locator("#sidebar-right-open").click()
            instellingen = page.locator(
                "#sidebar-right .options-list > .option-row, "
                "#sidebar-right .options-list > .option-choice"
            )
            self.assertGreater(instellingen.count(), 30)
            for index in range(instellingen.count()):
                with self.subTest(index=index):
                    blok = instellingen.nth(index)
                    self.assertEqual(blok.locator(":scope .option-icon").count(), 1)
                    bron = blok.locator(":scope .option-icon").get_attribute("src")
                    self.assertTrue(bron.endswith(".png"), bron)

            self.assertEqual(
                page.locator("#sidebar-right .options-section-icon").count(),
                0,
                "Sectiekoppen mogen geen teksttekens als pseudo-iconen gebruiken",
            )
        finally:
            page.close()

    def test_desktop_is_compact_en_mobiel_houdt_aanraakdoelen(self):
        page = self.open_reader(width=1280, height=900)
        try:
            page.locator("#sidebar-right-open").click()
            maten = page.locator("#sidebar-right").evaluate(
                """panel => {
                    const row = panel.querySelector('.option-row');
                    const heading = panel.querySelector('.options-category > summary');
                    const body = panel.querySelector('.options-body');
                    return {
                        rowMinHeight: parseFloat(getComputedStyle(row).minHeight),
                        rowPaddingTop: parseFloat(getComputedStyle(row).paddingTop),
                        headingHeight: parseFloat(getComputedStyle(heading).minHeight),
                        bodyPaddingTop: parseFloat(getComputedStyle(body).paddingTop),
                    };
                }"""
            )
            self.assertLessEqual(maten["rowMinHeight"], 50)
            self.assertLessEqual(maten["rowPaddingTop"], 7)
            self.assertLessEqual(maten["headingHeight"], 52)
            self.assertLessEqual(maten["bodyPaddingTop"], 14)
        finally:
            page.close()

        page = self.open_reader(width=390, height=844)
        try:
            page.locator("#mobile-opties-btn").click()
            page.locator("#sidebar-right").wait_for(state="visible", timeout=3_000)
            self.assertGreaterEqual(
                page.locator("#sidebar-right .option-row").first.evaluate(
                    "el => parseFloat(getComputedStyle(el).minHeight)"
                ),
                44,
            )
            page.locator('details[data-options-category="bronnen"] > summary').click()
            self.assertGreaterEqual(
                page.locator('details[data-options-category="bronnen"] .option-choice-inline label')
                .first.evaluate("el => parseFloat(getComputedStyle(el).minHeight)"),
                44,
            )
        finally:
            page.close()

    def test_lettertype_en_regelafstand_worden_toegepast_en_bewaard(self):
        page = self.open_reader()
        try:
            page.wait_for_function("window.Opties && window.Opties.state")
            page.locator("#sidebar-right-open").click()
            page.locator('details[data-options-category="weergave"] > summary').click()
            page.locator('#toggle-lettertype-alternatief').check()
            page.locator('#opt-regelafstand').fill("2")
            page.locator('#opt-regelafstand').dispatch_event("change")

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

    def test_bestaande_controls_staan_in_de_juiste_categorie(self):
        expected_category = {
            "toggle-versnummers": "weergave",
            "toggle-citaten": "weergave",
            "toggle-doorlopend": "weergave",
            "opt-audio-speed": "voorlezen",
            "toggle-kt-popup": "bronnen",
            "toggle-tags": "bronnen",
            "toggle-hs-vers": "bronnen",
        }
        page = self.open_reader()
        try:
            for control_id, category in expected_category.items():
                with self.subTest(control=control_id):
                    self.assertEqual(
                        page.locator(f'details[data-options-category="{category}"] #{control_id}').count(),
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
            theology = page.locator('details[data-options-category="theologie"]')
            theology.locator(":scope > summary").click()
            godsnaam = theology.locator('[data-option-summary="godsnaam"]')
            godsnaam.locator(":scope > summary").click()
            klassiek = godsnaam.locator('[data-optie="godsnaam"][value="klassiek"]')
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

    def test_zoom_staat_in_weergave_en_niet_meer_zwevend(self):
        page = self.open_reader()
        try:
            page.locator("#sidebar-right-open").click()
            self.assertEqual(page.locator('details[data-options-category="weergave"] #options-zoom').count(), 1)
            self.assertEqual(page.locator("body > #ov-zoom").count(), 0)
        finally:
            page.close()

    def test_boekvolgorde_staat_bij_theologie_en_niet_in_de_boekenzijbalk(self):
        page = self.open_reader()
        try:
            self.assertEqual(page.locator("#sidebar #sb-boekvolgorde").count(), 0)
            page.locator("#sidebar-right-open").click()
            keuze = page.locator('details[data-options-category="theologie"] [data-optie="boekvolgorde"]')
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
            page.locator('details[data-options-category="theologie"] > summary').click()
            keuze = page.locator('details[data-options-category="theologie"] [data-optie="boekvolgorde"]')
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
            page.locator('details[data-options-category="weergave"] > summary').click()
            page.locator("#options-zoom-in").click()
            page.wait_for_function("localStorage.getItem('ov_zoom') === '1.1'")
            self.assertEqual(page.locator("#options-zoom-value").inner_text(), "110%")

            page.reload(wait_until="domcontentloaded")
            page.locator("#sidebar-right-open").wait_for(state="visible", timeout=15_000)
            page.locator("#sidebar-right-open").click()
            page.locator('details[data-options-category="weergave"] > summary').click()
            self.assertEqual(page.locator("#options-zoom-value").inner_text(), "110%")
        finally:
            page.close()

    def test_grote_getallen_kunnen_ook_in_cijfers_worden_getoond(self):
        page = self.open_reader(location="numeri/2")
        try:
            page.locator("#sidebar-right-open").click()
            page.locator('details[data-options-category="theologie"] > summary').click()
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

    def test_desktop_paneel_is_via_de_kop_versleepbaar_en_bewaart_de_positie(self):
        page = self.open_reader(width=1280, height=900)
        try:
            page.locator("#sidebar-right-open").click()
            panel = page.locator("#sidebar-right")
            header = page.locator("#sidebar-right-header")
            begin = panel.bounding_box()
            kop = header.bounding_box()

            page.mouse.move(kop["x"] + 180, kop["y"] + kop["height"] - 22)
            page.mouse.down()
            page.mouse.move(kop["x"] + 30, kop["y"] + 120, steps=8)
            page.mouse.up()

            verplaatst = panel.bounding_box()
            self.assertLess(verplaatst["x"], begin["x"] - 100)
            opgeslagen = page.evaluate(
                "JSON.parse(localStorage.getItem('ov_options_panel_position'))"
            )
            self.assertAlmostEqual(opgeslagen["x"], verplaatst["x"], delta=2)
            self.assertAlmostEqual(opgeslagen["y"], verplaatst["y"], delta=2)

            panel.locator("#sidebar-right-toggle").click()
            page.locator("#sidebar-right-open").click()
            heropend = panel.bounding_box()
            self.assertAlmostEqual(heropend["x"], verplaatst["x"], delta=2)
            self.assertAlmostEqual(heropend["y"], verplaatst["y"], delta=2)
        finally:
            page.close()

    def test_desktop_sleepbeweging_blijft_binnen_de_viewport(self):
        page = self.open_reader(width=1000, height=700)
        try:
            page.locator("#sidebar-right-open").click()
            panel = page.locator("#sidebar-right")
            header = page.locator("#sidebar-right-header")
            kop = header.bounding_box()

            page.mouse.move(kop["x"] + 180, kop["y"] + kop["height"] - 22)
            page.mouse.down()
            page.mouse.move(-500, -500, steps=5)
            page.mouse.up()
            linksboven = panel.bounding_box()
            self.assertGreaterEqual(linksboven["x"], 15)
            self.assertGreaterEqual(linksboven["y"], 15)

            kop = header.bounding_box()
            page.mouse.move(kop["x"] + 180, kop["y"] + kop["height"] - 22)
            page.mouse.down()
            page.mouse.move(2000, 1500, steps=5)
            page.mouse.up()
            rechtsonder = panel.bounding_box()
            self.assertLessEqual(rechtsonder["x"] + rechtsonder["width"], 985)
            self.assertLessEqual(rechtsonder["y"] + rechtsonder["height"], 685)
        finally:
            page.close()

    def test_mobiel_negeert_een_opgeslagen_desktoppositie(self):
        page = self.open_reader(width=390, height=844)
        try:
            page.evaluate(
                "localStorage.setItem('ov_options_panel_position', JSON.stringify({x: 240, y: 40}))"
            )
            page.locator("#mobile-opties-btn").click()
            panel = page.locator("#sidebar-right")
            panel.wait_for(state="visible", timeout=3_000)
            box = panel.bounding_box()
            self.assertAlmostEqual(box["x"], 0, delta=1)
            self.assertAlmostEqual(box["width"], 390, delta=1)
            self.assertAlmostEqual(box["y"], 0, delta=1)
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

    def test_mobiele_darkmode_blijft_een_helder_schermvullend_optiescherm(self):
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
            style = panel.evaluate(
                """el => ({
                    background: getComputedStyle(el).backgroundColor,
                    radius: parseFloat(getComputedStyle(el).borderTopLeftRadius)
                })"""
            )

            self.assertAlmostEqual(box["y"], 0, delta=1)
            self.assertAlmostEqual(box["height"], 844, delta=1)
            self.assertEqual(style["radius"], 0)
            self.assertGreater(int(style["background"].split("(")[1].split(",")[0]), 230)
            self.assertEqual(page.locator("#options-title").count(), 0)
            self.assertEqual(page.locator(".options-preview").count(), 0)
            self.assertEqual(page.locator("details.options-category").count(), 5)
        finally:
            page.close()

    def test_compacte_kop_en_eenregelige_keuzes(self):
        page = self.open_reader()
        try:
            page.locator("#sidebar-right-open").click()
            panel = page.locator("#sidebar-right")
            self.assertEqual(panel.get_attribute("aria-label"), "Opties")
            self.assertEqual(panel.locator("#options-title").count(), 0)
            self.assertEqual(panel.locator(".options-preview").count(), 0)

            weergave = panel.locator('details[data-options-category="weergave"]')
            weergave.locator(":scope > summary").click()
            self.assertEqual(weergave.locator('select[data-optie="thema"]').count(), 1)
            self.assertEqual(weergave.locator('input[data-optie="thema"]').count(), 0)
            self.assertEqual(weergave.locator("#toggle-lettertype-alternatief").count(), 1)

            primary_rows = weergave.locator(":scope > .options-list > :not(.option-mirror)")
            self.assertEqual(primary_rows.last.locator("#toggle-dyslexia").count(), 1)
            self.assertEqual(weergave.locator("#toggle-dyslexia").locator("xpath=ancestor::label[1]").locator("small").count(), 0)

            bronnen = panel.locator('details[data-options-category="bronnen"]')
            bronnen.locator(":scope > summary").click()
            self.assertEqual(bronnen.locator("#toggle-strongs").locator("xpath=ancestor::label[1]").locator("small").count(), 0)

            most = panel.locator('details[data-options-category="meest-gebruikt"]')
            self.assertEqual(most.locator('[data-option-mirror="regelafstand"] input[type="range"]').count(), 1)
        finally:
            page.close()

    def test_lange_keuzerij_toont_de_actuele_waarde(self):
        page = self.open_reader()
        try:
            page.locator("#sidebar-right-open").click()
            current = page.locator('[data-option-mirror="godsnaam"] .option-current')
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

    def test_enter_klapt_een_categorie_open(self):
        page = self.open_reader()
        try:
            page.locator("#sidebar-right-open").click()
            category = page.locator('details[data-options-category="weergave"]')
            category.locator("summary").focus()
            page.keyboard.press("Enter")
            self.assertTrue(category.get_attribute("open") is not None)
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
