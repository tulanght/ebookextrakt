# file-path: src/extract_app/core/epub_parser.py
# version: 14.0
# last-updated: 2025-09-20
# description: Definitive version. Robust content extraction to handle varied HTML structures.

from ebooklib import epub
from bs4 import BeautifulSoup
from typing import List, Dict, Any
from pathlib import Path
from collections import OrderedDict
import os

def _flatten_toc_recursive(toc_items, flat_list):
    if isinstance(toc_items, epub.Link):
        flat_list.append(toc_items)
    elif hasattr(toc_items, '__iter__'):
        for item in toc_items:
            _flatten_toc_recursive(item, flat_list)

def _extract_html_content(doc_item, book, temp_image_dir) -> List:
    content = []
    soup = BeautifulSoup(doc_item.get_content(), 'xml')
    if not soup.body:
        return content

    # --- FINAL ALGORITHM ---
    # First, find and process all images to ensure none are missed.
    all_images = soup.body.find_all('img')
    processed_images = set()

    for img_tag in all_images:
        src = img_tag.get('src')
        if not src or src in processed_images: continue
        
        current_dir = Path(doc_item.get_name()).parent
        resolved_path = os.path.normpath(os.path.join(current_dir, src)).replace('\\', '/')
        
        image_item = book.get_item_with_href(resolved_path)
        if image_item:
            image_bytes = image_item.get_content()
            image_filename = f"epub_{Path(image_item.get_name()).name}"
            image_path = temp_image_dir / image_filename
            with open(image_path, "wb") as f: f.write(image_bytes)
            content.append(('image', str(image_path)))
            processed_images.add(src)

    # Second, get all text content, excluding image alt text already processed.
    # We get text from the whole body to ensure we don't miss text in non-standard tags.
    text = soup.body.get_text(separator='\n', strip=True)
    if text:
        content.append(('text', text))
        
    return content

def parse_epub(filepath: str) -> List[Dict[str, Any]]:
    temp_image_dir = Path("temp/images")
    temp_image_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        book = epub.read_epub(filepath)
        structured_content = []
        
        flat_toc = []
        _flatten_toc_recursive(book.toc, flat_toc)
        
        for link in flat_toc:
            title = link.title
            href = link.href.split('#')[0]
            
            doc_item = book.get_item_with_href(href)
            if not doc_item: continue

            print(f"🔎 Processing ToC item: {title} (source: {href})")
            chapter_content = _extract_html_content(doc_item, book, temp_image_dir)
            if chapter_content:
                structured_content.append({'title': title, 'content': chapter_content})
            
        return structured_content
    except Exception as e:
        import traceback
        traceback.print_exc()
        return [{'title': 'Error', 'content': [('text', f"An error occurred: {e}")]}]