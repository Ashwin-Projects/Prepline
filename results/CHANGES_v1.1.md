# PREPLINE results v1.0 → v1.1

## Read this first

- **v1.0's S_comp (51.54) was driven by non-core courses.** v1.0 scored all 66 course syllabi that have a text layer (303 modules): mostly electives (data science, IoT, security, blockchain) and ECE courses (digital systems, microprocessors). The core CS syllabi (DSA, DAA, OS, DBMS, CN, ...) contributed nothing, because their pages are scanned images with no text layer.
- **v1.1 covers only 3 core courses, because of scanning.** v1.1 keeps only allowlisted core CS courses. Just 3 have a readable syllabus: BCSE102P Structured and Object-Oriented Programming Lab, BMAT205L Discrete Mathematics and Graph Theory, and BCSE203E Web Programming. The other 23 allowlisted core courses are listed in the PDF's catalogue, but their syllabus pages have no text layer: BCSE101E, BCSE102L, BCSE103E, BCSE202L, BCSE202P, BCSE204L, BCSE204P, BCSE205L, BCSE301L, BCSE301P, BCSE302L, BCSE302P, BCSE303L, BCSE303P, BCSE304L, BCSE305L, BCSE306L, BCSE307L, BCSE307P, BCSE308L, BCSE308P, BCSE309L, BCSE309P. In all, 67 of 213 pages have no text layer (listed in `text_layer.pages_without_text` in amazon_sde1_v1.1.json).
- **Do not read v1.1's S_comp (60.37) as a curriculum measure, and do not compare it with v1.0.** It is higher than v1.0 despite scoring fewer courses: the scoring universe shrank to 9 granular skills (items 2 and 3), and those skills inherit coverage from high-level parents (trees, graphs, linked lists) that the Discrete Mathematics and OOP Lab syllabi happen to cover. It will become meaningful once readable core syllabi are supplied.
- **Next step (separate):** text-layer or offline-OCR'd PDFs of the Discipline Core syllabi will be supplied and scored as their own results version. `results/amazon_sde1_v1.0.json` is kept unchanged.
- **Frozen values unchanged:** tau = 0.50, gamma = 0.5, depth reference values, MIN_REPORTS = 15 and taxonomy v1.0 are now read from `config/scoring_v1.0.json`.

## Headline numbers

| Metric | v1.0 | v1.1 | Change |
|---|---|---|---|
| S_comp | 51.538 | 60.3657 | 8.8277 |
| Report count | 21 | 18 | -3 |
| Scoring universe (topics with I(t) > 0) | 21 | 9 | -12 |
| Runtime (s) | 1050.9 | 412.1 | -638.8 |

## Top-10 priority gaps, side by side

| Rank | v1.0 topic | v1.0 gap | v1.1 topic | v1.1 gap |
|---|---|---|---|---|
| 1 | Heaps and Priority Queues (`dsa.heaps`) | 0.0952 | Monotonic Stack and Queue (`dsa.stacks_queues.monotonic_stack`) | 0.1111 |
| 2 | Shortest Path Algorithms (`dsa.graphs.shortest_path`) | 0.0762 | Grid Path Dynamic Programming (`dsa.dp.grid`) | 0.0778 |
| 3 | Grid Path Dynamic Programming (`dsa.dp.grid`) | 0.0667 | Top K Elements and K-Way Merge (`dsa.heaps.top_k`) | 0.0556 |
| 4 | Top K Elements and K-Way Merge (`dsa.heaps.top_k`) | 0.0476 | Binary Search (`dsa.sorting_searching.binary_search`) | 0.0333 |
| 5 | Message Queues and Event-Driven Architecture (`system_design.messaging`) | 0.0476 | Lowest Common Ancestor (`dsa.trees.lowest_common_ancestor`) | 0.0122 |
| 6 | Lowest Common Ancestor (`dsa.trees.lowest_common_ancestor`) | 0.0302 | Shortest Path Algorithms (`dsa.graphs.shortest_path`) | 0.0097 |
| 7 | Monotonic Stack and Queue (`dsa.stacks_queues.monotonic_stack`) | 0.0269 | Binary Search Trees (`dsa.trees.bst`) | 0.0049 |
| 8 | Linked List Manipulation & Cycle Detection (`dsa.linked_lists.traversal_reversal`) | 0.0167 | Tree Traversals (`dsa.trees.traversal`) | 0.0036 |
| 9 | Binary Search (`dsa.sorting_searching.binary_search`) | 0.0125 | Linked List Manipulation & Cycle Detection (`dsa.linked_lists.traversal_reversal`) | 0.0 |
| 10 | Sorting and Searching (`dsa.sorting_searching`) | 0.0123 | – | – |

