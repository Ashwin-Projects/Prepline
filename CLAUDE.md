# CLAUDE.md - PREPLINE Project Context & Memory

## Overview & Purpose

**PREPLINE** is a Curriculum-to-Interview Alignment Engine. It quantitatively measures how closely a university's computer science curriculum aligns with the technical interview expectations of specific tech companies and software engineering roles.

### Core Problem Solved
University CS programs focus on foundational computer science theory, whereas industry technical interviews evaluate a specific, applied subset of that theory (e.g., LeetCode-style DSA, System Design, Leadership Principles). PREPLINE bridges this gap by creating an auditable, data-driven mapping between course syllabus documents (PDFs) and real interview experience reports (CSVs/JSON), outputting:
1. **Composite Alignment Score ($S_{\text{comp}}$)**: Overall alignment percentage (0-100%).
2. **Topic Coverage ($\text{Coverage}(t)$)**: Topic-level presence bit $C(t)$ and workload depth $D(t) \in [1.0, 5.0]$.
3. **Priority Gap List ($\text{PriorityGap}(t)$)**: Ranked list of preparation gaps based on interview importance $I(t)$ and missing coverage.

---

## Project Structure

```
prepline/
├── backend/                  # FastAPI endpoints and Pydantic schemas (backend/schemas.py)
├── dashboard/                # UI components and visualization frontend
├── data/
│   ├── raw/
│   │   ├── interviews/
│   │   │   └── amazon_sde1_interviews.csv # Original raw Amazon SDE-1 interview dataset (unmodified, committed)
│   │   └── syllabi/
│   │       ├── vit_syllabus_manifest.csv  # Manifest defining raw VIT CSE 2024-25 syllabus document sources
│   │       └── *.pdf                      # Input syllabus PDFs (gitignored)
│   ├── processed/            # Canonical dataset CSVs (reports.csv, questions.csv)
│   └── taxonomy/             # Versioned taxonomy hierarchy (taxonomy_v1.0.json)
├── pipeline/
│   ├── __init__.py
│   ├── interview_parser.py   # Dataset ingestion, parsing & deduplication logic (Phase 2)
│   ├── syllabus_parser.py    # Syllabus PDF text & depth metric extraction via pdfplumber (Phase 7)
│   ├── keyword_abstraction.py# Two-pass NLP abstraction logic (Phase 4)
│   ├── embeddings.py         # Local sentence embeddings via all-MiniLM-L6-v2 (Phase 5)
│   ├── taxonomy_mapper.py    # Canonical node mapping & 60/40 topic credit split (Phase 6)
│   └── scoring.py            # Coverage, importance, composite score & gap ranking (Phases 9-12)
├── evaluation/               # Benchmark scripts & unit tests (test_syllabus_parser, test_backend_api, etc.)
├── .gitignore                # Ignores virtual environments, cache, logs, data/raw/syllabi/*.pdf
├── README.md                 # Full project specification & mathematical formulation
└── requirements.txt          # Dependencies (torch, sentence-transformers, pdfplumber, pandas, etc.)
```

---

## Project Phases & Status

