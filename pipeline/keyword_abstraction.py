"""
Keyword Abstraction Module (Phase 4)

Handles Two-Pass Abstraction:
- Pass 1: Raw text (syllabus unit or interview question) -> intermediate keywords/concepts.
- Pass 2: Intermediate concept vector -> canonical taxonomy node mapping placeholder.

Every mapping preserves taxonomy_version.
"""

import re
from typing import List, Dict, Any, Optional

DEFAULT_TAXONOMY_VERSION = "v1.0"

# Stopwords list for concept extraction in Pass 1
COMMON_STOPWORDS = {
    "a", "an", "the", "and", "or", "in", "of", "to", "for", "with", "on", "at", "by",
    "from", "up", "about", "into", "over", "after", "is", "are", "was", "were", "be",
    "been", "being", "have", "has", "had", "do", "does", "did", "but", "if", "or",
    "because", "as", "until", "while", "this", "that", "these", "those", "it", "its",
    "introduction", "overview", "basics", "fundamentals", "advanced", "concepts",
    "module", "unit", "chapter", "lecture", "hours", "hour"
}


def extract_intermediate_concepts(text: str) -> List[str]:
    """
    Pass 1 Abstraction: Extracts normalized intermediate concept keywords from raw text.
    """
    if not text:
        return []
    
    # Tokenize words, convert to lowercase
    tokens = re.findall(r'\b[a-zA-Z]{2,}\b', text.lower())
    
    # Filter stopwords and deduplicate preserving order
    concepts = []
    seen = set()
    for token in tokens:
        if token not in COMMON_STOPWORDS and token not in seen:
            seen.add(token)
            concepts.append(token)
            
    return concepts


def two_pass_abstract(
    source_id: str,
    raw_text: str,
    source_type: str = "syllabus",
    taxonomy_version: str = DEFAULT_TAXONOMY_VERSION,
    matched_topic_ids: Optional[List[str]] = None,
    similarity_scores: Optional[Dict[str, float]] = None
) -> Dict[str, Any]:
    """
    Executes two-pass abstraction for a raw text input and returns the structured mapping.
    
    Schema:
    - source_id: unique identifier of raw text source (e.g. syllabus unit ID or report question ID)
    - source_type: 'syllabus' or 'interview'
    - intermediate_concepts: list of extracted keyword/concept strings (Pass 1)
    - matched_topic_ids: list of matched taxonomy node IDs (Pass 2, filled in Phase 5/6)
    - similarity_scores: dict mapping topic_id -> score (Pass 2, filled in Phase 5/6)
    - taxonomy_version: version string (e.g., 'v1.0')
    """
    intermediate_concepts = extract_intermediate_concepts(raw_text)
    
    return {
        "source_id": source_id,
        "source_type": source_type,
        "raw_text": raw_text,
        "intermediate_concepts": intermediate_concepts,
        "matched_topic_ids": matched_topic_ids or [],
        "similarity_scores": similarity_scores or {},
        "taxonomy_version": taxonomy_version
    }
