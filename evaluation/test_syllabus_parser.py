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
        
        result = parse_syllabus_pdf(valid_pdf_path, taxonomy_version="v1.0", core_courses=["CSE2001"])
        
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


    def test_bst_syllabus_unit_maps_to_taxonomy_presence(self):
        # Syllabus units must go through embedding matching (Phase 5), not just Pass 1 keyword extraction,
        # otherwise C(t) is 0 for every topic.
        from reportlab.pdfgen import canvas
        from pipeline.scoring import calculate_syllabus_coverage
        pdf_path = os.path.join(self.temp_dir.name, "vit_cse2002.pdf")

        c = canvas.Canvas(pdf_path)
        c.drawString(100, 750, "Course Code: CSE2002")
        c.drawString(100, 735, "Course Title: Data Structures")
        c.drawString(100, 700, "Module: 1 Binary Search Trees (8 hours)")
        c.drawString(100, 685, "Binary search trees: insertion, deletion and search in a BST.")
        c.save()

        result = parse_syllabus_pdf(pdf_path, taxonomy_version="v1.0", core_courses=["CSE2002"])
        mapping = result["two_pass_mappings"][0]
        # Syllabus units match only high-level concepts: the BST unit matches BST's parent, dsa.trees
        self.assertIn("dsa.trees", mapping["matched_topic_ids"])
        self.assertNotIn("dsa.trees.bst", mapping["matched_topic_ids"])
        self.assertEqual(mapping["taxonomy_version"], "v1.0")
        self.assertEqual(mapping["depth_signals"]["unit_hours"], 8)

        coverage = calculate_syllabus_coverage(result)
        bst = next(t for t in coverage["topic_coverage"] if t["topic_id"] == "dsa.trees.bst")
        self.assertEqual(bst["presence"], 1)
        self.assertEqual(bst["depth_status"], "measured")

    def test_bst_gets_inherited_coverage(self):
        from reportlab.pdfgen import canvas
        from pipeline.scoring import calculate_syllabus_coverage
        pdf_path = os.path.join(self.temp_dir.name, "vit_cse2002_inherit.pdf")

        c = canvas.Canvas(pdf_path)
        c.drawString(100, 750, "Course Code: CSE2002")
        c.drawString(100, 735, "Course Title: Data Structures")
        c.drawString(100, 700, "Module: 1 Binary Search Trees (8 hours)")
        c.drawString(100, 685, "Binary search trees: insertion, deletion and search in a BST.")
        c.save()

        result = parse_syllabus_pdf(pdf_path, taxonomy_version="v1.0", core_courses=["CSE2002"])
        coverage = {t["topic_id"]: t for t in calculate_syllabus_coverage(result)["topic_coverage"]}
        bst = coverage["dsa.trees.bst"]
        self.assertEqual(bst["coverage_source"], "inherited")
        self.assertEqual(bst["inherited_from"], "dsa.trees")
        self.assertGreater(bst["coverage"], 0.0)
        self.assertEqual(bst["coverage"], coverage["dsa.trees"]["coverage"])

class TestDepthSignals(unittest.TestCase):
    """Item 4: unit_hours from the module header line only; lab hours spread across a course's modules."""

    def test_unit_hours_header_only(self):
        unit_text = "Module: 3 Graph Algorithms\nBFS and DFS, practised over 10 hours of lab sessions."
        self.assertIsNone(extract_depth_signals(unit_text, {})["unit_hours"])

    def test_unit_hours_no_space(self):
        unit_text = "Module:5 Fundamentals of Graphs 6hours\nBasic definitions."
        self.assertEqual(extract_depth_signals(unit_text, {})["unit_hours"], 6)

    def test_lab_hours_spread_across_modules(self):
        signals = extract_depth_signals("Module:1 Intro 4 hours\nx", {"practical_hours": 2}, module_count=4)
        self.assertEqual(signals["lab_hours"], 7.5)  # 2 periods/week * 15 weeks / 4 modules

    def test_course_lab_hours_total_equals_practical_hours(self):
        from pipeline.syllabus_parser import parse_course_modules, segment_courses
        text = ("BCSE203E Web Programming 1 0 2 2\n"
                "Module:1 Introduction 2 hours\nWeb basics.\n"
                "Module:2 HTML 2 hours\nMarkup.\n"
                "Module:3 CSS 2 hours\nStyles.\n"
                "Module:4 JavaScript 3 hours\nScripts.\n"
                "Total Lecture hours: 15 hours\n")
        modules = parse_course_modules(segment_courses(text)[0])
        self.assertEqual(len(modules), 4)
        lab_hours = [m["depth_signals"]["lab_hours"] for m in modules]
        self.assertEqual(lab_hours, [7.5, 7.5, 7.5, 7.5])
        self.assertEqual(sum(lab_hours), 2 * 15)  # not 30 per module
        self.assertEqual([m["depth_signals"]["unit_hours"] for m in modules], [2, 2, 2, 3])

    def test_zero_practical_hours_no_lab_signal(self):
        self.assertIsNone(extract_depth_signals("Module:1 Intro 4 hours", {"practical_hours": 0}, module_count=3)["lab_hours"])


if __name__ == "__main__":
    unittest.main()
