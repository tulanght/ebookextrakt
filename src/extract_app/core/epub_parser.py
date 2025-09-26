# file-path: src/extract_app/core/epub_parser.py
# version: 66.1 (Dispatcher Fix)
# last-updated: 2025-09-26
# description: Correctly imports and calls the new specialized parser modules.

from ebooklib import epub
from bs4 import BeautifulSoup
from typing import List, Dict, Any
from pathlib import Path
import os

# Import các parser chuyên biệt
from .epub_parsers import simple_toc_parser, anchor_based_parser

# --- HELPER FUNCTIONS (Chỉ giữ lại các hàm chung nhất) ---
def _save_image_to_temp(image_item, temp_image_dir: Path, prefix="epub_") -> str:
    image_bytes = image_item.get_content()
    image_filename = f"{prefix}{Path(image_item.get_name()).name}"
    image_path = temp_image_dir / image_filename
    with open(image_path, "wb") as f:
        f.write(image_bytes)
    return str(image_path)

def _resolve_image_path(src: str, doc_item: epub.EpubHtml, book: epub.EpubBook):
    if not src: return None
    current_dir = Path(doc_item.get_name()).parent
    resolved_path_str = os.path.normpath(os.path.join(current_dir, src)).replace('\\', '/')
    return book.get_item_with_href(resolved_path_str)

# --- MASTER PARSE FUNCTION (BỘ ĐIỀU PHỐI) ---
def parse_epub(filepath: str) -> Dict[str, Any]:
    results = {'metadata': {}, 'content': []}
    temp_image_dir = Path("temp/images")
    temp_image_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        book = epub.read_epub(filepath)
        
        # --- Trích xuất Metadata & Ảnh bìa (đã ổn định) ---
        try: results['metadata']['title'] = book.get_metadata('DC', 'title')[0][0]
        except: results['metadata']['title'] = Path(filepath).stem
        try: results['metadata']['author'] = book.get_metadata('DC', 'creator')[0][0]
        except: results['metadata']['author'] = 'Không rõ'
        cover_path = ""
        cover_item = book.get_item_with_id('cover')
        if not cover_item:
            for item in book.get_items():
                if item.get_name().lower() in ['cover.xhtml', 'cover.html']:
                    cover_item = item
                    break
        if cover_item:
             try:
                 soup=BeautifulSoup(cover_item.get_content(),'xml')
                 img_tag=soup.find('img')
                 if img_tag and img_tag.get('src'):
                     final_cover_item=_resolve_image_path(img_tag.get('src'),cover_item,book)
                     if final_cover_item: cover_path=_save_image_to_temp(final_cover_item,temp_image_dir,"epub_cover_")
             except Exception: pass
        results['metadata']['cover_image_path'] = cover_path

        # --- Logic Điều phối ---
        is_nested = any(isinstance(item, (list, tuple)) for item in book.toc)
        
        if is_nested:
            print("=> Detected nested ToC. Using anchor-based parser.")
            results['content'] = anchor_based_parser.parse(book, temp_image_dir)
        else:
            print("=> Detected simple ToC. Using simple ToC parser.")
            results['content'] = simple_toc_parser.parse(book, temp_image_dir)

        return results

    except Exception as e:
        import traceback
        traceback.print_exc()
        return {'metadata': {}, 'content': [{'title': 'Error', 'content': [('text', f"An error occurred: {e}")]}]}