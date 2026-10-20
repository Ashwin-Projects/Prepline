# Scoring Correctness (v1.1) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix ten scoring-correctness, security, performance and housekeeping issues on local branch `fix/scoring-correctness`, then publish `results/amazon_sde1_v1.1.json` with a per-item change log.

**Architecture:** A single frozen config file (`config/scoring_v1.0.json`, loaded once by `pipeline/config.py`) becomes the source of every constant. The syllabus side is segmented into courses, then modules, before mapping. Syllabus units match only `high_level_concept` nodes, and granular skills inherit their coverage from them. The interview side filters questions before computing I(t), and the filtered report count drives both the density gate and the I(t) denominator.

**Tech Stack:** Python 3.13, pdfplumber 0.11.10, sentence-transformers 6.0.1 (all-MiniLM-L6-v2), rake-nltk 1.0.6 / nltk 3.9.1, FastAPI 0.136.1, pydantic v2, pytest 9.0.3.

**Spec:** the user's 10-item request of 2026-10-21 (in the session), plus the approved test decisions:
- The course allowlist is config-driven and passed in; tests supply their own allowlist containing CSE2001, and no test course enters the real config.
- `test_bst_syllabus_unit_maps_to_taxonomy_presence` is rewritten to assert the BST's high-level parent, and a new test asserts `dsa.trees.bst` has `coverage_source == "inherited"`.

CLAUDE.md "Skills policy" applies throughout.

## Global Constraints

- Branch `fix/scoring-correctness` created locally from `main` (`48d05a7`). **Never** run `git push`, `git merge`, `git fetch`/`pull`, or anything that touches the remote.
- **FROZEN:** τ = 0.50, γ = 0.5, depth reference values `{unit_hours: 10, slide_count: 20, slides: 20, lab_hours: 10, lab_count: 5, assignment_count: 5, assignments: 5}`, MIN_REPORTS = 15, taxonomy v1.0 contents. The semester-weeks conversion (×15) is also kept.
- One commit per item; failing test written and seen failing before the implementation (TDD Guard on). No Co-Authored-By trailer.
- Check Context7 before using sentence-transformers, pdfplumber, FastAPI or NLTK APIs (noted per step).
- Never overwrite an existing `results/*.json`. `results/amazon_sde1_v1.0.json` stays byte-identical.
- Tests never write into `data/processed/`; every writer takes a path, and tests pass `tmp_path`.
- Pipeline runs log stage timings and counts.

## Facts established during planning

- **PDF:** 213 pages, **67 with no text layer** (pages 15–18, 20–21, 30–32, 35–63, 152–160, 162–171, 174–183). Text extraction alone takes 412 s.
- **Courses:** 66 course headers are detectable, with no duplicates. Of the 26 courses in the D4 list, **only 3 have extractable syllabi**: BCSE203E Web Programming, BCSE102P Structured and OOP Lab, BMAT205L Discrete Mathematics and Graph Theory. The Discipline Core block (DSA, DAA, OS, DBMS, CN, …) sits on image-only pages 35–63, and the core titles appear only in the page-7 catalogue table. The other 63 detectable courses are electives and ECE courses (data science, IoT, security, blockchain, digital systems, microprocessors, …). The v1.0 S_comp of 51.54 is built mostly on those.
- **Interviews:** 98 question rows. The item 3 filter excludes 23 behavioral, 20 needs_review and 9 with no question_text, leaving 46 included rows across **18 reports** (gate passes, 18 ≥ 15).
- **Taxonomy:** 37 high_level_concept and 46 granular_skill nodes. Every granular node's direct parent is high-level, so the item 2 verification reports **0 orphans**.
- **Model:** the locally cached all-MiniLM-L6-v2 snapshot is revision `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`.

## Decisions (approved by the user 2026-10-21)

- **D1:** Rewrite the 5 `TestPhase9Scoring` expectations to the granular node (Task 6).
- **D2:** `test_pipeline_run_success` expects `report_count == 18`.
- **D3:** The importance cache key includes the SHA-256 of `questions.csv`.
- **D4 = (a):** Apply the core allowlist (21 Discipline Core + BCSE101E/102L/102P/103E + BMAT205L).
  - **Per-page text-layer detection:** the result JSON records which pages have no text layer and which courses were skipped as scanned, and lists `allowlisted_missing`.
  - **CHANGES_v1.1.md must state** that v1.0's S_comp was driven by non-core courses, and that v1.1 covers only 3 core courses because of scanning.
  - The user will supply text-layer or offline-OCR'd PDFs later, as a separate step.
