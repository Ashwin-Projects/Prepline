# PREPLINE results v1.2 — core course syllabi (vs v1.1 and v1.0)

`results/amazon_sde1_v1.2_course_syllabi.json`, syllabus `VIT_CSE_2024_25_courses`: the official 26-course VIT core,
supplied as individual course syllabus PDFs (`data/raw/syllabi/B[CM]*.pdf`, 27 files), scored as one combined syllabus
under `config/scoring_v1.2.json`. `results/amazon_sde1_v1.0.json`, `results/amazon_sde1_v1.1.json` and
`CHANGES_v1.1.md` are unchanged.

> **Revisions (owner-approved overwrites of v1.2), all on 2026-10-22.**
> 1. The allowlist was extended from 20 to the official 26 courses. The 20-course run (S_comp 88.7456, 162 units) is at
>    commit `060996c`.
> 2. Then 22 readable courses were scored (S_comp 89.8072, 177 units), at commit `b0e1238`.
> 3. Now BCSE101E, BCSE102L and BCSE103E are read from manual transcriptions (this run).

## Read this first

- **25 of the 26 core courses are scored. BCSE203E is not supplied.**
- **3 courses come from manual transcriptions, not PDF text.** BCSE101E, BCSE102L and BCSE103E are Microsoft
  Print-to-PDF files whose text is drawn as vector outlines, so they have no text layer. Claude transcribed the rendered
  pages into `data/raw/syllabi/transcribed/<CODE>.txt`. The parser uses a transcription only when a PDF has no text,
  and the result marks those courses and files `text_source: "manual_transcription"`. The transcriptions have not been
  checked against the PDFs by a person yet. One known gap: BCSE102L Module 4's last line is clipped in the source.
  The BCSE101E and BCSE103E "ETH"/"ELA" file pairs are byte-identical, so each course is read once and the copy is
  dropped as a duplicate.
- **The runs barely overlap.** v1.0 scored 66 text-layer courses of the full programme PDF (mostly electives and ECE).
  v1.1 scored 3 of them: BCSE102P, BMAT205L, BCSE203E. v1.2 shares only BCSE102P and BMAT205L with v1.0 and v1.1, and
  reads them from separate course PDFs. So the S_comp differences come from different syllabus inputs, not from one
  curriculum getting better.
- **S_comp 88.77 is driven by a 9-skill scoring universe.** The interview side is unchanged from v1.1:
  18 reports, 46 included questions, 9 granular skills with I(t) > 0. Each skill inherits the coverage of its
  high-level parent, and every one of those parents is covered with measured depth, so every universe topic has
  coverage between 0.85 and 0.93.
- **Some of the matches behind S_comp are wrong (see "Mapping quality").** For example, `dsa.dp` is covered by
  Computer Architecture and Compiler Design modules while DAA's DP module matches nothing. `system_design.messaging`
  is "present" only because of Java "IO Streams".
- **Config v1.2 differs from v1.1 only in the core allowlist** (and its source note). τ = 0.50, γ = 0.5, the depth
  reference values, MIN_REPORTS = 15, semester weeks = 15, taxonomy v1.0 and the embedding model are identical
  (test-guarded in `evaluation/test_config.py`).

## Headline numbers

| Metric | v1.0 | v1.1 (3 courses) | v1.2 (core course syllabi) |
|---|---|---|---|
| S_comp | 51.538 | 60.3657 | **88.7653** |
| Report count | 21 | 18 | 18 |
| Scoring universe (topics with I(t) > 0) | 21 | 9 | 9 |
| Runtime (s) | 1050.9 | 450.9 | 92.5 |

Compared with the previous 22-course revision (89.8072), S_comp fell by 1.04. The linked-list skill has the highest
importance (I = 0.222), and its parent `dsa.linked_lists` is now also matched by three BCSE102L modules: Pointers 4 h,
Structure and Union 2 h, and Overview of OOP 5 h. Their short hours pull the parent's mean depth from 3.70 to 3.29, so
coverage falls from 0.918 to 0.879. The OOP-overview match is doubtful (see "Mapping quality").

## Courses, modules and topics scored

