# Label adjudication — benchmark v1.0 (`labels_v1.0.csv`)

**In one sentence:** κ = 0.812 is agreement between two independent LLM labellers (a Claude draft vs a fresh Claude
subagent); their disagreements were adjudicated by the human owner; 191 rows are LLM cross-checked only, not
individually human-reviewed.

## Process

1. **LLM draft.** Claude labelled all 247 rows from `raw_text`, `LABELLING_GUIDE.md` and `TAXONOMY_CHEATSHEET.md`
   only (no embedding matcher, no similarity scores), with a confidence per row.
2. **Independent second labeller.** A separate Claude subagent saw only `item_id`, `source_type`, `raw_text`, the cheat
   sheet and the guide, and not the drafts. It labelled all 247 rows. Primary-label agreement with the draft:
   211 agree, 8 partial, 28 disagree; **Cohen's kappa 0.812**. Agreeing rows became `llm_cross_checked`.
   56 rows needed review: the 36 partial/disagree rows and 20 agreeing rows where one side had low confidence.
3. **Human rules.** The project owner approved rules R1–R5 (2026-10-22). Rows they clearly cover are
   `label_source = human_rule_adjudicated`, `reviewed = True`, and `review_notes` starts with the rule id, followed by
   both LLM labels. The `agreement` column keeps the original LLM comparison.

| Rule | Text | Rows |
|---|---|---|
| R1 | No generic parent nodes: if no specific node fits (hashing, greedy, intervals, …), `none` with `gap: <concept>` | 25 |
| R2 | Pure cryptography (DES/AES/MD5/SHA/cipher maths) → `none`; network security (TLS, firewalls, attacks) → `cn.network_security` | 7 |
| R3 | Language-syntax units (e.g. "Arrays and Functions in C") → `none` | 6 |
| R4 | An algorithm genuinely taught in any course is mapped (AI BFS/DFS → `dsa.graphs`); minimax/alpha-beta → `none` | 4 |
| R5 | Partial agreement → the more specific node is primary, the other secondary | 6 |
| | **Total adjudicated** | **48** |

R5 note: for BCSE303L_mod_7, BCSE308L_mod_3 and BCSE308P_exp_2 the other label was a domain root (`os`, `cn`), so it
was not kept as a secondary (R1). The owner confirmed this reading.

4. **Individual human decisions.** The owner decided the 8 rows the rules did not clearly cover
   (`label_source = human_adjudicated`, `reviewed = True`, `review_notes` starts with "human").

| item_id | Text | Decision |
|---|---|---|
| BCSE301P_exp_3 | ER diagram for requirements (SE lab) | keep `dbms.relational_model` |
| BCSE303P_exp_11 | File locking mechanism | keep `os.file_systems` + `os.process_synchronization` |
| BCSE309P_exp_10 | Web app with JSON web tokens | keep `cn.network_security` + `cn.application_layer` |
| BCSE308P_exp_3 | Flow control mechanisms (data-link lab) | `none`, gap: data-link flow control |
| AMZ013_L50 | "heap-based scheduling problem" | `none`, gap: priority-queue scheduling |
| AMZ016_L66 | LIS bridge problem | `dsa.dp.1d` + `dsa.dp.lcs` |
| AMZ020_L86 | Minimum Skips to Arrive on Time | `dsa.dp.1d` |
| BMAT205L_mod_6 | Trees, spanning trees, cut-sets | `dsa.trees` + `dsa.graphs` |

## Gold v1.0

All 56 review rows are settled (48 by rule, 8 individually) and `reviewed = True`. The other 191 rows are
`llm_cross_checked` (both LLM labellers chose the same primary) with `reviewed = False`; they are gold v1.0 on the
strength of that agreement between two LLM labellers, not a human check. `python evaluation/benchmark/validate_labels.py` reports these counts.

Gold v1.0 is frozen: BCSE203E Web Programming, supplied after these labels were built, has no rows here or in
`splits_v1.0.csv`, although it is scored in the v1.2 results.
