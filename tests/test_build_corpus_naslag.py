"""Regressietests voor de corpusbrede wiki-naslaggenerator."""

import json
from pathlib import Path

from scripts.build_corpus_naslag import build_all, load_corpus


ROOT = Path(__file__).resolve().parents[1]


def read_json(relative):
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def test_corpus_bevat_alleen_echte_verzen():
    corpus = load_corpus(ROOT)

    assert len(corpus) == read_json("data/stats.json")["verses_total"]
    assert all(item.text and item.chapter > 0 and item.verse > 0 for item in corpus)
    assert {item.testament for item in corpus} == {"OT", "NT", "AP"}


def test_bouwen_zonder_schrijven_is_deterministisch():
    assert build_all(ROOT, write=False) == build_all(ROOT, write=False)
