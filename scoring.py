"""Coverage scoring helpers for Prepline; scores describe mappings, not student readiness."""
from __future__ import annotations

from collections import Counter
from typing import Iterable


def topic_coverage(syllabus_topic_ids: Iterable[str], interview_topic_ids: Iterable[str]) -> dict:
    """Compute unique-topic coverage and interview-topic gaps."""
    syllabus = set(syllabus_topic_ids)
    interview = list(interview_topic_ids)
    counts = Counter(interview)
    unique_interview = set(counts)
    covered = unique_interview & syllabus
    gaps = unique_interview - syllabus
    denominator = len(unique_interview)
    return {
        "coverage_ratio": len(covered) / denominator if denominator else 0.0,
        "coverage_percent": round(100 * len(covered) / denominator, 2) if denominator else 0.0,
        "unique_interview_topics": denominator,
        "covered_topics": sorted(covered),
        "gap_topics": sorted(gaps),
        "interview_frequency": dict(sorted(counts.items())),
        "interpretation": "Topic overlap only; not a measure of course depth, interview probability, or student proficiency.",
    }


def weighted_coverage(syllabus_topic_ids: Iterable[str], interview_topic_weights: dict[str, float]) -> dict:
    """Weight interview topics by importance; syllabus presence is membership in the syllabus set."""
    if any(float(weight) < 0 for weight in interview_topic_weights.values()):
        raise ValueError("Interview topic weights must be non-negative")
    syllabus = set(syllabus_topic_ids)
    weights = {topic: float(weight) for topic, weight in interview_topic_weights.items()}
    total = sum(weights.values())
    covered = sorted(topic for topic, weight in weights.items() if topic in syllabus and weight > 0)
    gaps = sorted(topic for topic, weight in weights.items() if topic not in syllabus and weight > 0)
    covered_weight = sum(weights[topic] for topic in covered)
    ratio = covered_weight / total if total else 0.0
    return {
        "coverage_ratio": ratio,
        "coverage_percent": round(100 * ratio, 2),
        "covered_topics": covered,
        "gap_topics": gaps,
        "total_weight": total,
        "covered_weight": covered_weight,
        "interpretation": "Weighted topic overlap only; not a measure of course depth or student proficiency.",
    }
