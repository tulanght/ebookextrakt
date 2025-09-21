# file-path: src/extract_app/core/epub_parser.py (Definitive Final Version)
# version: 21.0
# last-updated: 2025-09-22
# description: Definitive version. Uses a recursive HTML parser to correctly handle nested content, figures, and captions.

from ebooklib import epub
from bs4 import BeautifulSoup, Tag, NavigableString
from typing import List, Dict, Any
from pathlib import Path
from collections import OrderedDict
import os

def _flatten_toc_recursive(toc_items, flat_list):
    """Recursively flattens the ToC to get all Link objects."""
    if isinstance(toc_items, epub.Link):
        flat_list.append(toc_items)
    elif hasattr(toc_items, '__iter__'):
        for item in toc_items:
            _flatten_toc_recursive(item, flat_list)

def _save_image_to_temp(image_item, temp_image_dir, prefix="epub_"):
    """Saves an image to the temp folder and returns its anchor path."""
    image_bytes = image_item.get_content()
    image_filename = f"{prefix}{Path(image_item.get_name()).name}"
    image_path = temp_image_dir / image_filename
    with open(image_path, "wb") as f:
        f.write(image_bytes)
    return str(image_path)

def _resolve_image_path(src, doc_item, book):
    """Resolves the relative path of an image."""
    if not src: return None
    current_dir = Path(doc_item.get_name()).parent
    resolved_path_str = os.path.normpath(os.path.join(current_dir, src)).replace('\\', '/')
    return book.get_item_with_href(resolved_path_str)

def _find_cover_from_toc(book, flat_toc):
    """Helper function to find the cover item by searching the ToC links."""
    for link in flat_toc:
        if 'cover' in link.title.lower() or 'cover' in link.href.lower():
            cover_item = book.get_item_with_href(link.href)
            if cover_item:
                if cover_item.get_name().lower().endswith(('.xhtml', '.html')):
                    soup = BeautifulSoup(cover_item.get_content(), 'xml')
                    img_tag = soup.find('img')
                    if img_tag and img_tag.get('src'):
                        return _resolve_image_path(img_tag.get('src'), cover_item, book)
                else:
                    return cover_item
    return None

def _parse_element_recursively(element, book, doc_item, temp_image_dir) -> List:
    """
    The definitive recursive content parser. Processes elements sequentially.
    """
    content_list = []
    if not isinstance(element, Tag):
        return content_list

    # Base Case 1: Handle <figure> as a complete unit
    if element.name == 'figure':
        img_tag = element.find('img')
        caption_tag = element.find('figcaption')
        if img_tag and img_tag.get('src'):
            image_item = _resolve_image_path(img_tag.get('src'), doc_item, book)
            if image_item:
                anchor = _save_image_to_temp(image_item, temp_image_dir)
                caption = caption_tag.get_text(strip=True) if caption_tag else ""
                content_list.append(('image', {'anchor': anchor, 'caption': caption}))
        return content_list

    # Base Case 2: Handle standalone images (not in a figure)
    if element.name == 'img':
        if element.get('src'):
            image_item = _resolve_image_path(element.get('src'), doc_item, book)
            if image_item:
                anchor = _save_image_to_temp(image_item, temp_image_dir)
                content_list.append(('image', {'anchor': anchor, 'caption': ''}))
        return content_list

    # Base Case 3: Handle text-containing tags that don't typically have complex children
    if element.name in ['p', 'h1', 'h2', 'h3', 'h4']:
        text = element.get_text(strip=True)
        if text:
            content_list.append(('text', text))
        # Unlike previous versions, we DON'T return here. We still check its children.
    
    # Recursive Step: If the element has children, parse them
    if hasattr(element, 'children'):
        for child in element.children:
            content_list.extend(_parse_element_recursively(child, book, doc_item, temp_image_dir))
                
    return content_list


def parse_epub(filepath: str) -> Dict[str, Any]:
    """
    The main EPUB parsing function. Extracts metadata and structured content.
    """
    results = {'metadata': {}, 'content': []}
    temp_image_dir = Path("temp/images")
    temp_image_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        book = epub.read_epub(filepath)
        
        # 1. Extract Metadata
        metadata = {}
        try: metadata['title'] = book.get_metadata('DC', 'title')[0][0]
        except: metadata['title'] = Path(filepath).stem
        try: metadata['author'] = book.get_metadata('DC', 'creator')[0][0]
        except: metadata['author'] = 'Không rõ'
        results['metadata'] = metadata

        # 2. Extract Cover Image (Definitive Multi-Tiered System)
        cover_path = ""
        cover_item = None
        
        for meta in book.get_metadata('OPF', 'meta'):
            if meta[1].get('name') == 'cover':
                cover_id = meta[1].get('content')
                cover_item = book.get_item_with_id(cover_id)
                if cover_item: print("Tìm thấy ảnh bìa qua OPF metadata.")
                break
        
        if not cover_item:
            for item in book.guide:
                if item.get('type') == 'cover' and item.get('href'):
                    href = item.get('href')
                    cover_item = book.get_item_with_href(href)
                    if cover_item: print("Tìm thấy mục cover qua Guide.")
                    break

        if not cover_item:
            flat_toc_for_cover = []
            _flatten_toc_recursive(book.toc, flat_toc_for_cover)
            cover_item = _find_cover_from_toc(book, flat_toc_for_cover)
            if cover_item: print(f"Tìm thấy ảnh bìa qua quét ToC: {cover_item.get_name()}")
        
        if cover_item:
            if cover_item.get_name().lower().endswith(('.xhtml', '.html')):
                soup = BeautifulSoup(cover_item.get_content(), 'xml')
                img_tag = soup.find('img')
                if img_tag and img_tag.get('src'):
                    final_cover_item = _resolve_image_path(img_tag.get('src'), cover_item, book)
                    if final_cover_item:
                        cover_path = _save_image_to_temp(final_cover_item, temp_image_dir, "epub_cover_")
            else:
                 cover_path = _save_image_to_temp(cover_item, temp_image_dir, "epub_cover_")
        results['metadata']['cover_image_path'] = cover_path

        # 3. Extract Content
        content_list = []
        flat_toc = []
        _flatten_toc_recursive(book.toc, flat_toc)
        
        for link in flat_toc:
            title = link.title
            href = link.href.split('#')[0]
            doc_item = book.get_item_with_href(href)
            if not doc_item: continue

            print(f"🔎 Processing ToC item: {title} (source: {href})")
            
            soup = BeautifulSoup(doc_item.get_content(), 'xml')
            if soup.body:
                chapter_content = _parse_element_recursively(soup.body, book, doc_item, temp_image_dir)
                if chapter_content:
                    content_list.append({'title': title, 'content': chapter_content})
        
        results['content'] = content_list
        return results
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {'metadata': {}, 'content': [{'title': 'Lỗi', 'content': [('text', f"Lỗi: {e}")]}]}