"""
Unit Tests for Phase 14 Backend API Skeleton

Tests API endpoints:
- GET / health check & supported targets
- POST /api/v1/validate-target (Amazon SDE-1 vs unsupported roles)
- POST /api/v1/syllabi/upload (PDF upload & scanned detection)
- POST /api/v1/pipeline/run (Pipeline execution & result structure)
"""

import unittest
import os
import tempfile
from fastapi.testclient import TestClient

from backend.app import app
from reportlab.pdfgen import canvas

client = TestClient(app)


class TestBackendAPI(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.temp_dir.cleanup()

    def create_sample_pdf(self, filename: str) -> str:
        pdf_path = os.path.join(self.temp_dir.name, filename)
        c = canvas.Canvas(pdf_path)
        c.drawString(100, 750, "Course Code: CSE2001")
        c.drawString(100, 735, "Course Title: Data Structures and Algorithms")
        c.drawString(100, 720, "L T P J C : 3 0 2 0 4")
        c.drawString(100, 680, "Module: 1 Stacks and Queues (6 hours)")
        c.drawString(100, 665, "Stack operations, Queue implementations. Lab exercise 1.")
        c.save()
        return pdf_path

    def test_health_check(self):
        response = client.get("/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["engine"], "PREPLINE")
        self.assertEqual(data["scope"], "Amazon SDE-1 Prototype")

    def test_supported_targets(self):
        response = client.get("/api/v1/supported-targets")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data["supported_targets"]), 1)
        self.assertEqual(data["supported_targets"][0]["company"], "Amazon")
        self.assertEqual(data["supported_targets"][0]["role"], "SDE-1")

    def test_validate_target_amazon_sde1(self):
        payload = {"company": "Amazon", "role": "SDE-1"}
        response = client.post("/api/v1/validate-target", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["eligible"])
        self.assertEqual(data["status"], "ELIGIBLE")
        self.assertGreaterEqual(data["report_count"], 15)

    def test_validate_target_unsupported_role(self):
        payload = {"company": "Google", "role": "L3"}
        response = client.post("/api/v1/validate-target", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data["eligible"])
        self.assertEqual(data["status"], "UNSUPPORTED_ROLE")

    def test_upload_syllabus_non_pdf(self):
        files = {"file": ("test.txt", b"Hello world text", "text/plain")}
        response = client.post("/api/v1/syllabi/upload", files=files)
        self.assertEqual(response.status_code, 400)

    def test_upload_syllabus_pdf_success(self):
        pdf_path = self.create_sample_pdf("test_syllabus.pdf")
        with open(pdf_path, "rb") as f:
            files = {"file": ("test_syllabus.pdf", f, "application/pdf")}
            response = client.post("/api/v1/syllabi/upload", files=files)
        
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertIn("syllabus_id", data)
        self.assertEqual(data["course_code"], "CSE2001")
        self.assertEqual(data["taxonomy_version"], "v1.0")

    def test_pipeline_run_success(self):
        # 1. Upload syllabus first
        pdf_path = self.create_sample_pdf("pipeline_syllabus.pdf")
        with open(pdf_path, "rb") as f:
            files = {"file": ("pipeline_syllabus.pdf", f, "application/pdf")}
            upload_res = client.post("/api/v1/syllabi/upload", files=files)
        
        syllabus_id = upload_res.json()["syllabus_id"]

        # 2. Run pipeline
        run_payload = {
            "syllabus_id": syllabus_id,
            "company": "Amazon",
            "role": "SDE-1"
        }
        response = client.post("/api/v1/pipeline/run", json=run_payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()

        # 3. Assert all required PREPLINE result fields
        self.assertEqual(data["company"], "Amazon")
        self.assertEqual(data["role"], "SDE-1")
        self.assertTrue(data["density_gate_passed"])
        self.assertIsNotNone(data["S_comp"])
        self.assertIn("topic_coverage", data)
        self.assertIn("interview_importance", data)
        self.assertIn("priority_gaps", data)
        self.assertEqual(data["taxonomy_version"], "v1.0")
        self.assertEqual(data["scoring_config_version"], "v1.0")
        self.assertIn("depth_confidence_status", data)


if __name__ == "__main__":
    unittest.main()
