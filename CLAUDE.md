# CLAUDE.md: PREPLINE

PREPLINE scores how well the VIT B.Tech CSE 2024-25 core syllabus (26 courses) covers the topics companies ask about in
interviews. For each company/role target it reports a composite score S_comp and ranked priority gaps. README.md covers
the overview, formulas, current results and limitations; `docs/ARCHITECTURE.md` has the data-flow diagram and "where to
change what". Read both before larger changes.

## Architecture

| Area | Role |
|---|---|
| `pipeline/config.py` | Loads the current scoring config (`config/scoring_v1.2.json`) once per path. All frozen constants come from it; never hard-code them. |
| `pipeline/syllabus_parser.py` | pdfplumber parsing: splits PDFs into courses → modules, keeps allowlisted core courses, extracts depth signals, detects pages with no text layer. Transcriptions for PDFs without text: `data/raw/syllabi/transcribed/<CODE>.txt`. |
| `pipeline/interview_parser.py` | Applies the interview filter (behavioural, `needs_review`, no question text, no report id) and writes `excluded_questions.csv`. |
| `pipeline/keyword_abstraction.py` → `embeddings.py` → `taxonomy_mapper.py` | Two-pass abstraction (RAKE concepts), local MiniLM cosine matching against node descriptions, and the deterministic 60/40 credit split. Applies the node-type rule: syllabus → `high_level_concept`, interview → `granular_skill`. |
| `pipeline/taxonomy_tree.py` | Granular skills inherit coverage from their nearest high-level ancestor. |
| `pipeline/scoring.py` | Coverage C(t)/D(t), importance I(t), S_comp with the density gate, and priority gaps. |
| `pipeline/unmapped_terms_logger.py`, `taxonomy_versioning.py` | Append-only unmapped-terms log; manual taxonomy-version governance. Neither automates migration. |
| `backend/` | FastAPI app (`app.py`). `routes.py`: upload / validate-target / pipeline run. `dashboard.py`: read-only results, comparison, benchmark, validation and pilot. `study.py`: study list. `report.py`: reportlab PDF. `schemas.py`: Pydantic models. Limits, CORS and file paths are in `config/api.json`. |
| `dashboard/web/` | Vite + React 19 + TS + Tailwind v4 + Recharts. It only reads saved files via the API and never runs the pipeline. |
| `evaluation/` | Runners (`run_full_pipeline.py`, `run_all_targets.py`), dashboard exporters (`export_topic_tables.py`, `export_study_modules.py`), `retro_validation.py`, `compare_results.py`, `review_unmapped_terms.py`, `benchmark/`, `pilot/`, and all pytest tests (`test_*.py`). |

Data: one folder per target, `data/processed/<target_id>/` (`reports.csv`, `questions.csv`, generated
`excluded_questions.csv`), registered in `config/targets.json`. Adding a target needs no code changes
(`docs/ADDING_A_COMPANY.md`). Report sources are listed in `data/SOURCES.md`.

## Commands

```powershell
pip install -r requirements.txt
python -m pytest evaluation -q                                    # Python tests
powershell -ExecutionPolicy Bypass -File scripts/start_demo.ps1   # API :8000 + dashboard :5173
python -m uvicorn backend.app:app --host 127.0.0.1 --port 8000    # API only
python evaluation/run_all_targets.py                              # results/<id>_v1.2_course_syllabi.json + COMPARISON.md
python evaluation/export_topic_tables.py; python evaluation/export_study_modules.py   # dashboard data
cd dashboard/web; npx playwright test                             # dashboard E2E (refreshes screenshots)
cd dashboard/web; npm run build; npm run lint                     # tsc + vite build; oxlint
```

Syllabus PDFs are gitignored (`data/raw/syllabi/*.pdf`, listed in `vit_syllabus_manifest.csv`). The backend loads the
embedding stack at import, and parsing the full VIT PDF takes minutes.

## Frozen constraints (change only with explicit owner approval and a new config version)

- τ = 0.50, γ = 0.5, depth reference values, `min_reports` = 15, semester weeks, taxonomy v1.0, the embedding model
  and its revision, the node-type rule, and the core-course allowlist: all in `config/scoring_v1.2.json`.
- The density gate needs ≥ 15 reports left after filtering. Below that, the status is `INSUFFICIENT_DATA` with no S_comp.
  Never relax the gate.
- Benchmark gold labels v1.0 and splits v1.0 are frozen. Never use the test split to choose a method or threshold.
- Every mapping and result pins `taxonomy_version`.

## Conventions

- **Versioned outputs, never overwritten.** Results, configs, the taxonomy, benchmark splits, topic tables, study
  modules and validation files are versioned. Runners skip or refuse existing files (use `--replace` or `--out-dir`
  where offered). Superseded configs (`scoring_v1.0`, `v1.1`) are kept as records.
- **Raw data is immutable.** `data/raw/interviews/amazon_sde1_interviews.csv` and the raw syllabi are never edited.
- **Report IDs** are unique, prefixed per company (`AMZ`, ...) and never reused. For example, `AMZ012` was removed as a
  duplicate of `AMZ004` and stays unused.
