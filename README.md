# Prepline

**Curriculum-to-Interview Alignment Engine**

Prepline measures how closely a university's computer science curriculum aligns with the technical interview requirements of a specific company and role. It parses syllabus PDFs and anonymized interview experience reports, maps both onto a shared taxonomy using local NLP embeddings, and produces a quantitative coverage score alongside a ranked list of preparation gaps.

> Prepline measures topic alignment and surfaces curriculum gaps. It is a diagnostic tool, not a guarantee of interview or hiring outcomes.

---

## Table of Contents

- [Overview](#overview)
- [Prototype Scope](#prototype-scope)
- [Execution Flow](#execution-flow)
- [Methodology](#methodology)
- [Data Schemas](#data-schemas)
- [Project Structure](#project-structure)
- [Evaluation Strategy](#evaluation-strategy)
- [MVP Exclusions](#mvp-exclusions)
- [Installation](#installation)
- [Usage](#usage)
- [Project Status](#project-status)

---

## Overview

University computer science coursework emphasizes foundational theory, while technical interviews assess a narrower, applied slice of that theory in company-specific combinations. Because no formal bridge connects degree coursework to industry hiring expectations, students have no reliable way to check whether their classes actually cover what a given company asks.

Prepline closes that gap by building an auditable, data-driven mapping between course syllabi and real interview experiences, so students can see — topic by topic — where their preparation is solid and where it falls short.

## Prototype Scope

The initial prototype is scoped to a single target: **Amazon Software Development Engineer I (SDE-1)**.

Constraining the prototype to one company/role pair keeps the taxonomy design, embedding thresholds, and scoring pipeline easy to validate end to end before expanding coverage. Scoring for a given company/role pair requires a minimum density gate of **15 unique, deduplicated interview reports** (`MIN_REPORTS = 15`); pairs below this threshold return an insufficient-data result rather than a score.

Additional company/role pairs (e.g., Google L3, Microsoft SDE-1) will be added only after the Amazon SDE-1 pipeline is fully built, benchmarked, and validated.

## Execution Flow

```
  Syllabus PDF                              Interview Reports
       |                                            |
   (pdfplumber)                               (JSON schema)
       |                                            |
       +--------------------+-----------------------+
                             |
                             v
                Two-Pass NLP Abstraction
          (raw text -> intermediate concepts)
                             |
                             v
                Local Sentence Embeddings
            (all-MiniLM-L6-v2, tau = 0.50)
                             |
                             v
                Versioned Taxonomy Mapping
                (60/40 credit allocation)
                             |
             +---------------+---------------+
             |                               |
             v                               v
      Syllabus Side                   Interview Side
      Presence: C(t)                  Report credit: W(r,t)
      Depth: D(t)                     Importance: I(t)
             |                               |
             +---------------+---------------+
                             |
                             v
               Coverage Score: Coverage(t)
               Overall Score: S_comp
               Priority Gap: PriorityGap(t)
```

1. **Input parsing** — Text-selectable syllabus PDFs are parsed with `pdfplumber`. Interview reports are validated against the report JSON schema.
2. **Two-pass abstraction** — Raw text is abstracted into intermediate concept vectors (Pass 1), then mapped to canonical taxonomy nodes (Pass 2).
3. **Local embedding and matching** — `all-MiniLM-L6-v2` embeds concept descriptions locally (no external API calls). Matches scoring above τ = 0.50 are assigned credit via a deterministic 60/40 split.
4. **Scoring** — Syllabus depth `D(t)` and topic coverage `Coverage(t)` are combined with interview topic importance `I(t)` to produce the composite score `S_comp` and the ranked `PriorityGap(t)` list.

## Methodology

### 1. Taxonomy and Embedding Matching

- **Taxonomy** (`taxonomy_v1.0.json`): a manually curated hierarchy covering DSA, DBMS, OS, Computer Networks, and System Design. Each node is tagged as `high_level_concept` (matched against syllabus units) or `granular_skill` (matched against interview questions), and carries a stable `topic_id` so renamed nodes remain trackable across versions.
- **Embeddings**: local `all-MiniLM-L6-v2` cosine similarity. Matches below τ = 0.50 are logged to `unmapped_terms.log` for periodic manual review.
- **60/40 topic credit split**:
  - A single topic above threshold receives 100% credit.
  - Multiple topics above threshold: the highest-similarity topic receives 60% (primary credit); the remaining 40% is split equally among the secondary topics.
  - Exact similarity ties are broken alphabetically by `topic_id`.

### 2. Presence and Depth Modeling

**Presence:**

$$C(t) = \begin{cases} 1 & \text{topic present in syllabus} \\ 0 & \text{topic absent} \end{cases}$$

**Depth:** workload signals are normalized against fixed reference values ($R_{\text{unit\_hours}} = 10$, $R_{\text{slides}} = 20$, $R_{\text{lab\_hours}} = 10$, $R_{\text{lab\_count}} = 5$, $R_{\text{assignments}} = 5$). Signals that are unavailable for a given topic are excluded from the average rather than treated as zero.

$$N(x) = \min\left(\frac{x}{R_x}, 1\right) \qquad D_{\text{norm}}(t) = \frac{\sum N(x)}{\text{available\_signals\_count}} \qquad D(t) = 1 + 4 \cdot D_{\text{norm}}(t)$$

This bounds $D(t)$ to $1 \le D(t) \le 5$. If no depth signals are available, $D(t) = 1$ and the result is flagged `depth_status = "fallback"`, which is kept distinct from a genuinely measured depth of 1.

**Normalized coverage:**

$$\text{Coverage}(t) = C(t) \cdot \left[\frac{1 - e^{-\gamma D(t)}}{1 - e^{-5\gamma}}\right], \qquad \gamma = 0.5 \text{ (MVP baseline, calibrated later against pilot data)}$$

Normalizing by $1 - e^{-5\gamma}$ ensures maximum measured depth ($D = 5$) maps to exactly 100% coverage while preserving diminishing returns.

### 3. Interview Importance and Overall Score

- **Report topic credit**: $W(r,t) = \max(\text{question-level credit for topic } t \text{ within report } r)$ — capped rather than summed, so repeated questions on the same topic within one report don't inflate its importance.
- **Topic importance**: $I(t) = \dfrac{\sum_r W(r,t)}{\text{total\_reports}}$
- **Composite score**:

$$S_{\text{comp}} = \left(\frac{\sum_{t \in U} I(t) \cdot \text{Coverage}(t)}{\sum_{t \in U} I(t)}\right) \times 100, \qquad U = \{t \mid I(t) > 0\}$$

### 4. Priority Gap Ranking

$$\text{PriorityGap}(t) = I(t) \cdot (1 - \text{Coverage}(t))$$

Topics are sorted in descending order of `PriorityGap(t)` to surface the highest-value preparation priorities first.

## Data Schemas

### Interview Report

Stored under `data/raw/interviews/`:

```json
{
  "report_id": "amz_sde1_001",
  "company": "Amazon",
  "role": "SDE-1",
  "round": "Coding Round 1",
  "question": "Given a binary tree, return its level-order traversal.",
  "source": "Glassdoor (permissive license)",
  "date": "2024-05-15"
}
```

### Syllabus Processing

- Text-selectable PDFs only; scanned/image-based PDFs are unsupported in the MVP.
- Extracts unit-level topics and numeric workload metrics: `unit_hours`, `slides`, `lab_hours`, `lab_count`, `assignments`.

## Project Structure

```
prepline/
├── backend/          # API endpoints and pipeline orchestration
├── dashboard/        # UI components and visualizations
├── data/
│   ├── raw/
│   │   ├── interviews/  # Raw Amazon SDE-1 interview reports (JSON)
│   │   └── syllabi/     # Input syllabus PDFs
│   ├── processed/       # Extracted terms, embeddings, score caches
│   └── taxonomy/        # taxonomy_v1.0.json
├── pipeline/
│   ├── __init__.py
│   ├── interview_parser.py
│   ├── syllabus_parser.py
│   ├── keyword_abstraction.py
│   ├── embeddings.py
│   ├── taxonomy_mapper.py
│   └── scoring.py
├── evaluation/       # Benchmark scripts and pilot evaluation
├── .gitignore
├── README.md
└── requirements.txt
```

## Evaluation Strategy

1. **Ground-truth benchmark**
   - 200+ manually verified `(raw_text, expected_taxonomy_node)` mappings, each pinned to a taxonomy version.
   - Split 70% development / 15% validation / 15% test.
   - Dev/validation data is used to compare sentence embeddings against TF-IDF and keyword-matching baselines and to tune the similarity threshold; final Precision/Recall/F1 is reported once on the untouched test split.
2. **Pilot outcome validation**
   - Topic-level coverage is compared against round-specific outcomes (e.g., System Design coverage vs. System Design round result) in an anonymized, consenting cohort, used to calibrate the depth parameter `γ`.
   - Confounders (communication ability, question draw, interviewer variation, referrals, luck) are documented explicitly rather than absorbed into the score.

## MVP Exclusions

The following are explicitly out of scope for the MVP:

- OCR or image-based PDF parsing
- Automated taxonomy clustering (HDBSCAN or LLM-based auto-generation)
- Automated taxonomy migration or score-recalculation triggers
- Supervised fine-tuning of embedding weights
- Recency weighting and interview-round-criticality weighting
- Institutional/cohort dashboards and multi-university support

## Installation

```bash
git clone <repository_url>
cd prepline

# Create and activate a virtual environment
python -m venv .venv

# Windows
.\.venv\Scripts\Activate.ps1

# Linux / macOS
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

**Requirements:** Python 3.10+, PyTorch, sentence-transformers, pdfplumber, pandas, numpy, scikit-learn.

## Usage

```bash
# Ingest and validate Amazon SDE-1 interview reports
python -m pipeline.interview_parser --company Amazon --role SDE-1

# Process a syllabus and calculate coverage
python -m pipeline.scoring --syllabus data/raw/syllabi/sample_syllabus.pdf
```

## Project Status

| Sprint | Phase(s) | Description | Status |
|---|---|---|---|
| 1 | Phase 1 | Environment & folder scaffolding | Completed |
| 1 | Phase 2 | Amazon SDE-1 interview dataset ingestion | Pending |
| 2 | Phase 3 | Versioned taxonomy definition (`taxonomy_v1.0.json`) | Pending |
| 3 | Phases 4–6 | Two-pass NLP abstraction, local embeddings, credit mapper | Pending |
| 4 | Phases 7–8 | Syllabus parsing & depth modeling | Pending |
| 5 | Phases 9–12 | Scoring engine & priority gap ranking | Pending |
| 6 | Phase 13 | Ground-truth benchmark & NLP evaluation | Pending |
| 7 | Phases 14–15 | Backend API & dashboard | Pending |
| 8 | Phase 16 | Pilot outcome validation & gamma calibration | Pending |

An optional, time-permitting extension (Sprint 9: DSA prerequisite graph and study roadmap generation) is scoped separately and is only attempted once Sprints 1–8 above are complete, benchmarked, and stable.