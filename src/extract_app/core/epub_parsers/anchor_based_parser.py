# file-path: src/extract_app/core/epub_parsers/anchor_based_parser.py
# version: 1.0
# last-updated: 2025-09-26
# description: A dedicated parser for complex, anchor-based, nested ToC structures.

from ebooklib import epub
from bs4 import BeautifulSoup, Tag
from typing import List, Dict, Any
from pathlib import Path
import os
# --- HELPER FUNCTIONS (Copied from main parser for independence) ---

def _save_image_to_temp(image_item, temp_image_dir: Path, prefix="epub_") -> str:
    # ... (Nội dung hàm này giữ nguyên như trong epub_parser.py v65.0)
    image_bytes = image_item.get_content()
    image_filename = f"{prefix}{Path(image_item.get_name()).name}"
    image_path = temp_image_dir / image_filename
    with open(image_path, "wb") as f:
        f.write(image_bytes)
    return str(image_path)

def _resolve_image_path(src: str, doc_item: epub.EpubHtml, book: epub.EpubBook):
    # ... (Nội dung hàm này giữ nguyên như trong epub_parser.py v65.0)
    if not src: return None
    current_dir = Path(doc_item.get_name()).parent
    resolved_path_str = os.path.normpath(os.path.join(current_dir, src)).replace('\\', '/')
    return book.get_item_with_href(resolved_path_str)

def _extract_content_from_tag_list(tags: List[Tag], book: epub.EpubBook, doc_item: epub.EpubHtml, temp_image_dir: Path) -> List:
    # ... (Nội dung hàm này giữ nguyên như trong epub_parser.py v65.0)
    content_list = []
    for element in tags:
        if not isinstance(element, Tag): continue
        for img_tag in element.find_all('img'):
            if img_tag.get('src'):
                image_item = _resolve_image_path(img_tag.get('src'), doc_item, book)
                if image_item:
                    anchor = _save_image_to_temp(image_item, temp_image_dir)
                    caption_tag = img_tag.find_parent('figure').find('figcaption') if img_tag.find_parent('figure') else None
                    caption = caption_tag.get_text(strip=True) if caption_tag else ""
                    content_list.append(('image', {'anchor': anchor, 'caption': caption}))
        if element.name not in ['figure', 'img']:
             text = element.get_text(strip=True)
             if text: content_list.append(('text', text))
    return content_list

def _get_all_anchor_ids(toc_items: List) -> set:
    anchor_ids = set()
    for item in toc_items:
        if isinstance(item, epub.Link):
            if '#' in item.href:
                anchor_ids.add(item.href.split('#')[1])
        elif isinstance(item, (list, tuple)):
            anchor_ids.update(_get_all_anchor_ids(item[1]))
    return anchor_ids

def _build_tree(toc_items: list, book: epub.EpubBook, temp_image_dir: Path, all_anchor_ids: set) -> List[Dict[str, Any]]:
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
                    for sibling in start_node.find_next_siblings():
                        if isinstance(sibling, Tag) and sibling.get('id') in all_anchor_ids:
                            break
                        content_slice.append(sibling)
                    if start_node.name not in ['body']:
                        content_slice.insert(0, start_node)
                    content = _extract_content_from_tag_list(content_slice, book, doc_item, temp_image_dir)
            node = {'title': item.title, 'content': content, 'children': []}
            tree.append(node)
        elif isinstance(item, (list, tuple)):
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
    Hàm công khai duy nhất để phân tích Ebook có cấu trúc anchor-based.
    """
    all_anchor_ids = _get_all_anchor_ids(book.toc)
    content_tree = _build_tree(book.toc, book, temp_image_dir, all_anchor_ids)
    return content_tree