| Phase | Description | Status | Notes |
|---|---|---|---|
| **Phase 1** | Scaffolding & environment setup | **Completed** | Directory structure and basic modules created |
| **Phase 2** | Raw interview dataset restructuring, expansion & deduplication | **Completed & Pushed** | Committed in `0dbe0e0`: `data/processed/reports.csv` (21 independent reports) & `data/processed/questions.csv` (99 rows); **Density Gate PASSED** |
| **Phase 3** | Versioned taxonomy definition | **Completed** | `taxonomy_v1.0.json` defined in `data/taxonomy/` |
| **Phases 4–6** | Two-pass NLP abstraction, local embeddings, 60/40 credit mapper | **Completed & Verified** | Built in `pipeline/keyword_abstraction.py`, `pipeline/embeddings.py`, `pipeline/taxonomy_mapper.py`. Uses `all-MiniLM-L6-v2`, threshold $\tau = 0.50$, deterministic 60/40 credit split. Validated 99/99 dataset items (75 mapped, 24 subthreshold). |
| **Phase 7** | Syllabus PDF parsing (`pdfplumber`) & depth modeling ($D(t)$) | **Completed & Tested** | Built in `pipeline/syllabus_parser.py`. Extract course metadata, depth signals, scanned PDF detection & test-covered (`test_syllabus_parser.py`). |
| **Phase 8** | Presence & Depth Modeling ($C(t)$, $D(t) \in [1.0, 5.0]$, $\text{Coverage}(t)$) | **Completed & Tested** | Built in `pipeline/scoring.py` (`calculate_syllabus_coverage`). Verified by `evaluation/test_scoring.py` |
| **Phase 9** | Per-Report Topic Importance ($W(r,t)$, $I(t)$) | **Completed & Tested** | Built in `pipeline/scoring.py` (`calculate_topic_importance`). Verified by `evaluation/test_scoring.py` |
| **Phase 10** | Overall Composite Alignment Score ($S_{\text{comp}}$) | **Completed & Tested** | Built in `pipeline/scoring.py` (`calculate_composite_score`). Universe $U = \{t \mid I(t) > 0\}$. Enforces 15-report density gate. Verified by `evaluation/test_scoring.py` |
| **Phase 11** | Priority Gap Ranking ($\text{PriorityGap}(t)$) | **Completed & Tested** | Built in `pipeline/scoring.py` (`rank_priority_gaps`). Calculates $\text{PriorityGap}(t) = I(t) \cdot (1 - \text{Coverage}(t))$, sorts descending with deterministic `topic_id` tie-breaking. Verified by `evaluation/test_scoring.py` |
| **Phase 12** | Unmapped-terms logging + taxonomy versioning | **Completed** | Built in `pipeline/unmapped_terms_logger.py`, `pipeline/taxonomy_versioning.py`, `evaluation/review_unmapped_terms.py`. Verified by `evaluation/test_phase12.py` |
| **Phase 13** | Ground-truth benchmark evaluation (200+ samples, 70/15/15 split) | **Pending** | Dev/Val/Test splits for NLP evaluation |
| **Phase 14** | Backend API & Scoring Integration | **Completed & Integrated** | FastAPI service in `backend/app.py`, `routes.py`, `schemas.py` fully integrated with Phase 8–11 scoring engine (`calculate_syllabus_coverage`, `calculate_topic_importance`, `calculate_composite_score`, `rank_priority_gaps`). Enforces 15-report density gate against canonical `reports.csv`. Tested by `evaluation/test_backend_api.py`. |
| **Phase 15** | Dashboard UI | **Pending** | UI frontend components and visualization |
| **Phase 16** | Pilot outcome validation & gamma calibration | **Pending** | Cohort outcome correlation |

---

## Session Accomplishments

1. **Phases 4–6 Final Validation & Verification**:
   - Merged latest `origin/main` baseline into `feature/sprint3-two-pass-abstraction`.
   - Executed full end-to-end dataset validation against all 99 questions in `data/processed/questions.csv`.
   - Confirmed **75 items mapped** ($\tau \ge 0.50$) and **24 subthreshold/behavioral items unmapped** ($\tau < 0.50$).
   - Verified 0 taxonomy version mismatches, 0 invented nodes, 0 credit allocation sum errors, and 100% adherence to the deterministic 60/40 credit split.

2. **NLTK Resource Handling Optimization**:
   - Updated `_get_rake()` in `pipeline/keyword_abstraction.py` with lazy initialization and auto-download checks (`stopwords`, `punkt`, `punkt_tab`) to guarantee zero import-time failures in fresh environments.

3. **Phase 2 Dataset Completion & Push**:
   - Expanded Amazon SDE-1 interview reports to **21 independent reports** (`AMZ001`–`AMZ011`, `AMZ013`–`AMZ022`). `AMZ012` remains removed as a duplicate of `AMZ004`.
   - Extracted and classified **99 total question/topic rows** into `data/processed/questions.csv`.
   - Committed changes in commit `0dbe0e0` ("Complete Phase 2 interview dataset") and pushed to `origin/main`.

4. **Syllabus Manifest Preparation (Phase 7)**:
   - Added `vit_syllabus_manifest.csv` mapping official VIT CSE 2024-25 curriculum PDF specifications and official source URLs.

5. **Test Suite Verification**:
   - Executed full test suite (`python -m unittest discover -s evaluation`). All **16 / 16 unit tests passed cleanly in 0.49s**.

