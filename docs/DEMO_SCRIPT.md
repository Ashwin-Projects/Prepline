# PREPLINE — 5-minute demo script

Start everything first with `scripts/start_demo.ps1` (backend :8000, dashboard :5173), select **Amazon SDE-1**, light
theme. Backup if the live demo fails: `docs/pilot/demo.webm` (82 s walkthrough) and `docs/pilot/img/*.png`.

Mapped to the eight review points, in order.

| # | Review point | Time | Where | Say / show |
|---|---|---|---|---|
| 1 | **A couple of companies + roles, full system run** | 0:00–0:40 | Overview, target switcher | “Four company/role pairs are configured — Amazon SDE-1, Microsoft SDE-1, Flipkart SDE-1, Google SWE-L3 — and scored in one run (`evaluation/run_all_targets.py`) against all 26 VIT CSE 2024-25 core courses (209 units).” Switch Amazon → Microsoft → Flipkart. |
| 2 | **15–20 unique interview experiences per pair** | 0:40–1:10 | Overview → Data card; Confidence → Insufficient data | “Deduplicated GfG experiences, one report id each: Amazon 21 collected → 18 usable, Microsoft 17 → 15, Flipkart 20 → 17. Google has 16 but only 8 usable, so it is gated out and shows *Insufficient data*, not a number.” Click Google. |
| 3 | **Versioned taxonomy with stable topic IDs** | 1:10–1:40 | Topic explorer; Methodology → versioning | “Taxonomy v1.0: 83 topics in DSA, DBMS, OS, Networks and System Design, each with a stable id such as `dbms.sql.subqueries`. Results store the taxonomy and config version; a change makes a new version and never rewrites old results.” |
| 4 | **Syllabus→taxonomy and interview→taxonomy mappings** | 1:40–2:20 | Methodology → pipeline; Topic explorer (coverage source) | “Two-pass abstraction, then local MiniLM similarity, τ = 0.50: syllabus units map to high-level concepts, interview questions to granular skills (60/40 credit when several match). Granular topics inherit coverage from their high-level parent.” |
| 5 | **Overall coverage score + topic-level priority gaps** | 2:20–3:10 | Overview → score, Priority gaps, What to study next, Download report (PDF) | “S_comp is importance-weighted coverage — Amazon 88.8, provisional. PriorityGap = I·(1 − coverage) ranks what to study; each gap lists the VIT modules to revise and two checked practice pages; the PDF bundles it all.” Open the PDF. |
| 6 | **Confidence indicators: insufficient data, fallback depth, unmapped terms** | 3:10–3:40 | Confidence page; badge on Overview | “Three indicators next to every number: the 15-report gate, topics at fallback depth, and interview terms that matched nothing. Microsoft has no margin above the gate, so its badge says Medium.” |
| 7 | **Benchmark with existing systems** | 3:40–4:20 | Benchmark page; `docs/EXISTING_PLATFORMS.md` | “247 gold labels; production MiniLM vs keyword match, TF-IDF and MiniLM on names. Test macro-F1 is low for all (0.21 production, 0.39 keyword) on 45 rows, so production is kept and its errors are published. Against LeetCode, GfG, InterviewBit and a curriculum-to-jobs study, PREPLINE is the only one scoring a given syllabus against a company's interview topics with a published formula.” |
| 8 | **Small pilot study** | 4:20–5:00 | Methodology → Participant pilot, Retrospective validation; `docs/pilot/` | “Students pick a company, rate its top-10 gaps against their weak areas (1–5); those who took its assessment tick the topics they met; everyone rates PREPLINE. Pre-registered: M1 hit rate vs the top-10 topics by importance, M2 gap match, M3 rating, per track. No responses analysed yet; the interim retrospective check gives top-10 hit rates of 88 / 55 / 48 % vs ~20 % random.” |

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
