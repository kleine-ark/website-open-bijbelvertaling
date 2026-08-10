from pathlib import Path
from html.parser import HTMLParser
import struct
import unittest


ROOT = Path(__file__).resolve().parents[1]
NAMES = (
    "kaart",
    "stamboom",
    "geografie",
    "maateenheden",
    "tijdsaanduidingen",
    "materialen",
    "dieren",
    "bomen-planten",
    "liederen",
    "gebeden",
)


def webp_chunks(data):
    offset = 12
    while offset + 8 <= len(data):
        name = data[offset : offset + 4]
        length = struct.unpack_from("<I", data, offset + 4)[0]
        payload = data[offset + 8 : offset + 8 + length]
        yield name, payload
        offset += 8 + length + (length % 2)


class ImageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.images = []

    def handle_starttag(self, tag, attrs):
        if tag == "img":
            self.images.append(dict(attrs))


class WikiCinemagraphTests(unittest.TestCase):
    def test_personen_en_muziekinstrumenten_zijn_aparte_wikipaginas(self):
        overview = (ROOT / "wiki-overzicht.html").read_text(encoding="utf-8")
        shell = (ROOT / "wiki.html").read_text(encoding="utf-8")

        for slug in ("personen", "muziekinstrumenten"):
            self.assertIn(f'href="wiki.html#{slug}"', overview)
            self.assertIn(f'href="#{slug}" data-page="{slug}.html"', shell)
            page = (ROOT / f"{slug}.html").read_text(encoding="utf-8")
            data_file = "personen-register" if slug == "personen" else f"naslag-{slug}"
            self.assertIn(f'data-naslag="data/{data_file}.json"', page)

    def test_removed_begrippen_page_is_not_linked_from_the_wiki(self):
        overview = (ROOT / "wiki-overzicht.html").read_text(encoding="utf-8")
        shell = (ROOT / "wiki.html").read_text(encoding="utf-8")

        self.assertNotIn('href="wiki.html#begrippen"', overview)
        self.assertNotIn('href="#begrippen"', shell)

        public_files = list(ROOT.glob("*.html")) + [
            ROOT / "llms.txt",
            ROOT / "sitemap.xml",
            ROOT / "scripts" / "build_sitemap.py",
        ]
        for path in public_files:
            self.assertNotIn(
                "begrippen.html",
                path.read_text(encoding="utf-8"),
                f"verwijderde Begrippenpagina wordt nog genoemd in {path.name}",
            )

    def test_motion_tiles_use_animated_webp_without_fallback(self):
        html = (ROOT / "wiki-overzicht.html").read_text(encoding="utf-8")
        self.assertNotIn("<picture", html)
        self.assertNotIn("prefers-reduced-motion", html)

        parser = ImageParser()
        parser.feed(html)
        images = {
            Path(image["src"]).stem: image
            for image in parser.images
            if image.get("src", "").startswith("images/wiki/")
        }

        self.assertEqual(set(images), set(NAMES))
        for name in NAMES:
            self.assertEqual(images[name]["src"], f"images/wiki/{name}.webp")

    def test_assets_are_animated_five_second_webp_loops(self):
        for name in NAMES:
            data = (ROOT / "images" / "wiki" / f"{name}.webp").read_bytes()
            self.assertEqual(data[:4], b"RIFF")
            self.assertEqual(data[8:12], b"WEBP")

            chunks = list(webp_chunks(data))
            vp8x = next(payload for kind, payload in chunks if kind == b"VP8X")
            width = 1 + int.from_bytes(vp8x[4:7], "little")
            height = 1 + int.from_bytes(vp8x[7:10], "little")
            self.assertEqual((width, height), (600, 300))

            anim = next(payload for kind, payload in chunks if kind == b"ANIM")
            self.assertEqual(int.from_bytes(anim[4:6], "little"), 0)

            frames = [payload for kind, payload in chunks if kind == b"ANMF"]
            self.assertGreater(len(frames), 1)
            duration = sum(
                int.from_bytes(frame[12:15], "little") for frame in frames
            )
            self.assertGreaterEqual(duration, 4000)
            self.assertLessEqual(duration, 6000)


if __name__ == "__main__":
    unittest.main()
