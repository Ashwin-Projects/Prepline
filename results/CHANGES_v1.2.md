# PREPLINE results v1.2 — core course syllabi (vs v1.1 and v1.0)

`results/amazon_sde1_v1.2_course_syllabi.json`, syllabus `VIT_CSE_2024_25_courses`: the 20 individual VIT course
syllabus PDFs (`data/raw/syllabi/BCSE*.pdf`, 12 theory + 8 lab) scored as one combined syllabus under
`config/scoring_v1.2.json`. `results/amazon_sde1_v1.0.json`, `results/amazon_sde1_v1.1.json` and `CHANGES_v1.1.md`
are unchanged.

## Read this first

- **The three runs share no courses.** v1.0 scored 66 text-layer courses of the full programme PDF (mostly electives
  and ECE). v1.1 scored 3 of them: BCSE102P, BMAT205L, BCSE203E. v1.2 scores the owner's 20 core course PDFs
  (BCSE202–BCSE309), none of which was readable in the programme PDF. So the S_comp differences below come from
  different syllabus inputs, not from one curriculum getting better, and should not be read as a trend.
- **v1.2 is the first run that scores the core curriculum.** All 20 files have a text layer on every page
  (32 pages in all), and every allowlisted core course is present and kept.
- **S_comp 88.75 is driven by a 9-skill scoring universe.** The interview side is unchanged from v1.1:
  18 reports, 46 included questions, 9 granular skills with I(t) > 0. Each skill inherits the coverage of its
  high-level parent (trees, graphs, linked lists, stacks/queues, heaps, dp, sorting/searching). The DSA course
  (BCSE202L + BCSE202P) now covers every one of those parents with measured depth, so every universe topic has
  coverage between 0.85 and 0.93.
- **Some of the matches behind S_comp are wrong (see "Mapping quality").** `dsa.dp`, the parent of the
  grid-DP gap, gets its coverage from Computer Architecture and Compiler Design modules. Meanwhile DAA's actual
  Dynamic Programming module matches nothing. Fixing that changes how topics are matched (τ is frozen), so it is
  logged in the backlog and not changed here.
- **Config v1.2 differs from v1.1 only in the core allowlist** (and its source note). τ = 0.50, γ = 0.5, the depth
  reference values, MIN_REPORTS = 15, semester weeks = 15, taxonomy v1.0 and the embedding model are identical
  (test-guarded in `evaluation/test_config.py`).

## Headline numbers

| Metric | v1.0 | v1.1 (3 courses) | v1.2 (core course syllabi) |
|---|---|---|---|
| S_comp | 51.538 | 60.3657 | **88.7456** |
| Report count | 21 | 18 | 18 |
| Scoring universe (topics with I(t) > 0) | 21 | 9 | 9 |
| Runtime (s) | 1050.9 | 450.9 | 17.8 |

## Courses, modules and topics scored

| | v1.0 | v1.1 | v1.2 |
|---|---|---|---|
| Syllabus input | programme PDF (213 pages) | programme PDF (213 pages) | 20 course PDFs (32 pages) |
| Courses scored | 66 | 3 | 20 (12 courses: 8 theory + lab pairs, 4 theory only) |
| Units scored | 303 | 17 | 162 = 84 theory modules + 78 lab experiments |
| Units matching ≥ 1 topic | 116 | 6 | 67 (52 theory, 15 lab) |
| Body-less modules skipped | – | – | 12 (Module 8 "Contemporary Issues" of every theory course) |
| Topics present (of 83) | 58 | 22 | 78 (34 matched directly + 44 granular inheriting from them) |
| Topics absent | 25 | 61 | 5: `system_design.load_balancing` (+ `.algorithms`), `system_design.messaging` (+ `.pub_sub`), `system_design.distributed_consensus` |

Course pairs (theory + lab): BCSE202 DSA, BCSE204 DAA, BCSE301 Software Engineering, BCSE302 Database Systems,
BCSE303 Operating Systems, BCSE307 Compiler Design, BCSE308 Computer Networks, BCSE309 Cryptography and Network Security.
Theory only: BCSE205 Computer Architecture and Organization, BCSE304 Theory of Computation, BCSE305 Embedded Systems,
BCSE306 Artificial Intelligence.

## Depth: measured vs fallback

| | v1.0 | v1.1 | v1.2 |
|---|---|---|---|
| All 83 topics | 58 measured / 25 fallback | 22 measured / 61 fallback | 78 measured / 5 fallback |
| Present topics | 58 measured | 22 measured | 78 measured |
| Units with ≥ 1 depth signal | – | 17 / 17 | 162 / 162 |