- **Question parsing rules:**
  - Quote exact question titles in `question_text` (leave `topic` empty).
  - Put general topic mentions in `topic` (leave `question_text` empty).
  - Never paraphrase, invent, merge or drop questions.
  - For ambiguous or summary blobs, set `needs_review=True` with a `review_reason`.
- **`round_type`** is one of:
  - `OA`: online or written tests;
  - `technical`: coding, DSA or algorithms;
  - `behavioral`: leadership principles, projects, resume or hiring-manager chats;
  - `system_design`;
  - `mixed`: technical and behavioural without a breakdown;
  - `unknown`.
- **Credit split:** one match above τ gets 100 %. With several, the top match gets 60 % and the rest share 40 % equally.
  Exact ties are broken alphabetically by `topic_id`.
- **Honest reporting:** scores are labelled provisional. Known mapping errors live in `docs/BACKLOG.md` and are shown on
  the dashboard. Retro validation must not be presented as the pilot or as outcome validation. Never invent results,
  pilot responses or calibration.
- **API safety:** the server binds to loopback by default (`PREPLINE_HOST` to change it), uploads are size, page and
  filename limited, CORS never allows credentials, and unhandled errors return a generic 500 with a request id.
- **Pilot data:** raw form exports (`data/pilot/responses*.csv`) stay local; only aggregated `results/pilot/` is
  committed.

## Dashboard UI (redesign 2026-10-24)

Spec and plan: `docs/superpowers/specs/2026-10-24-ui-redesign-scroll-story-design.md`,
`docs/superpowers/plans/2026-10-24-ui-redesign-scroll-story.md`.

- **Design system:** editorial academic.
  - Tokens in `dashboard/web/src/index.css`: paper `#f7f5f0` / ink `#0e0f13` themes and one ink-blue `--primary`.
  - The token names are unchanged, so components never use raw hex.
  - `--font-display` (bundled Newsreader) is for `h1`, card titles and the wordmark; Fira Sans/Code stay for UI and data.
  - `PageHeader` takes an `eyebrow` ("Dashboard · 0N").
- **Story route `/how-it-works`** (`src/story/`):
  - It sits outside `Layout` and runs five chapters: syllabus, taxonomy, interview evidence, scoring, gaps.
  - Every number comes from `/api/v1/results/{target}` and `/api/v1/comparison` via `story/data.ts`. Never hard-code
    story values.
  - The §4 strip is exact: column width = I(t)/ΣI and fill = Coverage(t), so the filled share is S_comp/100.
  - There are no invented course→topic connectors.
- **Motion:**
  - The `motion` package is imported only under `src/story/` (lazy route chunk); keep it out of the entry bundle.
  - Animate only transform and opacity, using full `transform` strings.
  - Chapters pin only on screens at least 900px wide and 700px tall (the `unpinned` CSS variant and `UNPINNED` in
    `useChapterProgress.ts` must agree).
  - Unpinned, progress tracks the scene element itself, so it animates as it enters view.
  - The story header is sticky only at 1000px and wider, so a wrapped company selector never covers a pinned stage.
  - While results load, chapters show a scene-sized skeleton.
  - `prefers-reduced-motion`: no pinning, every scene in its final state.
- **Theme toggle** lives in `components/ThemeToggle.tsx` (shared by the sidebar and the story header, same
  `prepline-theme` key).
- **Tests:**
  - `tests/story.spec.ts` checks the story numbers against the live API, plus reduced motion, 360 px, API-down,
    insufficient data and company switching.
  - `tests/design.spec.ts` checks the display face, nav entry, eyebrows and theme persistence.
- **Verification on 2026-10-24:**
  - `python -m pytest evaluation -q` → 339 passed.
  - `npx playwright test` → 42 passed, 6 skipped (`media.spec.ts`, needs `MEDIA=1`).
  - A final fresh-context code review found no Critical issues. All 4 Important findings were fixed test-first: phone
    scrub mapping, a company-switch test that now checks the new company's values, the loading skeleton, and short or
    medium-width pinning. 10 Minor findings are deferred.
  - `npm run lint` → exit 0, with `only-export-components` warnings only.
  - `npm run build` → OK.
  - A manual pass found no console errors (both themes, with and without reduced motion) and no horizontal overflow at
    768/390/360 px. The PDF export, study links, tooltips, Topic explorer search and company hand-off all work.

## Skills policy

- Workflow: Superpowers (brainstorm → plan → TDD → verify). Do not use ECC workflows.
- Constraint-Driven Development: the frozen constraints above stay frozen unless I explicitly say otherwise.
- Logic changes: TDD Guard on; write the failing test first.
- Check Context7 before using the sentence-transformers, pdfplumber, FastAPI or NLTK APIs.
- Versioned outputs/config: Deprecation & Migration; never overwrite old results files.
- Pipeline runs: log timings and counts (Observability).
- Before any merge: Claude Security review.
- Dashboard only: Impeccable (design), Emil Kowalski (motion, sparingly), Playwright (tests).
