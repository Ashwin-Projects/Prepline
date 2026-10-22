# Interview data sources

One folder per company/role target under `data/processed/<target_id>/` (see `docs/ADDING_A_COMPANY.md`). Every
report is one candidate's public interview-experience write-up. Questions are quoted from the page, not paraphrased.

| Target | Folder | Source | Reports | Collected | Dates |
|---|---|---|---|---|---|
| Amazon SDE-1 | `data/processed/amazon_sde1/` | GeeksforGeeks | 21 | Phase 2, committed 2026-09-08 (`0dbe0e0`); raw rows in `data/raw/interviews/amazon_sde1_interviews.csv` | `interview_date_or_year` as recorded in Phase 2 (the basis of each date was not recorded) |
| Microsoft SDE-1 | `data/processed/microsoft_sde1/` | GeeksforGeeks | 17 | 2026-10-22 | Mostly unknown: 3 from the article text, 14 are the article's publish date (`date_basis`; see the folder README) |

Both datasets are a convenience sample of what GeeksforGeeks has published, not a random sample of interviews.
Neither is limited to a date range.

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
