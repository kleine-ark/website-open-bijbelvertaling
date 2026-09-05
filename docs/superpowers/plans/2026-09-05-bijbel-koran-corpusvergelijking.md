# Bijbel–Koran Corpus Comparison Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a reproducible, local-only dashboard that compares the original-language Bible corpus with the Tanzil Uthmani Quran corpus by corpus size, words, controlled entities, verse occurrences, and total mentions.

**Architecture:** Keep the complete tool under `tools/corpusvergelijking/` and exclude that directory from deployment. Two Python adapters normalize Bible and Quran source snapshots to one typed schema; a deterministic aggregator writes a single browser-ready JSON file. A static HTML/CSS/JavaScript interface switches Bible scope without doing corpus analysis or network requests in the browser.

**Tech Stack:** Python 3 standard library, JSON, pytest, static HTML5/CSS/vanilla JavaScript, existing Open Vertaling chapter and naslag JSON.

**Spec:** `docs/superpowers/specs/2026-09-05-bijbel-koran-corpusvergelijking-design.md`

## Global Constraints

- Work only in `C:\Users\rickd\Documents\GitHub\website-open-bijbelvertaling`.
- The tool remains local: do not add it to public navigation, sitemap, service worker, downloads, or release metadata.
- Exclude `tools/corpusvergelijking/` from the production rsync payload.
- Default Bible scope is the 66 canonical books; also support canon plus apocrypha and the complete available Open Vertaling corpus.
- Count only original-language word tokens; never silently substitute Dutch translation words.
- Quran text source is Tanzil Uthmani as identified by Open Koran Weergave; persist source URL, version or checksum, license/attribution, and import date.
- Keep `entities`, `verses`, and `mentions` as separate measures.
- Every metric carries one of `complete`, `controlled_catalog`, `partial`, or `not_comparable`.
- An absent or incomplete source produces a visible coverage record, never a fabricated zero.
- Use stable, language-neutral concept IDs; Dutch labels and source-language forms are aliases.
- Preserve all unrelated changes in the existing dirty worktree and stage only files named by each task.

---

## File map

- `.github/workflows/deploy.yml` — excludes the complete local research tool from production deployment.
- `tools/corpusvergelijking/README.md` — local run instructions, sources, licenses, and metric definitions.
- `tools/corpusvergelijking/schema.py` — dataclasses, status constants, JSON serialization, and validation shared by both adapters.
- `tools/corpusvergelijking/bible_adapter.py` — corpus-scope selection and original-language Bible token extraction.
- `tools/corpusvergelijking/quran_adapter.py` — Tanzil/Open Koran snapshot loading and Quran token/entity normalization.
- `tools/corpusvergelijking/build.py` — aggregation, per-10,000 normalization, deterministic output, and command-line entry point.
- `tools/corpusvergelijking/concepts.json` — controlled category and cross-corpus concept mappings.
- `tools/corpusvergelijking/sources/openkoran/manifest.json` — source URLs, attribution, version/checksum, import date, and file checksums.
- `tools/corpusvergelijking/sources/openkoran/quran-uthmani.json` — local 114-soera Arabic word-token snapshot.
- `tools/corpusvergelijking/sources/openkoran/entities.json` — local controlled Open Koran entity snapshot with references.
- `tools/corpusvergelijking/output/corpusvergelijking.json` — deterministic generated dashboard data.
- `tools/corpusvergelijking/index.html` — local dashboard structure and accessible controls.
- `tools/corpusvergelijking/app.js` — JSON loading, scope switching, tables, bars, warnings, and method panel.
- `tools/corpusvergelijking/style.css` — responsive dashboard styling isolated from the public website CSS.
- `tests/fixtures/corpusvergelijking/` — minimal Bible and Quran fixtures for deterministic unit tests.
- `tests/test_corpusvergelijking_schema.py` — schema and invalid-input tests.
- `tests/test_corpusvergelijking_bible.py` — scope, word-token, and missing-source tests.
- `tests/test_corpusvergelijking_quran.py` — 114-soera, Basmala, token, checksum, and entity tests.
- `tests/test_corpusvergelijking_build.py` — aggregation, normalization, determinism, and cross-reference tests.
- `tests/test_corpusvergelijking_ui.py` — static UI contract and local-only deployment tests.

---

### Task 1: Protect the local-only deployment boundary and define the shared schema

**Files:**
- Modify: `.github/workflows/deploy.yml`
- Create: `tools/corpusvergelijking/schema.py`
- Create: `tests/test_corpusvergelijking_schema.py`
- Create: `tests/test_corpusvergelijking_ui.py`

**Interfaces:**
- Produces: `CoverageStatus`, `SourceMeta`, `Metric`, `EntityStat`, `CorpusResult`, `validate_result(result: CorpusResult) -> None`, and `to_jsonable(value: Any) -> Any`.
- Produces: a production exclusion rule for `tools/corpusvergelijking/` used by every later task.

