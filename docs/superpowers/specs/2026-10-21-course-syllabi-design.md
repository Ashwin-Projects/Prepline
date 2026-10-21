# Course-syllabi combined run — design (approved 2026-10-21)

## Goal

Score the owner's complete core syllabus — 20 individual VIT course PDFs in `data/raw/syllabi/BCSE*.pdf`
(12 theory `…L`, 8 lab `…P`) — as ONE combined syllabus, `VIT_CSE_2024_25_courses`. The full-programme PDF
(`B.Tech_CSE_2024_2025(1) (1).pdf`) is not used in this run and stays as-is.

## Decisions

1. **Config v1.2.** `config/scoring_v1.2.json` = v1.1 with only `syllabus.core_courses` (exactly the 20 file
   codes) and `syllabus.core_courses_source` changed, plus `config_version`/`description`/`supersedes`.
   τ, γ, depth reference values, MIN_REPORTS, semester weeks, taxonomy and model are identical to v1.1
   (test-guarded). The code loads v1.2. v1.0/v1.1 config and results files stay untouched. Old-allowlist
   courses without a file (BCSE101E, BCSE102L, BCSE102P, BCSE103E, BCSE203E, BMAT205L) are "not in core".
2. **Combined syllabus.** `parse_syllabus_pdfs(paths, syllabus_id)` reads and segments each file on its own,
   merges the courses, applies the allowlist/duplicate filter once, and returns the `parse_syllabus_pdf`
   schema plus `source_files`, `file_errors`, `course_groups`, per-file text layer. An unreadable file is
   recorded in `file_errors`; only "no core course at all" raises. `parse_syllabus_pdf(path)` keeps working.
   Every unit carries `course_code`, `course_group` (code without its trailing letter), `component`
   (`theory`|`lab`) and `source_file`. Ids: `<code>_mod_<n>` (modules), `<code>_exp_<n>` (experiments).
3. **Depth (option A, no double counting).** Theory units: `unit_hours` from the module header only (the
   L files have P = 0, so no lab hours). Lab-only courses become one unit per experiment with
   `lab_hours = course lab hours / experiment count` (course lab hours = "Total Laboratory Hours", else
   P × semester_weeks). `lab_count` = the course's experiment count, carried as
   `course_signals: {"lab_count": N}` and added by scoring **once per (topic, course)**, never per
   experiment. The API cache keeps `course_signals`.
4. **Parser fixes.** (a) text extraction with `x_tolerance=1.5` (fixes glued words); (b) strip VIT running
   page lines ("Agenda Item … Annexure …", "Proceedings of the … Academic Council …") before segmentation;
   (c) sequential experiment lists numbered `1.`, `1)` or `1 `; (d) a `CODE Title L T P C` header followed
   by a line of only 1–3 integers is accepted with all L-T-P-J-C fields `None` and
   `ltpc_status: "incomplete"` (BCSE205L; values not guessed), otherwise `ltpc_status: "complete"`;
   (e) modules with no body after stripping (Module 8 "Contemporary Issues") are not mapped and are listed
   in `skipped_modules`. Embedded theory+lab courses keep their current behaviour.
5. **CLI.** `run_full_pipeline.py` takes repeatable `--pdf`, or `--pdf-dir` + `--glob` (default
   `BCSE*.pdf`), and `--syllabus-id`; it logs per-file counts and stage timings and never overwrites results.
   `RESULTS_VERSION = "v1.2"`.
6. **Manifest.** `vit_syllabus_manifest.csv`: one row per course file plus the existing programme row
   (marked unused). New columns: `course_code, course_group, component, course_title, l_t_p_j_c,
   ltpc_status, used_in_course_run, source`. URLs blank for course rows; `source` = "VIT official course
   syllabus PDF, downloaded by user 2026-10-21".
7. **API.** Single upload unchanged. Multi-file upload → `docs/BACKLOG.md` (dashboard task).
8. **Outputs.** `results/amazon_sde1_v1.2_course_syllabi.json`; `results/CHANGES_v1.2.md` compares it with
   the v1.1 3-course run and v1.0 (S_comp, courses/modules/topics, measured vs fallback, top-10 gaps,
   unmapped terms) and notes the runs share no courses.
