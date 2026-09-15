"""Elk nummertje van een kanttekening hoort in de lezende tekst te staan.

Bij het aanbrengen van citaatopmaak is text2026_html in duizenden verzen
opnieuw opgebouwd, en daarbij vielen de notenmarkeringen weg: ruim tienduizend
kanttekeningen hadden geen nummertje meer om op te klikken. Niemand zag het,
want de citaatscripts vergelijken de kale tekst pas nadat ze alle <sup>'s
hebben weggestreept.

scripts/herstel_notenmarkers.py zet terug wat zeker terug te zetten is. Wat
overblijft staat op data/notenmarkers-werklijst.json. Deze test faalt zodra er
een nummertje ontbreekt dat niet op die werklijst staat, zodat een volgende
opmaakronde ze niet opnieuw ongemerkt kan wissen.
"""
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "herstel_notenmarkers", ROOT / "scripts" / "herstel_notenmarkers.py")
herstel = importlib.util.module_from_spec(spec)
spec.loader.exec_module(herstel)


def sup(nummer):
    return f'<sup class="note-marker" data-note="{nummer}">{nummer}</sup>'


def vers(noten, sv1888, ov2026):
    return {"marginNotes": [{"marker": n} for n in noten],
            "textSV1888_html": sv1888, "text2026_html": ov2026}


