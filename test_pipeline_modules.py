import unittest

from pipeline.interview_parser import load_interview_index
from pipeline.keyword_abstraction import find_topic_mentions, normalize_text
from pipeline.scoring import topic_coverage, weighted_coverage
from pipeline.syllabus_parser import load_course_catalog, search_course_catalog
from pipeline.taxonomy_mapper import load_taxonomy, map_keywords, map_tfidf


class PipelineModuleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.taxonomy = load_taxonomy()

    def test_taxonomy_keyword_mapping(self):
        result = map_keywords("Use dynamic programming to solve the problem.", self.taxonomy)
        self.assertIn("dsa.dynamic_programming", {row["topic_id"] for row in result})

    def test_tfidf_mapping_returns_ranked_scores(self):
        result = map_tfidf("SQL joins and relational database normalization", self.taxonomy, top_k=4)
        self.assertTrue(result)
        self.assertLessEqual(len(result), 4)
        self.assertEqual(result[0]["method"], "tfidf")
        self.assertGreaterEqual(result[0]["score"], result[-1]["score"])

    def test_normalization(self):
        self.assertEqual(normalize_text("SQL Joins!!"), "sql joins")

    def test_catalog_load_and_search(self):
        rows = load_course_catalog()
        self.assertGreaterEqual(len(rows), 20)
        matches = search_course_catalog("Operating Systems", rows)
        self.assertTrue(any(row["course_code"] == "BCSE303L" for row in matches))

    def test_interview_index_preserves_pending_status(self):
        rows = load_interview_index()
        self.assertEqual(len(rows), 19)
        self.assertEqual(load_interview_index(eligible_only=True), [])

    def test_unweighted_coverage_and_gaps(self):
        result = topic_coverage(
            ["dsa.arrays", "dsa.graphs"],
            ["dsa.arrays", "dsa.graphs", "dbms.normalization", "dbms.normalization"],
        )
        self.assertEqual(result["coverage_percent"], 66.67)
        self.assertEqual(result["gap_topics"], ["dbms.normalization"])
        self.assertEqual(result["interview_frequency"]["dbms.normalization"], 2)

    def test_weighted_coverage_uses_all_interview_weights(self):
        result = weighted_coverage(
            ["dsa.arrays"],
            {"dsa.arrays": 3, "dbms.normalization": 1},
        )
        self.assertEqual(result["coverage_percent"], 75.0)
        self.assertEqual(result["gap_topics"], ["dbms.normalization"])

    def test_negative_weight_rejected(self):
        with self.assertRaises(ValueError):
            weighted_coverage([], {"dsa.arrays": -1})


if __name__ == "__main__":
    unittest.main()
