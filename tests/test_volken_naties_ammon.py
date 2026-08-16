import contextlib
import http.server
import json
import pathlib
import re
import threading
import unittest

from playwright.sync_api import sync_playwright


ROOT = pathlib.Path(__file__).resolve().parents[1]


def read_json(relative):
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def expand_ref(reference):
    match = re.fullmatch(r"(\S+) (\d+):(\d+)(?:-(\d+))?", reference)
    assert match, reference
    book, chapter, first, last = match.groups()
    return {
        f"{book} {chapter}:{verse}"
        for verse in range(int(first), int(last or first) + 1)
    }


class _QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, _format, *_args):
        pass


class VolkenNatiesDataTest(unittest.TestCase):
    def setUp(self):
        self.catalogue = read_json("data/naslag-volken-naties.json")
        self.ammon = next(item for item in self.catalogue["items"] if item["id"] == "ammon")

    def test_four_nations_have_a_separate_naslag_item_with_ancestor_and_map(self):
        expected = {
            "ammon": ("Ben-Ammi", "Rabba"),
            "edom": ("Ezau", "Edom"),
            "midian": ("Midian", "Midian"),
            "moab": ("Moab", "Moab"),
        }
        actual = {item["id"]: item for item in self.catalogue["items"]}
        self.assertEqual(set(actual), set(expected))
        for item_id, (ancestor, map_location) in expected.items():
            with self.subTest(item_id=item_id):
                self.assertEqual(actual[item_id]["stamvader"]["naam"], ancestor)
                self.assertEqual(actual[item_id]["kaart"]["plaats"], map_location)
                self.assertTrue(actual[item_id]["verzen"])

    def test_ammon_is_a_nation_with_ben_ammi_as_ancestor(self):
        self.assertEqual(self.catalogue["titel"], "Volken & Naties")
        self.assertEqual(self.catalogue["canon"], "66 boeken")
        self.assertEqual(self.ammon["soort"], "volk")
        self.assertEqual(self.ammon["stamvader"]["naam"], "Ben-Ammi")
        self.assertEqual(self.ammon["stamvader"]["ref"], "genesis 19:38")
        self.assertIn("kinderen Ammons", self.ammon["naamvormen"])
        self.assertIn("Ammonieten", self.ammon["naamvormen"])

    def test_published_passages_only_use_the_66_canonical_books(self):
        books = read_json("data/books.json")["books"]
        canonical = {book["id"] for book in books if book["testament"] in {"OT", "NT"}}
        self.assertEqual(len(canonical), 66)
        for reference in self.ammon["verzen"]:
            self.assertIn(reference.split()[0], canonical, reference)

    def test_every_literal_ammon_reference_in_the_canon_is_covered(self):
        covered = set().union(*(expand_ref(ref) for ref in self.ammon["verzen"]))
        books = read_json("data/books.json")["books"]
        missing = []
        for book in books:
            if book["testament"] not in {"OT", "NT"}:
                continue
            for chapter in book["chaptersIncluded"]:
                chapter_file = ROOT / "data" / book["id"] / f"{chapter}.json"
                chapter_data = json.loads(chapter_file.read_text(encoding="utf-8"))
                for verse in chapter_data.get("verses", []):
                    text = re.sub(r"<[^>]+>", " ", verse.get("text2026_html") or verse.get("text2026") or "")
                    if re.search(r"(?i)\b(?:ben[- ]?ammi|ammon\w*|ammons)\b", text):
                        ref = f'{book["id"]} {chapter}:{verse["number"]}'
                        if ref not in covered:
                            missing.append(ref)
        self.assertEqual(missing, [])

    def test_ammon_has_a_map_card_using_the_existing_rabba_location(self):
        self.assertEqual(self.ammon["kaart"]["plaats"], "Rabba")
        self.assertEqual(self.ammon["kaart"]["zekerheid"], "benadering")
        self.assertEqual(self.ammon["kaart"]["bron"], "data/geografie.geojson")
        self.assertEqual(self.ammon["kaart"]["link"], "kaart.html?plaats=Rabba")
        features = read_json("data/geografie.geojson")["features"]
        rabba = next(feature for feature in features if feature["properties"]["naam"] == "Rabba")
        self.assertEqual(self.ammon["kaart"]["coordinaten"], rabba["geometry"]["coordinates"])

    def test_each_nation_map_card_is_backed_by_a_geographic_location(self):
        features = read_json("data/geografie.geojson")["features"]
        by_name = {feature["properties"]["naam"]: feature for feature in features}
        for item in self.catalogue["items"]:
            with self.subTest(item=item["id"]):
                feature = by_name[item["kaart"]["plaats"]]
                self.assertEqual(item["kaart"]["coordinaten"], feature["geometry"]["coordinates"])
                self.assertIn(item["kaart"]["zekerheid"], {"zeker", "waarschijnlijk", "onzeker", "benadering"})
                self.assertTrue(item["kaart"]["bron"])

    def test_ammon_has_a_topic_tag_with_the_same_canonical_coverage(self):
        tags = read_json("data/tags.json")["tags"]
        tag = next(tag for tag in tags if tag["id"] == "volk-ammon")
        expected = set().union(*(expand_ref(ref) for ref in self.ammon["verzen"]))
        actual = {entry["ref"] for entry in tag["verzen"]}
        self.assertEqual(actual, expected)
        self.assertTrue(all(entry["humanReviewed"] is False for entry in tag["verzen"]))

    def test_each_nation_has_a_topic_tag_with_the_same_canonical_coverage(self):
        tags = {tag["id"]: tag for tag in read_json("data/tags.json")["tags"]}
        for item in self.catalogue["items"]:
            with self.subTest(item=item["id"]):
                tag = tags[f'volk-{item["id"]}']
                expected = set().union(*(expand_ref(ref) for ref in item["verzen"]))
                self.assertEqual({entry["ref"] for entry in tag["verzen"]}, expected)


class VolkenNatiesBrowserTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        handler = lambda *args, **kwargs: _QuietHandler(*args, directory=str(ROOT), **kwargs)
        cls.server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base_url = f"http://127.0.0.1:{cls.server.server_port}"
        cls.playwright = sync_playwright().start()
        browser_path = next(
            path for path in (
                pathlib.Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
                pathlib.Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
            ) if path.exists()
        )
        cls.browser = cls.playwright.chromium.launch(executable_path=str(browser_path), headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)

    def test_ammon_detail_uses_ov_citations_and_shows_ancestor_and_map(self):
        page = self.browser.new_page(viewport={"width": 1200, "height": 900})
        with contextlib.closing(page):
            page.goto(f"{self.base_url}/volken-naties.html?item=ammon")
            page.locator("#naslag h1").wait_for()
            self.assertEqual(page.locator("#naslag h1").inner_text(), "Ammon")
            self.assertIn("Ben-Ammi", page.locator(".vn-stamvader").inner_text())
            self.assertIn("Rabba", page.locator(".vn-kaart").inner_text())
            self.assertIn("Bron: Geografische aanduidingen in Gods Woord", page.locator(".vn-kaart").inner_text())
            self.assertEqual(
                page.locator("a.vn-kaart").get_attribute("href"),
                "kaart.html?plaats=Rabba",
            )
            page.locator("#naslag-gekoppelde-teksten .gt-vers-tekst .osv-vers").first.wait_for(timeout=5000)
            first_link = page.locator("#naslag-gekoppelde-teksten .gt-vers-kop > a").first
            self.assertEqual(first_link.get_attribute("href"), "index.html#genesis/19/30")

    def test_each_nation_opens_as_its_own_detail_page_with_universal_citations(self):
        page = self.browser.new_page(viewport={"width": 1200, "height": 900})
        with contextlib.closing(page):
            for item_id, name in (("edom", "Edom"), ("midian", "Midian"), ("moab", "Moab")):
                with self.subTest(item_id=item_id):
                    page.goto(f"{self.base_url}/volken-naties.html?item={item_id}")
                    page.locator("#naslag h1").wait_for()
                    self.assertEqual(page.locator("#naslag h1").inner_text(), name)
                    page.locator(".vn-stamvader").wait_for()
                    page.locator(".vn-kaart").wait_for()
                    page.locator("#naslag-gekoppelde-teksten .gt-vers-tekst .osv-vers").first.wait_for(timeout=5000)

    def test_wiki_links_to_the_new_category_without_a_legacy_page(self):
        wiki = (ROOT / "wiki.html").read_text(encoding="utf-8")
        overview = (ROOT / "wiki-overzicht.html").read_text(encoding="utf-8")
        self.assertIn('data-page="volken-naties.html"', wiki)
        self.assertIn('href="wiki.html#volken-naties"', overview)


if __name__ == "__main__":
    unittest.main()