- **D5:** Use the execution order below.
- **TDD Guard: skipped.** Tests-first is kept through Superpowers TDD.
- **Orphan granular nodes:** fall back to direct coverage **and log a warning** (`logging.warning`, naming the topic ids).
- **Execution:** native. The plan file is the first commit on the branch.

## Execution order (one commit each)

Config comes first, because items 1, 2, 4 and 5 add keys to it and item 8's cache is keyed on its version. The output-neutral items (8, 7, 10) come next. Then the five scoring-changing items run one at a time, each followed by a full pipeline run, so CHANGES_v1.1.md can attribute every S_comp and gap movement to one item.

| Task | Item | Changes outputs? | Full run after? |
|---|---|---|---|
| 0 | baseline | – | yes: must reproduce S_comp 51.538 on current `main` |
| 1 | 6 config | no | no (tests prove identical values) |
| 2 | 8 performance | no | yes: must still equal 51.538, and records the speed-up |
| 3 | 7 security | no | no |
| 4 | 10 housekeeping | no | no |
| 5 | 3 interview filtering | yes | run A |
| 6 | 2 node-type matching | yes | run B |
| 7 | 1 course segmentation | yes | run C |
| 8 | 4 depth signals | yes | run D |
| 9 | 5 boilerplate stoplist | yes | run E (= v1.1) |
| 10 | 9 results v1.1 + CHANGES | – | final file from run E's code |
| 11 | pre-merge checks (policy) | – | report only |

Attribution is sequential in this order, and CHANGES_v1.1.md says so. Intermediate run JSONs stay in the scratchpad, uncommitted; their numbers are copied into CHANGES_v1.1.md. One run is about 15–18 min, so runs go in the background. That's 7 runs, roughly 2 h of background time in total.

## File structure

| File | Responsibility |
|---|---|
| `config/scoring_v1.0.json` (new) | All frozen numbers, rules, allowlist, stoplist |
| `pipeline/config.py` (new) | `load_scoring_config(path=None) -> dict` (cached), `CONFIG_PATH` |
| `pipeline/taxonomy_tree.py` (new) | Ancestor walk + orphan verification |
| `pipeline/interview_parser.py` (currently a 4-line stub) | Question filtering, excluded-CSV writer, report counting |
| `pipeline/syllabus_parser.py` | Course segmentation, module parsing, depth signals, allowlist filter |
| `pipeline/keyword_abstraction.py` | Boilerplate stripping before RAKE |
| `pipeline/embeddings.py` | Node-type filter, batch encoding, pinned model revision |
| `pipeline/taxonomy_mapper.py` | Passes the node type derived from source_type |
| `pipeline/scoring.py` | Coverage inheritance, derived report count, importance cache |
| `backend/routes.py`, `backend/schemas.py` | Filename sanitising, config-driven versions, allowlist dependency, v2 `Field` usage |
| `evaluation/run_full_pipeline.py` | v1.1 output, no-overwrite guard, stage timings/counts |
| `evaluation/compare_results.py` (new) | Builds the v1.0-vs-v1.1 tables for CHANGES_v1.1.md |
| New tests | `test_config.py`, `test_performance.py`, `test_upload_security.py`, `test_schemas.py`, `test_interview_filter.py`, `test_node_type_matching.py`, `test_syllabus_segmentation.py`, `test_boilerplate.py`, `test_run_full_pipeline.py` |

## Review Focus

1. **A PDF with no detectable course header** (any non-VIT upload) → `UnsupportedPDFError("no course headers found")`, and the API returns 400, never a silent 0-unit result. Test in Task 7.
2. **An allowlist that keeps nothing** → `NoCoreCoursesError` (a `ValueError`), and the API returns 400 listing the dropped codes. Test in Task 7.
3. **The same course code printed twice in one PDF** → the second copy is dropped with reason `"duplicate"`, and `source_id`s stay unique. Test in Task 7.
4. **An upload filename that sanitises to nothing or loses `.pdf`** (`"../.pdf"`, `"..\\..\\"`) → falls back to `upload.pdf` inside the temp dir. Test in Task 3.
5. **Filtering that leaves fewer than 15 reports** → `INSUFFICIENT_DATA` from both the API and `run_full_pipeline`, and I(t) is never computed with a 0 denominator. Test in Task 5.