- [ ] **Step 1: Write failing schema and deployment tests**

```python
# tests/test_corpusvergelijking_schema.py
from pathlib import Path
import pytest

from tools.corpusvergelijking.schema import (
    CorpusResult, EntityStat, Metric, SourceMeta, validate_result,
)


def source() -> SourceMeta:
    return SourceMeta(
        id="fixture",
        name="Fixture",
        language="hebrew",
        url="https://example.invalid/source",
        version="sha256:abc",
        imported_at="2026-09-05",
        attribution="Public-domain fixture",
    )


def test_schema_keeps_three_measures_separate():
    entity = EntityStat(
        concept_id="material.gold",
        label="Goud",
        category="materials",
        entities=1,
        verses=2,
        mentions=3,
        status="controlled_catalog",
        references=["genesis.2.11", "exodus.25.3"],
    )
    assert (entity.entities, entity.verses, entity.mentions) == (1, 2, 3)


def test_validator_rejects_unknown_coverage_status():
    result = CorpusResult(
        corpus_id="bible-canon",
        label="Bijbel — canoniek",
        sources=[source()],
        units={"books": Metric(66, "complete")},
        words=Metric(2, "complete"),
        unique_words=Metric(2, "complete"),
        categories={},
        warnings=[],
    )
    result.words.status = "klaar"
    with pytest.raises(ValueError, match="coverage status"):
        validate_result(result)
```

```python
# tests/test_corpusvergelijking_ui.py
from pathlib import Path

ROOT = Path(__file__).parents[1]


def test_local_tool_is_excluded_from_production_deploy():
    workflow = (ROOT / ".github/workflows/deploy.yml").read_text(encoding="utf-8")
    assert "tools/corpusvergelijking/" in workflow


def test_local_tool_is_not_linked_from_public_surfaces():
    for name in ("wiki.html", "sitemap.xml", "sw.js"):
        assert "corpusvergelijking" not in (ROOT / name).read_text(encoding="utf-8").lower()
```

- [ ] **Step 2: Run the focused tests and verify failure**

Run: `python -m pytest -q tests/test_corpusvergelijking_schema.py tests/test_corpusvergelijking_ui.py`

Expected: collection fails because `tools.corpusvergelijking.schema` does not exist and the deploy exclusion is absent.

- [ ] **Step 3: Implement the schema and deployment exclusion**

Use dataclasses with these exact fields:

```python
# tools/corpusvergelijking/schema.py
from dataclasses import asdict, dataclass, field
from typing import Any

COVERAGE_STATUSES = {"complete", "controlled_catalog", "partial", "not_comparable"}


@dataclass
class SourceMeta:
    id: str
    name: str
    language: str
    url: str
    version: str
    imported_at: str
    attribution: str


@dataclass
class Metric:
    value: int | float | None
    status: str
    note: str = ""


@dataclass
class EntityStat:
    concept_id: str
    label: str
    category: str
    entities: int
    verses: int
    mentions: int
    status: str
    references: list[str] = field(default_factory=list)
    note: str = ""


@dataclass
class CorpusResult:
    corpus_id: str
    label: str
    sources: list[SourceMeta]
    units: dict[str, Metric]
    words: Metric
    unique_words: Metric
    categories: dict[str, list[EntityStat]]
    warnings: list[str]


def _check_status(status: str) -> None:
    if status not in COVERAGE_STATUSES:
        raise ValueError(f"unknown coverage status: {status}")


def validate_result(result: CorpusResult) -> None:
    _check_status(result.words.status)
    _check_status(result.unique_words.status)
    for metric in result.units.values():
        _check_status(metric.status)
    seen: set[str] = set()
    for category, entities in result.categories.items():
        for entity in entities:
            _check_status(entity.status)
            if entity.category != category:
                raise ValueError(f"category mismatch: {entity.concept_id}")
            if entity.concept_id in seen:
                raise ValueError(f"duplicate concept id: {entity.concept_id}")
            seen.add(entity.concept_id)
            if entity.verses != len(set(entity.references)):
                raise ValueError(f"verse/reference mismatch: {entity.concept_id}")


def to_jsonable(value: Any) -> Any:
    return asdict(value)
```

Add this exact line to `rsync_excludes` in `.github/workflows/deploy.yml`:

```yaml
        tools/corpusvergelijking/
```

- [ ] **Step 4: Run the focused tests**

Run: `python -m pytest -q tests/test_corpusvergelijking_schema.py tests/test_corpusvergelijking_ui.py`

Expected: all tests pass.

- [ ] **Step 5: Commit only Task 1 files**

