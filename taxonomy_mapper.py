"""Map syllabus/interview text to taxonomy nodes using transparent baselines."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Sequence

from pipeline.keyword_abstraction import find_topic_mentions

ROOT = Path(__file__).resolve().parents[1]


def load_taxonomy(path: str | Path = ROOT / "data/taxonomy/taxonomy_v1.1.json") -> dict:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not payload.get("topics"):
        raise ValueError("Taxonomy must contain at least one topic")
    ids = [topic.get("topic_id") for topic in payload["topics"]]
    if any(not topic_id for topic_id in ids) or len(ids) != len(set(ids)):
        raise ValueError("Taxonomy topic IDs must be present and unique")
    return payload


def topic_descriptions(taxonomy: dict) -> tuple[list[str], list[str]]:
    ids, descriptions = [], []
    for topic in taxonomy["topics"]:
        ids.append(topic["topic_id"])
        descriptions.append(" ".join(str(topic.get(field, "")) for field in ("name", "description", "topic_id")).strip())
    return ids, descriptions


def map_keywords(text: str, taxonomy: dict) -> list[dict]:
    """Return matched topics; ambiguous text can map to multiple nodes."""
    topic_by_id = {topic["topic_id"]: topic for topic in taxonomy["topics"]}
    return [
        {"topic_id": item["topic_id"], "topic_name": topic_by_id[item["topic_id"]].get("name", item["topic_id"]),
         "score": 1.0, "method": "keyword", "matched_phrase": item["matched_phrase"]}
        for item in find_topic_mentions(text, taxonomy["topics"])
    ]


def map_tfidf(text: str, taxonomy: dict, top_k: int = 5) -> list[dict]:
    """Rank all taxonomy topics by TF-IDF cosine similarity."""
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity

    ids, descriptions = topic_descriptions(taxonomy)
    vectorizer = TfidfVectorizer(ngram_range=(1, 2), lowercase=True)
    topic_vectors = vectorizer.fit_transform(descriptions)
    text_vector = vectorizer.transform([text])
    scores = cosine_similarity(text_vector, topic_vectors)[0]
    order = sorted(range(len(ids)), key=lambda index: (-float(scores[index]), ids[index]))[:max(0, top_k)]
    names = {topic["topic_id"]: topic.get("name", topic["topic_id"]) for topic in taxonomy["topics"]}
    return [{"topic_id": ids[index], "topic_name": names[ids[index]], "score": float(scores[index]),
             "method": "tfidf"} for index in order if scores[index] > 0]


def map_embeddings(text: str, taxonomy: dict, top_k: int = 5,
                   model_name: str = "sentence-transformers/all-MiniLM-L6-v2") -> list[dict]:
    """Optional semantic baseline; requires sentence-transformers and model download."""
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:
        raise RuntimeError("Install evaluation/requirements.txt to use embedding mapping") from exc
    ids, descriptions = topic_descriptions(taxonomy)
    model = SentenceTransformer(model_name)
    topic_vectors = model.encode(descriptions, normalize_embeddings=True)
    query_vector = model.encode([text], normalize_embeddings=True)[0]
    scores = topic_vectors @ query_vector
    names = {topic["topic_id"]: topic.get("name", topic["topic_id"]) for topic in taxonomy["topics"]}
    order = sorted(range(len(ids)), key=lambda index: (-float(scores[index]), ids[index]))[:max(0, top_k)]
    return [{"topic_id": ids[index], "topic_name": names[ids[index]], "score": float(scores[index]),
             "method": "embedding", "model": model_name} for index in order]


def map_text(text: str, taxonomy: dict, methods: Sequence[str] = ("keyword", "tfidf")) -> dict:
    """Run requested mapping methods without silently substituting one for another."""
    output = {}
    for method in methods:
        if method == "keyword":
            output[method] = map_keywords(text, taxonomy)
        elif method == "tfidf":
            output[method] = map_tfidf(text, taxonomy)
        elif method == "embedding":
            output[method] = map_embeddings(text, taxonomy)
        else:
            raise ValueError(f"Unknown mapping method: {method}")
    return output