## What caused each change (sequential attribution)

Each row is a full pipeline run after one more item was applied, in this order; the deltas are relative to the row above, so an item's effect is measured on top of the items before it.

| Step | S_comp | Δ S_comp | Scoring universe | Entered top 10 | Left top 10 | Runtime (s) |
|---|---|---|---|---|---|---|
| v1.0 baseline | 51.538 | – | 21 | – | – | 1050.9 |
| Item 8 - performance (batch encode, cache) | 51.538 | 0.0 | 21 | – | – | 936.0 |
| Item 3 - interview filtering | 46.4298 | -5.1082 | 15 | `dsa.trees` | `dsa.sorting_searching` | 955.0 |
| Item 2 - node-type matching + inheritance | 75.2426 | 28.8128 | 9 | `dsa.trees.bst`, `dsa.trees.traversal` | `dsa.heaps`, `system_design.messaging`, `dsa.trees` | 844.4 |
| Item 1 - course segmentation, core allowlist | 60.3657 | -14.8769 | 9 | – | – | 472.0 |
| Item 4 - depth signals | 60.3657 | 0.0 | 9 | – | – | 451.5 |
| Item 5 - boilerplate stoplist | 60.3657 | 0.0 | 9 | – | – | 405.4 |

## Item by item

| Item | Change | Effect on v1.1 (measured run after run) |
|---|---|---|
| 8 Performance | Batch-encode each source's concepts; cache interview importance per (company, role, taxonomy version, config version, questions.csv SHA-256) | No output change (S_comp 51.538, every field identical); runtime 1116 s → 936 s |
| 3 Interview filtering | Exclude behavioral rounds, needs_review rows and rows without question_text (52 of 98 rows; see `data/processed/excluded_questions.csv`); report count = reports with ≥1 included question | Questions 98 → 46, reports 21 → 18 (density gate still passes, ≥15); S_comp 51.538 → 46.43; scoring universe 21 → 15 |
| 2 Node-type matching | Syllabus units match only high-level concepts, interview questions only granular skills; a granular skill inherits its nearest high-level ancestor's coverage (`coverage_source: inherited`) | S_comp 46.43 → 75.24; scoring universe 15 → 9 granular skills; topics present 58 → 74. All 46 granular nodes have a high-level ancestor (0 orphans) |
| 1 Course segmentation | Split the PDF into courses then modules; keep only the core CS allowlist; record pages without a text layer and allowlisted courses with no readable syllabus | Courses scored 66 → 3; modules 303 → 16; S_comp 75.24 → 60.37; runtime 844 s → 472 s (fewer modules, and each page's text is now extracted once instead of twice) |
| 4 Depth signals | lab_hours = course practical hours spread across its modules; unit_hours read from the module header line only | No change to S_comp, the top-10 gaps or measured/fallback counts. In v1.1 it only alters BCSE203E Web Programming (P = 4, 7 modules: lab_hours 60 → 8.57 per module), whose topics are outside the 9-skill scoring universe |
| 5 Boilerplate stoplist | Strip module/annexure/approved/academic council/proceedings/... plus dates, years and bare numbers from syllabus text before RAKE | No change to S_comp or the top-10 gaps; syllabus units matching ≥1 topic 4 → 5 |
| 6 Central config | All frozen constants and rules in `config/scoring_v1.0.json`, loaded once | No output change (values identical) |
| 7 Security | Upload filenames sanitised before joining paths (path traversal fixed) | API only; no result change |
| 10 Housekeeping | pydantic v2 `Field(examples=...)`; pytest under `# test` | No result change |

## Runtime

v1.0: 1050.9 s (re-measured baseline 1116.1 s). v1.1: 412.1 s, of which PDF text extraction is 411.1 s (`stage_timings_seconds`). The pdfplumber pass over the 213-page PDF now dominates.
