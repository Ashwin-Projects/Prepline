"""
Unit Test Suite for Phase 8 Presence & Depth Modeling (pipeline/scoring.py)

Tests:
1. Topic presence vs absence (syllabus-wide bit C(t))
2. Single and multiple depth signal normalizations
3. Missing depth signals exclusion (not treated as 0)
4. Reference depth values reaching max depth D=5 and coverage=1.0
5. Fallback depth (D=1.0, depth_status='fallback', count=0) vs Measured depth
6. Bounded depth D(t) in [1.0, 5.0] and coverage in [0.0, 1.0]
7. Zero coverage when topic is absent C(t)=0
8. Deterministic repeated execution
9. Taxonomy version preservation
"""

import unittest
import math
from pipeline.scoring import calculate_syllabus_coverage, normalize_signal, MVP_REFERENCE_VALUES


class TestPhase8Scoring(unittest.TestCase):

    def setUp(self):
        self.mock_taxonomy_nodes = [
            {
                "topic_id": "dsa.trees.bst",
                "name": "Binary Search Trees",
                "type": "granular_skill",
                "domain": "dsa",
                "description": "Binary search tree node operations"
            },
            {
                "topic_id": "dsa.dp.knapsack",
                "name": "0/1 Knapsack Problem",
                "type": "granular_skill",
                "domain": "dsa",
                "description": "Dynamic programming knapsack variations"
            },
            {
                "topic_id": "os.concurrency.deadlock",
                "name": "Deadlock Detection and Prevention",
                "type": "high_level_concept",
                "domain": "os",
                "description": "Operating system process deadlock conditions"
            }
        ]

    def test_normalize_signal(self):
        # unit_hours reference is 10
        self.assertEqual(normalize_signal("unit_hours", 5), 0.5)
        self.assertEqual(normalize_signal("unit_hours", 10), 1.0)
        self.assertEqual(normalize_signal("unit_hours", 15), 1.0)  # capped at 1.0
        self.assertIsNone(normalize_signal("unit_hours", None))

        # slide_count reference is 20
        self.assertEqual(normalize_signal("slide_count", 10), 0.5)

        # lab_count reference is 5
        self.assertEqual(normalize_signal("lab_count", 5), 1.0)

    def test_topic_presence_and_absence(self):
        mock_syllabus = {
            "syllabus_id": "test_syl_001.pdf",
            "taxonomy_version": "v1.0",
            "two_pass_mappings": [
                {
                    "source_id": "mod_1",
                    "matched_topic_ids": ["dsa.trees.bst"],
                    "depth_signals": {"unit_hours": 6, "lab_count": None}
                }
            ]
        }

        res = calculate_syllabus_coverage(mock_syllabus, taxonomy_nodes=self.mock_taxonomy_nodes)
        cov_map = {item["topic_id"]: item for item in res["topic_coverage"]}

        # Present topic
        self.assertEqual(cov_map["dsa.trees.bst"]["presence"], 1)
        self.assertGreater(cov_map["dsa.trees.bst"]["coverage"], 0.0)

        # Absent topics
        self.assertEqual(cov_map["dsa.dp.knapsack"]["presence"], 0)
        self.assertEqual(cov_map["dsa.dp.knapsack"]["coverage"], 0.0)
        self.assertEqual(cov_map["os.concurrency.deadlock"]["presence"], 0)
        self.assertEqual(cov_map["os.concurrency.deadlock"]["coverage"], 0.0)

    def test_missing_signals_excluded_not_treated_as_zero(self):
        # If only unit_hours = 10 is present, N(x) = 1.0, available count = 1.
        # D_norm = 1.0 / 1 = 1.0 -> D(t) = 1 + 4(1.0) = 5.0.
        # If missing signals were treated as 0 (e.g. 5 signals total), D_norm would be 1.0/5 = 0.2 -> D(t) = 1.8.
        # Excluded signals must yield D(t) = 5.0!
        mock_syllabus = {
            "syllabus_id": "test_syl_002.pdf",
            "taxonomy_version": "v1.0",
            "two_pass_mappings": [
                {
                    "source_id": "mod_1",
                    "matched_topic_ids": ["dsa.trees.bst"],
                    "depth_signals": {
                        "unit_hours": 10,
                        "slide_count": None,
                        "lab_hours": None,
                        "lab_count": None,
                        "assignment_count": None
                    }
                }
            ]
        }

        res = calculate_syllabus_coverage(mock_syllabus, taxonomy_nodes=self.mock_taxonomy_nodes)
        item = res["topic_coverage"][0]

        self.assertEqual(item["depth_signal_count"], 1)
        self.assertEqual(item["depth_status"], "measured")
        self.assertEqual(item["depth"], 5.0)
        self.assertEqual(item["coverage"], 1.0)

    def test_reference_values_reach_max_depth_and_coverage(self):
        # All signals at or above reference values: N(x) = 1.0 for each
        mock_syllabus = {
            "syllabus_id": "test_syl_max.pdf",
            "taxonomy_version": "v1.0",
            "two_pass_mappings": [
                {
                    "source_id": "mod_1",
                    "matched_topic_ids": ["dsa.trees.bst"],
                    "depth_signals": {
                        "unit_hours": 10,
                        "slide_count": 20,
                        "lab_hours": 10,
                        "lab_count": 5,
                        "assignment_count": 5
                    }
                }
            ]
        }

        res = calculate_syllabus_coverage(mock_syllabus, taxonomy_nodes=self.mock_taxonomy_nodes)
        item = res["topic_coverage"][0]

        self.assertEqual(item["presence"], 1)
        self.assertEqual(item["depth_signal_count"], 5)
        self.assertEqual(item["depth_status"], "measured")
        self.assertEqual(item["depth"], 5.0)
        self.assertEqual(item["coverage"], 1.0)

    def test_fallback_depth_vs_measured_depth(self):
        # Case A: Topic present, but all depth signals are None -> Fallback D=1.0
        # Case B: Topic present, depth signal gives N(x)=0.0 (e.g. 0 hours) -> Measured D=1.0
        mock_syllabus = {
            "syllabus_id": "test_fallback.pdf",
            "taxonomy_version": "v1.0",
            "two_pass_mappings": [
                {
                    "source_id": "mod_1",
                    "matched_topic_ids": ["dsa.trees.bst"],
                    "depth_signals": {
                        "unit_hours": None,
                        "slide_count": None
                    }
                },
                {
                    "source_id": "mod_2",
                    "matched_topic_ids": ["dsa.dp.knapsack"],
                    "depth_signals": {
                        "unit_hours": 0
                    }
                }
            ]
        }

        res = calculate_syllabus_coverage(mock_syllabus, taxonomy_nodes=self.mock_taxonomy_nodes)
        cov_map = {item["topic_id"]: item for item in res["topic_coverage"]}

        # Fallback D=1.0
        bst = cov_map["dsa.trees.bst"]
        self.assertEqual(bst["presence"], 1)
        self.assertEqual(bst["depth"], 1.0)
        self.assertEqual(bst["depth_status"], "fallback")
        self.assertEqual(bst["depth_signal_count"], 0)

        # Measured D=1.0
        knapsack = cov_map["dsa.dp.knapsack"]
        self.assertEqual(knapsack["presence"], 1)
        self.assertEqual(knapsack["depth"], 1.0)
        self.assertEqual(knapsack["depth_status"], "measured")
        self.assertEqual(knapsack["depth_signal_count"], 1)

    def test_depth_range_and_coverage_bounds(self):
        mock_syllabus = {
            "syllabus_id": "test_bounds.pdf",
            "taxonomy_version": "v1.0",
            "two_pass_mappings": [
                {
                    "source_id": "mod_1",
                    "matched_topic_ids": ["dsa.trees.bst"],
                    "depth_signals": {"unit_hours": 3, "lab_count": 2}
                }
            ]
        }

        res = calculate_syllabus_coverage(mock_syllabus, taxonomy_nodes=self.mock_taxonomy_nodes)

        for item in res["topic_coverage"]:
            self.assertTrue(1.0 <= item["depth"] <= 5.0, f"Depth {item['depth']} out of bounds")
            self.assertTrue(0.0 <= item["coverage"] <= 1.0, f"Coverage {item['coverage']} out of bounds")

    def test_deterministic_execution_and_taxonomy_version(self):
        mock_syllabus = {
            "syllabus_id": "test_det.pdf",
            "taxonomy_version": "v1.0",
            "two_pass_mappings": [
                {
                    "source_id": "mod_1",
                    "matched_topic_ids": ["dsa.trees.bst"],
                    "depth_signals": {"unit_hours": 6}
                }
            ]
        }

        run1 = calculate_syllabus_coverage(mock_syllabus, taxonomy_nodes=self.mock_taxonomy_nodes)
        run2 = calculate_syllabus_coverage(mock_syllabus, taxonomy_nodes=self.mock_taxonomy_nodes)

        self.assertEqual(run1, run2)
        self.assertEqual(run1["taxonomy_version"], "v1.0")
        for item in run1["topic_coverage"]:
            self.assertEqual(item["taxonomy_version"], "v1.0")


