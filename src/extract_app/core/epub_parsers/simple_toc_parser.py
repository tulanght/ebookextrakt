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
from . import utils
from ...shared import debug_logger

# --- CONFIGURATION ---
HEADING_SPLIT_THRESHOLD = 15

# --- HELPER FUNCTION (Specific to this module) ---
def _has_meaningful_content_between(
    start_tag: Tag, end_tag: Tag | None
) -> bool:
    """Checks for real content (text or images) between two tags."""
    for sibling in start_tag.find_next_siblings():
        if sibling == end_tag:
            break
        # Ignore NavigableString objects that are just whitespace
        if not isinstance(sibling, Tag):
            if isinstance(sibling, str) and sibling.strip():
                return True
            continue
        # If we find any tag that is not just a container, it's meaningful
        if sibling.get_text(strip=True) or sibling.find('img'):
            return True
    return False


# --- CORE LOGIC ---
# pylint: disable=too-many-locals, too-many-branches
def _process_chapter(
    soup_body: Tag, book: epub.EpubBook, doc_item: epub.EpubHtml, temp_image_dir: Path
) -> Tuple[List, List]:
    """
    Processes a single chapter using the definitive Anchor & Siblings algorithm.
    """
    potential_levels = ['h2', 'h3', 'h4', 'h5', 'h6']
    all_headings = soup_body.find_all(potential_levels)

    if not all_headings:
        return utils.extract_content_from_tags(
            soup_body.find_all(True), book, doc_item, temp_image_dir
        ), []

    counts = Counter(h.name for h in all_headings)
    separator_tag = None
    for tag_level in potential_levels:
        if counts.get(tag_level, 0) > 1:
            separator_tag = tag_level
            break

    should_split = separator_tag and counts.get(
        separator_tag, 0) > HEADING_SPLIT_THRESHOLD
    if not should_split:
        return utils.extract_content_from_tags(
            soup_body.find_all(True), book, doc_item, temp_image_dir
        ), []

    # --- HIERARCHICAL TREE BUILDER ---
    final_nodes = []
    separators = soup_body.find_all(separator_tag)

    if separators:
        intro_tags = list(separators[0].find_previous_siblings())
        intro_tags.reverse()
        if intro_tags:
            intro_content = utils.extract_content_from_tags(
                intro_tags, book, doc_item, temp_image_dir)
            if intro_content:
                final_nodes.append(
                    {'title': 'Phần mở đầu', 'content': intro_content, 'children': []})

    current_sub_chapter_node = None
    for i, separator in enumerate(separators):
        next_separator = separators[i+1] if i + 1 < len(separators) else None
        is_sub_chapter_heading = not _has_meaningful_content_between(
            separator, next_separator)

        if is_sub_chapter_heading:
            sub_chapter_node = {
                'title': separator.get_text(strip=True), 'content': [], 'children': []
            }
            final_nodes.append(sub_chapter_node)
            current_sub_chapter_node = sub_chapter_node
        else:
            title = separator.get_text(strip=True)
            tags = [separator]
            for sibling in separator.find_next_siblings():
                if sibling == next_separator:
                    break
                tags.append(sibling)
            content = utils.extract_content_from_tags(
                tags, book, doc_item, temp_image_dir)
            article_node = {'title': title, 'content': content, 'children': []}

            if current_sub_chapter_node is not None:
                current_sub_chapter_node['children'].append(article_node)
            else:
                final_nodes.append(article_node)

    return [], final_nodes


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