---

### Task 0: Branch + baseline reproduction

- [ ] `git switch -c fix/scoring-correctness main`; `git status` is clean apart from this untracked plan.
- [ ] Commit this plan file as the first commit (`Add v1.1 scoring-correctness plan`). TDD Guard is skipped per the user.
- [ ] `python -m pytest evaluation -q -p no:cacheprovider` → `64 passed`.
- [ ] Background: `python evaluation/run_full_pipeline.py --pdf "data/raw/syllabi/B.Tech_CSE_2024_2025(1) (1).pdf" --out <scratchpad>/run_baseline.json`. The result must match S_comp 51.538 and the top-10 gaps of `results/amazon_sde1_v1.0.json`. If it differs, **stop and report** environment drift before changing any code.

### Task 1: Central config (item 6)

**Files:** Create `config/scoring_v1.0.json`, `pipeline/config.py`, `evaluation/test_config.py`. Modify `pipeline/scoring.py`, `pipeline/embeddings.py`, `pipeline/keyword_abstraction.py`, `backend/routes.py`, `evaluation/run_full_pipeline.py`.

**Interfaces:**
- Produces: `pipeline.config.load_scoring_config(path: Optional[str] = None) -> dict`. It reads the file once per path and returns the same dict object afterwards. `pipeline.config.CONFIG_PATH`.
- Keys added now: `config_version: "v1.0"`, `taxonomy_version: "v1.0"`, `taxonomy_path: "data/taxonomy/taxonomy_v1.0.json"`, `similarity_threshold: 0.50`, `gamma: 0.5`, `depth_reference_values` (the 7 keys above), `semester_weeks: 15`, `min_reports: 15`, `embedding_model: {"name": "all-MiniLM-L6-v2", "revision": "1110a243fdf4706b3f48f1d95db1a4f5529b4d41"}`. Later tasks add `interview_filter`, `node_type_rule`, `coverage_inheritance`, `syllabus.core_courses` and `syllabus.boilerplate_stoplist`.
- These public names stay importable and are now sourced from the config: `scoring.GAMMA_DEFAULT`, `scoring.MVP_REFERENCE_VALUES`, `scoring.MIN_REPORTS`, `scoring.DEFAULT_TAXONOMY_VERSION`, `embeddings.SIMILARITY_THRESHOLD`, `keyword_abstraction.DEFAULT_TAXONOMY_VERSION`.
- Removed: `routes.MIN_REPORTS_REQUIRED`, `run_full_pipeline.MIN_REPORTS` and `SCORING_CONFIG_VERSION`, and every `"v1.0"` literal in `routes.py`, `run_full_pipeline.py` and `scoring.py`.

- [ ] **Tests** (`test_config.py`):
  - `test_frozen_values`: `similarity_threshold == 0.50`, `gamma == 0.5`, `min_reports == 15`, `taxonomy_version == "v1.0"`, `semester_weeks == 15`, and the reference-values dict equals the literal above. This is the Constraint-Driven freeze guard.
  - `test_loaded_once`: `load_scoring_config() is load_scoring_config()`.
  - `test_module_constants_come_from_config`: each re-exported constant equals its config value.
  - `test_no_hardcoded_versions`: the regex `"v1\.0"` finds 0 hits in the source of those three files.
- [ ] Run → FAIL (`ModuleNotFoundError: pipeline.config`).
- [ ] Implement. Context7: `SentenceTransformer(..., revision=...)` in sentence-transformers 6.0.1.
- [ ] `pytest evaluation -q` → all pass. Commit `Centralise scoring constants in config/scoring_v1.0.json`.

### Task 2: Batch encoding + importance cache (item 8)

**Files:** Modify `pipeline/embeddings.py`, `pipeline/scoring.py`, `backend/routes.py`. Create `evaluation/test_performance.py`.