| | v1.0 | v1.1 | v1.2 |
|---|---|---|---|
| Syllabus input | programme PDF (213 pages) | programme PDF (213 pages) | 27 course PDFs (45 pages; 10 pages without a text layer, read from 3 transcriptions) |
| Courses scored | 66 | 3 | 25 of 26 core (16 course groups); 2 duplicate files dropped |
| Units scored | 303 | 17 | 201 = 113 theory modules + 88 lab units (86 experiments + 2 embedded lab blocks) |
| Units matching ≥ 1 topic | 116 | 6 | 83 (65 theory, 18 lab) |
| Body-less modules skipped | – | – | 13 (Module 8 "Contemporary Issues" of every BCSE2xx/3xx theory course and BMAT205L) |
| Topics present (of 83) | 58 | 22 | 80 (35 matched directly + 45 granular inheriting from them) |
| Topics absent | 25 | 61 | 3: `system_design.load_balancing` (+ `.algorithms`), `system_design.distributed_consensus` |

The 16 course groups scored:
- **Theory + lab:** BCSE102 Structured and Object-Oriented Programming, BCSE202 DSA, BCSE204 DAA, BCSE301 Software
  Engineering, BCSE302 Database Systems, BCSE303 Operating Systems, BCSE307 Compiler Design, BCSE308 Computer
  Networks, BCSE309 Cryptography and Network Security.
- **Embedded theory + lab in one syllabus (E):** BCSE101 Computer Programming: Python, BCSE103 Computer Programming: Java.
- **Theory only:** BCSE205 Computer Architecture and Organization, BCSE304 Theory of Computation, BCSE305 Embedded
  Systems, BCSE306 Artificial Intelligence, BMAT205 Discrete Mathematics and Graph Theory.

## Depth: measured vs fallback

| | v1.0 | v1.1 | v1.2 |
|---|---|---|---|
| All 83 topics | 58 measured / 25 fallback | 22 measured / 61 fallback | 80 measured / 3 fallback |
| Present topics | 58 measured | 22 measured | 80 measured |
| Units with ≥ 1 depth signal | – | 17 / 17 | 201 / 201 |

The 3 fallback topics in v1.2 are the 3 absent system-design topics. Every present topic has measured depth.

Where depth comes from in v1.2:
- **Theory modules (L files):** `unit_hours` from the module header (1–10 h). The L files have no practical periods,
  so their modules carry no lab hours.
- **Lab experiments (P files):** `lab_hours` = the course's lab hours ÷ its experiment count. That is 30 h for the
  BCSE2xx/3xx labs (2.5–5 h per experiment) and 60 h for BCSE102P (7.5 h per experiment). `lab_count` is the experiment
  count (6–12), added once per (topic, lab course).
- **Embedded E courses (BCSE101E, BCSE103E):** this is the existing embedded behaviour. Their 60 lab hours are spread
  over all 8 units (7 theory modules + 1 "Indicative Experiments" block), 7.5 h each, so their theory modules carry a
  lab signal too. The lab block is one unit, not split into experiments. Noted in the backlog.
- **Effect of the lab signals:** 15 of the 35 directly matched topics are matched by both theory and lab units. The lab
  signals lowered depth for 5 of them and raised it for 10, with a mean change of +0.09 on the 1–5 scale. No topic is
  present through a lab alone.

## Top-10 priority gaps, side by side

v1.1 and v1.2 have 9 universe topics, so they list 9 gaps.