```powershell
git add .github/workflows/deploy.yml tools/corpusvergelijking/schema.py tests/test_corpusvergelijking_schema.py tests/test_corpusvergelijking_ui.py
git commit -m "feat: isoleer lokale corpusvergelijking"
```

---

### Task 2: Import and validate the Open Koran snapshot

**Files:**
- Create: `tools/corpusvergelijking/quran_adapter.py`
- Create: `tools/corpusvergelijking/sources/openkoran/manifest.json`
- Create: `tools/corpusvergelijking/sources/openkoran/quran-uthmani.json`
- Create: `tools/corpusvergelijking/sources/openkoran/entities.json`
- Create: `tests/fixtures/corpusvergelijking/quran-mini.json`
- Create: `tests/fixtures/corpusvergelijking/quran-entities-mini.json`
- Create: `tests/fixtures/corpusvergelijking/quran-manifest-mini.json`
- Create: `tests/test_corpusvergelijking_quran.py`

**Interfaces:**
- Consumes: schema types from Task 1.
- Produces: `load_quran(corpus_path: Path, entities_path: Path, manifest_path: Path, require_full_corpus: bool = True) -> CorpusResult`.
- Source token schema: `{"surah": 1, "ayah": 1, "words": [{"position": 1, "text": "بِسْمِ", "lemma": "بِسْم", "root": "سمو"}]}`.
- Entity schema: `{"concept_id": "material.gold", "category": "materials", "label": "Goud", "status": "controlled_catalog", "occurrences": [{"ref": "3:14", "word_positions": [4]}]}`.

- [ ] **Step 1: Create minimal Quran fixtures and failing tests**

```python
# tests/test_corpusvergelijking_quran.py
import hashlib
import json
from pathlib import Path
import pytest

from tools.corpusvergelijking.quran_adapter import load_quran

FIX = Path(__file__).parent / "fixtures/corpusvergelijking"


def test_quran_counts_orthographic_tokens_and_basmala_once():
    result = load_quran(
        FIX / "quran-mini.json",
        FIX / "quran-entities-mini.json",
        FIX / "quran-manifest-mini.json",
        require_full_corpus=False,
    )
    assert result.words.value == 6
    assert result.units["surahs"].value == 1
    assert result.units["verses"].value == 2


def test_quran_entity_counts_unique_verses_and_total_mentions():
    result = load_quran(
        FIX / "quran-mini.json",
        FIX / "quran-entities-mini.json",
        FIX / "quran-manifest-mini.json",
        require_full_corpus=False,
    )
    gold = result.categories["materials"][0]
    assert gold.entities == 1
    assert gold.verses == 1
    assert gold.mentions == 2


def test_quran_rejects_bad_snapshot_checksum(tmp_path):
    manifest = json.loads((FIX / "quran-manifest-mini.json").read_text(encoding="utf-8"))
    manifest["files"]["quran-uthmani.json"] = "sha256:deadbeef"
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ValueError, match="checksum"):
        load_quran(FIX / "quran-mini.json", FIX / "quran-entities-mini.json", path, require_full_corpus=False)
```

The mini corpus contains exactly two ayahs and six `words` entries. Its entity fixture maps two word positions in one ayah to `material.gold`. Generate the fixture checksums from their UTF-8 bytes and store them in `quran-manifest-mini.json`.

- [ ] **Step 2: Run the Quran tests and verify failure**

Run: `python -m pytest -q tests/test_corpusvergelijking_quran.py`

Expected: collection fails because `quran_adapter.py` does not exist.

- [ ] **Step 3: Implement the Quran adapter**

Implement these exact rules:

```python
def normalize_arabic_word(word: str) -> str:
    # Remove Quranic annotation marks and combining marks for the unique-form
    # key, while retaining the Unicode base letters.
    normalized = unicodedata.normalize("NFD", word)
    return "".join(ch for ch in normalized if not unicodedata.combining(ch) and unicodedata.category(ch).startswith("L"))


def load_quran(corpus_path, entities_path, manifest_path, require_full_corpus=True):
    verify_manifest_checksums(manifest_path, [corpus_path, entities_path])
    verses = read_json(corpus_path)["verses"]
    if require_full_corpus and {v["surah"] for v in verses} != set(range(1, 115)):
        raise ValueError("Quran snapshot must contain all 114 surahs")
    # Validate unique (surah, ayah, position), count words and unique normalized
    # forms, and resolve every occurrence word position before building result.
```

Set Quran corpus word metrics to `complete`; set imported entity metrics to each entry's supplied `controlled_catalog` status. Reject missing verse references, missing word positions, duplicate token IDs, negative counts, unknown categories, and a manifest whose declared SHA-256 differs from file bytes.

- [ ] **Step 4: Populate and verify the full local snapshot**

