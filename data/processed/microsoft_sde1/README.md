# Microsoft SDE-1 interview experiences (GeeksforGeeks), collected 2026-10-22

`reports.csv` and `questions.csv` use the same columns as `data/processed/reports.csv` and `questions.csv`, with two
additions: `date_basis` in `reports.csv` and `source_url` in `questions.csv`. Every report's page was fetched on
2026-10-22. Questions are quoted as written on the page and never paraphrased. Vague mentions, questions given only as
a link, and quotes that were excerpted are marked `needs_review=True` with a reason.

## Coverage: 17 reports, not 20

GeeksforGeeks has few Microsoft SDE-1 full-time posts that can be dated to 2023–2026. After excluding internships,
SDE-II roles, pre-2023 interviews and duplicates, 17 reports remain.

- **`date_basis = article_text` (3 reports):** the date is stated in the article. MSFT001 (12-12-2025),
  MSFT002 (26-06-2025), MSFT003 (2023).
- **`date_basis = page_last_updated` (14 reports):** the article states no interview date. The date given is the page's
  "Last Updated" date, and many pages share the same bulk date, 23-07-2025. These may be older experiences: for
  example, MSFT009 mentions a "vaccinated" grid problem and MSFT013 a CoCubes test. Filter on `date_basis` if only
  verified 2023–2026 reports should be used.
- **Location:** only MSFT003, MSFT004 and MSFT005 name an Indian city (Hyderabad). MSFT001 and MSFT002 are Indian
  candidates, with the interview location not stated. The rest say "Not stated".

## Excluded pages (fetched, not used)

| Page | Reason |
|---|---|
| microsoft-interview-experience-on-campus-2023-2 | internship |
| microsoft-interview-experience-for-sde-on-campus | campus drive Nov 2021, internship to PPO (pre-2023) |
| microsoft-interview-experience-for-swe | applied Dec 2021 (pre-2023) |
| microsoft-full-time-interview-experience-on-campus | August 2018 |
| microsoft-interview-interview-experience-for-full-time | academic year 2018-19 |
| microsoft-interview-experience-for-software-engineer | 3 April 2021 |
| microsoft-interview-experience-for-sde-off-campus | last updated April 2021 (pre-2023) |
| microsoft-interview-experience-for-sde-1-2 | "due to the pandemic situation", no date (likely pre-2023) |
| microsoft-interview-experience-off-campus | Microsoft Engage 2021 (pre-2023) |
| microsoft-interview-experience-off-campus-2 | duplicate of the page above (same candidate and question set) |

Searches also surfaced internships, SDE-II/L61/L62 roles and old "Set N" posts; these were not fetched.
