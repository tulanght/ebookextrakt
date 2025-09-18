# file-path: src/extract_app/core/epub_parser.py
# version: 1.1
# last-updated: 2025-09-18
# description: Thay đổi cấu trúc trả về thành danh sách các chương (list of lists).

from ebooklib import epub
from bs4 import BeautifulSoup
from typing import List, Tuple, Any

def parse_epub(filepath: str) -> List[List[Tuple[str, Any]]]:
    """
    Mở một file EPUB và trích xuất nội dung, nhóm theo từng chương/document.

    Args:
        filepath: Đường dẫn đến file EPUB.

    Returns:
        Một danh sách các danh sách. Mỗi danh sách con chứa content tuples của một chương.
    """
    all_chapters_content = []
    try:
        book = epub.read_epub(filepath)
        
        for item in book.get_items_of_type(9): # 9 is ITEM_DOCUMENT
            single_chapter_content = []
            soup = BeautifulSoup(item.get_content(), 'xml') 
            
            for element in soup.find_all(['p', 'img']):
                if element.name == 'p' and element.get_text(strip=True):
                    single_chapter_content.append(('text', element.get_text(strip=True)))
                elif element.name == 'img':
                    src = element.get('src')
                    image_item = book.get_item_with_href(src)
                    if image_item:
                        single_chapter_content.append(('image', image_item.get_content()))
            
            if single_chapter_content:
                all_chapters_content.append(single_chapter_content)

        return all_chapters_content
    except Exception as e:
        print(f"Lỗi khi xử lý file EPUB: {e}")
        return [[('text', f"Không thể đọc file: {filepath}. Lỗi: {e}")]]