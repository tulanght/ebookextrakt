# file-path: src/extract_app/core/epub_parser.py
# version: 2.7
# last-updated: 2025-09-18
# description: Tái cấu trúc lớn, gom nhóm nội dung theo file nguồn (href) để sửa lỗi crash.

from ebooklib import epub
from bs4 import BeautifulSoup
from typing import List, Dict, Any
from pathlib import Path
from collections import OrderedDict

def _get_unique_chapters_from_toc(book, toc_items, unique_chapters):
    """
    Hàm đệ quy để lấy ra một danh sách duy nhất các chương (href) và tiêu đề chính.
    """
    for item in toc_items:
        if isinstance(item, tuple):
            _get_unique_chapters_from_toc(book, item, unique_chapters)
        elif isinstance(item, epub.Link):
            href = item.href.split('#')[0]
            if href not in unique_chapters:
                unique_chapters[href] = item.title

def parse_epub(filepath: str) -> List[Dict[str, Any]]:
    temp_image_dir = Path("temp/images")
    temp_image_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        book = epub.read_epub(filepath)
        structured_content = []
        
        # Bước 1: Tạo danh sách các chương duy nhất dựa trên href
        unique_chapters = OrderedDict()
        _get_unique_chapters_from_toc(book, book.toc, unique_chapters)

        # Bước 2: Duyệt qua danh sách chương duy nhất đó để xử lý
        for href, title in unique_chapters.items():
            print(f"🔎 Đang xử lý file chương: {title} (href: {href})")
            
            doc_item = book.get_item_with_href(href)
            if not doc_item: continue

            chapter_content = []
            soup = BeautifulSoup(doc_item.get_content(), 'xml')

            if soup.body:
                content_tags = soup.body.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'img'])
                
                for tag in content_tags:
                    if tag.name == 'img':
                        src = tag.get('src')
                        if not src: continue
                        
                        image_item = book.get_item_with_href(src)
                        if image_item:
                            image_bytes = image_item.get_content()
                            image_ext = Path(image_item.get_name()).suffix
                            image_filename = f"epub_{Path(image_item.get_name()).stem}{image_ext}"
                            image_path = temp_image_dir / image_filename
                            with open(image_path, "wb") as f:
                                f.write(image_bytes)
                            chapter_content.append(('image', str(image_path)))
                    else:
                        text = tag.get_text(strip=True)
                        if text:
                            chapter_content.append(('text', text))
            
            if chapter_content:
                structured_content.append({'title': title, 'content': chapter_content})

        return structured_content
    except Exception as e:
        print(f"Lỗi khi xử lý file EPUB: {e}")
        return [{'title': 'Lỗi', 'content': [('text', f"Lỗi: {e}")]}]