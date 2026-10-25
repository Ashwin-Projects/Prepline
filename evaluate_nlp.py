"""Phase 13: evaluate Prepline taxonomy matching methods.

Run from repository root:
    pip install -r evaluation/requirements.txt
    python evaluation/evaluate_nlp.py --data evaluation/ground_truth.csv

Ground truth must be manually verified. This script does not generate labels.
"""
import argparse
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import accuracy_score, precision_recall_fscore_support
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.model_selection import train_test_split

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TAXONOMY = ROOT / "data" / "taxonomy" / "taxonomy_v1.1.json"
DEFAULT_DATA = ROOT / "evaluation" / "ground_truth.csv"
RANDOM_STATE = 42


def normalize_text(value):
    return re.sub(r"[^a-z0-9]+", " ", str(value).lower()).strip()


def load_taxonomy(path):
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    topics = payload.get("topics", [])
    if not topics:
        raise ValueError(f"No topics found in {path}")
    topic_ids = [item["topic_id"] for item in topics]
    descriptions = [
        f'{item.get("name", "")} {item.get("description", "")}'.strip()
        for item in topics
    ]
    return payload.get("taxonomy_version", "unknown"), topic_ids, descriptions


def make_splits(frame):
    """70% development, 15% validation, 15% test; fixed seed for reproducibility."""
    counts = frame["expected_topic_id"].value_counts()
    stratify = frame["expected_topic_id"] if len(counts) and counts.min() >= 2 and int(np.ceil(len(frame) * 0.15)) >= len(counts) else None
    dev_val, test = train_test_split(
        frame, test_size=0.15, random_state=RANDOM_STATE, stratify=stratify
    )
    counts = dev_val["expected_topic_id"].value_counts()
    stratify = dev_val["expected_topic_id"] if len(counts) and counts.min() >= 2 and int(np.ceil(len(dev_val) * (0.15 / 0.85))) >= len(counts) else None
    development, validation = train_test_split(
        dev_val, test_size=(0.15 / 0.85), random_state=RANDOM_STATE, stratify=stratify
    )
    return development, validation, test


def keyword_scores(texts, descriptions):
    """Simple Jaccard token-overlap baseline."""
    topic_tokens = [set(normalize_text(d).split()) for d in descriptions]
    rows = []
    for text in texts:
        tokens = set(normalize_text(text).split())
        rows.append([
            len(tokens & target) / max(len(tokens | target), 1)
            for target in topic_tokens
        ])
    return np.asarray(rows, dtype=float)


def tfidf_scores(texts, descriptions):
    vectorizer = TfidfVectorizer(ngram_range=(1, 2), lowercase=True)
    # Fit vocabulary on taxonomy descriptions only to avoid validation/test leakage.
    topic_vectors = vectorizer.fit_transform(descriptions)
    text_vectors = vectorizer.transform(list(texts))
    return cosine_similarity(text_vectors, topic_vectors)


def embedding_scores(texts, descriptions):
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:
        raise RuntimeError(
            "sentence-transformers is not installed; install evaluation/requirements.txt"
        ) from exc
    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    topic_vectors = model.encode(descriptions, normalize_embeddings=True)
    text_vectors = model.encode(list(texts), normalize_embeddings=True)
    return np.asarray(text_vectors @ topic_vectors.T)


def predict(scores, topic_ids, threshold):
    indices = scores.argmax(axis=1)
    values = scores[np.arange(len(scores)), indices]
    return [
        topic_ids[index] if score >= threshold else "__unmapped__"
        for index, score in zip(indices, values)
    ]


def macro_f1(y_true, y_pred):
    return float(precision_recall_fscore_support(
        y_true, y_pred, average="macro", zero_division=0
    )[2])


def tune_threshold(scores, y_true, topic_ids):
    """Choose a threshold on validation data only."""
    candidates = [0.0, 0.10, 0.20, 0.30, 0.35, 0.40, 0.45, 0.50, 0.55, 0.60, 0.70, 0.80]
    scored = [(macro_f1(y_true, predict(scores, topic_ids, t)), t) for t in candidates]
    best_f1, best_threshold = max(scored)
    return best_threshold, best_f1


