# Interview data sources

One folder per company/role target under `data/processed/<target_id>/` (see `docs/ADDING_A_COMPANY.md`). Every
report is one candidate's public interview-experience write-up. Questions are quoted from the page, not paraphrased.

| Target | Folder | Source | Reports | Collected | Dates |
|---|---|---|---|---|---|
| Amazon SDE-1 | `data/processed/amazon_sde1/` | GeeksforGeeks | 21 | Phase 2, committed 2026-09-08 (`0dbe0e0`); raw rows in `data/raw/interviews/amazon_sde1_interviews.csv` | `interview_date_or_year` as recorded in Phase 2 (the basis of each date was not recorded) |
| Microsoft SDE-1 | `data/processed/microsoft_sde1/` | GeeksforGeeks | 17 | 2026-10-22 | Mostly unknown: 3 from the article text, 14 are the article's publish date (`date_basis`; see the folder README) |
| Google SWE new-grad / L3 | `data/processed/google_swe_l3/` | GeeksforGeeks | 16 | 2026-10-22 | Mostly unknown: 2 from the article text, 14 are the article's publish date (see the folder README) |
| Flipkart SDE-1 | `data/processed/flipkart_sde1/` | GeeksforGeeks | 20 | 2026-10-22 | 10 from the article text, 10 are the article's publish date (see the folder README) |

All datasets are a convenience sample of what GeeksforGeeks has published, not a random sample of interviews.
None is limited to a date range.

## Amazon SDE-1 (`data/processed/amazon_sde1/reports.csv`)

AMZ012 was removed as a duplicate of AMZ004, and its ID is not reused.

| Report | Date or year | Source |
|---|---|---|
| AMZ001 | 25-01-2025 | https://www.geeksforgeeks.org/interview-experiences/amazon-interview-experience-for-sde1-fresher-off-campus/ |
| AMZ002 | 2025 | https://www.geeksforgeeks.org/interview-experiences/amazon-interview-experience-for-sde-1-14/ |
| AMZ003 | 2025 | https://www.geeksforgeeks.org/interview-experiences/amazon-interview-experience-for-sde-1-21/ |
| AMZ004 | 2025 | https://www.geeksforgeeks.org/interview-experiences/amazon-interview-experience-for-sde-1-20/ |
| AMZ005 | 2025 | https://www.geeksforgeeks.org/interview-experiences/amazon-interview-experience-for-sde-1-13/ |
| AMZ006 | 2025 | https://www.geeksforgeeks.org/interview-experiences/amazon-interview-experience-for-sde-1-25/ |
| AMZ007 | 2025 | https://www.geeksforgeeks.org/interview-experiences/amazon-interview-experience-for-sde1-off-campus/ |
| AMZ008 | 2025 | https://www.geeksforgeeks.org/interview-experiences/amazon-interview-experience-for-sde-1-off-campus/ |
| AMZ009 | 2025 | https://www.geeksforgeeks.org/interview-experiences/amazon-interview-experience-for-sde-1-on-campus/ |
| AMZ010 | 2024 | https://www.geeksforgeeks.org/interview-experiences/amazon-interview-experience-for-sde-1-34/ |
| AMZ011 | 2022 | https://www.geeksforgeeks.org/interview-experiences/amazon-interview-experience-for-sde-1-26/ |
| AMZ013 | 2021 | https://www.geeksforgeeks.org/interview-experiences/amazon-interview-experience-for-sde-1-10/ |
| AMZ014 | 2021 | https://www.geeksforgeeks.org/interview-experiences/amazon-interview-experience-for-sde-1-9/ |
| AMZ015 | 2021 | https://www.geeksforgeeks.org/interview-experiences/amazon-interview-experience-for-sde-1-29/ |
| AMZ016 | 2021 | https://www.geeksforgeeks.org/interview-experiences/amazon-interview-experience-for-sde-1-16/ |
| AMZ017 | 2021 | https://www.geeksforgeeks.org/interview-experiences/amazon-interview-experience-for-sde-1-17/ |
| AMZ018 | 2021 | https://www.geeksforgeeks.org/interview-experiences/amazon-interview-experience-for-sde-1-18/ |
| AMZ019 | 2022 | https://www.geeksforgeeks.org/interview-experiences/amazon-interview-experience-for-sde-1-30/ |
| AMZ020 | 2022 | https://www.geeksforgeeks.org/interview-experiences/amazon-interview-experience-for-sde-1-31/ |
| AMZ021 | 2023 | https://www.geeksforgeeks.org/interview-experiences/amazon-interview-experience-for-sde-1-32/ |
| AMZ022 | 2023 | https://www.geeksforgeeks.org/interview-experiences/amazon-interview-experience-for-sde-1-33/ |

