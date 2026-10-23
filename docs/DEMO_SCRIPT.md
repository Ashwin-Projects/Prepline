# PREPLINE — 5-minute demo script

Start everything first with `scripts/start_demo.ps1` (backend :8000, dashboard :5173), select **Amazon SDE-1**, light
theme. Backup if the live demo fails: `docs/pilot/demo.webm` (82 s walkthrough) and `docs/pilot/img/*.png`.

The eight review points below are a standard project-review structure (no official list is in the repository);
reorder the sections if the panel uses a different rubric.

| # | Review point | Time | Where | Say |
|---|---|---|---|---|
| 1 | **Problem & motivation** | 0:00–0:30 | Overview header | “University syllabi teach theory; interviews test a narrow applied slice. PREPLINE measures, per company and role, how much of what interviewers ask the VIT CSE 2024-25 core syllabus covers, and what to study next.” |
| 2 | **Existing work & gap** | 0:30–0:50 | (spoken) `docs/EXISTING_PLATFORMS.md` | “LeetCode, GfG and InterviewBit tell you *which questions* a company asks; curriculum-mapping studies compare syllabi with *job postings*. None scores a specific curriculum against a specific company's interview topics with a transparent, versioned formula.” |
| 3 | **Architecture & method** | 0:50–1:40 | Methodology page | “Two-pass abstraction → local MiniLM embeddings, τ = 0.50 → deterministic 60/40 credit split → importance I(t) per report, depth-weighted coverage, S_comp over the topics with I(t) > 0, and PriorityGap = I·(1 − coverage). Taxonomy v1.0 and config v1.2 are frozen and stamped on every result.” (`docs/ARCHITECTURE.md`) |
| 4 | **Data** | 1:40–2:10 | Overview → Data card; Confidence page | “Public GfG interview experiences, deduplicated; a 15-report density gate. Amazon 18, Microsoft 15, Flipkart 17 usable reports; Google has 8, so it shows *Insufficient data* instead of a number.” Click Google, then back. |
| 5 | **Implementation & product** | 2:10–3:10 | Overview → Priority gaps → What to study next → Download report (PDF); Compare | “Each gap lists the VIT modules its coverage comes from — loose matches are flagged — and two checked practice pages. The PDF carries the provisional score, confidence, gaps, study plan, versions and a disclaimer.” Open the PDF. Show Compare: “similar scores are not a ranking.” |
| 6 | **Evaluation** | 3:10–3:50 | Benchmark page | “247 gold labels; test macro-F1 is low for every matcher (0.21 for production MiniLM, 0.39 for keywords) on a 45-row test set. We kept production and published the errors under Known mapping limitations.” |
| 7 | **Validation** | 3:50–4:30 | Methodology → Retrospective validation, Participant pilot | “Leave-one-report-out top-10 hit rate: Amazon 88 %, Microsoft 55 %, Flipkart 48 % vs ~20 % random. The student pilot form is ready (pre-registered: topic hit rate, gap match, rating, per track); no responses are analysed yet.” |
| 8 | **Limitations & future work** | 4:30–5:00 | Overview → Known mapping limitations | “Matcher errors (DP false negatives, Java I/O → messaging), no taxonomy node for hashing or greedy, one source site, small samples. Next: a larger benchmark, more sources, the pilot results, then γ calibration.” |

## Five likely questions — honest answers

1. **“κ = 0.81 — who were the labellers?”** Two LLM labellers: a Claude draft and an independent fresh Claude
   subagent. κ = 0.812 is LLM–LLM agreement, not human inter-rater reliability. Disagreements were adjudicated by
   rules (48) and by me (8); 191 rows were only LLM cross-checked. A human second labeller is the next step.
2. **“Flipkart 89.7, Microsoft 89.1, Amazon 88.8 — so Flipkart fits VIT best?”** No. Each company has its own scoring
   universe (Amazon 9 topics, Microsoft 14, Flipkart 13), so the scores share neither denominator nor topic set.
   Similar scores are not a ranking; the dashboard and the PDF both say so.
3. **“Retrospective validation 88 % — isn't that strong evidence?”** It is inflated. When a company's topic universe is
   small (Amazon: 9 topics with any importance), a top-10 list covers almost all of it, so a high hit rate is nearly
   guaranteed. The held-out topics also come from the same matcher, so mapping errors cancel instead of showing. It
   checks internal consistency, not real-world validity; that is what the student pilot is for.
4. **“Where does the interview data come from?”** Only GeeksforGeeks interview experiences: one site, shared writing
   style, self-selected authors, uneven dates. Results describe what GfG posters reported, not companies' official
   processes. More sources (with permissive terms) are future work.
5. **“How reliable is the benchmark with 45 test rows?”** Not very: 35 syllabus + 10 interview rows from two courses and
   three reports. Dev, val and test disagree on the best matcher, so the honest conclusion is “too small to decide”.
   We did not tune τ or the matcher on it.
