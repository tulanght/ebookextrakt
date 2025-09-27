# file-path: src/extract_app/core/epub_parsers/simple_toc_parser.py
# version: 13.2 (Pylint E1136 Final Fix)
# last-updated: 2025-09-27
# description: Refactors the tree-building logic to be clearer for the Pylint static analyzer, definitively fixing E1136.

"""
Parser for EPUB files with a simple, flat Table of Contents structure.

This module uses a data-driven heuristic to intelligently decide whether to
split a chapter into multiple articles or treat it as a single content block.
It can build a hierarchical tree (Chapter -> Sub-Chapter -> Article) if
the structure is detected within the content.
"""

import os
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Tuple

from bs4 import BeautifulSoup, Tag
from ebooklib import epub

# --- CONFIGURATION ---
# A chapter containing more than 15 sub-headings is a strong indicator
# that it's a "container chapter" that needs to be split.
HEADING_SPLIT_THRESHOLD = 15


# --- HELPER FUNCTIONS (Stable) ---
def _save_image_to_temp(image_item, temp_image_dir: Path, prefix="epub_") -> str:
    """Saves an image item to a temporary directory and returns its path."""
    image_bytes = image_item.get_content()
    image_filename = f"{prefix}{Path(image_item.get_name()).name}"
    image_path = temp_image_dir / image_filename
    with open(image_path, "wb") as f:
        f.write(image_bytes)
    return str(image_path)


def _resolve_image_path(src: str, doc_item: epub.EpubHtml, book: epub.EpubBook):
    """Resolves the absolute path of an image given its relative src."""
    if not src:
        return None
    current_dir = Path(doc_item.get_name()).parent
    resolved_path_str = os.path.normpath(
        os.path.join(current_dir, src)).replace('\\', '/')
    return book.get_item_with_href(resolved_path_str)


def _extract_content_from_tags(
    tags: List[Tag], book: epub.EpubBook, doc_item: epub.EpubHtml, temp_image_dir: Path
) -> List:
    """Extracts text and image data from a list of BeautifulSoup tags."""
    content_list = []
    for element in tags:
        if not isinstance(element, Tag):
            continue
        temp_soup = BeautifulSoup(str(element), 'xml')
        temp_tag = temp_soup.find(element.name)
        if not temp_tag:
            continue
        for img_tag in temp_tag.find_all('img'):
            if img_tag.get('src'):
                image_item = _resolve_image_path(
                    img_tag.get('src'), doc_item, book)
                if image_item:
                    anchor = _save_image_to_temp(
                        image_item, temp_image_dir)
                    caption_tag = (img_tag.find_parent('figure').find('figcaption')
                                 if img_tag.find_parent('figure') else None)
                    caption = caption_tag.get_text(
                        strip=True) if caption_tag else ""
                    content_list.append(
                        ('image', {'anchor': anchor, 'caption': caption}))
            img_tag.decompose()
        text = temp_tag.get_text(strip=True)
        if text:
            content_list.append(('text', text))
    return content_list


def _has_meaningful_content_between(
    start_tag: Tag, end_tag: Tag | None, separator_tag_name: str
) -> bool:
    """Checks for real content (text or images) between two tags."""
    for sibling in start_tag.find_next_siblings():
        if sibling == end_tag:
            break
        if not isinstance(sibling, Tag):
            continue
        if sibling.name != separator_tag_name and \
           (sibling.get_text(strip=True) or sibling.find('img')):
            return True
    return False


# --- CORE LOGIC ---
# pylint: disable=too-many-locals, too-many-branches
def _process_chapter(
    soup_body: Tag, book: epub.EpubBook, doc_item: epub.EpubHtml, temp_image_dir: Path
) -> Tuple[List, List]:
    """
    Processes a single chapter, splitting it into a hierarchical structure
    if necessary, based on heading analysis.
    """
    potential_levels = ['h2', 'h3', 'h4', 'h5', 'h6']
    all_headings = soup_body.find_all(potential_levels)

    if not all_headings:
        return _extract_content_from_tags(
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
        return _extract_content_from_tags(
            soup_body.find_all(True), book, doc_item, temp_image_dir
        ), []

    # --- HIERARCHICAL TREE BUILDER ---
    children = []
    separators = soup_body.find_all(separator_tag)
    sub_chapter_node = None

    if separators:
        intro_tags = list(separators[0].find_previous_siblings())
        intro_tags.reverse()
        if intro_tags:
            intro_content = _extract_content_from_tags(
                intro_tags, book, doc_item, temp_image_dir)
            if intro_content:
                children.append(
                    {'title': 'Phần mở đầu', 'content': intro_content, 'children': []})


    for i, separator in enumerate(separators):
        next_separator = separators[i+1] if i + 1 < len(separators) else None
        is_sub_chapter = not _has_meaningful_content_between(
            separator, next_separator, separator_tag)

        if is_sub_chapter:
            sub_chapter_node = {
                'title': separator.get_text(strip=True), 'content': [], 'children': []
            }
            children.append(sub_chapter_node)
        else:
            title = separator.get_text(strip=True)
            tags = [separator]
            for sibling in separator.find_next_siblings():
                if sibling == next_separator:
                    break
                tags.append(sibling)

            content = _extract_content_from_tags(
                tags, book, doc_item, temp_image_dir)
            article = {'title': title, 'content': content, 'children': []}

            # *** REFACTORED LOGIC TO FIX E1136 ***
            # Explicitly determine where to append the article.
            # This is clearer for the static analyzer.
            if isinstance(sub_chapter_node, dict):
                # Append to the current sub-chapter's children list
                sub_chapter_node['children'].append(article)
            else:
                # Append directly to the main chapter's children list

                children.append(article)
    return [], children


def parse(book: epub.EpubBook, temp_image_dir: Path) -> List[Dict[str, Any]]:
    """Parses an EPUB book with a simple ToC into a structured tree."""
    tree = []
    for link in book.toc:
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
        node = {'title': link.title,
                'content': content, 'children': children}
        if node['content'] or node['children']:
            tree.append(node)
    return tree