**Interfaces:**
- `embeddings.match_concepts_to_taxonomy(concepts, threshold=SIMILARITY_THRESHOLD)`:
  - It makes **one** `model.encode(concepts, convert_to_tensor=True)` call, then one `util.cos_sim(matrix, taxonomy_embeddings)`.
  - The return type, tie-breaks and unmapped list are unchanged. `_match_single_concept` is deleted.
- `scoring.get_interview_importance(company: str, role: str, questions_csv: str, total_reports_count: Optional[int] = None) -> dict` is memoised on `(company, role, taxonomy_version, config_version[, questions_sha256 if D3])`.
- `scoring.clear_importance_cache() -> None`. `routes.run_pipeline` uses `get_interview_importance`.
- [ ] **Tests:**
  - `test_batch_matches_equal_per_concept`: concepts `"binary search tree"`, `"deadlock"`, `"rate limiting"`, `"sql joins"`, `"leetcode"`, `"hash map"`. The matched ids must equal a reference built in the test by encoding each concept alone, and the scores must agree within `1e-5`.
  - `test_single_encode_call_per_source`: spy on `encode`; 6 concepts → `call_count == 1`.
  - `test_importance_cache_hit`: spy on `map_source_to_taxonomy`. A second identical call makes 0 new calls; after `clear_importance_cache()` it recomputes.
  - `test_cache_key_varies_by_role`.
- [ ] Run → FAIL. Implement (Context7: `encode` batching, `util.cos_sim`). Tests pass.
- [ ] Background full run → S_comp **must equal 51.538** with the same top-10. Record `runtime_seconds` against the baseline.
- [ ] Commit `Batch-encode concepts and cache interview importance`.

### Task 3: Upload filename sanitising + Claude Security on backend/ (item 7)

**Files:** Modify `backend/routes.py`. Create `evaluation/test_upload_security.py`.

**Interfaces:** `routes.safe_upload_filename(name: Optional[str]) -> str`:
- It turns `\` into `/`, then applies `os.path.basename`.
- It replaces every char outside `[A-Za-z0-9._-]` with `_` and strips leading dots.
- An empty result, or one not ending in `.pdf` (case-insensitive), becomes `"upload.pdf"`.
- It's used for `temp_path`, `syllabus_id` and the response `filename`. The `.pdf` check still runs on the raw name first.
- [ ] **Tests:**
  - `test_safe_upload_filename` (parametrised): `"../../evil.pdf"→"evil.pdf"`, `"..\\..\\evil.pdf"→"evil.pdf"`, `"my syllabus (1).pdf"→"my_syllabus__1_.pdf"`, `"../.pdf"→"upload.pdf"`, `"..\\..\\"→"upload.pdf"`, `None→"upload.pdf"`.
  - `test_upload_with_traversal_filename_stays_in_tempdir`: spy-wrap `routes.parse_syllabus_pdf`, POST `"../../evil.pdf"`, then assert 201, `os.path.basename(path) == "evil.pdf"`, `".." not in path`, and response `filename == "evil.pdf"`.
- [ ] Run → FAIL. Implement (Context7: FastAPI `UploadFile`). Pass.
- [ ] Dispatch the `claude-security:claude-security` agent scoped to `backend/`. Only the filename issue gets fixed in this commit. Everything else is reported to you, unfixed.
- [ ] Commit `Sanitise uploaded syllabus filenames`.

### Task 4: Pydantic v2 + requirements (item 10)

**Files:** Modify `backend/schemas.py`, `requirements.txt`. Create `evaluation/test_schemas.py`.

- [ ] **Test** `test_schemas_emit_no_pydantic_deprecations`: inside `warnings.catch_warnings(record=True)` with `simplefilter("always")`, `importlib.reload(backend.schemas)` records no `PydanticDeprecatedSince20`.
- [ ] Run → FAIL (6 warnings).
- [ ] Replace `Field(..., example=X)` with `Field(..., examples=[X])`. `model_config = ConfigDict(...)` is only needed for model-level settings (none today), and there are no validators to migrate.
- [ ] Move `pytest==9.0.3` under `# test` (CRLF kept).
- [ ] `pytest evaluation -q -W error::pydantic.warnings.PydanticDeprecatedSince20` → pass. Commit `Use pydantic v2 Field examples; group pytest under test deps`.

### Task 5: Interview filtering (item 3)

