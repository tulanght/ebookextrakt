# file-path: src/extract_app/core/epub_parsers/anchor_based_parser.py
# version: 3.0 (Refactored with Utils)
# last-updated: 2025-09-28
# description: Refactored to use shared helper functions from utils.py.

"""
Parser for EPUB files with a complex, nested, anchor-based ToC structure.
"""
from pathlib import Path
from typing import Any, Dict, List

from bs4 import BeautifulSoup, Tag
from ebooklib import epub

# Import shared helper functions
from . import utils
from ...shared import debug_logger


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
        # Determine link and children
        link = None
        children = []
        
        if isinstance(item, epub.Link):
            link = item
        elif isinstance(item, (list, tuple)):
            link = item[0]
            children = item[1]
            
        if link:
            title = link.title if hasattr(link, 'title') else "Unknown"
            debug_logger.log(f"AnchorParser: Đang xử lý node '{title}'")
            
            # --- Extraction Logic (Refactored) ---
            href_parts = link.href.split('#')
            file_href = href_parts[0]
            anchor_id = href_parts[1] if len(href_parts) > 1 else None
            
            doc_item = book.get_item_with_href(file_href)
            content = []
            
            if doc_item:
                try:
                    soup = BeautifulSoup(doc_item.get_content(), 'xml')
                    start_node = soup.find(id=anchor_id) if anchor_id else soup.body
                    
                    if start_node:
                        content_slice = []
                        if start_node.name == 'body':
                            debug_logger.log(f"  [DEBUG] Found body start_node for {file_href}")
                            # Case 1: Whole file
                            for child in start_node.find_all(recursive=False):
                                if isinstance(child, Tag):
                                    content_slice.append(child)
                        else:
                            # Case 2: Anchor based
                            debug_logger.log(f"  [DEBUG] Found anchor start_node: {start_node.name}#{anchor_id}")
                            
                            content_slice.append(start_node)
                            
                            # "Climb and Collect" Strategy:
                            # 1. Get siblings of current node.
                            # 2. Move to parent.
                            # 3. Get siblings of parent (which represent content AFTER the parent container).
                            # 4. Repeat until body.
                            
                            curr_element = start_node
                            full_stop = False
                            
                            while curr_element:
                                for sibling in curr_element.find_next_siblings():
                                    if isinstance(sibling, Tag):
                                         # Check if this sibling is a start of another section
                                         if sibling.get('id') in all_anchor_ids:
                                              debug_logger.log(f"  [DEBUG] Stopping at sibling anchor: {sibling.get('id')}")
                                              full_stop = True
                                              break
                                         
                                         # Also checking for nested anchors inside the sibling is expensive/complex.
                                         # Usually the top-level container has the ID. 
                                         # If we need deeper check: sibling.find(id=...) -> if found in all_anchor_ids: stop?
                                         # For now, trust top-level ID or explicit anchor tags.
                                    
                                    content_slice.append(sibling)
                                
                                if full_stop:
                                    break
                                
                                curr_element = curr_element.parent
                                if not curr_element or curr_element.name == 'body':
                                    break

                        debug_logger.log(f"  [DEBUG] Collected {len(content_slice)} tags.")
                        content = utils.extract_content_from_tags(
                            content_slice, book, doc_item, temp_image_dir
                        )
                        debug_logger.log(f"  [DEBUG] Extracted content items: {len(content)}")
                    else:
                        debug_logger.log(f"  [WARNING] start_node not found for id={anchor_id} in {file_href}")

                except Exception as e:
                    debug_logger.log(f"Error parsing content for '{title}': {e}")

            # --- Recurse for children ---
            children_nodes = _build_tree(children, book, temp_image_dir, all_anchor_ids)
            
            node = {
                'title': title,
                'content': content,
                'children': children_nodes
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