"""
Item 2: node-type matching and coverage inheritance.

Syllabus units match only high_level_concept nodes; interview questions match only
granular_skill nodes. A granular skill's coverage is inherited from its nearest
high_level_concept ancestor (coverage_source == "inherited").
"""
import logging

from backend.schemas import TopicCoverageItem
from pipeline import embeddings, scoring, taxonomy_mapper
from pipeline.taxonomy_tree import find_granular_without_high_level_ancestor, nearest_high_level_ancestor

REAL_NODES = scoring.load_taxonomy_nodes(scoring.DEFAULT_TAXONOMY_PATH)
NODE_TYPES = {n["topic_id"]: n["type"] for n in REAL_NODES}
BST_TEXT = "Binary search trees: insertion, deletion and search in a BST."


def _by_id(nodes):
    return {n["topic_id"]: n for n in nodes}


def test_real_taxonomy_has_no_orphans():
    assert find_granular_without_high_level_ancestor(REAL_NODES) == []


def test_orphan_detected():
    nodes = [
        {"topic_id": "a", "type": "high_level_concept", "parent_id": None},
        {"topic_id": "a.ok", "type": "granular_skill", "parent_id": "a"},
        {"topic_id": "x.root", "type": "granular_skill", "parent_id": None},
        {"topic_id": "y.dangling", "type": "granular_skill", "parent_id": "missing"},
    ]
    assert find_granular_without_high_level_ancestor(nodes) == ["x.root", "y.dangling"]


def test_nearest_ancestor_skips_granular_parent():
    nodes = [
        {"topic_id": "a", "type": "high_level_concept", "parent_id": None},
        {"topic_id": "a.b", "type": "granular_skill", "parent_id": "a"},
        {"topic_id": "a.b.c", "type": "granular_skill", "parent_id": "a.b"},
    ]
    assert nearest_high_level_ancestor("a.b.c", _by_id(nodes)) == "a"


def test_nearest_ancestor_cycle_safe():
    nodes = [
        {"topic_id": "g1", "type": "granular_skill", "parent_id": "g2"},
        {"topic_id": "g2", "type": "granular_skill", "parent_id": "g1"},
    ]
    assert nearest_high_level_ancestor("g1", _by_id(nodes)) is None


def test_match_filters_high_level():
    ids, _, _ = embeddings.match_concepts_to_taxonomy(["binary search tree insertion"], node_type="high_level_concept")
    assert ids
    assert {NODE_TYPES[t] for t in ids} == {"high_level_concept"}


def test_match_filters_granular():
    ids, _, _ = embeddings.match_concepts_to_taxonomy(["binary search tree insertion"], node_type="granular_skill")
    assert ids
    assert {NODE_TYPES[t] for t in ids} == {"granular_skill"}


def test_node_type_none_unchanged():
    concepts = ["binary search tree insertion", "deadlock"]
    all_ids, all_scores, _ = embeddings.match_concepts_to_taxonomy(concepts)
    high, _, _ = embeddings.match_concepts_to_taxonomy(concepts, node_type="high_level_concept")
    gran, _, _ = embeddings.match_concepts_to_taxonomy(concepts, node_type="granular_skill")
    assert set(all_ids) == set(high) | set(gran)


def test_concept_matching_only_other_type_is_unmapped():
    # "deadlock" clears tau only against OS nodes; restricting to a type that has no such
    # match must report it as unmapped rather than silently dropping it.
    _, _, unmapped = embeddings.match_concepts_to_taxonomy(["deadlock"], node_type="granular_skill", threshold=0.99)
    assert unmapped == ["deadlock"]


def test_syllabus_source_matches_only_high_level():
    record = taxonomy_mapper.map_source_to_taxonomy("syl_1", BST_TEXT, source_type="syllabus")
    assert record["matched_topic_ids"]
    assert {NODE_TYPES[t] for t in record["matched_topic_ids"]} == {"high_level_concept"}


def test_interview_source_matches_only_granular():
    record = taxonomy_mapper.map_source_to_taxonomy("q_1", BST_TEXT, source_type="interview")
    assert record["matched_topic_ids"]
    assert {NODE_TYPES[t] for t in record["matched_topic_ids"]} == {"granular_skill"}


def _coverage_map(mappings, nodes=REAL_NODES):
    res = scoring.calculate_syllabus_coverage(
        {"syllabus_id": "s", "taxonomy_version": "v1.0", "two_pass_mappings": mappings}, taxonomy_nodes=nodes
    )
    return {item["topic_id"]: item for item in res["topic_coverage"]}


def test_granular_inherits_parent_coverage():
    cov = _coverage_map([{"matched_topic_ids": ["dsa.trees"], "depth_signals": {"unit_hours": 8}}])
    parent, child = cov["dsa.trees"], cov["dsa.trees.bst"]
    assert parent["coverage_source"] == "direct"
    assert child["coverage_source"] == "inherited"
    assert child["inherited_from"] == "dsa.trees"
    for key in ("presence", "depth", "coverage", "depth_status", "depth_signal_count"):
        assert child[key] == parent[key], key
    assert child["coverage"] > 0


def test_granular_of_absent_parent_inherits_zero():
    cov = _coverage_map([{"matched_topic_ids": ["dsa.trees"], "depth_signals": {"unit_hours": 8}}])
    assert cov["dsa.heaps.top_k"]["coverage"] == 0.0
    assert cov["dsa.heaps.top_k"]["coverage_source"] == "inherited"


def test_orphan_falls_back_with_warning(caplog):
    nodes = [{"topic_id": "x.orphan", "name": "Orphan", "type": "granular_skill", "parent_id": None}]
    with caplog.at_level(logging.WARNING):
        cov = _coverage_map([{"matched_topic_ids": ["x.orphan"], "depth_signals": {"unit_hours": 8}}], nodes)
    assert cov["x.orphan"]["coverage_source"] == "direct"
    assert cov["x.orphan"]["coverage"] > 0
    assert any("x.orphan" in r.getMessage() for r in caplog.records if r.levelno == logging.WARNING)


def test_coverage_item_schema_accepts_inheritance_fields():
    cov = _coverage_map([{"matched_topic_ids": ["dsa.trees"], "depth_signals": {"unit_hours": 8}}])
    item = TopicCoverageItem(**cov["dsa.trees.bst"])
    assert item.coverage_source == "inherited"
    assert item.inherited_from == "dsa.trees"