**Files:** Modify `pipeline/interview_parser.py`, `pipeline/scoring.py`, `backend/routes.py`, `evaluation/run_full_pipeline.py`, `config/scoring_v1.0.json`, `evaluation/test_backend_api.py` (D2). Create `evaluation/test_interview_filter.py`, `data/processed/excluded_questions.csv` (generated).

**Interfaces:**
- Config: `interview_filter: {"exclude_round_types": ["behavioral"], "exclude_needs_review": true, "require_question_text": true}`.
- `interview_parser.filter_questions(rows: List[dict]) -> Tuple[List[dict], List[dict]]` returns `(included, excluded)`:
  - Each excluded row is a copy carrying `exclusion_reason`: all matching reasons, `;`-joined, in the order `behavioral_round;needs_review;no_question_text`.
  - Empty means `""`, `"nan"` (case-insensitive) or `None`.
  - `needs_review` is true for `True` or `"true"`/`"1"`/`"yes"`.
  - A missing column means not excluded.
- `interview_parser.write_excluded_questions(excluded: List[dict], path: str) -> None` writes the original columns plus `exclusion_reason`.
- `interview_parser.count_reports(rows: List[dict]) -> int` counts distinct non-empty `report_id`s.
- `scoring.calculate_topic_importance(questions_input, total_reports_count: Optional[int] = None, taxonomy_nodes=...)`:
  - The default of `21` is removed, and the function applies `filter_questions`.
  - When `total_reports_count` is None, it uses `count_reports(included)`.
  - The fallback from `question_text` to the `topic` column is removed.
  - The result adds `questions_included` and `questions_excluded` counts.
- `routes` and `run_full_pipeline` compute `report_count = count_reports(included)` once and pass the same value to the gate and to I(t).
- Deleted: `routes._get_report_count` and `run_full_pipeline.count_reports`.
- `run_full_pipeline` writes `data/processed/excluded_questions.csv` (path overridable) and prints counts per reason.
- [ ] **Tests:**
  - Filter rules: `test_behavioral_excluded`, `test_needs_review_string_and_bool`, `test_nan_question_text_excluded`, `test_multiple_reasons_joined` (→ `"behavioral_round;needs_review"`), `test_missing_columns_included`.
  - `test_write_excluded_questions`: tmp_path; the header ends with `exclusion_reason`.
  - `test_real_dataset_counts`: 46 included, 52 excluded, `count_reports(included) == 18`.
  - `test_importance_denominator_defaults_to_included_reports`: 2 reports, one all-behavioral → denominator 1.
  - `test_topic_only_rows_contribute_nothing`.
  - `test_density_gate_below_15_after_filtering` (Review Focus 5): a fixture CSV that leaves 14 reports → `"INSUFFICIENT_DATA"` (patch `routes.QUESTIONS_CSV_PATH`).
  - D2: 21 → 18.
- [ ] Run → FAIL. Implement. Pass. Background run → **run A**. Commit `Filter interview questions before scoring; derive report count`, with `excluded_questions.csv`.

### Task 6: Node-type matching + coverage inheritance (item 2)

**Files:** Create `pipeline/taxonomy_tree.py`, `evaluation/test_node_type_matching.py`. Modify `pipeline/embeddings.py`, `pipeline/taxonomy_mapper.py`, `pipeline/scoring.py`, `backend/schemas.py`, `config/scoring_v1.0.json`, `evaluation/test_syllabus_parser.py` (approved), `evaluation/test_scoring.py` (D1).

**Interfaces:**
- Config: `node_type_rule: {"syllabus": "high_level_concept", "interview": "granular_skill"}`, `coverage_inheritance: {"granular_skill": "nearest_high_level_ancestor"}`.
- `taxonomy_tree.nearest_high_level_ancestor(topic_id: str, nodes_by_id: Dict[str, dict]) -> Optional[str]` walks `parent_id` and is cycle-safe.
- `taxonomy_tree.find_granular_without_high_level_ancestor(nodes: List[dict]) -> List[str]` returns sorted ids.
- `embeddings.match_concepts_to_taxonomy(..., node_type: Optional[str] = None)` scores only nodes of that type, by filtering the cached embedding rows by index. A concept matching no allowed node counts as unmapped.
- `taxonomy_mapper.map_source_to_taxonomy` passes `node_type=config["node_type_rule"].get(source_type)`.
- `scoring.calculate_syllabus_coverage`:
  - High-level nodes are computed as now, with `coverage_source: "direct"`.
  - Each granular node with a high-level ancestor copies that ancestor's `presence`, `depth`, `coverage`, `depth_status` and `depth_signal_count`, plus `coverage_source: "inherited"` and `inherited_from`.
  - A granular node with **no** ancestor in the supplied nodes (only the existing Phase 8 mock fixtures, which have no `parent_id`) keeps direct computation, so those tests stay untouched. It also emits **one `logging.warning`** listing the orphan ids. Test: `test_orphan_falls_back_with_warning` (`caplog`).
