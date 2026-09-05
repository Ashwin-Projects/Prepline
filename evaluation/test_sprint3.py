"""
run:
pip install sentence-transformers rake-nltk 
python3 -c "import nltk; nltk.download('stopwords'); nltk.download('punkt_tab')"
python3 evaluation/test_sprint3.py

"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pipeline.embeddings import load_taxonomy
from pipeline.taxonomy_mapper import map_source_to_taxonomy, assign_credit

TAXONOMY_PATH = "data/taxonomy/taxonomy_v1.0.json"


def test_single_match_gets_full_credit():
    assert assign_credit({"dsa.arrays.intervals": 0.83}) == {"dsa.arrays.intervals": 1.0}


def test_two_matches_split_60_40():
    result = assign_credit({"dsa.trees.bst": 0.71, "dsa.trees.traversal": 0.55})
    assert result["dsa.trees.bst"] == 0.6
    assert result["dsa.trees.traversal"] == 0.4


def test_zero_matches_returns_empty_credit():
    assert assign_credit({}) == {}


def test_tie_breaks_alphabetically():
    # both at exactly 0.60 -> "aaa" should win as primary
    result = assign_credit({"zzz.topic": 0.60, "aaa.topic": 0.60})
    assert result["aaa.topic"] == 0.6
    assert result["zzz.topic"] == 0.4


def test_end_to_end_on_real_taxonomy():
    load_taxonomy(TAXONOMY_PATH)
    record = map_source_to_taxonomy(
        "AMZ001_R1_Q1", "Burning Tree traversal problem", source_type="interview"
    )
    assert record["source_id"] == "AMZ001_R1_Q1"
    assert record["taxonomy_version"] == "v1.0"
    assert len(record["matched_topic_ids"]) == len(record["similarity_scores"])
    assert sum(record["credit"].values()) <= 1.0 + 1e-9
    print(record)  # eyeball the actual match quality against the real taxonomy


if __name__ == "__main__":
    test_single_match_gets_full_credit()
    test_two_matches_split_60_40()
    test_zero_matches_returns_empty_credit()
    test_tie_breaks_alphabetically()
    test_end_to_end_on_real_taxonomy()
    print("All Sprint 3 tests passed.")