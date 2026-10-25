# Phase 2 / Phase 13 source review log

Review date: 2026-10-10
Scope: discovery and topic-level review of public interview-experience pages for research and taxonomy mapping.

## Important boundary

This log records source discovery and a topic-level summary based on publicly visible page content. It is not a legal opinion, does not grant permission to bulk-reproduce source text, and does not constitute independent human annotation of a benchmark row. Before a source is admitted to the production Phase 2 dataset, check its current terms, whether the report is independent, role/cohort fit, and whether its content may be stored for this use. For Phase 13, a source-backed mapping remains a candidate until a human reviewer verifies the exact source and label.

## Source candidates reviewed

| Source ID | Public page | Topic-level observations | Use in Phase 2 |
|---|---|---|---|
| SRC-AMZ-001 | https://leetcode.com/discuss/post/6414650/Amazon-SDE-1-Interview-Experience-or-February-2025-or-Offer-Received/ | Grid path/max-sum reasoning, Keys and Rooms (graph traversal), matrix problem, behavioral principles | Candidate; confirm distinct report and terms |
| SRC-AMZ-002 | https://leetcode.com/discuss/post/7344078/amazon-sde-1-interview-experience-dsa-ro-mxfs/ | Ladder-and-bricks variant (heap/greedy), Evaluate Division (weighted graph traversal), edge cases | Candidate; confirm distinct report and terms |
| SRC-AMZ-003 | https://leetcode.com/discuss/post/6915570/amazon-sde-1-interview-experience-2025-o-r3jt/ | Rotten Oranges (BFS), diagonal binary-tree traversal, Course Schedule/topological sort, low-level design | Candidate; confirm distinct report and terms |
| SRC-AMZ-004 | https://leetcode.com/discuss/post/6813913/amazon-sde-1-interview-experience-2025-o-p3fd/ | Low-level design, DSA coding rounds, complexity and modular design, behavioral discussion | Candidate; report includes linked edit; check overlap before counting |
| SRC-AMZ-005 | https://leetcode.com/discuss/post/6824103/ | Package/dependency installer design, dependency graph, cycle detection, topological order, Word Break variant (DFS/memoization/Trie/DP) | Candidate; confirm role and independent report |
| SRC-AMZ-006 | https://leetcode.com/discuss/post/7724048/ | Maximum-bombs graph reachability, greedy interval/placement problem, next-greater-element stack pattern | Candidate; confirm role and terms |
| SRC-AMZ-007 | https://leetcode.com/discuss/post/6347580/Amazon-or-SDE-1-fresher-or-India/ | Binary tree infection traversal, merge intervals, parking-lot object-oriented design | Candidate; confirm role and terms |
| SRC-AMZ-008 | https://leetcode.com/discuss/post/6606011/amazon-sde-1-interview-experience-27-mar-ermb/ | Parentheses/string processing, median of two sorted arrays, heap optimization, dynamic programming | Candidate; confirm source details and terms |
| SRC-AMZ-009 | https://leetcode.com/discuss/post/7136974/ | Large-number divisibility/string processing, arrays/number theory, behavioral question | Candidate; confirm role and terms |
| SRC-AMZ-010 | https://leetcode.com/discuss/post/7407012/sde-1-fresher-interview-experience-off-c-yfoq/ | Graph/priority queue, greedy prefix reasoning, interval overlap, subsequence DP, BFS | Candidate; confirm role and terms |
| SRC-AMZ-011 | https://leetcode.com/discuss/post/8471051/ | Binary search, dynamic programming, BFS, graph path/currency conversion, DSU, stack-based string decoding | Candidate; newer report; verify date and role fit |
| SRC-AMZ-012 | https://leetcode.com/discuss/post/1191068/Amazon-SDE-1-Interview-Experience/ | Graphs, trees, linked lists, arrays, OOP, behavioral questions | Candidate; older report; verify role/date fit |

## Taxonomy mapping suggestions (not benchmark labels)

The topic summaries above suggest likely mappings into taxonomy v1.1 such as:
- grid traversal / Rotten Oranges / tree infection -> graph traversal (BFS/DFS) or trees, depending on the exact problem;
- Keys and Rooms / Evaluate Division / Maximum Bombs -> graph traversal;
- Course Schedule / dependency installation -> directed graphs and topological sorting;
- Ladder-and-bricks / heap optimization -> heaps and greedy algorithms;
- Word Break -> dynamic programming, recursion/memoization, and possibly tries;
- Merge Intervals / interval overlap -> sorting and interval algorithms;
- Next Greater Element -> monotonic stack;
- Median of Two Sorted Arrays -> binary search;
- Currency conversion with repeated queries -> weighted graph / disjoint-set union;
- parking lot / package installer -> object-oriented design / low-level design;
- behavioral Leadership Principles -> outside the current technical taxonomy unless a separate behavioral taxonomy is added.

These are taxonomy mapping suggestions only. Where a report mentions a variant or multiple plausible concepts, annotators should label the specific concept actually tested, allow multi-labels only if the benchmark schema explicitly supports them, and record uncertainty instead of guessing.

## Phase 2 acceptance gate

Do not mark Phase 2 complete merely because 12 candidate URLs are listed. Independently review all report rows in `data/raw/interviews/amazon_sde1_interview_experiences_phase2.csv`; check for cross-posts, report independence, role and date fit, current terms, and eligibility. Only then count unique eligible reports toward the minimum of 15.

## Phase 13 acceptance gate

This log is not a substitute for 200+ human-reviewed, source-backed mappings. Populate `evaluation/ground_truth.csv` only after each row has a verifiable source and an actual reviewer/date. Keep synthetic candidates separate. Run metrics only on accepted labels, with the final test set untouched until the pipeline and threshold are frozen.


## Additional public-indexed sources checked (2026-10-10)

The following pages surfaced additional concrete topic summaries during a later search pass. They were used to add candidate rows to `evaluation/source_backed_mappings_for_review.csv`; none is cleared for bulk use and none of the new mappings is human-verified.

- https://www.geeksforgeeks.org/interview-experiences/amazon-interview-experience-for-sde-1-25/ — Copy List with Random Pointer; Validate BST variant.
- https://www.geeksforgeeks.org/interview-experiences/amazon-interview-experience-for-sde1/ — reverse string in chunks; set-bit counting; OS/DBMS/CN MCQ topics.
- https://www.geeksforgeeks.org/interview-experiences/amazon-interview-sde-1-interview-experience/ — BST from sorted array; row with maximum ones; next greater element; rotated-array binary search.
- https://www.geeksforgeeks.org/interview-experiences/amazon-interview-experience-sde-1-2/ — longest palindrome; sum tree; reverse list in groups; maximum-sum subsequence; top view; missing positive.
- https://www.geeksforgeeks.org/interview-experiences/amazon-interview-experience-sde-1-20/ — meeting rooms; top-k frequent elements.
- https://www.geeksforgeeks.org/interview-experiences/amazon-interview-experience-for-sde-1-on-campus/ — maximum units on a truck; minimum platforms; palindrome linked list; knight shortest path.
- https://www.geeksforgeeks.org/interview-experiences/amazon-interview-experience-on-campus-for-sde-1/ — coin-change DP; range-count queries; recurrence complexity; FIFO page replacement; networking and SQL fundamentals.

Source summaries were taken from public search-index excerpts. Before admission to Phase 2 or Phase 13, open each page, verify exact interpretation and role/date, check current source terms, and deduplicate cross-posts.
