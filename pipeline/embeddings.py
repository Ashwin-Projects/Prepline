"""
Phase 5 - Local Sentence Embeddings

Loads all-MiniLM-L6-v2 locally (no external API calls). Embeds taxonomy node descriptions once and caches them, then matches a list of
intermediate concepts (as produced by keyword_abstraction.two_pass_abstract's `intermediate_concepts` field)
against taxonomy nodes via cosine similarity.

Output shape matches the existing repo contract in keyword_abstraction.py:
- matched_topic_ids: List[str]
- similarity_scores: Dict[str, float]   (topic_id -> score, not a parallel list, so scores can never drift out of alignment with IDs)
"""
import json
from typing import List, Dict, Tuple
from sentence_transformers import SentenceTransformer, util

SIMILARITY_THRESHOLD = 0.50  # MVP baseline (Phase 5.3) - frozen after benchmark

_model = None
_taxonomy_nodes = None
_taxonomy_embeddings = None


def load_model():
    global _model
    if _model is None:
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


def load_taxonomy(taxonomy_path: str) -> int:
    """
    Loads taxonomy_v*.json and pre-computes + caches embeddings for every
    node's description. Call this once at pipeline startup, not per-item.

    Expected taxonomy node shape (adjust the key names here if the real
    Sprint 2 file differs - only `topic_id` and a description field are
    required):
    {"topic_id": "dsa.trees.bst", "type": "granular_skill", "description": "..."}
    """
    global _taxonomy_nodes, _taxonomy_embeddings
    model = load_model()
    with open(taxonomy_path, "r") as f:
        data = json.load(f)
    nodes = data["nodes"] if isinstance(data, dict) and "nodes" in data else data
    _taxonomy_nodes = nodes
    descriptions = [n.get("description", n["topic_id"]) for n in nodes]
    _taxonomy_embeddings = model.encode(descriptions, convert_to_tensor=True)
    return len(nodes)


def _match_single_concept(concept_text: str, threshold: float) -> List[Tuple[str, float]]:
    """
    Embed one concept string, return every taxonomy node scoring >=
    threshold, sorted by similarity descending, exact-score ties broken
    alphabetically by topic_id (Phase 6.4).
    """
    if _taxonomy_nodes is None or _taxonomy_embeddings is None:
        raise RuntimeError("Call load_taxonomy(path) before matching.")

    model = load_model()
    concept_emb = model.encode(concept_text, convert_to_tensor=True)
    scores = util.cos_sim(concept_emb, _taxonomy_embeddings)[0]

    matches = [
        (_taxonomy_nodes[i]["topic_id"], float(scores[i]))
        for i in range(len(_taxonomy_nodes))
        if float(scores[i]) >= threshold
    ]
    matches.sort(key=lambda x: (-x[1], x[0]))
    return matches


def match_concepts_to_taxonomy(
    concepts: List[str], threshold: float = SIMILARITY_THRESHOLD
) -> Tuple[List[str], Dict[str, float]]:
    """
    Phase 5, applied across an entire source's `intermediate_concepts` list (i.e. everything two_pass_abstract() extracted for one
    source_id). Matches each concept independently, then merges results by topic_id - keeping the best score seen for that topic across all
    concepts belonging to this source.

    Returns (matched_topic_ids, similarity_scores) in exactly the shape two_pass_abstract()'s output dict expects, so the caller can just do:
        record["matched_topic_ids"], record["similarity_scores"] = \\ 
        match_concepts_to_taxonomy(record["intermediate_concepts"])
    """
    best_by_topic: Dict[str, float] = {}
    for concept in concepts:
        for topic_id, score in _match_single_concept(concept, threshold):
            if topic_id not in best_by_topic or score > best_by_topic[topic_id]:
                best_by_topic[topic_id] = score

    ordered = sorted(best_by_topic.items(), key=lambda x: (-x[1], x[0]))
    matched_topic_ids = [topic_id for topic_id, _ in ordered]
    similarity_scores = dict(ordered)
    return matched_topic_ids, similarity_scores