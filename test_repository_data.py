import csv
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class RepositoryDataTests(unittest.TestCase):
    def test_taxonomy_ids_unique(self):
        data = json.loads((ROOT / "data/taxonomy/taxonomy_v1.1.json").read_text(encoding="utf-8"))
        ids = [topic["topic_id"] for topic in data["topics"]]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertGreaterEqual(len(ids), 1)

    def test_candidate_mappings_have_valid_topics_and_review_status(self):
        taxonomy = json.loads((ROOT / "data/taxonomy/taxonomy_v1.1.json").read_text(encoding="utf-8"))
        valid = {topic["topic_id"] for topic in taxonomy["topics"]}
        for name in ("source_backed_mappings_for_review.csv", "codeprep_mappings_for_review.csv"):
            with (ROOT / "evaluation" / name).open(encoding="utf-8-sig", newline="") as stream:
                rows = list(csv.DictReader(stream))
            self.assertGreater(len(rows), 0, name)
            for row in rows:
                self.assertIn(row["expected_topic_id"], valid)
                self.assertEqual(row["taxonomy_version"], taxonomy["taxonomy_version"])
                self.assertEqual(row["review_status"], "needs_human_review")
                self.assertEqual(row["reviewer"], "")
                self.assertEqual(row["review_date"], "")

    def test_ground_truth_does_not_auto_accept_candidates(self):
        with (ROOT / "evaluation/ground_truth.csv").open(encoding="utf-8-sig", newline="") as stream:
            rows = list(csv.DictReader(stream))
        self.assertFalse(any(row.get("review_status", "").lower() in {"verified", "approved"} for row in rows))

    def test_validator_passes_structural_checks(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts/validate_prepline_data.py")],
            cwd=ROOT, capture_output=True, text=True, check=False
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
