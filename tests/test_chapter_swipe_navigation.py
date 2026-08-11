"""Regressietesten voor horizontale hoofdstuknavigatie in het leesgebied."""

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


class ChapterSwipeNavigationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        handler = lambda *args, **kwargs: _QuietHandler(
            *args, directory=str(ROOT), **kwargs
        )
        cls.server = _QuietServer(("127.0.0.1", 0), handler)
        cls.server_thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.server_thread.start()
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
        cls.server_thread.join(timeout=2)

    def open_reader(self, location="genesis/1"):
        page = self.browser.new_page(viewport={"width": 390, "height": 844}, has_touch=True)
        page.goto(f"{self.base_url}/index.html#{location}", wait_until="domcontentloaded")
        page.locator('.verse-row[data-verse="1"]').wait_for(timeout=15_000)
        return page

    @staticmethod
    def swipe(page, start_x, start_y, end_x, end_y, target_selector="#verses-container"):
        page.locator(target_selector).evaluate(
            """(el, coords) => {
                const makeTouch = (x, y) => new Touch({ identifier: 1, target: el, clientX: x, clientY: y });
                const send = (type, x, y, touches) => el.dispatchEvent(new TouchEvent(type, {
                    bubbles: true,
                    changedTouches: [makeTouch(x, y)],
                    touches: touches ? [makeTouch(x, y)] : [],
                }));
                send('touchstart', coords[0], coords[1], true);
                send('touchend', coords[2], coords[3], false);
            }""",
            [start_x, start_y, end_x, end_y],
        )

    def test_swipe_naar_links_op_tekst_navigeert_naar_volgend_hoofdstuk(self):
        page = self.open_reader()
        try:
            self.swipe(page, 320, 320, 120, 324)
            page.wait_for_url("**#genesis/2", timeout=5_000)
        finally:
            page.close()

    def test_overwegend_verticale_veeg_blijft_in_hetzelfde_hoofdstuk(self):
        page = self.open_reader()
        try:
            self.swipe(page, 220, 320, 185, 120)
            page.wait_for_timeout(250)
            self.assertTrue(page.url.endswith("#genesis/1"))
        finally:
            page.close()

    def test_veeg_die_op_een_knop_begint_navigeert_niet(self):
        page = self.open_reader()
        try:
            page.locator("#verses-container").evaluate(
                """container => {
                    const button = document.createElement('button');
                    button.id = 'swipe-interactive-target';
                    button.textContent = 'Interactief';
                    container.appendChild(button);
                }"""
            )
            self.swipe(page, 320, 320, 120, 324, "#swipe-interactive-target")
            page.wait_for_timeout(250)
            self.assertTrue(page.url.endswith("#genesis/1"))
        finally:
            page.close()

    def test_veeg_vooruit_op_het_laatste_hoofdstuk_volgt_de_boekgrens(self):
        page = self.open_reader("genesis/50")
        try:
            self.swipe(page, 320, 320, 120, 324)
            page.wait_for_url("**#exodus/1", timeout=5_000)
        finally:
            page.close()
