"""Browserregressie voor feedback op een selectie over meerdere hoofdstukken."""

import contextlib
import http.server
from pathlib import Path
import threading
import unittest
from urllib.parse import parse_qs

from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[1]


class _QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, _format, *_args):
        pass


class FeedbackMultipleSelectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        handler = lambda *args, **kwargs: _QuietHandler(
            *args, directory=str(ROOT), **kwargs
        )
        cls.server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
        cls.server_thread = threading.Thread(
            target=cls.server.serve_forever, daemon=True
        )
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

    def test_feedback_over_meerdere_hoofdstukken_verstuurt_volledige_selectie(self):
        page = self.browser.new_page(viewport={"width": 1280, "height": 900})
        requests = []

        def capture_form(route, request):
            requests.append(parse_qs(request.post_data or ""))
            route.fulfill(status=204, body="")

        page.route("https://docs.google.com/forms/**", capture_form)
        try:
            page.goto(
                f"{self.base_url}/index.html#genesis/1",
                wait_until="domcontentloaded",
            )
            page.locator('.verse-row[data-chapter="1"][data-verse="31"]').wait_for(
                timeout=15_000
            )
            page.evaluate("() => App.renderChapter('genesis', 2, {append: true})")
            page.locator('.verse-row[data-chapter="2"][data-verse="2"]').wait_for(
                timeout=15_000
            )

            expected_lines = page.evaluate(
                """() => {
                    VerseSelect.selected = new Set([
                        'genesis/1/31', 'genesis/2/1', 'genesis/2/2'
                    ]);
                    const data = VerseSelect._buildRefAndText();
                    VerseSelect.openNote();
                    return data.items.map(item => `${item.num} ${item.text}`);
                }"""
            )

            self.assertEqual(
                page.locator("#feedback-modal .fb-ref").text_content(),
                "Genesis 1:31; Genesis 2:1-2",
            )
            self.assertEqual(
                page.locator("#feedback-modal .fb-quote").inner_text().splitlines(),
                expected_lines,
            )

            page.locator("#fb-suggestion").fill("Controleer deze doorlopende zin.")
            page.get_by_role("button", name="Principe", exact=True).click()
            page.locator("#feedback-modal .fb-send").click()
            page.wait_for_function("() => document.querySelector('.fb-status').textContent.includes('verstuurd')")

            self.assertEqual(len(requests), 1)
            fields = FeedbackFields(requests[0])
            self.assertEqual(fields.reference, "Genesis 1:31; Genesis 2:1-2")
            self.assertEqual(fields.selection.splitlines(), expected_lines)
            self.assertEqual(fields.suggestion, "[Principe] Controleer deze doorlopende zin.")
        finally:
            page.close()


class FeedbackFields:
    """Lees de functionele velden uit het echte formulierverzoek."""

    def __init__(self, data):
        self.reference = data["entry.1027694877"][0]
        self.selection = data["entry.644152872"][0]
        self.suggestion = data["entry.758123662"][0]


if __name__ == "__main__":
    unittest.main()
