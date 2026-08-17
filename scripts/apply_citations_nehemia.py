#!/usr/bin/env python3
"""Herstel de nagekeken citaatopmaak van Nehemia zonder tekst te wijzigen."""

from pathlib import Path

from apply_citations_2koningen import kaal, markeer, zonder_spraak
from sweep_principe import lees, schrijf

ROOT = Path(__file__).resolve().parents[1]

RANGES = {
    (5, 13): [("mens", "Zo schudde God", "uitgeschud en leeg."), ("mens", "Amen!", "Amen!")],
    (6, 2): [("mens", "Kom en laat ons", "in het dal Ono.")],
    (6, 5): [],
    (6, 6): [("mens", "Het is onder", "deze zaken zijn.")],
    (6, 8): [("mens", "Er is van", "uit uw hart.")],
    (7, 65): [("mens", "dat zij van", "urim en thummim.")],
    (8, 7): [("mens", "Amen, amen!", "Amen, amen!")],
    (8, 9): [],
    (8, 12): [("mens", "Zwijg, want", "bedroeft u niet.")],
    (13, 9): [],
    (13, 11): [("mens", "Waarom is", "God verlaten?")],
    (13, 25): [("mens", "Als u uw", "voor u zult nemen!")],
}


def main():
    geraakt = 0
    per_hoofdstuk = {}
    for (hoofdstuk, vers), bereiken in RANGES.items():
        per_hoofdstuk.setdefault(hoofdstuk, {})[vers] = bereiken
    for hoofdstuk, opdrachten in per_hoofdstuk.items():
        pad = ROOT / "data" / "nehemia" / f"{hoofdstuk}.json"
        data, vorm = lees(str(pad))
        for vers in data["verses"]:
            if vers["number"] not in opdrachten:
                continue
            oud = vers["text2026_html"]
            basis = zonder_spraak(oud)
            nieuw = markeer(basis, opdrachten[vers["number"]]) if opdrachten[vers["number"]] else basis
            if kaal(oud) != kaal(nieuw):
                raise AssertionError(f"Nehemia {hoofdstuk}:{vers['number']}: tekst gewijzigd")
            if nieuw != oud:
                vers["text2026_html"] = nieuw
                geraakt += 1
        schrijf(str(pad), data, vorm)
    print(f"Citaatopmaak in {geraakt} verzen van Nehemia hersteld.")


if __name__ == "__main__":
    main()
