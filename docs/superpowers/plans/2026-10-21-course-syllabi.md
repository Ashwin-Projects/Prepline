# Course-syllabi combined run Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Score the 20 core course PDFs as one combined syllabus under config v1.2.

**Architecture:** Parser gains per-file reading + a multi-file entry point; lab-only courses split into
experiment units; scoring adds course-level signals once per (topic, course). Runner accepts many PDFs.

**Tech Stack:** Python 3.13, pdfplumber, pytest, FastAPI (unchanged API surface).

**Spec:** `docs/superpowers/specs/2026-10-21-course-syllabi-design.md`

## Global Constraints

- τ = 0.50, γ = 0.5, depth reference values, MIN_REPORTS = 15, semester_weeks = 15, taxonomy v1.0: unchanged.
- Never overwrite `results/*` or `config/scoring_v1.0.json` / `config/scoring_v1.1.json`.
- Local branch `data/course-syllabi` only; no push/merge.
- Header-line parsing stays token-based (no backtracking regexes; see `test_regex_safety.py`).

## Review Focus

- Topic matched by several experiments of one lab → `lab_count` enters its signals exactly once (Task 3 test).
- Experiment list with mixed `6.` / `6 ` numbering → all items counted (Task 2 test, BCSE204P layout).
- Wrapped experiment lines starting with a number that breaks the sequence → not a new experiment (Task 2 test).
- One unreadable file in a folder → recorded in `file_errors`, others still scored (Task 4 test).
- API upload → cached mappings keep `course_signals` (Task 3 test).

---

### Task 1: Config v1.2

**Files:** Create `config/scoring_v1.2.json`; Modify `pipeline/config.py`, `evaluation/test_config.py`.

- [ ] Test `test_code_points_at_v1_2_config` (basename `scoring_v1.2.json`, `config_version == "v1.2"`) and
  `test_v1_2_changes_only_core_courses` (v1.1 vs v1.2 differ only in `config_version`, `description`,
  `supersedes`, `syllabus.core_courses`, `syllabus.core_courses_source`; core_courses == the 20 codes).
- [ ] Run → FAIL. Create v1.2 file, point `CONFIG_PATH` at it. Run → PASS. Commit.

### Task 2: Parser fixes (extraction, running lines, incomplete L-T-P-C, experiments, empty modules)

**Files:** Modify `pipeline/syllabus_parser.py`; Test `evaluation/test_course_syllabi.py`.

**Produces:** `strip_running_lines(text) -> str`; `split_experiments(text) -> List[str]`;
course metadata key `ltpc_status`; module dicts gain `source_id`, `component`, `course_group`, `empty`,
lab units gain `course_signals`.

- [ ] Tests: running lines removed; `BCSE205L … L T P C` / `3 0` → recognised, all LTPJC `None`,
  `ltpc_status == "incomplete"`; BCSE204P-style list (1.–5. then `6 `–`11 `) → 11 experiments; a wrapped
  line starting `2nd Edition` inside item 3 is not an experiment; lab course → units `<code>_exp_1..n`,
  `lab_hours == 30 / n`, `depth_signals["lab_count"] is None`, `course_signals == {"lab_count": n}`;
  body-less Module 8 → `empty` and excluded; objectives text not in any experiment unit.
- [ ] Run → FAIL; implement; run new + existing parser tests → PASS. Commit.

### Task 3: Course-level signals in scoring + API cache

**Files:** Modify `pipeline/scoring.py`, `backend/routes.py`; Test `evaluation/test_course_syllabi.py`.

- [ ] Test `test_lab_count_counted_once_per_course`: three mappings of course `X` matching `t` each with
  `lab_hours 3`, `course_signals {"lab_count": 10}` → `depth_signal_count == 4` for `t`; a second course
  `Y` matching `t` adds one more lab_count signal. Test the cached mapping fields include `course_signals`.
- [ ] Run → FAIL; implement (dedupe key `(topic_id, course_code)`); run → PASS. Commit.

### Task 4: `parse_syllabus_pdfs` + collect helper

**Files:** Modify `pipeline/syllabus_parser.py`; Test `evaluation/test_course_syllabi.py` (reportlab PDFs).

**Produces:** `collect_syllabus_pdfs(folder: str, pattern: str = "BCSE*.pdf") -> List[str]`;
`parse_syllabus_pdfs(paths, syllabus_id, taxonomy_version=..., core_courses=None, max_pages=None) -> dict`.

- [ ] Tests: theory + lab PDFs → one result, `syllabus_id` as given, `source_files`, units tagged with
  `course_group`/`component`/`source_file`, unique source_ids, `course_groups` pairs L+P; an unreadable
  file → `file_errors`, rest kept; all unreadable/none core → raises; glob excludes non-matching PDFs.
- [ ] Run → FAIL; implement sharing internals with `parse_syllabus_pdf`; run all parser tests → PASS. Commit.

### Task 5: Runner, manifest, backlog

**Files:** Modify `evaluation/run_full_pipeline.py`, `evaluation/test_run_full_pipeline.py`,
`data/raw/syllabi/vit_syllabus_manifest.csv`, `docs/BACKLOG.md`.

- [ ] Tests: `RESULTS_VERSION == "v1.2"`; argument parsing yields file list from `--pdf-dir`/`--glob`;
  manifest course rows' codes == v1.2 `core_courses`, each with the agreed `source`.
- [ ] Run → FAIL; implement; run → PASS. Commit.

### Task 6: Run + changelog + verify

- [ ] `python evaluation/run_full_pipeline.py --pdf-dir data/raw/syllabi --syllabus-id VIT_CSE_2024_25_courses --out results/amazon_sde1_v1.2_course_syllabi.json`
- [ ] Write `results/CHANGES_v1.2.md` (vs v1.1 and v1.0). Full suite `python -m pytest evaluation -q`. Commit.
