"""Browserregressies voor OPV als primaire, parallelle en citaateditie."""

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

    def copyfile(self, source, outputfile):
        with contextlib.suppress(ConnectionError):
            super().copyfile(source, outputfile)


class OpvReaderTests(unittest.TestCase):
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

    def new_page(self, settings=None):
        page = self.browser.new_page(viewport={"width": 1280, "height": 900})
        page.set_default_timeout(10_000)
        if settings is not None:
            page.add_init_script(
                "localStorage.setItem('sv2026_vertaalopties', "
                + json.dumps(json.dumps(settings))
                + ")"
            )
        return page

    @staticmethod
    def observe_runtime(page):
        observed = {"pageerrors": [], "console_errors": [], "http_errors": [], "requests": []}
        page.on("pageerror", lambda error: observed["pageerrors"].append(str(error)))
        page.on(
            "console",
            lambda message: observed["console_errors"].append(message.text)
            if message.type == "error"
            else None,
        )
        page.on("request", lambda request: observed["requests"].append(request.url))
        page.on(
            "response",
            lambda response: observed["http_errors"].append(
                {"status": response.status, "url": response.url}
            )
            if response.status >= 400
            else None,
        )
        return observed

    @staticmethod
    def open_sources(page):
        page.locator("#topnav-tekstopties").click()
        sources = page.locator('details[data-options-category="bronnen"]')
        sources.evaluate("element => { element.open = true; }")

    def test_opv_is_primaire_editie_en_bewaart_readerdata(self):
        page = self.new_page()
        try:
            page.goto(
                f"{self.base_url}/index.html?editie=nl-opv#genesis/1",
                wait_until="domcontentloaded",
            )
            verse = page.locator('.verse-row[data-verse="1"] .col-2026')
            verse.wait_for()
            self.assertIn("hemel", verse.inner_text())
            self.assertEqual(verse.get_attribute("lang"), "nl")

            readerdata = page.evaluate(
                """async () => {
                    const raw = await fetch('data/edities/opv/chapters/genesis/1.json').then(r => r.json());
                    const chapter = await TekstEditie.loadChapterForEdition('nl-opv', 'genesis', 1);
                    return {
                        meta: chapter._translation,
                        raw,
                        normalized: {
                            schema: chapter.schema,
                            editie: chapter.editie,
                            boek: chapter.boek,
                            hoofdstuk: chapter.number,
                            kop: chapter.heading,
                            blokken: chapter.blokken,
                            verzen: chapter.verses.map(verse => ({
                                nummer: verse.number,
                                status: verse.status,
                                bron: verse.bron,
                                begrippen: verse.begrippen,
                                citaten: verse.citaten,
                                review: verse.review,
                                segmenten: verse.segmenten,
                                translationSegments: verse.translationSegments,
                            })),
                        },
                    };
                }"""
            )
            raw = readerdata["raw"]
            normalized = readerdata["normalized"]
            self.assertEqual(readerdata["meta"]["code"], "nl-opv")
            self.assertEqual(readerdata["meta"]["naam"], "Open Parafrase Vertaling (proef)")
            self.assertEqual(
                {key: normalized[key] for key in ("schema", "editie", "boek", "hoofdstuk", "kop", "blokken")},
                {key: raw[key] for key in ("schema", "editie", "boek", "hoofdstuk", "kop", "blokken")},
            )
            self.assertEqual(len(normalized["verzen"]), 31)
            for actual, expected in zip(normalized["verzen"], raw["verzen"]):
                self.assertEqual(actual["nummer"], expected["nummer"])
                self.assertEqual(actual["status"], expected["review"]["status"])
                for key in ("bron", "begrippen", "citaten", "review", "segmenten"):
                    self.assertEqual(actual[key], expected[key], f"vers {expected['nummer']} veld {key}")
                self.assertEqual(actual["translationSegments"], expected["segmenten"])
        finally:
            page.close()

    def test_wisselen_naar_opv_gebeurt_zonder_reload_en_blijft_bewaard(self):
        page = self.new_page()
        try:
            page.goto(f"{self.base_url}/index.html#genesis/1", wait_until="domcontentloaded")
            page.locator('.verse-row[data-verse="1"]').wait_for()
            page.evaluate("window.__opvDocumentMarker = 'zelfde-document'")
            self.open_sources(page)
            edition = page.locator("#opt-teksteditie")
            edition.focus()
            edition.select_option("nl-opv")

            page.locator('.verse-row[data-verse="1"] .col-2026').filter(has_text="hemel").wait_for()
            self.assertEqual(page.evaluate("window.__opvDocumentMarker"), "zelfde-document")
            self.assertEqual(page.evaluate("document.activeElement.id"), "opt-teksteditie")
            self.assertIn("editie=nl-opv", page.url)
            self.assertEqual(
                page.evaluate(
                    "JSON.parse(localStorage.getItem('sv2026_vertaalopties')).teksteditie"
                ),
                "nl-opv",
            )
            page.reload(wait_until="domcontentloaded")
            page.locator('.verse-row[data-verse="1"] .col-2026').filter(has_text="hemel").wait_for()
            self.assertEqual(page.locator("#opt-teksteditie").input_value(), "nl-opv")
            self.assertIn("editie=nl-opv", page.url)
        finally:
            page.close()

    def test_opv_kan_parallel_naast_open_vertaling_worden_getoond(self):
        page = self.new_page()
        try:
            page.goto(f"{self.base_url}/index.html#genesis/1", wait_until="domcontentloaded")
            page.locator('.verse-row[data-verse="1"]').wait_for()
            self.open_sources(page)
            page.locator('[data-parallel-editie="nl-opv"]').check()

            parallel = page.locator(
                '.verse-row[data-verse="1"] .parallel-edition[data-editie="nl-opv"]'
            )
            parallel.wait_for()
            self.assertIn("maakte God de hemel", parallel.inner_text())
            self.assertEqual(parallel.get_attribute("lang"), "nl")
            self.assertEqual(
                page.evaluate(
                    "JSON.parse(localStorage.getItem('sv2026_vertaalopties')).parallelEdities"
                ),
                ["nl-opv"],
            )
        finally:
            page.close()

    def test_parallelle_opv_promotie_maakt_drie_echte_parallelle_plaatsen_vrij(self):
        page = self.new_page()
        try:
            page.goto(f"{self.base_url}/index.html#genesis/1", wait_until="domcontentloaded")
            page.locator('.verse-row[data-verse="1"]').wait_for()
            self.open_sources(page)
            opv = page.locator('[data-parallel-editie="nl-opv"]')
            opv.check()
            page.locator(
                '.verse-row[data-verse="1"] .parallel-edition[data-editie="nl-opv"]'
            ).wait_for()

            page.locator("#opt-teksteditie").select_option("nl-opv")
            page.locator('.verse-row[data-verse="1"] .col-2026').filter(
                has_text="maakte God de hemel"
            ).wait_for()
            self.assertFalse(opv.is_checked())
            self.assertEqual(
                page.evaluate(
                    "JSON.parse(localStorage.getItem('sv2026_vertaalopties')).parallelEdities"
                ),
                [],
            )

            for code in ("nl-ov", "en-webbe", "fr-lsg1910"):
                page.locator(f'[data-parallel-editie="{code}"]').check()
            page.locator(
                '.verse-row[data-verse="1"] .parallel-edition[data-editie="fr-lsg1910"]'
            ).wait_for()
            self.assertEqual(
                page.evaluate(
                    "JSON.parse(localStorage.getItem('sv2026_vertaalopties')).parallelEdities"
                ),
                ["nl-ov", "en-webbe", "fr-lsg1910"],
            )
            self.assertEqual(
                page.locator('.verse-row[data-verse="1"] .parallel-edition:not(.primary-edition)').count(),
                3,
            )
            self.assertTrue(page.locator('[data-parallel-editie="ar-vd"]').is_disabled())
        finally:
            page.close()

    def test_opv_toont_buiten_pilotdekking_een_explicitiete_melding(self):
        page = self.new_page()
        try:
            page.goto(
                f"{self.base_url}/index.html?editie=nl-opv#genesis/6",
                wait_until="domcontentloaded",
            )
            unavailable = page.locator(".translation-unavailable")
            unavailable.wait_for()
            self.assertIn("Genesis is niet beschikbaar", unavailable.inner_text())
            self.assertIn("Open Parafrase Vertaling (proef)", unavailable.inner_text())
            self.assertEqual(page.locator(".verse-row").count(), 0)
        finally:
            page.close()

    def test_ov_audio_wordt_gewist_bij_onbeschikbare_opv_en_herstelt_via_link(self):
        page = self.new_page()
        observed = self.observe_runtime(page)
        try:
            page.goto(f"{self.base_url}/index.html#genesis/6", wait_until="domcontentloaded")
            ov_row = page.locator('.verse-row[data-verse="1"]')
            ov_row.wait_for()
            self.assertEqual(ov_row.get_attribute("data-status"), "final")
            self.assertTrue(page.locator("#audio-play-big").is_visible())
            self.assertIn("audio/genesis/6-m.mp3", page.locator("#audio-el").get_attribute("src"))

            observed["requests"].clear()
            self.open_sources(page)
            page.locator("#opt-teksteditie").select_option("nl-opv")
            unavailable = page.locator(".translation-unavailable")
            unavailable.wait_for()
            self.assertEqual(page.locator(".verse-row").count(), 0)
            self.assertFalse(page.locator("#audio-play-big").is_visible())
            self.assertFalse(page.locator("#audio-play-mobile").is_visible())
            self.assertIsNone(page.locator("#audio-el").get_attribute("src"))
            self.assertFalse(
                any(url.endswith("/data/edities/opv/chapters/genesis/6.json") for url in observed["requests"])
            )

            restore = unavailable.locator("a")
            self.assertIn("?editie=nl-ov#genesis/6", restore.get_attribute("href"))
            page.locator("#sidebar-right-toggle").click()
            page.locator("#sidebar-right").wait_for(state="hidden")
            page.wait_for_function("document.activeElement?.id === 'topnav-tekstopties'")
            restore.focus()
            self.assertTrue(restore.evaluate("element => element === document.activeElement"))
            restore.click()
            restored = page.locator('.verse-row[data-verse="1"]')
            restored.wait_for()
            self.assertEqual(restored.get_attribute("data-status"), "final")
            self.assertTrue(page.locator("#audio-play-big").is_visible())
            self.assertIn("audio/genesis/6-m.mp3", page.locator("#audio-el").get_attribute("src"))
            self.assertEqual(observed["pageerrors"], [])
            self.assertEqual(observed["http_errors"], [])
        finally:
            page.close()

    def test_onbeschikbare_opv_wist_alle_warme_ov_hoofdstukstatus_en_herstelt(self):
        page = self.new_page()
        observed = self.observe_runtime(page)
        try:
            page.goto(f"{self.base_url}/index.html#spreuken/1", wait_until="domcontentloaded")
            page.locator('.verse-row[data-verse="1"]').wait_for()
            page.locator("#ai-concept-banner").wait_for(state="visible")
            page.locator("#book-dating").wait_for(state="visible")
            title = page.locator("#chapter-title")
            self.assertTrue(title.evaluate("element => element.classList.contains('chapter-unverified')"))
            self.assertEqual(title.locator(".chapter-concept-tag").count(), 1)

            self.open_sources(page)
            page.locator("#opt-teksteditie").select_option("nl-opv")
            page.locator(".translation-unavailable").wait_for()
            self.assertEqual(page.locator(".verse-row").count(), 0)
            self.assertFalse(page.locator("#ai-concept-banner").is_visible())
            self.assertFalse(title.evaluate("element => element.classList.contains('chapter-unverified')"))
            self.assertEqual(title.locator(".chapter-concept-tag").count(), 0)
            self.assertFalse(page.locator("#book-dating").is_visible())
            self.assertFalse(page.locator("#ethiopic-banner").is_visible())
            self.assertFalse(page.locator("#audio-play-big").is_visible())
            self.assertIsNone(page.locator("#audio-el").get_attribute("src"))
            self.assertFalse(page.locator("#book-intro").is_visible())
            self.assertFalse(page.locator("#chapter-intro").is_visible())
            self.assertIn("Spreuken 1", title.inner_text())

            page.locator("#opt-teksteditie").select_option("nl-ov")
            page.locator('.verse-row[data-verse="1"]').wait_for()
            page.locator("#ai-concept-banner").wait_for(state="visible")
            page.locator("#book-dating").wait_for(state="visible")
            self.assertTrue(title.evaluate("element => element.classList.contains('chapter-unverified')"))
            self.assertEqual(title.locator(".chapter-concept-tag").count(), 1)
            self.assertNotIn("editie=", page.url)
            self.assertEqual(observed["pageerrors"], [])
            self.assertEqual(observed["http_errors"], [])
        finally:
            page.close()

    def test_vertraagde_ov_datering_kan_onbeschikbare_opv_niet_overschrijven(self):
        page = self.new_page()
        page.add_init_script(
            """(() => {
                const fetchNow = window.fetch.bind(window);
                window.__datingRequestStarted = false;
                let releaseDating;
                const datingGate = new Promise(resolve => { releaseDating = resolve; });
                window.__releaseDatingResponse = () => releaseDating();
                window.fetch = (...args) => {
                    const url = String(args[0]);
                    if (url.endsWith('data/book-dating.json')) {
                        window.__datingRequestStarted = true;
                        return datingGate.then(() => fetchNow(...args));
                    }
                    return fetchNow(...args);
                };
            })();"""
        )
        observed = self.observe_runtime(page)
        try:
            page.goto(f"{self.base_url}/index.html#spreuken/1", wait_until="domcontentloaded")
            page.locator('.verse-row[data-verse="1"]').wait_for()
            page.wait_for_function("window.__datingRequestStarted")

            self.open_sources(page)
            page.locator("#opt-teksteditie").select_option("nl-opv")
            page.locator(".translation-unavailable").wait_for()
            page.evaluate("window.__releaseDatingResponse()")
            page.wait_for_function("App._bookDating && App._bookDating.spreuken")

            stale_dating = page.evaluate(
                """() => {
                    const box = document.getElementById('book-dating');
                    return {
                        visible: !!box && getComputedStyle(box).display !== 'none',
                        text: box ? box.textContent.trim() : '',
                    };
                }"""
            )
            self.assertFalse(stale_dating["visible"])
            self.assertEqual(stale_dating["text"], "")

            page.locator("#opt-teksteditie").select_option("nl-ov")
            page.locator('.verse-row[data-verse="1"]').wait_for()
            page.locator("#book-dating").wait_for(state="visible")
            self.assertIn("Schrijftijd:", page.locator("#book-dating").inner_text())

            page.locator("#opt-teksteditie").select_option("nl-opv")
            page.locator(".translation-unavailable").wait_for()
            page.evaluate("location.hash = '#genesis/1'")
            page.locator('.verse-row[data-verse="1"] .col-2026').filter(
                has_text="maakte God de hemel"
            ).wait_for()
            page.locator("#book-dating").wait_for(state="visible")
            self.assertIn("Schrijftijd:", page.locator("#book-dating").inner_text())
            self.assertEqual(observed["pageerrors"], [])
            self.assertEqual(observed["http_errors"], [])
        finally:
            page.close()

    def test_opv_prefetch_respecteert_werkelijk_gepubliceerde_hoofdstukken(self):
        page = self.new_page()
        page.add_init_script(
            """window.__opvIdleCallbacks = 0;
               window.requestIdleCallback = callback => {
                   window.__opvIdleCallbacks += 1;
                   setTimeout(() => callback({ didTimeout: false, timeRemaining: () => 50 }), 0);
                   return window.__opvIdleCallbacks;
               };"""
        )
        observed = self.observe_runtime(page)
        try:
            page.goto(
                f"{self.base_url}/index.html?editie=nl-opv#genesis/1",
                wait_until="domcontentloaded",
            )
            page.locator('.verse-row[data-verse="1"]').wait_for()
            page.wait_for_function("window.__opvIdleCallbacks > 0")
            page.wait_for_timeout(250)
            opv_requests = [
                url for url in observed["requests"] if "/data/edities/opv/chapters/" in url
            ]
            self.assertTrue(any(url.endswith("/genesis/2.json") for url in opv_requests))
            self.assertFalse(any(url.endswith("/genesis/6.json") for url in opv_requests))
            observed["requests"].clear()
            page.goto(
                f"{self.base_url}/index.html?editie=nl-opv#johannes/1",
                wait_until="domcontentloaded",
            )
            page.locator('.verse-row[data-verse="52"]').wait_for()
            page.wait_for_function("window.__opvIdleCallbacks > 0")
            page.wait_for_timeout(250)
            opv_requests = [
                url for url in observed["requests"] if "/data/edities/opv/chapters/" in url
            ]
            self.assertFalse(any(url.endswith("/johannes/2.json") for url in opv_requests))
            self.assertFalse(any(url.endswith("/johannes/6.json") for url in opv_requests))
            self.assertEqual(observed["pageerrors"], [])
            self.assertEqual(observed["console_errors"], [])
            self.assertEqual(observed["http_errors"], [])
        finally:
            page.close()

    def test_wiki_citaat_volgt_de_globale_opv_editie_en_bronnaam(self):
        page = self.new_page({"teksteditie": "nl-opv"})
        try:
            page.goto(
                f"{self.base_url}/liederen.html?item=lied-bij-de-schelfzee",
                wait_until="domcontentloaded",
            )
            page.wait_for_function("typeof window.OSV !== 'undefined'")
            citation = page.evaluate(
                """async () => {
                    const result = await OSV.cite('genesis 1:1');
                    return {
                        edition: result.editie,
                        language: result.taal,
                        html: result.html,
                        plain: result.plain,
                    };
                }"""
            )
            self.assertEqual(citation["edition"], "nl-opv")
            self.assertEqual(citation["language"], "nl")
            self.assertIn("In het begin maakte God", citation["plain"])
            self.assertIn("Open Parafrase Vertaling (proef)", citation["html"])
            self.assertNotIn("(Open Vertaling)", citation["html"])
        finally:
            page.close()

    def test_echte_wiki_refresh_bewaart_url_en_item_en_ververst_bronlink(self):
        page = self.new_page()
        observed = self.observe_runtime(page)
        try:
            page.goto(f"{self.base_url}/wiki.html#dieren", wait_until="domcontentloaded")
            page.locator("#wiki-frame").evaluate(
                "frame => { frame.src = 'dieren.html?item=vee'; }"
            )
            frame = page.frame_locator("#wiki-frame")
            item = frame.locator('.gt-vers[data-ref="genesis 1:24"]')
            item.locator(".ov-naslagtekst .osv-vers").first.wait_for(timeout=15_000)
            wiki_url = page.url
            frame_url = page.locator("#wiki-frame").evaluate("frame => frame.contentWindow.location.href")

            self.open_sources(page)
            page.locator("#opt-teksteditie").select_option("nl-opv")
            page.wait_for_function(
                """() => {
                    const frame = document.getElementById('wiki-frame');
                    const item = frame && frame.contentDocument &&
                        frame.contentDocument.querySelector('.gt-vers[data-ref="genesis 1:24"]');
                    const citation = item && item.querySelector('.ov-naslagtekst');
                    return citation && citation.dataset.osvEditie === 'nl-opv';
                }""",
                timeout=15_000,
            )
            citation = item.locator(".ov-naslagtekst")
            self.assertIn("Laat de aarde levende wezens", citation.inner_text())
            self.assertEqual(citation.get_attribute("lang"), "nl")
            self.assertEqual(citation.get_attribute("data-osv-editie"), "nl-opv")
            self.assertEqual(
                item.locator(".gt-vers-kop > a").get_attribute("href"),
                "index.html?editie=nl-opv#genesis/1/24",
            )
            self.assertEqual(page.url, wiki_url)
            self.assertEqual(
                page.locator("#wiki-frame").evaluate("frame => frame.contentWindow.location.href"),
                frame_url,
            )
            self.assertIn("?item=vee", frame_url)
            self.assertEqual(observed["pageerrors"], [])
            self.assertEqual(observed["http_errors"], [])
        finally:
            page.close()

    def test_opv_erft_geen_ov_verificatiestatus_of_audio(self):
        page = self.new_page()
        try:
            page.goto(
                f"{self.base_url}/index.html?editie=nl-opv#genesis/1",
                wait_until="domcontentloaded",
            )
            row = page.locator('.verse-row[data-verse="1"]')
            row.wait_for()
            self.assertEqual(row.get_attribute("data-status"), "concept")
            self.assertFalse(page.locator("#audio-play-big").is_visible())
            self.assertFalse(page.locator("#audio-play-mobile").is_visible())
            self.assertEqual(page.locator("#ai-concept-banner:visible").count(), 0)
            self.assertEqual(page.locator("#chapter-title .chapter-concept-tag").count(), 0)

            self.open_sources(page)
            page.locator("#opt-teksteditie").select_option("nl-ov")
            restored = page.locator('.verse-row[data-verse="1"]')
            page.wait_for_function(
                "document.querySelector('.verse-row[data-verse=\"1\"]')?.dataset.status === 'final'"
            )
            self.assertEqual(restored.get_attribute("data-status"), "final")
            self.assertNotIn("editie=", page.url)
            self.assertTrue(page.locator("#audio-play-big").is_visible())
            self.assertIn("audio/genesis/1-m.mp3", page.locator("#audio-el").get_attribute("src"))
        finally:
            page.close()


if __name__ == "__main__":
    unittest.main()