- `schemas.TopicCoverageItem` gains `coverage_source: str = "direct"` and `inherited_from: Optional[str] = None`.
- `run_full_pipeline` prints and stores `granular_without_high_level_ancestor` (expected `[]`).
- [ ] **Tests:**
  - Ancestry: `test_real_taxonomy_has_no_orphans`, `test_orphan_detected`, `test_nearest_ancestor_skips_granular_parent`.
  - Matching: `test_match_filters_high_level`, `test_match_filters_granular` (concept `"binary search tree insertion"`; every returned id has the requested type), `test_node_type_none_unchanged`, `test_syllabus_source_matches_only_high_level`, `test_interview_source_matches_only_granular`.
  - Inheritance: `test_granular_inherits_parent_coverage` (syllabus matches `dsa.trees` → `dsa.trees.bst` has equal coverage, `"inherited"`, `inherited_from == "dsa.trees"`).
  - Approved BST changes: the BST test asserts `"dsa.trees" in matched_topic_ids`, and new `test_bst_gets_inherited_coverage` asserts presence 1 and `"inherited"`.
  - D1: rewrite `TestPhase9Scoring` expectations to the question's granular match (`os.deadlocks.prevention_avoidance`, credit 1.0 if it is the only granular match). The 60/40 test uses a question probed during implementation to match ≥2 granular nodes, recorded in the test, asserting 0.6/21 and 0.4/(k−1)/21.
- [ ] Run → FAIL. Implement. Pass. Background run → **run B**. Commit `Match syllabus to high-level and interviews to granular nodes; inherit coverage`.

### Task 7: Course segmentation + core-course allowlist (item 1)

**Files:** Modify `pipeline/syllabus_parser.py`, `backend/routes.py`, `evaluation/run_full_pipeline.py`, `config/scoring_v1.0.json`, `evaluation/test_syllabus_parser.py`, `evaluation/test_backend_api.py`. Create `evaluation/test_syllabus_segmentation.py`.

**Observed layout (real PDF):**
- **Course headers** come in two forms: `^BECE102L Digital Systems Design 3 0 0 3`, or `^BMAT205L Discrete Mathematics and Graph Theory L T P C` with `3 1 0 4` on the next line.
- **L-T-P-C (4 numbers)** is used throughout this PDF; L-T-P-J-C (5) must also parse.
- **Modules:** `Module:1 Digital Logic 8 hours` (also `6hours`).
- **Course boundary:** a course ends at the next header.
- **Module boundary:** a module ends at the next module, or at the first terminator line: `Total Lecture hours`, `Total Laboratory Hours`, `Text Book`, `Reference Book`, `Mode of Evaluation`, `Recommended by`, `Approved by`.
- **Catalogue rows** (pages 6–14) start with a serial number and must not match.
- **Test-fixture labelled format** (`Course Code: CSE2001` / `Course Title: …` / `L T P J C : 3 0 2 0 4`) must also be detected.

