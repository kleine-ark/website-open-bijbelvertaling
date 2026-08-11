#!/usr/bin/env python3
"""Voeg Bijbelteksten over verkenners en spionnen toe aan de waarheidstag."""

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from sweep_principe import lees, schrijf  # noqa: E402


REFERENTIES = (
    "genesis 42:9", "genesis 42:11", "genesis 42:14", "genesis 42:16",
    "genesis 42:30", "genesis 42:31", "genesis 42:34",
    "numeri 13:2", "numeri 13:16", "numeri 13:17", "numeri 13:21",
    "numeri 13:25", "numeri 13:32", "numeri 14:6", "numeri 14:7",
    "numeri 14:34", "numeri 14:36", "numeri 14:38", "numeri 21:1",
    "numeri 21:32", "deuteronomium 1:22", "deuteronomium 1:23",
    "deuteronomium 1:24", "deuteronomium 1:25",
    "jozua 2:1", "jozua 2:14", "jozua 2:16", "jozua 2:22",
    "jozua 2:23", "jozua 2:24", "jozua 6:22", "jozua 6:23",
    "jozua 6:25", "jozua 14:7", "richteren 1:23", "richteren 1:24",
    "richteren 1:25", "richteren 18:2", "richteren 18:14",
    "richteren 18:17", "1samuel 26:4", "2samuel 10:3",
    "2samuel 15:10", "1kronieken 19:3",
    "psalmen 5:9", "psalmen 27:11", "psalmen 54:7", "psalmen 56:3",
    "psalmen 59:11", "psalmen 92:12", "lukas 20:20", "galaten 2:4",
    "hebreeen 11:31", "1makkabeeen 5:38", "1makkabeeen 12:26",
    "1meqabyan 13:20", "jubileeen 44:9",
)


def main() -> None:
    pad = ROOT / "data" / "tags.json"
    data, vorm = lees(str(pad))
    tag = next(item for item in data["tags"] if item["id"] == "waarheid-en-levensgevaar")
    bestaand = {item["ref"] for item in tag["verzen"]}
    toegevoegd = 0
    for ref in REFERENTIES:
        if ref in bestaand:
            continue
        tag["verzen"].append({"ref": ref, "rang": 3})
        bestaand.add(ref)
        toegevoegd += 1
    schrijf(str(pad), data, vorm)
    print(f"Waarheidstag: {toegevoegd} verwijzingen toegevoegd; {len(bestaand)} totaal.")


if __name__ == "__main__":
    main()
