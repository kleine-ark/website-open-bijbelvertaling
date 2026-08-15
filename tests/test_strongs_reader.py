"""Browser- en datacontracten voor bronvaste Strong-verwijzingen."""

import contextlib
import hashlib
import http.server
import json
from pathlib import Path
import tempfile
import threading
import unittest
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from audit_woordnummers import audit
from import_inline_woordnummers import apply_review_file, parse_usj

from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[1]


class _QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, _format, *_args):
        pass


class _QuietServer(http.server.ThreadingHTTPServer):
    def handle_error(self, _request, _client_address):
        pass


class StrongsReaderBrowserTests(unittest.TestCase):
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

    def open_reader(self, location="genesis/1", width=1280, height=900):
        page = self.browser.new_page(viewport={"width": width, "height": height})
        page.goto(f"{self.base_url}/index.html#{location}", wait_until="domcontentloaded")
        page.locator('.verse-row[data-verse="1"]').wait_for(timeout=15_000)
        return page

    def enable_strongs(self, page, expect_inline=True):
        if page.viewport_size["width"] <= 768:
            page.locator("#topnav-hamburger").click()
            page.locator("#topnav-mobile-tekstopties").click()
        else:
            page.locator("#topnav-tekstopties").click()
        page.locator('details[data-options-category="bronnen"] > summary').click()
        page.locator("#toggle-strongs").check()
        page.locator("#sidebar-right-toggle").click()
        if expect_inline:
            page.locator('.verse-row[data-verse="1"] .col-2026 .strongs-inline').first.wait_for(timeout=5_000)

    def test_strongs_voorkeur_staat_standaard_uit_en_wordt_bewaard(self):
        page = self.open_reader()
        try:
            page.locator("#topnav-tekstopties").click()
            page.locator('details[data-options-category="bronnen"] > summary').click()
            toggle = page.locator("#toggle-strongs")
            self.assertFalse(toggle.is_checked())
            toggle.check()
            page.wait_for_function(
                "JSON.parse(localStorage.getItem('sv2026_vertaalopties')).strongs === 'aan'"
            )
            page.reload(wait_until="domcontentloaded")
            page.locator("#topnav-tekstopties").wait_for(state="visible", timeout=15_000)
            page.locator("#topnav-tekstopties").click()
            page.locator('details[data-options-category="bronnen"] > summary').click()
            self.assertTrue(toggle.is_checked())
        finally:
            page.close()

    def test_strongnummers_staan_inline_na_het_bijbehorende_nederlandse_woord(self):
        page = self.open_reader("johannes/1")
        try:
            self.enable_strongs(page)
            cell = page.locator('.verse-row[data-verse="1"] .col-2026')
            first = cell.locator('[data-strongs="G1722"]').first
            self.assertEqual(first.inner_text(), "<1722>")
            styles = first.evaluate("""el => ({
                verticalAlign: getComputedStyle(el).verticalAlign,
                backgroundColor: getComputedStyle(el).backgroundColor
            })""")
            self.assertEqual(styles["verticalAlign"], "baseline")
            self.assertIn(styles["backgroundColor"], {"transparent", "rgba(0, 0, 0, 0)"})
            self.assertTrue(first.evaluate("""el => {
                const range = document.createRange();
                range.setStart(el.parentNode, 0);
                range.setEndBefore(el);
                const fragment = range.cloneContents();
                fragment.querySelectorAll('.strongs-inline, .note-marker').forEach(marker => marker.remove());
                return fragment.textContent.trimEnd().endsWith('In');
            }"""))
            self.assertEqual(cell.locator('.strongs-alignment').count(), 0)
            self.assertEqual(cell.locator('.strongs-source-word').count(), 0)
        finally:
            page.close()

    def test_johannes_1_6_plaatst_de_naamstrong_na_johannes(self):
        """De gecontroleerde naamkoppeling volgt de Nederlandse woordvolgorde."""
        page = self.open_reader("johannes/1")
        try:
            self.enable_strongs(page)
            cell = page.locator('.verse-row[data-verse="6"] .col-2026')
            trigger = cell.locator('[data-strongs="G2491"]')
            self.assertEqual(trigger.count(), 1)
            self.assertTrue(trigger.evaluate("""el => {
                const range = document.createRange();
                range.setStart(el.parentNode, 0);
                range.setEndBefore(el);
                return range.toString().trimEnd().endsWith('Johannes');
            }"""))
        finally:
            page.close()

    def test_johannes_1_7_plaatst_g846_na_hem(self):
        """De Griekse woordvolgorde verandert de Nederlandse ankerplek niet."""
        page = self.open_reader("johannes/1")
        try:
            self.enable_strongs(page)
            cell = page.locator('.verse-row[data-verse="7"] .col-2026')
            trigger = cell.locator('[data-strongs="G846"]')
            self.assertEqual(trigger.count(), 1)
            self.assertTrue(trigger.evaluate("""el => {
                const firstStrong = el.previousElementSibling;
                if (!firstStrong || firstStrong.dataset.strongs !== 'G1223') return false;
                const range = document.createRange();
                range.setStart(firstStrong.parentNode, 0);
                range.setEndBefore(firstStrong);
                return range.toString().trimEnd().endsWith('hem');
            }"""))
        finally:
            page.close()

    def test_johannes_1_8_plaatst_getuigenisstrong_na_getuigen(self):
        page = self.open_reader("johannes/1")
        try:
            self.enable_strongs(page)
            cell = page.locator('.verse-row[data-verse="8"] .col-2026')
            trigger = cell.locator('[data-strongs="G3140"]')
            self.assertEqual(trigger.count(), 1)
            self.assertTrue(trigger.evaluate("""el => {
                const range = document.createRange();
                range.setStart(el.parentNode, 0);
                range.setEndBefore(el);
                return range.toString().trimEnd().endsWith('getuigen');
            }"""))
        finally:
            page.close()

    def test_johannes_1_9_plaatst_wereldstrong_na_wereld(self):
        page = self.open_reader("johannes/1")
        try:
            self.enable_strongs(page)
            cell = page.locator('.verse-row[data-verse="9"] .col-2026')
            trigger = cell.locator('[data-strongs="G2889"]')
            self.assertEqual(trigger.count(), 1)
            self.assertTrue(trigger.evaluate("""el => {
                const firstStrong = el.previousElementSibling?.previousElementSibling;
                if (!firstStrong || firstStrong.dataset.strongs !== 'G1519') return false;
                const range = document.createRange();
                range.setStart(firstStrong.parentNode, 0);
                range.setEndBefore(firstStrong);
                return range.toString().trimEnd().endsWith('wereld');
            }"""))
        finally:
            page.close()

    def test_johannes_1_10_plaatst_kennenstrong_na_gekend(self):
        page = self.open_reader("johannes/1")
        try:
            self.enable_strongs(page)
            cell = page.locator('.verse-row[data-verse="10"] .col-2026')
            trigger = cell.locator('[data-strongs="G1097"]')
            self.assertEqual(trigger.count(), 1)
            self.assertTrue(trigger.evaluate("""el => {
                const range = document.createRange();
                range.setStart(el.parentNode, 0);
                range.setEndBefore(el);
                return range.toString().trimEnd().endsWith('gekend');
            }"""))
        finally:
            page.close()

    def test_johannes_1_11_plaatst_ontvangststrong_na_aangenomen(self):
        page = self.open_reader("johannes/1")
        try:
            self.enable_strongs(page)
            cell = page.locator('.verse-row[data-verse="11"] .col-2026')
            trigger = cell.locator('[data-strongs="G3880"]')
            self.assertEqual(trigger.count(), 1)
            self.assertTrue(trigger.evaluate("""el => {
                const range = document.createRange();
                range.setStart(el.parentNode, 0);
                range.setEndBefore(el);
                return range.toString().trimEnd().endsWith('aangenomen');
            }"""))
        finally:
            page.close()

    def test_johannes_1_12_plaatst_ontvangststrong_na_aangenomen(self):
        """Ook bij de volgende zin blijft G2983 aan het Nederlandse werkwoord."""
        page = self.open_reader("johannes/1")
        try:
            self.enable_strongs(page)
            cell = page.locator('.verse-row[data-verse="12"] .col-2026')
            trigger = cell.locator('[data-strongs="G2983"]')
            self.assertEqual(trigger.count(), 1)
            self.assertTrue(trigger.evaluate("""el => {
                const range = document.createRange();
                range.setStart(el.parentNode, 0);
                range.setEndBefore(el);
                return range.toString().trimEnd().endsWith('aangenomen');
            }"""))
        finally:
            page.close()

    def test_johannes_1_20_plaatst_christusstrong_na_christus(self):
        """De belijdenis in Johannes 1:20 houdt de titel aan het juiste woord."""
        page = self.open_reader("johannes/1")
        try:
            self.enable_strongs(page)
            cell = page.locator('.verse-row[data-verse="20"] .col-2026')
            trigger = cell.locator('[data-strongs="G5547"]')
            self.assertEqual(trigger.count(), 1)
            self.assertTrue(trigger.evaluate("""el => {
                const range = document.createRange();
                range.setStart(el.parentNode, 0);
                range.setEndBefore(el);
                const fragment = range.cloneContents();
                fragment.querySelectorAll('.strongs-inline').forEach(marker => marker.remove());
                return fragment.textContent.trimEnd().endsWith('Christus');
            }"""))
        finally:
            page.close()

    def test_johannes_1_25_plaatst_doopstrong_na_doopt(self):
        page = self.open_reader("johannes/1")
        try:
            self.enable_strongs(page)
            cell = page.locator('.verse-row[data-verse="25"] .col-2026')
            trigger = cell.locator('[data-strongs="G907"]')
            self.assertEqual(trigger.count(), 1)
            self.assertTrue(trigger.evaluate("""el => {
                const range = document.createRange();
                range.setStart(el.parentNode, 0);
                range.setEndBefore(el);
                return range.toString().trimEnd().endsWith('doopt');
            }"""))
        finally:
            page.close()

    def test_johannes_1_29_plaatst_lamstrong_bij_lam_van_god(self):
        page = self.open_reader("johannes/1")
        try:
            self.enable_strongs(page)
            cell = page.locator('.verse-row[data-verse="29"] .col-2026')
            trigger = cell.locator('[data-strongs="G286"]')
            self.assertEqual(trigger.count(), 1)
            self.assertTrue(trigger.evaluate("""el => {
                const range = document.createRange();
                range.setStart(el.parentNode, 0);
                range.setEndBefore(el);
                const fragment = range.cloneContents();
                fragment.querySelectorAll('.strongs-inline').forEach(marker => marker.remove());
                return fragment.textContent.trimEnd().endsWith('Lam van God');
            }"""))
        finally:
            page.close()

    def test_johannes_1_34_plaatst_zoonstrong_bij_de_zoon_van_god(self):
        page = self.open_reader("johannes/1")
        try:
            self.enable_strongs(page)
            cell = page.locator('.verse-row[data-verse="34"] .col-2026')
            trigger = cell.locator('[data-strongs="G5207"]')
            self.assertEqual(trigger.count(), 1)
            self.assertTrue(trigger.evaluate("""el => {
                const range = document.createRange();
                range.setStart(el.parentNode, 0);
                range.setEndBefore(el);
                const fragment = range.cloneContents();
                fragment.querySelectorAll('.strongs-inline').forEach(marker => marker.remove());
                return fragment.textContent.trimEnd().endsWith('de Zoon van God');
            }"""))
        finally:
            page.close()

    def test_johannes_1_36_plaatst_lamstrong_bij_lam_van_god(self):
        page = self.open_reader("johannes/1")
        try:
            self.enable_strongs(page)
            cell = page.locator('.verse-row[data-verse="36"] .col-2026')
            trigger = cell.locator('[data-strongs="G286"]')
            self.assertEqual(trigger.count(), 1)
            self.assertTrue(trigger.evaluate("""el => {
                const range = document.createRange();
                range.setStart(el.parentNode, 0);
                range.setEndBefore(el);
                const fragment = range.cloneContents();
                fragment.querySelectorAll('.strongs-inline').forEach(marker => marker.remove());
                return fragment.textContent.trimEnd().endsWith('het Lam van God');
            }"""))
        finally:
            page.close()

    def test_johannes_1_38_plaatst_volgstrong_na_volgen(self):
        page = self.open_reader("johannes/1")
        try:
            self.enable_strongs(page)
            cell = page.locator('.verse-row[data-verse="38"] .col-2026')
            trigger = cell.locator('[data-strongs="G190"]')
            self.assertEqual(trigger.count(), 1)
            self.assertTrue(trigger.evaluate("""el => {
                const range = document.createRange();
                range.setStart(el.parentNode, 0);
                range.setEndBefore(el);
                const fragment = range.cloneContents();
                fragment.querySelectorAll('.strongs-inline').forEach(marker => marker.remove());
                return fragment.textContent.trimEnd().endsWith('volgen');
            }"""))
        finally:
            page.close()

    def test_johannes_2_1_plaatst_derdestrong_bij_de_derde_dag(self):
        page = self.open_reader("johannes/2")
        try:
            self.enable_strongs(page)
            trigger = page.locator('.verse-row[data-verse="1"] .col-2026 [data-strongs="G5154"]')
            self.assertEqual(trigger.count(), 1)
            self.assertTrue(trigger.evaluate("""el => {
                const range = document.createRange(); range.setStart(el.parentNode, 0); range.setEndBefore(el);
                const fragment = range.cloneContents(); fragment.querySelectorAll('.strongs-inline, .note-marker').forEach(marker => marker.remove());
                return fragment.textContent.trimEnd().endsWith('op de derde dag');
            }"""))
        finally:
            page.close()

    def test_johannes_2_rendert_alle_434_gecontroleerde_tr_tokens_inline(self):
        page = self.open_reader("johannes/2")
        try:
            self.enable_strongs(page)
            self.assertEqual(
                page.locator('.verse-row .col-2026 .strongs-inline').count(),
                434,
            )
        finally:
            page.close()

    def test_johannes_2_11_plaatst_tekenstrong_bij_van_de_tekenen(self):
        page = self.open_reader("johannes/2")
        try:
            self.enable_strongs(page)
            trigger = page.locator('.verse-row[data-verse="11"] .col-2026 [data-strongs="G4592"]')
            self.assertEqual(trigger.count(), 1)
            self.assertTrue(trigger.evaluate("""el => {
                const range = document.createRange(); range.setStart(el.parentNode, 0); range.setEndBefore(el);
                const fragment = range.cloneContents(); fragment.querySelectorAll('.strongs-inline').forEach(marker => marker.remove());
                return fragment.textContent.trimEnd().endsWith('van de tekenen');
            }"""))
        finally:
            page.close()

    def test_johannes_2_25_plaatst_mensstrong_bij_in_de_mens(self):
        page = self.open_reader("johannes/2")
        try:
            self.enable_strongs(page)
            triggers = page.locator('.verse-row[data-verse="25"] .col-2026 [data-strongs="G444"]')
            self.assertEqual(triggers.count(), 2)
            self.assertTrue(triggers.nth(1).evaluate("""el => {
                const range = document.createRange(); range.setStart(el.parentNode, 0); range.setEndBefore(el);
                const fragment = range.cloneContents(); fragment.querySelectorAll('.strongs-inline').forEach(marker => marker.remove());
                return fragment.textContent.trimEnd().endsWith('wat in de mens was');
            }"""))
        finally:
            page.close()

    def test_johannes_3_rendert_alle_672_gecontroleerde_tr_tokens_inline(self):
        page = self.open_reader("johannes/3")
        try:
            self.enable_strongs(page)
            self.assertEqual(page.locator('.verse-row .col-2026 .strongs-inline').count(), 672)
        finally:
            page.close()

    def test_johannes_3_16_plaatst_eniggeborenstrong_bij_eniggeboren_zoon(self):
        page = self.open_reader("johannes/3")
        try:
            self.enable_strongs(page)
            trigger = page.locator('.verse-row[data-verse="16"] .col-2026 [data-strongs="G3439"]')
            self.assertEqual(trigger.count(), 1)
            self.assertTrue(trigger.evaluate("""el => {
                const range = document.createRange(); range.setStart(el.parentNode, 0); range.setEndBefore(el);
                const fragment = range.cloneContents(); fragment.querySelectorAll('.strongs-inline, .note-marker').forEach(marker => marker.remove());
                return fragment.textContent.trimEnd().endsWith('eniggeboren Zoon gegeven heeft');
            }"""))
        finally:
            page.close()

    def test_johannes_3_36_plaatst_toornstrong_bij_de_toorn_van_god(self):
        page = self.open_reader("johannes/3")
        try:
            self.enable_strongs(page)
            trigger = page.locator('.verse-row[data-verse="36"] .col-2026 [data-strongs="G3709"]')
            self.assertEqual(trigger.count(), 1)
            self.assertTrue(trigger.evaluate("""el => {
                const range = document.createRange(); range.setStart(el.parentNode, 0); range.setEndBefore(el);
                const fragment = range.cloneContents(); fragment.querySelectorAll('.strongs-inline, .note-marker').forEach(marker => marker.remove());
                return fragment.textContent.trimEnd().endsWith('de toorn van God');
            }"""))
        finally:
            page.close()

    def test_johannes_4_rendert_alle_953_gecontroleerde_tr_tokens_inline(self):
        page = self.open_reader("johannes/4")
        try:
            self.enable_strongs(page)
            per_verse = {
                number: page.locator(f'.verse-row[data-verse="{number}"] .col-2026 .strongs-inline').count()
                for number in range(1, 55)
            }
            rendered_last = page.locator('.verse-row[data-verse="54"] .col-2026 .strongs-inline').evaluate_all(
                "elements => elements.map(element => element.dataset.strongs)"
            )
            self.assertEqual(sum(per_verse.values()), 953, {"counts": per_verse, "verse54": rendered_last})
        finally:
            page.close()

    def test_johannes_4_1_plaatst_vergelijkende_vormstrong_bij_meer_discipelen_maakte(self):
        page = self.open_reader("johannes/4")
        try:
            self.enable_strongs(page)
            trigger = page.locator('.verse-row[data-verse="1"] .col-2026 [data-strongs="G4119"]')
            self.assertEqual(trigger.count(), 1)
            self.assertTrue(trigger.evaluate("""el => {
                const range = document.createRange(); range.setStart(el.parentNode, 0); range.setEndBefore(el);
                const fragment = range.cloneContents(); fragment.querySelectorAll('.strongs-inline, .note-marker').forEach(marker => marker.remove());
                return fragment.textContent.trimEnd().endsWith('meer discipelen maakte');
            }"""))
        finally:
            page.close()

    def test_johannes_4_10_plaatst_waterstrong_bij_levend_water(self):
        page = self.open_reader("johannes/4")
        try:
            self.enable_strongs(page)
            trigger = page.locator('.verse-row[data-verse="10"] .col-2026 [data-strongs="G5204"]')
            self.assertEqual(trigger.count(), 1)
            self.assertTrue(trigger.evaluate("""el => {
                const range = document.createRange(); range.setStart(el.parentNode, 0); range.setEndBefore(el);
                const fragment = range.cloneContents(); fragment.querySelectorAll('.strongs-inline, .note-marker').forEach(marker => marker.remove());
                return fragment.textContent.trimEnd().endsWith('levend water');
            }"""))
        finally:
            page.close()

    def test_johannes_4_14_plaatst_toekomstcode_bij_zal_geven(self):
        page = self.open_reader("johannes/4")
        try:
            self.enable_strongs(page)
            trigger = page.locator('.verse-row[data-verse="14"] .col-2026 [data-strongs="G1325"]').first
            self.assertEqual(trigger.inner_text(), "<1325>(5692)")
            self.assertEqual(trigger.get_attribute("data-tvm"), "G5692")
        finally:
            page.close()

    def test_johannes_4_25_plaatst_messiasstrong_bij_de_messias(self):
        page = self.open_reader("johannes/4")
        try:
            self.enable_strongs(page)
            trigger = page.locator('.verse-row[data-verse="25"] .col-2026 [data-strongs="G3323"]')
            self.assertEqual(trigger.count(), 1)
            self.assertTrue(trigger.evaluate("""el => {
                const range = document.createRange(); range.setStart(el.parentNode, 0); range.setEndBefore(el);
                const fragment = range.cloneContents(); fragment.querySelectorAll('.strongs-inline, .note-marker').forEach(marker => marker.remove());
                return fragment.textContent.trimEnd().endsWith('dat de Messias komt');
            }"""))
        finally:
            page.close()

    def test_johannes_4_42_plaatst_zaligmakerstrong_bij_zaligmaker(self):
        page = self.open_reader("johannes/4")
        try:
            self.enable_strongs(page)
            trigger = page.locator('.verse-row[data-verse="42"] .col-2026 [data-strongs="G4990"]')
            self.assertEqual(trigger.count(), 1)
            self.assertTrue(trigger.evaluate("""el => {
                const range = document.createRange(); range.setStart(el.parentNode, 0); range.setEndBefore(el);
                const fragment = range.cloneContents(); fragment.querySelectorAll('.strongs-inline, .note-marker').forEach(marker => marker.remove());
                return fragment.textContent.trimEnd().endsWith('de Zaligmaker van de wereld');
            }"""))
        finally:
            page.close()

    def test_johannes_4_46_toont_vormnummer_en_tijdcode_bij_was(self):
        page = self.open_reader("johannes/4")
        try:
            self.enable_strongs(page)
            trigger = page.locator('.verse-row[data-verse="46"] .col-2026 [data-strongs="G2258"]')
            self.assertEqual(trigger.inner_text(), "<2258>(5713)")
            self.assertEqual(trigger.get_attribute("data-tvm"), "G5713")
        finally:
            page.close()

    def test_johannes_5_1_tot_10_rendert_alle_172_gecontroleerde_tr_tokens_inline(self):
        page = self.open_reader("johannes/5")
        try:
            self.enable_strongs(page)
            per_verse = {
                number: page.locator(f'.verse-row[data-verse="{number}"] .col-2026 .strongs-inline').count()
                for number in range(1, 11)
            }
            self.assertEqual(sum(per_verse.values()), 172, per_verse)
        finally:
            page.close()

    def test_johannes_5_5_gebruikt_de_uitgeschreven_tr_getalvariant(self):
        page = self.open_reader("johannes/5")
        try:
            self.enable_strongs(page)
            verse = page.locator('.verse-row[data-verse="5"] .col-2026')
            self.assertEqual(verse.locator('[data-strongs="G5144"]').count(), 1)
            self.assertEqual(verse.locator('[data-strongs="G3638"]').count(), 1)
            self.assertEqual(verse.locator('[data-strongs="G2258"]').inner_text(), "<2258>(5713)")
        finally:
            page.close()

    def test_mattheus_1_1_plaatst_christusstrong_na_christus(self):
        page = self.open_reader("mattheus/1")
        try:
            self.enable_strongs(page)
            cell = page.locator('.verse-row[data-verse="1"] .col-2026')
            trigger = cell.locator('[data-strongs="G5547"]')
            self.assertEqual(trigger.count(), 1)
            self.assertTrue(trigger.evaluate("""el => {
                const range = document.createRange();
                range.setStart(el.parentNode, 0);
                range.setEndBefore(el);
                const fragment = range.cloneContents(); fragment.querySelectorAll('.strongs-inline').forEach(marker => marker.remove());
                return fragment.textContent.trimEnd().endsWith('CHRISTUS');
            }"""))
        finally:
            page.close()

    def test_mattheus_1_20_plaatst_engelstrong_na_engel(self):
        """De boodschapper blijft aan het Nederlandse zelfstandig naamwoord gekoppeld."""
        page = self.open_reader("mattheus/1")
        try:
            self.enable_strongs(page)
            cell = page.locator('.verse-row[data-verse="20"] .col-2026')
            trigger = cell.locator('[data-strongs="G32"]')
            self.assertEqual(trigger.count(), 1)
            self.assertTrue(trigger.evaluate("""el => {
                const range = document.createRange();
                range.setStart(el.parentNode, 0);
                range.setEndBefore(el);
                const fragment = range.cloneContents();
                fragment.querySelectorAll('.strongs-inline').forEach(marker => marker.remove());
                return fragment.textContent.trimEnd().endsWith('engel');
            }"""))
        finally:
            page.close()

    def test_gebed_van_manasse_plaatst_g2464_alleen_na_izaak(self):
        page = self.open_reader("gebedvanmanasse/1")
        try:
            self.enable_strongs(page)
            cell = page.locator('.verse-row[data-verse="1"] .col-2026')
            trigger = cell.locator('[data-strongs="G2464"]')
            self.assertEqual(trigger.count(), 1)
            self.assertTrue(trigger.evaluate("""el => {
                const range = document.createRange();
                range.setStart(el.parentNode, 0);
                range.setEndBefore(el);
                return range.toString().trimEnd().endsWith('Izaäk');
            }"""))
        finally:
            page.close()

    def test_nagekeken_genesis_haalt_corpusmapping_op_zonder_grondtekstregel(self):
        page = self.open_reader("genesis/1")
        try:
            self.enable_strongs(page)
            cell = page.locator('.verse-row[data-verse="1"] .col-2026')
            self.assertGreater(cell.locator('.strongs-inline').count(), 0)
            self.assertEqual(cell.locator('.strongs-alignment').count(), 0)
            self.assertEqual(cell.locator('.strongs-source-word').count(), 0)
        finally:
            page.close()

    def test_nagekeken_1samuel_haalt_corpusmapping_op_zonder_grondtekstregel(self):
        page = self.open_reader("1samuel/1")
        try:
            self.enable_strongs(page)
            cell = page.locator('.verse-row[data-verse="1"] .col-2026')
            self.assertGreater(cell.locator('.strongs-inline').count(), 0)
            self.assertEqual(cell.locator('.strongs-alignment').count(), 0)
            self.assertEqual(cell.locator('.strongs-source-word').count(), 0)
        finally:
            page.close()

    def test_mattheus_1_24_plaatst_opstaanstrong_na_opgewekt(self):
        """G1453 hoort bij 'opgewekt zijnde', nooit bij het lidwoord 'de'."""
        page = self.open_reader("mattheus/1")
        try:
            self.enable_strongs(page)
            cell = page.locator('.verse-row[data-verse="24"] .col-2026')
            wake = cell.locator('[data-strongs="G1453"]')
            self.assertEqual(wake.count(), 1)
            self.assertTrue(wake.evaluate("""el => {
                const range = document.createRange();
                range.setStart(el.parentNode, 0);
                range.setEndBefore(el);
                const fragment = range.cloneContents();
                fragment.querySelectorAll('.strongs-inline').forEach(marker => marker.remove());
                return fragment.textContent.trimEnd().endsWith('opgewekt zijnde');
            }"""))
            sleep = cell.locator('[data-strongs="G5258"]')
            self.assertEqual(sleep.count(), 1)
            self.assertTrue(sleep.evaluate("""el => {
                const range = document.createRange();
                range.setStart(el.parentNode, 0);
                range.setEndBefore(el);
                return range.toString().trimEnd().endsWith('slaap');
            }"""))
        finally:
            page.close()

    def test_klik_op_strong_opent_toegankelijke_bottom_sheet_met_woordenboeklink(self):
        page = self.open_reader("johannes/1")
        try:
            self.enable_strongs(page)
            trigger = page.locator('.verse-row[data-verse="1"] .col-2026 [data-strongs="G1722"]').first
            trigger.click()
            sheet = page.locator("#strongs-sheet")
            sheet.wait_for(state="visible", timeout=5_000)
            self.assertEqual(sheet.get_attribute("role"), "dialog")
            self.assertEqual(sheet.get_attribute("aria-modal"), "true")
            self.assertIn("G1722", page.locator("#strongs-sheet-number").inner_text())
            self.assertTrue(page.locator("#strongs-sheet-word").inner_text().strip())
            self.assertTrue(page.locator("#strongs-sheet-definition").inner_text().strip())
            self.assertIn("TBESG", page.locator("#strongs-sheet .lexicon-source").inner_text())
            self.assertEqual(
                page.locator("#strongs-sheet .lexicon-gloss").inner_text(),
                "in, op, onder, met",
            )
            self.assertIn(
                "het meest voorkomende voorzetsel",
                page.locator("#strongs-sheet-definition").inner_text(),
            )
            self.assertIn(
                "taal=grieks&entry=G1722",
                page.locator("#strongs-sheet-full-link").get_attribute("href"),
            )

            page.locator("#strongs-sheet-definition").click()
            self.assertTrue(sheet.is_visible(), "interactie binnen het paneel mag het niet sluiten")

            page.locator(".strongs-sheet-close").focus()
            page.keyboard.press("Shift+Tab")
            self.assertEqual(page.evaluate("document.activeElement.id"), "strongs-sheet-full-link")
            page.keyboard.press("Tab")
            self.assertIn("strongs-sheet-close", page.evaluate("document.activeElement.className"))

            page.keyboard.press("Escape")
            self.assertFalse(sheet.is_visible())
            self.assertTrue(trigger.evaluate("el => document.activeElement === el"))
        finally:
            page.close()

    def test_meerdere_strongnummers_worden_afzonderlijk_aanklikbaar(self):
        page = self.open_reader()
        try:
            html = page.evaluate(
                """() => OVWoordnummers.renderInline('testwoord', [{
                    tekst: 'testwoord', voorkomen: 1, strongs: ['H1', 'G3056'],
                    bronwoorden: ['bronwoord'], transliteraties: ['test'], glossen: ['betekenis']
                }])"""
            )
            self.assertIn('data-strongs="H1"', html)
            self.assertIn('data-strongs="G3056"', html)
            self.assertIn("&lt;1&gt;</button>", html)
            self.assertIn("&lt;3056&gt;</button>", html)
        finally:
            page.close()

    def test_inline_markeringen_behouden_de_nederlandse_leesrichting(self):
        page = self.open_reader("johannes/1")
        try:
            self.enable_strongs(page)
            cell = page.locator('.verse-row[data-verse="1"] .col-2026')
            self.assertEqual(cell.evaluate("el => getComputedStyle(el).direction"), "ltr")
            self.assertGreater(cell.locator('.strongs-inline').count(), 0)
        finally:
            page.close()

    def test_bottom_sheet_past_op_mobiel_en_sluit_via_de_achtergrond(self):
        page = self.open_reader("johannes/1", width=390, height=844)
        try:
            self.enable_strongs(page)
            trigger = page.locator('.verse-row[data-verse="1"] [data-strongs="G1722"]').first
            trigger.click()
            sheet = page.locator("#strongs-sheet")
            sheet.wait_for(state="visible", timeout=5_000)
            panel = page.locator(".strongs-sheet-panel")
            panel_box = panel.bounding_box()
            self.assertLessEqual(panel_box["width"], 390)
            self.assertAlmostEqual(panel_box["x"], 0, delta=1)
            self.assertAlmostEqual(panel_box["y"] + panel_box["height"], 844, delta=1)
            self.assertEqual(panel.evaluate("el => getComputedStyle(el).position"), "absolute")
            self.assertEqual(panel.evaluate("el => getComputedStyle(el).bottom"), "0px")

            sheet.click(position={"x": 4, "y": 4})
            self.assertFalse(sheet.is_visible())
            self.assertTrue(trigger.evaluate("el => document.activeElement === el"))
        finally:
            page.close()

    def test_ongemapte_latijnse_en_geez_woordnummers_krijgen_geen_aparte_grondtekstregel(self):
        page = self.open_reader("4ezra/1")
        try:
            self.enable_strongs(page, expect_inline=False)
            cell = page.locator('.verse-row[data-verse="1"] .col-2026')
            self.assertEqual(cell.locator('.strongs-alignment').count(), 0)
            self.assertEqual(cell.locator('.strongs-source-word').count(), 0)
        finally:
            page.close()

    def test_niet_afzonderlijk_vertaald_grondwoord_blijft_inline_zichtbaar(self):
        page = self.open_reader()
        try:
            html = page.evaluate(
                """() => OVWoordnummers.renderInline('het Woord', [{
                    tekst: '', anker: 'Woord', voorkomen: 1, plaats: 'na',
                    strongs: ['G3588'], bronwoorden: ['ὁ'],
                    status: 'niet_afzonderlijk_weergegeven',
                    reviewstatus: 'handmatig_gecontroleerd'
                }])"""
            )
            self.assertIn('Woord<button', html)
            self.assertIn('data-strongs="G3588"', html)
            self.assertIn('data-alignment-status="niet_afzonderlijk_weergegeven"', html)
        finally:
            page.close()

    def test_johannes_1_toont_tr_vormnummer_en_ongemapt_grondwoord_inline(self):
        page = self.open_reader("johannes/1")
        try:
            self.enable_strongs(page)
            first = page.locator('.verse-row[data-verse="1"] .col-2026')
            was = first.locator('[data-strongs="G2258"]').first
            self.assertEqual(was.inner_text(), "<2258>(5713)")
            self.assertTrue(was.evaluate("""el => {
                const range = document.createRange(); range.setStart(el.parentNode, 0); range.setEndBefore(el);
                const fragment = range.cloneContents(); fragment.querySelectorAll('.strongs-inline, .note-marker').forEach(marker => marker.remove());
                return fragment.textContent.trimEnd().endsWith('was');
            }"""))

            twelfth = page.locator('.verse-row[data-verse="12"] .col-2026')
            unrendered = twelfth.locator(
                '[data-strongs="G846"][data-alignment-status="niet_afzonderlijk_weergegeven"]'
            )
            self.assertEqual(unrendered.count(), 1)
            unrendered.click()
            page.locator("#strongs-sheet").wait_for(state="visible", timeout=5_000)
        finally:
            page.close()

    def test_johannes_1_2_toont_woordnummer_met_tijdcode(self):
        page = self.open_reader("johannes/1")
        try:
            self.enable_strongs(page)
            was = page.locator(
                '.verse-row[data-verse="2"] .col-2026 [data-strongs="G2258"]'
            ).first
            self.assertEqual(was.inner_text(), "<2258>(5713)")
            self.assertEqual(was.get_attribute("data-tvm"), "G5713")
        finally:
            page.close()

    def test_griekse_sheet_toont_herzien_artikel_met_aanklikbare_tekstverwijzingen(self):
        page = self.open_reader("johannes/1")
        try:
            self.enable_strongs(page)
            page.locator('.verse-row[data-verse="1"] .col-2026 [data-strongs="G1722"]').first.click()
            definition = page.locator("#strongs-sheet-definition")
            definition.wait_for(timeout=5_000)
            self.assertIn("het meest voorkomende voorzetsel", definition.inner_text())
            reference = definition.locator('a[href="index.html#lukas/7/37"]')
            self.assertGreater(reference.count(), 0)
            self.assertEqual(reference.first.inner_text(), "Lukas 7:37")
        finally:
            page.close()

    def test_geez_woordnummer_staat_inline_en_opent_het_dillmann_woordenboek(self):
        page = self.open_reader("henoch/1")
        try:
            self.enable_strongs(page)
            trigger = page.locator('.verse-row[data-verse="1"] .col-2026 [data-strongs="OVG3907"]')
            self.assertEqual(trigger.inner_text(), "<3907>")
            trigger.click()
            sheet = page.locator("#strongs-sheet")
            sheet.wait_for(state="visible", timeout=5_000)
            self.assertIn("DILLMANN GE’EZ-WOORDENBOEK", sheet.locator(".lexicon-source").inner_text())
            self.assertIn(
                "taal=geez&zoek=OVG3907",
                sheet.locator("#strongs-sheet-full-link").get_attribute("href"),
            )
        finally:
            page.close()

    def test_strongnummers_blijven_helderblauw_in_donker_thema(self):
        page = self.browser.new_page(viewport={"width": 1280, "height": 900})
        page.add_init_script(
            "localStorage.setItem('sv2026_vertaalopties', JSON.stringify({thema:'donker'}))"
        )
        try:
            page.goto(f"{self.base_url}/index.html#johannes/1", wait_until="domcontentloaded")
            page.locator('.verse-row[data-verse="1"]').wait_for(timeout=15_000)
            self.enable_strongs(page)
            color = page.locator('.verse-row[data-verse="1"] [data-strongs="G1722"]').first.evaluate(
                "el => getComputedStyle(el).color"
            )
            self.assertEqual(color, "rgb(131, 187, 239)")
        finally:
            page.close()

        page = self.open_reader("henoch/1")
        try:
            self.enable_strongs(page, expect_inline=False)
            cell = page.locator('.verse-row[data-verse="1"] .col-2026')
            self.assertEqual(cell.locator('.strongs-alignment').count(), 0)
            self.assertEqual(cell.locator('.strongs-source-word').count(), 0)
        finally:
            page.close()

    def test_gedeelde_renderer_is_beschikbaar_voor_interne_citaties(self):
        page = self.open_reader("johannes/1")
        try:
            html = page.evaluate(
                """() => OVWoordnummers.renderInline('In het begin', [{
                    tekst: 'begin', voorkomen: 1, strongs: ['G746'],
                    bronwoorden: ['ἀρχῇ'], transliteraties: ['arche'], glossen: ['begin']
                }])"""
            )
            self.assertIn('begin<button', html)
            self.assertIn('data-strongs="G746"', html)
        finally:
            page.close()

    def test_interne_citatie_neemt_globale_woordnummervoorkeur_over(self):
        page = self.browser.new_page(viewport={"width": 1280, "height": 900})
        page.add_init_script(
            "localStorage.setItem('sv2026_vertaalopties', JSON.stringify({strongs:'aan'}))"
        )
        try:
            page.goto(f"{self.base_url}/onderwerpen.html", wait_until="domcontentloaded")
            page.wait_for_function("window.OSV && window.OVTekstweergave")
            html = page.evaluate("() => OSV.cite('johannes 1:1', {link:false}).then(r => r.html)")
            self.assertNotIn('class="strongs-alignment', html)
            self.assertIn('data-strongs="G1722"', html)

            page.locator("body").evaluate(
                "(el, markup) => el.insertAdjacentHTML('beforeend', markup)", html
            )
            page.locator('[data-strongs="G1722"]').first.click()
            page.locator("#strongs-sheet").wait_for(state="visible", timeout=5_000)
            self.assertIn("G1722", page.locator("#strongs-sheet-number").inner_text())
        finally:
            page.close()

    def test_doorlopende_leesversie_neemt_woordnummervoorkeur_over(self):
        page = self.browser.new_page(viewport={"width": 900, "height": 900})
        page.add_init_script(
            "localStorage.setItem('sv2026_vertaalopties', JSON.stringify({strongs:'aan'}))"
        )
        try:
            page.goto(f"{self.base_url}/lees.html#johannes/1", wait_until="domcontentloaded")
            trigger = page.locator('.verse-span[data-verse="1"] .verse-text [data-strongs="G1722"]')
            trigger.wait_for(state="visible", timeout=15_000)
            self.assertEqual(trigger.inner_text(), "<1722>")
            self.assertEqual(page.locator('.verse-span[data-verse="1"] .strongs-alignment').count(), 0)
            trigger.click()
            page.locator("#strongs-sheet").wait_for(state="visible", timeout=5_000)
        finally:
            page.close()

    def test_stronglabels_blijven_buiten_gekopieerde_bijbeltekst(self):
        page = self.open_reader("johannes/1")
        try:
            self.enable_strongs(page)
            copied = page.evaluate(
                """() => {
                    VerseSelect.selected = new Set(['johannes/1/1']);
                    return VerseSelect._buildRefAndText().plain;
                }"""
            )
            self.assertNotIn("G1722", copied)
            self.assertIn("begin", copied.lower())
        finally:
            page.close()


