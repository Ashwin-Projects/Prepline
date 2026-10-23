# PREPLINE pilot protocol (Phase 16) — pre-registered 2026-10-22, revised 2026-10-23 for the final form, before any data

## Aim

A small descriptive pilot asking whether PREPLINE's top-10 priority gaps per company match students' own weak areas
and the topics students actually met in assessments. It checks face validity and usefulness; it does not validate
S_comp or calibrate the model.

## Participants (students only; no faculty)

VIT CSE students, recruited by the project owner. Every participant chooses **one company — Amazon, Microsoft or
Flipkart** (Google has no PREPLINE profile: 8 of 15 required interview reports) and rates that company's gaps. Q3
splits them into two tracks:

| Track | Who (Q3) | Answers | Target n |
|---|---|---|---|
| **A** | Has taken an online assessment or interview with that company (any outcome, internships included) | Q2 gap match, Q4 topics encountered, Q5 rating | 10–20 |
| **B** | Has not | Q2 gap match (perceived), Q5 rating | 10–20 |

Results are always reported **per track and per company with their n**; cells with fewer than 3 participants are
reported but not interpreted.

## Consent and anonymisation

The form description is the information sheet (`docs/pilot/FORM.md`). Consent is a required checkbox; responses
without it are excluded and counted. The form collects no name, email, roll number or participant id. The raw export
(`data/pilot/responses*.csv`) is git-ignored; only the aggregated `results/pilot/` files are committed. Free-text
answers (Q4 "Other", Q6) are not published verbatim.

## The form (built by hand in Google Forms; exact text in `docs/pilot/FORM.md`)

1. Consent checkbox.
2. **Q1** company (Amazon / Microsoft / Flipkart) → one section per company.
3. **Q2** grid "How well do the identified topic gaps match your own weak areas?" — rows = that company's top-10
   priority gaps (Amazon has 9: only 9 topics have a positive gap); columns 1 Not at all, 2 Slightly, 3 Moderately,
   4 Very well, 5 Exactly matches my weak areas.
4. **Q3** "Have you taken an online assessment or interview with this company?" Yes → Track A (Q4); No → Track B (Q5).
5. **Q4** (Track A) "Which technical topics did you encounter in that assessment or interview?" — 20 checkbox options:
   16 topic areas mapped to taxonomy v1.0 topics, plus Hashing, Greedy algorithms, Other and Cannot recall.
6. **Q5** grid "Please rate PREPLINE." — 4 statements, 1 Strongly disagree … 5 Strongly agree (both tracks; Track A
   reaches it after Q4).
7. **Q6** "What would most improve PREPLINE?" (optional).

## Pre-registered analysis (decided now; descriptive only)

Profiles are fixed to the saved v1.2 results (26 core courses, config v1.2, taxonomy v1.0). Per participant, then
averaged per company and per track:

| Metric | Definition |
|---|---|
| **M1 Topic hit rate** (Track A) | Of the Q4 options ticked that map to taxonomy topics, the share whose topics include at least one of the company's top-10 priority gaps (mapping in `docs/pilot/FORM.md`). **Hashing, Greedy algorithms and Other** have no taxonomy node: they are left out of M1 and reported separately (how many Track A participants ticked each). **Cannot recall** is excluded. A participant with no mapped option has no M1. |
| **M2 Gap match** (both tracks) | Mean Q2 rating (1–5) over the gap rows answered. Track B's is perceived, not tested: it is reported separately and never pooled with Track A's. |
| **M3 Rating** (both tracks) | Mean of the 4 Q5 statements (1–5); also reported for both tracks together. |

Reported: n, mean and range per metric, per company and per track; one chart (Track A M1 per company). **No
inferential statistics** (no p-values, confidence intervals or hypothesis tests) at this n, and no ranking of
companies. Any analysis not listed here is labelled exploratory.

**Deferred: γ calibration.** Calibrating γ (and the depth reference values) needs round-level outcomes and a much
larger sample. This pilot collects neither, so γ stays at 0.5.

## Known limitations

Self-selected, small sample; recall of interview topics is imperfect; participants see PREPLINE's gaps before
answering Q4 (no blinding); Q4 options are coarser than taxonomy topics, so an option counts as a hit when any of its
topics is a top-10 gap (this favours broad options such as "Dynamic programming"); the taxonomy has no node for
hashing or greedy algorithms; Microsoft and Flipkart rest on 15 and 17 reports.

## Running the analysis

Download the responses as CSV (Responses → ⋮ → Download responses (.csv)) to `data/pilot/responses.csv`, then:

```powershell
python evaluation/pilot/analyze_pilot.py data/pilot/responses.csv            # first run
python evaluation/pilot/analyze_pilot.py data/pilot/responses.csv --replace  # after more responses
```

Writes `results/pilot/PILOT_RESULTS.md`, `pilot_results.json` and `pilot_m1_topic_hit_rate.png`; the dashboard's
Methodology page then shows the numbers. The script checks that the export has every expected column (Q2 columns
repeat once per company section; that is expected) and refuses synthetic test data in `results/pilot/`.