class TestPhase9Scoring(unittest.TestCase):

    def setUp(self):
        from pipeline.embeddings import load_taxonomy
        import os
        self.taxonomy_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "data",
            "taxonomy",
            "taxonomy_v1.0.json"
        )
        load_taxonomy(self.taxonomy_path)

        self.mock_taxonomy_nodes = [
            {
                "topic_id": "os.deadlocks",
                "name": "Deadlocks",
                "type": "high_level_concept",
                "domain": "os",
                "description": "Necessary conditions for deadlock, resource allocation graphs, and handling strategies."
            },
            {
                "topic_id": "os.deadlocks.prevention_avoidance",
                "name": "Deadlock Prevention and Banker's Algorithm",
                "type": "granular_skill",
                "domain": "os",
                "description": "Breaking Coffman conditions, Banker's safety algorithm, deadlock detection, and recovery mechanisms."
            },
            {
                "topic_id": "dbms.normalization.normal_forms",
                "name": "Normal Forms (1NF, 2NF, 3NF, BCNF)",
                "type": "granular_skill",
                "domain": "dbms",
                "description": "Decomposing tables to satisfy First, Second, Third, and Boyce-Codd Normal Forms."
            }
        ]

    def test_one_question_one_report(self):
        from pipeline.scoring import calculate_topic_importance

        questions = [
            {
                "report_id": "AMZ001",
                "round": "Round 1",
                "round_type": "technical",
                "question_text": "Deadlock Detection and Prevention",
                "topic": ""
            }
        ]

        res = calculate_topic_importance(questions, total_reports_count=21, taxonomy_nodes=self.mock_taxonomy_nodes)
        imp_map = {item["topic_id"]: item for item in res["interview_importance"]}

        d_main = imp_map["os.deadlocks"]
        self.assertEqual(d_main["matched_report_count"], 1)
        self.assertAlmostEqual(d_main["importance"], 0.6 / 21.0, places=4)

    def test_multiple_questions_same_topic_in_one_report_takes_max_not_sum(self):
        from pipeline.scoring import calculate_topic_importance

        # Three questions in AMZ001 all matching Deadlocks
        questions = [
            {"report_id": "AMZ001", "question_text": "Deadlock Detection and Prevention", "topic": ""},
            {"report_id": "AMZ001", "question_text": "Deadlocks and resource allocation graph", "topic": ""},
            {"report_id": "AMZ001", "question_text": "Banker's algorithm for deadlock prevention", "topic": ""}
        ]

        res = calculate_topic_importance(questions, total_reports_count=21, taxonomy_nodes=self.mock_taxonomy_nodes)
        imp_map = {item["topic_id"]: item for item in res["interview_importance"]}

        d_main = imp_map["os.deadlocks"]
        # Must take MAX credit within report (0.6), NOT sum (1.8)!
        self.assertEqual(d_main["matched_report_count"], 1)
        self.assertAlmostEqual(d_main["importance"], 0.6 / 21.0, places=4)

    def test_multiple_topics_in_one_report(self):
        from pipeline.scoring import calculate_topic_importance

        questions = [
            {"report_id": "AMZ001", "question_text": "Deadlock Detection and Prevention", "topic": ""}
        ]

        res = calculate_topic_importance(questions, total_reports_count=21, taxonomy_nodes=self.mock_taxonomy_nodes)
        imp_map = {item["topic_id"]: item for item in res["interview_importance"]}

        self.assertEqual(imp_map["os.deadlocks"]["matched_report_count"], 1)
        self.assertEqual(imp_map["os.deadlocks.prevention_avoidance"]["matched_report_count"], 1)

    def test_60_40_credit_split_preservation(self):
        from pipeline.scoring import calculate_topic_importance

        # Deadlock Detection and Prevention triggers 60/40 split between os.deadlocks (0.6) and os.deadlocks.prevention_avoidance (0.4)
        questions = [
            {"report_id": "AMZ001", "question_text": "Deadlock Detection and Prevention", "topic": ""}
        ]

        res = calculate_topic_importance(questions, total_reports_count=21, taxonomy_nodes=self.mock_taxonomy_nodes)
        imp_map = {item["topic_id"]: item for item in res["interview_importance"]}

        d_main = imp_map["os.deadlocks"]
        d_sub = imp_map["os.deadlocks.prevention_avoidance"]

        self.assertAlmostEqual(d_main["importance"], 0.6 / 21.0, places=4)
        self.assertAlmostEqual(d_sub["importance"], 0.4 / 21.0, places=4)

    def test_topic_importance_denominator_uses_total_independent_reports(self):
        from pipeline.scoring import calculate_topic_importance

        # 2 independent reports (AMZ001, AMZ002) matching Deadlocks
        questions = [
            {"report_id": "AMZ001", "question_text": "Deadlock Detection and Prevention", "topic": ""},
            {"report_id": "AMZ002", "question_text": "Deadlock Detection and Prevention", "topic": ""}
        ]

        res = calculate_topic_importance(questions, total_reports_count=21, taxonomy_nodes=self.mock_taxonomy_nodes)
        imp_map = {item["topic_id"]: item for item in res["interview_importance"]}

        d_main = imp_map["os.deadlocks"]
        self.assertEqual(d_main["matched_report_count"], 2)
        self.assertAlmostEqual(d_main["importance"], 1.2 / 21.0, places=4)

    def test_absent_topics_receive_zero_importance(self):
        from pipeline.scoring import calculate_topic_importance

        questions = [
            {"report_id": "AMZ001", "question_text": "Deadlock Detection and Prevention", "topic": ""}
        ]

        res = calculate_topic_importance(questions, total_reports_count=21, taxonomy_nodes=self.mock_taxonomy_nodes)
        imp_map = {item["topic_id"]: item for item in res["interview_importance"]}

        nf = imp_map["dbms.normalization.normal_forms"]
        self.assertEqual(nf["matched_report_count"], 0)
        self.assertEqual(nf["importance"], 0.0)

    def test_deterministic_execution_and_bounds(self):
        from pipeline.scoring import calculate_topic_importance

        questions = [
            {"report_id": "AMZ001", "question_text": "Deadlock Detection and Prevention", "topic": ""},
            {"report_id": "AMZ002", "question_text": "Deadlock Detection and Prevention", "topic": ""}
        ]

        run1 = calculate_topic_importance(questions, total_reports_count=21, taxonomy_nodes=self.mock_taxonomy_nodes)
        run2 = calculate_topic_importance(questions, total_reports_count=21, taxonomy_nodes=self.mock_taxonomy_nodes)

        self.assertEqual(run1, run2)
        for item in run1["interview_importance"]:
            self.assertTrue(0.0 <= item["importance"] <= 1.0)

    def test_real_21_report_dataset_integration(self):
        from pipeline.scoring import calculate_topic_importance
        import os

        questions_csv = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "data",
            "processed",
            "questions.csv"
        )
        self.assertTrue(os.path.exists(questions_csv))

        res = calculate_topic_importance(questions_csv, total_reports_count=21)

        self.assertEqual(res["total_reports_count"], 21)
        self.assertEqual(res["taxonomy_version"], "v1.0")
        self.assertGreater(len(res["interview_importance"]), 0)

        for item in res["interview_importance"]:
            self.assertTrue(0.0 <= item["importance"] <= 1.0)
            self.assertTrue(0 <= item["matched_report_count"] <= 21)


