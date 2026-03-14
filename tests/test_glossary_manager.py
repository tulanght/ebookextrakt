# --------------------------------------------------------------------------------
# Project: ExtractPDF-EPUB
# File: tests/test_glossary_manager.py
# Version: 1.0.0
# Description: Unit tests for GlossaryManager core logic.
# --------------------------------------------------------------------------------

import unittest
import json
import tempfile
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from extract_app.core.glossary_manager import GlossaryManager


class TestGlossaryManagerInit(unittest.TestCase):
    """Tests for initialization and persistence loading."""

    def _make_manager(self, tmp_dir):
        return GlossaryManager(data_path=str(Path(tmp_dir) / "glossary.json"))

    def test_default_data_when_no_file(self):
        """New manager with no file should initialize with General category."""
        with tempfile.TemporaryDirectory() as tmp:
            gm = self._make_manager(tmp)
            self.assertEqual(gm.get_categories(), ["General"])
            self.assertEqual(gm.get_active_category(), "General")

    def test_creates_file_on_init(self):
        """Should auto-create the JSON file on first run."""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "glossary.json"
            self.assertFalse(path.exists())
            GlossaryManager(data_path=str(path))
            self.assertTrue(path.exists())

    def test_loads_existing_data(self):
        """Should correctly load pre-existing categories and terms."""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "glossary.json"
            pre_data = {
                "active_category": "Biology",
                "categories": {
                    "General": {},
                    "Biology": {"habitat": "môi trường sống"}
                }
            }
            path.write_text(json.dumps(pre_data), encoding="utf-8")
            gm = GlossaryManager(data_path=str(path))
            self.assertEqual(gm.get_active_category(), "Biology")
            self.assertIn("Biology", gm.get_categories())
            self.assertEqual(gm.get_terms("Biology"), {"habitat": "môi trường sống"})

    def test_corrupted_file_fallback(self):
        """Corrupted JSON file should not crash — falls back to default."""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "glossary.json"
            path.write_text("this is not valid json", encoding="utf-8")
            gm = GlossaryManager(data_path=str(path))
            # Should still have the General category from DEFAULT_DATA
            self.assertIn("General", gm.get_categories())


class TestCategoryManagement(unittest.TestCase):
    """Tests for category CRUD operations."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.gm = GlossaryManager(data_path=str(Path(self.tmp) / "g.json"))

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_add_category(self):
        self.gm.add_category("Biology")
        self.assertIn("Biology", self.gm.get_categories())

    def test_add_duplicate_category_noop(self):
        self.gm.add_category("Biology")
        self.gm.add_category("Biology")
        self.assertEqual(self.gm.get_categories().count("Biology"), 1)

    def test_add_empty_string_category_noop(self):
        self.gm.add_category("")
        self.assertNotIn("", self.gm.get_categories())

    def test_set_active_category_existing(self):
        self.gm.add_category("History")
        result = self.gm.set_active_category("History")
        self.assertTrue(result)
        self.assertEqual(self.gm.get_active_category(), "History")

    def test_set_active_category_nonexistent_returns_false(self):
        result = self.gm.set_active_category("NonExistent")
        self.assertFalse(result)
        self.assertEqual(self.gm.get_active_category(), "General")

    def test_delete_category_success(self):
        self.gm.add_category("Gardening")
        # Must not be active; General is active
        result = self.gm.delete_category("Gardening")
        self.assertTrue(result)
        self.assertNotIn("Gardening", self.gm.get_categories())

    def test_cannot_delete_general(self):
        result = self.gm.delete_category("General")
        self.assertFalse(result)
        self.assertIn("General", self.gm.get_categories())

    def test_cannot_delete_active_category(self):
        self.gm.add_category("Biology")
        self.gm.set_active_category("Biology")
        result = self.gm.delete_category("Biology")  # Active → should fail
        self.assertFalse(result)
        self.assertIn("Biology", self.gm.get_categories())

    def test_delete_nonexistent_returns_false(self):
        result = self.gm.delete_category("Nonexistent")
        self.assertFalse(result)


class TestTermManagement(unittest.TestCase):
    """Tests for term CRUD operations."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.gm = GlossaryManager(data_path=str(Path(self.tmp) / "g.json"))

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_add_term_to_active_category(self):
        self.gm.add_term("habitat", "môi trường sống")
        self.assertEqual(self.gm.get_terms()["habitat"], "môi trường sống")

    def test_add_term_with_whitespace_stripped(self):
        self.gm.add_term("  species  ", "  giống loài  ")
        self.assertIn("species", self.gm.get_terms())
        self.assertEqual(self.gm.get_terms()["species"], "giống loài")

    def test_add_term_to_specific_category(self):
        self.gm.add_category("History")
        self.gm.add_term("civil war", "nội chiến", category="History")
        self.assertNotIn("civil war", self.gm.get_terms("General"))
        self.assertIn("civil war", self.gm.get_terms("History"))

    def test_add_term_updates_existing(self):
        """Adding a term that already exists should update its value."""
        self.gm.add_term("habitat", "môi trường sống")
        self.gm.add_term("habitat", "môi trường")  # Updated
        self.assertEqual(self.gm.get_terms()["habitat"], "môi trường")

    def test_add_term_empty_en_ignored(self):
        self.gm.add_term("", "some value")
        self.assertEqual(self.gm.get_terms(), {})

    def test_add_term_empty_vi_ignored(self):
        self.gm.add_term("habitat", "")
        self.assertEqual(self.gm.get_terms(), {})

    def test_delete_term(self):
        self.gm.add_term("photosynthesis", "quang hợp")
        self.gm.delete_term("photosynthesis")
        self.assertNotIn("photosynthesis", self.gm.get_terms())

    def test_delete_nonexistent_term_noop(self):
        """Deleting a term that doesn't exist should not raise an error."""
        self.gm.delete_term("nonexistent_term")  # Must not throw
        self.assertEqual(self.gm.get_terms(), {})

    def test_get_terms_returns_empty_for_unknown_category(self):
        terms = self.gm.get_terms("UnknownCategory")
        self.assertEqual(terms, {})


