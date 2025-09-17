# file-path: src/extract_app/core/epub_parser.py
# version: 1.0
# last-updated: 2025-09-17
# description: Chứa logic nghiệp vụ để trích xuất nội dung từ file EPUB.

from ebooklib import epub
from bs4 import BeautifulSoup
from typing import List, Tuple, Any

def parse_epub(filepath: str) -> List[Tuple[str, Any]]:
    """
    # hotfix - 2025-09-17 - Chuyển sang dùng XML parser để xử lý XHTML trong EPUB.
    Mở một file EPUB và trích xuất nội dung dưới dạng danh sách các khối văn bản và hình ảnh.

    Args:
        filepath: Đường dẫn đến file EPUB.

    Returns:
        Một danh sách các tuple, mỗi tuple chứa ('loại_nội_dung', dữ_liệu).
    """
    content_list = []
    try:
        book = epub.read_epub(filepath)
        items = list(book.get_items())

        for item in book.get_items_of_type(9): # 9 is ITEM_DOCUMENT
            # Thay đổi ở dòng ngay dưới đây: dùng 'xml' thay vì 'lxml'
            soup = BeautifulSoup(item.get_content(), 'xml') 
            
            for element in soup.find_all(['p', 'img']):
                if element.name == 'p' and element.get_text(strip=True):
                    content_list.append(('text', element.get_text(strip=True)))
                elif element.name == 'img':
                    src = element.get('src')
                    image_item = book.get_item_with_href(src)
                    if image_item:
                        content_list.append(('image', image_item.get_content()))

        return content_list
    except Exception as e:
        print(f"Lỗi khi xử lý file EPUB: {e}")
        content_list.append(('text', f"Không thể đọc file: {filepath}. Lỗi: {e}"))
        return content_list