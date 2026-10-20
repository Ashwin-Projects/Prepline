"""
Phase 6 - Deterministic 60/40 Multi-Topic Mapping
(+ Phase 12.1 unmapped-term logging wired in)

Orchestrates Phase 4 (keyword_abstraction.two_pass_abstract) + Phase 5 (embeddings.match_concepts_to_taxonomy) into the final stored mapping
record, and applies the deterministic primary/secondary credit split.

This is the module Sprint 4/5 (syllabus depth modeling, scoring.py) should import from.
"""
from typing import Dict
from pipeline.keyword_abstraction import two_pass_abstract, DEFAULT_TAXONOMY_VERSION
from pipeline.embeddings import match_concepts_to_taxonomy, SIMILARITY_THRESHOLD
from pipeline.unmapped_terms_logger import log_unmapped_terms
from pipeline.config import load_scoring_config

# Syllabus units match only high_level_concept nodes; interview questions only granular_skill nodes.
_NODE_TYPE_RULE = load_scoring_config()["node_type_rule"]


def assign_credit(similarity_scores: Dict[str, float]) -> Dict[str, float]:
    """
    Phase 6, steps 2-4: deterministic 60/40 credit split, applied to the     similarity_scores dict produced by Phase 5 for one source.

    - 0 matches  -> {} (unmapped; caller should log to unmapped_terms.log)
    - 1 match    -> 100% credit
    - 2+ matches -> highest similarity = primary (60%), remaining 40% split equally among secondaries. Exact-score ties
                    are broken alphabetically by topic_id.
    """
    if not similarity_scores:
        return {}

    ordered = sorted(similarity_scores.items(), key=lambda x: (-x[1], x[0]))
    if len(ordered) == 1:
        return {ordered[0][0]: 1.0}
    primary_topic = ordered[0][0]
    secondary_topics = [topic_id for topic_id, _ in ordered[1:]]
    credit = {primary_topic: 0.60}
    share = 0.40 / len(secondary_topics)
    for topic_id in secondary_topics:
        credit[topic_id] = share
    return credit


def map_source_to_taxonomy(
    source_id: str,
    raw_text: str,
    source_type: str = "syllabus",
    taxonomy_version: str = DEFAULT_TAXONOMY_VERSION,
    threshold: float = SIMILARITY_THRESHOLD,
) -> dict:
    """
    Full Phase 4-6 pipeline for one source. IMPORTANT: `raw_text` should be ONE question (interview side) or ONE syllabus unit's text
    (syllabus side) - not a multi-question/multi-round blob. Per Phase 6.5, credits are stored per-question; Phase 9 aggregates across
    questions within a report afterward. If raw interview data isn't already split to one-question-per-row, that split belongs in
    interview_parser.py (Phase 2), upstream of this function.

    Returns the same schema as keyword_abstraction.two_pass_abstract(), with matched_topic_ids and similarity_scores now actually filled in
    (Phase 5), plus an added `credit` field (Phase 6) that Sprint 5's scoring.py consumes for W(r,t) and I(t).

    Every call that finds below-threshold concepts automatically logs them (Phase 12.1) - no separate step needed by callers.
    """
    record = two_pass_abstract(
        source_id=source_id,
        raw_text=raw_text,
        source_type=source_type,
        taxonomy_version=taxonomy_version,
    )

    matched_topic_ids, similarity_scores, unmapped_concepts = match_concepts_to_taxonomy(
        record["intermediate_concepts"],
        threshold=threshold,
        node_type=_NODE_TYPE_RULE.get(source_type),
    )
    record["matched_topic_ids"] = matched_topic_ids
    record["similarity_scores"] = similarity_scores
    record["credit"] = assign_credit(similarity_scores)

    log_unmapped_terms(
        unmapped_concepts,
        source_type=source_type,
        taxonomy_version=taxonomy_version,
        source_id=source_id,
    )

    return record
