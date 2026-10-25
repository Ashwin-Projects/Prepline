# Source terms review — Phase 2

Review date: 2026-10-10  
Purpose: decide whether publicly indexed interview-experience pages can be treated as an automatically usable corpus for Prepline.

## Findings from the current published terms

- **LeetCode:** https://leetcode.com/terms/ states that crawling, scraping, and spidering any part of the service are prohibited, and its content section describes platform content as copyrighted/proprietary unless otherwise specified.
- **GeeksforGeeks:** https://www.geeksforgeeks.org/legal/terms-of-use/ prohibits systematically retrieving data/content to create or compile a collection, compilation, database, or directory without written permission. It also prohibits data mining/robots and unauthorized automated extraction.
- **GeeksforGeeks copyright information:** https://www.geeksforgeeks.org/legal/copyright-information/ says unauthorized transmission, publication, or use of site content without prior knowledge or written permission is prohibited.

## Decision for this repository

**Permission is not established.** Public visibility is not equivalent to permission to collect and redistribute the content. The existing interview rows and 202 mapping candidates contain short factual topic summaries and source URLs; they must remain review candidates and must not be represented as a legally cleared production dataset.

Do not run automated scraping against these services. Before using their material as the Phase 2/Phase 13 corpus, obtain written permission or replace those records with data whose license clearly permits the intended collection, storage, transformation, and evaluation.

## What is still required

1. Obtain written permission from the relevant source owner(s), or replace the source corpus with appropriately licensed / directly contributed reports.
2. Review at least 15 distinct eligible reports, verify role/cohort fit, and record report-level deduplication evidence.
3. Record the actual permission basis, reviewer, and review date in the source review ledger.
4. Only then consider rows for the production dataset. Do not infer legal approval from a public URL, search snippet, or this summary.

This is a source-terms risk review, not legal advice or a legal opinion.

## Additional source checked: Jointaro / Taro

Checked 2026-10-10:
- Terms: https://www.jointaro.com/terms/
- Robots.txt: https://www.jointaro.com/robots.txt
- The terms page's prohibited-uses section expressly prohibits spidering, crawling, and scraping. The robots file allows general crawling, but that does not override the terms or grant a redistribution license.
- Decision: **not cleared for bulk collection or redistribution**. The existing user-provided Jointaro CSV remains a discovery index only until the operator grants written permission or the team confirms a separate license for the exact content and intended use. Do not infer that robots.txt Allow: / means content reuse is authorized.

## Source decisions

| Source | Current decision | Allowed next step |
|---|---|---|
| LeetCode Discuss | Not cleared; terms prohibit crawling/scraping/spidering | Request written permission or exclude from production corpus |
| GeeksforGeeks | Not cleared; terms restrict systematic compilation/data mining without permission | Request written permission or exclude from production corpus |
| Jointaro / Taro | Not cleared; terms prohibit spidering/crawling/scraping | Request written permission or exclude from production corpus |
| CodePrep CC BY 4.0 question bank | Candidate practice-question source; verify attribution and exact license provenance in LICENSED_QUESTION_SOURCE.md | May support a separately described practice-question benchmark; it does not count as interview-experience reports |
| Direct first-person contributions | Potentially eligible only with explicit contributor permission covering storage, transformation, evaluation, and repository publication | Use the contributor intake template and retain permission evidence |

No source above is being declared legally approved by this file. This is a conservative project-level screening, not legal advice.