def calculate_metrics(y_true, y_pred):
    p, r, f1, _ = precision_recall_fscore_support(
        y_true, y_pred, average="macro", zero_division=0
    )
    return {
        "accuracy": round(float(accuracy_score(y_true, y_pred)), 4),
        "macro_precision": round(float(p), 4),
        "macro_recall": round(float(r), 4),
        "macro_f1": round(float(f1), 4),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default=str(DEFAULT_DATA))
    parser.add_argument("--taxonomy", default=str(DEFAULT_TAXONOMY))
    parser.add_argument("--output", default=str(ROOT / "evaluation" / "results.json"))
    parser.add_argument("--allow-unreviewed", action="store_true", help="Diagnostic only: permit candidate labels; output is explicitly marked non-benchmark.")
    args = parser.parse_args()

    frame = pd.read_csv(args.data)
    required = {"raw_text", "expected_topic_id", "taxonomy_version"}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"CSV is missing required columns: {sorted(missing)}")
    frame = frame.dropna(subset=list(required))
    provenance_required = {"source_id", "source_type", "source_url", "review_status", "reviewer", "review_date"}
    missing_provenance = provenance_required - set(frame.columns)
    if missing_provenance and not args.allow_unreviewed:
        raise ValueError(f"Ground-truth CSV is missing provenance/review columns: {sorted(missing_provenance)}")
    if not args.allow_unreviewed:
        accepted_status = frame["review_status"].astype(str).str.strip().str.lower().isin({"verified", "approved"})
        provenance_ok = (
            frame["source_id"].astype(str).str.strip().ne("")
            & frame["source_url"].astype(str).str.match(r"^https?://", case=False)
            & frame["reviewer"].astype(str).str.strip().ne("")
            & frame["review_date"].astype(str).str.strip().ne("")
        )
        rejected = int((~(accepted_status & provenance_ok)).sum())
        if rejected:
            raise ValueError(f"{rejected} rows are not explicitly verified/approved with reviewer, date, source ID, and URL. Candidate labels are not benchmark ground truth. Use --allow-unreviewed only for a clearly labelled diagnostic run.")
    frame["raw_text"] = frame["raw_text"].astype(str).str.strip()
    frame = frame[frame["raw_text"].ne("")]
    duplicate_pairs = frame.duplicated(subset=["raw_text", "expected_topic_id"]).sum()
    if duplicate_pairs:
        raise ValueError(f"Found {int(duplicate_pairs)} duplicate raw_text/topic pairs. Deduplicate before evaluation.")
    if len(frame) < 20:
        raise ValueError(
            f"Only {len(frame)} labelled rows found. Add manually verified examples "
            "before treating the benchmark as meaningful."
        )

    taxonomy_version, topic_ids, descriptions = load_taxonomy(args.taxonomy)
    if not frame["taxonomy_version"].eq(taxonomy_version).all():
        raise ValueError(f"All rows must use taxonomy_version={taxonomy_version!r}.")
    unknown = sorted(set(frame["expected_topic_id"]) - set(topic_ids))
    if unknown:
        raise ValueError(f"Ground-truth topic IDs absent from taxonomy: {unknown}")

    development, validation, test = make_splits(frame)
    print(
        f"Taxonomy {taxonomy_version}; rows={len(frame)}; "
        f"development={len(development)}, validation={len(validation)}, test={len(test)}"
    )
    print("The development split is reserved for development; thresholds use validation.")
    print("Do not tune methods or thresholds after inspecting final test results.")

    methods = {
        "keyword": keyword_scores,
        "tfidf": tfidf_scores,
        "sentence_embeddings": embedding_scores,
    }
    y_val = validation["expected_topic_id"].astype(str).tolist()
    y_test = test["expected_topic_id"].astype(str).tolist()
    report = {
        "taxonomy_version": taxonomy_version,
        "dataset_rows": int(len(frame)),
        "split_sizes": {
            "development": int(len(development)),
            "validation": int(len(validation)),
            "test": int(len(test)),
        },
        "random_state": RANDOM_STATE,
        "benchmark_validity": "diagnostic_only_unreviewed_labels" if args.allow_unreviewed else "reviewed_labels_required",
        "methods": {},
        "notes": [
            "Ground-truth labels must be manually verified.",
            "Threshold selection uses validation data only.",
            "Report final test metrics only after freezing method and threshold choices.",
            "Inspect per-topic errors and class imbalance before drawing conclusions.",
            "The development split is held for development; zero-shot baselines do not fit parameters on it.",
        ],
    }

    for name, scorer in methods.items():
        try:
            val_scores = scorer(validation["raw_text"].tolist(), descriptions)
            threshold, val_f1 = tune_threshold(val_scores, y_val, topic_ids)
            test_scores = scorer(test["raw_text"].tolist(), descriptions)
            test_predictions = predict(test_scores, topic_ids, threshold)
            report["methods"][name] = {
                "threshold": float(threshold),
                "validation_macro_f1": round(val_f1, 4),
                "test_metrics": calculate_metrics(y_test, test_predictions),
                "per_topic_test_metrics": {
                    topic: {
                        "support": int(sum(label == topic for label in y_test)),
                        "precision": round(float(precision_recall_fscore_support(y_test, test_predictions, labels=[topic], average=None, zero_division=0)[0][0]), 4),
                        "recall": round(float(precision_recall_fscore_support(y_test, test_predictions, labels=[topic], average=None, zero_division=0)[1][0]), 4),
                        "f1": round(float(precision_recall_fscore_support(y_test, test_predictions, labels=[topic], average=None, zero_division=0)[2][0]), 4),
                    } for topic in sorted(set(y_test))
                },
            }
            print(f"{name}: threshold={threshold:.2f}; test={report['methods'][name]['test_metrics']}")
        except RuntimeError as exc:
            report["methods"][name] = {"skipped": str(exc)}
            print(f"{name}: skipped ({exc})")

    Path(args.output).write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Saved report: {args.output}")


if __name__ == "__main__":
    main()
