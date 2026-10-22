# Microsoft SDE-1 interview experiences (GeeksforGeeks), collected 2026-10-22

Microsoft SDE-1, GeeksforGeeks, interview dates mostly unknown.

`reports.csv` and `questions.csv` use the same columns as `data/processed/amazon_sde1/reports.csv` and `questions.csv`,
with three additions: `date_basis` and `page_published` in `reports.csv`, and `source_url` in `questions.csv`. Every
report's page was fetched on 2026-10-22. Questions are quoted as written on the page and never paraphrased. Vague
mentions, questions given only as a link, and quotes that were excerpted are marked `needs_review=True` with a reason.

## Dates: 17 reports, interview dates mostly unknown

These reports are not limited to 2023–2026. Only 3 articles state when the interview happened.

- **`date_basis = article_text` (3 reports):** `interview_date_or_year` is the date stated in the article. These are
  MSFT001 (12-12-2025), MSFT002 (26-06-2025) and MSFT003 (2023).
- **`date_basis = published` (14 reports):** the article states no interview date, so `interview_date_or_year` is the
  article's original publish date. The page header shows only a "Last Updated" date, so the publish date comes from the
  page's metadata (JSON-LD `datePublished`, `article:published_time`), re-fetched on 2026-10-22. The publish dates run
  from 2018 to 2024: MSFT013 2018, MSFT005 2019, MSFT017 2020, MSFT008/009/010 2021, MSFT004/007 2022,
  MSFT006/014/015/016 2023 and MSFT011/012 2024. The interview happened on or before that date.
- **`page_published`** is the publish date for all 17 reports, including the 3 dated from the article text.
- **Location:** only MSFT003, MSFT004 and MSFT005 name an Indian city (Hyderabad). MSFT001 and MSFT002 are Indian
  candidates, with the interview location not stated. The rest say "Not stated".

## Excluded pages (fetched, not used)

These were excluded during collection (internships, SDE-II, duplicates, and interviews stated or dated before 2023).
The kept reports above were not held to the same pre-2023 rule, because most of them have no interview date.

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
