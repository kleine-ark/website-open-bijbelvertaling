import json
from pathlib import Path

from scripts.registreer_reviewprincipes_samuel_koningen import REVIEW_CORRECTIES


ROOT = Path(__file__).resolve().parents[1]


def normaliseer(tekst: str) -> str:
    return " ".join(tekst.lower().split())


def test_alle_opgeslagen_reviewcorrecties_hebben_een_principe():
    principes = json.loads(
        (ROOT / "data" / "wijzigingsprincipes.json").read_text(encoding="utf-8")
    )["principes"]
    paren = {
        (normaliseer(item["oud"]), normaliseer(item["nieuw"]))
        for item in principes
    }

    ontbrekend = []
    for boek, hoofdstuk, vers, oud, nieuw in REVIEW_CORRECTIES:
        if (normaliseer(oud), normaliseer(nieuw)) not in paren:
            ontbrekend.append(f"{boek} {hoofdstuk}:{vers}: {oud!r} -> {nieuw!r}")

    assert not ontbrekend, "Ontbrekende principes:\n" + "\n".join(ontbrekend)


def test_nieuwe_reviewprincipes_zijn_tot_hun_beoordeelde_context_begrensd():
    principes = json.loads(
        (ROOT / "data" / "wijzigingsprincipes.json").read_text(encoding="utf-8")
    )["principes"]
    reviewprincipes = [item for item in principes if item.get("bron") == "menselijke-review"]

    assert reviewprincipes
    assert all(item.get("bereik") for item in reviewprincipes)


def test_reviewcorrecties_zijn_in_de_verzen_aan_hun_principe_gekoppeld():
    principes = json.loads(
        (ROOT / "data" / "wijzigingsprincipes.json").read_text(encoding="utf-8")
    )["principes"]
    ids = {}
    for item in principes:
        sleutel = (normaliseer(item["oud"]), normaliseer(item["nieuw"]))
        ids.setdefault(sleutel, set()).add(item["id"])
    hoofdstukken = {}
    ontbrekend = []
    for boek, hoofdstuk, versnummer, oud, nieuw in REVIEW_CORRECTIES:
        sleutel = (boek, hoofdstuk)
        if sleutel not in hoofdstukken:
            hoofdstukken[sleutel] = json.loads(
                (ROOT / "data" / boek / f"{hoofdstuk}.json").read_text(encoding="utf-8")
            )
        vers = next(
            item for item in hoofdstukken[sleutel]["verses"] if item["number"] == versnummer
        )
        verwacht = ids[(normaliseer(oud), normaliseer(nieuw))]
        gekoppeld = {item.get("principe") for item in vers.get("phraseDiff", [])}
        if verwacht.isdisjoint(gekoppeld):
            ontbrekend.append(
                f"{boek} {hoofdstuk}:{versnummer} -> {', '.join(sorted(verwacht))}"
            )

    assert not ontbrekend, "Niet gekoppelde reviewprincipes:\n" + "\n".join(ontbrekend)


def test_reviewprincipe_ids_zijn_uniek():
    principes = json.loads(
        (ROOT / "data" / "wijzigingsprincipes.json").read_text(encoding="utf-8")
    )["principes"]
    ids = [item["id"] for item in principes if item["id"].startswith("MR-SK-")]
    assert len(ids) == len(set(ids))
