# file-path: src/extract_app/core/epub_parsers/anchor_based_parser.py
# version: 2.1 (Robust Content Slicing)
# last-updated: 2025-09-27
# description: Implements a more robust content slicing method that is independent of HTML nesting structure, fixing the "0 words, 0 images" bug.

"""
Parser for EPUB files with a complex, nested, anchor-based ToC structure.
"""
from pathlib import Path
from typing import Any, Dict, List

from bs4 import BeautifulSoup, Tag
from ebooklib import epub

# Import shared helper functions
from . import utils


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
    """Recursively builds the content tree from the ToC using a robust slicing method."""
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
                    # --- ROBUST SLICING LOGIC ---
                    all_tags_in_doc = start_node.find_all_next(True)
                    content_slice = []
                    for tag in all_tags_in_doc:
                        # Stop if we hit any tag that is another anchor in the ToC
                        if tag.get('id') in all_anchor_ids:
                            break
                        content_slice.append(tag)

                    # Include the starting node itself in the content
                    if start_node.name not in ['body']:
                         content_slice.insert(0, start_node)

                    content = utils.extract_content_from_tags(
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
    """
    all_anchor_ids = _get_all_anchor_ids(book.toc)
    content_tree = _build_tree(book.toc, book, temp_image_dir, all_anchor_ids)
    return content_tree