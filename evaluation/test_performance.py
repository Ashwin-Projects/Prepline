"""
Item 8: batch concept encoding and the interview-importance cache.

Batch encoding must give the same matches as encoding concepts one at a time,
with one encode() call per source. The importance cache is keyed on
(company, role, taxonomy_version, config_version, questions.csv SHA-256).
"""
import csv

import pytest
from sentence_transformers import util

from pipeline import embeddings, scoring, taxonomy_mapper

CONCEPTS = ["binary search tree", "deadlock", "rate limiting", "sql joins", "leetcode", "hash map"]


@pytest.fixture
def loaded_taxonomy():
    embeddings.load_taxonomy(embeddings.DEFAULT_TAXONOMY_PATH)
    return embeddings


def _reference_matches(concept, threshold):
    model = embeddings.load_model()
    emb = model.encode(concept, convert_to_tensor=True)
    scores = util.cos_sim(emb, embeddings._taxonomy_embeddings)[0]
    return {
        embeddings._taxonomy_nodes[i]["topic_id"]: float(scores[i])
        for i in range(len(embeddings._taxonomy_nodes))
        if float(scores[i]) >= threshold
    }


def test_batch_matches_equal_per_concept(loaded_taxonomy):
    threshold = embeddings.SIMILARITY_THRESHOLD
    ids, scores, unmapped = embeddings.match_concepts_to_taxonomy(CONCEPTS, threshold=threshold)

    expected: dict = {}
    expected_unmapped = []
    for concept in CONCEPTS:
        ref = _reference_matches(concept, threshold)
        if not ref:
            expected_unmapped.append(concept)
        for topic_id, score in ref.items():
            expected[topic_id] = max(score, expected.get(topic_id, score))

    assert set(ids) == set(expected)
    assert unmapped == expected_unmapped
    for topic_id, score in expected.items():
        assert scores[topic_id] == pytest.approx(score, abs=1e-5)


def test_single_encode_call_per_source(loaded_taxonomy, monkeypatch):
    model = embeddings.load_model()
    real_encode = model.encode
    calls = []

    def counting_encode(*args, **kwargs):
        calls.append(args)
        return real_encode(*args, **kwargs)

    monkeypatch.setattr(model, "encode", counting_encode)
    embeddings.match_concepts_to_taxonomy(CONCEPTS)
    assert len(calls) == 1


@pytest.fixture
def questions_csv(tmp_path):
    path = tmp_path / "questions.csv"
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["report_id", "question_text", "topic"])
        writer.writeheader()
        writer.writerow({"report_id": "R1", "question_text": "Deadlock Detection and Prevention", "topic": ""})
    return str(path)


@pytest.fixture
def mapping_calls(monkeypatch):
    real = taxonomy_mapper.map_source_to_taxonomy
    calls = []

    def counting(*args, **kwargs):
        calls.append(kwargs.get("source_id"))
        return real(*args, **kwargs)

    monkeypatch.setattr(taxonomy_mapper, "map_source_to_taxonomy", counting)
    scoring.clear_importance_cache()
    yield calls
    scoring.clear_importance_cache()


def test_importance_cache_hit(questions_csv, mapping_calls):
    first = scoring.get_interview_importance("Amazon", "SDE-1", questions_csv, total_reports_count=21)
    after_first = len(mapping_calls)
    assert after_first > 0

    second = scoring.get_interview_importance("Amazon", "SDE-1", questions_csv, total_reports_count=21)
    assert len(mapping_calls) == after_first
    assert second == first

    scoring.clear_importance_cache()
    scoring.get_interview_importance("Amazon", "SDE-1", questions_csv, total_reports_count=21)
    assert len(mapping_calls) == 2 * after_first


def test_cache_key_varies_by_role(questions_csv, mapping_calls):
    scoring.get_interview_importance("Amazon", "SDE-1", questions_csv, total_reports_count=21)
    n = len(mapping_calls)
    scoring.get_interview_importance("Amazon", "SDE-2", questions_csv, total_reports_count=21)
    assert len(mapping_calls) == 2 * n


def test_cache_key_varies_by_questions_hash(questions_csv, mapping_calls):
    scoring.get_interview_importance("Amazon", "SDE-1", questions_csv, total_reports_count=21)
    n = len(mapping_calls)
    with open(questions_csv, "a", encoding="utf-8", newline="") as f:
        f.write("R2,Binary search tree insertion,\n")
    scoring.get_interview_importance("Amazon", "SDE-1", questions_csv, total_reports_count=21)
    assert len(mapping_calls) > n
