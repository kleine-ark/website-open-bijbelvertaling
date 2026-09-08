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

    def new_page(self, settings=None, viewport=None):
        page = self.browser.new_page(
            viewport=viewport or {"width": 1280, "height": 900},
            service_workers="block",
        )
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

            flow = page.locator('.opv-reading-flow[data-book="genesis"][data-chapter="1"]')
            self.assertEqual(flow.count(), 1)
            self.assertEqual(page.locator("#verses-container > .opv-reading-flow").count(), 1)
            self.assertEqual(flow.get_attribute("aria-labelledby"), "chapter-title")
            self.assertEqual(page.locator("#chapter-title").evaluate("el => el.tagName"), "H2")
            self.assertIn("Genesis 1", page.locator("#chapter-title").inner_text())
            self.assertEqual(flow.locator(".opv-passage").count(), 7)
            self.assertEqual(
                flow.locator(".opv-passage-title").evaluate_all(
                    "titles => titles.map(title => title.tagName)"
                ),
                ["H3"] * 7,
            )
            self.assertEqual(flow.locator(".verse-row.opv-verse").count(), 31)
            self.assertEqual(flow.locator(".opv-verse-anchor").count(), 31)
            self.assertEqual(page.locator("#verses-container > .verse-row").count(), 0)
            self.assertEqual(
                flow.locator(".opv-passage").evaluate_all(
                    "els => els.map(el => [el.dataset.blockId, el.dataset.range, "
                    "el.querySelector('.opv-passage-title').textContent.trim()])"
                ),
                [
                    ["gen-1-b1", "1-2", "Het begin"],
                    ["gen-1-b2", "3-5", "Licht en donker"],
                    ["gen-1-b3", "6-8", "Het hemelgewelf"],
                    ["gen-1-b4", "9-13", "Land en planten"],
                    ["gen-1-b5", "14-19", "Lichten aan de hemel"],
                    ["gen-1-b6", "20-23", "Dieren in het water en vogels"],
                    ["gen-1-b7", "24-31", "Landdieren en mensen"],
                ],
            )
            self.assertEqual(
                flow.locator(".opv-verse").evaluate_all(
                    "els => els.map(el => Number(el.dataset.verse))"
                ),
                list(range(1, 32)),
            )
            first_anchor = flow.locator('.opv-verse[data-verse="1"] .opv-verse-anchor')
            self.assertEqual(first_anchor.get_attribute("href"), "#genesis/1/1")
            self.assertEqual(first_anchor.get_attribute("data-col"), "num")
            self.assertEqual(first_anchor.get_attribute("aria-label"), "Genesis 1 vers 1")
            self.assertEqual(first_anchor.get_attribute("tabindex"), "0")
            self.assertEqual(
                flow.locator('.opv-verse[data-verse="1"] .opv-verse-text').get_attribute("data-col"),
                "2026",
            )

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

    def test_opv_toont_buiten_gepubliceerde_dekking_een_explicitiete_melding(self):
        page = self.new_page()
        try:
            page.goto(
                f"{self.base_url}/index.html?editie=nl-opv#genesis/26",
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
            page.goto(f"{self.base_url}/index.html#genesis/26", wait_until="domcontentloaded")
            ov_row = page.locator('.verse-row[data-verse="1"]')
            ov_row.wait_for()
            self.assertEqual(ov_row.get_attribute("data-status"), "final")
            self.assertTrue(page.locator("#audio-play-big").is_visible())
            self.assertIn("audio/genesis/26-m.mp3", page.locator("#audio-el").get_attribute("src"))

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
                any(url.endswith("/data/edities/opv/chapters/genesis/26.json") for url in observed["requests"])
            )

            restore = unavailable.locator("a")
            self.assertIn("?editie=nl-ov#genesis/26", restore.get_attribute("href"))
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
            self.assertIn("audio/genesis/26-m.mp3", page.locator("#audio-el").get_attribute("src"))
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
            self.assertFalse(any(url.endswith("/genesis/26.json") for url in opv_requests))
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
            self.assertTrue(any(url.endswith("/johannes/2.json") for url in opv_requests))
            self.assertFalse(any(url.endswith("/johannes/6.json") for url in opv_requests))
            observed["requests"].clear()
            page.goto(
                f"{self.base_url}/index.html?editie=nl-opv#johannes/5",
                wait_until="domcontentloaded",
            )
            page.locator('.verse-row[data-verse="47"]').wait_for()
            page.wait_for_function("window.__opvIdleCallbacks > 0")
            page.wait_for_timeout(250)
            opv_requests = [
                url for url in observed["requests"] if "/data/edities/opv/chapters/" in url
            ]
            self.assertTrue(any(url.endswith("/johannes/4.json") for url in opv_requests))
            self.assertFalse(any(url.endswith("/johannes/6.json") for url in opv_requests))
            self.assertEqual(observed["pageerrors"], [])
            self.assertEqual(observed["console_errors"], [])
            self.assertEqual(observed["http_errors"], [])
        finally:
            page.close()

    def test_johannes_two_to_five_render_all_verses_and_preserve_annotations(self):
        expected = {2: (25, "De bruiloft in Kana en de tempel in Jeruzalem"),
                    3: (36, "Nieuw leven van God"),
                    4: (54, "Jezus geeft levend water"),
                    5: (47, "Jezus geeft leven")}
        for number, (count, heading) in expected.items():
            with self.subTest(chapter=number):
                page = self.new_page()
                observed = self.observe_runtime(page)
                try:
                    page.goto(f"{self.base_url}/index.html?editie=nl-opv#johannes/{number}",
                              wait_until="domcontentloaded")
                    page.locator(f'.verse-row[data-verse="{count}"] .col-2026').wait_for()
                    raw = json.loads((ROOT / f"data/edities/opv/chapters/johannes/{number}.json")
                                     .read_text(encoding="utf-8"))
                    self.assertEqual(count, page.locator(".verse-row[data-verse]").count())
                    for verse in raw["verzen"]:
                        rendered = page.locator(f'.verse-row[data-verse="{verse["nummer"]}"] .col-2026')
                        self.assertTrue(rendered.is_visible())
                        self.assertIn(verse["tekst"], rendered.text_content())
                    normalized = page.evaluate(
                        """async n => {
                            const c = await TekstEditie.loadChapterForEdition('nl-opv', 'johannes', n);
                            return {heading: c.heading, blocks: c.blokken,
                                verses: c.verses.map(v => ({number: v.number, bron: v.bron,
                                    segmenten: v.segmenten, begrippen: v.begrippen,
                                    citaten: v.citaten, review: v.review}))};
                        }""", number)
                    self.assertEqual(heading, normalized["heading"])
                    self.assertEqual(raw["blokken"], normalized["blocks"])
                    self.assertEqual([{"number": v["nummer"], **{key: v[key] for key in
                                      ("bron", "segmenten", "begrippen", "citaten", "review")}}
                                      for v in raw["verzen"]], normalized["verses"])
                    self.assertEqual([], observed["pageerrors"])
                    self.assertEqual([], observed["http_errors"])
                finally:
                    page.close()

    def test_alle_opv_hoofdstukken_hebben_exacte_boekstructuur_en_annotaties(self):
        expected = {
            ("genesis", 1): (31, 7, 15, 13, 78),
            ("genesis", 2): (25, 6, 15, 4, 58),
            ("genesis", 3): (24, 6, 7, 20, 57),
            ("genesis", 4): (26, 5, 9, 14, 55),
            ("genesis", 5): (32, 5, 5, 1, 43),
            ("johannes", 1): (52, 7, 45, 36, 180),
            ("johannes", 2): (25, 4, 16, 11, 69),
            ("johannes", 3): (36, 5, 49, 33, 133),
            ("johannes", 4): (54, 8, 29, 41, 143),
            ("johannes", 5): (47, 5, 40, 39, 131),
        }
        page = self.new_page()
        observed = self.observe_runtime(page)
        totals = [0, 0, 0, 0, 0]
        try:
            page.goto(f"{self.base_url}/index.html?editie=nl-opv#genesis/1",
                      wait_until="domcontentloaded")
            page.locator(".opv-reading-flow").wait_for()
            for (book, chapter), wanted in expected.items():
                actual = page.evaluate(
                    """async ([book, chapter]) => {
                        await App.renderChapter(book, chapter);
                        const flow = document.querySelector('.opv-reading-flow');
                        return [
                            flow.querySelectorAll('.opv-verse-anchor').length,
                            flow.querySelectorAll('.opv-passage').length,
                            flow.querySelectorAll('[data-opv-concept]').length,
                            flow.querySelectorAll('[data-opv-citation]').length,
                            flow.querySelectorAll('[data-opv-segment]').length,
                        ];
                    }""",
                    [book, chapter],
                )
                self.assertEqual(actual, list(wanted), f"{book} {chapter}")
                self.assertEqual(page.locator(".opv-reading-flow").count(), 1)
                self.assertEqual(page.locator(".opv-reading-flow .verse-row.opv-verse").count(), wanted[0])
                totals = [a + b for a, b in zip(totals, actual)]
            self.assertEqual(totals, [352, 58, 230, 212, 947])
            self.assertEqual(observed["pageerrors"], [])
        finally:
            page.close()

    def test_opv_segmenttekst_wordt_nooit_als_html_uitgevoerd(self):
        payload = json.loads(
            (ROOT / "data/edities/opv/chapters/genesis/1.json").read_text(encoding="utf-8")
        )
        injected = '<img src=x onerror="window.__opvInjected=true"> & letterlijk'
        payload["verzen"][0]["segmenten"][0]["tekst"] = injected
        payload["verzen"][0]["tekst"] = "".join(
            segment["tekst"] for segment in payload["verzen"][0]["segmenten"]
        )
        page = self.new_page()
        page.route(
            "**/data/edities/opv/chapters/genesis/1.json",
            lambda route: route.fulfill(
                status=200, content_type="application/json", body=json.dumps(payload)
            ),
        )
        try:
            page.goto(f"{self.base_url}/index.html?editie=nl-opv#genesis/1",
                      wait_until="domcontentloaded")
            text = page.locator('.opv-verse[data-verse="1"] .opv-verse-text')
            text.wait_for()
            self.assertIn(injected, text.text_content())
            self.assertEqual(text.locator('img:not(.dropcap-image), img[src="x"]').count(), 0)
            self.assertFalse(page.evaluate("Boolean(window.__opvInjected)"))
        finally:
            page.close()

    def test_geneste_citaten_volgen_globale_toggle_zonder_rerender_of_tekstverlies(self):
        page = self.new_page()
        try:
            page.goto(f"{self.base_url}/index.html?editie=nl-opv#johannes/3",
                      wait_until="domcontentloaded")
            verse = page.locator('.opv-verse[data-verse="7"] .opv-verse-text')
            verse.wait_for()
            outer = verse.locator('[data-opv-citation="JHN.3.7.q1"]')
            inner = outer.locator('[data-opv-citation="JHN.3.7.q2"]')
            self.assertEqual(outer.count(), 1)
            self.assertEqual(inner.count(), 1)
            self.assertTrue(outer.evaluate("el => el.classList.contains('god-speaks')"))
            self.assertEqual(outer.get_attribute("data-opv-citation-semantic"),
                             "spraak.jezus.jhn3v7q1")
            self.assertEqual(outer.get_attribute("data-opv-speaker"), "jezus")
            self.assertEqual(outer.get_attribute("data-opv-speaker-type"), "god")
            citation_fixture = page.evaluate(
                """() => {
                    const verse = document.querySelector('.opv-verse[data-verse="7"] .opv-verse-text');
                    const fixture = document.createElement('span');
                    fixture.className = 'opv-citation-fixture';
                    for (const speakerClass of ['direct-speech', 'god-speaks', 'angel-speaks']) {
                        const wrapper = document.createElement('span');
                        wrapper.className = `opv-citation ${speakerClass}`;
                        const concept = document.createElement('button');
                        concept.type = 'button';
                        concept.className = 'opv-concept';
                        concept.dataset.opvConcept = speakerClass;
                        concept.textContent = speakerClass;
                        wrapper.appendChild(concept);
                        fixture.appendChild(wrapper);
                    }
                    verse.append(' ', fixture);
                    const angel = fixture.querySelector('.angel-speaks');
                    return {
                        before:getComputedStyle(angel, '::before').content,
                        after:getComputedStyle(angel, '::after').content,
                    };
                }"""
            )
            self.assertNotIn(citation_fixture["before"], ("none", "normal", '""'))
            self.assertNotIn(citation_fixture["after"], ("none", "normal", '""'))
            before_text = verse.text_content()
            outer.evaluate("el => { el.__sameCitationNode = true; }")

            page.locator("#topnav-tekstopties").click()
            page.locator('details[data-options-category="weergave"]').evaluate(
                "element => { element.open = true; }"
            )
            toggle = page.locator("#toggle-citaten")
            toggle.uncheck()
            self.assertTrue(page.locator("body").evaluate("el => el.classList.contains('citaten-uit')"))
            self.assertTrue(outer.evaluate("el => el.__sameCitationNode === true"))
            self.assertEqual(verse.text_content(), before_text)
            neutral_light = verse.evaluate(
                """el => {
                    const failures = [...el.querySelectorAll(
                        '.opv-citation, .opv-citation [data-opv-concept]'
                    )].map(node => {
                        const own=getComputedStyle(node), parent=getComputedStyle(node.parentElement);
                        return {tag:node.tagName, classes:node.className, color:own.color,
                            parentColor:parent.color, style:own.fontStyle,
                            parentStyle:parent.fontStyle, weight:own.fontWeight,
                            parentWeight:parent.fontWeight};
                    }).filter(item => item.color!==item.parentColor ||
                        item.style!==item.parentStyle || item.weight!==item.parentWeight);
                    return {
                        descendants: failures.length === 0,
                        failures,
                        pseudos:[...el.querySelectorAll('.opv-citation-fixture .opv-citation')]
                            .every(node => ['none','normal','""'].includes(
                                getComputedStyle(node, '::before').content
                            ) && ['none','normal','""'].includes(
                                getComputedStyle(node, '::after').content
                            )),
                    };
                }"""
            )
            self.assertTrue(neutral_light["descendants"], neutral_light["failures"])
            self.assertTrue(neutral_light["pseudos"])

            page.evaluate("document.documentElement.dataset.theme='donker'")
            neutral_dark = verse.evaluate(
                """el => [...el.querySelectorAll(
                    '.opv-citation, .opv-citation [data-opv-concept]'
                )].every(node => {
                    const own=getComputedStyle(node), parent=getComputedStyle(node.parentElement);
                    return own.color===parent.color && own.fontStyle===parent.fontStyle &&
                        own.fontWeight===parent.fontWeight;
                })"""
            )
            self.assertTrue(neutral_dark)
            toggle.check()
            self.assertFalse(page.locator("body").evaluate("el => el.classList.contains('citaten-uit')"))
            self.assertTrue(outer.evaluate("el => el.__sameCitationNode === true"))
            self.assertEqual(verse.text_content(), before_text)
        finally:
            page.close()

    def test_exact_begrip_is_veilig_toetsenbordvriendelijk_en_sluit_met_focus_return(self):
        registry = json.loads(
            (ROOT / "data/edities/opv/concepten.json").read_text(encoding="utf-8")
        )
        concept = next(item for item in registry["concepten"] if item["id"] == "farizeeen")
        concept["label"] = '<img src=x onerror="window.__conceptInjected=true"> Farizeeën'
        concept["uitleg"] = '<script>window.__conceptInjected=true</script> veilige uitleg'
        page = self.new_page()
        concept_requests = []

        def fulfill_registry(route):
            concept_requests.append(route.request.url)
            route.fulfill(status=200, content_type="application/json", body=json.dumps(registry))

        page.route("**/data/edities/opv/concepten.json", fulfill_registry)
        try:
            page.goto(f"{self.base_url}/index.html?editie=nl-opv#johannes/3",
                      wait_until="domcontentloaded")
            trigger = page.locator('[data-opv-concept="farizeeen"]').first
            trigger.wait_for()
            self.assertEqual(trigger.evaluate("el => el.tagName"), "BUTTON")
            self.assertEqual(trigger.get_attribute("type"), "button")
            self.assertEqual(trigger.get_attribute("aria-expanded"), "false")
            self.assertEqual(trigger.get_attribute("aria-controls"), "opv-concept-dialog")
            trigger.focus()
            page.keyboard.press("Enter")
            dialog = page.locator("#opv-concept-dialog")
            dialog.wait_for(state="visible")
            self.assertEqual(trigger.get_attribute("aria-expanded"), "true")
            self.assertEqual(dialog.get_attribute("tabindex"), "-1")
            self.assertTrue(dialog.evaluate("el => el.contains(document.activeElement)"))
            page.keyboard.press("Tab")
            self.assertTrue(dialog.evaluate("el => el.contains(document.activeElement)"))
            page.keyboard.press("Shift+Tab")
            self.assertTrue(dialog.evaluate("el => el.contains(document.activeElement)"))
            fallback_focus = dialog.evaluate(
                """el => {
                    el.querySelector('.opv-concept-close').hidden = true;
                    el.focus();
                    return document.activeElement === el;
                }"""
            )
            self.assertTrue(fallback_focus)
            page.keyboard.press("Tab")
            self.assertTrue(dialog.evaluate("el => document.activeElement === el"))
            dialog.evaluate(
                """el => {
                    const close = el.querySelector('.opv-concept-close');
                    close.hidden = false;
                    close.focus();
                }"""
            )
            self.assertEqual(dialog.locator(".opv-concept-title").text_content(), concept["label"])
            self.assertEqual(dialog.locator(".opv-concept-explanation").text_content(), concept["uitleg"])
            self.assertEqual(dialog.locator("img, script").count(), 0)
            self.assertFalse(page.evaluate("Boolean(window.__conceptInjected)"))
            page.keyboard.press("Escape")
            dialog.wait_for(state="hidden")
            self.assertEqual(trigger.get_attribute("aria-expanded"), "false")
            self.assertTrue(trigger.evaluate("el => el === document.activeElement"))

            second = page.locator("[data-opv-concept]").nth(1)
            second.focus()
            page.keyboard.press("Space")
            dialog.wait_for(state="visible")
            dialog.locator(".opv-concept-close").click()
            self.assertEqual(len(concept_requests), 1)

            trigger.focus()
            page.keyboard.press("Enter")
            dialog.wait_for(state="visible")
            closed = page.evaluate(
                """() => {
                    const trigger = document.querySelector('[data-opv-concept="farizeeen"]');
                    App._closeOpvConcept(true);
                    return {
                        open: document.getElementById('opv-concept-dialog').open,
                        expanded: trigger.getAttribute('aria-expanded'),
                        triggerCleared: App._opvConceptTrigger === null,
                        restoreCleared: App._opvRestoreConceptFocus === false,
                        focused: document.activeElement === trigger,
                    };
                }"""
            )
            self.assertEqual(closed, {
                "open": False,
                "expanded": "false",
                "triggerCleared": True,
                "restoreCleared": True,
                "focused": True,
            })
            repeated = page.evaluate(
                """() => {
                    App._closeOpvConcept(true);
                    return {
                        open: document.getElementById('opv-concept-dialog').open,
                        triggerCleared: App._opvConceptTrigger === null,
                        restoreCleared: App._opvRestoreConceptFocus === false,
                    };
                }"""
            )
            self.assertEqual(repeated, {
                "open": False,
                "triggerCleared": True,
                "restoreCleared": True,
            })

            before = trigger.text_content()
            page.evaluate("Begrippen.toggle(false)")
            self.assertEqual(trigger.text_content(), before)
            self.assertEqual(trigger.get_attribute("tabindex"), "-1")
            self.assertTrue(trigger.evaluate("el => el.classList.contains('opv-concept-disabled')"))
            page.evaluate("Begrippen.toggle(true)")
            self.assertEqual(trigger.get_attribute("tabindex"), "0")
            self.assertEqual(page.locator(".opv-reading-flow .begrip-link").count(), 0)
        finally:
            page.close()

    def test_vertraagd_begrippenregister_mag_na_editiewissel_niets_openen(self):
        page = self.new_page()
        page.add_init_script(
            """(() => {
                const fetchNow = window.fetch.bind(window);
                let release;
                const gate = new Promise(resolve => { release = resolve; });
                window.__releaseOpvConcepts = () => release();
                window.fetch = (...args) => String(args[0]).endsWith('data/edities/opv/concepten.json')
                    ? gate.then(() => fetchNow(...args)) : fetchNow(...args);
            })();"""
        )
        try:
            page.goto(f"{self.base_url}/index.html?editie=nl-opv#johannes/3",
                      wait_until="domcontentloaded")
            page.locator('[data-opv-concept="farizeeen"]').click()
            page.evaluate("TekstEditie.setCode('nl-ov'); App.renderChapter('johannes', 3)")
            page.locator('.verse-row:not(.opv-verse)[data-verse="1"]').wait_for()
            page.evaluate("window.__releaseOpvConcepts()")
            page.wait_for_timeout(150)
            self.assertEqual(page.locator(".opv-reading-flow").count(), 0)
            self.assertEqual(page.locator("#opv-concept-dialog:visible").count(), 0)
        finally:
            page.close()

    def test_parallelpaden_en_editiewissel_behouden_elk_hun_eigen_dom(self):
        page = self.new_page({"teksteditie": "nl-opv", "parallelEdities": ["nl-ov"]})
        try:
            page.goto(f"{self.base_url}/index.html?editie=nl-opv#genesis/1",
                      wait_until="domcontentloaded")
            flow = page.locator(".opv-reading-flow")
            flow.wait_for()
            self.assertEqual(flow.locator('.parallel-edition.primary-edition[data-editie="nl-opv"]').count(), 31)
            self.assertEqual(flow.locator('.parallel-edition[data-editie="nl-ov"]').count(), 31)
            self.assertIn("In het begin", flow.locator('.opv-verse[data-verse="1"] .parallel-edition[data-editie="nl-ov"]').inner_text())

            page.evaluate(
                """async () => {
                    Opties.state.teksteditie = 'nl-ov';
                    Opties.state.parallelEdities = ['nl-opv'];
                    Opties.save();
                    TekstEditie.setCode('nl-ov');
                    await App.renderChapter('genesis', 1);
                }"""
            )
            legacy = page.locator('.verse-row:not(.opv-verse)[data-verse="1"]')
            legacy.wait_for()
            self.assertEqual(page.locator(".opv-reading-flow").count(), 0)
            self.assertEqual(page.locator("#verses-container > .verse-row").count(), 31)
            self.assertEqual(page.locator('.parallel-edition[data-editie="nl-opv"]').count(), 31)

            page.evaluate(
                """async () => {
                    Opties.state.teksteditie = 'nl-opv';
                    Opties.state.parallelEdities = [];
                    Opties.save();
                    TekstEditie.setCode('nl-opv');
                    await App.renderChapter('genesis', 1);
                }"""
            )
            page.locator(".opv-reading-flow").wait_for()
            self.assertEqual(page.locator("#verses-container > .verse-row").count(), 0)
            self.assertEqual(page.locator(".verse-row.opv-verse").count(), 31)
        finally:
            page.close()

    def test_begrippen_scannen_alleen_niet_opv_in_beide_parallelrichtingen(self):
        page = self.new_page({"teksteditie": "nl-opv", "parallelEdities": ["nl-ov"]})
        try:
            page.goto(f"{self.base_url}/index.html?editie=nl-opv#genesis/1",
                      wait_until="domcontentloaded")
            flow = page.locator(".opv-reading-flow")
            flow.wait_for()
            page.evaluate("async () => { Begrippen.active=false; await Begrippen.toggle(true); }")

            opv_primary = flow.locator('.parallel-edition[data-editie="nl-opv"]')
            ov_parallel = flow.locator('.parallel-edition[data-editie="nl-ov"]')
            self.assertEqual(opv_primary.locator("[data-opv-segment]").count(), 78)
            self.assertEqual(opv_primary.locator("[data-opv-concept]").count(), 15)
            self.assertEqual(opv_primary.locator(".opv-citation").count(), 13)
            self.assertEqual(opv_primary.locator(".begrip-link").count(), 0)
            self.assertGreater(ov_parallel.locator(".begrip-link").count(), 0)

            page.evaluate(
                """async () => {
                    await Begrippen.toggle(false);
                    const checkbox = document.getElementById('toggle-begrippen');
                    if (checkbox) checkbox.checked = false;
                    Begrippen.active = false;
                    Opties.state.teksteditie = 'nl-ov';
                    Opties.state.parallelEdities = ['nl-opv'];
                    Opties.save();
                    TekstEditie.setCode('nl-ov');
                    await App.renderChapter('genesis', 1);
                    await Begrippen.toggle(true);
                }"""
            )
            legacy = page.locator('.verse-row:not(.opv-verse)[data-verse="1"]')
            legacy.wait_for()
            opv_parallel = page.locator('.parallel-edition[data-editie="nl-opv"]')
            ov_primary = page.locator('.parallel-edition.primary-edition[data-editie="nl-ov"]')
            self.assertEqual(opv_parallel.locator("[data-opv-segment]").count(), 78)
            self.assertEqual(opv_parallel.locator("[data-opv-concept]").count(), 15)
            self.assertEqual(opv_parallel.locator(".opv-citation").count(), 13)
            self.assertEqual(opv_parallel.locator(".begrip-link").count(), 0)
            self.assertGreater(ov_primary.locator(".begrip-link").count(), 0)
            opv_parallel.locator('[data-opv-concept]').first.click()
            page.wait_for_timeout(150)
            self.assertEqual(page.locator("#opv-concept-dialog:visible").count(), 1)
            self.assertTrue(page.locator("#opv-concept-dialog .opv-concept-title").inner_text())
        finally:
            page.close()

    def test_versanker_hashfocus_en_reduced_motion_blijven_werken(self):
        page = self.new_page()
        page.emulate_media(reduced_motion="reduce")
        try:
            page.goto(f"{self.base_url}/index.html?editie=nl-opv#johannes/3/16",
                      wait_until="domcontentloaded")
            row = page.locator('.opv-verse[data-verse="16"]')
            row.wait_for()
            anchor = row.locator(".opv-verse-anchor")
            self.assertEqual(anchor.get_attribute("href"), "#johannes/3/16")
            page.evaluate(
                """() => {
                    const row = document.querySelector('.opv-verse[data-verse="16"]');
                    row.scrollIntoView = options => { window.__opvScrollOptions = options; };
                    App.focusVerse('johannes', 3, 16);
                }"""
            )
            page.wait_for_function("window.__opvScrollOptions")
            self.assertEqual(page.evaluate("window.__opvScrollOptions.behavior"), "auto")
            self.assertFalse(row.evaluate("el => el.classList.contains('verse-flash')"))
            anchor.click()
            self.assertTrue(page.url.endswith("#johannes/3/16"))
        finally:
            page.close()

    def test_verouderde_normale_render_publiceert_na_nieuw_hoofdstuk_niets(self):
        page = self.new_page({"teksteditie": "nl-opv", "parallelEdities": ["nl-ov"]})
        try:
            page.goto(f"{self.base_url}/index.html?editie=nl-opv#genesis/1",
                      wait_until="domcontentloaded")
            page.locator('.opv-reading-flow[data-chapter="1"]').wait_for()
            page.evaluate(
                """() => {
                    const original = TekstEditie.loadChapterForEdition.bind(TekstEditie);
                    let release;
                    const gate = new Promise(resolve => { release = resolve; });
                    window.__releaseStaleNormal = release;
                    window.__staleNormalHeld = false;
                    TekstEditie.loadChapterForEdition = async (code, book, chapter) => {
                        if (code === 'nl-ov' && book === 'genesis' && chapter === 2) {
                            window.__staleNormalHeld = true;
                            await gate;
                        }
                        return original(code, book, chapter);
                    };
                    Navigation.currentBook = 'genesis';
                    Navigation.currentChapter = 2;
                    window.__staleNormalRender = App.renderChapter('genesis', 2);
                }"""
            )
            page.wait_for_function("window.__staleNormalHeld")

            page.evaluate(
                """async () => {
                    Navigation.currentBook = 'johannes';
                    Navigation.currentChapter = 1;
                    await App.renderChapter('johannes', 1);
                }"""
            )
            page.locator('.opv-reading-flow[data-book="johannes"][data-chapter="1"]').wait_for()
            page.evaluate(
                """async () => {
                    window.__releaseStaleNormal();
                    await window.__staleNormalRender;
                }"""
            )

            self.assertEqual(page.locator(".opv-reading-flow").count(), 1)
            self.assertEqual(
                page.locator(".opv-reading-flow").get_attribute("data-book"), "johannes"
            )
            self.assertEqual(
                page.locator(".opv-reading-flow").get_attribute("data-chapter"), "1"
            )
            self.assertEqual(page.evaluate("App._currentPrimaryEditionCode"), "nl-opv")
            self.assertIn("Johannes 1", page.locator("#chapter-title").inner_text())
        finally:
            page.close()

    def test_hashnavigatie_invalideert_oude_render_al_voor_nieuwe_render_start(self):
        page = self.new_page({"teksteditie": "nl-opv", "parallelEdities": []})
        try:
            page.goto(
                f"{self.base_url}/index.html?editie=nl-opv#genesis/1",
                wait_until="domcontentloaded",
            )
            page.locator('.opv-reading-flow[data-book="genesis"][data-chapter="1"]').wait_for()
            page.evaluate(
                """() => {
                    const loadChapter = DataLoader.loadChapter.bind(DataLoader);
                    let releaseChapter;
                    const chapterGate = new Promise(resolve => { releaseChapter = resolve; });
                    window.__releaseOldHashRender = releaseChapter;
                    window.__oldHashRenderHeld = false;
                    DataLoader.prefetchAdjacent = () => {};
                    DataLoader.loadChapter = async (book, chapter) => {
                        if (book === 'genesis' && Number(chapter) === 2) {
                            window.__oldHashRenderHeld = true;
                            await chapterGate;
                        }
                        return loadChapter(book, chapter);
                    };

                    const renderChapterNav = Navigation.renderChapterNav.bind(Navigation);
                    let releaseNavigation;
                    const navigationGate = new Promise(resolve => { releaseNavigation = resolve; });
                    window.__releaseNewHashNavigation = releaseNavigation;
                    window.__newHashNavigationHeld = false;
                    Navigation.renderChapterNav = async book => {
                        if (book === 'johannes') {
                            window.__newHashNavigationHeld = true;
                            await navigationGate;
                        }
                        return renderChapterNav(book);
                    };

                    Navigation.currentBook = 'genesis';
                    Navigation.currentChapter = 2;
                    window.__oldHashRender = App.renderChapter('genesis', 2);
                }"""
            )
            page.wait_for_function("window.__oldHashRenderHeld")
            page.evaluate("location.hash = '#johannes/1'")
            page.wait_for_function(
                "window.__newHashNavigationHeld && Navigation.currentBook === 'johannes'"
            )
            during = page.evaluate(
                """async () => {
                    window.__releaseOldHashRender();
                    const oldResult = await window.__oldHashRender;
                    const flow = document.querySelector('.opv-reading-flow');
                    return {
                        oldResult,
                        flow: flow && `${flow.dataset.book}/${flow.dataset.chapter}`,
                        hash: location.hash,
                        navigationBook: Navigation.currentBook,
                    };
                }"""
            )
            self.assertEqual(during, {
                "oldResult": False,
                "flow": "genesis/1",
                "hash": "#johannes/1",
                "navigationBook": "johannes",
            })
            page.evaluate("window.__releaseNewHashNavigation()")
            page.locator('.opv-reading-flow[data-book="johannes"][data-chapter="1"]').wait_for()
        finally:
            page.close()

    def test_oude_opv_begriptrigger_kan_tijdens_editiewissel_geen_dialog_openen(self):
        page = self.new_page({"teksteditie": "nl-opv", "parallelEdities": []})
        try:
            page.goto(
                f"{self.base_url}/index.html?editie=nl-opv#johannes/3",
                wait_until="domcontentloaded",
            )
            trigger = page.locator('[data-opv-concept="farizeeen"]').first
            trigger.wait_for()
            page.evaluate(
                """() => {
                    const loadChapter = DataLoader.loadChapter.bind(DataLoader);
                    let release;
                    const gate = new Promise(resolve => { release = resolve; });
                    window.__releaseEditionRender = release;
                    window.__editionRenderHeld = false;
                    DataLoader.loadChapter = async (book, chapter) => {
                        if (TekstEditie.code() === 'nl-ov' && book === 'johannes' &&
                            Number(chapter) === 3) {
                            window.__editionRenderHeld = true;
                            await gate;
                        }
                        return loadChapter(book, chapter);
                    };
                    window.__oldOpvTrigger = document.querySelector(
                        '[data-opv-concept="farizeeen"]'
                    );
                    Opties.state.teksteditie = 'nl-ov';
                    Opties.state.parallelEdities = [];
                    Opties.save();
                    TekstEditie.setCode('nl-ov');
                    window.__pendingEditionRender = App.renderChapter('johannes', 3);
                }"""
            )
            page.wait_for_function("window.__editionRenderHeld")
            trigger.click()
            page.wait_for_timeout(150)
            state = page.evaluate(
                """async () => {
                    window.__releaseEditionRender();
                    await window.__pendingEditionRender;
                    const dialog = document.getElementById('opv-concept-dialog');
                    const oldTrigger = window.__oldOpvTrigger;
                    return {
                        edition: App._currentPrimaryEditionCode,
                        flowCount: document.querySelectorAll('.opv-reading-flow').length,
                        dialogOpen: Boolean(dialog && dialog.open),
                        oldTriggerConnected: oldTrigger.isConnected,
                        oldTriggerExpanded: oldTrigger.getAttribute('aria-expanded'),
                        triggerCleared: App._opvConceptTrigger === null,
                        restoreCleared: App._opvRestoreConceptFocus === false,
                        activeInDialog: Boolean(dialog && dialog.contains(document.activeElement)),
                    };
                }"""
            )
            self.assertEqual(state, {
                "edition": "nl-ov",
                "flowCount": 0,
                "dialogOpen": False,
                "oldTriggerConnected": False,
                "oldTriggerExpanded": "false",
                "triggerCleared": True,
                "restoreCleared": True,
                "activeInDialog": False,
            })
        finally:
            page.close()

    def test_verouderde_append_en_prepend_verliezen_dom_en_continuous_state(self):
        page = self.new_page({"teksteditie": "nl-opv", "parallelEdities": []})
        page.add_init_script(
            "localStorage.setItem('doorlopend', 'true');"
            "window.IntersectionObserver = class { observe() {} disconnect() {} };"
        )
        try:
            page.goto(f"{self.base_url}/index.html?editie=nl-opv#genesis/2",
                      wait_until="domcontentloaded")
            page.locator('.opv-reading-flow[data-chapter="2"]').wait_for()

            page.evaluate(
                """() => {
                    const original = DataLoader.loadChapter.bind(DataLoader);
                    const holds = new Map();
                    window.__holdChapter = (book, chapter) => {
                        let release;
                        const gate = new Promise(resolve => { release = resolve; });
                        holds.set(`${book}:${chapter}`, {gate, release, seen:false});
                    };
                    window.__chapterHeld = (book, chapter) =>
                        Boolean(holds.get(`${book}:${chapter}`)?.seen);
                    window.__releaseChapter = (book, chapter) =>
                        holds.get(`${book}:${chapter}`)?.release();
                    DataLoader.loadChapter = async (book, chapter) => {
                        const hold = holds.get(`${book}:${chapter}`);
                        if (hold) {
                            hold.seen = true;
                            await hold.gate;
                        }
                        return original(book, chapter);
                    };
                    DataLoader.prefetchAdjacent = () => {};
                    window.__holdChapter('genesis', 3);
                    App._contLast = {bookId:'genesis', chapterNum:2};
                    window.__staleAppend = App._loadNextContinuous();
                }"""
            )
            page.wait_for_function("window.__chapterHeld('genesis', 3)")
            page.evaluate(
                """async () => {
                    Navigation.currentBook = 'johannes';
                    Navigation.currentChapter = 1;
                    await App.renderChapter('johannes', 1);
                    window.__releaseChapter('genesis', 3);
                    await window.__staleAppend;
                }"""
            )
            self.assertEqual(
                page.locator(".opv-reading-flow").evaluate_all(
                    "els => els.map(el => `${el.dataset.book}/${el.dataset.chapter}`)"
                ),
                ["johannes/1"],
            )
            self.assertEqual(
                page.evaluate("App._contLast"), {"bookId": "johannes", "chapterNum": 1}
            )
            self.assertEqual(
                page.evaluate("App._contFirst"), {"bookId": "johannes", "chapterNum": 1}
            )
            self.assertFalse(page.evaluate("App._contLoading"))

            page.evaluate(
                """async () => {
                    Navigation.currentBook = 'genesis';
                    Navigation.currentChapter = 2;
                    await App.renderChapter('genesis', 2);
                    window.__holdChapter('genesis', 1);
                    App._contFirst = {bookId:'genesis', chapterNum:2};
                    window.__stalePrepend = App._loadPrevContinuous();
                }"""
            )
            page.wait_for_function("window.__chapterHeld('genesis', 1)")
            page.evaluate(
                """async () => {
                    Opties.state.teksteditie = 'nl-ov';
                    Opties.state.parallelEdities = [];
                    Opties.save();
                    TekstEditie.setCode('nl-ov');
                    Navigation.currentBook = 'genesis';
                    Navigation.currentChapter = 2;
                    await App.renderChapter('genesis', 2);
                    window.__releaseChapter('genesis', 1);
                    await window.__stalePrepend;
                }"""
            )
            self.assertEqual(page.locator(".opv-reading-flow").count(), 0)
            self.assertEqual(page.locator("#verses-container > .verse-row").count(), 25)
            self.assertEqual(page.evaluate("App._currentPrimaryEditionCode"), "nl-ov")
            self.assertEqual(
                page.evaluate("App._contLast"), {"bookId": "genesis", "chapterNum": 2}
            )
            self.assertEqual(
                page.evaluate("App._contFirst"), {"bookId": "genesis", "chapterNum": 2}
            )
            self.assertFalse(page.evaluate("App._contLoading"))
        finally:
            page.close()

    def test_doorlopend_lezen_append_prepend_en_publicatiegrenzen(self):
        page = self.new_page()
        page.add_init_script(
            """localStorage.setItem('doorlopend', 'true');
               window.IntersectionObserver = class { observe() {} disconnect() {} };"""
        )
        observed = self.observe_runtime(page)
        try:
            page.goto(f"{self.base_url}/index.html?editie=nl-opv#genesis/2",
                      wait_until="domcontentloaded")
            page.locator('.opv-reading-flow[data-chapter="2"]').wait_for()
            page.evaluate("App._contFirst={bookId:'genesis',chapterNum:2}; App._loadPrevContinuous()")
            page.wait_for_function("document.querySelectorAll('.opv-reading-flow').length === 2")
            self.assertEqual(
                page.locator(".opv-reading-flow").evaluate_all("els => els.map(el => el.dataset.chapter)"),
                ["1", "2"],
            )
            page.evaluate("App._contLast={bookId:'genesis',chapterNum:2}; App._loadNextContinuous()")
            page.wait_for_function("document.querySelectorAll('.opv-reading-flow').length === 3")
            self.assertEqual(
                page.locator(".opv-reading-flow").evaluate_all("els => els.map(el => el.dataset.chapter)"),
                ["1", "2", "3"],
            )
            chapter_labels = page.locator(".opv-reading-flow").evaluate_all(
                """flows => flows.map(flow => {
                    const id = flow.getAttribute('aria-labelledby');
                    const heading = id && document.getElementById(id);
                    return {
                        id,
                        headingTag: heading && heading.tagName,
                        headingText: heading && heading.textContent.trim(),
                        passageTags: [...flow.querySelectorAll('.opv-passage-title')]
                            .map(title => title.tagName),
                    };
                })"""
            )
            self.assertEqual(
                [item["headingText"] for item in chapter_labels],
                ["Genesis 1", "Genesis 2", "Genesis 3"],
            )
            self.assertEqual(
                [item["headingTag"] for item in chapter_labels], ["H2", "H2", "H2"]
            )
            self.assertEqual(len({item["id"] for item in chapter_labels}), 3)
            self.assertTrue(all(
                item["passageTags"] and set(item["passageTags"]) == {"H3"}
                for item in chapter_labels
            ))

            for book in ("genesis", "johannes"):
                page.evaluate("([book]) => App.renderChapter(book, 5)", [book])
                page.locator('.opv-reading-flow[data-chapter="5"]').wait_for()
                observed["requests"].clear()
                page.evaluate("([book]) => { App._contLast={bookId:book,chapterNum:5}; return App._loadNextContinuous(); }", [book])
                page.wait_for_timeout(150)
                self.assertEqual(page.locator('.opv-reading-flow[data-chapter="5"]').count(), 1)
                self.assertEqual(page.locator(".translation-unavailable").count(), 0)
                self.assertFalse(any(url.endswith(f"/{book}/6.json") for url in observed["requests"]))
            self.assertFalse(any("/lukas/" in url for url in observed["requests"]))
            self.assertEqual(observed["pageerrors"], [])
        finally:
            page.close()

    def test_mobiele_opv_versankers_blijven_op_360_en_390_bedienbaar(self):
        for width in (360, 390):
            with self.subTest(width=width):
                page = self.new_page(
                    {"teksteditie": "nl-opv"},
                    viewport={"width": width, "height": 800},
                )
                try:
                    page.goto(
                        f"{self.base_url}/index.html?editie=nl-opv#genesis/1",
                        wait_until="domcontentloaded",
                    )
                    page.locator('.opv-verse[data-verse="31"]').wait_for()
                    self.assertTrue(
                        page.locator("#content").evaluate(
                            "el => el.classList.contains('layout-eronder')"
                        )
                    )
                    anchors = page.locator(".opv-reading-flow .opv-verse-anchor").evaluate_all(
                        """items => items.map(anchor => {
                            const rect = anchor.getBoundingClientRect();
                            return {
                                verse: anchor.closest('.opv-verse').dataset.verse,
                                display: getComputedStyle(anchor).display,
                                width: rect.width,
                                height: rect.height,
                                tabIndex: anchor.tabIndex,
                                ariaHidden: anchor.getAttribute('aria-hidden'),
                            };
                        })"""
                    )
                    self.assertEqual(len(anchors), 31)
                    self.assertEqual(
                        [item for item in anchors if item["display"] == "none"], []
                    )
                    self.assertEqual(
                        [item for item in anchors if item["width"] < 24 or item["height"] < 24],
                        [],
                    )
                    self.assertTrue(all(item["tabIndex"] == 0 for item in anchors))
                    self.assertTrue(all(item["ariaHidden"] == "false" for item in anchors))
                    first = page.locator('.opv-verse[data-verse="1"] .opv-verse-anchor')
                    first.focus()
                    self.assertTrue(first.evaluate("el => document.activeElement === el"))
                finally:
                    page.close()

    def test_opv_versankers_blijven_op_desktop_in_beide_layouts_bedienbaar(self):
        for layout in ("naast", "eronder"):
            with self.subTest(layout=layout):
                page = self.new_page(
                    {"teksteditie": "nl-opv", "kolomLayout": layout},
                    viewport={"width": 1440, "height": 900},
                )
                try:
                    page.goto(
                        f"{self.base_url}/index.html?editie=nl-opv#genesis/1",
                        wait_until="domcontentloaded",
                    )
                    page.locator('.opv-verse[data-verse="31"]').wait_for()
                    self.assertEqual(
                        page.locator("#content").evaluate(
                            "(el, expected) => el.classList.contains(`layout-${expected}`)",
                            layout,
                        ),
                        True,
                    )
                    anchors = page.locator(
                        ".opv-reading-flow .opv-verse-anchor"
                    ).evaluate_all(
                        """items => items.map(anchor => {
                            const rect = anchor.getBoundingClientRect();
                            return {
                                verse: anchor.closest('.opv-verse').dataset.verse,
                                display: getComputedStyle(anchor).display,
                                width: rect.width,
                                height: rect.height,
                                tabIndex: anchor.tabIndex,
                                ariaHidden: anchor.getAttribute('aria-hidden'),
                            };
                        })"""
                    )
                    self.assertEqual(len(anchors), 31)
                    self.assertEqual(
                        [item for item in anchors if item["display"] == "none"], []
                    )
                    self.assertEqual(
                        [
                            item
                            for item in anchors
                            if item["width"] < 24 or item["height"] < 24
                        ],
                        [],
                    )
                    self.assertTrue(all(item["tabIndex"] == 0 for item in anchors))
                    self.assertTrue(all(item["ariaHidden"] == "false" for item in anchors))
                    first = page.locator(
                        '.opv-verse[data-verse="1"] .opv-verse-anchor'
                    )
                    first.focus()
                    self.assertTrue(first.evaluate("el => document.activeElement === el"))
                finally:
                    page.close()

        legacy = self.new_page(
            {"teksteditie": "nl-ov", "kolomLayout": "eronder"},
            viewport={"width": 1440, "height": 900},
        )
        try:
            legacy.goto(
                f"{self.base_url}/index.html#genesis/1", wait_until="domcontentloaded"
            )
            first_number = legacy.locator(
                '#verses-container > .verse-row[data-verse="1"] > .verse-num'
            )
            first_number.wait_for(state="attached")
            self.assertEqual(first_number.evaluate("el => getComputedStyle(el).display"), "none")
            self.assertEqual(legacy.locator(".opv-reading-flow").count(), 0)
        finally:
            legacy.close()

    def test_eerste_opv_versanker_blijft_klikbaar_onder_de_decoratieve_dropcap(self):
        for theme in ("licht", "donker"):
            for layout in ("naast", "eronder"):
                with self.subTest(theme=theme, layout=layout):
                    page = self.new_page(
                        {
                            "teksteditie": "nl-opv",
                            "kolomLayout": layout,
                            "thema": theme,
                        },
                        viewport={"width": 1440, "height": 900},
                    )
                    try:
                        page.goto(
                            f"{self.base_url}/index.html?editie=nl-opv#genesis/1",
                            wait_until="domcontentloaded",
                        )
                        row = page.locator('.opv-verse[data-verse="1"]')
                        row.wait_for()
                        anchor = row.locator(".opv-verse-anchor")
                        dropcap = row.locator(".dropcap-image:visible")
                        self.assertEqual(dropcap.count(), 1)
                        dropcap_box = dropcap.bounding_box()
                        self.assertIsNotNone(dropcap_box)
                        self.assertGreater(dropcap_box["width"], 0)
                        self.assertGreater(dropcap_box["height"], 0)

                        hit_samples = anchor.evaluate(
                            """anchor => {
                                const rect = anchor.getBoundingClientRect();
                                const samples = [];
                                for (let row = 0; row < 5; row += 1) {
                                    for (let column = 0; column < 5; column += 1) {
                                        const x = rect.left + rect.width * (column + 0.5) / 5;
                                        const y = rect.top + rect.height * (row + 0.5) / 5;
                                        const hit = document.elementFromPoint(x, y);
                                        samples.push({
                                            ownsHit: Boolean(hit &&
                                                (hit === anchor || anchor.contains(hit))),
                                            target: hit && (hit.id ||
                                                (typeof hit.className === 'string'
                                                    ? hit.className
                                                    : hit.className?.baseVal) || hit.tagName),
                                        });
                                    }
                                }
                                return samples;
                            }"""
                        )
                        self.assertEqual(len(hit_samples), 25)
                        self.assertEqual(
                            [sample for sample in hit_samples if not sample["ownsHit"]], []
                        )

                        anchor_box = anchor.bounding_box()
                        self.assertIsNotNone(anchor_box)
                        page.mouse.click(
                            anchor_box["x"] + anchor_box["width"] / 2,
                            anchor_box["y"] + anchor_box["height"] / 2,
                        )
                        self.assertEqual(page.evaluate("location.hash"), "#genesis/1/1")
                    finally:
                        page.close()

        legacy = self.new_page(
            {"teksteditie": "nl-ov", "kolomLayout": "eronder", "thema": "donker"},
            viewport={"width": 1440, "height": 900},
        )
        try:
            legacy.goto(
                f"{self.base_url}/index.html#genesis/1", wait_until="domcontentloaded"
            )
            first_number = legacy.locator(
                '#verses-container > .verse-row[data-verse="1"] > .verse-num'
            )
            first_number.wait_for(state="attached")
            legacy_dropcap = legacy.locator(
                '#verses-container > .verse-row[data-verse="1"] .dropcap-image:visible'
            )
            self.assertEqual(first_number.evaluate("el => getComputedStyle(el).display"), "none")
            self.assertEqual(legacy_dropcap.count(), 1)
            self.assertIsNotNone(legacy_dropcap.bounding_box())
            self.assertEqual(legacy.locator(".opv-reading-flow").count(), 0)
        finally:
            legacy.close()

    def test_hoofdstuknavigatie_negeert_vertraagde_oude_boekrequest(self):
        page = self.new_page({"teksteditie": "nl-opv"})
        try:
            page.goto(
                f"{self.base_url}/index.html?editie=nl-opv#genesis/1",
                wait_until="domcontentloaded",
            )
            page.locator('.opv-reading-flow[data-book="genesis"][data-chapter="1"]').wait_for()
            page.evaluate(
                """() => {
                    const loadBook = DataLoader.loadBook.bind(DataLoader);
                    let release;
                    const gate = new Promise(resolve => { release = resolve; });
                    window.__releaseOldChapterNav = release;
                    window.__oldChapterNavHeld = false;
                    DataLoader.loadBook = async bookId => {
                        if (bookId === 'johannes') {
                            window.__oldChapterNavHeld = true;
                            await gate;
                        }
                        return loadBook(bookId);
                    };

                    const renderChapterNav = Navigation.renderChapterNav.bind(Navigation);
                    Navigation.renderChapterNav = async (...args) => {
                        const result = await renderChapterNav(...args);
                        if (args[0] === 'johannes') window.__oldChapterNavSettled = true;
                        return result;
                    };
                }"""
            )
            page.evaluate("location.hash = '#johannes/1'")
            page.wait_for_function(
                "window.__oldChapterNavHeld && Navigation.currentBook === 'johannes'"
            )

            page.evaluate("location.hash = '#genesis/2'")
            page.wait_for_function(
                """() => document.querySelector(
                    '.opv-reading-flow[data-book="genesis"][data-chapter="2"]'
                ) && document.querySelectorAll('#chapter-nav button').length === 50"""
            )
            page.evaluate(
                """() => {
                    window.__oldChapterNavMutationCount = 0;
                    window.__oldChapterNavObserver = new MutationObserver(records => {
                        window.__oldChapterNavMutationCount += records.length;
                    });
                    window.__oldChapterNavObserver.observe(
                        document.getElementById('chapter-nav'),
                        {childList: true, attributes: true, subtree: true}
                    );
                    window.__releaseOldChapterNav();
                }"""
            )
            page.wait_for_function("window.__oldChapterNavSettled")
            page.evaluate("() => new Promise(resolve => requestAnimationFrame(resolve))")
            state = page.evaluate(
                """() => {
                    window.__oldChapterNavObserver.disconnect();
                    const buttons = [...document.querySelectorAll('#chapter-nav button')];
                    return {
                        hash: location.hash,
                        book: Navigation.currentBook,
                        chapter: Navigation.currentChapter,
                        flow: document.querySelector('.opv-reading-flow')?.dataset.book + '/' +
                            document.querySelector('.opv-reading-flow')?.dataset.chapter,
                        chapters: buttons.map(button => Number(button.dataset.chapter)),
                        active: buttons.filter(button => button.classList.contains('active'))
                            .map(button => Number(button.dataset.chapter)),
                        staleMutations: window.__oldChapterNavMutationCount,
                    };
                }"""
            )
            self.assertEqual(state["hash"], "#genesis/2")
            self.assertEqual(state["book"], "genesis")
            self.assertEqual(state["chapter"], 2)
            self.assertEqual(state["flow"], "genesis/2")
            self.assertEqual(state["chapters"], list(range(1, 51)))
            self.assertEqual(state["active"], [2])
            self.assertEqual(state["staleMutations"], 0)
        finally:
            page.close()

    def test_mobiele_header_blijft_bij_zoom_hittestbaar_zonder_overlap(self):
        for width in (360, 390):
            for theme in ("licht", "donker"):
                with self.subTest(width=width, theme=theme):
                    page = self.new_page(
                        {"teksteditie": "nl-opv", "thema": theme},
                        viewport={"width": width, "height": 844},
                    )
                    try:
                        page.goto(
                            f"{self.base_url}/index.html?editie=nl-opv#genesis/1",
                            wait_until="domcontentloaded",
                        )
                        page.locator('.opv-reading-flow[data-chapter="1"]').wait_for()
                        for zoom in (1, 2):
                            page.evaluate(
                                "value => { document.documentElement.style.zoom = String(value); }",
                                zoom,
                            )
                            page.evaluate(
                                "() => new Promise(resolve => requestAnimationFrame(resolve))"
                            )
                            geometry = page.evaluate(
                                """() => {
                                    const nav = document.getElementById('topnav');
                                    const brand = document.querySelector('.topnav-brand-link');
                                    const logo = document.querySelector('.topnav-logo');
                                    const settings = document.getElementById('topnav-tekstopties');
                                    const menu = document.getElementById('topnav-hamburger');
                                    const controls = [brand, settings, menu];
                                    const rects = controls.map(control =>
                                        control.getBoundingClientRect());
                                    const logoRect = logo.getBoundingClientRect();
                                    const area = (left, right) => Math.max(0,
                                        Math.min(left.right, right.right) -
                                            Math.max(left.left, right.left)) *
                                        Math.max(0, Math.min(left.bottom, right.bottom) -
                                            Math.max(left.top, right.top));
                                    return {
                                        overlaps: [
                                            area(logoRect, rects[1]),
                                            area(logoRect, rects[2]),
                                            area(rects[1], rects[2]),
                                        ],
                                        controls: controls.map((control, index) => {
                                            const rect = rects[index];
                                            const x = rect.left + rect.width / 2;
                                            const y = rect.top + rect.height / 2;
                                            const hit = document.elementFromPoint(x, y);
                                            return {
                                                width: rect.width,
                                                height: rect.height,
                                                left: rect.left,
                                                right: rect.right,
                                                top: rect.top,
                                                bottom: rect.bottom,
                                                hit: Boolean(hit &&
                                                    (hit === control || control.contains(hit))),
                                                hitId: hit?.id || '',
                                                hitClass: hit?.className?.baseVal ||
                                                    hit?.className || '',
                                            };
                                        }),
                                        viewport: {
                                            width: window.innerWidth,
                                            height: window.innerHeight,
                                        },
                                        horizontalOverflow: Math.max(
                                            document.documentElement.scrollWidth - window.innerWidth,
                                            document.body.scrollWidth - window.innerWidth,
                                            nav.scrollWidth - nav.clientWidth
                                        ),
                                        logoCssHeight: parseFloat(getComputedStyle(logo).height),
                                    };
                                }"""
                            )
                            self.assertEqual(geometry["overlaps"], [0, 0, 0], geometry)
                            self.assertLessEqual(geometry["horizontalOverflow"], 1, geometry)
                            for control in geometry["controls"]:
                                self.assertGreater(control["width"], 0, geometry)
                                self.assertGreater(control["height"], 0, geometry)
                                self.assertGreaterEqual(control["left"], 0, geometry)
                                self.assertLessEqual(
                                    control["right"], geometry["viewport"]["width"] + 1, geometry
                                )
                                self.assertGreaterEqual(control["top"], 0, geometry)
                                self.assertLessEqual(
                                    control["bottom"], geometry["viewport"]["height"] + 1, geometry
                                )
                                self.assertTrue(control["hit"], geometry)
                            if zoom == 1:
                                self.assertAlmostEqual(
                                    geometry["logoCssHeight"], 44, delta=0.5
                                )
                    finally:
                        page.close()

    def test_parallelle_opv_houdt_mobiele_hoofdstukpijlen_in_beide_richtingen_vrij(self):
        directions = (
            ("nl-opv", "nl-ov", "?editie=nl-opv"),
            ("nl-ov", "nl-opv", ""),
        )
        for primary, parallel, query in directions:
            for width in (360, 390):
                for theme in ("licht", "donker"):
                    with self.subTest(
                        primary=primary, parallel=parallel, width=width, theme=theme
                    ):
                        page = self.new_page(
                            {
                                "teksteditie": primary,
                                "parallelEdities": [parallel],
                                "kolomLayout": "eronder",
                                "thema": theme,
                            },
                            viewport={"width": width, "height": 844},
                        )
                        try:
                            page.goto(
                                f"{self.base_url}/index.html{query}#johannes/4",
                                wait_until="domcontentloaded",
                            )
                            page.locator(
                                '.verse-row[data-verse="54"] '
                                '.parallel-edition[data-editie="nl-opv"]'
                            ).wait_for()
                            for zoom in (1, 2):
                                page.evaluate(
                                    "value => { document.documentElement.style.zoom = String(value); }",
                                    zoom,
                                )
                                geometry = page.evaluate(
                                    """async () => {
                                        const content = document.getElementById('content');
                                        const footer = document.getElementById('mobile-footer-nav');
                                        const buttons = [
                                            document.getElementById('mobile-prev-btn'),
                                            document.getElementById('mobile-next-btn'),
                                        ];
                                        const opvRoots = [...document.querySelectorAll(
                                            '#verses-container .parallel-edition[data-editie="nl-opv"]'
                                        )];
                                        const area = (left, right) => Math.max(0,
                                            Math.min(left.right, right.right) -
                                                Math.max(left.left, right.left)) *
                                            Math.max(0, Math.min(left.bottom, right.bottom) -
                                                Math.max(left.top, right.top));
                                        const overlap = () => {
                                            const contentRect = content.getBoundingClientRect();
                                            const viewport = {
                                                left: Math.max(0, contentRect.left),
                                                right: Math.min(window.innerWidth, contentRect.right),
                                                top: Math.max(0, contentRect.top),
                                                bottom: Math.min(window.innerHeight, contentRect.bottom),
                                            };
                                            const buttonRects = buttons.map(button =>
                                                button.getBoundingClientRect());
                                            let maximum = 0;
                                            for (const root of opvRoots) {
                                                const walker = document.createTreeWalker(
                                                    root, NodeFilter.SHOW_TEXT
                                                );
                                                while (walker.nextNode()) {
                                                    if (!walker.currentNode.textContent.trim()) continue;
                                                    const range = document.createRange();
                                                    range.selectNodeContents(walker.currentNode);
                                                    for (const rect of range.getClientRects()) {
                                                        const clipped = {
                                                            left: Math.max(rect.left, viewport.left),
                                                            right: Math.min(rect.right, viewport.right),
                                                            top: Math.max(rect.top, viewport.top),
                                                            bottom: Math.min(rect.bottom, viewport.bottom),
                                                        };
                                                        if (clipped.right <= clipped.left ||
                                                            clipped.bottom <= clipped.top) continue;
                                                        for (const buttonRect of buttonRects) {
                                                            maximum = Math.max(
                                                                maximum, area(clipped, buttonRect)
                                                            );
                                                        }
                                                    }
                                                }
                                            }
                                            return maximum;
                                        };
                                        const scroller = App._getScroller();
                                        const maximumScroll = scroller === content
                                            ? content.scrollHeight - content.clientHeight
                                            : document.documentElement.scrollHeight - window.innerHeight;
                                        const overlaps = [];
                                        for (const position of [0, maximumScroll / 2, maximumScroll]) {
                                            if (scroller === content) content.scrollTop = position;
                                            else window.scrollTo(0, position);
                                            await new Promise(resolve => requestAnimationFrame(resolve));
                                            overlaps.push(overlap());
                                        }
                                        const footerStyle = getComputedStyle(footer);
                                        const buttonRects = buttons.map(button =>
                                            button.getBoundingClientRect());
                                        return {
                                            contentPosition: getComputedStyle(content).position,
                                            ownsScroller: App._getScroller() === content,
                                            maxOverlap: Math.max(...overlaps),
                                            footerBackground: footerStyle.backgroundColor,
                                            footerBorder: parseFloat(footerStyle.borderTopWidth),
                                            horizontalOverflow: Math.max(
                                                document.documentElement.scrollWidth - window.innerWidth,
                                                document.body.scrollWidth - window.innerWidth,
                                                content.scrollWidth - content.clientWidth
                                            ),
                                            buttons: buttons.map((button, index) => {
                                                const rect = buttonRects[index];
                                                const hit = document.elementFromPoint(
                                                    rect.left + rect.width / 2,
                                                    rect.top + rect.height / 2
                                                );
                                                return {
                                                    left: rect.left,
                                                    right: rect.right,
                                                    top: rect.top,
                                                    bottom: rect.bottom,
                                                    hit: Boolean(hit &&
                                                        (hit === button || button.contains(hit))),
                                                };
                                            }),
                                            viewport: {
                                                width: window.innerWidth,
                                                height: window.innerHeight,
                                            },
                                        };
                                    }"""
                                )
                                self.assertEqual(
                                    geometry["contentPosition"], "fixed", geometry
                                )
                                self.assertTrue(geometry["ownsScroller"], geometry)
                                self.assertEqual(geometry["maxOverlap"], 0, geometry)
                                self.assertLessEqual(
                                    geometry["horizontalOverflow"], 1, geometry
                                )
                                self.assertGreaterEqual(geometry["footerBorder"], 1, geometry)
                                self.assertNotIn(
                                    geometry["footerBackground"],
                                    ("transparent", "rgba(0, 0, 0, 0)"),
                                )
                                for button in geometry["buttons"]:
                                    self.assertGreaterEqual(button["left"], 0, geometry)
                                    self.assertLessEqual(
                                        button["right"],
                                        geometry["viewport"]["width"] + 1,
                                        geometry,
                                    )
                                    self.assertGreaterEqual(button["top"], 0, geometry)
                                    self.assertLessEqual(
                                        button["bottom"],
                                        geometry["viewport"]["height"] + 1,
                                        geometry,
                                    )
                                    self.assertTrue(button["hit"], geometry)
                        finally:
                            page.close()

    def test_donkere_opv_focusindicatoren_hebben_minimaal_drie_op_een_contrast(self):
        page = self.new_page(
            {"teksteditie": "nl-opv", "thema": "donker"},
            viewport={"width": 390, "height": 800},
        )
        try:
            page.goto(
                f"{self.base_url}/index.html?editie=nl-opv#johannes/3",
                wait_until="domcontentloaded",
            )
            page.locator('[data-opv-concept="farizeeen"]').first.wait_for()

            def focus_contrast(selector, background_selector):
                page.keyboard.press("Tab")
                locator = page.locator(selector).first
                locator.focus()
                return locator.evaluate(
                    """(el, backgroundSelector) => {
                        const channels = value => (value.match(/[0-9.]+/g) || [])
                            .slice(0, 3).map(Number);
                        const luminance = value => {
                            const rgb = channels(value).map(channel => channel / 255).map(channel =>
                                channel <= 0.04045 ? channel / 12.92 :
                                    Math.pow((channel + 0.055) / 1.055, 2.4));
                            return 0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2];
                        };
                        const style = getComputedStyle(el);
                        const background = getComputedStyle(
                            el.closest(backgroundSelector) || document.body
                        ).backgroundColor;
                        const foregroundLuminance = luminance(style.outlineColor);
                        const backgroundLuminance = luminance(background);
                        return {
                            contrast: (Math.max(foregroundLuminance, backgroundLuminance) + 0.05) /
                                (Math.min(foregroundLuminance, backgroundLuminance) + 0.05),
                            focusVisible: el.matches(':focus-visible'),
                            outlineColor: style.outlineColor,
                            outlineStyle: style.outlineStyle,
                        };
                    }""",
                    background_selector,
                )

            for selector in (
                '.opv-verse[data-verse="2"] .opv-verse-anchor',
                "[data-opv-concept]",
            ):
                measured = focus_contrast(selector, "body")
                self.assertTrue(measured["focusVisible"], measured)
                self.assertNotEqual(measured["outlineStyle"], "none")
                self.assertGreaterEqual(measured["contrast"], 3, measured)

            trigger = page.locator('[data-opv-concept="farizeeen"]').first
            trigger.focus()
            page.keyboard.press("Enter")
            dialog = page.locator("#opv-concept-dialog")
            dialog.wait_for(state="visible")
            measured = focus_contrast(".opv-concept-close", ".opv-concept-dialog")
            self.assertTrue(measured["focusVisible"], measured)
            self.assertNotEqual(measured["outlineStyle"], "none")
            self.assertGreaterEqual(measured["contrast"], 3, measured)
        finally:
            page.close()

    def test_mobiele_opv_scrollruimte_houdt_hoofdstukpijlen_vrij_van_tekst(self):
        page = self.new_page(
            {"teksteditie": "nl-opv", "kolomLayout": "eronder"},
            viewport={"width": 390, "height": 844},
        )
        try:
            page.goto(
                f"{self.base_url}/index.html?editie=nl-opv#johannes/4",
                wait_until="domcontentloaded",
            )
            page.locator('.opv-verse[data-verse="54"]').wait_for()
            for zoom in (1, 2):
                page.evaluate("zoom => { document.documentElement.style.zoom = String(zoom); }", zoom)
                geometry = page.evaluate(
                    """async () => {
                        const content = document.getElementById('content');
                        const footer = document.getElementById('mobile-footer-nav');
                        const buttons = [
                            document.getElementById('mobile-prev-btn'),
                            document.getElementById('mobile-next-btn'),
                        ];
                        const area = (left, right) => Math.max(0,
                            Math.min(left.right, right.right) - Math.max(left.left, right.left)) *
                            Math.max(0,
                                Math.min(left.bottom, right.bottom) - Math.max(left.top, right.top));
                        const overlapAtCurrentPosition = () => {
                            const viewport = content.getBoundingClientRect();
                            const buttonRects = buttons.map(button => button.getBoundingClientRect());
                            let maximum = 0;
                            const walker = document.createTreeWalker(
                                content.querySelector('.opv-reading-flow'), NodeFilter.SHOW_TEXT
                            );
                            while (walker.nextNode()) {
                                if (!walker.currentNode.textContent.trim()) continue;
                                const range = document.createRange();
                                range.selectNodeContents(walker.currentNode);
                                for (const rect of range.getClientRects()) {
                                    const clipped = {
                                        left: Math.max(rect.left, viewport.left),
                                        right: Math.min(rect.right, viewport.right),
                                        top: Math.max(rect.top, viewport.top),
                                        bottom: Math.min(rect.bottom, viewport.bottom),
                                    };
                                    if (clipped.right <= clipped.left || clipped.bottom <= clipped.top) continue;
                                    for (const buttonRect of buttonRects) {
                                        maximum = Math.max(maximum, area(clipped, buttonRect));
                                    }
                                }
                            }
                            return maximum;
                        };
                        const positions = [0, content.scrollHeight / 2, content.scrollHeight];
                        const overlaps = [];
                        for (const position of positions) {
                            content.scrollTop = position;
                            await new Promise(resolve => requestAnimationFrame(resolve));
                            overlaps.push(overlapAtCurrentPosition());
                        }
                        const footerStyle = getComputedStyle(footer);
                        const buttonRects = buttons.map(button => button.getBoundingClientRect());
                        return {
                            contentPosition: getComputedStyle(content).position,
                            contentTop: parseFloat(getComputedStyle(content).top),
                            contentBottom: getComputedStyle(content).bottom,
                            contentOverflowY: getComputedStyle(content).overflowY,
                            footerBackground: footerStyle.backgroundColor,
                            footerBorder: parseFloat(footerStyle.borderTopWidth),
                            ownsScroller: App._getScroller() === content,
                            maxOverlap: Math.max(...overlaps),
                            horizontalOverflow: Math.max(
                                document.documentElement.scrollWidth - window.innerWidth,
                                document.body.scrollWidth - window.innerWidth,
                                content.scrollWidth - content.clientWidth
                            ),
                            buttons: buttons.map((button, index) => {
                                const rect = buttonRects[index];
                                const x = rect.left + rect.width / 2;
                                const y = rect.top + rect.height / 2;
                                const hit = document.elementFromPoint(x, y);
                                return {
                                    left: rect.left,
                                    right: rect.right,
                                    top: rect.top,
                                    bottom: rect.bottom,
                                    hit: Boolean(hit && (hit === button || button.contains(hit))),
                                };
                            }),
                            viewport: {width: window.innerWidth, height: window.innerHeight},
                        };
                    }"""
                )
                self.assertEqual(geometry["contentPosition"], "fixed", geometry)
                self.assertEqual(geometry["contentTop"], 109, geometry)
                self.assertIn("64px", geometry["contentBottom"])
                self.assertIn(geometry["contentOverflowY"], ("auto", "scroll"))
                self.assertTrue(geometry["ownsScroller"], geometry)
                self.assertEqual(geometry["maxOverlap"], 0, geometry)
                self.assertLessEqual(geometry["horizontalOverflow"], 1, geometry)
                self.assertGreaterEqual(geometry["footerBorder"], 1, geometry)
                self.assertNotIn(geometry["footerBackground"], ("transparent", "rgba(0, 0, 0, 0)"))
                for button in geometry["buttons"]:
                    self.assertGreaterEqual(button["left"], 0, geometry)
                    self.assertLessEqual(button["right"], geometry["viewport"]["width"] + 1, geometry)
                    self.assertGreaterEqual(button["top"], 0, geometry)
                    self.assertLessEqual(button["bottom"], geometry["viewport"]["height"] + 1, geometry)
                    self.assertTrue(button["hit"], geometry)
        finally:
            page.close()

        legacy = self.new_page(
            {"teksteditie": "nl-ov", "kolomLayout": "eronder"},
            viewport={"width": 390, "height": 844},
        )
        try:
            legacy.goto(f"{self.base_url}/index.html#johannes/4", wait_until="domcontentloaded")
            legacy.locator('.verse-row[data-verse="54"]').wait_for()
            sentinel = legacy.evaluate(
                """() => {
                    const content = document.getElementById('content');
                    const footer = document.getElementById('mobile-footer-nav');
                    const first = document.querySelector('.verse-row[data-verse="1"] .verse-num');
                    return {
                        contentPosition: getComputedStyle(content).position,
                        footerBackground: getComputedStyle(footer).backgroundColor,
                        footerBorder: getComputedStyle(footer).borderTopWidth,
                        ownsScroller: App._getScroller() === content,
                        firstNumberDisplay: getComputedStyle(first).display,
                    };
                }"""
            )
            self.assertEqual(sentinel, {
                "contentPosition": "static",
                "footerBackground": "rgba(0, 0, 0, 0)",
                "footerBorder": "0px",
                "ownsScroller": False,
                "firstNumberDisplay": "none",
            })
        finally:
            legacy.close()

    def test_boektypografie_opties_contrast_en_mobiele_viewport(self):
        page = self.new_page(viewport={"width": 1280, "height": 900})
        try:
            page.goto(f"{self.base_url}/index.html?editie=nl-opv#johannes/3",
                      wait_until="domcontentloaded")
            flow = page.locator(".opv-reading-flow")
            flow.wait_for()
            metrics = flow.evaluate(
                """el => {
                    const style = getComputedStyle(el);
                    const rect = el.getBoundingClientRect();
                    const anchor = el.querySelector('.opv-verse-anchor');
                    const ar = anchor.getBoundingClientRect();
                    const rgb = value => value.match(/[0-9.]+/g).slice(0, 3).map(Number);
                    const luminance = value => {
                        const parts = rgb(value).map(v => v / 255).map(v =>
                            v <= .04045 ? v / 12.92 : Math.pow((v + .055) / 1.055, 2.4));
                        return .2126 * parts[0] + .7152 * parts[1] + .0722 * parts[2];
                    };
                    const fg = luminance(getComputedStyle(anchor).color);
                    const bg = luminance(getComputedStyle(document.body).backgroundColor);
                    const probe = document.createElement('span');
                    probe.style.cssText = 'position:absolute;visibility:hidden;width:1ch;padding:0';
                    probe.textContent = '0'; el.appendChild(probe);
                    const ch = probe.getBoundingClientRect().width; probe.remove();
                    const contentWidth = rect.width - parseFloat(style.paddingLeft) - parseFloat(style.paddingRight);
                    const parentRect = el.parentElement.getBoundingClientRect();
                    return {maxWidth: style.maxWidth, contentCh: contentWidth / ch,
                        fontSize: parseFloat(style.fontSize),
                        lineHeight: parseFloat(style.lineHeight), width: rect.width,
                        centered: Math.abs((rect.left - parentRect.left) - (parentRect.right - rect.right)) < 3,
                        anchorWidth: ar.width, anchorHeight: ar.height,
                        contrast: (Math.max(fg, bg) + .05) / (Math.min(fg, bg) + .05),
                        border: style.borderTopWidth, shadow: style.boxShadow,
                        background: style.backgroundColor};
                }"""
            )
            self.assertGreaterEqual(metrics["contentCh"], 62)
            self.assertLessEqual(metrics["contentCh"], 72)
            self.assertGreaterEqual(metrics["fontSize"], 18)
            self.assertLessEqual(metrics["fontSize"], 20)
            self.assertGreaterEqual(metrics["lineHeight"] / metrics["fontSize"], 1.65)
            self.assertLessEqual(metrics["lineHeight"] / metrics["fontSize"], 1.9)
            self.assertTrue(metrics["centered"])
            self.assertGreaterEqual(metrics["anchorWidth"], 24)
            self.assertGreaterEqual(metrics["anchorHeight"], 24)
            self.assertGreaterEqual(metrics["contrast"], 4.5)
            self.assertEqual(metrics["border"], "0px")
            self.assertEqual(metrics["shadow"], "none")

            base = flow.evaluate("el => ({font:getComputedStyle(el).fontFamily,line:getComputedStyle(el).lineHeight})")
            page.locator("#topnav-tekstopties").click()
            page.locator('details[data-options-category="weergave"]').evaluate(
                "element => { element.open = true; }"
            )
            page.locator("#toggle-lettertype-alternatief").check()
            alternate = flow.evaluate("el => getComputedStyle(el).fontFamily")
            self.assertNotEqual(alternate, base["font"])
            page.locator("#opt-regelafstand").fill("2")
            roomy = flow.evaluate("el => parseFloat(getComputedStyle(el).lineHeight)")
            self.assertGreater(roomy, float(base["line"].replace("px", "")))
            page.locator("#toggle-dyslexia").check()
            self.assertTrue(page.locator("body").evaluate("el => el.classList.contains('dyslexia-mode')"))
            self.assertNotEqual(flow.evaluate("el => getComputedStyle(el).letterSpacing"), "normal")
            page.locator("#sidebar-right-toggle").click()
            page.locator("#sidebar-right").wait_for(state="hidden")

            anchor = page.locator(".opv-verse-anchor").first
            box_before = anchor.bounding_box()
            page.evaluate("Opties.state.versnummers='uit'; Opties.applyVerseNumbersClass()")
            self.assertEqual(anchor.count(), 1)
            self.assertEqual(anchor.get_attribute("tabindex"), "-1")
            box_after = anchor.bounding_box()
            self.assertAlmostEqual(box_before["width"], box_after["width"], delta=0.5)
            self.assertAlmostEqual(box_before["height"], box_after["height"], delta=0.5)

            page.set_viewport_size({"width": 360, "height": 800})
            page.evaluate("document.documentElement.dataset.theme='donker'")
            page.evaluate("Opties.state.versnummers='aan'; Opties.applyVerseNumbersClass()")
            dark_concept = page.locator(".opv-citation [data-opv-concept]").first.evaluate(
                """el => ({background:getComputedStyle(el).backgroundColor,
                    color:getComputedStyle(el).color,
                    citationColor:getComputedStyle(el.closest('.opv-citation')).color})"""
            )
            self.assertEqual(dark_concept["background"], "rgba(0, 0, 0, 0)")
            self.assertEqual(dark_concept["color"], dark_concept["citationColor"])
            mobile = flow.evaluate(
                """el => { const r=el.getBoundingClientRect(), s=getComputedStyle(el);
                    return {left:r.left,right:r.right,width:r.width,client:el.clientWidth,
                        scroll:el.scrollWidth,paddingBottom:parseFloat(s.paddingBottom),
                        viewport:document.documentElement.clientWidth,
                        bodyScroll:document.body.scrollWidth}; }"""
            )
            self.assertGreaterEqual(mobile["left"], 0)
            self.assertLessEqual(mobile["right"], mobile["viewport"] + 1)
            self.assertLessEqual(mobile["scroll"], mobile["client"] + 1)
            self.assertLessEqual(mobile["bodyScroll"], mobile["viewport"] + 1)
            self.assertGreaterEqual(mobile["paddingBottom"], 24)
            self.assertEqual(page.evaluate("window.innerWidth"), 360)

            page.locator("[data-opv-concept]").first.click()
            dialog = page.locator("#opv-concept-dialog")
            dialog.wait_for(state="visible")
            dialog_box = dialog.bounding_box()
            viewport = page.evaluate("({width:window.innerWidth,height:window.innerHeight})")
            self.assertGreaterEqual(dialog_box["x"], 0)
            self.assertLessEqual(dialog_box["x"] + dialog_box["width"], viewport["width"] + 1)
            self.assertGreaterEqual(dialog_box["y"], 0)
            self.assertLessEqual(dialog_box["y"] + dialog_box["height"], viewport["height"] + 1)
            self.assertIn("rgb", dialog.evaluate("el => getComputedStyle(el).backgroundColor"))
            dark_close = dialog.locator(".opv-concept-close").evaluate(
                "el => ({background:getComputedStyle(el).backgroundColor, "
                "color:getComputedStyle(el).color})"
            )
            self.assertEqual(dark_close["background"], "rgb(214, 183, 95)")
            self.assertEqual(dark_close["color"], "rgb(20, 32, 42)")
            dialog.locator(".opv-concept-close").click()

            page.evaluate("document.documentElement.style.zoom='2'")
            zoomed = flow.evaluate("el => ({client:el.clientWidth, scroll:el.scrollWidth})")
            self.assertLessEqual(zoomed["scroll"], zoomed["client"] + 1)
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

    def test_opv_progress_en_statusindicator_gebruiken_eigen_vocabulaire_met_legacybehoud(self):
        page = self.new_page()
        try:
            page.goto(
                f"{self.base_url}/index.html?editie=nl-opv#genesis/1",
                wait_until="domcontentloaded",
            )
            page.locator('.opv-reading-flow[data-chapter="1"]').wait_for()
            page.evaluate(
                """() => {
                    const rows = [...document.querySelectorAll('.opv-reading-flow .opv-verse')];
                    rows.forEach(row => { row.dataset.status = 'concept'; });
                    rows[1].dataset.status = 'bron_gecontroleerd';
                    rows[2].dataset.status = 'taal_gecontroleerd';
                    rows[3].dataset.status = 'definitief';
                    App.updateProgress();
                }"""
            )
            self.assertEqual(
                page.locator("#progress-text").inner_text(),
                "1/31 definitief (28 concept, 1 bron gecontroleerd, 1 taal gecontroleerd)",
            )
            self.assertEqual(page.locator("#progress-fill").evaluate("el => el.style.width"), "3%")
            opv_markers = page.locator(".opv-reading-flow .opv-verse-anchor").evaluate_all(
                """anchors => anchors.slice(0, 4).map(anchor => ({
                    background: getComputedStyle(anchor, '::after').backgroundColor,
                    width: parseFloat(getComputedStyle(anchor, '::after').width),
                    height: parseFloat(getComputedStyle(anchor, '::after').height),
                }))"""
            )
            self.assertEqual(
                [marker["background"] for marker in opv_markers],
                [
                    "rgb(203, 164, 73)",
                    "rgb(118, 151, 138)",
                    "rgb(118, 151, 138)",
                    "rgb(92, 184, 92)",
                ],
            )
            self.assertTrue(all(marker["width"] > 0 and marker["height"] > 0
                                for marker in opv_markers))

            page.evaluate(
                """async () => {
                    Opties.state.teksteditie = 'nl-ov';
                    Opties.state.parallelEdities = [];
                    Opties.save();
                    TekstEditie.setCode('nl-ov');
                    await App.renderChapter('genesis', 1);
                    const rows = [...document.querySelectorAll('#verses-container > .verse-row')];
                    rows.forEach(row => { row.dataset.status = 'empty'; });
                    rows[1].dataset.status = 'draft';
                    rows[2].dataset.status = 'review';
                    rows[3].dataset.status = 'final';
                    App.updateProgress();
                }"""
            )
            self.assertEqual(
                page.locator("#progress-text").inner_text(),
                "1/31 definitief (1 concept, 1 review)",
            )
            self.assertEqual(page.locator("#progress-fill").evaluate("el => el.style.width"), "3%")
        finally:
            page.close()


if __name__ == "__main__":
    unittest.main()