class TestPromptInjection(unittest.TestCase):
    """Tests for get_active_glossary_string() — the LLM prompt serialization."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.gm = GlossaryManager(data_path=str(Path(self.tmp) / "g.json"))

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_empty_category_returns_empty_string(self):
        """Active category with no terms must return ''."""
        result = self.gm.get_active_glossary_string()
        self.assertEqual(result, "")

    def test_single_term_format(self):
        """Format must be: 'en_term' → 'vi_term'"""
        self.gm.add_term("habitat", "môi trường sống")
        result = self.gm.get_active_glossary_string()
        self.assertIn("'habitat' → 'môi trường sống'", result)

    def test_multiple_terms_one_per_line(self):
        """Multiple terms should each appear on their own line."""
        self.gm.add_term("habitat", "môi trường sống")
        self.gm.add_term("species", "giống loài")
        result = self.gm.get_active_glossary_string()
        lines = result.strip().split("\n")
        self.assertEqual(len(lines), 2)

    def test_glossary_reflects_active_category(self):
        """String must reflect the active, not another, category."""
        self.gm.add_category("Biology")
        self.gm.add_term("biome", "quần xã sinh vật", category="Biology")
        self.gm.add_term("castle", "lâu đài", category="General")
        self.gm.set_active_category("Biology")
        result = self.gm.get_active_glossary_string()
        self.assertIn("biome", result)
        self.assertNotIn("castle", result)


class TestPersistence(unittest.TestCase):
    """Tests that changes are correctly saved and reloaded from JSON."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.path = str(Path(self.tmp) / "g.json")

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_terms_survive_reload(self):
        """Terms added in one session should be loadable in the next."""
        gm1 = GlossaryManager(data_path=self.path)
        gm1.add_category("Biology")
        gm1.add_term("photosynthesis", "quang hợp", category="Biology")

        # Simulate a new session
        gm2 = GlossaryManager(data_path=self.path)
        self.assertIn("Biology", gm2.get_categories())
        self.assertEqual(gm2.get_terms("Biology").get("photosynthesis"), "quang hợp")

    def test_active_category_survives_reload(self):
        gm1 = GlossaryManager(data_path=self.path)
        gm1.add_category("History")
        gm1.set_active_category("History")
        gm2 = GlossaryManager(data_path=self.path)
        self.assertEqual(gm2.get_active_category(), "History")

class TestRelevantGlossaryString(unittest.TestCase):
    """Tests for get_relevant_glossary_string() — chunk-aware filtering."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.gm = GlossaryManager(data_path=str(Path(self.tmp) / "g.json"))
        # Add a realistic glossary
        self.gm.add_term("sow", "lợn nái")
        self.gm.add_term("wild boar", "lợn rừng")
        self.gm.add_term("snout", "mõm")
        self.gm.add_term("habitat", "môi trường sống")
        self.gm.add_term("Tamworth", "(giống lợn) Tamworth")

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_returns_only_matching_terms(self):
        """Only terms present in source text should appear."""
        text = "The sow used her snout to dig for roots."
        result = self.gm.get_relevant_glossary_string(text)
        self.assertIn("sow", result)
        self.assertIn("snout", result)
        self.assertNotIn("habitat", result)
        self.assertNotIn("wild boar", result)

    def test_case_insensitive_matching(self):
        """Matching should be case-insensitive."""
        text = "The SOW is a female pig."
        result = self.gm.get_relevant_glossary_string(text)
        self.assertIn("sow", result)

    def test_word_boundary_no_partial_match(self):
        """'sow' should NOT match in 'Moscow'."""
        text = "The delegation traveled to Moscow for the conference."
        result = self.gm.get_relevant_glossary_string(text)
        self.assertNotIn("sow", result)

    def test_empty_text_returns_empty(self):
        result = self.gm.get_relevant_glossary_string("")
        self.assertEqual(result, "")

    def test_multi_word_term_matching(self):
        """Multi-word terms like 'wild boar' should match as a phrase."""
        text = "The wild boar is the ancestor of the domestic pig."
        result = self.gm.get_relevant_glossary_string(text)
        self.assertIn("wild boar", result)


if __name__ == '__main__':
    unittest.main()
