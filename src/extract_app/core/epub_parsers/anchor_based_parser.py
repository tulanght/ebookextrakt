# file-path: src/extract_app/core/epub_parsers/anchor_based_parser.py
# version: 1.1 (Pylint Compliance)
# last-updated: 2025-09-27
# description: Cleans up the anchor-based parser module to meet Pylint standards.

"""
Parser for EPUB files with a complex, nested, anchor-based ToC structure.

This module is designed to handle Ebooks where the Table of Contents (ToC)
uses hrefs with anchors (e.g., 'chapter1.xhtml#section2') to define a deep,
hierarchical structure.
"""

import os
from pathlib import Path
from typing import Any, Dict, List
from bs4 import BeautifulSoup, Tag
from ebooklib import epub

# --- HELPER FUNCTIONS ---
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


def _extract_content_from_tag_list(
    tags: List[Tag], book: epub.EpubBook, doc_item: epub.EpubHtml, temp_image_dir: Path
) -> List:
    """Extracts text and image data from a list of BeautifulSoup tags."""
    content_list = []
    for element in tags:
        if not isinstance(element, Tag):
            continue
        for img_tag in element.find_all('img'):
            if img_tag.get('src'):
                image_item = _resolve_image_path(
                    img_tag.get('src'), doc_item, book)
                if image_item:
                    anchor = _save_image_to_temp(image_item, temp_image_dir)
                    caption_tag = (img_tag.find_parent('figure').find('figcaption')
                                 if img_tag.find_parent('figure') else None)

                    caption = caption_tag.get_text(
                        strip=True) if caption_tag else ""
                    content_list.append(
                        ('image', {'anchor': anchor, 'caption': caption}))
        # Extract text only if the element itself is not a figure or image container
        if element.name not in ['figure', 'img']:
            text = element.get_text(strip=True)
            if text:
                content_list.append(('text', text))
    return content_list


def _get_all_anchor_ids(toc_items: List) -> set:
    """Recursively collects all anchor IDs from the ToC."""
    anchor_ids = set()
    for item in toc_items:
        if isinstance(item, epub.Link):
            if '#' in item.href:
                anchor_ids.add(item.href.split('#')[1])
        elif isinstance(item, (list, tuple)):
            anchor_ids.update(_get_all_anchor_ids(item[1]))
    return anchor_ids



# pylint: disable=too-many-locals
def _build_tree(
    toc_items: list, book: epub.EpubBook, temp_image_dir: Path, all_anchor_ids: set
) -> List[Dict[str, Any]]:
    """Recursively builds the content tree from the ToC."""
    tree = []
    for item in toc_items:
        if isinstance(item, epub.Link):
            href_parts = item.href.split('#')
            file_href = href_parts[0]
            anchor_id = href_parts[1] if len(href_parts) > 1 else None
            doc_item = book.get_item_with_href(file_href)
            content = []
            if doc_item:
                soup = BeautifulSoup(doc_item.get_content(), 'xml')
                start_node = soup.find(id=anchor_id) if anchor_id else soup.body
                if start_node:
                    content_slice = []
                    # Collect all sibling tags until the next anchor is found
                    for sibling in start_node.find_next_siblings():
                        if isinstance(sibling, Tag) and sibling.get('id') in all_anchor_ids:
                            break
                        content_slice.append(sibling)
                    # Include the starting node itself if it's not the body
                    if start_node.name not in ['body']:
                        content_slice.insert(0, start_node)
                    content = _extract_content_from_tag_list(
                        content_slice, book, doc_item, temp_image_dir
                    )
            node = {'title': item.title, 'content': content, 'children': []}
            tree.append(node)
        elif isinstance(item, (list, tuple)):
            # Handle nested ToC sections
            section_link, children_items = item[0], item[1]
            node = {
                'title': section_link.title,
                'content': [],
                'children': _build_tree(children_items, book, temp_image_dir, all_anchor_ids)
            }
            tree.append(node)
    return tree


def parse(book: epub.EpubBook, temp_image_dir: Path) -> List[Dict[str, Any]]:
    """
    Public function to parse an EPUB with a complex, anchor-based ToC.

    Args:
        book: The ebooklib EpubBook object.
        temp_image_dir: The path to the temporary directory for storing images.

    Returns:
        A list of dictionaries representing the structured content tree.
    """
    all_anchor_ids = _get_all_anchor_ids(book.toc)
    content_tree = _build_tree(book.toc, book, temp_image_dir, all_anchor_ids)
    return content_tree