6. **Phase 8 (Presence & Depth Modeling) Implementation & Verification**:
   - Implemented `calculate_syllabus_coverage()` in `pipeline/scoring.py` following PREPLINE Final Execution Blueprint v1.1.
   - Aggregate syllabus-wide presence bit $C(t) \in \{0, 1\}$.
   - Normalized available depth signals $N(x) = \min(x/R_x, 1.0)$ using exact reference constants (`unit_hours`=10, `slide_count`=20, `lab_hours`=10, `lab_count`=5, `assignment_count`=5). Missing signals are excluded from denominator rather than treated as zero.
   - Calculated depth $D(t) = 1.0 + 4.0 \cdot D_{\text{norm}}(t)$ bounded in $[1.0, 5.0]$, distinguishing measured depth from fallback depth ($D=1.0$, `depth_status="fallback"`).
   - Applied decay coverage formula $\text{Coverage}(t) = C(t) \cdot \left[\frac{1 - e^{-\gamma D(t)}}{1 - e^{-5\gamma}}\right]$ with $\gamma = 0.5$.
   - Built comprehensive test suite in `evaluation/test_scoring.py` (7 unit test cases).
   - Executed full test suite (`python -m unittest discover -s evaluation`). All **23 / 23 unit tests passed cleanly in 0.50s**.

7. **Phase 9 (Per-Report Topic Importance) Implementation & Verification**:
   - Implemented `calculate_topic_importance()` in `pipeline/scoring.py` consuming question inputs and computing question credits via `pipeline.taxonomy_mapper.map_source_to_taxonomy()`.
   - Grouped questions by `report_id` and enforced max credit capping $W(r,t) = \max_{q \in r}(\text{credit}(q, t))$ within each report to prevent duplicate question inflation.
   - Aggregated topic importance $I(t) = \frac{\sum_r W(r,t)}{\text{total\_reports\_count}}$ across $N=21$ independent Amazon SDE-1 reports.
   - Added comprehensive unit test suite `TestPhase9Scoring` in `evaluation/test_scoring.py` covering single question, multiple questions in one report (max capping), 60/40 split preservation, total reports denominator, unmapped topic zeroes, and full 99-question / 21-report integration.
   - Executed full test suite (`python -m unittest discover -s evaluation`). All **31 / 31 unit tests passed cleanly in 16.3s**.

8. **Phase 10 & Phase 11 (Composite Score & Priority Gap Ranking) Implementation & Verification**:
   - Implemented `calculate_composite_score(importance_dict, coverage_dict)` in `pipeline/scoring.py` using formula $S_{\text{comp}} = \left[\frac{\sum_{t \in U} (I(t) \cdot \text{Coverage}(t))}{\sum_{t \in U} I(t)}\right] \times 100$ over positive-importance scoring universe $U = \{t \mid I(t) > 0\}$. Enforces minimum 15-report density gate.
   - Implemented `rank_priority_gaps(importance_dict, coverage_dict, taxonomy_nodes)` in `pipeline/scoring.py` calculating $\text{PriorityGap}(t) = I(t) \cdot (1 - \text{Coverage}(t))$ for $t \in U$. Excludes zero-importance topics ($I(t) \le 0$) and sorts descending with deterministic `topic_id` tie-breaking. Returns `PriorityGapItem`-compatible structure with 1-indexed ranks.
   - Built unit test suites `TestPhase10Scoring` and `TestPhase11Scoring` in `evaluation/test_scoring.py` covering known scores, multiple topics, zero-importance exclusion, score bounding, empty input handling, descending gap sorting, and deterministic tie handling.
   - Executed full unit test suite (`python -m unittest discover -s evaluation`). All **42 / 42 unit tests passed cleanly in 17.7s**.

9. **Phase 8–11 Backend API Integration & Final Verification**:
   - Replaced all scaffold/mock values (`S_comp=76.5`, static coverage, mock report count) in `backend/routes.py` (`POST /api/v1/pipeline/run` and `POST /api/v1/validate-target`) with real outputs from `pipeline/scoring.py` (`calculate_syllabus_coverage`, `calculate_topic_importance`, `calculate_composite_score`, `rank_priority_gaps`).
   - Connected target report density gate to canonical dataset `data/processed/reports.csv` (`report_count=21`).
   - Extended `evaluation/test_backend_api.py` with end-to-end integration tests confirming dynamic calculation of $S_{\text{comp}}$, real importance and coverage lists, descending gap rankings, and total absence of mock values.
   - Performed clean import/startup check (`from backend.app import app`).
   - Executed full test suite (`python -m unittest discover -s evaluation`). All **43 / 43 unit tests passed cleanly in 17.8s**.

---

## Key Decisions, Rules & Schemas Established

