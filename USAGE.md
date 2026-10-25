# Running Prepline locally

Prepline currently provides a prototype pipeline for taxonomy mapping, VIT course-catalog search, topic-overlap scoring, and research-readiness checks. It does **not** yet claim a complete syllabus topic extraction or a validated interview corpus.

## Setup

Python 3.10 or newer is recommended.

```bash
python -m venv .venv
# Windows PowerShell:
.venv\\Scripts\\Activate.ps1
# macOS/Linux:
# source .venv/bin/activate
python -m pip install -e .
python -m pip install -r evaluation/requirements.txt
```

Embedding mapping is optional and may download a sentence-transformer model on first use. To avoid it, use the default keyword/TF-IDF methods.

## Commands

Map a question or topic summary:

```bash
python -m pipeline.cli map "Use BFS to find the shortest path in an unweighted graph"
python -m pipeline.cli map "Normalize a relational database" --methods keyword
```

Search the extracted VIT Discipline Core catalog:

```bash
python -m pipeline.cli courses "Operating Systems"
```

Calculate topic overlap from explicitly mapped topic IDs:

```bash
python -m pipeline.cli coverage --syllabus-topic-ids dsa.arrays,dsa.graphs --interview-topic-ids dsa.arrays,dbms.normalization
```

For weighted overlap, create a JSON file such as `weights.json` containing topic IDs and numeric weights, then pass `--weights weights.json`. In weighted mode, the weight file defines the interview-topic universe; `--interview-topic-ids` is still required by the CLI for a consistent interface but is not used by the weighted calculation.

Check whether research data meets the recorded acceptance gates:

```bash
python -m pipeline.cli readiness
```

The readiness command is expected to return a non-zero exit code until source permission/independence checks, the full official syllabus artifact or an accepted alternative, and the minimum verified benchmark set are documented. Do not bypass these gates by marking candidate records as approved without genuine evidence.

## Tests and validation

```bash
python scripts/validate_prepline_data.py
python -m unittest discover -s tests -v
```

Coverage is only a topic-overlap estimate. It does not establish how deeply a course teaches a topic, how likely a company is to ask it, or whether an individual student is interview-ready.
