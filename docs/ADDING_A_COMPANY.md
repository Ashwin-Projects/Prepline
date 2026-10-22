# Adding a company/role target

You need two things: a data folder and one config entry. No code changes.

## 1. Data folder: `data/processed/<target_id>/`

Use a lower-case `<target_id>` such as `google_l3`. The folder holds two CSV files. The filter rules are in
`config/scoring_v1.2.json` (`interview_filter`).

- **`reports.csv`**: one row per independent interview report, deduplicated. It needs a `report_id` column; the IDs
  must be unique, with a short prefix such as `GOO001`. Also fill `company, role, location, interview_date_or_year,
  outcome, source_name, source_url`, as in `data/processed/amazon_sde1/reports.csv`.
- **`questions.csv`**: one row per question or topic mention, with the columns `report_id, round, round_type,
  question_text, topic, needs_review, review_reason`. The pipeline scores only these rows:
  - `round_type` is not `behavioral`;
  - `needs_review` is `False`;
  - `question_text` is not empty.

Quote questions from the source and never paraphrase them. Put a vague mention in `topic` and leave `question_text`
empty. The CLAUDE.md parsing rules apply.

Add a short `README.md` saying where the reports came from, when they were collected, and how dates were set. Also
add the target to `data/SOURCES.md`.

## 2. Config entry: `config/targets.json`

```json
{"id": "google_l3", "company": "Google", "role": "L3", "data_dir": "data/processed/google_l3"}
```

The API (`/api/v1/supported-targets`, `/validate-target`, `/pipeline/run`) and both runners read this file. Restart the
API after editing it.

## 3. Run and compare

```
python evaluation/run_all_targets.py
```

This writes `results/<target_id>_v1.2_course_syllabi.json` for each new target and regenerates
`results/COMPARISON.md`. Existing results files are kept, not re-run. A target with fewer than 15 reports left after
filtering gets `status: INSUFFICIENT_DATA` and no S_comp (density gate, `min_reports` in the scoring config). To run one
target on its own: `python evaluation/run_full_pipeline.py --target <target_id> --pdf-dir data/raw/syllabi --glob
"B[CM]*.pdf" --syllabus-id VIT_CSE_2024_25_courses`.

The test `evaluation/test_targets.py::test_new_target_needs_only_data_folder_and_config_entry` checks that a new target
works with nothing else added.
