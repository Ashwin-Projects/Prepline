"""
Unit Test Suite for Phase 12 - Unmapped Terms & Taxonomy Versioning

Tests:
1. Below-threshold concepts are returned as unmapped by Phase 5 matching
2. Logger writes one JSON line per term with source_id, source_type, taxonomy_version
3. Review frequency counts distinct sources, so pipeline reruns don't inflate it
4. Review filters by taxonomy_version and skips malformed log lines
5. Version-change recording validates input and rejects duplicate versions
6. Affected mappings / company-role pairs respect old_version and never mutate input
"""

import json
import os
import tempfile
import unittest

from pipeline import embeddings
from pipeline.unmapped_terms_logger import log_unmapped_terms
from pipeline.taxonomy_versioning import (
    record_taxonomy_version_change,
    find_affected_mappings,
    find_affected_company_role_pairs,
    get_changelog,
)
from evaluation.review_unmapped_terms import load_log, aggregate


class TestUnmappedTermsLogging(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.log_path = os.path.join(self.tmpdir.name, "unmapped_terms.log")

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_threshold_above_one_leaves_every_concept_unmapped(self):
        concepts = ["binary search tree", "deadlock"]
        ids, scores, unmapped = embeddings.match_concepts_to_taxonomy(concepts, threshold=1.01)
        self.assertEqual(ids, [])
        self.assertEqual(scores, {})
        self.assertEqual(unmapped, concepts)

    def test_logger_writes_one_line_per_term(self):
        log_unmapped_terms(["foo", "bar"], "interview", "v1.0", source_id="R1_q0", log_path=self.log_path)
        entries = load_log(self.log_path)
        self.assertEqual([e["term"] for e in entries], ["foo", "bar"])
        for e in entries:
            self.assertEqual(e["source_id"], "R1_q0")
            self.assertEqual(e["source_type"], "interview")
            self.assertEqual(e["taxonomy_version"], "v1.0")
            self.assertIn("logged_at", e)

    def test_logger_ignores_empty_list(self):
        log_unmapped_terms([], "interview", "v1.0", log_path=self.log_path)
        self.assertFalse(os.path.exists(self.log_path))

    def test_frequency_counts_distinct_sources_not_reruns(self):
        for _ in range(3):  # same data rerun three times, as the API does per request
            log_unmapped_terms(["leetcode"], "interview", "v1.0", source_id="R1_q0", log_path=self.log_path)
            log_unmapped_terms(["leetcode"], "interview", "v1.0", source_id="R2_q0", log_path=self.log_path)
        rows = aggregate(load_log(self.log_path))
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["frequency"], 2)
        self.assertEqual(rows[0]["occurrences"], 6)

    def test_aggregate_sorts_by_frequency_and_filters_version(self):
        log_unmapped_terms(["rare"], "syllabus", "v1.0", source_id="S1", log_path=self.log_path)
        for i in range(3):
            log_unmapped_terms(["common"], "interview", "v1.0", source_id=f"R{i}", log_path=self.log_path)
        log_unmapped_terms(["newer"], "interview", "v1.1", source_id="R9", log_path=self.log_path)
        rows = aggregate(load_log(self.log_path), taxonomy_version="v1.0")
        self.assertEqual([r["term"] for r in rows], ["common", "rare"])

    def test_malformed_lines_are_skipped(self):
        log_unmapped_terms(["ok"], "interview", "v1.0", source_id="R1", log_path=self.log_path)
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write("{not json\n")
        self.assertEqual(len(load_log(self.log_path)), 1)


class TestTaxonomyVersioning(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.changelog = os.path.join(self.tmpdir.name, "taxonomy_changelog.json")
        self.mappings = [
            {"company": "Amazon", "role": "SDE-1", "matched_topic_ids": ["dsa.trees.bst"], "taxonomy_version": "v1.0"},
            {"company": "Amazon", "role": "SDE-1", "matched_topic_ids": ["dsa.dp.knapsack"], "taxonomy_version": "v1.0"},
            {"company": "Google", "role": "L3", "credit": {"dsa.trees.bst": 1.0}, "taxonomy_version": "v1.1"},
            {"source_type": "syllabus", "matched_topic_ids": ["dsa.trees.bst"], "taxonomy_version": "v1.0"},
        ]

    def tearDown(self):
        self.tmpdir.cleanup()

    def _record(self, **overrides):
        kwargs = dict(
            change_type="additive", old_version="v1.0", new_version="v1.1",
            affected_topic_ids=["dsa.trees.bst"], reason="test", reviewed_by="tester",
            changelog_path=self.changelog,
        )
        kwargs.update(overrides)
        return record_taxonomy_version_change(**kwargs)

    def test_record_appends_to_changelog(self):
        entry = self._record()
        self.assertEqual(get_changelog(self.changelog), [entry])
        with open(self.changelog, encoding="utf-8") as f:
            self.assertEqual(json.load(f)[0]["new_version"], "v1.1")

    def test_invalid_change_type_rejected(self):
        with self.assertRaises(ValueError):
            self._record(change_type="rename")

    def test_same_version_rejected(self):
        with self.assertRaises(ValueError):
            self._record(new_version="v1.0")

    def test_empty_affected_topics_rejected(self):
        with self.assertRaises(ValueError):
            self._record(affected_topic_ids=[])

    def test_duplicate_new_version_rejected(self):
        self._record()
        with self.assertRaises(ValueError):
            self._record(change_type="structural")
        self.assertEqual(len(get_changelog(self.changelog)), 1)

    def test_affected_pairs_filtered_by_old_version(self):
        pairs = find_affected_company_role_pairs(["dsa.trees.bst"], self.mappings, old_version="v1.0")
        self.assertEqual(pairs, [("Amazon", "SDE-1")])

    def test_affected_pairs_without_version_filter_reads_credit_too(self):
        pairs = find_affected_company_role_pairs(["dsa.trees.bst"], self.mappings)
        self.assertEqual(pairs, [("Amazon", "SDE-1"), ("Google", "L3")])

    def test_affected_mappings_include_syllabus_records(self):
        affected = find_affected_mappings(["dsa.trees.bst"], self.mappings, old_version="v1.0")
        self.assertEqual(len(affected), 2)
        self.assertIn("syllabus", [m.get("source_type") for m in affected])

    def test_lookup_is_read_only(self):
        before = json.dumps(self.mappings, sort_keys=True)
        find_affected_mappings(["dsa.trees.bst"], self.mappings)
        self.assertEqual(json.dumps(self.mappings, sort_keys=True), before)


if __name__ == "__main__":
    unittest.main()
