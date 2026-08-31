import json
from pathlib import Path

from scripts import import_inline_woordnummers as importer


def _write_guide(path):
    path.write_text(
        json.dumps(
            {
                "type": "USJ",
                "version": "3.1",
                "content": [
                    {"type": "chapter", "marker": "c", "number": "3"},
                    {
                        "type": "para",
                        "marker": "p",
                        "content": [
                            {"type": "verse", "marker": "v", "number": "13"},
                            {"type": "char", "marker": "w", "strong": "G1", "content": ["one"]},
                            {"type": "verse", "marker": "v", "number": "14"},
                            {"type": "char", "marker": "w", "strong": "G2", "content": ["two"]},
                        ],
                    },
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def test_cross_source_verse_replacement_is_idempotent(tmp_path):
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    source_path = source_dir / "51PHP.usj"
    _write_guide(source_path)
    source_hash = importer._sha256(source_path)

    data_dir = tmp_path / "data" / "filippenzen"
    data_dir.mkdir(parents=True)
    legacy = {
        "dataset": "robinson-scrivener-tr",
        "versie": "PHP.UTR",
        "sha256": "TR-SOURCE",
        "referentie": "PHP 3:14",
    }
    chapter = {
        "verses": [
            {
                "number": 14,
                "text2026": "Een twee",
                "grondtekst": [
                    {"woord": "one", "strongs": "G1"},
                    {"woord": "two", "strongs": "G2"},
                ],
                "woordnummers": [
                    {
                        "tekst": "Een twee",
                        "voorkomen": 1,
                        "strongs": ["G1", "G2"],
                        "herkomst": legacy,
                    }
                ],
            }
        ]
    }
    (data_dir / "3.json").write_text(json.dumps(chapter), encoding="utf-8")

    review = {
        "source": {
            "id": "bsb-full-strongs-usj",
            "version": "5.6",
            "sha256": source_hash,
        },
        "books": [
            {
                "code": "PHP",
                "repo_book": "filippenzen",
                "chapter": 3,
                "source_file": "51PHP.usj",
                "source_file_sha256": source_hash,
                "vervang_bronherkomst": {
                    "dataset": "robinson-scrivener-tr",
                    "versie": "PHP.UTR",
                    "sha256": "TR-SOURCE",
                    "referentie_code": "PHP",
                },
                "verses": [
                    {
                        "verse": 14,
                        "source_verse": 14,
                        "vervang_bronrecords": True,
                        "mappings": [
                            {
                                "tekst": "Een",
                                "source_verse": 13,
                                "bronindices": [0],
                                "grondindices": [0],
                                "confidence": 1,
                                "reviewstatus": "handmatig_gecontroleerd",
                            },
                            {
                                "tekst": "twee",
                                "bronindices": [0],
                                "grondindices": [1],
                                "confidence": 1,
                                "reviewstatus": "handmatig_gecontroleerd",
                            },
                        ],
                    }
                ],
            }
        ],
    }
    review_path = tmp_path / "review.json"
    review_path.write_text(json.dumps(review), encoding="utf-8")

    first = importer.apply_review_file(review_path, source_dir, tmp_path / "data", write=True)
    second = importer.apply_review_file(review_path, source_dir, tmp_path / "data", write=True)
    saved = json.loads((data_dir / "3.json").read_text(encoding="utf-8"))

    assert first["replaced"] == 1
    assert second["replaced"] == 2
    assert [mapping["tekst"] for mapping in saved["verses"][0]["woordnummers"]] == [
        "Een",
        "twee",
    ]
