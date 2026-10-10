# Phase 2 — Contributed interview experience intake

Prepline needs first-hand, independently contributed interview experiences. Public visibility alone is not permission to copy reports into a dataset.

## Preferred contribution path

Ask contributors to write a short factual summary of their own interview experience, or submit questions they personally remember. Do not include interviewer names, candidate names, confidential company material, personal contact details, or copied passages from third-party websites.

Before inclusion, record:
- company and role/level;
- approximate date or recruiting cohort (month/year is enough);
- round type and a concise question/topic summary in the contributor's own words;
- whether the contribution is first-hand and whether it was posted elsewhere;
- explicit permission for Prepline to store, transform, and redistribute the contribution under the project's stated data license;
- reviewer, review date, and a duplicate/cohort check.

## Consent and license

A contributor must actively agree to the permission/license text in the intake form. Do not prefill consent or infer it from submitting a report. If permission is not recorded, keep the record out of the production dataset.

Suggested consent text for the contributor form (have the project owner review before launch):

> I confirm that this is my own recollection or a summary written in my own words, that I have removed confidential and identifying information, and that I give Prepline permission to store, transform, and redistribute this contribution under CC BY 4.0 with attribution to the contributor name or pseudonym I provide. I understand that I should not submit confidential interview material or content copied from another source.

This is a suggested intake statement, not legal advice. Obtain appropriate advice for a public production dataset and give contributors a way to request correction/removal where required.

## Deduplication

Compare canonicalized question summaries, company/role, approximate date/cohort, round, and known cross-post links. Two URLs are not necessarily two independent reports. Record the comparison decision and rationale in the ledger.

## Files

- Use `contributor_report_template.csv` as the intake schema.
- Keep pending rows out of the production interview dataset.
- Run `python scripts/check_phase_readiness.py` after review; the readiness check deliberately fails closed when acceptance fields are missing.