The 5 fallback topics in v1.2 are the 5 absent system-design topics. Every present topic has measured depth.

Where depth comes from in v1.2 (no double counting):
- **Theory modules:** `unit_hours` from the module header (3–10 h; each course totals 45 lecture hours). The theory
  files have no practical periods, so they carry no lab hours.
- **Lab experiments:** `lab_hours` = the course's 30 lab hours ÷ its experiment count (2.5–5 h each). `lab_count` is
  the experiment count (6–12), added once per (topic, lab course) however many of that course's experiments match
  the topic.
- **Effect of the lab signals:** 13 of the 34 directly matched topics are matched by both a theory module and a
  lab experiment. The lab signals lowered depth for 6 of them and raised it for 7, with a mean change of −0.04 on
  the 1–5 scale. No topic is present through a lab alone. Depth is a mean of the normalised signals, so a short
  experiment (e.g. 3 h → 0.3) can pull down a topic that a 7-hour module alone would score at 0.7.

## Top-10 priority gaps, side by side

v1.1 and v1.2 have 9 universe topics, so they list 9 gaps.

| Rank | v1.0 topic | gap | v1.1 topic | gap | v1.2 topic | gap (I · (1 − cov)) |
|---|---|---|---|---|---|---|
| 1 | Heaps and Priority Queues (`dsa.heaps`) | 0.0952 | Monotonic Stack and Queue (`dsa.stacks_queues.monotonic_stack`) | 0.1111 | Linked List Manipulation & Cycle Detection (`dsa.linked_lists.traversal_reversal`) | 0.0266 (0.222 · 0.120) |
| 2 | Shortest Path Algorithms (`dsa.graphs.shortest_path`) | 0.0762 | Grid Path DP (`dsa.dp.grid`) | 0.0778 | Monotonic Stack and Queue (`dsa.stacks_queues.monotonic_stack`) | 0.0133 |
| 3 | Grid Path DP (`dsa.dp.grid`) | 0.0667 | Top K Elements (`dsa.heaps.top_k`) | 0.0556 | Lowest Common Ancestor (`dsa.trees.lowest_common_ancestor`) | 0.0113 |
| 4 | Top K Elements (`dsa.heaps.top_k`) | 0.0476 | Binary Search (`dsa.sorting_searching.binary_search`) | 0.0333 | Shortest Path Algorithms (`dsa.graphs.shortest_path`) | 0.0094 |
| 5 | Message Queues (`system_design.messaging`) | 0.0476 | Lowest Common Ancestor (`dsa.trees.lowest_common_ancestor`) | 0.0122 | Top K Elements (`dsa.heaps.top_k`) | 0.0085 |
| 6 | Lowest Common Ancestor (`dsa.trees.lowest_common_ancestor`) | 0.0302 | Shortest Path Algorithms (`dsa.graphs.shortest_path`) | 0.0097 | Grid Path DP (`dsa.dp.grid`) | 0.0057 |
| 7 | Monotonic Stack and Queue (`dsa.stacks_queues.monotonic_stack`) | 0.0269 | Binary Search Trees (`dsa.trees.bst`) | 0.0049 | Binary Search (`dsa.sorting_searching.binary_search`) | 0.0047 |
| 8 | Linked List Manipulation (`dsa.linked_lists.traversal_reversal`) | 0.0167 | Tree Traversals (`dsa.trees.traversal`) | 0.0036 | Binary Search Trees (`dsa.trees.bst`) | 0.0045 |
| 9 | Binary Search (`dsa.sorting_searching.binary_search`) | 0.0125 | Linked List Manipulation (`dsa.linked_lists.traversal_reversal`) | 0.0 | Tree Traversals (`dsa.trees.traversal`) | 0.0034 |
| 10 | Sorting and Searching (`dsa.sorting_searching`) | 0.0123 | – | – | – | – |

In v1.2 no universe topic is uncovered: the largest gap is 0.027, against 0.111 in v1.1. The ranking now mostly
follows interview importance I(t), because coverage is nearly flat (0.85–0.93). Where each v1.2 gap's coverage
comes from (the inherited parent and the units matching it):