class PlaatsingTests(unittest.TestCase):
    def test_nummertjes_komen_terug_in_een_citaat(self):
        # Genesis 1:3, zoals het na de citaatopmaak op de site stond.
        v = vers(["10", "11"],
                 f"En God{sup('10')} zeide: Daar zij{sup('11')} licht! en daar werd licht.",
                 'En God zei: <span class="god-speaks"><i>Daar zij licht!</i></span> en daar werd licht.')
        html, geplaatst, lijst = herstel.herstel_vers(v)
        self.assertEqual(
            html,
            f'En God{sup("10")} zei: <span class="god-speaks"><i>Daar zij{sup("11")} licht!</i></span>'
            ' en daar werd licht.')
        self.assertEqual((geplaatst, lijst), (["10", "11"], []))

    def test_nummertje_voor_het_eerste_woord_blijft_buiten_de_span(self):
        v = vers(["a", "2"],
                 f"{sup('a')} Zalig zijn de{sup('2')} armen van geest; want hunner is het Koninkrijk.",
                 '<span class="god-speaks"><i>Zalig zijn de armen van geest; want van hen is het Koninkrijk.</i></span>')
        html, _, _ = herstel.herstel_vers(v)
        self.assertTrue(html.startswith(sup("a") + '<span class="god-speaks">'))
        self.assertIn(f"de{sup('2')} armen", html)

    def test_nummertje_aan_versbegin_krijgt_een_spatie_voor_de_tekst(self):
        v = vers(["t"], f"{sup('t')} En Hij kwam, en vond hen slapende.", "En Hij kwam, en vond hen slapende.")
        html, _, _ = herstel.herstel_vers(v)
        self.assertEqual(html, f"{sup('t')} En Hij kwam, en vond hen slapende.")

    def test_gelijke_verzen_in_een_hoofdstuk_krijgen_elk_hun_eigen_nummertjes(self):
        # 1 Koningen 19:10 en 19:14 zijn woordelijk gelijk; de html komt twee keer voor.
        import tempfile
        tekst = "En hij zei: Ik heb zeer geijverd voor JAHWEH."
        hoofdstuk = {"number": 19, "verses": [
            {"number": 10, "marginNotes": [{"marker": "19"}],
             "textSV1888_html": f"En hij zeide: Ik heb zeer{sup('19')} geijverd voor den HEERE.",
             "text2026": tekst, "text2026_html": tekst},
            {"number": 11, "text2026": "Tussenvers.", "text2026_html": "Tussenvers."},
            {"number": 14, "marginNotes": [{"marker": "30"}],
             "textSV1888_html": f"En hij zeide: Ik heb zeer geijverd{sup('30')} voor den HEERE.",
             "text2026": tekst, "text2026_html": tekst},
        ]}
        with tempfile.TemporaryDirectory() as wortel:
            pad = Path(wortel) / "data" / "koningen" / "19.json"
            pad.parent.mkdir(parents=True)
            pad.write_text(json.dumps(hoofdstuk, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            herstel.main(["--wortel", wortel, "--boek", "koningen", "--schrijf"])
            uit = json.loads(pad.read_text(encoding="utf-8"))["verses"]
        self.assertEqual(uit[0]["text2026_html"], f"En hij zei: Ik heb zeer{sup('19')} geijverd voor JAHWEH.")
        self.assertEqual(uit[1]["text2026_html"], "Tussenvers.")
        self.assertEqual(uit[2]["text2026_html"], f"En hij zei: Ik heb zeer geijverd{sup('30')} voor JAHWEH.")

    def test_nummertjes_op_dezelfde_plek_houden_hun_volgorde(self):
        v = vers(["1", "a"],
                 f"In{sup('1')}{sup('a')} den beginne schiep God den hemel.",
                 f"In{sup('1')} het begin schiep God de hemel.")
        html, _, _ = herstel.herstel_vers(v)
        self.assertEqual(html, f"In{sup('1')}{sup('a')} het begin schiep God de hemel.")

    def test_nummertje_na_een_leesteken_blijft_na_het_leesteken(self):
        v = vers(["44"],
                 f"Of tergen wij den Heere?{sup('44')} Zijn wij sterker dan Hij?",
                 "Of tergen wij de Heere? Zijn wij sterker dan Hij?")
        html, _, _ = herstel.herstel_vers(v)
        self.assertEqual(html, f"Of tergen wij de Heere?{sup('44')} Zijn wij sterker dan Hij?")

    def test_onzekere_plek_gaat_naar_de_werklijst_en_niet_in_de_tekst(self):
        v = vers(["7"],
                 f"Toen sprak de koning{sup('7')} tot zijn knechten.",
                 "En hij zei tegen de dienaren van het paleis dat zij moesten gaan.")
        html, geplaatst, lijst = herstel.herstel_vers(v)
        self.assertEqual(html, v["text2026_html"])
        self.assertEqual(geplaatst, [])
        self.assertEqual([item["marker"] for item in lijst], ["7"])

    def test_nummertje_zonder_bron_gaat_naar_de_werklijst(self):
        v = vers(["101"], "Doch indien een ander iets geopenbaard is.", "Maar als een ander iets geopenbaard is.")
        v["text1637_html"] = f"Doch indien {sup('1')} eenen anderen [yet] geopenbaert is."
        html, geplaatst, lijst = herstel.herstel_vers(v)
        self.assertEqual(html, v["text2026_html"])
        self.assertEqual(lijst[0]["reden"], "geen_nummertje_in_bron")


class CorpusTests(unittest.TestCase):
    def test_geen_nummertje_verdwijnt_ongemerkt(self):
        werklijst = json.loads((ROOT / "data" / "notenmarkers-werklijst.json").read_text(encoding="utf-8"))
        bekend = {(i["boek"], i["hoofdstuk"], i["vers"], i["marker"]) for i in werklijst["items"]}
        nieuw = []
        for boek, hoofdstuk, pad in herstel.hoofdstukken(ROOT):
            _, data = herstel.lees(pad)
            if data is None:
                continue
            for v in data["verses"]:
                for marker in herstel.ontbrekende_markers(v):
                    if (boek, hoofdstuk, v["number"], marker) not in bekend:
                        nieuw.append(f"{boek} {hoofdstuk}:{v['number']} noot {marker}")
        self.assertEqual(
            nieuw, [],
            f"{len(nieuw)} kanttekening(en) zonder nummertje in text2026_html, niet op de werklijst. "
            f"Draai scripts/herstel_notenmarkers.py. Eerste: {nieuw[:15]}")


if __name__ == "__main__":
    unittest.main()
