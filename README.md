# Prepline

**Curriculum-to-Interview Alignment Engine**

Prepline measures how closely a university's computer science curriculum covers the topics that specific companies ask
about in technical interviews. It parses syllabus PDFs and public interview-experience write-ups, maps both onto a
shared taxonomy with local NLP embeddings, and produces a composite coverage score plus a ranked list of preparation
gaps for each company/role.

> Prepline measures topic alignment and surfaces curriculum gaps. It is a diagnostic tool, not a guarantee of
> interview or hiring outcomes.

---

## Contents

- [Current scope and results](#current-scope-and-results)
- [Run the dashboard](#run-the-dashboard)
- [Pipeline and methodology](#pipeline-and-methodology)
- [Data](#data)
- [Benchmark](#benchmark)
- [Student pilot](#student-pilot)
- [Testing](#testing)
- [Project structure](#project-structure)
- [Project status](#project-status)
- [Limitations](#limitations)
- [Future work](#future-work)

## Current scope and results

- **Syllabus:** the VIT B.Tech CSE 2024-25 core, **all 26 core courses** (28 course PDFs; 3 read from manual
  transcriptions because their PDFs have no text layer), scored as one combined syllabus: 209 units (120 theory modules,
  89 lab units).
- **Targets:** 4 company/role pairs, each a data folder plus one entry in `config/targets.json`.
- **Frozen scoring config v1.2:** taxonomy v1.0 (83 topics), τ = 0.50, γ = 0.5, `MIN_REPORTS = 15`.

| Target | Reports collected → usable | Density gate | S_comp (provisional) | Scored topics |
|---|---|---|---|---|
| Amazon SDE-1 | 21 → 18 | passed | 88.77 | 9 |
| Microsoft SDE-1 | 17 → 15 | passed | 89.09 | 14 |
| Google SWE new-grad / L3 | 16 → 8 | **not met** | — (INSUFFICIENT_DATA) | — |
| Flipkart SDE-1 | 20 → 17 | passed | 89.74 | 13 |

Each company is scored on its own set of interview topics, so similar scores are **not a ranking**. Scores are
provisional because of known mapping errors (see [Limitations](#limitations)). Full details:
`results/COMPARISON.md`, `results/CHANGES_v1.2.md`.

## Run the dashboard

```powershell
pip install -r requirements.txt                                   # once (Python 3.10+)
powershell -ExecutionPolicy Bypass -File scripts/start_demo.ps1   # API :8000 + dashboard :5173, opens the browser
```

Needs Node.js 20+ for the dashboard (packages install on first run). Six pages: **Overview** (S_comp, confidence,
data card, priority gaps, coverage by domain, **What to study next** — VIT modules to revise and two checked practice
links per gap — a **Download report (PDF)** button, known mapping limitations), **Compare** (all targets side by side),
**Topic explorer** (all 83 topics), **Confidence** (insufficient data, fallback depth, unmapped terms), **Benchmark**,
**Methodology**. Light and dark themes; laid out for a 1366×768 projector. See `dashboard/README.md`.

Re-running the pipeline:

```powershell
python evaluation/run_all_targets.py        # results/<target>_v1.2_course_syllabi.json + results/COMPARISON.md
python evaluation/export_topic_tables.py    # results/topics/ (per-topic tables for the dashboard)
python evaluation/export_study_modules.py   # results/study/ (modules to revise per topic, 'What to study next')
```

Practice links live in `config/practice_links.json`; every URL was opened and checked (GeeksforGeeks only, because
LeetCode refuses automated checks). The PDF report (`GET /api/v1/report/<target>`) is built from saved files only.

Results files are versioned and not overwritten; delete a file deliberately to regenerate it. Adding a company needs
only a data folder and one config entry (`docs/ADDING_A_COMPANY.md`).

## Pipeline and methodology

```
 Course PDFs (26)  -> boilerplate stripped -> RAKE concepts -> MiniLM vs high-level nodes -> Coverage(t)
 Interview reports -> filtered questions   -> RAKE concepts -> MiniLM vs granular skills  -> Importance I(t)
                                                                                  -> S_comp, PriorityGap(t)
```

- **Taxonomy** (`data/taxonomy/taxonomy_v1.0.json`): 83 nodes in DSA, DBMS, OS, Computer Networks and System Design.
  Syllabus units match `high_level_concept` nodes; interview questions match `granular_skill` nodes, which inherit
  coverage from their nearest high-level ancestor.
- **Matching:** local `all-MiniLM-L6-v2` cosine similarity against each node's description, τ = 0.50. With several
  matches the best topic gets 60 % credit and the rest share 40 %. Unmatched terms go to `unmapped_terms.log`.
- **Depth:** workload signals (unit hours, lab hours, experiment count) normalised by reference values;
  $D(t) = 1 + 4 \cdot \text{mean}\,\min(x/R_x, 1) \in [1, 5]$, or $D = 1$ flagged *fallback* when no signal exists.
- **Coverage:** $\text{Coverage}(t) = C(t)\cdot\frac{1-e^{-\gamma D(t)}}{1-e^{-5\gamma}}$, γ = 0.5 (a present topic at
  fallback depth counts ≈ 43 % covered).
- **Importance:** $I(t) = \frac{1}{N}\sum_r \max_{q\in r}\text{credit}(q,t)$ over the N reports with at least one usable
  question (behavioural rounds, vague mentions and link-only questions are filtered out).
- **Composite score:** $S_{\text{comp}} = 100\cdot\frac{\sum_{t\in U} I(t)\,\text{Coverage}(t)}{\sum_{t\in U} I(t)}$,
  $U = \{t \mid I(t) > 0\}$, computed only when N ≥ 15.
- **Priority gap:** $\text{PriorityGap}(t) = I(t)\,(1 - \text{Coverage}(t))$, ranked descending.

## Data

| Target | Folder | Source |
|---|---|---|
| Amazon SDE-1 | `data/processed/amazon_sde1/` | GeeksforGeeks, 21 reports |
| Microsoft SDE-1 | `data/processed/microsoft_sde1/` | GeeksforGeeks, 17 reports (interview dates mostly unknown) |
| Google SWE new-grad / L3 | `data/processed/google_swe_l3/` | GeeksforGeeks, 16 reports |
| Flipkart SDE-1 | `data/processed/flipkart_sde1/` | GeeksforGeeks, 20 reports |

Each folder has `reports.csv`, `questions.csv` (questions quoted verbatim; vague ones `needs_review=True`) and a README
with inclusion rules and excluded pages. Every report's URL and date basis is in `data/SOURCES.md`. Syllabus inputs and
their status are in `data/raw/syllabi/vit_syllabus_manifest.csv`.

## Benchmark

Phase 13, `results/benchmark/BENCHMARK.md`. 247 gold items (201 syllabus units from 25 courses + 46 Amazon interview
questions), grouped 70/15/15 dev/val/test split (seed 20261022). Thresholds were chosen on dev, checked on val; test was
never used for a choice (it was computed twice by accident, with identical numbers).

| Method | τ (dev) | Test accuracy | Test macro-F1 |
|---|---|---|---|
| (a) Keyword match on node names | 0.40 | 0.644 | 0.388 |
| (b) TF-IDF, name + description | 0.30 | 0.533 | 0.200 |
| (c) MiniLM, description only (production) | 0.55 | 0.533 | 0.213 |
| (d) MiniLM, name + description | 0.40 | 0.489 | 0.338 |

Production (c) has the best val macro-F1, so it is kept; dev and test favour (a)/(d), and val/test are small (35 and 45
items), so a larger val set is needed before changing the matcher.

**Gold labels:** κ = 0.812 is agreement between two independent LLM labellers (a Claude draft vs a fresh Claude
subagent); their disagreements (56 rows) were adjudicated by the human owner; the other 191 rows are LLM cross-checked
only, not individually human-reviewed (`evaluation/benchmark/ADJUDICATION.md`). Gold v1.0 is frozen and does not
include BCSE203E, which was added to the syllabus afterwards.

## Student pilot

Phase 16, pre-registered in `docs/pilot/PILOT_PROTOCOL.md`; the form is built by hand from `docs/pilot/FORM.md`
(consent → company → that company's top-10 gaps rated 1–5 → “taken an OA/interview with this company?” → Track A ticks
the topics met → both rate PREPLINE). `python evaluation/pilot/analyze_pilot.py data/pilot/responses.csv` reads the
Google Forms CSV export and reports, per track and company, M1 topic hit rate against the company's top-10 topics by
importance I(t) (Hashing, Greedy, OOP and Other reported apart; Cannot recall excluded), M2 mean gap match and M3 mean
rating. No responses are analysed yet.
Annotated screenshots for participants are in `docs/pilot/img/`, a 82-second walkthrough in `docs/pilot/demo.webm`.

## Testing

```powershell
python -m pytest evaluation -q                   # Python suite (pipeline, API, data, benchmark)
cd dashboard/web; npx playwright test            # dashboard end-to-end; refreshes dashboard/screenshots/
$env:MEDIA = "1"; npx playwright test tests/media.spec.ts   # regenerate docs/pilot/img and demo.webm
```

## Project structure

```
backend/            FastAPI app: upload/validate/run (routes.py), read-only dashboard endpoints (dashboard.py),
                    study list (study.py), PDF report (report.py)
config/             scoring_v1.0–v1.2.json (frozen), targets.json, api.json, practice_links.json
dashboard/web/      Vite + React + TypeScript + Tailwind + Recharts dashboard, Playwright tests
data/               raw syllabi and interviews, processed per-target folders, taxonomy, SOURCES.md
docs/               ARCHITECTURE.md, DEMO_SCRIPT.md, EXISTING_PLATFORMS.md, ADDING_A_COMPANY.md, BACKLOG.md,
                    pilot/ (protocol, form, screenshots, demo video), plans and specs
evaluation/         runners (run_full_pipeline, run_all_targets, export_topic_tables), tests, benchmark/
pipeline/           parsing, abstraction, embeddings, taxonomy mapping, scoring
results/            versioned results, COMPARISON.md, CHANGES_v1.x.md, topics/, study/, benchmark/, validation/
scripts/            start_demo.ps1
```

Architecture diagram and code graph: `docs/ARCHITECTURE.md`. Demo: `docs/DEMO_SCRIPT.md`; related platforms:
`docs/EXISTING_PLATFORMS.md`.

## Project status

| Sprint | Phase(s) | Description | Status |
|---|---|---|---|
| 1 | 1–2 | Scaffolding; interview dataset ingestion | Done |
| 2 | 3 | Versioned taxonomy (`taxonomy_v1.0.json`) | Done |
| 3 | 4–6 | Two-pass abstraction, local embeddings, credit mapper | Done |
| 4 | 7–8 | Syllabus parsing (26 course PDFs), depth modelling | Done |
| 5 | 9–12 | Importance, S_comp, priority gaps, unmapped-term logging | Done |
| 6 | 13 | Ground-truth benchmark (gold v1.0, 4 matchers) | Done |
| 7 | 14–15 | Backend API and dashboard | Done |
| 8 | 16 | Student pilot (form, protocol, analysis ready; no responses yet); γ calibration deferred | In progress |
| 9 | — | Optional: DSA prerequisite graph and study roadmap | Optional; a per-gap study list ships on the Overview |

## Limitations

- **Mapping errors are in every score.** Nodes are matched by description only, so DAA's "Dynamic Programming" module
  misses `dsa.dp`; Java "IO Streams" matches message queues and React "Routing" matches the network layer (false
  positives); there are no nodes for hashing, greedy algorithms, interval problems, string matching or object-oriented
  design. All listed in `docs/BACKLOG.md` → *Known mapping limitations*.
- **Small, public, convenience-sampled interview data** (16–21 reports per company, mostly undated, from one site);
  Google is below the density gate.
- **Scores are close to the ceiling (88–90) and depend on small scoring universes (9–14 topics).**
- **Benchmark val/test are small**, and most gold labels were LLM-produced (see [Benchmark](#benchmark)).
- **No outcome validation yet:** γ and the depth reference values are uncalibrated (Phase 16).
- Out of scope: OCR, automated taxonomy generation, per-student electives, authentication on the API.

## Future work

1. Run the student pilot and publish its per-track results; γ calibration needs round-level outcomes and a larger
   cohort.
2. Taxonomy v1.1 with the missing nodes, and a matcher that uses node names (candidate from the benchmark, needs a
   larger validation set and a new config version).
3. More interview reports (Google first) and more sources than GeeksforGeeks.
4. Human review of the 191 LLM-cross-checked gold rows; extend the benchmark to BCSE203E.
5. Optional Sprint 9: prerequisite graph and study roadmap per priority gap.