| Universe topic | Parent | Parent depth | Units matching the parent |
|---|---|---|---|
| linked_lists.traversal_reversal | `dsa.linked_lists` | 3.30 | BCSE202L M2; BCSE202P exp 3, 6 |
| stacks_queues.monotonic_stack | `dsa.stacks_queues` | 3.30 | BCSE202L M2; BCSE202P exp 1, 2 |
| trees.lowest_common_ancestor / bst / traversal | `dsa.trees` | 3.48 | 12 units in BCSE202, 204, 302, 304, 306, 307 |
| graphs.shortest_path | `dsa.graphs` | 3.44 | 9 units in BCSE202, 204, 205, 302, 307 |
| heaps.top_k | `dsa.heaps` | 3.00 | BCSE202L M7 only |
| dp.grid | `dsa.dp` | 3.80 | **BCSE205L M4 (memory systems), BCSE307L M7 (parallelism)**: spurious matches; see below |
| sorting_searching.binary_search | `dsa.sorting_searching` | 3.10 | 7 units in BCSE202, 204, 306 |

## Mapping quality (read before quoting S_comp)

- **Concepts are compared only with each taxonomy node's description, never its name.** BCSE204L Module 2
  "Design Paradigms: Dynamic Programming, Backtracking and Branch & Bound" extracts the concept "dynamic programming",
  but it scores 0.450 against `dsa.dp`'s description ("Optimization via overlapping subproblems, optimal substructure,
  memoization, …"), below τ = 0.50. With the node name prepended it would score 0.731. Instead, `dsa.dp` is matched at
  0.504 by Computer Architecture Module 4 and 0.503 by Compiler Design Module 7. DAA's entire lab (11 experiments) also
  matches nothing except string matching. The grid-DP gap is therefore "covered" by the wrong courses.
- **95 of 162 units match no topic**, partly because the taxonomy has no node for them. By course: Software Engineering
  16 of 17 units unmatched, DAA 13 of 18, Compiler Design 13 of 17, Cryptography 11 of 17, OS 10 of 19, Networks 9 of 16.
- Other matches to check: BCSE202L Module 1 "Algorithm Analysis" matches `dbms.nosql`, `dbms.sql` and
  `dbms.normalization`.
- None of this is changed in v1.2: τ, the taxonomy and the matcher are frozen. The node-name issue is in
  `docs/BACKLOG.md` as an owner decision.

## Unmapped terms

| | v1.0 | v1.1 | v1.2 |
|---|---|---|---|
| Distinct terms | 4868 | 282 | 1060 |
| … syllabus / interview | 4784 / 89 | 232 / 50 | 1013 / 50 |
| Total occurrences | 7859 | 335 | 1249 |
| Top terms | module (303), 2022 (49), annexure (49), board (39), academic council (38), … | javascript (3), article (2), aside elements (2), … | introduction (16), implementation (9), applications (8), develop (7), algorithm (6), implement (6), non (6), types (6), design (5), overview (5) |

The v1.0 page and approval boilerplate (module, annexure, academic council, proceedings) is gone. In v1.2 the
running page lines are stripped before parsing and empty modules are skipped. The remaining top terms are generic
syllabus verbs and nouns. The 50 interview terms are the same as in v1.1 (unchanged interview data).

## What changed in the pipeline for v1.2

| Change | Where | Effect on this run |
|---|---|---|
| Config v1.2: core allowlist = the 20 supplied course codes | `config/scoring_v1.2.json` | 20 courses kept, 0 dropped, 0 allowlisted missing |
| Combined syllabus from many PDFs (`parse_syllabus_pdfs`), units tagged with `course_group` / `component` / `source_file` | `pipeline/syllabus_parser.py` | One syllabus from 20 files; 0 file errors |
| Text extraction with `x_tolerance=1.5` | parser | Words no longer glued ("DataStructuresand" → "Data Structures and"); 114 tokens recovered in the first 16 files checked |
| VIT running page lines stripped | parser | Page headers and footers no longer fall inside modules that cross a page break |
| Incomplete L-T-P-C row accepted, values left blank (`ltpc_status: "incomplete"`) | parser | BCSE205L (only "3 0" in its text layer) is scored instead of silently dropped |
| Lab-only course → one unit per experiment; lab hours spread across experiments; `lab_count` once per (topic, course) | parser + `pipeline/scoring.py` | 78 experiment units; no lab hours on theory modules |
| Body-less modules skipped and listed | parser | 12 Module-8 headers not mapped (`skipped_modules`) |
| Runner: `--pdf` (repeatable), `--pdf-dir` + `--glob`, `--syllabus-id`; per-course unit log | `evaluation/run_full_pipeline.py` | Programme PDF excluded by the `BCSE*.pdf` glob |

## Runtime

17.8 s (parse 17.0 s, importance 0.7 s), against 450.9 s for v1.1 and 1050.9 s for v1.0. Nearly all of the
difference is input size: 32 small text pages instead of the 213-page programme PDF, whose 67 scanned pages were
slow to extract.
