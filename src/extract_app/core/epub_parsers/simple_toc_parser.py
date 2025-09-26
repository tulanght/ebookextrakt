# file-path: src/extract_app/core/epub_parsers/simple_toc_parser.py
# version: 13.1 (Pylint Compliance)
# last-updated: 2025-09-26
# description: Fixes critical Pylint errors (E1136) and refactors for compliance.

"""
Parser for EPUB files with a simple, flat Table of Contents structure.

This module uses a data-driven heuristic to intelligently decide whether to
split a chapter into multiple articles or treat it as a single content block.
It can build a hierarchical tree (Chapter -> Sub-Chapter -> Article) if
the structure is detected within the content.
"""

import os
from pathlib import Path
from collections import Counter
from typing import List, Dict, Any, Tuple
from ebooklib import epub
from bs4 import BeautifulSoup, Tag

# --- CONFIGURATION ---
# A chapter containing more than 15 sub-headings is a strong indicator
# that it's a "container chapter" that needs to be split.
HEADING_SPLIT_THRESHOLD = 15

# --- HELPER FUNCTIONS ---
def _save_image_to_temp(image_item, temp_image_dir: Path, prefix="epub_") -> str:
    # ... (Nội dung hàm này không thay đổi)
    image_bytes = image_item.get_content()
    image_filename = f"{prefix}{Path(image_item.get_name()).name}"
    image_path = temp_image_dir / image_filename
    with open(image_path, "wb") as f:
        f.write(image_bytes)
    return str(image_path)

def _resolve_image_path(src: str, doc_item: epub.EpubHtml, book: epub.EpubBook):
    # ... (Nội dung hàm này không thay đổi)
    if not src:
        return None
    current_dir = Path(doc_item.get_name()).parent
    resolved_path_str = os.path.normpath(os.path.join(current_dir, src)).replace('\\', '/')
    return book.get_item_with_href(resolved_path_str)

def _extract_content_from_tags(
    tags: List[Tag], book: epub.EpubBook, doc_item: epub.EpubHtml, temp_image_dir: Path
) -> List:
    # ... (Nội dung hàm này không thay đổi)
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
                image_item = _resolve_image_path(img_tag.get('src'), doc_item, book)
                if image_item:
                    anchor = _save_image_to_temp(image_item, temp_image_dir)
                    caption_tag = (img_tag.find_parent('figure').find('figcaption')
                                 if img_tag.find_parent('figure') else None)
                    caption = caption_tag.get_text(strip=True) if caption_tag else ""
                    content_list.append(('image', {'anchor': anchor, 'caption': caption}))
            img_tag.decompose()
        text = temp_tag.get_text(strip=True)
        if text:
            content_list.append(('text', text))
    return content_list

def _has_meaningful_content_between(start_tag: Tag, end_tag: Tag, separator_tag_name: str) -> bool:
    # ... (Nội dung hàm này không thay đổi)
    for sibling in start_tag.find_next_siblings():
        if sibling == end_tag:
            break
        if not isinstance(sibling, Tag):
            continue
        if sibling.name != separator_tag_name and (sibling.get_text(strip=True) or sibling.find('img')):
            return True
    return False

# --- CORE LOGIC ---
# pylint: disable=too-many-locals, too-many-branches
def _process_chapter(
    soup_body: Tag, book: epub.EpubBook, doc_item: epub.EpubHtml, temp_image_dir: Path
) -> Tuple[List, List]:
    # ... (Phần heuristic không thay đổi)
    potential_separator_levels = ['h2', 'h3', 'h4', 'h5', 'h6']
    all_headings = soup_body.find_all(potential_separator_levels)
    if not all_headings:
        return _extract_content_from_tags(soup_body.find_all(True), book, doc_item, temp_image_dir), []
    heading_counts = Counter(h.name for h in all_headings)
    separator_tag = None
    for tag_level in potential_separator_levels:
        if heading_counts.get(tag_level, 0) > 1:
            separator_tag = tag_level
            break
    should_split = separator_tag and heading_counts.get(separator_tag, 0) > HEADING_SPLIT_THRESHOLD
    if not should_split:
        return _extract_content_from_tags(soup_body.find_all(True), book, doc_item, temp_image_dir), []

    # --- THUẬT TOÁN XÂY DỰNG CÂY ---
    children_nodes = []
    separators = soup_body.find_all(separator_tag)
    current_sub_chapter_node = None

    intro_tags = list(separators[0].find_previous_siblings())
    intro_tags.reverse()
    if intro_tags:
        intro_content = _extract_content_from_tags(intro_tags, book, doc_item, temp_image_dir)
        if intro_content:
            children_nodes.append({'title': 'Phần mở đầu', 'content': intro_content, 'children': []})

    for i, separator in enumerate(separators):
        next_separator = separators[i+1] if i + 1 < len(separators) else None
        is_sub_chapter_heading = not _has_meaningful_content_between(separator, next_separator, separator_tag)

        if is_sub_chapter_heading:
            current_sub_chapter_node = {
                'title': separator.get_text(strip=True), 'content': [], 'children': []
            }
            children_nodes.append(current_sub_chapter_node)
        else:
            article_title = separator.get_text(strip=True)
            content_tags = [separator]
            for sibling in separator.find_next_siblings():
                if sibling == next_separator:
                    break
                content_tags.append(sibling)
            article_content = _extract_content_from_tags(content_tags, book, doc_item, temp_image_dir)
            article_node = {'title': article_title, 'content': article_content, 'children': []}

            # *** FIX LỖI E1136 TẠI ĐÂY ***
            # Đảm bảo current_sub_chapter_node là một dictionary trước khi truy cập
            if isinstance(current_sub_chapter_node, dict):
                current_sub_chapter_node['children'].append(article_node)
            else:
                children_nodes.append(article_node)
    return [], children_nodes

def parse(book: epub.EpubBook, temp_image_dir: Path) -> List[Dict[str, Any]]:
    """Parse an EPUB book with a simple ToC into a structured tree."""
    # ... (Nội dung hàm này không thay đổi)
    content_tree = []
    for link in book.toc:
        if any(keyword in link.title.lower() for keyword in ['cover', 'title', 'copyright', 'dedication', 'contents']):
            continue
        file_href = link.href.split('#')[0]
        doc_item = book.get_item_with_href(file_href)
        if not (doc_item and doc_item.media_type == 'application/xhtml+xml'):
            continue
        soup = BeautifulSoup(doc_item.get_content(), 'xml')
        if not soup.body:
            continue
        content, children = _process_chapter(soup.body, book, doc_item, temp_image_dir)
        node = {'title': link.title, 'content': content, 'children': children}
        if node['content'] or node['children']:
            content_tree.append(node)
    return content_tree