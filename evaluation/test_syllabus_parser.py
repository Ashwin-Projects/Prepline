"""
Unit Tests for Phase 7 Syllabus Parser
Tests text-selectable VIT syllabus parsing and scanned PDF detection.
"""

import unittest
import os
import tempfile
import pdfplumber

from pipeline.syllabus_parser import (
    parse_syllabus_pdf,
    is_scanned_pdf,
    UnsupportedPDFError,
    extract_course_metadata,
    extract_depth_signals
)


class TestSyllabusParser(unittest.TestCase):

    def setUp(self):
        # We will create temporary PDFs for testing
        self.temp_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_extract_course_metadata(self):
        sample_text = """
        Course Code: CSE2001
        Course Title: Data Structures and Algorithms
        L T P J C
        3 0 2 0 4
        """
        meta = extract_course_metadata(sample_text)
        self.assertEqual(meta["course_code"], "CSE2001")
        self.assertEqual(meta["course_title"], "Data Structures and Algorithms")
        self.assertEqual(meta["lecture_hours"], 3)
        self.assertEqual(meta["practical_hours"], 2)
        self.assertEqual(meta["credits"], 4)

    def test_extract_depth_signals(self):
        unit_text = """
        Module 1: Stacks and Queues (6 hours)
        Array implementation of stacks. Lab exercise 1 and Lab exercise 2.
        Assignment 1: Evaluate postfix expression.
        """
        course_meta = {"practical_hours": 2}
        depth = extract_depth_signals(unit_text, course_meta)
        
        self.assertEqual(depth["unit_hours"], 6)
        self.assertEqual(depth["lab_count"], 2)
        self.assertEqual(depth["assignment_count"], 1)

    def test_scanned_pdf_detection(self):
        # Create a mock PDF with no text (simulating scanned image PDF)
        from reportlab.pdfgen import canvas
        scanned_pdf_path = os.path.join(self.temp_dir.name, "scanned_syllabus.pdf")
        
        c = canvas.Canvas(scanned_pdf_path)
        # Draw only shapes/images, no text string
        c.rect(100, 100, 200, 200, fill=1)
        c.save()

        self.assertTrue(is_scanned_pdf(scanned_pdf_path))
        with self.assertRaises(UnsupportedPDFError):
            parse_syllabus_pdf(scanned_pdf_path)

    def test_text_selectable_pdf_parsing(self):
        # Create a text-selectable PDF with VIT syllabus format
        from reportlab.pdfgen import canvas
        valid_pdf_path = os.path.join(self.temp_dir.name, "vit_cse2001.pdf")
        
        c = canvas.Canvas(valid_pdf_path)
        c.drawString(100, 750, "Course Code: CSE2001")
        c.drawString(100, 735, "Course Title: Data Structures and Algorithms")
        c.drawString(100, 720, "L T P J C : 3 0 2 0 4")
        
        c.drawString(100, 680, "Module: 1 Stacks and Queues (6 hours)")
        c.drawString(100, 665, "Basic operations on stacks and queues. Lab exercise 1.")
        c.drawString(100, 650, "Assignment 1: Implementation of double ended queue.")
        
        c.drawString(100, 600, "Module: 2 Trees and Binary Search Trees (8 hours)")
        c.drawString(100, 585, "Binary tree traversals, BST insertion and deletion. Lab exercise 2.")
        c.save()

        self.assertFalse(is_scanned_pdf(valid_pdf_path))
        
        result = parse_syllabus_pdf(valid_pdf_path, taxonomy_version="v1.0")
        
        self.assertEqual(result["source_type"], "syllabus")
        self.assertEqual(result["taxonomy_version"], "v1.0")
        self.assertEqual(result["course_metadata"]["course_code"], "CSE2001")
        self.assertEqual(len(result["two_pass_mappings"]), 2)
        
        # Check two-pass abstraction mapping structure & preserved taxonomy version
        first_mapping = result["two_pass_mappings"][0]
        self.assertEqual(first_mapping["source_id"], "CSE2001_mod_1")
        self.assertEqual(first_mapping["source_type"], "syllabus")
        self.assertEqual(first_mapping["taxonomy_version"], "v1.0")
        self.assertIn("stacks", first_mapping["intermediate_concepts"])
        self.assertIn("queues", first_mapping["intermediate_concepts"])
        self.assertEqual(first_mapping["depth_signals"]["unit_hours"], 6)


if __name__ == "__main__":
    unittest.main()
