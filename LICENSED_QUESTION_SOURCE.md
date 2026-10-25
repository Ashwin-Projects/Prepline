# Licensed interview-question source manifest

Review date: 2026-10-10

## Source

- Project: CodePrep Open Interview Questions
- Repository: https://github.com/codeprepdev/codeprep-questions
- Data file: https://github.com/codeprepdev/codeprep-questions/blob/main/data/questions.json
- Upstream dataset metadata declares license: **CC-BY-4.0**
- Required attribution: **CodePrep — https://codeprep.dev**
- Dataset description: curated software-engineering practice questions with answers/explanations; this is a practice-question bank, not a collection of candidate-submitted interview experience reports.
- Upstream dataset metadata declares 110 questions.
- Upstream license text: https://github.com/codeprepdev/codeprep-questions/blob/main/LICENSE

## Prepline handling

- `evaluation/codeprep_mappings_for_review.csv` contains 78 topic-mapping candidates created from prompts in the licensed source dataset.
- Candidate taxonomy labels were suggested using deterministic text/topic rules and are **not human-verified ground truth**.
- Every row is marked `needs_human_review`; reviewer/date are intentionally blank.
- Preserve the required attribution when redistributing or using the derived data.
- Check upstream license/data exclusions and source changes before release; this note records the published metadata observed on the review date, not a legal opinion.
- This practice-question dataset can support Phase 13 candidate generation, but it does **not** meet Phase 2's separate requirement for at least 15 independent, eligible candidate experience reports.
