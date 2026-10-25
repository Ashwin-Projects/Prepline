"""Keyword normalization and taxonomy-aware phrase extraction."""
from __future__ import annotations

import re
from collections import defaultdict
from typing import Iterable

STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "how",
    "in", "into", "is", "it", "of", "on", "or", "the", "to", "what", "when",
    "where", "which", "why", "with", "would", "you", "your",
}


def normalize_text(value: str) -> str:
    """Lowercase text and normalize punctuation/whitespace for matching."""
    return re.sub(r"[^a-z0-9+#.]+", " ", str(value).lower()).strip()


def tokens(value: str) -> list[str]:
    return [token for token in normalize_text(value).split() if token not in STOP_WORDS]


def build_alias_index(topics: Iterable[dict]) -> dict[str, set[str]]:
    """Map normalized topic names and IDs to the topic IDs that own them."""
    index: dict[str, set[str]] = defaultdict(set)
    for topic in topics:
        topic_id = str(topic["topic_id"])
        candidates = {topic_id, topic_id.replace(".", " ").replace("_", " "),
                      str(topic.get("name", ""))}
        candidates.update(topic.get("aliases", []) or [])
        for candidate in candidates:
            phrase = normalize_text(candidate)
            if phrase:
                index[phrase].add(topic_id)
    return dict(index)


def find_topic_mentions(text: str, topics: Iterable[dict]) -> list[dict]:
    """Return exact phrase matches, longest phrase first; this is a baseline, not semantic truth."""
    normalized = f" {normalize_text(text)} "
    index = build_alias_index(topics)
    found = []
    for phrase, topic_ids in index.items():
        if len(phrase) < 3:
            continue
        if f" {phrase} " in normalized:
            for topic_id in sorted(topic_ids):
                found.append({"topic_id": topic_id, "matched_phrase": phrase})
    found.sort(key=lambda row: (-len(row["matched_phrase"]), row["topic_id"]))
    return found
