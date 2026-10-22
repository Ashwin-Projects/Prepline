# PREPLINE pilot protocol (Phase 16) — pre-registered 2026-10-22, before any data

## Aim

A small descriptive pilot asking whether PREPLINE's company profiles and priority gaps match what students actually
met in interviews. It checks face validity and usefulness; it does not validate S_comp or calibrate the model.

## Participants

- VIT CSE students who took an online assessment or interview with **Amazon, Microsoft, Flipkart or Google**
  (any year, any outcome). Recruited by the project owner.
- Target **n = 10–20** in total. No minimum per company; companies with fewer than 3 participants are reported but not
  interpreted.
- Google has no PREPLINE profile yet (8 of 15 required interview reports), so Google participants answer only the
  usefulness items and the topics-asked question.

## Consent and anonymisation

Information sheet (paste at the top of the form): *"PREPLINE compares the VIT CSE syllabus with topics companies ask
in interviews. This 10-minute form asks which topics you were asked and how well PREPLINE's suggested gaps match your
weak areas. Taking part is voluntary; you can skip any question and withdraw by giving the researcher your participant
id before the analysis date. No name, email or roll number is collected. Answers are reported only as group averages."*

- Consent is a required checkbox; responses without it are excluded and counted.
- The owner hands out **participant ids P01, P02, …** in person. The id-to-person list is kept offline by the owner,
  never in the repository, and destroyed after the analysis. The form does not collect email addresses or names.
- The raw form export (`data/pilot/responses*.csv`) is git-ignored; only the aggregated `results/pilot/` files are
  committed. Free-text comments are not published verbatim.

## Procedure

1. Participant opens the dashboard (Overview + Compare for their company) or a printout of the same pages.
2. Participant fills the Google Form (`docs/pilot/FORM.md`): consent, participant id, company and role, rounds,
   topics actually asked (taxonomy skill names), a 1–5 rating of each of the top-10 priority gaps shown for their
   company, and 5 usefulness items.
3. The owner exports the responses as CSV and runs the analysis (below).

## Pre-registered analysis (decided now; descriptive only)

Profiles are fixed to the saved v1.2 results (26 core courses, config v1.2, taxonomy v1.0). Per participant, then
averaged per company and over all consenting participants:

| Metric | Definition |
|---|---|
| **M1 Topic hit rate** | Of the taxonomy topics the student was actually asked, the share that are in PREPLINE's top-10 most important topics for that company (by I(t)). Students who ticked no taxonomy topic are skipped. |
| **M2 Gap relevance** | Mean 1–5 rating of "this gap matched my real weak areas" over the top-10 priority gaps shown for that company; "N/A" answers are skipped. |
| **M3 Usefulness** | Mean of 5 items rated 1–5 (easy to understand; would help plan preparation; confidence information helped judge trust; would use before a real interview; would recommend). |

Reported: n, mean and range per metric, per company and overall, plus one chart (M1 per company). Companies with no
PREPLINE profile have no M1/M2. **No inferential statistics** (no p-values, confidence intervals or hypothesis
tests) at this n, and no ranking of companies. Any analysis not listed here is labelled exploratory.

**Deferred: γ calibration.** Calibrating γ (and the depth reference values) needs round-level outcomes (pass/fail per
round matched to topic coverage) and a much larger sample. This pilot collects neither, so γ stays at 0.5.

## Known limitations

Self-selected, small sample; recall of interview topics is imperfect; participants see PREPLINE's gaps before rating
them (no blinding); the taxonomy lacks nodes for some common topics (hashing, greedy, intervals), so M1 can be lowered
by questions PREPLINE cannot represent; Microsoft and Flipkart rest on 15 and 17 reports.

## Running the analysis

```powershell
python evaluation/pilot/analyze_pilot.py data/pilot/responses.csv          # first run
python evaluation/pilot/analyze_pilot.py data/pilot/responses.csv --replace  # after more responses
```

Writes `results/pilot/PILOT_RESULTS.md`, `pilot_results.json` and `pilot_m1_topic_hit_rate.png`; the dashboard's
Methodology page then shows the numbers. The script checks that the export has every expected column and refuses
synthetic test data (participant ids starting `SYN`) in `results/pilot/`.