**Interfaces:**
- Config: `syllabus.core_courses: [D4 list]`. No test courses.
- `syllabus_parser.segment_courses(full_text: str) -> List[dict]`. Keys: `course_code`, `course_title`, `lecture_hours`, `tutorial_hours`, `practical_hours`, `project_hours` (None for 4-number LTPC), `credits`, `text`.
- `syllabus_parser.filter_core_courses(courses, allowlist: Iterable[str]) -> Tuple[List[dict], List[dict]]`. Dropped dicts add `drop_reason` (`"not_in_allowlist"` | `"duplicate"`).
- `syllabus_parser.parse_course_modules(course: dict) -> List[dict]`. The module keys are unchanged, plus `course_code`. A course with no `Module:` headers (labs) yields one unit with `module_number: 0`.
- `class NoCoreCoursesError(ValueError)`.
- `parse_syllabus_pdf(pdf_path, taxonomy_version=..., core_courses: Optional[Iterable[str]] = None)`:
  - None means the config allowlist.
  - It raises `UnsupportedPDFError` when no header is found, and `NoCoreCoursesError` when none is kept.
  - It adds `courses`, `course_filter: {"kept": [codes], "dropped": [{course_code, course_title, drop_reason}], "allowlisted_missing": [codes]}`, and `text_layer: {"page_count": int, "pages_without_text": [1-based page numbers], "scanned_courses": [codes]}`.
  - `scanned_courses` are allowlisted codes that appear in the PDF's catalogue text but have no detectable syllabus header. This is the same set as `allowlisted_missing` when the catalogue lists them.
  - Per-page detection uses `syllabus_parser.page_has_text_layer(page_text: str) -> bool` (stripped length ≥ `MIN_TEXT_LENGTH_THRESHOLD`). Each page's text is extracted once and reused.
  - Tests: `test_text_layer_detection_per_page` (a reportlab PDF with one text page and one blank page → `pages_without_text == [2]`), `test_scanned_allowlisted_course_reported` (fixture text where the catalogue mentions CSE2002, which has no header → `"CSE2002"` in both `scanned_courses` and `allowlisted_missing`).
  - `course_metadata` becomes the first kept course (back-compat), and `source_id` keeps the format `f"{course_code}_mod_{n}"`.
  - `extract_course_metadata` stays as a wrapper over the header parser, so its existing test is unchanged.
- `routes.get_core_courses() -> List[str]` is a FastAPI dependency of `upload_syllabus`. `NoCoreCoursesError` → 400. Tests use `app.dependency_overrides[get_core_courses] = lambda: ["CSE2001"]`.
- `run_full_pipeline` prints the kept list, the dropped list (code, title, reason) and `allowlisted_missing`, and stores `course_filter`.
- [ ] **Tests** (text fixtures unless noted):
  - Header detection: `test_segments_inline_and_nextline_ltpc` (2 courses, correct numbers, `project_hours is None`), `test_ltpjc_five_numbers`, `test_catalogue_rows_not_courses`, `test_labelled_header_format`.
  - Module parsing: `test_module_bounded_by_terminators` (the last module excludes "Text Book(s)" and "Approved by Academic Council"; Course Objectives text is excluded), `test_lab_course_without_modules_single_unit`.
  - Allowlist: `test_filter_core_courses`, `test_duplicate_course_dropped` (RF 3), `test_allowlisted_missing_reported`.
  - Errors: `test_no_headers_raises_unsupported` (RF 1), `test_nothing_kept_raises`, `test_api_returns_400_when_no_core_courses` (RF 2).
  - `test_two_course_pdf_keeps_allowlisted_only` (reportlab PDF, allowlist `["CSE2001"]`).
  - Existing parser tests pass `core_courses=["CSE2001"]` / `["CSE2002"]`. Backend tests set the dependency override in `setUp` and clear it in `tearDown`.
- [ ] Run → FAIL. Implement (Context7: pdfplumber, only if a new call is used). Pass. Background run → **run C**. Commit `Segment syllabus into courses and keep core CS courses`.

### Task 8: Depth signals (item 4)

**Files:** Modify `pipeline/syllabus_parser.py`, `evaluation/run_full_pipeline.py`, `evaluation/test_syllabus_parser.py` (add tests only).

**Interfaces:** `extract_depth_signals(unit_text: str, course_metadata: dict, module_count: int = 1) -> dict`:
- `unit_hours` comes from the **header line only**, the first non-empty line of `unit_text`.
- `lab_hours = practical_hours * config["semester_weeks"] / module_count`. It's None when `practical_hours` is falsy.
- `parse_course_modules` passes that course's module count.
- `run_full_pipeline` prints measured/fallback counts for all topics and present topics, plus modules with ≥1 signal.
- [ ] **Tests:**
  - `test_unit_hours_header_only` (body says `"10 hours"`, header has none → None).
  - `test_unit_hours_no_space` (`"Module:5 Fundamentals of Graphs 6hours"` → 6).
  - `test_lab_hours_spread_across_modules` (P=2, 4 modules → 7.5 each, sum 30).
  - `test_zero_practical_hours_no_lab_signal`.
  - The existing `test_extract_depth_signals` stays green.
