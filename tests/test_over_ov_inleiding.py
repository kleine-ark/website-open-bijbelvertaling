from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class OverOvInleidingTests(unittest.TestCase):
    def test_verwijderde_uitleg_over_oorspronkelijke_bewoording_ontbreekt(self):
        html = (ROOT / "over-ov.html").read_text(encoding="utf-8")

        self.assertNotIn(
            "Wie de oorspronkelijke bewoording wil zien, zet de opties gewoon uit.",
            html,
        )
        self.assertNotIn(
            "De hertaling is met behulp van AI gedaan.",
            html,
        )
        self.assertNotIn(
            "altijd gebaseerd op de Statenvertaling",
            html,
        )

    def test_opent_met_vier_schriftteksten_over_de_kracht_van_gods_woord(self):
        html = (ROOT / "over-ov.html").read_text(encoding="utf-8")
        begin = html.index('<div class="page">')
        eerste_tussenkop = html.index("<h2>Wat is de Open Vertaling?</h2>")
        opening = html[begin:eerste_tussenkop]

        for verwijzing in (
            "Psalmen 119:9",
            "Hebreeën 4:12",
            "Jesaja 55:11",
            "Jeremia 23:29",
        ):
            self.assertIn(verwijzing, opening)
        self.assertEqual(opening.count('class="woordkracht-ref"'), 4)
        self.assertEqual(opening.count('class="woordkracht-tekst"'), 4)

    def test_statusnoemt_de_actuele_menselijk_nagekeken_boeken(self):
        html = (ROOT / "over-ov.html").read_text(encoding="utf-8")

        self.assertNotIn("Genesis 1&ndash;20", html)
        for naam in (
            "Genesis",
            "Exodus",
            "Leviticus",
            "Numeri",
            "Deuteronomium",
            "Jozua",
            "Richteren 1&ndash;7",
            "Ruth",
            "Ezra",
            "Psalmen",
            "Prediker",
            "de twaalf kleine profeten",
        ):
            self.assertIn(naam, html)


if __name__ == "__main__":
    unittest.main()
