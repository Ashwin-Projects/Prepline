# Prepline

**Curriculum-to-Interview Alignment Engine**

Prepline measures how closely a university's computer science curriculum covers the topics that specific companies ask
about in technical interviews. It parses syllabus PDFs and public interview-experience write-ups, maps both onto a
shared taxonomy with local NLP embeddings, and produces a composite coverage score plus a ranked list of preparation
gaps for each company/role.

> Prepline measures topic alignment and surfaces curriculum gaps. It is a diagnostic tool, not a guarantee of
> interview or hiring outcomes.

## Contents

- [Scope and results](#scope-and-results)
- [Features](#features)
- [Architecture](#architecture)
- [Setup](#setup)
- [Usage](#usage)
- [Evaluation](#evaluation)
- [Testing](#testing)
- [Project structure](#project-structure)
- [Limitations](#limitations)

## Scope and results

- **Syllabus:** the VIT B.Tech CSE 2024-25 core: 26 courses from 28 course PDFs, scored as one combined syllabus of 209
  units (120 theory modules, 89 lab units). Three courses (BCSE101E, BCSE102L, BCSE103E) are read from manual
  transcriptions in `data/raw/syllabi/transcribed/` because their PDFs have no text layer.
- **Targets:** 4 company/role pairs, each a data folder plus one entry in `config/targets.json`.
- **Scoring config v1.2 (frozen):** taxonomy v1.0 (83 topics), τ = 0.50, γ = 0.5, `MIN_REPORTS = 15`,
  `all-MiniLM-L6-v2` at a pinned revision.

| Target | Reports collected → usable | Density gate | S_comp (provisional) | Scored topics |
|---|---|---|---|---|
| Amazon SDE-1 | 21 → 18 | passed | 88.77 | 9 |
| Microsoft SDE-1 | 17 → 15 | passed | 89.09 | 14 |
| Google SWE new-grad / L3 | 16 → 8 | **not met** | — (INSUFFICIENT_DATA) | — |
| Flipkart SDE-1 | 20 → 17 | passed | 89.74 | 13 |

Each company is scored on its own set of interview topics, so similar scores are **not a ranking**. Scores are
provisional because of known mapping errors (see [Limitations](#limitations)). Details: `results/COMPARISON.md`,
`results/CHANGES_v1.2.md`.

## Features

- **Scoring pipeline:** syllabus parsing with depth signals, interview-question filtering, two-pass keyword abstraction,
  embedding-based taxonomy mapping, coverage, importance, composite score and priority-gap ranking.
- **Multi-target:** adding a company needs only a data folder and one config entry (`docs/ADDING_A_COMPANY.md`).
- **FastAPI backend:** syllabus upload, density-gate check and pipeline run, plus read-only endpoints over the saved
  results, a study list per target and a downloadable PDF report.
- **How it works** (`/how-it-works`): a scroll-driven walkthrough of the pipeline in five chapters, drawn from the saved
  results for the selected company, leading into the dashboard.
- **Dashboard** (`dashboard/README.md`) with six pages:
  - **Overview:** S_comp with a confidence badge, data card, priority gaps, coverage by domain, known mapping limitations,
    **What to study next** (VIT modules to revise and two checked practice links per gap) and **Download report (PDF)**.
  - **Compare:** all targets side by side.
  - **Topic explorer:** all 83 topics.
  - **Confidence:** insufficient data, fallback depth and unmapped terms.
  - **Benchmark:** the matcher comparison.
  - **Methodology:** formulas, the retrospective validation and the pilot status.

  Light and dark themes; laid out for a 1366×768 projector and reflows to phone width.
- **Evaluation:** a matcher benchmark on gold labels, a leave-one-report-out retrospective validation, and a
  pre-registered student pilot with its analysis script.
- **Versioned outputs:** results, configs, the taxonomy and benchmark splits are versioned and never overwritten.

## Architecture

```
 Course PDFs (26)  -> boilerplate stripped -> RAKE concepts -> MiniLM vs high-level nodes -> Coverage(t)
 Interview reports -> filtered questions   -> RAKE concepts -> MiniLM vs granular skills  -> Importance I(t)
                                                                                  -> S_comp, PriorityGap(t)
```

- **Taxonomy** (`data/taxonomy/taxonomy_v1.0.json`): 83 nodes in DSA, DBMS, OS, Computer Networks and System Design.
  Syllabus units match `high_level_concept` nodes; interview questions match `granular_skill` nodes, which inherit
  coverage from their nearest high-level ancestor.
- **Interview filter:** behavioural rounds, `needs_review` rows and rows without question text or report id are
  excluded (written to the target's `excluded_questions.csv`).
- **Matching:** local `all-MiniLM-L6-v2` cosine similarity against each node's description, τ = 0.50. With several
  matches, the best topic gets 60 % credit and the rest share 40 %; ties are broken by `topic_id`. Below-threshold
  terms go to an append-only unmapped-terms log.
- **Depth:** workload signals (unit hours, lab hours, experiment count, etc.) normalised by reference values;
  $D(t) = 1 + 4 \cdot \text{mean}\,\min(x/R_x, 1) \in [1, 5]$, or $D = 1$, flagged *fallback*, when no signal exists.
- **Coverage:** $\text{Coverage}(t) = C(t)\cdot\frac{1-e^{-\gamma D(t)}}{1-e^{-5\gamma}}$, γ = 0.5 (a present topic at
  fallback depth counts ≈ 43 % covered).
- **Importance:** $I(t) = \frac{1}{N}\sum_r \max_{q\in r}\text{credit}(q,t)$ over the N reports with at least one usable
  question.
- **Composite score:** $S_{\text{comp}} = 100\cdot\frac{\sum_{t\in U} I(t)\,\text{Coverage}(t)}{\sum_{t\in U} I(t)}$,
  $U = \{t \mid I(t) > 0\}$, computed only when N ≥ 15; otherwise the status is `INSUFFICIENT_DATA`.
- **Priority gap:** $\text{PriorityGap}(t) = I(t)\,(1 - \text{Coverage}(t))$, ranked descending.

The dashboard only reads saved results through the API; it never runs the pipeline. Diagram, code graph and "where to
change what": `docs/ARCHITECTURE.md`.

## Setup

- Python 3.10+: `pip install -r requirements.txt`. The embedding model downloads on first use; NLTK data downloads
  lazily.
- Node.js 20+ for the dashboard. `scripts/start_demo.ps1` installs its npm packages on first run.
- Syllabus PDFs are gitignored. To re-run the pipeline, place them in `data/raw/syllabi/` as listed in
  `data/raw/syllabi/vit_syllabus_manifest.csv`. The dashboard works without them, from the committed results.

## Usage

**Dashboard:**

```powershell
powershell -ExecutionPolicy Bypass -File scripts/start_demo.ps1   # API on :8000 + dashboard on :5173, opens the browser
```

`-NoBrowser` skips opening the browser; `-Python <path>` picks another interpreter. API docs:
http://127.0.0.1:8000/docs.

**API endpoints** (all under `/api/v1`):

| Group | Endpoints |
|---|---|
| Pipeline | `POST /syllabi/upload`, `POST /validate-target`, `POST /pipeline/run`, `GET /supported-targets` |
| Dashboard (read-only) | `GET /targets`, `/results/{target_id}`, `/comparison`, `/benchmark`, `/validation`, `/pilot`, `/study/{target_id}`, `/report/{target_id}` (PDF) |

Upload limits, CORS origins and the dashboard's file paths are set in `config/api.json`. The server binds to
`127.0.0.1` unless `PREPLINE_HOST` is set.

**Re-running the pipeline:**

```powershell
python evaluation/run_all_targets.py        # results/<target>_v1.2_course_syllabi.json + results/COMPARISON.md
python evaluation/export_topic_tables.py    # results/topics/ (per-topic tables for the dashboard)
python evaluation/export_study_modules.py   # results/study/ ('What to study next')
python evaluation/run_full_pipeline.py --target <id> --pdf-dir data/raw/syllabi --glob "B[CM]*.pdf" --syllabus-id VIT_CSE_2024_25_courses   # one target
```

Existing results files are not overwritten: a target whose file exists is skipped, so delete the file deliberately or
use another `--out-dir` to regenerate it. Practice links live in `config/practice_links.json`. Every URL was opened and
checked; only GeeksforGeeks links are used, because LeetCode refuses automated checks.

## Evaluation

**Matcher benchmark** (`results/benchmark/BENCHMARK.md`). 247 gold items (201 syllabus units from 25 courses + 46
Amazon interview questions), with a grouped 70/15/15 dev/val/test split (seed 20261022). Thresholds were chosen on dev
and checked on val. Test was never used to make a choice; it was computed twice by accident, with identical numbers.

| Method | τ (dev) | Test accuracy | Test macro-F1 |
|---|---|---|---|
| (a) Keyword match on node names | 0.40 | 0.644 | 0.388 |
| (b) TF-IDF, name + description | 0.30 | 0.533 | 0.200 |
| (c) MiniLM, description only (production) | 0.55 | 0.533 | 0.213 |
| (d) MiniLM, name + description | 0.40 | 0.489 | 0.338 |

Production (c) has the best val macro-F1, so it is kept. Dev and test favour (a) and (d), but val and test are small
(35 and 45 items), so a larger val set is needed before changing the matcher. Gold labels: κ = 0.812 between two
independent LLM labellers. The human owner adjudicated their 56 disagreements; the other 191 rows are LLM cross-checked
only (`evaluation/benchmark/ADJUDICATION.md`). Gold v1.0 is frozen and excludes BCSE203E.

**Retrospective validation** (`results/validation/RETRO_VALIDATION.md`, `python evaluation/retro_validation.py`).
Leave-one-report-out: each held-out report's topics are compared with the top-10 topics by importance from the other
reports, against a random baseline drawn from the 46 interview skills.

| Company | PREPLINE top-10 hit rate | Random baseline |
|---|---|---|
| Amazon SDE-1 | 88.0 % | 18.9 % |
| Microsoft SDE-1 | 55.0 % | 21.5 % |
| Flipkart SDE-1 | 47.9 % | 21.9 % |

This reuses the same public reports Prepline is built from, so it is not outcome validation.

**Student pilot** (`docs/pilot/PILOT_PROTOCOL.md`, pre-registered). The Google Form is built by hand from
`docs/pilot/FORM.md`, which is generated by `evaluation/pilot/build_form.py`. Participants rate a company's top-10 gaps;
Track A (students who took that company's OA or interview) also ticks the topics they met. To analyse a Google Forms
CSV export:

```powershell
python evaluation/pilot/analyze_pilot.py data/pilot/responses.csv
```

The analysis reports M1 (topic hit rate), M2 (mean gap match) and M3 (mean rating) per track and company. **No
responses have been analysed yet.** Raw exports stay local (`data/pilot/responses*.csv` is gitignored).

## Testing

```powershell
python -m pytest evaluation -q                               # Python suite: pipeline, API, data, benchmark, pilot
cd dashboard/web; npx playwright install chromium            # once
npx playwright test                                          # dashboard E2E; starts or reuses both servers
$env:MEDIA = "1"; npx playwright test tests/media.spec.ts    # regenerate docs/pilot/img and demo.webm
```

Playwright runs refresh `dashboard/screenshots/`. `tests/worst-case.spec.ts` feeds extreme data through route mocks.

## Project structure

```
backend/        FastAPI app (app.py): pipeline routes (routes.py), read-only dashboard endpoints (dashboard.py),
                study list (study.py), PDF report (report.py), Pydantic schemas (schemas.py)
config/         scoring_v1.0–v1.2.json (v1.2 current), targets.json, api.json, practice_links.json
dashboard/web/  Vite + React 19 + TypeScript + Tailwind v4 + Recharts dashboard, Playwright tests
data/           raw syllabi and interviews, processed/<target>/ folders, taxonomy, pilot template, SOURCES.md
docs/           ARCHITECTURE.md, ADDING_A_COMPANY.md, BACKLOG.md, DEMO_SCRIPT.md, EXISTING_PLATFORMS.md, pilot/
evaluation/     runners, exporters, retro validation, tests, benchmark/, pilot/
pipeline/       config, parsing, abstraction, embeddings, taxonomy mapping and versioning, scoring
results/        versioned results, COMPARISON.md, CHANGES_v1.x.md, topics/, study/, benchmark/, validation/
scripts/        start_demo.ps1
```

Interview data comes from GeeksforGeeks. Each target folder has `reports.csv`, `questions.csv` (questions quoted
verbatim) and a README with its inclusion rules. Every report's URL and date basis is listed in `data/SOURCES.md`.

## Limitations

- **Mapping errors are in every score.** Nodes are matched by description only:
  - DAA's "Dynamic Programming" module misses `dsa.dp`.
  - There are false positives: Java "IO Streams" matches message queues, and React "Routing" matches the network layer.
  - The taxonomy has no nodes for hashing, greedy algorithms, interval problems, string matching or object-oriented
    design.

  Details: `docs/BACKLOG.md` → *Known mapping limitations*.
- **The interview data is small, public and convenience-sampled:** 16–21 reports per company from one site, mostly
  undated. Google is below the density gate.
- **Scores are close to the ceiling (88–90)** and rest on small scoring universes of 9–14 topics.
- **The benchmark's val and test sets are small**, and most gold labels were produced by LLMs.
- **There is no outcome validation yet.** γ and the depth reference values are uncalibrated, and the pilot has no
  responses.
- **Out of scope:** OCR (pages without a text layer are detected and skipped), automated taxonomy generation,
  per-student electives, and API authentication.

Planned work is tracked in `docs/BACKLOG.md`.