| Rank | v1.0 topic | gap | v1.1 topic | gap | v1.2 topic | gap (I · (1 − cov)) |
|---|---|---|---|---|---|---|
| 1 | Heaps and Priority Queues (`dsa.heaps`) | 0.0952 | Monotonic Stack and Queue (`dsa.stacks_queues.monotonic_stack`) | 0.1111 | Linked List Manipulation & Cycle Detection (`dsa.linked_lists.traversal_reversal`) | 0.0269 (0.222 · 0.121) |
| 2 | Shortest Path Algorithms (`dsa.graphs.shortest_path`) | 0.0762 | Grid Path DP (`dsa.dp.grid`) | 0.0778 | Monotonic Stack and Queue (`dsa.stacks_queues.monotonic_stack`) | 0.0133 |
| 3 | Grid Path DP (`dsa.dp.grid`) | 0.0667 | Top K Elements (`dsa.heaps.top_k`) | 0.0556 | Lowest Common Ancestor (`dsa.trees.lowest_common_ancestor`) | 0.0110 |
| 4 | Top K Elements (`dsa.heaps.top_k`) | 0.0476 | Binary Search (`dsa.sorting_searching.binary_search`) | 0.0333 | Shortest Path Algorithms (`dsa.graphs.shortest_path`) | 0.0094 |
| 5 | Message Queues (`system_design.messaging`) | 0.0476 | Lowest Common Ancestor (`dsa.trees.lowest_common_ancestor`) | 0.0122 | Top K Elements (`dsa.heaps.top_k`) | 0.0085 |
| 6 | Lowest Common Ancestor (`dsa.trees.lowest_common_ancestor`) | 0.0302 | Shortest Path Algorithms (`dsa.graphs.shortest_path`) | 0.0097 | Grid Path DP (`dsa.dp.grid`) | 0.0057 |
| 7 | Monotonic Stack and Queue (`dsa.stacks_queues.monotonic_stack`) | 0.0269 | Binary Search Trees (`dsa.trees.bst`) | 0.0049 | Binary Search (`dsa.sorting_searching.binary_search`) | 0.0047 |
| 8 | Linked List Manipulation (`dsa.linked_lists.traversal_reversal`) | 0.0167 | Tree Traversals (`dsa.trees.traversal`) | 0.0036 | Binary Search Trees (`dsa.trees.bst`) | 0.0044 |
| 9 | Binary Search (`dsa.sorting_searching.binary_search`) | 0.0125 | Linked List Manipulation (`dsa.linked_lists.traversal_reversal`) | 0.0 | Tree Traversals (`dsa.trees.traversal`) | 0.0033 |
| 10 | Sorting and Searching (`dsa.sorting_searching`) | 0.0123 | – | – | – | – |

In v1.2 no universe topic is uncovered: the largest gap is 0.027, against 0.111 in v1.1. The ranking mostly follows
interview importance I(t), because coverage is nearly flat (0.85–0.93). Where each v1.2 gap's coverage comes from (the
inherited parent and the units matching it):

| Universe topic | Parent | Parent depth | Units matching the parent |
|---|---|---|---|
| linked_lists.traversal_reversal | `dsa.linked_lists` | 3.29 | BCSE202L M2; BCSE202P exp 3, 6; BCSE102P exp 3; BCSE102L M3, M4, M5 |
| stacks_queues.monotonic_stack | `dsa.stacks_queues` | 3.30 | BCSE202L M2; BCSE202P exp 1, 2 |
| trees.lowest_common_ancestor / bst / traversal | `dsa.trees` | 3.51 | 14 units in BCSE202, 204, 302, 304, 306, 307, BMAT205, BCSE103E (lab block) |
| graphs.shortest_path | `dsa.graphs` | 3.44 | 11 units in BCSE202, 204, 205, 302, 307, BMAT205 |
| heaps.top_k | `dsa.heaps` | 3.00 | BCSE202L M7 only |
| dp.grid | `dsa.dp` | 3.80 | **BCSE205L M4 (memory systems), BCSE307L M7 (parallelism)**: spurious matches; see below |
| sorting_searching.binary_search | `dsa.sorting_searching` | 3.10 | 7 units in BCSE202, 204, 306 |

## Mapping quality (read before quoting S_comp)

- **Concepts are compared only with each taxonomy node's description, never its name.** BCSE204L Module 2
  "Design Paradigms: Dynamic Programming, Backtracking and Branch & Bound" extracts the concept "dynamic programming",
  but it scores 0.450 against `dsa.dp`'s description ("Optimization via overlapping subproblems, optimal substructure,
  memoization, …"), below τ = 0.50. With the node name prepended it would score 0.731. Instead, `dsa.dp` is matched at
  0.504 by Computer Architecture Module 4 and 0.503 by Compiler Design Module 7. DAA's entire lab (11 experiments) also
  matches nothing except string matching.
- **New doubtful matches from the programming courses:**
  - Module 1/2 of BCSE101E, BCSE102L and BCSE103E ("Data Types", "Reserved words", "Variables") match `dbms.sql` and
    `dbms.nosql`.
  - BCSE103E Module 6 "IO Streams and Files" and its lab block match `system_design.messaging`, which makes messaging
    and pub/sub "present".
  - BCSE102L Module 5 "Overview of Object-Oriented Programming" matches `dsa.linked_lists`.
