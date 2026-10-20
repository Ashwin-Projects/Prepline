"""
Taxonomy hierarchy helpers for coverage inheritance (item 2).

A granular_skill's syllabus coverage is inherited from its nearest
high_level_concept ancestor, found by walking parent_id.
"""
from typing import Dict, List, Optional

HIGH_LEVEL = "high_level_concept"
GRANULAR = "granular_skill"


def nearest_high_level_ancestor(topic_id: str, nodes_by_id: Dict[str, dict]) -> Optional[str]:
    """Walks parent_id from topic_id; returns the first high_level_concept ancestor, or None (cycle-safe)."""
    seen = {topic_id}
    parent_id = (nodes_by_id.get(topic_id) or {}).get("parent_id")
    while parent_id and parent_id not in seen:
        seen.add(parent_id)
        parent = nodes_by_id.get(parent_id)
        if parent is None:
            return None
        if parent.get("type") == HIGH_LEVEL:
            return parent_id
        parent_id = parent.get("parent_id")
    return None


def find_granular_without_high_level_ancestor(nodes: List[dict]) -> List[str]:
    """Sorted ids of granular_skill nodes that have no high_level_concept ancestor."""
    by_id = {n["topic_id"]: n for n in nodes}
    return sorted(
        n["topic_id"]
        for n in nodes
        if n.get("type") == GRANULAR and nearest_high_level_ancestor(n["topic_id"], by_id) is None
    )