Export the same Tanzil Uthmani word records and controlled entity records used by Open Koran Weergave into the two named JSON files. Generate the manifest after both snapshots exist, so its checksums cannot be copied incorrectly:

```python
source_dir = Path("tools/corpusvergelijking/sources/openkoran")
files = {}
for name in ("quran-uthmani.json", "entities.json"):
    digest = hashlib.sha256((source_dir / name).read_bytes()).hexdigest()
    files[name] = f"sha256:{digest}"
manifest = {
    "source": "Open Koran Weergave",
    "source_url": "https://openkoran.nl/",
    "arabic_text": "Tanzil Uthmani",
    "version": "Open Koran v0.11",
    "imported_at": "2026-09-05",
    "attribution": "Arabische tekst: Tanzil (Uthmani); gecontroleerde catalogus: Open Koran Weergave",
    "files": files,
}
(source_dir / "manifest.json").write_text(
    json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    encoding="utf-8",
)
```

Do not scrape rendered HTML tables as the canonical snapshot; export structured verse/word IDs and controlled entity occurrences from Open Koran's own data source.

- [ ] **Step 5: Run the Quran validation tests against fixtures and the full snapshot**

Add:

```python
def test_full_quran_snapshot_has_114_surahs():
    root = Path(__file__).parents[1] / "tools/corpusvergelijking/sources/openkoran"
    result = load_quran(root / "quran-uthmani.json", root / "entities.json", root / "manifest.json")
    assert result.units["surahs"].value == 114
    assert result.units["verses"].value > 6200
    assert result.words.value > 70000
    assert result.words.status == "complete"
```

Run: `python -m pytest -q tests/test_corpusvergelijking_quran.py`

Expected: all tests pass and no coverage warning claims the controlled entity catalog is corpus-complete.

- [ ] **Step 6: Commit only Task 2 files**

```powershell
git add tools/corpusvergelijking/quran_adapter.py tools/corpusvergelijking/sources/openkoran tests/fixtures/corpusvergelijking tests/test_corpusvergelijking_quran.py
git commit -m "feat: voeg Tanzil-corpusmomentopname toe"
```

---

### Task 3: Build Bible scope selection and original-language word counts

**Files:**
- Create: `tools/corpusvergelijking/bible_adapter.py`
- Create: `tests/fixtures/corpusvergelijking/books-mini.json`
- Create: `tests/fixtures/corpusvergelijking/bible/genesis/1.json`
- Create: `tests/fixtures/corpusvergelijking/bible/mattheus/1.json`
- Create: `tests/fixtures/corpusvergelijking/bible/tobit/1.json`
- Create: `tests/fixtures/corpusvergelijking/bible/henoch/1.json`
- Create: `tests/test_corpusvergelijking_bible.py`

**Interfaces:**
- Consumes: `data/books.json`; chapter `verses[*].grondtekst[*].woord`; schema types from Task 1.
- Produces: `BibleScope` literal values `canon`, `canon_apocrypha`, `complete`.
- Produces: `select_books(books: list[dict], scope: str) -> list[dict]` and `load_bible(root: Path, scope: str, books_path: Path | None = None) -> CorpusResult`.

- [ ] **Step 1: Write failing scope and token tests**

```python
# tests/test_corpusvergelijking_bible.py
from pathlib import Path

from tools.corpusvergelijking.bible_adapter import load_bible, select_books

FIX = Path(__file__).parent / "fixtures/corpusvergelijking"


def test_canon_scope_excludes_apocrypha_and_ethiopic():
    books = __import__("json").loads((FIX / "books-mini.json").read_text(encoding="utf-8"))["books"]
    assert [b["id"] for b in select_books(books, "canon")] == ["genesis", "mattheus"]


def test_expanded_scopes_are_additive():
    books = __import__("json").loads((FIX / "books-mini.json").read_text(encoding="utf-8"))["books"]
    assert [b["id"] for b in select_books(books, "canon_apocrypha")] == ["genesis", "mattheus", "tobit"]
    assert [b["id"] for b in select_books(books, "complete")] == ["genesis", "mattheus", "tobit", "henoch"]


def test_word_count_uses_grondtekst_not_dutch_translation():
    result = load_bible(FIX / "bible", "canon", FIX / "books-mini.json")
    assert result.words.value == 5
    assert result.unique_words.value == 5


def test_missing_ground_text_marks_scope_partial():
    result = load_bible(FIX / "bible", "complete", FIX / "books-mini.json")
    assert result.words.status == "partial"
    assert any("henoch 1:1" in warning.lower() for warning in result.warnings)
```

- [ ] **Step 2: Run the Bible tests and verify failure**

Run: `python -m pytest -q tests/test_corpusvergelijking_bible.py`

Expected: collection fails because `bible_adapter.py` does not exist.