- **118 of 201 units match no topic**, partly because the taxonomy has no node for them. By course:
  - Software Engineering 16 of 17 unmatched, DAA 13 of 18, Compiler Design 13 of 17, Cryptography 11 of 17,
    OS 10 of 19, Structured/OO Programming (L + P) 9 of 16, Networks 9 of 16.
  - Theory of Computation 6 of 7, Python 6 of 8, Java 4 of 8, Discrete Mathematics 4 of 7.
- Other matches to check: BCSE202L Module 1 "Algorithm Analysis" matches `dbms.nosql`, `dbms.sql` and
  `dbms.normalization`.
- None of this is changed in v1.2: τ, the taxonomy and the matcher are frozen. The node-name issue is in
  `docs/BACKLOG.md` as an owner decision. The Phase 13 benchmark (`evaluation/benchmark/`) will measure it.

## Unmapped terms

| | v1.0 | v1.1 | v1.2 |
|---|---|---|---|
| Distinct terms | 4868 | 282 | 1305 |
| … syllabus / interview | 4784 / 89 | 232 / 50 | 1258 / 50 |
| Total occurrences | 7859 | 335 | 1631 |
| Top terms | module (303), 2022 (49), annexure (49), board (39), academic council (38), … | javascript (3), article (2), aside elements (2), … | introduction (18), types (10), functions (9), implementation (9), applications (8), algorithm (7), develop (7), multi (7), non (7), overview (7) |

The v1.0 page and approval boilerplate (module, annexure, academic council, proceedings) is gone. In v1.2 the
running page lines are stripped before parsing and empty modules are skipped. The remaining top terms are generic
syllabus verbs and nouns. The 50 interview terms are the same as in v1.1 (unchanged interview data).

## What changed in the pipeline for v1.2

| Change | Where | Effect on this run |
|---|---|---|
| Config v1.2: core allowlist = the official 26 core courses | `config/scoring_v1.2.json` | 25 courses kept, 2 duplicate files dropped, 1 allowlisted missing (BCSE203E) |
| Combined syllabus from many PDFs (`parse_syllabus_pdfs`), units tagged with `course_group` / `component` / `source_file`; unreadable files go to `file_errors` | `pipeline/syllabus_parser.py` | One syllabus from 27 files; 0 file errors |
| Manual transcription for a PDF without a text layer (`transcribed/<CODE>.txt`, `#` comment lines ignored, `text_source` recorded) | parser + runner (`--transcriptions-dir`, default `<pdf-dir>/transcribed`) | BCSE101E, BCSE102L, BCSE103E scored (24 units) |
| Text extraction with `x_tolerance=1.5` | parser | Words no longer glued ("DataStructuresand" → "Data Structures and"); 114 tokens recovered in the first 16 files checked |
| VIT running page lines stripped | parser | Page headers and footers no longer fall inside modules that cross a page break |
| Incomplete L-T-P-C row accepted, values left blank (`ltpc_status: "incomplete"`) | parser | BCSE205L (only "3 0" in its text layer) is scored instead of silently dropped |
| Lab-only course → one unit per experiment; lab hours spread across experiments; `lab_count` once per (topic, course) | parser + `pipeline/scoring.py` | 86 experiment units; no lab hours on L-file theory modules |
| Body-less modules skipped and listed | parser | 13 Module-8 headers not mapped (`skipped_modules`) |
| Runner: `--pdf` (repeatable), `--pdf-dir` + `--glob`, `--syllabus-id`; per-course unit log | `evaluation/run_full_pipeline.py` | Run with `--glob "B[CM]*.pdf"`: includes BMAT205L, excludes the programme PDF (`B.Tech…`) |

## Runtime

92.5 s (parse 91.1 s, importance 1.4 s), against 450.9 s for v1.1 and 1050.9 s for v1.0. The 22 text-layer course PDFs
parse in about 17 s. Most of the rest is spent extracting the 5 vector-outline PDFs (about 2,700 curves per page)
before their transcriptions are used.
