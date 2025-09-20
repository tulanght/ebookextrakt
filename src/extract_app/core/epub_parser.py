# file-path: src/extract_app/core/epub_parser.py
# version: 16.0
# last-updated: 2025-09-20
# description: Definitive version. Uses a direct, sequential scan of all content tags.

from ebooklib import epub
from bs4 import BeautifulSoup
from typing import List, Dict, Any
from pathlib import Path
from collections import OrderedDict
import os

def _get_unique_hrefs_from_toc(toc_items, unique_hrefs):
    """Recursively gets a unique, ordered list of hrefs from the ToC."""
    for item in toc_items:
        if isinstance(item, tuple):
            _get_unique_hrefs_from_toc(item, unique_hrefs)
        elif isinstance(item, epub.Link):
            href = item.href.split('#')[0]
            if href not in unique_hrefs:
                unique_hrefs[href] = item.title

def _resolve_image_path(src, doc_item, book):
    """Resolves the relative path of an image."""
    if not src: return None
    current_dir = Path(doc_item.get_name()).parent
    resolved_path_str = os.path.normpath(os.path.join(current_dir, src)).replace('\\', '/')
    return book.get_item_with_href(resolved_path_str)

def _save_image_to_temp(image_item, temp_image_dir):
    """Saves an image to the temp folder and returns its anchor path."""
    image_bytes = image_item.get_content()
    image_filename = f"epub_{Path(image_item.get_name()).name}"
    image_path = temp_image_dir / image_filename
    with open(image_path, "wb") as f:
        f.write(image_bytes)
    return str(image_path)

def parse_epub(filepath: str) -> List[Dict[str, Any]]:
    temp_image_dir = Path("temp/images")
    temp_image_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        book = epub.read_epub(filepath)
        structured_content = []
        
        unique_hrefs = OrderedDict()
        _get_unique_hrefs_from_toc(book.toc, unique_hrefs)

        for href, title in unique_hrefs.items():
            doc_item = book.get_item_with_href(href)
            if not doc_item: continue

            print(f"🔎 Processing chapter file: {title} (source: {href})")
            chapter_content = []
            soup = BeautifulSoup(doc_item.get_content(), 'xml')

            if soup.body:
                # --- DEFINITIVE ALGORITHM ---
                # Get a single, flat list of all relevant tags in the order they appear..
                content_tags = soup.body.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'div', 'figure', 'img'])
                
                for tag in content_tags:
                    # Handle image tags specifically
                    if tag.name == 'img':
                        image_item = _resolve_image_path(tag.get('src'), doc_item, book)
                        if image_item:
                            anchor = _save_image_to_temp(image_item, temp_image_dir)
                            # Check if the parent is a figure to find a caption
                            caption = ""
                            if tag.parent.name == 'figure':
                                caption_tag = tag.parent.find('figcaption')
                                if caption_tag:
                                    caption = caption_tag.get_text(strip=True)
                            chapter_content.append(('image', {'anchor': anchor, 'caption': caption}))
                    # Handle text-containing tags, but avoid double-counting text from figures
                    elif tag.name != 'figure':
                        text = tag.get_text(strip=True)
                        if text:
                            chapter_content.append(('text', text))
            
            if chapter_content:
                structured_content.append({'title': title, 'content': chapter_content})

        return structured_content
    except Exception as e:
        import traceback
        traceback.print_exc()
        return [{'title': 'Error', 'content': [('text', f"An error occurred: {e}")]}]