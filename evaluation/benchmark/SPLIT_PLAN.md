# Benchmark split plan (Phase 13 part 2, not built yet)

**Goal:** split `labels_v1.0.csv` into 70 / 15 / 15 dev / val / test with a fixed seed. Splits are grouped so that no
course and no interview report has items in two splits.

## Groups

| source_type | group key | groups | rows | group sizes |
|---|---|---|---|---|
| syllabus | `course_group` = `course_or_report` minus its trailing L/P (BCSE202L + BCSE202P → BCSE202) | 12 | 162 | 7–19 units |
| interview | `report_id` (`course_or_report`) | 18 | 46 | 1–5 questions |

The theory and lab files of one course are a single group, because their units overlap in content (e.g. DSA
Module 2 and lab experiments 1–3). Splitting them would leak.

## Algorithm (deterministic)

1. Split each source_type separately, so dev, val and test all contain syllabus and interview items.
2. Sort the groups by key, then shuffle them with `random.Random(SEED)`, using the fixed constant
   `SEED = 20261022` in code.
3. Assign the groups in that order, each one going to the split furthest below its target row count
   (70 / 15 / 15 % of that source_type's rows). Ties go to test, then val, then dev.
4. Write `evaluation/benchmark/splits_v1.0.csv` (`item_id, source_type, group, split`) and never overwrite it.
   A new labelling or grouping gets a new version.

## Expected sizes and caveats

- Syllabus is about 113 / 24 / 24 units, but only 12 groups exist, so val and test are about 2 courses each. Their
  scores depend on which courses land there. Report the courses in each split next to every metric.
- Interview is about 32 / 7 / 7 questions. Val and test are small, so report counts and exact matches, not only
  percentages (one question is about 14 %).
- The achieved ratios deviate from 70/15/15 because whole groups move together. The builder prints the achieved rows
  and groups per split, and a test fails if any split of a source_type is empty.

## Usage rules

- **dev:** inspect errors and design matchers freely.
- **val:** compare matcher variants. Any change it motivates to a frozen value (τ, taxonomy) still needs owner approval
  and a new config version.
- **test:** scored once per frozen matcher version and reported. Never used for choices.

## Tests to write first (part 2)

1. The same seed gives identical splits.
2. No group appears in two splits.
3. Every row is assigned exactly once.
4. Each split has syllabus and interview rows.
5. Achieved row shares are within one group size of 70/15/15.
6. BCSE202L and BCSE202P land in the same split.