class StrongsDataTests(unittest.TestCase):
    def test_importer_gebruikt_explicit_source_verse_voor_verschoven_lokaal_vers(self):
        source_document = {
            "type": "USJ",
            "content": [
                {"type": "chapter", "number": "1"},
                {"type": "verse", "number": "2"},
                {"type": "char", "marker": "w", "strong": "G3056", "content": ["Word"]},
            ],
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source_dir = root / "source"; source_dir.mkdir()
            source_path = source_dir / "demo.usj"
            source_path.write_text(json.dumps(source_document), encoding="utf-8")
            digest = hashlib.sha256(source_path.read_bytes()).hexdigest().upper()
            data_dir = root / "data" / "demo"; data_dir.mkdir(parents=True)
            (data_dir / "1.json").write_text(json.dumps({"verses":[{"number":1,"text2026":"Woord","grondtekst":[{"woord":"λόγος","strongs":"G3056"}]}]}), encoding="utf-8")
            review = {"source":{"id":"test","version":"1","sha256":"x"},"books":[{"code":"DEM","repo_book":"demo","chapter":1,"source_file":"demo.usj","source_file_sha256":digest,"verses":[{"verse":1,"source_verse":2,"mappings":[{"tekst":"Woord","bronindices":[0],"grondindices":[0],"confidence":1.0,"reviewstatus":"handmatig_gecontroleerd"}]}]}]}
            review_path = root / "review.json"; review_path.write_text(json.dumps(review), encoding="utf-8")
            report = apply_review_file(review_path, source_dir, root / "data", write=True)
            result = json.loads((data_dir / "1.json").read_text(encoding="utf-8"))
        self.assertEqual(report["added"], 1)
        self.assertEqual(result["verses"][0]["woordnummers"][0]["herkomst"]["referentie"], "DEM 1:2")

    def test_johannes_review_metadata_bewaart_bewezen_verscorrespondentie(self):
        pilot = json.loads((ROOT / "data" / "woordnummers-pilot-johannes.json").read_text(encoding="utf-8"))
        correspondence = {
            item["local_verse"]: item
            for item in pilot["books"][0]["verse_correspondence"]
        }
        self.assertEqual(correspondence[38]["status"], "gedeeltelijk")
        self.assertEqual(correspondence[39]["status"], "afwijkend")
        for local_verse in range(40, 46):
            self.assertEqual(correspondence[local_verse]["status"], "afwijkend")
            self.assertIn("grondtekst", correspondence[local_verse]["reden"])

    def test_usj_parser_behoudt_geneste_versgrens_in_char_inhoud(self):
        """Een USJ-versmarker kan binnen opgemaakte inhoud staan (Johannes 1:39)."""
        fixture = {
            "type": "USJ",
            "content": [
                {"type": "chapter", "number": "1"},
                {
                    "type": "para",
                    "content": [
                        {"type": "verse", "number": "38"},
                        {
                            "type": "char",
                            "marker": "qt",
                            "content": [
                                {"type": "verse", "number": "39"},
                                {
                                    "type": "char",
                                    "marker": "w",
                                    "strong": "G4226",
                                    "content": ["where"],
                                },
                            ],
                        },
                    ],
                },
            ]
        }
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "nested.usj"
            source.write_text(json.dumps(fixture), encoding="utf-8")
            parsed = parse_usj(source)
        self.assertEqual(parsed[(1, 39)], [{"text": "where", "strongs": ["G4226"]}])

    def test_alle_88_boeken_hebben_bronvaste_woordnummers(self):
        report = audit()
        self.assertEqual(report["books"], 88)
        self.assertEqual(report["books_with_numbers"], 88)
        self.assertFalse(report["invalid"])
        self.assertEqual(set(report["families"]), {"H", "G", "OVL", "OVG"})

    def test_woordverwijzingen_gebruiken_alleen_ondersteunde_nummerfamilies(self):
        families = set()
        for chapter_file in ROOT.glob("data/*/[0-9]*.json"):
            data = json.loads(chapter_file.read_text(encoding="utf-8"))
            for verse in data.get("verses", []):
                if not isinstance(verse, dict):
                    continue
                for word in verse.get("grondtekst", []) or []:
                    if not isinstance(word, dict):
                        continue
                    value = str(word.get("strongs") or "")
                    if value:
                        for number in value.split():
                            if number.startswith("OVL"):
                                families.add("OVL")
                            elif number.startswith("OVG"):
                                families.add("OVG")
                            elif number.startswith("H"):
                                families.add("H")
                            elif number.startswith("G"):
                                families.add("G")
                            else:
                                self.fail(f"Onbekende woordnummerfamilie: {number}")
        self.assertEqual(families, {"H", "G", "OVL", "OVG"})


if __name__ == "__main__":
    unittest.main()
