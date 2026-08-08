import importlib.util
import json
import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "build_tijdsaanduidingen_data.py"
OUTPUT = ROOT / "data" / "naslag-tijdsaanduidingen.json"


def load_builder():
    spec = importlib.util.spec_from_file_location("build_tijdsaanduidingen_data", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TijdsaanduidingenDataTest(unittest.TestCase):
    def test_builder_finds_all_known_groups_across_the_corpus(self):
        data = load_builder().build_index(ROOT)
        groepen = data["groepen"]

        self.assertIn("markus 15:25", groepen["dag-3"])
        self.assertIn("johannes 4:52", groepen["dag-7"])
        self.assertIn("handelingen 23:23", groepen["nacht-3"])
        self.assertIn("4baruch 1:11", groepen["nacht-6"])
        self.assertIn("richteren 7:19", groepen["middelste-waak"])
        self.assertIn("exodus 14:24", groepen["morgenwake"])
        self.assertEqual(data["aantalUniekeVindplaatsen"], 52)

    def test_checked_in_output_is_current(self):
        expected = load_builder().build_index(ROOT)
        actual = json.loads(OUTPUT.read_text(encoding="utf-8"))
        self.assertEqual(actual, expected)


if __name__ == "__main__":
    unittest.main()