## Microsoft SDE-1 (`data/processed/microsoft_sde1/reports.csv`)

Microsoft SDE-1, GeeksforGeeks, interview dates mostly unknown. Pages fetched and excluded, and how dates were set, are
listed in `data/processed/microsoft_sde1/README.md`.

| Report | Date or year | Date basis | Page published | Source |
|---|---|---|---|---|
| MSFT001 | 12-12-2025 | article_text | 27-12-2025 | https://www.geeksforgeeks.org/interview-experiences/microsoft-software-engineer-l60-interview-experience-december-2025-off-campus/ |
| MSFT002 | 26-06-2025 | article_text | 25-07-2025 | https://www.geeksforgeeks.org/interview-experiences/microsoft-interview-experience-for-swe-devops/ |
| MSFT003 | 2023 | article_text | 16-05-2024 | https://www.geeksforgeeks.org/microsoft-interview-experience-2023 |
| MSFT004 | 28-03-2022 | published | 28-03-2022 | https://www.geeksforgeeks.org/interview-experiences/microsoft-interview-experience-for-sde-1-hyderabad/ |
| MSFT005 | 04-05-2019 | published | 04-05-2019 | https://www.geeksforgeeks.org/interview-experiences/microsoft-interview-experience-sde-1-off-campus-8-months-exp/ |
| MSFT006 | 27-01-2023 | published | 27-01-2023 | https://www.geeksforgeeks.org/interview-experiences/microsoft-interview-experience-for-sde-1-on-campus/ |
| MSFT007 | 23-02-2022 | published | 23-02-2022 | https://www.geeksforgeeks.org/interview-experiences/microsoft-interview-experience-for-sde-1-off-campus/ |
| MSFT008 | 31-03-2021 | published | 31-03-2021 | https://www.geeksforgeeks.org/interview-experiences/microsoft-interview-experience-for-sde-i-1-year-experienced/ |
| MSFT009 | 21-12-2021 | published | 21-12-2021 | https://www.geeksforgeeks.org/interview-experiences/microsoft-interview-experience-for-sde-i-on-campus/ |
| MSFT010 | 20-12-2021 | published | 20-12-2021 | https://www.geeksforgeeks.org/interview-experiences/microsoft-interview-experience-for-software-engineer-1-year-experienced/ |
| MSFT011 | 27-05-2024 | published | 27-05-2024 | https://www.geeksforgeeks.org/interview-experiences/microsoft-interview-experience-for-sde-9/ |
| MSFT012 | 03-05-2024 | published | 03-05-2024 | https://www.geeksforgeeks.org/interview-experiences/microsoft-interview-experience-sde-i/ |
| MSFT013 | 11-08-2018 | published | 11-08-2018 | https://www.geeksforgeeks.org/interview-experiences/microsoft-sde-on-campus-full-time/ |
| MSFT014 | 04-07-2023 | published | 04-07-2023 | https://www.geeksforgeeks.org/interview-experiences/microsoft-interview-experience-for-sde-5/ |
| MSFT015 | 24-04-2023 | published | 24-04-2023 | https://www.geeksforgeeks.org/interview-experiences/microsoft-interview-experience-for-sde-4/ |
| MSFT016 | 24-01-2023 | published | 24-01-2023 | https://www.geeksforgeeks.org/microsoft-interview-experience-for-sde-3 |
| MSFT017 | 26-04-2020 | published | 26-04-2020 | https://www.geeksforgeeks.org/microsoft-interview-experience-for-sde-1 |

## Google SWE new-grad / L3 (`data/processed/google_swe_l3/reports.csv`)

