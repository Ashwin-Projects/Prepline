# Existing platforms and approaches

How PREPLINE relates to interview-preparation platforms and to curriculum-mapping research. Checked on 2026-10-23 with
web search; “fetched” means the page itself was opened and read, “search-reported” means only search results or
third-party pages describe it (the official page refused automated access).

| | What it gives a student | Data basis | Curriculum-aware? | Transparent scoring? |
|---|---|---|---|---|
| **LeetCode company tags** (Premium) | Problems filtered by companies that asked them, with a frequency signal | Crowd-reported, undocumented | No | No — LeetCode publishes no definition of “frequency” |
| **GeeksforGeeks company archives** | Per-company preparation pages: practice problems, topics, interview experiences | Candidate-written interview experiences | No | n/a (no score) |
| **InterviewBit** | A levelled programming track (Time Complexity → Arrays → … → DP, Graphs) and company question pages | Curated problems | No | n/a |
| **Course–job fit (Kverne et al., ASEE 2025)** | A course-level alignment measure for a programme | Syllabi vs 197,296 job postings, transformer embeddings | Yes | Method published |
| **PREPLINE** | Per company/role: coverage score, ranked priority gaps, modules to revise, practice links | GfG interview experiences vs the VIT CSE 2024-25 core syllabus | Yes | Yes — versioned formula, taxonomy, config |

## LeetCode company tags (search-reported)

LeetCode Premium's company-tagged lists let users filter problems by the companies that asked them and sort by
frequency; third-party reviews call this the main reason people subscribe. LeetCode does not document how frequency is
computed, and users on its own discussion board report inconsistent orderings and time windows. leetcode.com refused
automated fetches (HTTP 403), so these points rest on search results and community posts, not the official page.
Sources: [LeetCode discuss: “Is LeetCode ordering company questions by frequency incorrectly?”](https://leetcode.com/discuss/general-discussion/1677842/is-leetcode-ordering-company-questions-by-frequency-incorrectly),
[LeetCode discuss: “Sort by Frequency in Tagged Questions”](https://leetcode.com/discuss/feedback/5595287/Sort-by-Frequency-in-Tagged-Questions/),
[Design Gurus: Is LeetCode free or paid?](https://www.designgurus.io/answers/detail/is-leetcode-free-or-paid).

**Difference:** question-level and company-level only; it says nothing about which of those topics a given syllabus
already teaches.

## GeeksforGeeks company archives (fetched)

GfG's *Company Wise Interview Preparation* page links, for each company (Amazon, Microsoft, Flipkart and others),
practice problems, a preparation guide, preparation topics and interview experiences. Individual experiences are
numbered posts of uneven age and detail. PREPLINE's interview data comes **only** from these GfG experiences.
Sources: [GfG Company Wise Interview Preparation](https://www.geeksforgeeks.org/company-preparation/),
[example: Amazon Interview | Set 63 (For SDE-1)](https://www.geeksforgeeks.org/?p=126142).

**Difference:** GfG is the raw material; PREPLINE aggregates it into per-topic importance, deduplicates reports and
applies a density gate before it shows any number.

## InterviewBit (fetched)

InterviewBit's programming course is levelled (Time Complexity, Arrays, Math, … Dynamic Programming, Graphs), and its
FAQ says interview questions “tend to get repeated” and that most are on the site. The site has company interview
question pages; the topic pages do not attribute problems to companies.
Sources: [InterviewBit FAQ](https://www.interviewbit.com/pages/faq/),
[InterviewBit programming course — Graphs](https://www.interviewbit.com/courses/programming/topics/graphs/).

**Difference:** a fixed generic path, not one derived from a company's reports or a student's curriculum.

## One curriculum-mapping approach: Course–Job Fit (fetched)

Kverne, Monteverdi, Polyzou, Lisetti and Bhimani (Florida International University), *Course-Job Fit: Understanding
the Contextual Relationship Between Computing Courses and Employment Opportunities*, 2025 ASEE Annual Conference &
Exposition. They embed course syllabi and job descriptions with transformer models and compare them across 197,296
job postings in five technical fields; core courses aligned better with job demand than electives.
Source: [ASEE 2025 paper page](https://nemo.asee.org/public/conferences/365/papers/48456/view).

**Difference:** closest in method (syllabus text vs industry text in embedding space), but its target is *job
postings* and its unit is the *course*. PREPLINE targets *interview reports* for one company and role, scores at the
taxonomy-topic level, and turns the result into a ranked study list.

## What PREPLINE adds

A curriculum-specific, company-specific score with a published formula, a frozen and versioned taxonomy and config,
an explicit density gate (no number below 15 reports), visible confidence indicators and known mapping errors, and a
study list tied to the student's own course modules.
