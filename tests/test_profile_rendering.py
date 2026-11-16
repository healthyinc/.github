#!/usr/bin/env python3
"""Falsifiable unit tests for SVG XML chart rendering, README updates, and modularity caps."""

import os
import re
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SCRIPTS_DIR = os.path.join(REPO_ROOT, "scripts")
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

import svg_charts
import update_readme


class ProfileRenderingTests(unittest.TestCase):
    def test_svg_valid_xml_and_readme_tag_replacement(self):
        """Verifies SVG XML validity (including C++ & C escaping) and README section updates."""
        with tempfile.TemporaryDirectory() as tmp:
            lang_svg = os.path.join(tmp, "languages.svg")
            act_svg = os.path.join(tmp, "activity.svg")
            svg_charts.generate_languages_svg({"Python": 204800, "C++ & C": 51200}, lang_svg)
            svg_charts.generate_activity_svg([2] * 52, act_svg)
            ET.parse(lang_svg)
            ET.parse(act_svg)

            prof_md = os.path.join(tmp, "profile_README.md")
            root_md = os.path.join(tmp, "README.md")
            template = (
                "<!-- START_MATRIX -->\nold\n<!-- END_MATRIX -->\n"
                "<!-- START_STATS -->\nold\n<!-- END_STATS -->\n"
                "<!-- START_COLLABORATORS -->\nold\n<!-- END_COLLABORATORS -->\n"
            )
            with open(prof_md, "w", encoding="utf-8") as handle:
                handle.write(template)

            self.assertTrue(update_readme.update_readme_files("STATS_OK", "MATRIX_OK", "COLLABS_OK", prof_md, root_md))
            with open(root_md, "r", encoding="utf-8") as handle:
                rendered = handle.read()
            self.assertIn("STATS_OK", rendered)
            self.assertIn("MATRIX_OK", rendered)
            self.assertIn("COLLABS_OK", rendered)

    def test_modularity_and_terminology_hygiene(self):
        """Enforces <=500 LOC file modularity and prohibits sprint/phase terminology."""
        forbidden = re.compile(r"\b(sprint|sub-sprint|phase|milestone|iteration|track)\b", re.IGNORECASE)
        for rel in ["profile/README.md", "README.md"]:
            with open(os.path.join(REPO_ROOT, rel), "r", encoding="utf-8") as handle:
                self.assertIsNone(forbidden.search(handle.read()), f"Forbidden term in {rel}")

        for fname in os.listdir(SCRIPTS_DIR):
            if fname.endswith(".py"):
                with open(os.path.join(SCRIPTS_DIR, fname), "r", encoding="utf-8") as handle:
                    self.assertLessEqual(sum(1 for _ in handle), 500, f"{fname} exceeds 500 LOC")


if __name__ == "__main__":
    unittest.main()
