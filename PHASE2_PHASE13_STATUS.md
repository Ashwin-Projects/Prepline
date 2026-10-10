# Prepline Phase 2 + Phase 13 Status

Updated: 2026-10-10 (source review pass)

## Latest work in this pass

- Added `evaluation/SOURCE_REVIEW_LOG.md` with 12 publicly discoverable interview-experience candidates, topic-level summaries, candidate taxonomy mapping suggestions, and explicit source/legal/deduplication caveats.
- Added `evaluation/source_backed_mappings_for_review.csv` with 202 unique source-linked topic-mapping candidates from publicly indexed interview reports. Every row remains `needs_human_review` and is excluded from benchmark metrics.
- Added `scripts/check_phase_readiness.py` and `scripts/validate_prepline_data.py` for fail-closed acceptance checks and schema/topic-reference validation.
- Added repository tests and `.github/workflows/validate-data.yml` so schema/taxonomy checks run on pushes and pull requests.
- Updated review CLI so approval decisions alone enter `ground_truth.csv`; rejections are recorded in `evaluation/review_decisions.csv`.

## Phase 2 — Dataset construction

Implemented in repository:
- Source-linked Amazon SDE-I interview experience discovery CSV with round/question-topic summaries and review fields.
- Official VIT CSE 2024-25 syllabus manifest with the official PDF URL and course-code scope.
- Extracted the Discipline Core course catalog from the user's available VIT syllabus PDF into `data/raw/syllabi/vit_cse_2024_2025_discipline_core_catalog.csv` (21 rows, printed page 2); added `data/raw/syllabi/README.md` with provenance and limitations.
- Downloader script that fetches the PDF from VIT's official host, validates the PDF signature, and prints SHA-256.
- Phase 2 README describing schema, source review, deduplication, legal-use checks, and ingestion expectations.
- Contributor intake template and guide for first-hand reports with explicit permission, cohort checks, and duplicate evidence.

Still required before Phase 2 can be marked complete:
- Confirm at least 15 independent, eligible Amazon SDE-I reports after cross-post/deduplication checks.
- Written permission or replacement with appropriately licensed/directly contributed sources is required before using the current LeetCode/GeeksforGeeks index as a production corpus; see `data/raw/interviews/SOURCE_TERMS_REVIEW.md`.
- Record permission basis, reviewer, date, and report-level deduplication evidence.
- Run the syllabus downloader locally, verify text-selectability, and preserve the original PDF at `data/raw/syllabi/VIT_CSE_2024_2025.pdf`.
- Parse reviewed sources into processed data while preserving provenance.

## Phase 13 — Ground-truth benchmark

Implemented in repository:
- Expanded taxonomy v1.1 (56 topic nodes); original v1.0 snapshot preserved.
- 392 synthetic candidate prompts in `evaluation/candidate_mappings_for_review.csv`, explicitly marked unverified.
- Empty `evaluation/ground_truth.csv` with provenance and human-review fields.
- Evaluation script comparing keyword overlap, TF-IDF, and sentence embeddings, using development/validation/test splits and validation-only threshold tuning.
- Documentation of benchmark requirements and limitations.
- A human review CLI to approve/reject candidates explicitly and write decisions into the ground-truth file without auto-approval.
- 78 additional CC BY 4.0 practice-question mapping candidates with attribution; still pending human verification.

Additional licensed candidate pool added in the latest pass:
- `evaluation/codeprep_mappings_for_review.csv` contains 78 question-to-topic candidates derived from the CodePrep Open Interview Questions dataset, whose published metadata declares CC BY 4.0; attribution and source details are documented in `data/raw/interviews/LICENSED_QUESTION_SOURCE.md`.
- These are practice questions, not candidate experience reports, and their taxonomy labels are machine-suggested; every row remains `needs_human_review`.

Still required before Phase 13 can be marked complete:
- Collect at least 200 source-backed examples permitted for this use and suitable for the benchmark.
- Have a human reviewer verify each text-to-topic mapping and fill reviewer/date/status fields.
- Ensure the final test split is untouched during model/threshold selection.
- Run the evaluation on verified examples and save/review metrics and per-topic errors.

## Important interpretation

File counts are not completion evidence by themselves. The repository now contains scaffolding, a public-source discovery index, and a licensed practice-question candidate pool, but both phases remain pending their explicit validation gates above. Do not present synthetic candidates as real interview questions or as manually verified ground truth.


