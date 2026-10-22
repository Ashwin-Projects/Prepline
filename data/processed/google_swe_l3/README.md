# Google SWE new-grad / L3 interview experiences (GeeksforGeeks), collected 2026-10-22

Google SWE new-grad / L3, GeeksforGeeks, interview dates mostly unknown. 16 reports, not 20: GeeksforGeeks has no more
real reports that fit this role, and none were padded.

The columns match `data/processed/microsoft_sde1/`: `reports.csv` adds `date_basis` and `page_published`, and
`questions.csv` adds `source_url`. Each report's page was fetched on 2026-10-22, and every question is quoted as
written on the page; build-time checks confirmed each quote appears in the fetched article text. Vague mentions
("a question on trees") go in `topic` with `needs_review=True`. Questions the page gives as examples rather than the
exact ones, or as a related problem because of an NDA, are also `needs_review=True`, with the reason.

## Which reports are included

A page is kept only if it names a new-grad, university-graduate, on-campus, SDE-1 or Level 3 software engineering
role at Google, and describes at least one question or round topic. Experienced-hire "Software Engineer" pages that
do not state the level are excluded, because they may be L4 or above.

- **Dates:** `date_basis = article_text` for GOOG001 (21-11-2024) and GOOG008 (2022). The other 14 use the article's
  original publish date from the page's JSON-LD `datePublished` (`date_basis = published`); the interview happened on
  or before it. Publish dates run from 2019 to 2024.
- **Filtering:** only 8 of the 16 reports keep at least one question after the interview filter (most pages give only
  topics). With fewer than 15, this target will return `INSUFFICIENT_DATA` when scored.

## Excluded pages (fetched, not used)

| Page(s) | Reason |
|---|---|
| google-interview-experience-21, -for-swe-2, -for-software-engineer-2, -9-2, -on-campus-2020 | internship (SWE intern, STEP) |
| google-l4-interview-experience, -for-software-engineer-5, -for-l5-engineer, -13 | L4 or L5 |
| google-interview-experience-for-chrome-os-firmware-engineer-2-year-exp | firmware engineer role |
| google-interview-experience-22, -20, -15, -2021-virtual | student; role not stated (likely internship) |
| google-interview-experience-for-software-engineer-7, -16, -for-software-engineer-4, -for-software-developer, -off-campus-2, -swe-full-time, -for-sde-2024, -for-sde-3, -for-sde-4, -for-software-engineer, -for-swe, -7, -for-sde-2, -for-software-engineer-2020, -for-software-engineer-november-2020, -for-sde, -on-site-for-sde, -3, -telephonic-sde, -2; google-india-interview-experience(-for-sde); google-bangalore-interview-experience(-2, -3); google-interview-experience (Set 4); google-mountain-view-interview | level not stated (mostly experienced hires) or 4 years' experience |
| google-interview-experience-18 | same text as google-interview-experience-for-software-developer |
| google-interview-experience-19 | paraphrase of google-interview-experience-17 (GOOG004) |
| google-interview-experience-for-software-engineer-6 | same text as google-interview-experience-16 |
| google-interview-experience-maximum-subarray-sum | same author and text as google-interview-experience-on-campus (GOOG005) |
| google-chennai-interview-experience-for-sde-1, -for-software-enginner, -for-software-engineer-3, -14 | no questions or round topics described |
| google-mountain-view-interview-experience(-2), google-interview-experience-12, -8, -10, -2-2, -11 | TopTalent profile interviews of new grads; no questions or round topics |
| google-interview-experience-set-6, google-interview-question-for-java-position | not a SWE interview (aptitude/rating test; take-home statement without a role) |

Tag-page results for internships, STEP, Kickstart/online challenges, Foobar, TSS, GDSC and non-engineering roles
were not fetched.
