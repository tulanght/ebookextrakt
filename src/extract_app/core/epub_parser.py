# file-path: src/extract_app/core/epub_parser.py
# version: 4.0
# last-updated: 2025-09-19
# description: Viết lại hoàn toàn. Sử dụng một hàm đệ quy duy nhất để xử lý ToC và nội dung, đảm bảo không bỏ sót.

from ebooklib import epub
from bs4 import BeautifulSoup
from typing import List, Dict, Any
from pathlib import Path

def parse_epub(filepath: str) -> List[Dict[str, Any]]:
    """
    Hàm chính để bắt đầu quá trình phân tích file EPUB.
    """
    temp_image_dir = Path("temp/images")
    temp_image_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        book = epub.read_epub(filepath)
        structured_content = []
        
        # Bắt đầu duyệt đệ quy từ mục lục gốc
        _recursive_toc_parser(book, book.toc, structured_content, temp_image_dir)

        return structured_content
    except Exception as e:
        print(f"Lỗi khi xử lý file EPUB: {e}")
        return [{'title': 'Lỗi', 'content': [('text', f"Lỗi: {e}")]}]

def _recursive_toc_parser(book, toc_items, structured_content, temp_image_dir):
    """
    Hàm đệ quy duy nhất, duyệt qua cây mục lục và xử lý nội dung ngay khi tìm thấy.
    """
    for item in toc_items:
        # 1. Nếu item là một tuple, nó chứa các mục con -> đi sâu vào trong
        if isinstance(item, tuple):
            _recursive_toc_parser(book, item, structured_content, temp_image_dir)
            
        # 2. Nếu là một Link, đây là một chương/mục cần xử lý
        elif isinstance(item, epub.Link):
            title = item.title
            href = item.href.split('#')[0]
            print(f"🔎 Đang xử lý mục: {title} (href: {href})")

            doc_item = book.get_item_with_href(href)
            if not doc_item:
                continue

            # 3. Bóc tách nội dung của mục này
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
                            # Đảm bảo tên file là duy nhất
                            image_filename = f"epub_{Path(image_item.get_name()).name}"
                            image_path = temp_image_dir / image_filename
                            with open(image_path, "wb") as f:
                                f.write(image_bytes)
                            chapter_content.append(('image', str(image_path)))
                    else:
                        text = tag.get_text(strip=True)
                        if text:
                            chapter_content.append(('text', text))
            
            # 4. Thêm chương/mục đã xử lý vào kết quả cuối cùng
            if chapter_content:
                structured_content.append({'title': title, 'content': chapter_content})