- [ ] **Step 3: Implement scope classification and token extraction**

Use `testament == "AP"` for apocrypha and `book.get("ethiopic")` or the repository's established Ethiopic marker for Ethiopic books. Define canonical as `testament in {"OT", "NT"}` and not Ethiopic. Preserve `data/books.json` order.

For each selected chapter, read every verse and count `verse["grondtekst"]` entries whose `woord` contains at least one Unicode letter. Build unique-form keys by NFD-normalizing and removing combining marks, but retain the original-language value for audit output. Never read `text2026` or `text2026_html` for word counts.

Set the corpus metric to `partial` and add an exact `boek hoofdstuk:vers` warning for every non-empty verse that lacks usable `grondtekst`. Group repeated warnings per book in the serialized result to keep the interface readable.

- [ ] **Step 4: Run the Bible tests**

Run: `python -m pytest -q tests/test_corpusvergelijking_bible.py`

Expected: all tests pass.

- [ ] **Step 5: Add real-corpus invariants**

```python
def test_real_canon_has_exactly_66_books():
    root = Path(__file__).parents[1]
    result = load_bible(root, "canon")
    assert result.units["books"].value == 66
    assert result.units["chapters"].value > 1100
    assert result.units["verses"].value > 30000


def test_bible_scope_counts_are_monotonic():
    root = Path(__file__).parents[1]
    values = [load_bible(root, scope).units["books"].value for scope in ("canon", "canon_apocrypha", "complete")]
    assert values == sorted(values)
```

Run: `python -m pytest -q tests/test_corpusvergelijking_bible.py`

Expected: all tests pass; partial original-language coverage remains explicit rather than failing the build.

- [ ] **Step 6: Commit only Task 3 files**

```powershell
git add tools/corpusvergelijking/bible_adapter.py tests/fixtures/corpusvergelijking/books-mini.json tests/fixtures/corpusvergelijking/bible tests/test_corpusvergelijking_bible.py
git commit -m "feat: tel Bijbelse grondtekst per corpusomvang"
```

---

### Task 4: Normalize controlled concepts and Bible entity occurrences

**Files:**
- Create: `tools/corpusvergelijking/concepts.json`
- Modify: `tools/corpusvergelijking/bible_adapter.py`
- Modify: `tests/test_corpusvergelijking_bible.py`
- Create: `tests/fixtures/corpusvergelijking/concepts-mini.json`
- Create: `tests/fixtures/corpusvergelijking/naslag-materialen-mini.json`

**Interfaces:**
- Consumes: existing `data/naslag-materialen.json`, `data/naslag-dieren.json`, `data/naslag-bomen-planten.json`, `data/naslag-personen.json`, `data/geografie-runtime.geojson`, `data/naslag-volken-naties.json`, `data/naslag-tijdsaanduidingen.json`, and original-language `grondtekst` tokens. Categories without a repository naslag file are defined explicitly in `concepts.json` and counted only through ground-token source IDs or forms.
- Produces: `load_concepts(path: Path) -> dict[str, dict]` and `load_bible_entities(root: Path, selected_book_ids: set[str], concepts: dict, naslag_paths: dict[str, Path] | None = None) -> dict[str, list[EntityStat]]`.

- [ ] **Step 1: Write failing concept tests**

```python
def test_concept_mapping_is_language_neutral_and_filters_scope():
    result = load_bible_entities(
        FIX,
        {"genesis"},
        load_concepts(FIX / "concepts-mini.json"),
        naslag_paths={"materials": FIX / "naslag-materialen-mini.json"},
    )
    gold = result["materials"][0]
    assert gold.concept_id == "material.gold"
    assert gold.references == ["genesis.2.11"]
    assert gold.mentions == 1


def test_duplicate_concept_id_is_rejected(tmp_path):
    path = tmp_path / "concepts.json"
    path.write_text('[{"id":"material.gold"},{"id":"material.gold"}]', encoding="utf-8")
    with pytest.raises(ValueError, match="duplicate concept"):
        load_concepts(path)
```

The mini mapping must show separate aliases:

```json
[
  {
    "id": "material.gold",
    "category": "materials",
    "label_nl": "Goud",
    "bible_ids": ["goud"],
    "quran_ids": ["goud"],
    "source_ids": {"hebrew": ["H2091"], "greek": ["G5557"]},
    "source_aliases": {"hebrew": ["זהב"], "greek": ["χρυσός"], "arabic": ["ذَهَب"]}
  }
]
```

- [ ] **Step 2: Run the focused test and verify failure**

Run: `python -m pytest -q tests/test_corpusvergelijking_bible.py -k concept`

Expected: fails because concept loaders are absent.

- [ ] **Step 3: Implement concept and occurrence loading**

