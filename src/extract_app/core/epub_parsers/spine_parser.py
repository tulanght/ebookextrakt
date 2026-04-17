# --------------------------------------------------------------------------------
# Project: ExtractPDF-EPUB
# File: src/extract_app/core/epub_parsers/spine_parser.py
# Version: 1.0.0
# Author: Antigravity
# Description: Fallback parser for EPUB files with broken or empty Table of
#              Contents. Reads chapters directly from the OPF spine in order,
#              skipping boilerplate pages (cover, toc, copyright, etc.).
# --------------------------------------------------------------------------------

"""
Spine-based fallback parser for EPUB files with broken/empty ToC.

When the NCX/NAV Table of Contents is structurally broken (e.g. a single empty
Link with href=''), this parser falls back to reading the OPF spine — the
ordered list of all content documents as declared by the publisher.

This guarantees content extraction even when the ToC is unusable.
"""

from pathlib import Path
from typing import Any, Dict, List

from bs4 import BeautifulSoup
from ebooklib import epub, ITEM_DOCUMENT

from . import utils
from ...shared import debug_logger


# Boilerplate page names to skip (case-insensitive substring match)
_SKIP_TITLES = {
    'cover', 'title', 'copyright', 'dedication', 'toc', 'contents',
    'half', 'halftitle', 'colophon', 'nav', 'index',
}

# Boilerplate href patterns to skip (case-insensitive)
_SKIP_HREFS = {
    'cover', 'title', 'copyright', 'dedication', 'half',
    'nav', 'toc', 'contents', 'colophon',
}


def _is_boilerplate(href: str, body_text: str) -> bool:
    """Heuristic to detect non-content pages.

    Args:
        href: The document href/filename.
        body_text: Extracted plain text from the document body.

    Returns:
        True if the page should be skipped.
    """
    name = Path(href).stem.lower()
    # Skip by filename pattern
    if any(skip in name for skip in _SKIP_HREFS):
        return True
    # Skip if body is very short (< 80 chars) — likely a wrapper page
    if len(body_text.strip()) < 80:
        return True
    return False


def parse(book: epub.EpubBook, temp_image_dir: Path) -> List[Dict[str, Any]]:
    """Parse an EPUB by reading its OPF spine in order.

    Used as a fallback when the ToC (NCX/NAV) is empty or broken.

    Args:
        book: The parsed EpubBook object.
        temp_image_dir: Directory to save extracted images.

    Returns:
        List of chapter dicts with keys: title, content, children.
    """
    tree: List[Dict[str, Any]] = []

    # book.spine is a list of (item_id, linear) tuples
    spine_ids = [item_id for item_id, linear in book.spine]
    debug_logger.log(f"SpineParser: {len(spine_ids)} spine items found.")

    for item_id in spine_ids:
        doc_item = book.get_item_with_id(item_id)
        if doc_item is None:
            debug_logger.log(f"  [SKIP] No item found for id={item_id!r}")
            continue

        href = doc_item.get_name()
        media_type = getattr(doc_item, 'media_type', '')
        if 'xhtml' not in media_type and 'html' not in media_type:
            debug_logger.log(f"  [SKIP] Non-HTML item: {href!r} ({media_type})")
            continue

        try:
            soup = BeautifulSoup(doc_item.get_content(), 'html.parser')
            body = soup.find('body')
            if not body:
                debug_logger.log(f"  [SKIP] No body tag in {href!r}")
                continue

            body_text = body.get_text(strip=True)
            if _is_boilerplate(href, body_text):
                debug_logger.log(f"  [SKIP] Boilerplate: {href!r}")
                continue

            # Derive chapter title from <h1>/<h2> or filename
            title_tag = body.find(['h1', 'h2', 'h3'])
            if title_tag:
                chapter_title = title_tag.get_text(strip=True)
            else:
                chapter_title = Path(href).stem.replace('-', ' ').replace('_', ' ').title()

            debug_logger.log(f"  [OK] Spine item: {href!r} -> title={chapter_title!r}")

            # Extract all body children
            tags = [child for child in body.find_all(recursive=False)]
            content = utils.extract_content_from_tags(tags, book, doc_item, temp_image_dir)

            if content:
                tree.append({
                    'title': chapter_title,
                    'content': content,
                    'children': [],
                })
            else:
                debug_logger.log(f"  [WARN] No content extracted from {href!r}")

        except Exception as e:  # pylint: disable=broad-except
            debug_logger.log(f"  [ERROR] spine item {href!r}: {e}")
            continue

    debug_logger.log(f"SpineParser: {len(tree)} chapters extracted from spine.")
    return tree
