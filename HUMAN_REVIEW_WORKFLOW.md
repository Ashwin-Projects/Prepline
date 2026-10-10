# Human review workflow

Run from the repository root:

```bash
python scripts/review_phase13_candidates.py
```

The script presents candidate prompts, taxonomy IDs, source links, and provenance notes. It requires an explicit reviewer identifier and a per-row approve/reject/skip decision. It writes decisions to `evaluation/ground_truth.csv`; it does not approve anything automatically.

Before approving a row:
1. Open and verify the cited source.
2. Check source license/permission permits this use and redistribution.
3. Confirm the prompt summary is faithful to the source and does not reproduce a protected passage.
4. Confirm the taxonomy topic is correct and taxonomy version matches the current schema.
5. Reject duplicate text/topic pairs or ambiguous labels.

**Do not approve a row merely to increase the count.** Reaching 200 approved labels does not by itself satisfy Phase 2's separate interview-report requirement. The current licensed CodePrep source is a practice-question bank, not a candidate interview-experience corpus.