Normalize all references to `book.chapter.verse` for the Bible and `surah:ayah` for the Quran. Use the naslag files to define and audit the entity universe, but count occurrences against the selected verses' original-language `grondtekst` tokens. A token matches only when its `lemma_strongs` or `strongs` value occurs in the concept's language-specific `source_ids`, or—where no stable source ID exists—its normalized `woord` occurs in `source_aliases`. Set:

- `entities = 1` for each controlled concept present in the selected scope;
- `verses = len(set(references))`;
- `mentions` to the number of matching ground tokens;
- `references` to the sorted unique verses containing at least one matching ground token;
- status `partial` with a source-coverage note when a selected verse lacks usable `grondtekst` or a concept lacks a required language mapping.

Do not infer cross-corpus equivalence from equal Dutch labels. Every included pairing must exist explicitly in `concepts.json`.

- [ ] **Step 4: Populate all first-version concepts**

Create entries for every controlled item currently present in either source under these category IDs:

```text
people, peoples, places, writings, materials, animals, plants,
food_drink, clothing_objects, nature, time_numbers_measures
```

Unpaired corpus-specific entities still receive a stable concept ID and appear with the other corpus as `not_comparable`; they are not discarded.

- [ ] **Step 5: Run concept and schema validation**

Run: `python -m pytest -q tests/test_corpusvergelijking_bible.py tests/test_corpusvergelijking_quran.py tests/test_corpusvergelijking_schema.py`

Expected: all tests pass; every concept ID is unique and every mapped reference resolves.

- [ ] **Step 6: Commit only Task 4 files**

```powershell
git add tools/corpusvergelijking/concepts.json tools/corpusvergelijking/bible_adapter.py tests/test_corpusvergelijking_bible.py tests/fixtures/corpusvergelijking/concepts-mini.json tests/fixtures/corpusvergelijking/naslag-materialen-mini.json
git commit -m "feat: normaliseer vergelijkbare corpusbegrippen"
```

---

### Task 5: Aggregate deterministic comparison output

**Files:**
- Create: `tools/corpusvergelijking/build.py`
- Create: `tools/corpusvergelijking/output/.gitkeep`
- Create: `tests/test_corpusvergelijking_build.py`

**Interfaces:**
- Consumes: `load_bible(...)`, `load_quran(...)`, `validate_result(...)`, and `concepts.json`.
- Produces: `rate_per_10000(value: int | None, word_count: int | None) -> float | None`.
- Produces: `build_comparison(root: Path) -> dict` with keys `schema_version`, `generated_at`, `default_scope`, `scopes`, `quran`, `comparisons`, and `methodology`.
- Produces: `write_comparison(output: Path, inputs: dict, generated_at: str) -> None`.
- CLI: `python tools/corpusvergelijking/build.py --generated-at 2026-09-05T00:00:00Z`.

- [ ] **Step 1: Write failing aggregation tests**

```python
# tests/test_corpusvergelijking_build.py
import json
from pathlib import Path
import pytest

from tools.corpusvergelijking.build import rate_per_10000, write_comparison
from tools.corpusvergelijking.schema import CorpusResult, Metric


def test_rate_per_10000_keeps_absolute_count_separate():
    assert rate_per_10000(25, 50000) == 5.0
    assert rate_per_10000(None, 50000) is None
    assert rate_per_10000(1, None) is None


@pytest.fixture
def fixture_inputs():
    def corpus(corpus_id, words):
        return CorpusResult(
            corpus_id=corpus_id,
            label=corpus_id,
            sources=[],
            units={"verses": Metric(2, "complete")},
            words=Metric(words, "complete"),
            unique_words=Metric(words, "complete"),
            categories={},
            warnings=[],
        )
    return {
        "scopes": {
            "canon": corpus("bible-canon", 5),
            "canon_apocrypha": corpus("bible-canon-apocrypha", 7),
            "complete": corpus("bible-complete", 9),
        },
        "quran": corpus("quran", 6),
    }


def test_build_is_byte_deterministic(tmp_path, fixture_inputs):
    first = tmp_path / "first.json"
    second = tmp_path / "second.json"
    write_comparison(first, fixture_inputs, generated_at="2026-09-05T00:00:00Z")
    write_comparison(second, fixture_inputs, generated_at="2026-09-05T00:00:00Z")
    assert first.read_bytes() == second.read_bytes()


def test_output_contains_all_three_bible_scopes(tmp_path, fixture_inputs):
    output = tmp_path / "comparison.json"
    write_comparison(output, fixture_inputs, generated_at="2026-09-05T00:00:00Z")
    data = json.loads(output.read_text(encoding="utf-8"))
    assert data["default_scope"] == "canon"
    assert set(data["scopes"]) == {"canon", "canon_apocrypha", "complete"}
```

- [ ] **Step 2: Run the build tests and verify failure**

