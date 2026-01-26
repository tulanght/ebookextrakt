# file-path: src/extract_app/core/epub_parsers/simple_toc_parser.py
# version: 17.0 (Refactored with Utils)
# last-updated: 2025-09-28
# description: Refactored to use shared helper functions from utils.py.

"""
Parser for EPUB files with a simple, flat Table of Contents structure.
"""

from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Tuple

from bs4 import BeautifulSoup, Tag
from ebooklib import epub

# Import shared helper functions
# Import shared helper functions
from . import utils
from ...shared import debug_logger
from ..content_structurer import SmartSplitter





# pylint: disable=too-many-locals, too-many-branches
def _process_chapter(
    soup_body: Tag, book: epub.EpubBook, doc_item: epub.EpubHtml, temp_image_dir: Path
) -> Tuple[List, List]:
    """
    Processes a single chapter using SmartSplitter to divide it into sections.
    """
    # 1. Split into sections based on headers
    sections = SmartSplitter.split_soup_to_sections(soup_body)
    
    # 2. Logic to determine if we have a "Main Content" (no subtitle) or just subsections
    processed_content = []
    processed_children = []
    
    for section in sections:
        subtitle = section.get('subtitle', 'Nội dung')
        tags = section.get('tags', [])
        
        # Extract content using the Utils (handles images, saving, cleaning)
        extracted_data = utils.extract_content_from_tags(tags, book, doc_item, temp_image_dir)
        
        if not extracted_data:
            continue
            
        # Heuristic: If subtitle is "Nội dung" or empty, treat as specific parent content?
        # SmartSplitter defaults to "Nội dung".
        # If it's the ONLY section and title is "Nội dung", it's the main content.
        if len(sections) == 1 and subtitle == "Nội dung":
            processed_content.extend(extracted_data)
        else:
            # It's a subsection/subchapter
            processed_children.append({
                'title': subtitle,
                'content': extracted_data,
                'children': []
            })
            
    return processed_content, processed_children


def parse(book: epub.EpubBook, temp_image_dir: Path) -> List[Dict[str, Any]]:
    """Parses an EPUB book with a simple ToC into a structured tree."""
    tree = []
    for link in book.toc:
        debug_logger.log(f"SimpleParser: Đang kiểm tra link '{link.title}'")
        if any(kw in link.title.lower() for kw in
               ['cover', 'title', 'copyright', 'dedication', 'contents']):
            continue
        href = link.href.split('#')[0]
        doc_item = book.get_item_with_href(href)
        if not (doc_item and doc_item.media_type == 'application/xhtml+xml'):
            continue
        soup = BeautifulSoup(doc_item.get_content(), 'xml')
        if not soup.body:
            continue
        content, children = _process_chapter(
            soup.body, book, doc_item, temp_image_dir)
        debug_logger.log(f"  -> Đã extract: {len(content)} bài viết con, {len(children)} chương con.")
        node = {'title': link.title,
                'content': content, 'children': children}
        if node['content'] or node['children']:
            tree.append(node)
    return tree