# --------------------------------------------------------------------------------
# Project: ExtractPDF-EPUB
# File: tests/test_prompt_builder.py
# Version: 1.0.0
# Author: Antigravity
# Description: Unit tests for PromptBuilder — all build_* methods and clean_output.
#              Run with: pytest tests/test_prompt_builder.py -v
# --------------------------------------------------------------------------------

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from extract_app.core.prompt_builder import PromptBuilder


@pytest.fixture
def builder():
    return PromptBuilder()


# ─────────────────────────────────────────────────────────────────────────────
# build_translation_prompt
# ─────────────────────────────────────────────────────────────────────────────

class TestBuildTranslationPrompt:

    def test_returns_string(self, builder):
        result = builder.build_translation_prompt("Hello world")
        assert isinstance(result, str)

    def test_contains_system_tag(self, builder):
        result = builder.build_translation_prompt("Hello")
        assert "<SYSTEM>" in result
        assert "</SYSTEM>" in result

    def test_contains_source_text(self, builder):
        text = "The dog barked loudly."
        result = builder.build_translation_prompt(text)
        assert text in result

    def test_no_glossary_omits_glossary_section(self, builder):
        result = builder.build_translation_prompt("test", glossary_str="")
        assert "TỪ VỰNG BẮT BUỘC" not in result

    def test_with_glossary_includes_terms(self, builder):
        glossary = "sow → lợn nái\nentelodonts → entelodont"
        result = builder.build_translation_prompt("text", glossary_str=glossary)
        assert "TỪ VỰNG BẮT BUỘC" in result
        assert "sow → lợn nái" in result

    def test_image_placeholder_instruction_present(self, builder):
        result = builder.build_translation_prompt("test")
        assert "__IMG_" in result or "placeholder" in result.lower() or "IMG" in result

    def test_no_explanation_instruction_present(self, builder):
        """Prompt must instruct AI not to explain."""
        result = builder.build_translation_prompt("text")
        assert "KHÔNG giải thích" in result or "TUYỆT ĐỐI KHÔNG" in result


# ─────────────────────────────────────────────────────────────────────────────
# build_transform_prompt
# ─────────────────────────────────────────────────────────────────────────────

class TestBuildTransformPrompt:

    def test_website_variant_returns_string(self, builder):
        result = builder.build_transform_prompt("archive text", "original en", "website")
        assert isinstance(result, str)

    def test_website_variant_contains_archive_text(self, builder):
        result = builder.build_transform_prompt("ARCHIVE CONTENT", "original", "website")
        assert "ARCHIVE CONTENT" in result

    def test_website_variant_mentions_website(self, builder):
        result = builder.build_transform_prompt("text", "orig", "website")
        assert "website" in result.lower()

    def test_facebook_variant_returns_string(self, builder):
        result = builder.build_transform_prompt("archive", "original", "facebook")
        assert isinstance(result, str)

    def test_facebook_variant_contains_archive_text(self, builder):
        result = builder.build_transform_prompt("ARCHIVE FB", "original", "facebook")
        assert "ARCHIVE FB" in result

    def test_facebook_with_custom_instructions(self, builder):
        custom = "Bạn là Gem — chuyên gia động vật học."
        result = builder.build_transform_prompt("arch", "orig", "facebook", gem_instructions=custom)
        assert custom in result

    def test_unknown_variant_returns_none(self, builder):
        result = builder.build_transform_prompt("arch", "orig", "tiktok")
        assert result is None

    def test_facebook_includes_original_text(self, builder):
        """Facebook prompt references original EN text for style context."""
        result = builder.build_transform_prompt("archive", "ORIGINAL EN TEXT", "facebook")
        assert "ORIGINAL EN TEXT" in result


# ─────────────────────────────────────────────────────────────────────────────
# build_glossary_extraction_prompt
# ─────────────────────────────────────────────────────────────────────────────

