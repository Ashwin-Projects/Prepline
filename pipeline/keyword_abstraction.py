"""
Keyword Abstraction Module (Phase 4)

Handles Two-Pass Abstraction:
- Pass 1: Raw text (syllabus unit or interview question) -> intermediate keywords/concepts.
- Pass 2: Intermediate concept vector -> canonical taxonomy node mapping placeholder.

Every mapping preserves taxonomy_version.
"""

from typing import List, Dict, Any, Optional
from rake_nltk import Rake

DEFAULT_TAXONOMY_VERSION = "v1.0"

_rake = None


def _get_rake():
    global _rake
    if _rake is None:
        import nltk
        for resource in ["corpora/stopwords", "tokenizers/punkt", "tokenizers/punkt_tab"]:
            try:
                nltk.data.find(resource)
            except LookupError:
                target = resource.split("/")[-1]
                nltk.download(target, quiet=True)
        try:
            nltk.data.find("tokenizers/punkt_tab/english/")
        except LookupError:
            nltk.download("punkt_tab", quiet=True)
        _rake = Rake(min_length=1, max_length=4)
    return _rake


def extract_intermediate_concepts(text: str) -> List[str]:
    """
    Pass 1 Abstraction: Extracts normalized intermediate concept keywords
    from raw text. Uses RAKE for phrase-level extraction (e.g. "overlapping
    intervals" stays one concept, "parking lot design" stays one concept)
    instead of splitting into single words, which matches much better
    against taxonomy node descriptions in Phase 5's embedding similarity.
    """
    if not text or not text.strip():
        return []

    rake = _get_rake()
    rake.extract_keywords_from_text(text)
    ranked = rake.get_ranked_phrases()

    concepts = []
    seen = set()
    for phrase in ranked:
        phrase = phrase.strip().lower()
        if phrase and phrase not in seen and len(phrase) > 2:
            seen.add(phrase)
            concepts.append(phrase)
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