## Final execution attempt (2026-10-10)

A further public-source research pass confirmed examples of topic summaries from publicly indexed Amazon SDE-1 experience pages, including graph traversal, trees, heaps, binary search, dynamic programming, strings, and linked lists. These remain candidates and must be verified against their source pages before acceptance. Examples reviewed during this pass include:
- https://leetcode.com/discuss/post/7344078/amazon-sde-1-interview-experience-dsa-ro-mxfs/
- https://leetcode.com/discuss/post/6915570/amazon-sde-1-interview-experience-2025-o-r3jt/
- https://leetcode.com/discuss/post/1191068/Amazon-SDE-1-Interview-Experience/
- https://leetcode.com/discuss/post/6414650/Amazon-SDE-1-Interview-Experience-or-February-2025-or-Offer-Received/
- https://www.geeksforgeeks.org/interview-experiences/amazon-interview-experience-for-sde-1-25/
- https://www.geeksforgeeks.org/interview-experiences/amazon-interview-experience-sde-1-2/

The official VIT PDF download was attempted from the current execution environment but could not be retrieved because outbound DNS/network access was unavailable. The user's library copy was available, so a 21-row Discipline Core catalog was extracted and committed. The original PDF binary is still not stored in the repository, and full syllabus text/topic extraction remains pending.

### Additional implementation pass (2026-10-10)

- Extracted the user's available VIT CSE 2024-25 syllabus PDF into a structured Discipline Core catalog at `data/raw/syllabi/vit_cse_2024_2025_discipline_core_catalog.csv` (21 rows, printed page 2). The original PDF binary is not committed, and this is not a full topic-level syllabus extraction.
- Expanded the source-linked mapping candidate list to 202 unique rows using publicly indexed interview reports. All remain `needs_human_review`; candidate count does not satisfy the manual-verification gate.
- Updated the evaluator to reject unreviewed labels by default and include per-topic diagnostics.

### Final status

**Not complete / not accepted yet.** No ground-truth rows have been promoted to verified, because a model-generated label cannot honestly be represented as a human reviewer’s approval. The 202 unique candidate mapping rows are for review only. Phase 2 sources also remain pending legal-use and independent-report checks. The readiness checker is intended to fail closed until these conditions are met.

To finish the remaining external/manual gates, a human reviewer with access to the original pages must:
1. Review current terms/permission and independence for at least 15 eligible interview reports and set review fields only when supported.
2. Download the official PDF locally using `python scripts/download_vit_syllabus.py`, validate text extraction, and commit the PDF only if permitted by its terms; otherwise keep the official source URL and record the access decision.
3. Verify at least 200 source-backed mappings one by one, mark them reviewed with a real reviewer identity/date, and ensure taxonomy labels are supported by each source.
4. Run `python scripts/check_phase_readiness.py`, fix any remaining gates, then run `python evaluation/evaluate_nlp.py --data evaluation/ground_truth.csv --taxonomy data/taxonomy/taxonomy_v1.1.json`. Review split integrity and save the resulting metrics only if all preconditions pass.


## Latest candidate expansion (2026-10-10)

The source-backed candidate pool now has 202 unique text/topic pairs across indexed public interview-experience pages. Rows remain explicitly unverified; some underlying interview reports discuss similar problems; row-level exact text/topic duplicates were removed, but report-level cross-posts and source independence still require review. This does not count as 200 accepted benchmark labels. The ground-truth CSV remains header-only.


Duplicate cleanup note (2026-10-10): 39 repeated raw-text/topic pairs were removed from the candidate pool, and 27 distinct source-linked candidates were added. The file now has 202 unique raw-text/topic pairs. All remain `needs_human_review`; this is a candidate pool, not accepted ground truth.


## Source terms review update (2026-10-10)

Reviewed current published terms for LeetCode and GeeksforGeeks. Both contain restrictions relevant to scraping/systematic compilation; the terms review is documented at `data/raw/interviews/SOURCE_TERMS_REVIEW.md`. Therefore current public-page summaries remain discovery candidates only. No written permission has been obtained, and Phase 2 cannot be accepted as complete on the basis of these sources alone.

## Latest follow-up implementation (2026-10-10)