Inclusion rules and the pages fetched and excluded are in `data/processed/google_swe_l3/README.md`.

| Report | Role (as stated) | Date or year | Date basis | Page published | Source |
|---|---|---|---|---|---|
| GOOG001 | Software Engineer, University Graduate 2025 | 21-11-2024 | article_text | 30-12-2024 | https://www.geeksforgeeks.org/interview-experiences/google-interview-experience-software-engineer-university-graduate-2025/ |
| GOOG002 | SWE (on-campus) | 15-10-2024 | published | 15-10-2024 | https://www.geeksforgeeks.org/interview-experiences/google-interview-experience-for-swe-on-campus-2024/ |
| GOOG003 | SWE FTE (on-campus) | 13-09-2024 | published | 13-09-2024 | https://www.geeksforgeeks.org/interview-experiences/google-interview-experience-swe-fte-on-campus-2024/ |
| GOOG004 | University Graduate | 08-05-2024 | published | 08-05-2024 | https://www.geeksforgeeks.org/interview-experiences/google-interview-experience-17/ |
| GOOG005 | Not stated (on-campus) | 14-05-2024 | published | 14-05-2024 | https://www.geeksforgeeks.org/interview-experiences/google-interview-experience-on-campus/ |
| GOOG006 | SDE1 | 07-05-2024 | published | 07-05-2024 | https://www.geeksforgeeks.org/interview-experiences/google-interview-experience-sde-1/ |
| GOOG007 | SWE (on-campus) | 29-04-2024 | published | 29-04-2024 | https://www.geeksforgeeks.org/interview-experiences/google-interview-experience-for-swe-on-campus/ |
| GOOG008 | Not stated (on-campus, full-time offer) | 2022 | article_text | 14-06-2023 | https://www.geeksforgeeks.org/interview-experiences/google-interview-experience-on-campus-2022/ |
| GOOG009 | SWE (on-campus and off-campus application) | 24-04-2023 | published | 24-04-2023 | https://www.geeksforgeeks.org/interview-experiences/google-swe-interview-experience/ |
| GOOG010 | Software Engineering Graduate | 30-03-2021 | published | 30-03-2021 | https://www.geeksforgeeks.org/interview-experiences/google-taiwan-interview-experience-for-software-engineering-graduate/ |
| GOOG011 | Software Engineer 2021 New Grad | 17-12-2020 | published | 17-12-2020 | https://www.geeksforgeeks.org/interview-experiences/google-interview-experience-for-software-engineer-2021-new-grad/ |
| GOOG012 | University Grad 2020 | 21-04-2020 | published | 21-04-2020 | https://www.geeksforgeeks.org/interview-experiences/google-interview-onsite-university-grad-2020/ |
| GOOG013 | New grad (2020), off-campus | 13-04-2020 | published | 13-04-2020 | https://www.geeksforgeeks.org/interview-experiences/google-off-campus-interview-experience/ |
| GOOG014 | Software Developer Level 3 | 05-03-2020 | published | 05-03-2020 | https://www.geeksforgeeks.org/interview-experiences/google-munich-software-developer-interview-experience/ |
| GOOG015 | SDE1 | 13-07-2019 | published | 13-07-2019 | https://www.geeksforgeeks.org/interview-experiences/google-interview-experience-for-sde-1/ |
| GOOG016 | SDE1 (off-campus) | 16-06-2019 | published | 16-06-2019 | https://www.geeksforgeeks.org/interview-experiences/google-off-campus-sde-1/ |

## Flipkart SDE-1 (`data/processed/flipkart_sde1/reports.csv`)

Inclusion rules and the pages fetched and excluded are in `data/processed/flipkart_sde1/README.md`.