- **Canonical Dataset Location**: Processed CSVs live under `data/processed/reports.csv` and `data/processed/questions.csv`.
- **Density Gate Constraint**: Scoring requires a minimum density of `MIN_REPORTS = 15` unique deduplicated reports per company/role pair. Current Amazon SDE-1 count is **21 unique reports**; density gate is **PASSED**.
- **Report ID Continuation**: Report IDs must be assigned sequentially (`AMZ001`..`AMZ011`, `AMZ013`..`AMZ022`). Never reuse removed duplicate IDs (`AMZ012`).
- **Parsing Rules for Questions**:
  - Exact question titles $\rightarrow$ `question_text` (leave `topic` empty).
  - General topic mentions $\rightarrow$ `topic` (leave `question_text` empty).
  - No paraphrasing, inventing, merging, or dropping of questions/topics.
  - Ambiguous/summary blobs $\rightarrow$ `needs_review: true` with a clear reason in `review_reason`.
- **Classification Rules for `round_type`**:
  - `OA`: Online assessments, written coding tests.
  - `technical`: Coding problems, DSA, algorithms.
  - `behavioral`: Workstyle, Leadership Principles, project/resume discussions, hiring manager chats.
  - `system_design`: System design problems (e.g. Parking Lot design, LED system design).
  - `mixed`: Rounds blending technical and behavioral without sub-breakdown.
  - `unknown`: Used when classification cannot be confidently made.
- **Credit Allocation Rule (60/40 Split)**:
  - Single topic above $\tau = 0.50 \rightarrow 100\%$ credit.
  - Multiple topics above $\tau = 0.50 \rightarrow 60\%$ to top similarity match, $40\%$ divided equally among secondary matches.
  - Exact ties broken alphabetically by `topic_id`.

---

## Current Dataset Summary

- **Raw Input File Rows (`amazon_sde1_interviews.csv`)**: 15 (unmodified baseline, committed)
- **Unique Independent Reports (`data/processed/reports.csv`)**: **21** (`AMZ001`–`AMZ011`, `AMZ013`–`AMZ022`)
- **Duplicate Reports Removed / Rejected**: 1 (`AMZ012` duplicate of `AMZ004`)
- **Total Question/Topic Rows (`data/processed/questions.csv`)**: **99**
- **PREPLINE Density Gate Requirement (`MIN_REPORTS = 15`)**: **PASSED (21 / 15 reports)**
- **Git Branch Status**: Up to date with `origin/main` (Commit `0dbe0e0`)

---

## Report status (12 Oct 2026)

- **Report draft**: Drafted as a Claude Doc titled "PREPLINE Project Report (AI-assisted draft)".
- **Verified figures**:
  - Amazon SDE-1 interview reports: **21**
  - Taxonomy: **v1.0**, **83 topics**
  - $S_{\text{comp}}$: **51.54**
  - Top priority gaps: heaps, shortest path, grid DP, top-K, message queues
  - Depth status: **58 measured / 25 fallback**
  - Test suite: **64 tests** passing
- **Remaining gaps**:
  - Second company-role pair
  - Phase 13 ground-truth benchmark
  - Teacher pilot
  - Scanned syllabus pages (OCR excluded from MVP)
  - Dashboard

---

## Instructions for Future Claude Sessions

1. **Read `CLAUDE.md` First**: Always inspect this file before starting work on PREPLINE to get up-to-date context.
2. **Do Not Modify Raw Data**: `amazon_sde1_interviews.csv` must remain unmodified as the raw baseline.
3. **Data Sources for Pipeline**: When building or running `pipeline/interview_parser.py` or scoring modules, consume `reports.csv` and `questions.csv` from `data/processed/`.
4. **Preserve Taxonomy Versioning**: All concept mappings and evaluations must pin to `taxonomy_version` (e.g., `v1.0`).

---

## Skills policy
- Workflow: Superpowers (brainstorm → plan → TDD → verify). Do not use ECC workflows.
- Constraint-Driven Development: τ=0.50, γ=0.5, depth reference values, MIN_REPORTS=15, taxonomy v1.0 are FROZEN unless I explicitly say otherwise.
- Logic changes: TDD Guard on; failing test first.
- Check Context7 before using sentence-transformers, pdfplumber, FastAPI, NLTK APIs.
- Versioned outputs/config: Deprecation & Migration; never overwrite old results files.
- Pipeline runs: log timings and counts (Observability).
- Before any merge: Claude Security review.
- Dashboard only: Impeccable (design), Emil Kowalski (motion, sparingly), Playwright (tests).