class TestBuildGlossaryExtractionPrompt:

    def test_returns_string(self, builder):
        result = builder.build_glossary_extraction_prompt("Some English text here.")
        assert isinstance(result, str)

    def test_contains_source_text(self, builder):
        text = "The wild boars roam freely."
        result = builder.build_glossary_extraction_prompt(text)
        assert text in result

    def test_default_subject_used(self, builder):
        result = builder.build_glossary_extraction_prompt("text")
        assert "tổng hợp" in result

    def test_custom_subject_injected(self, builder):
        result = builder.build_glossary_extraction_prompt("text", subject="động vật học")
        assert "động vật học" in result

    def test_prompt_asks_for_json_array(self, builder):
        result = builder.build_glossary_extraction_prompt("text")
        assert "JSON" in result

    def test_text_truncated_at_15000_chars(self, builder):
        """Oversized texts must be truncated to prevent oversized API calls."""
        long_text = "word " * 10000  # ~50k chars
        result = builder.build_glossary_extraction_prompt(long_text)
        # The prompt itself must still be finite and reasonable
        # 15000 char limit + some prompt overhead
        assert len(result) < 20000

    def test_prompt_instructs_not_to_extract_common_words(self, builder):
        result = builder.build_glossary_extraction_prompt("text")
        # Should mention filtering out basic words
        assert "water" in result or "KHÔNG trích xuất" in result or "phổ thông" in result


# ─────────────────────────────────────────────────────────────────────────────
# clean_output
# ─────────────────────────────────────────────────────────────────────────────

class TestCleanOutput:

    def test_plain_text_unchanged(self, builder):
        text = "Đây là bản dịch thuần túy."
        assert builder.clean_output(text) == text

    def test_strips_leading_trailing_whitespace(self, builder):
        text = "   Bản dịch.   "
        assert builder.clean_output(text) == "Bản dịch."

    def test_removes_code_fence_markdown(self, builder):
        text = "```\nBản dịch đây.\n```"
        result = builder.clean_output(text)
        assert "```" not in result
        assert "Bản dịch đây." in result

    def test_removes_python_code_fence(self, builder):
        text = "```python\ncode here\n```"
        result = builder.clean_output(text)
        assert "```" not in result

    def test_removes_vietnamese_preamble(self, builder):
        text = "Dưới đây là bản dịch sang tiếng Việt:\n\nNội dung thực."
        result = builder.clean_output(text)
        assert "Dưới đây là" not in result
        assert "Nội dung thực." in result

    def test_removes_bản_dịch_preamble(self, builder):
        text = "Bản dịch:\n\nActual content here."
        result = builder.clean_output(text)
        assert "Actual content here." in result

    def test_removes_note_suffix(self, builder):
        text = "Good translation.\n\nLưu ý: This is a note from the AI."
        result = builder.clean_output(text)
        assert "Lưu ý" not in result
        assert "Good translation." in result

    def test_collapses_excessive_blank_lines(self, builder):
        text = "Line 1\n\n\n\n\nLine 2"
        result = builder.clean_output(text)
        assert "\n\n\n" not in result
        assert "Line 1" in result
        assert "Line 2" in result

    def test_preserves_markdown_formatting(self, builder):
        """Bold, italic, headings etc. must survive cleaning."""
        text = "## Heading\n\n**Bold** and *italic* text."
        result = builder.clean_output(text)
        assert "## Heading" in result
        assert "**Bold**" in result
        assert "*italic*" in result

    def test_preserves_image_placeholders(self, builder):
        """__IMG_NNN__ anchors must never be stripped."""
        text = "Paragraph with __IMG_000__ placeholder inside."
        result = builder.clean_output(text)
        assert "__IMG_000__" in result

    def test_empty_string_returns_empty(self, builder):
        assert builder.clean_output("") == ""

    def test_only_whitespace_returns_empty(self, builder):
        result = builder.clean_output("   \n  \n  ")
        assert result.strip() == ""

    def test_here_is_english_preamble_removed(self, builder):
        text = "Here is the translation:\n\nActual text."
        result = builder.clean_output(text)
        assert "Here is the translation" not in result
        assert "Actual text." in result