Run: `python -m pytest -q tests/test_corpusvergelijking_build.py`

Expected: collection fails because `build.py` does not exist.

- [ ] **Step 3: Implement aggregation and deterministic writing**

Serialize with:

```python
json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
```

Sort categories by the fixed category order from Task 4, entities by descending mentions and then `concept_id`, sources by `id`, warnings lexicographically, and references by numeric canonical order. `rate_per_10000` returns `round(value / word_count * 10000, 2)` only when both operands are usable and `word_count > 0`.

For each category and scope emit:

```json
{
  "category": "materials",
  "bible": {"entities": 59, "verses": 0, "mentions": 0, "per_10000": 0.0, "status": "controlled_catalog"},
  "quran": {"entities": 8, "verses": 48, "mentions": 58, "per_10000": 0.0, "status": "controlled_catalog"},
  "shared_concepts": 5
}
```

The displayed example values must be replaced by computed values. If a count is unavailable, serialize `null`, not zero.

- [ ] **Step 4: Run build tests and generate the real output**

Run: `python -m pytest -q tests/test_corpusvergelijking_build.py`

Run: `python tools/corpusvergelijking/build.py --generated-at 2026-09-05T00:00:00Z`

Expected: tests pass and `tools/corpusvergelijking/output/corpusvergelijking.json` is written.

- [ ] **Step 5: Validate real output determinism**

Run the build twice with the same `--generated-at`, compute SHA-256 after each run, and assert equality in `test_real_output_is_current_and_deterministic`. Also assert that every non-null normalized value matches its absolute count and corresponding word count.

Run: `python -m pytest -q tests/test_corpusvergelijking_build.py`

Expected: all tests pass.

- [ ] **Step 6: Commit only Task 5 files**

```powershell
git add tools/corpusvergelijking/build.py tools/corpusvergelijking/output tests/test_corpusvergelijking_build.py
git commit -m "feat: bouw reproduceerbare corpusvergelijking"
```

---

### Task 6: Build the local comparison dashboard

**Files:**
- Create: `tools/corpusvergelijking/index.html`
- Create: `tools/corpusvergelijking/app.js`
- Create: `tools/corpusvergelijking/style.css`
- Modify: `tests/test_corpusvergelijking_ui.py`

**Interfaces:**
- Consumes: `output/corpusvergelijking.json` from Task 5.
- Produces: `renderDashboard(data: ComparisonData, scope: string)`, `renderCategoryTable(category)`, and `formatMetric(metric)` in `app.js`.
- UI storage key: `ov-corpusvergelijking-scope` with values `canon`, `canon_apocrypha`, or `complete`.

- [ ] **Step 1: Write failing static UI contract tests**

```python
def test_dashboard_has_accessible_scope_control_and_methodology():
    html = (ROOT / "tools/corpusvergelijking/index.html").read_text(encoding="utf-8")
    assert 'id="bible-scope"' in html
    assert '<option value="canon" selected>' in html
    assert '<option value="canon_apocrypha">' in html
    assert '<option value="complete">' in html
    assert '<details id="methodology">' in html
    assert 'aria-live="polite"' in html


def test_dashboard_loads_only_local_generated_data():
    js = (ROOT / "tools/corpusvergelijking/app.js").read_text(encoding="utf-8")
    assert "output/corpusvergelijking.json" in js
    assert "openkoran.nl" not in js
    assert "fetch(" in js


def test_dashboard_labels_all_coverage_states():
    js = (ROOT / "tools/corpusvergelijking/app.js").read_text(encoding="utf-8")
    for status in ("complete", "controlled_catalog", "partial", "not_comparable"):
        assert status in js
```

- [ ] **Step 2: Run the UI tests and verify failure**

Run: `python -m pytest -q tests/test_corpusvergelijking_ui.py`

Expected: fails because the dashboard files do not exist.

- [ ] **Step 3: Implement semantic HTML and data-state handling**

The page must contain:

- one `h1` with “Bijbel en Koran in cijfers”;
- a labeled Bible-scope `select` defaulting to canonical;
- a source summary for both corpora;
- core statistic cards for units, verses, word tokens, and unique word forms;
- category comparison bars showing absolute values and per-10,000 values side by side;
- tables with explicit columns `Entiteiten`, `Verzen`, `Vermeldingen`, and `Per 10.000 woorden`;
- visible status badges and warning text;
- a `<details id="methodology">` section reproducing the definitions from the spec;
- an error panel for missing or invalid JSON.

Use `textContent` for imported labels and notes; do not inject source strings via `innerHTML`.

- [ ] **Step 4: Implement responsive visual design**

