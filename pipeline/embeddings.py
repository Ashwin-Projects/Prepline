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
import os
from typing import List, Dict, Optional, Tuple
from sentence_transformers import SentenceTransformer, util

from pipeline.config import load_scoring_config, resolve_path

_CONFIG = load_scoring_config()

SIMILARITY_THRESHOLD = _CONFIG["similarity_threshold"]  # MVP baseline (Phase 5.3) - frozen after benchmark

DEFAULT_TAXONOMY_PATH = resolve_path(_CONFIG["taxonomy_path"])

_model = None
_taxonomy_nodes = None
_taxonomy_embeddings = None


def load_model():
    global _model
    if _model is None:
        model_cfg = _CONFIG["embedding_model"]
        _model = SentenceTransformer(model_cfg["name"], revision=model_cfg["revision"])
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
    with open(taxonomy_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    nodes = data["nodes"] if isinstance(data, dict) and "nodes" in data else data
    _taxonomy_nodes = nodes
    descriptions = [n.get("description", n["topic_id"]) for n in nodes]
    _taxonomy_embeddings = model.encode(descriptions, convert_to_tensor=True)
    return len(nodes)


def _ensure_taxonomy_loaded() -> None:
    if _taxonomy_nodes is None or _taxonomy_embeddings is None:
        if os.path.exists(DEFAULT_TAXONOMY_PATH):
            load_taxonomy(DEFAULT_TAXONOMY_PATH)
        else:
            raise RuntimeError("Call load_taxonomy(path) before matching.")


def match_concepts_to_taxonomy(
    concepts: List[str], threshold: float = SIMILARITY_THRESHOLD, node_type: Optional[str] = None
) -> Tuple[List[str], Dict[str, float], List[str]]:
    """
    Phase 5, applied across an entire source's `intermediate_concepts` list (i.e. everything two_pass_abstract() extracted for one
    source_id). All concepts are encoded in one batch and scored against every taxonomy node, then results are merged by topic_id -
    keeping the best score seen for that topic across all concepts belonging to this source.

    Returns (matched_topic_ids, similarity_scores, unmapped_concepts). The first two are in exactly the shape two_pass_abstract()'s output
    dict expects; matched_topic_ids is sorted by similarity descending, exact-score ties broken alphabetically by topic_id (Phase 6.4).
    unmapped_concepts is every concept that scored below threshold against EVERY taxonomy node - this feeds Phase 12.1 logging.

    node_type (e.g. "high_level_concept" or "granular_skill") restricts matching to nodes of that type; a concept that clears
    the threshold only against other node types counts as unmapped.
    """
    best_by_topic: Dict[str, float] = {}
    unmapped_concepts: List[str] = []
    if concepts:
        _ensure_taxonomy_loaded()
        concept_embeddings = load_model().encode(list(concepts), convert_to_tensor=True)
        score_rows = util.cos_sim(concept_embeddings, _taxonomy_embeddings).tolist()
        candidates = [
            i for i, node in enumerate(_taxonomy_nodes)
            if node_type is None or node.get("type") == node_type
        ]
        for concept, scores in zip(concepts, score_rows):
            matched = False
            for i in candidates:
                score = scores[i]
                if score >= threshold:
                    matched = True
                    topic_id = _taxonomy_nodes[i]["topic_id"]
                    if topic_id not in best_by_topic or score > best_by_topic[topic_id]:
                        best_by_topic[topic_id] = score
            if not matched:
                unmapped_concepts.append(concept)
    ordered = sorted(best_by_topic.items(), key=lambda x: (-x[1], x[0]))
    matched_topic_ids = [topic_id for topic_id, _ in ordered]
    similarity_scores = dict(ordered)
    return matched_topic_ids, similarity_scores, unmapped_concepts
