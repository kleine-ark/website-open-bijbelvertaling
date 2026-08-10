from html.parser import HTMLParser
from pathlib import Path
import struct
import unittest

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
NAMES = ("liederen", "gebeden")


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


class WikiLiederenGebedenLogoTests(unittest.TestCase):
    def test_generated_art_sources_match_the_painterly_wiki_style(self):
        for name in NAMES:
            source = ROOT / "images" / "wiki" / "bronnen" / f"{name}.webp"
            with Image.open(source) as artwork:
                self.assertEqual(artwork.size, (1200, 600))

            with Image.open(ROOT / "images" / "wiki" / f"{name}.webp") as animation:
                animation.seek(0)
                frame = animation.convert("RGB")
                colors = frame.getcolors(frame.width * frame.height)
                self.assertIsNotNone(colors)
                self.assertGreater(len(colors), 5000)

    def test_tiles_use_only_generated_raster_art(self):
        html = (ROOT / "wiki-overzicht.html").read_text(encoding="utf-8")
        parser = ImageParser()
        parser.feed(html)
        images = {
            Path(image["src"]).stem: image
            for image in parser.images
            if Path(image.get("src", "")).stem in NAMES
        }

        self.assertNotIn("<picture", html)
        self.assertEqual(set(images), set(NAMES))
        for name in NAMES:
            self.assertEqual(images[name]["src"], f"images/wiki/{name}.webp")
            self.assertFalse((ROOT / "images" / "wiki" / f"{name}.svg").exists())

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
            self.assertEqual(len(frames), 50)
            duration = sum(
                int.from_bytes(frame[12:15], "little") for frame in frames
            )
            self.assertEqual(duration, 5000)


if __name__ == "__main__":
    unittest.main()
