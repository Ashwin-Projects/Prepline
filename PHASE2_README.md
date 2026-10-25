# Phase 2 — Interview and Syllabus Dataset

## Repository layout

- `data/raw/interviews/amazon_sde1_interview_experiences_phase2.csv`: source-linked index of public Amazon SDE-I experience pages. It contains short topic summaries, not copied source prose.
- `data/raw/syllabi/vit_curriculum_manifest_phase2.csv`: official VIT B.Tech CSE 2024-25 syllabus metadata and relevant course codes.
- `data/raw/syllabi/VIT_CSE_2024_2025.pdf`: target path for the original official syllabus PDF.
- `scripts/download_vit_syllabus.py`: downloads the PDF directly from the official VIT host and prints a SHA-256 checksum.

## Interview CSV schema

Each row records `report_id`, company, role, round summary, question/topic summary, source URL, source date or page date, platform, deduplication status, source review status, and legal review status.

## Dataset quality gates

This is a source-discovery/index stage, not a claim that all source pages have been legally cleared or independently verified.

1. Review each URL and confirm the page describes one actual interview experience for Amazon SDE-I (exclude SDE-II, internships, and unrelated roles).
2. Compare narratives and dates to detect cross-posts or duplicate reports. The CSV explicitly flags duplicate candidates and uncertain overlaps; do not count these toward the minimum.
3. Record the actual experience date where available; do not infer an exact interview date from a page's last-updated date.
4. Confirm source terms and permitted use before automated collection, bulk extraction, or redistribution. Keep only short factual summaries and source URLs in this index.
5. Maintain at least 15 **independent, eligible** reports after these checks. Current rows are discovery candidates; the unique-report gate remains pending review.
6. Download the official VIT PDF using the script, preserve it unchanged, verify text-selectability, and record checksum/metadata. The PDF itself is not committed by this connector workflow.

## Run syllabus downloader

From repository root:

```bash
python scripts/download_vit_syllabus.py
```

The PDF is fetched from the official VIT URL in the manifest. Do not substitute a third-party mirror.

## Downstream ingestion

Only after the review gates pass should the pipeline parse interview reports and syllabus topics into `data/processed/`. Preserve source identifiers and taxonomy version in all derived records.


## Source permission

Public interview pages are not automatically cleared for corpus use. See [source terms review](interviews/SOURCE_TERMS_REVIEW.md) before admitting indexed pages to the production dataset.
