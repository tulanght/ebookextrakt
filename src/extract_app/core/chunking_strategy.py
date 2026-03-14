# --------------------------------------------------------------------------------
# Project: ExtractPDF-EPUB
# File: src/extract_app/core/chunking_strategy.py
# Version: 1.0.0
# Author: Antigravity
# Description: Pure text chunking and anchor protection helpers.
#              No external project dependencies — easy to unit test.
# --------------------------------------------------------------------------------

import re
from typing import List, Tuple, Dict


DEFAULT_CHUNK_SIZE = 3000


class ChunkingStrategy:
    """
    Splits long text into translation-friendly chunks and protects/restores
    image anchor tags so the AI cannot mangle them.
    """

    def chunk_text(self, text: str, chunk_size: int = DEFAULT_CHUNK_SIZE) -> List[str]:
        """Split text into chunks, preferring Markdown header boundaries.

        Strategy:
        1. Split by Markdown headings (## or ###) to keep sub-sections intact.
        2. If a sub-section exceeds chunk_size, fallback to paragraph splitting.
        3. Merge small adjacent sections if they fit within chunk_size.
        """
        if len(text) <= chunk_size:
            return [text]

        # Step 1: Split by Markdown headings (## or ###, but not # = article title)
        sections = re.split(r'(?=\n#{2,3} )', text)
        sections = [s.strip() for s in sections if s.strip()]

        # Step 2: Process sections — split oversized ones by paragraphs
        processed_sections = []
        for section in sections:
            if len(section) <= chunk_size:
                processed_sections.append(section)
            else:
                paragraphs = re.split(r'\n\n+', section)
                sub_chunk: List[str] = []
                sub_size = 0
                for para in paragraphs:
                    para = para.strip()
                    if not para:
                        continue
                    if sub_size + len(para) > chunk_size and sub_chunk:
                        processed_sections.append('\n\n'.join(sub_chunk))
                        sub_chunk = [para]
                        sub_size = len(para)
                    else:
                        sub_chunk.append(para)
                        sub_size += len(para)
                if sub_chunk:
                    processed_sections.append('\n\n'.join(sub_chunk))

        # Step 3: Merge small adjacent sections to reduce API calls
        chunks: List[str] = []
        current_chunk: List[str] = []
        current_size = 0

        for section in processed_sections:
            section_size = len(section)
            if current_size + section_size > chunk_size and current_chunk:
                chunks.append('\n\n'.join(current_chunk))
                current_chunk = [section]
                current_size = section_size
            else:
                current_chunk.append(section)
                current_size += section_size

        if current_chunk:
            chunks.append('\n\n'.join(current_chunk))

        return chunks if chunks else [text]

    def protect_anchors(self, text: str) -> Tuple[str, Dict[str, str]]:
        """Replace [Image: ...] tags with safe __IMG_NNN__ placeholders.

        Returns:
            (protected_text, mapping)  where mapping[placeholder] = original_tag
        """
        anchor_pattern = r'\[Image:.*?\]'
        anchors = re.findall(anchor_pattern, text)
        mapping: Dict[str, str] = {}

        protected_text = text
        for i, anchor in enumerate(anchors):
            placeholder = f"__IMG_{i:03d}__"
            mapping[placeholder] = anchor
            protected_text = protected_text.replace(anchor, placeholder, 1)

        return protected_text, mapping

    def restore_anchors(self, text: str, mapping: Dict[str, str]) -> str:
        """Restore __IMG_NNN__ placeholders back to original anchor tags.
        Also handles 'mutated' placeholders produced by some LLMs.
        """
        restored = text
        for placeholder, original in mapping.items():
            if placeholder in restored:
                restored = restored.replace(placeholder, original)
            else:
                # Relaxed regex for LLM mutations like _IMG_001_, IMG_001, etc.
                if placeholder.startswith("__IMG_") and placeholder.endswith("__"):
                    idx = placeholder[6:-2]
                    pattern = r'_*\s*IMG\s*_*\s*' + idx + r'\s*_*'
                    restored = re.sub(pattern, original, restored, flags=re.IGNORECASE)
        return restored
