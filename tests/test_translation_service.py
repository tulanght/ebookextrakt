# --------------------------------------------------------------------------------
# Project: ExtractPDF-EPUB
# File: tests/test_translation_service.py
# Version: 1.0.0
# Author: Antigravity
# Description: Unit tests for TranslationService and LocalTranslationService.
# --------------------------------------------------------------------------------

import unittest
from unittest.mock import MagicMock, patch
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


class TestCleanTranslationOutput(unittest.TestCase):
    """Tests for TranslationService._clean_translation_output()."""

    def setUp(self):
        """Create a minimal TranslationService with mocked dependencies."""
        mock_settings = MagicMock()
        mock_settings.get_api_key.return_value = ""
        mock_settings.get.return_value = ""

        with patch('extract_app.core.translation_service.genai'):
            from extract_app.core.translation_service import TranslationService
            self.service = TranslationService(mock_settings)

    def test_strips_code_fences(self):
        """AI sometimes wraps output in code fences — should be removed."""
        raw = "```\nĐây là bản dịch.\n```"
        result = self.service._clean_translation_output(raw)
        self.assertEqual(result, "Đây là bản dịch.")

    def test_strips_preamble_vietnamese(self):
        """Remove common Vietnamese preambles like 'Dưới đây là bản dịch'."""
        raw = "Dưới đây là bản dịch tiếng Việt:\nNội dung thực sự."
        result = self.service._clean_translation_output(raw)
        self.assertEqual(result, "Nội dung thực sự.")

    def test_strips_trailing_notes(self):
        """Remove trailing notes appended by AI."""
        raw = "Nội dung dịch xong.\n\nLưu ý: Đây chỉ là bản dịch tham khảo."
        result = self.service._clean_translation_output(raw)
        self.assertEqual(result, "Nội dung dịch xong.")

    def test_collapses_excessive_newlines(self):
        """3+ newlines should be collapsed to 2."""
        raw = "Đoạn 1.\n\n\n\n\nĐoạn 2."
        result = self.service._clean_translation_output(raw)
        self.assertEqual(result, "Đoạn 1.\n\nĐoạn 2.")

    def test_preserves_img_placeholders(self):
        """__IMG_XXX__ placeholders must survive cleaning."""
        raw = "__IMG_001__ cho thấy loài này.\n\n__IMG_002__ là bản đồ."
        result = self.service._clean_translation_output(raw)
        self.assertIn("__IMG_001__", result)
        self.assertIn("__IMG_002__", result)

    def test_clean_text_passthrough(self):
        """Already clean text should pass through unchanged."""
        raw = "Đây là văn bản sạch."
        result = self.service._clean_translation_output(raw)
        self.assertEqual(result, raw)


class TestChunkText(unittest.TestCase):
    """Tests for TranslationService.chunk_text()."""

    def setUp(self):
        mock_settings = MagicMock()
        mock_settings.get_api_key.return_value = ""
        mock_settings.get.return_value = ""

        with patch('extract_app.core.translation_service.genai'):
            from extract_app.core.translation_service import TranslationService
            self.service = TranslationService(mock_settings)

    def test_short_text_no_split(self):
        """Text shorter than chunk_size should return as single chunk."""
        text = "Short text."
        chunks = self.service.chunk_text(text, chunk_size=1000)
        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0], text)

    def test_splits_by_markdown_headers(self):
        """Text with ## headers should split at header boundaries."""
        text = "Intro paragraph.\n\n## Section A\n\nContent A.\n\n## Section B\n\nContent B."
        chunks = self.service.chunk_text(text, chunk_size=30)
        self.assertGreater(len(chunks), 1)

    def test_returns_nonempty_chunks(self):
        """All returned chunks should be non-empty."""
        text = "A " * 500 + "\n\n## Header\n\n" + "B " * 500
        chunks = self.service.chunk_text(text, chunk_size=200)
        for chunk in chunks:
            self.assertTrue(len(chunk.strip()) > 0)


class TestLocalPromptStrictness(unittest.TestCase):
    """Tests for LocalTranslationService strict prompt construction."""

    def test_strict_prompt_contains_rules(self):
        """STRICT_SYSTEM_PROMPT must contain critical rules."""
        from extract_app.core.local_genai import LocalTranslationService
        prompt = LocalTranslationService.STRICT_SYSTEM_PROMPT
        self.assertIn("__IMG_000__", prompt)
        self.assertIn("KHÔNG giải thích", prompt)
        self.assertIn("Markdown", prompt)


class TestAnchorProtection(unittest.TestCase):
    """Tests for anchor protection and restoration pipeline."""

    def setUp(self):
        mock_settings = MagicMock()
        mock_settings.get_api_key.return_value = ""
        mock_settings.get.return_value = ""

        with patch('extract_app.core.translation_service.genai'):
            from extract_app.core.translation_service import TranslationService
            self.service = TranslationService(mock_settings)

    def test_protect_and_restore_roundtrip(self):
        """Protecting and then restoring anchors should return original text."""
        original = "Some text [Image: photo.jpg] more text [Image: diagram.png] end."
        protected, mapping = self.service._protect_anchors(original)
        
        # Placeholders should be present
        self.assertIn("__IMG_000__", protected)
        self.assertIn("__IMG_001__", protected)
        self.assertNotIn("[Image:", protected)
        
        # Restore
        restored = self.service._restore_anchors(protected, mapping)
        self.assertEqual(restored, original)

    def test_no_anchors_passthrough(self):
        """Text without anchors should pass through unchanged."""
        text = "No images here."
        protected, mapping = self.service._protect_anchors(text)
        self.assertEqual(protected, text)
        self.assertEqual(len(mapping), 0)

    def test_restores_mutated_local_placeholders(self):
        """Local AI often mutates __IMG_001__ into italics or drops underscores."""
        mapping = {
            "__IMG_000__": "[Image: first.jpg]",
            "__IMG_001__": "[Image: second.png]",
            "__IMG_002__": "[Image: third.webp]"
        }
        # Simulate local LLM corrupted output
        corrupted = "Đây là _IMG_000_ và __ IMG_001 __ cũng như IMG_002."
        restored = self.service._restore_anchors(corrupted, mapping)
        
        self.assertIn("[Image: first.jpg]", restored)
        self.assertIn("[Image: second.png]", restored)
        self.assertIn("[Image: third.webp]", restored)


class TestOverlapLeakageStripping(unittest.TestCase):
    """Tests for the overlap context stripping logic used in local sequential translation."""

    def test_strips_text_before_separator(self):
        """When overlap is prepended, output before --- should be stripped."""
        # Simulate what translate_text does when i > 0
        simulated_output = "Đoạn overlap cũ đã được dịch\n\n---\n\nĐoạn mới được dịch chính xác."
        
        # The logic from translate_text:
        if '---' in simulated_output:
            parts = simulated_output.split('---', 1)
            result = parts[1].strip() if len(parts) > 1 else simulated_output
        
        self.assertEqual(result, "Đoạn mới được dịch chính xác.")

    def test_no_separator_keeps_full_text(self):
        """If model doesn't include ---, keep full output."""
        simulated_output = "Đoạn dịch hoàn chỉnh không có separator."
        
        if '---' in simulated_output:
            parts = simulated_output.split('---', 1)
            result = parts[1].strip() if len(parts) > 1 else simulated_output
        else:
            result = simulated_output
        
        self.assertEqual(result, "Đoạn dịch hoàn chỉnh không có separator.")


if __name__ == '__main__':
    unittest.main()
