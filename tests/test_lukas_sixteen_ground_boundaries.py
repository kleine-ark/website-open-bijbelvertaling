import json
import re
from pathlib import Path

from scripts.import_inline_woordnummers import _grondtekst_sha256


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_GROUND_SHA = "76C7EC5EB45688D2A5B6353AA9595B8A3FAA093130DD52A43FF4DBCD80ADD0D6"


def _chapter():
    return json.loads((ROOT / "data/lukas/16.json").read_text(encoding="utf-8"))


def _review():
    return json.loads(
        (ROOT / "data/woordnummers-review/lukas-16.json").read_text(encoding="utf-8")
    )


def _whole_word_occurrences(text, target):
    return list(re.finditer(rf"(?<!\w){re.escape(target)}(?!\w)", text, re.I | re.U))


def test_lukas_zestien_behoudt_alle_grondtokens_en_de_nieuwe_pin():
    chapter = _chapter()
    assert sum(len(verse.get("grondtekst", [])) for verse in chapter["verses"]) == 604
    assert _grondtekst_sha256(chapter) == EXPECTED_GROUND_SHA


def test_lukas_zestien_rijke_man_staat_bij_het_zichtbare_vers_drieentwintig():
    verses = {int(verse["number"]): verse for verse in _chapter()["verses"]}
    assert [token["woord"] for token in verses[22]["grondtekst"][-4:]] == [
        "τον", "κολπον", "του", "αβρααμ"
    ]
    assert [token["woord"] for token in verses[23]["grondtekst"][:7]] == [
        "απεθανεν", "δε", "και", "ο", "πλουσιος", "και", "εταφη"
    ]


def test_lukas_zestien_review_is_atomair_volledig_en_bereikbaar():
    chapter = _chapter()
    review_path = ROOT / "data/woordnummers-review/lukas-16.json"
    review = _review()
    book = review["books"][0]
    verses = {int(verse["number"]): verse for verse in chapter["verses"]}

    assert book["grondtekst_sha256"] == EXPECTED_GROUND_SHA
    assert [record["verse"] for record in book["verses"]] == list(range(1, 32))
    assert "voorstel_" not in review_path.read_text(encoding="utf-8")

    mappings = [mapping for record in book["verses"] for mapping in record["mappings"]]
    assert len(mappings) == 497
    assert sum(len(mapping["grondindices"]) for mapping in mappings) == 604

    for record in book["verses"]:
        verse = verses[record["verse"]]
        covered = [index for mapping in record["mappings"] for index in mapping["grondindices"]]
        assert sorted(covered) == list(range(len(verse["grondtekst"])))
        assert len(covered) == len(set(covered))

        for mapping in record["mappings"]:
            assert mapping["reviewstatus"] == "handmatig_gecontroleerd"
            assert mapping["confidence"] == 1
            assert mapping["bronindices"] == mapping["grondindices"]
            assert 1 <= len(mapping["grondindices"]) <= 3
            target = mapping.get("tekst") or mapping["anker"]
            assert len(target.split()) <= 4
            occurrences = _whole_word_occurrences(verse["text2026"], target)
            assert occurrences, (record["verse"], target)
            if "voorkomen" not in mapping:
                assert len(occurrences) == 1, (record["verse"], target, len(occurrences))
            else:
                assert 1 <= mapping["voorkomen"] <= len(occurrences)


def test_lukas_zestien_geprojecteerde_records_zijn_atomair_en_volledig():
    chapter = _chapter()
    records = [mapping for verse in chapter["verses"] for mapping in verse["woordnummers"]]

    assert len(records) == 497
    assert sum(len(mapping["herkomst"]["grondindices"]) for mapping in records) == 604
    assert not any(
        mapping.get("tekst", "").strip() == verse["text2026"].strip()
        for verse in chapter["verses"]
        for mapping in verse["woordnummers"]
    )
