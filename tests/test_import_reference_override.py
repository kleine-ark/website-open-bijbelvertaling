import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "import_inline_woordnummers_reference_override",
    ROOT / "scripts" / "import_inline_woordnummers.py",
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_legacy_reference_override_blijft_idempotent(tmp_path):
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    source_path = source_dir / "45ACT.usj"
    source_path.write_text(
        json.dumps(
            {
                "type": "USJ",
                "version": "3.1",
                "content": [
                    {"type": "chapter", "marker": "c", "number": "1"},
                    {
                        "type": "para",
                        "marker": "p",
                        "content": [
                            {"type": "verse", "marker": "v", "number": "2"},
                            {
                                "type": "char",
                                "marker": "w",
                                "strong": "G1722",
                                "content": ["In"],
                            },
                        ],
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    source_hash = MODULE._sha256(source_path)

    data_dir = tmp_path / "data" / "handelingen"
    data_dir.mkdir(parents=True)
    chapter_path = data_dir / "1.json"
    chapter_path.write_text(
        json.dumps(
            {
                "verses": [
                    {
                        "number": 1,
                        "text2026": "In",
                        "grondtekst": [{"woord": "εν", "strongs": "G1722"}],
                        "woordnummers": [
                            {
                                "tekst": "In",
                                "strongs": ["G1722"],
                                "herkomst": {
                                    "dataset": "legacy-tr",
                                    "versie": "1",
                                    "sha256": "LEGACY",
                                    "referentie": "ACT 1:1",
                                },
                            },
                            {
                                "tekst": "In",
                                "strongs": ["G1722"],
                                "herkomst": {
                                    "dataset": "guide",
                                    "versie": "1",
                                    "sha256": source_hash,
                                    "referentie": "ACT 1:1",
                                },
                            }
                        ],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    review_path = tmp_path / "review.json"
    review_path.write_text(
        json.dumps(
            {
                "source": {
                    "id": "guide",
                    "version": "1",
                    "sha256": source_hash,
                },
                "books": [
                    {
                        "code": "ACT",
                        "repo_book": "handelingen",
                        "chapter": 1,
                        "source_file": "45ACT.usj",
                        "source_file_sha256": source_hash,
                        "vervang_bronherkomst": {
                            "dataset": "legacy-tr",
                            "versie": "1",
                            "sha256": "LEGACY",
                        },
                        "verses": [
                            {
                                "verse": 1,
                                "source_verse": 2,
                                "vervang_bronrecords": True,
                                "vervang_bronreferentie": "ACT 1:1",
                                "mappings": [
                                    {
                                        "tekst": "In",
                                        "bronindices": [0],
                                        "grondindices": [0],
                                        "confidence": 1,
                                        "reviewstatus": "handmatig_gecontroleerd",
                                    }
                                ],
                            }
                        ],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    first = MODULE.apply_review_file(review_path, source_dir, tmp_path / "data", write=True)
    second = MODULE.apply_review_file(review_path, source_dir, tmp_path / "data", write=True)
    saved = json.loads(chapter_path.read_text(encoding="utf-8"))

    assert first["replaced"] == 2
    assert second["replaced"] == 1
    assert len(saved["verses"][0]["woordnummers"]) == 1
    assert saved["verses"][0]["woordnummers"][0]["herkomst"]["referentie"] == "ACT 1:2"
