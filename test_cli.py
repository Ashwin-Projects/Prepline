import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class CliTests(unittest.TestCase):
    def run_cli(self, *args):
        return subprocess.run(
            [sys.executable, "-m", "pipeline.cli", *args],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_map_command_emits_keyword_match(self):
        result = self.run_cli("map", "dynamic programming", "--methods", "keyword")
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertIn("dsa.dynamic_programming", {row["topic_id"] for row in payload["keyword"]})

    def test_coverage_command_reports_gaps(self):
        result = self.run_cli(
            "coverage",
            "--syllabus-topic-ids", "dsa.arrays,dsa.graphs",
            "--interview-topic-ids", "dsa.arrays,dbms.normalization",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["coverage_percent"], 50.0)
        self.assertEqual(payload["gap_topics"], ["dbms.normalization"])

    def test_course_search(self):
        result = self.run_cli("courses", "Operating Systems")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("BCSE303L", result.stdout)


if __name__ == "__main__":
    unittest.main()