- Added explicit Phase 2 evidence columns to all 19 interview-index rows: `deduplication_evidence`, `permission_basis`, `reviewer`, and `review_date`. Existing values are intentionally blank because no permission or independent-review evidence has been established.
- Updated the structural validator to require those fields in the interview index, aligning it with the readiness checker.
- Added `workflow_dispatch` to the GitHub Actions workflow so repository validation can be triggered manually as well as on pushes and pull requests.

These are workflow/schema improvements, not completion of the research gates. The 19 interview rows are still discovery candidates, no Phase 13 labels have been approved, and no benchmark metrics should be reported until the original sources and labels have actually been reviewed. At the time of that earlier note, push-triggered workflow status had not yet been verified. A later run succeeded; see the CLI and packaging pass below.

## Pipeline implementation pass (2026-10-10)

Implemented reusable Python modules for:
- Taxonomy phrase matching and text normalization.
- TF-IDF topic ranking and optional sentence-embedding ranking.
- Loading and searching the currently extracted VIT course catalog, with optional local-PDF text extraction.
- Loading interview-index rows while preserving source review status and excluding unapproved rows from eligible-only results.
- Unique-topic and weighted coverage calculations, with explicit warnings that overlap is not course depth or student proficiency.

Added pipeline tests and updated CI to install the baseline mapping dependencies before running tests. The first run exposed a missing scikit-learn dependency in CI; the workflow was corrected to install NumPy, pandas, and scikit-learn. The follow-up run passed; later CLI tests and documentation changes also passed in GitHub Actions.

These code additions do not fill the external evidence gaps: the syllabus file is still only a 21-course catalog extract, the 19 interview records are not cleared, the benchmark has zero approved labels, and no valid research benchmark scores exist yet.


## CLI and packaging pass (2026-10-10)

- Added a runnable CLI for taxonomy mapping (`map`), course-catalog search (`courses`), explicit topic-overlap scoring (`coverage`), and fail-closed research readiness checks (`readiness`).
- Added Python package metadata and a `prepline` console entry point, developer setup documentation, and CLI tests.
- The latest GitHub Actions run for commit `754bccaceee0e31ae28c7f46b3e6ee5b78afb245` completed successfully: [workflow run](https://github.com/Vedant0407/prepline/actions/runs/38071503442).

The CLI is a working prototype, not evidence that the source-data gates have passed. The current VIT PDF provides a 21-row Discipline Core catalog on printed page 2, but does not include detailed module-level syllabi for those core courses in the extractable sections identified so far. The PDF has 10 curriculum pages followed by annexure material for other courses; course-topic mapping must not be inferred from course titles alone. Phase 2/13 remain blocked by source permission/independence review, detailed syllabus-topic evidence, and 200 genuinely human-reviewed mappings.

## Additional source-eligibility check (2026-10-10)

- Checked Jointaro/Taro's published terms at https://www.jointaro.com/terms/ and robots.txt at https://www.jointaro.com/robots.txt. The terms prohibit spidering, crawling, and scraping. Robots.txt allowing crawlers does not grant content-reuse or redistribution rights. The Jointaro candidate CSV found in the project workspace must therefore remain a discovery index unless written permission or an applicable separate license is confirmed.
- Added `data/raw/interviews/PERMISSION_REQUEST_TEMPLATE.md` to request explicit written permission for the intended academic use.
- This does not close the legal-use gate: no written permission has been received. LeetCode and GeeksforGeeks remain excluded from the production corpus unless permission is obtained.

## Current completion decision

**Phase 2: NOT COMPLETE.** The repository has a 21-row catalog of Discipline Core courses and a discovery index of interview reports, but there are not 15 eligible reports with documented source permission, role/cohort review, and independent-report evidence. The official PDF's full topic-level syllabus extraction is also not committed as a verified structured dataset.

**Phase 13: NOT COMPLETE.** Candidate pools are useful for annotation, but `evaluation/ground_truth.csv` still has no accepted human-reviewed rows. The 200-label threshold, frozen 70/15/15 split, and benchmark results cannot be honestly claimed until permitted examples have been reviewed and accepted. CI passing only validates repository checks; it is not evidence that these research gates pass.

The remaining gates require external evidence or actual human decisions. Do not change candidate status to approved to make readiness pass. Use the permission request template and review workflow; retain the reply/permission basis and reviewer decisions in the repository.
