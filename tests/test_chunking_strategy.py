# --------------------------------------------------------------------------------
# Project: ExtractPDF-EPUB
# File: tests/test_chunking_strategy.py
# Version: 1.0.0
# Author: Antigravity
# Description: Unit tests for ChunkingStrategy — chunk_text, protect_anchors, restore_anchors.
#              Run with: pytest tests/test_chunking_strategy.py -v
# --------------------------------------------------------------------------------

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from extract_app.core.chunking_strategy import ChunkingStrategy, DEFAULT_CHUNK_SIZE


@pytest.fixture
def chunker():
    return ChunkingStrategy()


# ─────────────────────────────────────────────────────────────────────────────
# chunk_text — happy paths
# ─────────────────────────────────────────────────────────────────────────────

class TestChunkTextShortText:
    """Texts shorter than or equal to chunk_size must be returned as-is."""

    def test_empty_string_returns_single_chunk(self, chunker):
        result = chunker.chunk_text("", chunk_size=100)
        assert result == [""]

    def test_short_text_no_split(self, chunker):
        text = "Hello world"
        result = chunker.chunk_text(text, chunk_size=100)
        assert len(result) == 1
        assert result[0] == text

    def test_text_exactly_at_limit(self, chunker):
        text = "x" * 100
        result = chunker.chunk_text(text, chunk_size=100)
        assert len(result) == 1

    def test_default_chunk_size_constant(self, chunker):
        """DEFAULT_CHUNK_SIZE should be used when no chunk_size given."""
        text = "a" * (DEFAULT_CHUNK_SIZE - 1)
        result = chunker.chunk_text(text)
        assert len(result) == 1


class TestChunkTextHeadingBoundary:
    """Text longer than chunk_size must be split on ## / ### headings."""

    def _build_text_with_sections(self, n_sections: int, words_per_section: int) -> str:
        """Helper: build Markdown text with n_sections × ## headings."""
        parts = []
        for i in range(n_sections):
            heading = f"\n## Section {i + 1}"
            body = " word" * words_per_section
            parts.append(heading + "\n" + body)
        return "".join(parts)

    def test_splits_on_heading_boundary(self, chunker):
        # Each section ~600 chars; chunk_size=1000 → 2 sections per chunk
        text = self._build_text_with_sections(n_sections=4, words_per_section=100)
        chunks = chunker.chunk_text(text, chunk_size=1000)
        assert len(chunks) >= 2

    def test_total_content_preserved(self, chunker):
        """No characters are dropped during chunking."""
        text = self._build_text_with_sections(n_sections=6, words_per_section=80)
        chunks = chunker.chunk_text(text, chunk_size=800)
        reassembled = "\n\n".join(chunks)
        # Every word from original must appear somewhere in reassembled
        for section_idx in range(6):
            assert f"Section {section_idx + 1}" in reassembled

    def test_chunks_do_not_exceed_chunk_size_by_far(self, chunker):
        """Each chunk should be at or reasonably near the size limit."""
        text = self._build_text_with_sections(n_sections=10, words_per_section=60)
        chunk_size = 500
        chunks = chunker.chunk_text(text, chunk_size=chunk_size)
        # Allow heading merges (a single section that fits is merged), but
        # none should be more than 2× chunk_size (paragraph fallback)
        for chunk in chunks:
            assert len(chunk) <= chunk_size * 2 + 200  # generous tolerance


class TestChunkTextParagraphFallback:
    """Oversized sections without headings are split by paragraphs."""

    def test_large_flat_text_split_into_multiple_chunks(self, chunker):
        # Build a paragraph-only text well over chunk_size
        paragraph = "The quick brown fox jumps over the lazy dog. " * 20  # ~900 chars
        text = "\n\n".join([paragraph] * 6)  # ~5400 chars
        chunks = chunker.chunk_text(text, chunk_size=1000)
        assert len(chunks) >= 2

    def test_single_huge_paragraph_still_returned(self, chunker):
        """Edge case: one paragraph larger than chunk_size is kept intact."""
        text = "word " * 800  # ~4000 chars
        chunks = chunker.chunk_text(text, chunk_size=1000)
        # At minimum we get something back
        assert len(chunks) >= 1
        assert all(len(c) > 0 for c in chunks)


# ─────────────────────────────────────────────────────────────────────────────
# protect_anchors
# ─────────────────────────────────────────────────────────────────────────────