class TestPhase10Scoring(unittest.TestCase):

    def test_simple_known_score(self):
        from pipeline.scoring import calculate_composite_score
        importance = {"interview_importance": [{"topic_id": "t1", "importance": 0.5}, {"topic_id": "t2", "importance": 0.5}]}
        coverage = {"topic_coverage": [{"topic_id": "t1", "coverage": 1.0}, {"topic_id": "t2", "coverage": 0.0}]}
        res = calculate_composite_score(importance, coverage)
        self.assertEqual(res["composite_score"], 50.0)
        self.assertEqual(res["S_comp"], 50.0)
        self.assertEqual(res["scoring_universe_size"], 2)

    def test_multiple_topics(self):
        from pipeline.scoring import calculate_composite_score
        importance = {
            "interview_importance": [
                {"topic_id": "t1", "importance": 0.6},
                {"topic_id": "t2", "importance": 0.4},
                {"topic_id": "t3", "importance": 0.2}
            ]
        }
        coverage = {
            "topic_coverage": [
                {"topic_id": "t1", "coverage": 0.8},
                {"topic_id": "t2", "coverage": 0.5},
                {"topic_id": "t3", "coverage": 1.0}
            ]
        }
        res = calculate_composite_score(importance, coverage)
        self.assertAlmostEqual(res["composite_score"], 73.3333, places=3)
        self.assertEqual(res["scoring_universe_size"], 3)

    def test_zero_importance_topics_excluded(self):
        from pipeline.scoring import calculate_composite_score
        importance = {
            "interview_importance": [
                {"topic_id": "t1", "importance": 0.5},
                {"topic_id": "t2", "importance": 0.0}
            ]
        }
        coverage = {
            "topic_coverage": [
                {"topic_id": "t1", "coverage": 1.0},
                {"topic_id": "t2", "coverage": 0.2}
            ]
        }
        res = calculate_composite_score(importance, coverage)
        self.assertEqual(res["composite_score"], 100.0)
        self.assertEqual(res["scoring_universe_size"], 1)

    def test_score_bounded_correctly(self):
        from pipeline.scoring import calculate_composite_score
        max_res = calculate_composite_score(
            {"t1": 0.8, "t2": 0.4},
            {"t1": 1.0, "t2": 1.0}
        )
        self.assertEqual(max_res["composite_score"], 100.0)

        min_res = calculate_composite_score(
            {"t1": 0.8, "t2": 0.4},
            {"t1": 0.0, "t2": 0.0}
        )
        self.assertEqual(min_res["composite_score"], 0.0)

    def test_deterministic_repeated_execution(self):
        from pipeline.scoring import calculate_composite_score
        importance = {"t1": 0.6, "t2": 0.3}
        coverage = {"t1": 0.7, "t2": 0.4}

        run1 = calculate_composite_score(importance, coverage)
        run2 = calculate_composite_score(importance, coverage)

        self.assertEqual(run1, run2)

    def test_empty_input_handling(self):
        from pipeline.scoring import calculate_composite_score
        res1 = calculate_composite_score({}, {})
        self.assertEqual(res1["composite_score"], 0.0)
        self.assertEqual(res1["scoring_universe_size"], 0)

        res2 = calculate_composite_score([], [])
        self.assertEqual(res2["composite_score"], 0.0)