| Report | Role (as stated) | Date or year | Date basis | Page published | Source |
|---|---|---|---|---|---|
| FLPK001 | SDE1 (on-campus FTE) | 01-12-2024 | article_text | 20-12-2024 | https://www.geeksforgeeks.org/interview-experiences/flipkart-interview-experience-for-sde-1-on-campus-fte/ |
| FLPK002 | SDE1 | 20-06-2024 | article_text | 27-06-2024 | https://www.geeksforgeeks.org/interview-experiences/flipkart-interview-experience-sde-1/ |
| FLPK003 | SDE1 (off-campus, freshers) | 17-06-2024 | published | 17-06-2024 | https://www.geeksforgeeks.org/interview-experiences/flipkart-interview-experience-for-sde-1-off-campus-3/ |
| FLPK004 | SDE1 (off-campus) | 10-06-2024 | article_text | 14-06-2024 | https://www.geeksforgeeks.org/interview-experiences/flipkart-interview-experience-for-sde-1-off-campus-2024-1/ |
| FLPK005 | SDE-1 (off-campus) | 25-04-2024 | article_text | 13-05-2024 | https://www.geeksforgeeks.org/interview-experiences/flipkart-interview-experience-for-sde-1-off-campus-2024/ |
| FLPK006 | SDE-I | 2022 | article_text | 09-05-2024 | https://www.geeksforgeeks.org/interview-experiences/flipkart-interview-experience-for-sde-5/ |
| FLPK007 | SDE1 | 08-05-2024 | published | 08-05-2024 | https://www.geeksforgeeks.org/interview-experiences/flipkart-interview-experience-for-sde-1-7/ |
| FLPK008 | SDE1 (off-campus) | 25-11-2023 | published | 25-11-2023 | https://www.geeksforgeeks.org/interview-experiences/flipkart-interview-experience-for-sde-1-off-campus-2/ |
| FLPK009 | SDE1 (off-campus) | 30-10-2023 | published | 30-10-2023 | https://www.geeksforgeeks.org/interview-experiences/flipkart-interview-experience-for-sde1-off-campus-2023/ |
| FLPK010 | SDE1 (off-campus) | 11-09-2023 | published | 11-09-2023 | https://www.geeksforgeeks.org/interview-experiences/flipkart-interview-experience-for-sde-1-off-campus/ |
| FLPK011 | SDE 1 intern+FTE (Flipkart GRiD 3.0, off-campus) | 18-10-2021 | published | 18-10-2021 | https://www.geeksforgeeks.org/interview-experiences/flipkart-interview-experience-for-sde-1-4/ |
| FLPK012 | Software development (on-campus full-time) | 24-08-2021 | published | 24-08-2021 | https://www.geeksforgeeks.org/interview-experiences/flipkart-interview-experience-for-sde/ |
| FLPK013 | SDE-I (1 year experienced) | 30-06-2021 | published | 30-06-2021 | https://www.geeksforgeeks.org/interview-experiences/flipkart-interview-experience-for-sde-i-1-year-experienced/ |
| FLPK014 | SDE1 | 16-06-2021 | published | 16-06-2021 | https://www.geeksforgeeks.org/interview-experiences/flipkart-interview-experience-for-sde-1-3/ |
| FLPK015 | SDE-1 (1.7 years experience) | 2021 | article_text | 18-05-2021 | https://www.geeksforgeeks.org/interview-experiences/flipkart-interview-experience-for-sde-1-2/ |
| FLPK016 | SDE full-time (on-campus) | 01-2021 | article_text | 03-02-2021 | https://www.geeksforgeeks.org/interview-experiences/flipkart-interview-experience-for-sde-full-time-on-campus/ |
| FLPK017 | SDE1 (off-campus, new grad 2021) | 10-2020 | article_text | 17-11-2020 | https://www.geeksforgeeks.org/interview-experiences/flipkart-interview-experience-for-sde-1off-campus/ |
| FLPK018 | SDE1 (on-campus) | 10-2020 | article_text | 05-11-2020 | https://www.geeksforgeeks.org/interview-experiences/flipkart-interview-experience-for-sde-1-on-campus/ |
| FLPK019 | SDE-1 (on-campus) | 15-09-2020 | published | 15-09-2020 | https://www.geeksforgeeks.org/interview-experiences/flipkart-interview-experience-for-sde-1-on-campus-2020/ |
| FLPK020 | SDE1 (on-campus) | 2019 | article_text | 26-08-2019 | https://www.geeksforgeeks.org/interview-experiences/flipkart-interview-experience-for-sde-1-on-campus-2019-2/ |
