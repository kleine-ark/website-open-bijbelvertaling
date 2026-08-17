import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def vers(hoofdstuk, nummer):
    data = json.loads((ROOT / "data" / "nehemia" / f"{hoofdstuk}.json").read_text(encoding="utf-8"))
    return next(item for item in data["verses"] if item["number"] == nummer)


class NehemiaGoogleReviewTest(unittest.TestCase):
    def test_eenduidige_correcties_zijn_verwerkt(self):
        verwacht = [
            ((2, 9), ("ruiters", "ruiteren")),
            ((3, 13), ("grendels", "grendelen")),
            ((3, 18), ("herstelden", "verbeterden")),
            ((4, 2), ("zwakke Joden", "amechtige Joden")),
            ((4, 8), ("samenzwering", "verbintenis")),
            ((4, 10), ("dragers is afgenomen", "dragers is vervallen")),
            ((4, 10), ("veel puin", "veel stof")),
            ((4, 22), ("overnachte", "vernachte")),
            ((4, 23), ("werpspies", "geweer")),
            ((5, 18), ("alle wijn", "allen wijn")),
            ((6, 19), ("bang te maken", "vreesachtig te maken")),
            ((9, 3), ("een vierde deel", "een vierendeel")),
            ((9, 11), ("gespleten", "gekliefd")),
            ((10, 33), ("voedseloffer", "spijsoffer")),
        ]
        for item in verwacht:
            (hoofdstuk, nummer), (nieuw, oud) = item
            tekst = vers(hoofdstuk, nummer)["text2026"]
            self.assertIn(nieuw, tekst, f"Nehemia {hoofdstuk}:{nummer}")
            self.assertIsNone(re.search(rf"(?<!\w){re.escape(oud)}(?!\w)", tekst),
                              f"Nehemia {hoofdstuk}:{nummer}")

    def test_reviewcorrecties_hebben_een_principe(self):
        for hoofdstuk, nummer in [(2, 9), (3, 13), (3, 18), (4, 2), (4, 8), (4, 10),
                                  (4, 22), (4, 23), (5, 18), (6, 19), (9, 3), (9, 11), (10, 33)]:
            verschillen = vers(hoofdstuk, nummer).get("phraseDiff", [])
            self.assertTrue(any(item.get("principe") for item in verschillen),
                            f"Nehemia {hoofdstuk}:{nummer} mist principe")

    def test_vertelling_staat_buiten_de_citaatopmaak(self):
        self.assertNotIn('class="direct-speech"', vers(6, 5)["text2026_html"])
        self.assertNotIn('class="direct-speech"', vers(8, 9)["text2026_html"])
        self.assertNotIn('class="direct-speech"', vers(13, 9)["text2026_html"])
        html = vers(13, 11)["text2026_html"]
        self.assertIn('<span class="direct-speech"><i>Waarom is', html)
        self.assertIn('</i></span> Maar ik verzamelde', html)


if __name__ == "__main__":
    unittest.main()