Use a two-column comparison at desktop width and a single-column layout below `760px`. Give Bible and Quran consistent, distinguishable colors; encode status with text and icon as well as color. Keep tables horizontally scrollable on small screens. Honor `prefers-reduced-motion` and `prefers-color-scheme`; all controls must have visible keyboard focus.

- [ ] **Step 5: Run UI tests and serve locally**

Run: `python -m pytest -q tests/test_corpusvergelijking_ui.py`

Run from repository root: `python -m http.server 65436`

Open locally: `http://127.0.0.1:65436/tools/corpusvergelijking/`

Expected: canonical scope is selected, switching scope updates every Bible metric without reloading, incomplete metrics show warnings, no external request appears, and the page remains usable at 390px and 1440px widths.

- [ ] **Step 6: Commit only Task 6 files**

```powershell
git add tools/corpusvergelijking/index.html tools/corpusvergelijking/app.js tools/corpusvergelijking/style.css tests/test_corpusvergelijking_ui.py
git commit -m "feat: toon lokale Bijbel-Koran-vergelijking"
```

---

### Task 7: Document sources, run the release gate, and verify local isolation

**Files:**
- Create: `tools/corpusvergelijking/README.md`
- Modify: `tests/test_corpusvergelijking_ui.py`
- Modify: `tests/test_corpusvergelijking_build.py`

**Interfaces:**
- Consumes: all earlier tasks.
- Produces: one documented command sequence for refreshing sources, rebuilding, testing, and locally opening the dashboard.

- [ ] **Step 1: Add failing documentation and isolation tests**

```python
def test_readme_documents_sources_metrics_and_refresh_commands():
    readme = (ROOT / "tools/corpusvergelijking/README.md").read_text(encoding="utf-8")
    for required in (
        "Tanzil Uthmani",
        "Open Koran Weergave",
        "orthografische woordtokens",
        "gecontroleerde catalogus",
        "python tools/corpusvergelijking/build.py",
        "python -m http.server 65436",
    ):
        assert required in readme


def test_no_public_file_references_local_tool():
    forbidden = [ROOT / "wiki.html", ROOT / "sitemap.xml", ROOT / "sw.js", ROOT / "downloads.html"]
    assert all("corpusvergelijking" not in path.read_text(encoding="utf-8").lower() for path in forbidden)
```

- [ ] **Step 2: Run the tests and verify failure**

Run: `python -m pytest -q tests/test_corpusvergelijking_ui.py -k 'readme or public'`

Expected: README test fails because the file does not exist.

- [ ] **Step 3: Write the README**

Document:

1. the three Bible scopes and canonical default;
2. every source path used by the Bible adapter;
3. Open Koran v0.11 and Tanzil Uthmani attribution from the snapshot manifest;
4. exact definitions of entity, verse, mention, token, and unique normalized word form;
5. why Arabic and Hebrew clitics make word counts source-bound rather than absolute linguistic facts;
6. all four coverage states;
7. how to refresh the structured Open Koran export, update manifest checksums, build output, run tests, and serve locally;
8. the rule that the tool is not a theological verdict and must remain excluded from production unless separately approved.

- [ ] **Step 4: Run the complete focused test suite**

Run:

```powershell
python -m pytest -q tests/test_corpusvergelijking_schema.py tests/test_corpusvergelijking_bible.py tests/test_corpusvergelijking_quran.py tests/test_corpusvergelijking_build.py tests/test_corpusvergelijking_ui.py
```

Expected: all tests pass.

- [ ] **Step 5: Rebuild and verify the generated artifact**

Run:

```powershell
python tools/corpusvergelijking/build.py --generated-at 2026-09-05T00:00:00Z
python -m pytest -q tests/test_corpusvergelijking_build.py tests/test_corpusvergelijking_ui.py
git diff --check -- tools/corpusvergelijking tests/test_corpusvergelijking_*.py .github/workflows/deploy.yml
```

Expected: rebuild succeeds, tests pass, and `git diff --check` emits no output.

- [ ] **Step 6: Visually verify the local dashboard**

Serve on port 65436 and inspect canonical, canon-plus-apocrypha, and complete scopes at desktop and mobile widths. Confirm that status badges, null metrics, source/version information, category tables, and normalized rates visibly update. Confirm through browser network inspection that the page requests only local files.

- [ ] **Step 7: Commit only Task 7 files**

```powershell
git add tools/corpusvergelijking/README.md tests/test_corpusvergelijking_ui.py tests/test_corpusvergelijking_build.py tools/corpusvergelijking/output/corpusvergelijking.json
git commit -m "docs: verantwoord lokale corpusvergelijking"
```

- [ ] **Step 8: Final repository audit without touching unrelated work**

Run:

```powershell
git status --short
git log -7 --oneline
```

Expected: the seven task commits are present; any pre-existing unrelated modifications remain untouched and uncommitted. Do not push or merge unless the user separately asks for it.