class TestPhase11Scoring(unittest.TestCase):

    def test_correct_gap_calculation(self):
        from pipeline.scoring import rank_priority_gaps
        importance = {"t1": 0.8, "t2": 0.5}
        coverage = {"t1": 0.5, "t2": 0.2}

        res = rank_priority_gaps(importance, coverage)
        self.assertEqual(len(res), 2)
        gap_map = {item["topic_id"]: item for item in res}
        self.assertAlmostEqual(gap_map["t1"]["priority_gap"], 0.4)
        self.assertAlmostEqual(gap_map["t2"]["priority_gap"], 0.4)

    def test_descending_ranking(self):
        from pipeline.scoring import rank_priority_gaps
        importance = {"t1": 0.8, "t2": 0.9, "t3": 0.4}
        coverage = {"t1": 0.5, "t2": 0.1, "t3": 0.0}

        res = rank_priority_gaps(importance, coverage)
        self.assertEqual(res[0]["topic_id"], "t2")
        self.assertEqual(res[0]["rank"], 1)
        self.assertAlmostEqual(res[0]["priority_gap"], 0.81)

    def test_zero_importance_topics_excluded(self):
        from pipeline.scoring import rank_priority_gaps
        importance = {"t1": 0.8, "t2": 0.0}
        coverage = {"t1": 0.5, "t2": 0.0}

        res = rank_priority_gaps(importance, coverage)
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]["topic_id"], "t1")

    def test_correct_rank_numbering(self):
        from pipeline.scoring import rank_priority_gaps
        importance = {"t1": 0.6, "t2": 0.8, "t3": 0.4}
        coverage = {"t1": 0.0, "t2": 0.0, "t3": 0.0}

        res = rank_priority_gaps(importance, coverage)
        ranks = [item["rank"] for item in res]
        self.assertEqual(ranks, [1, 2, 3])

    def test_deterministic_tie_handling(self):
        from pipeline.scoring import rank_priority_gaps
        importance = {"t_beta": 0.5, "t_alpha": 0.5}
        coverage = {"t_beta": 0.2, "t_alpha": 0.2}

        res = rank_priority_gaps(importance, coverage)
        self.assertEqual(res[0]["topic_id"], "t_alpha")
        self.assertEqual(res[1]["topic_id"], "t_beta")


if __name__ == "__main__":
    unittest.main()




