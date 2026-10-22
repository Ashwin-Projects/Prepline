# Flipkart SDE-1 interview experiences (GeeksforGeeks), collected 2026-10-22

Flipkart SDE-1, GeeksforGeeks, interview dates partly known. 20 reports.

The columns match `data/processed/microsoft_sde1/`: `reports.csv` adds `date_basis` and `page_published`, and
`questions.csv` adds `source_url`. Each report's page was fetched on 2026-10-22, and every question is quoted as
written on the page; build-time checks confirmed each quote appears in the fetched article text. Vague mentions go in
`topic` with `needs_review=True`. Questions given only as a link, problems the page says are "similar to, not the
exact ones", and NDA overviews are also `needs_review=True`, with the reason.

## Which reports are included

The 20 most recently published pages that describe a Flipkart SDE-1 / SDE-I interview (on-campus, off-campus or
GRiD SDE 1 intern+FTE), with at least one question or round topic. Older SDE-1 pages (2015–2019, "Set 31"–"Set 51"
and similar) were not used once 20 were reached.

- **Dates:** 10 reports use a date stated in the article (`date_basis = article_text`): an interview date, month or
  year. The other 10 use the article's original publish date from the page's JSON-LD `datePublished`
  (`date_basis = published`). Interview years run from 2019 to 2024.
- **Filtering:** 17 of the 20 reports keep at least one question after the interview filter.

## Excluded pages (fetched, not used)

| Page(s) | Reason |
|---|---|
| flipkart-interview-experience-for-sde-2-1, -sde-2-bengaluru-may-2024-reject, flipkart-interview-for-sde2-backend, -for-sde-2-4, -for-sde-2-off-campus, -for-sde-2-3, -for-sde-2-3-5-years-experienced, -for-sde-2-2, -for-sde2-2-5-yr-exp, -sde-2, flipkart-interview-for-sde-ii(-2), -for-sde-2, flipkart-machine-coding-round-experience | SDE-2 |
| flipkart-interview-experience-for-sde-i | paraphrase of flipkart-interview-experience-for-sde-5 (FLPK006) |
| flipkart-interview-experience-7 | generic process description; same questions as flipkart-interview-experience-for-sde-1off-campus (FLPK017) |
| flipkart-interview-experience-for-sde-4 | template text with no actual experience |
| flipkart-interview-experience-for-sde-3 | Flipkart Runway (internship programme) |
| flipkart-interview-experience-for-senior-product-manager | product role |
| flipkart-interview-experience-2 | testing/automation role |
| flipkart-interview-experience-3, flipkart-interview-experience-on-campus-2021 | role not stated |
| flipkart-interview-experience-for-sde-mobile | preparation document; no questions |

Contest pages (GRiD, Runway hackathon), application/data/UI engineer, sales and internship pages were not fetched.
