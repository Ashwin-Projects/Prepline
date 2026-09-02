"""
Phase 3 Taxonomy Validation Test Suite

Validates:
1. JSON loads successfully from data/taxonomy/taxonomy_v1.0.json
2. taxonomy_version is exactly "v1.0"
3. All topic_id values are unique, machine-friendly, and non-empty
4. Every node contains required fields: topic_id, name, type, description, domain
5. Node type is strictly 'high_level_concept' or 'granular_skill'
6. All five major domains (dsa, dbms, os, cn, system_design) are present
7. Descriptions are non-empty and detailed enough for embedding
"""

import unittest
import json
import os
import re

TAXONOMY_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "data",
    "taxonomy",
    "taxonomy_v1.0.json"
)

REQUIRED_DOMAINS = {"dsa", "dbms", "os", "cn", "system_design"}
ALLOWED_TYPES = {"high_level_concept", "granular_skill"}


class TestVersionedTaxonomy(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        self_dir = os.path.dirname(os.path.abspath(__file__))
        cls.taxonomy_file = os.path.abspath(os.path.join(self_dir, "..", "data", "taxonomy", "taxonomy_v1.0.json"))
        cls.assertTrue(os.path.exists(cls.taxonomy_file), f"Taxonomy file missing at {cls.taxonomy_file}")
        
        with open(cls.taxonomy_file, "r", encoding="utf-8") as f:
            cls.data = json.load(f)

    def test_json_structure_and_version(self):
        self.assertIn("taxonomy_version", self.data)
        self.assertEqual(self.data["taxonomy_version"], "v1.0")
        self.assertIn("nodes", self.data)
        self.assertIsInstance(self.data["nodes"], list)
        self.assertGreater(len(self.data["nodes"]), 0)

    def test_five_domains_represented(self):
        found_domains = set()
        for node in self.data["nodes"]:
            domain = node.get("domain")
            if domain:
                found_domains.add(domain.lower())
        
        missing = REQUIRED_DOMAINS - found_domains
        self.assertEqual(len(missing), 0, f"Missing required domains: {missing}")

    def test_topic_id_uniqueness_and_format(self):
        seen_ids = set()
        topic_id_pattern = re.compile(r'^[a-z0-9_]+(?:\.[a-z0-9_]+)*$')

        for node in self.data["nodes"]:
            topic_id = node.get("topic_id")
            self.assertIsNotNone(topic_id, f"Node missing topic_id: {node}")
            self.assertNotIn(topic_id, seen_ids, f"Duplicate topic_id found: '{topic_id}'")
            seen_ids.add(topic_id)

            # Assert machine-friendly ID format (lowercase, dot-separated, alphanumeric/underscore)
            self.assertTrue(
                topic_id_pattern.match(topic_id),
                f"topic_id '{topic_id}' does not match required format (lowercase, dot-separated)"
            )

    def test_node_fields_and_classification(self):
        for node in self.data["nodes"]:
            topic_id = node.get("topic_id")
            self.assertIn("name", node, f"Node '{topic_id}' missing name")
            self.assertIn("type", node, f"Node '{topic_id}' missing type")
            self.assertIn("description", node, f"Node '{topic_id}' missing description")
            self.assertIn("domain", node, f"Node '{topic_id}' missing domain")

            # Check valid node type
            node_type = node["type"]
            self.assertIn(
                node_type,
                ALLOWED_TYPES,
                f"Node '{topic_id}' has invalid type '{node_type}'. Must be one of {ALLOWED_TYPES}"
            )

            # Check description richness for sentence embedding
            desc = node["description"]
            self.assertGreaterEqual(
                len(desc.strip().split()),
                5,
                f"Node '{topic_id}' description too short for embedding: '{desc}'"
            )

    def test_parent_id_validity(self):
        all_ids = {node["topic_id"] for node in self.data["nodes"]}
        for node in self.data["nodes"]:
            parent_id = node.get("parent_id")
            if parent_id is not None:
                self.assertIn(
                    parent_id,
                    all_ids,
                    f"Node '{node['topic_id']}' references unknown parent_id '{parent_id}'"
                )


if __name__ == "__main__":
    unittest.main()