- [ ] Run → FAIL. Implement. Pass. Background run → **run D**. Commit `Spread practical hours across modules; read unit hours from module header`.

### Task 9: Boilerplate stoplist (item 5)

**Files:** Modify `pipeline/keyword_abstraction.py`, `config/scoring_v1.0.json`. Create `evaluation/test_boilerplate.py`.

**Interfaces:**
- Config `syllabus.boilerplate_stoplist`: `["module", "annexure", "approved", "academic council", "proceedings", "board of studies", "recommended by", "syllabus version", "pre-requisite", "course objectives", "course outcomes", "text book", "text books", "reference books", "mode of evaluation", "total lecture hours", "total laboratory hours", "hours", "item"]`. Built-in patterns for years `\b(19|20)\d{2}\b` and dates `\b\d{1,2}[./-]\d{1,2}[./-]\d{2,4}\b` are added on top. The list comes from the v1.0 run's top unmapped syllabus terms and is editable.
- `keyword_abstraction.strip_boilerplate(text: str, stoplist: Iterable[str]) -> str` removes whole-word, case-insensitive matches (longest phrase first) and replaces each with `" , "`, so RAKE never fuses neighbours.
- `two_pass_abstract` applies it before RAKE **only when `source_type == "syllabus"`**.
- [ ] **Tests:**
  - `test_removes_stoplist_phrases_case_insensitive`, `test_word_boundary_keeps_modular_arithmetic`, `test_removes_years_and_dates`.
  - `test_syllabus_concepts_exclude_boilerplate`: `"Approved by Academic Council No. 66 Date 16-06-2022. Module:1 Binary search trees"` → no concept contains `academic council`/`approved`/`2022`/`module`, and `"binary search trees"` remains.
  - `test_interview_text_untouched`.
- [ ] Run → FAIL. Implement. Pass. Background run → **run E**. Commit `Strip syllabus boilerplate before RAKE`.

### Task 10: Results v1.1 + CHANGES (item 9)

**Files:** Modify `evaluation/run_full_pipeline.py`. Create `evaluation/compare_results.py`, `evaluation/test_run_full_pipeline.py`, `results/amazon_sde1_v1.1.json`, `results/CHANGES_v1.1.md`.

**Interfaces:**
- `run_full_pipeline`: the default `--out` becomes `results/amazon_sde1_v1.1.json`. If `--out` exists it exits non-zero; there is no overwrite flag. The result adds `stage_timings_seconds: {parse, coverage, importance, scoring}`.
- `compare_results.build_changes(old: dict, new: dict, steps: List[Tuple[str, dict]]) -> str` returns Markdown. `steps` is the ordered (item label, run JSON) list for runs A–E.
- CHANGES_v1.1.md contents:
  - S_comp v1.0 → v1.1.
  - Top-10 gaps side by side.
  - Runtime v1.0 vs v1.1.
  - Per-item attribution: ΔS_comp, and gaps entering or leaving the top 10 at each step.
  - A note that attribution is sequential.
  - The D4 caveat, stated plainly: v1.0's S_comp was driven by non-core courses (electives and ECE courses with text layers), and v1.1 covers only the 3 core courses with readable syllabi because the Discipline Core pages are scanned. It lists `allowlisted_missing` and `pages_without_text`, and says text-layer or OCR'd PDFs will follow as a separate step.
- [ ] **Tests:** `test_refuses_to_overwrite_existing_results` (→ `SystemExit`, file unchanged), `test_build_changes_tables`.
- [ ] Run → FAIL. Implement. Pass.
- [ ] Run to `results/amazon_sde1_v1.1.json`; it must equal run E apart from `generated_at`/timings. Generate CHANGES. `git diff --stat results/amazon_sde1_v1.0.json` must be empty.
- [ ] Commit `Publish v1.1 results and change log`.

### Task 11: Pre-merge checks (policy)

- [ ] `pytest evaluation -q` → all pass, including in a fresh venv built from `requirements.txt`.
- [ ] Claude Security review of `main..fix/scoring-correctness` → reported to the user, nothing fixed without approval.
- [ ] Summary to user. **No merge, no push.**