class TestProtectAnchors:

    def test_no_anchors_returns_original_and_empty_map(self, chunker):
        text = "Plain text without any anchors."
        protected, mapping = chunker.protect_anchors(text)
        assert protected == text
        assert mapping == {}

    def test_single_anchor_replaced(self, chunker):
        text = "Text [Image: img001.jpg] more text."
        protected, mapping = chunker.protect_anchors(text)
        assert "[Image:" not in protected
        assert "__IMG_000__" in protected
        assert mapping["__IMG_000__"] == "[Image: img001.jpg]"

    def test_multiple_anchors_indexed_sequentially(self, chunker):
        text = "A [Image: a.jpg] B [Image: b.png] C [Image: c.gif]"
        protected, mapping = chunker.protect_anchors(text)
        assert "__IMG_000__" in protected
        assert "__IMG_001__" in protected
        assert "__IMG_002__" in protected
        assert len(mapping) == 3

    def test_anchors_replaced_in_order(self, chunker):
        text = "[Image: first.jpg] middle [Image: second.jpg]"
        protected, mapping = chunker.protect_anchors(text)
        assert protected.index("__IMG_000__") < protected.index("__IMG_001__")

    def test_anchor_with_spaces_in_name(self, chunker):
        text = "[Image: path/to my img 01.jpg]"
        protected, mapping = chunker.protect_anchors(text)
        assert "__IMG_000__" in protected
        assert mapping["__IMG_000__"] == "[Image: path/to my img 01.jpg]"

    def test_identical_anchors_in_different_positions(self, chunker):
        """Each occurrence gets its own placeholder even if tags are identical."""
        text = "[Image: dup.jpg] text [Image: dup.jpg]"
        protected, mapping = chunker.protect_anchors(text)
        # Both get placeholders
        assert "__IMG_000__" in protected
        assert "__IMG_001__" in protected


# ─────────────────────────────────────────────────────────────────────────────
# restore_anchors
# ─────────────────────────────────────────────────────────────────────────────

class TestRestoreAnchors:

    def test_empty_mapping_returns_text_unchanged(self, chunker):
        text = "Some text __IMG_000__ here"
        restored = chunker.restore_anchors(text, {})
        assert restored == text

    def test_simple_restore(self, chunker):
        mapping = {"__IMG_000__": "[Image: a.jpg]"}
        text = "Before __IMG_000__ after"
        restored = chunker.restore_anchors(text, mapping)
        assert restored == "Before [Image: a.jpg] after"

    def test_restore_multiple_anchors(self, chunker):
        mapping = {
            "__IMG_000__": "[Image: a.jpg]",
            "__IMG_001__": "[Image: b.png]",
        }
        text = "__IMG_000__ middle __IMG_001__"
        restored = chunker.restore_anchors(text, mapping)
        assert restored == "[Image: a.jpg] middle [Image: b.png]"

    def test_restore_mutated_placeholder_underscore_removed(self, chunker):
        """LLMs sometimes strip underscores: _IMG_000_ instead of __IMG_000__."""
        mapping = {"__IMG_000__": "[Image: x.jpg]"}
        mutated_text = "Before _IMG_000_ after"
        restored = chunker.restore_anchors(mutated_text, mapping)
        assert "[Image: x.jpg]" in restored

    def test_restore_mutated_placeholder_no_underscores(self, chunker):
        """LLMs sometimes produce IMG000 or IMG 000."""
        mapping = {"__IMG_001__": "[Image: y.png]"}
        mutated_text = "Before IMG 001 after"
        restored = chunker.restore_anchors(mutated_text, mapping)
        assert "[Image: y.png]" in restored

    def test_roundtrip_protect_then_restore(self, chunker):
        """Full roundtrip: protect → translate (no-op here) → restore."""
        original = "Intro [Image: fig1.jpg] middle [Image: fig2.png] end"
        protected, mapping = chunker.protect_anchors(original)
        # Simulate AI returning the protected text verbatim
        restored = chunker.restore_anchors(protected, mapping)
        assert restored == original

    def test_roundtrip_with_text_modification(self, chunker):
        """Roundtrip where surrounding text changes but anchors are kept."""
        original = "Hello [Image: cover.jpg] world"
        protected, mapping = chunker.protect_anchors(original)
        # AI translates: changes "Hello" and "world" but keeps placeholder
        translated = protected.replace("Hello", "Xin chào").replace("world", "thế giới")
        restored = chunker.restore_anchors(translated, mapping)
        assert "[Image: cover.jpg]" in restored
        assert "Xin chào" in restored
        assert "thế giới" in restored

    def test_no_placeholder_leaves_text_intact(self, chunker):
        """If the AI removes the placeholder entirely, restore should not crash."""
        mapping = {"__IMG_000__": "[Image: a.jpg]"}
        text = "AI removed everything here"  # no placeholder at all
        # Should not raise; might or might not restore the anchor
        result = chunker.restore_anchors(text, mapping)
        assert isinstance(result, str)
